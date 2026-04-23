#include <chrono>
#include <memory>
#include <string>

// Main BehaviorTree.CPP runtime.
//
// Flow role:
// 1. Load the XML tree.
// 2. Register the custom node that talks to the Python server.
// 3. Tick the tree until the sandwich task succeeds or fails.
// 4. Optionally publish the tree state to Groot.

#include <ament_index_cpp/get_package_share_directory.hpp>
#include <behaviortree_cpp/bt_factory.h>
#include <rclcpp/rclcpp.hpp>

#if __has_include(<behaviortree_cpp/loggers/groot2_publisher.h>)
#include <behaviortree_cpp/loggers/groot2_publisher.h>
using GrootPublisherT = BT::Groot2Publisher;
#define SANDWICH_BT_HAS_GROOT 1
#elif __has_include(<behaviortree_cpp/loggers/bt_zmq_publisher.h>)
#include <behaviortree_cpp/loggers/bt_zmq_publisher.h>
using GrootPublisherT = BT::PublisherZMQ;
#define SANDWICH_BT_HAS_GROOT 1
#else
#define SANDWICH_BT_HAS_GROOT 0
#endif

#include "sandwich_bt_runtime_cpp/run_named_command_node.hpp"

namespace
{

std::string default_tree_xml_path()
{
  return ament_index_cpp::get_package_share_directory("sandwich_bt_runtime_cpp") + "/trees/sandwich_tree.xml";
}

}  // namespace

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);

  // Runtime parameters:
  // - which XML tree to load
  // - which service to call on the Python side
  // - BT tick period
  // - whether to publish to Groot
  auto node = std::make_shared<rclcpp::Node>("sandwich_bt_runner");
  node->declare_parameter<std::string>("tree_xml_path", default_tree_xml_path());
  node->declare_parameter<std::string>("service_name", "/sandwich_bt/run_command");
  node->declare_parameter<int>("tick_ms", 100);
  node->declare_parameter<bool>("enable_groot_publisher", true);

  const auto tree_xml_path = node->get_parameter("tree_xml_path").as_string();
  const auto service_name = node->get_parameter("service_name").as_string();
  const auto tick_ms = node->get_parameter("tick_ms").as_int();
  const auto enable_groot = node->get_parameter("enable_groot_publisher").as_bool();

  BT::BehaviorTreeFactory factory;
  // Register the custom leaf that calls the Python skill server.
  factory.registerBuilder<sandwich_bt_runtime_cpp::RunNamedCommandNode>(
    "RunNamedCommand",
    [node, service_name](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::RunNamedCommandNode>(
        instance_name,
        config,
        node,
        service_name);
    });

  BT::Tree tree = factory.createTreeFromFile(tree_xml_path);

#if SANDWICH_BT_HAS_GROOT
  std::unique_ptr<GrootPublisherT> groot_publisher;
  if (enable_groot) {
    groot_publisher = std::make_unique<GrootPublisherT>(tree);
    RCLCPP_INFO(node->get_logger(), "Groot publisher enabled.");
  }
#else
  if (enable_groot) {
    RCLCPP_WARN(node->get_logger(), "Groot publisher requested but no compatible BT.CPP publisher header was found.");
  }
#endif

  BT::NodeStatus status = BT::NodeStatus::RUNNING;
  rclcpp::WallRate rate(std::chrono::milliseconds(tick_ms));

  // Main BT loop: each tick may trigger one service-backed leaf execution.
  while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
    status = tree.tickOnce();
    rclcpp::spin_some(node);
    rate.sleep();
  }

  rclcpp::spin_some(node);
  if (status == BT::NodeStatus::SUCCESS) {
    RCLCPP_INFO(node->get_logger(), "Behavior tree completed with SUCCESS.");
    rclcpp::shutdown();
    return 0;
  }

  RCLCPP_ERROR(node->get_logger(), "Behavior tree completed with FAILURE.");
  rclcpp::shutdown();
  return 1;
}
