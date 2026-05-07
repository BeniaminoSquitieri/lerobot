/**
 * @file sandwich_bt_main.cpp
 * @brief Entry point for the BehaviorTree.CPP sandwich runner.
 *
 * This executable loads a BT XML file, registers custom BT nodes, ticks the tree,
 * and exposes optional Groot monitoring when supported.
 */
#include <chrono>
#include <memory>
#include <string>

#include <ament_index_cpp/get_package_share_directory.hpp>
#include <rclcpp/rclcpp.hpp>

#if __has_include(<behaviortree_cpp/bt_factory.h>)
#include <behaviortree_cpp/bt_factory.h>
#elif __has_include(<behaviortree_cpp_v3/bt_factory.h>)
#include <behaviortree_cpp_v3/bt_factory.h>
#else
#error "BehaviorTree.CPP headers were not found."
#endif

#if __has_include(<behaviortree_cpp/loggers/groot2_publisher.h>)
#include <behaviortree_cpp/loggers/groot2_publisher.h>
using GrootPublisherT = BT::Groot2Publisher;
#define SANDWICH_BT_HAS_GROOT 1
#elif __has_include(<behaviortree_cpp/loggers/bt_zmq_publisher.h>)
#include <behaviortree_cpp/loggers/bt_zmq_publisher.h>
using GrootPublisherT = BT::PublisherZMQ;
#define SANDWICH_BT_HAS_GROOT 1
#elif __has_include(<behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>)
#include <behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>
using GrootPublisherT = BT::PublisherZMQ;
#define SANDWICH_BT_HAS_GROOT 1
#else
#define SANDWICH_BT_HAS_GROOT 0
#endif

#include "sandwich_bt_runtime_cpp/run_named_command_node.hpp"
#include "sandwich_bt_runtime_cpp/verify_skill_outcome_node.hpp"

namespace
{

/**
 * @brief Returns the installed default sandwich behavior-tree XML path.
 */
std::string default_tree_xml_path()
{
  return ament_index_cpp::get_package_share_directory("sandwich_bt_runtime_cpp") + "/trees/sandwich_tree.xml";
}

}  // namespace

/**
 * @brief Runs the ROS2 node that loads, registers, and ticks the sandwich BT.
 *
 * @param argc Process argument count forwarded to rclcpp.
 * @param argv Process argument vector forwarded to rclcpp.
 * @return 0 when the tree finishes with SUCCESS, 1 for FAILURE.
 */
int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);

  // Runtime parameters:
  // - which XML tree to load
  // - where the BT sends skill/gate commands
  // - where the BT polls VLM state
  // - BT tick period
  // - whether to publish to Groot
  auto node = std::make_shared<rclcpp::Node>("sandwich_bt_runner");
  node->declare_parameter<std::string>("tree_xml_path", default_tree_xml_path());
  node->declare_parameter<std::string>("bt_command_service", "/sandwich_bt/run");
  node->declare_parameter<std::string>("vlm_state_service", "/sandwich_bt/vlm_state");
  node->declare_parameter<int>("tick_ms", 100);
  node->declare_parameter<bool>("enable_groot_publisher", true);

  const auto tree_xml_path = node->get_parameter("tree_xml_path").as_string();
  const auto bt_command_service = node->get_parameter("bt_command_service").as_string();
  const auto vlm_state_service = node->get_parameter("vlm_state_service").as_string();
  const auto tick_ms = node->get_parameter("tick_ms").as_int();
  const auto enable_groot = node->get_parameter("enable_groot_publisher").as_bool();

  // Register each custom XML tag with a lambda that injects the already-created
  // ROS2 node and service name into the BT node constructor.
  BT::BehaviorTreeFactory factory;
  factory.registerBuilder<sandwich_bt_runtime_cpp::RunNamedCommandNode>(
    "RunNamedCommand",
    [node, bt_command_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::RunNamedCommandNode>(
        instance_name,
        config,
        node,
        bt_command_service);
    });
  factory.registerBuilder<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "VerifySkillOutcome",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  // These aliases use the same ROS2 VLM state service but make the XML/Groot
  // graph show whether a node is a waiting gate or a post-skill retry decision.
  factory.registerBuilder<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "WaitForVLMDecision",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  factory.registerBuilder<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "VLMReplanningDecision",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });

  // Loading from file keeps the BT topology editable without recompiling this
  // executable; malformed XML or missing node tags will fail at this point.
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
  rclcpp::WallRate rate{std::chrono::milliseconds(tick_ms)};

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
