/**
 * @file sandwich_bt_main.cpp
 * @brief Entry point for the BehaviorTree.CPP sandwich runner.
 *
 * This executable loads a BT XML file, registers custom BT nodes, ticks the tree,
 * and exposes optional Groot monitoring when supported.
 */
#include <chrono>
#include <exception>
#include <memory>
#include <string>

#include <ament_index_cpp/get_package_share_directory.hpp>
#include <rclcpp/rclcpp.hpp>

#if __has_include(<behaviortree_cpp/bt_factory.h>)
#include <behaviortree_cpp/blackboard.h>
#include <behaviortree_cpp/bt_factory.h>
#elif __has_include(<behaviortree_cpp_v3/bt_factory.h>)
#include <behaviortree_cpp_v3/blackboard.h>
#include <behaviortree_cpp_v3/bt_factory.h>
#else
#error "BehaviorTree.CPP headers were not found."
#endif

#if __has_include(<behaviortree_cpp/loggers/groot2_publisher.h>)
#include <behaviortree_cpp/loggers/groot2_publisher.h>
using GrootPublisherT = BT::Groot2Publisher;
#define SANDWICH_BT_HAS_GROOT 1
#define SANDWICH_BT_HAS_GROOT2_PUBLISHER 1
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

#ifndef SANDWICH_BT_HAS_GROOT2_PUBLISHER
#define SANDWICH_BT_HAS_GROOT2_PUBLISHER 0
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
  return ament_index_cpp::get_package_share_directory("sandwich_bt_runtime_cpp") + "/trees/makesandwitch.xml";
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
  node->declare_parameter<int>("groot_publisher_port", 1667);
  node->declare_parameter<std::string>("bt.initial_scene_ready_gate", "initial_scene_ready");
  node->declare_parameter<std::string>("bt.place_first_toast_skill", "place_first_toast");
  node->declare_parameter<double>("bt.place_first_toast_timeout_s", 120.0);
  node->declare_parameter<std::string>("bt.pour_ingredient_gate", "pour_ingredient");
  node->declare_parameter<std::string>("bt.second_toast_ready_gate", "second_toast_ready");
  node->declare_parameter<std::string>("bt.place_second_toast_skill", "place_second_toast");
  node->declare_parameter<double>("bt.place_second_toast_timeout_s", 30.0);

  const auto tree_xml_path = node->get_parameter("tree_xml_path").as_string();
  const auto bt_command_service = node->get_parameter("bt_command_service").as_string();
  const auto vlm_state_service = node->get_parameter("vlm_state_service").as_string();
  const auto tick_ms = node->get_parameter("tick_ms").as_int();
  const auto enable_groot = node->get_parameter("enable_groot_publisher").as_bool();
  const auto groot_port = node->get_parameter("groot_publisher_port").as_int();
  const auto initial_scene_ready_gate = node->get_parameter("bt.initial_scene_ready_gate").as_string();
  const auto place_first_toast_skill = node->get_parameter("bt.place_first_toast_skill").as_string();
  const auto place_first_toast_timeout_s = node->get_parameter("bt.place_first_toast_timeout_s").as_double();
  const auto pour_ingredient_gate = node->get_parameter("bt.pour_ingredient_gate").as_string();
  const auto second_toast_ready_gate = node->get_parameter("bt.second_toast_ready_gate").as_string();
  const auto place_second_toast_skill = node->get_parameter("bt.place_second_toast_skill").as_string();
  const auto place_second_toast_timeout_s = node->get_parameter("bt.place_second_toast_timeout_s").as_double();

  // Register each custom XML tag with a lambda that injects the already-created
  // ROS2 node and service name into the BT node constructor.
  BT::BehaviorTreeFactory factory;
  const auto robot_skill_builder =
    [node, bt_command_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::RunRobotSkillNode>(
        instance_name,
        config,
        node,
        bt_command_service);
    };
  const auto vlm_gate_builder =
    [node, bt_command_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::OpenVLMGateNode>(
        instance_name,
        config,
        node,
        bt_command_service);
    };
  factory.registerBuilder<sandwich_bt_runtime_cpp::RunRobotSkillNode>(
    "RunRobotSkill",
    robot_skill_builder);
  factory.registerBuilder<sandwich_bt_runtime_cpp::OpenVLMGateNode>(
    "OpenVLMGate",
    vlm_gate_builder);
  factory.registerBuilder<sandwich_bt_runtime_cpp::OpenVLMGateNode>(
    "PrepareInitialScene",
    vlm_gate_builder);
  factory.registerBuilder<sandwich_bt_runtime_cpp::OpenVLMGateNode>(
    "PrepareSecondToast",
    vlm_gate_builder);
  factory.registerBuilder<sandwich_bt_runtime_cpp::RunRobotSkillNode>(
    "PlaceFirstToast",
    robot_skill_builder);
  factory.registerBuilder<sandwich_bt_runtime_cpp::RunRobotSkillNode>(
    "PlaceSecondToast",
    robot_skill_builder);
  factory.registerBuilder<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "VerifySkillOutcome",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  factory.registerBuilder<sandwich_bt_runtime_cpp::WaitForGateVerdictNode>(
    "WaitForGateVerdict",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::WaitForGateVerdictNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  factory.registerBuilder<sandwich_bt_runtime_cpp::WaitForSkillVerdictNode>(
    "WaitForSkillVerdict",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<sandwich_bt_runtime_cpp::WaitForSkillVerdictNode>(
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

  auto blackboard = BT::Blackboard::create();
  blackboard->set("initial_scene_ready_gate", initial_scene_ready_gate);
  blackboard->set("place_first_toast_skill", place_first_toast_skill);
  blackboard->set("place_first_toast_timeout_s", place_first_toast_timeout_s);
  blackboard->set("pour_ingredient_gate", pour_ingredient_gate);
  blackboard->set("second_toast_ready_gate", second_toast_ready_gate);
  blackboard->set("place_second_toast_skill", place_second_toast_skill);
  blackboard->set("place_second_toast_timeout_s", place_second_toast_timeout_s);

  RCLCPP_INFO(
    node->get_logger(),
    "Loaded BT task parameters: initial_scene_ready_gate='%s', place_first_toast_skill='%s', "
    "place_first_toast_timeout_s=%.2f, pour_ingredient_gate='%s', second_toast_ready_gate='%s', "
    "place_second_toast_skill='%s', place_second_toast_timeout_s=%.2f.",
    initial_scene_ready_gate.c_str(),
    place_first_toast_skill.c_str(),
    place_first_toast_timeout_s,
    pour_ingredient_gate.c_str(),
    second_toast_ready_gate.c_str(),
    place_second_toast_skill.c_str(),
    place_second_toast_timeout_s);

  // Loading from file keeps the BT topology editable without recompiling this
  // executable; malformed XML or missing node tags will fail at this point.
  BT::Tree tree = factory.createTreeFromFile(tree_xml_path, blackboard);

#if SANDWICH_BT_HAS_GROOT
  std::unique_ptr<GrootPublisherT> groot_publisher;
  if (enable_groot) {
    try {
#if SANDWICH_BT_HAS_GROOT2_PUBLISHER
      groot_publisher = std::make_unique<GrootPublisherT>(tree, static_cast<unsigned>(groot_port));
      RCLCPP_INFO(node->get_logger(), "Groot publisher enabled on port %d.", groot_port);
#else
      groot_publisher = std::make_unique<GrootPublisherT>(tree);
      RCLCPP_INFO(
        node->get_logger(),
        "Groot publisher enabled. The 'groot_publisher_port' parameter is only supported with Groot2Publisher.");
#endif
    } catch (const std::exception& exc) {
      RCLCPP_WARN(
        node->get_logger(),
        "Could not start Groot publisher: %s. Continuing without Groot monitoring. "
        "If this says 'Address already in use', another sandwich_bt_runner may still be running "
        "or the port is occupied; stop it or pass '-p enable_groot_publisher:=false'.",
        exc.what());
      groot_publisher.reset();
    }
  }
#else
  if (enable_groot) {
    RCLCPP_WARN(node->get_logger(), "Groot publisher requested but no compatible BT.CPP publisher header was found.");
  }
#endif

  BT::NodeStatus status = BT::NodeStatus::RUNNING;
  rclcpp::WallRate rate{std::chrono::milliseconds(tick_ms)};

  const auto cleanup = [&](const char* reason) {
    const bool ros_context_active = rclcpp::ok();
    if (ros_context_active) {
      RCLCPP_INFO(node->get_logger(), "Stopping behavior tree runner: %s", reason);
    }
    try {
      tree.haltTree();
    } catch (const std::exception& exc) {
      if (ros_context_active) {
        RCLCPP_WARN(node->get_logger(), "Exception while halting behavior tree: %s", exc.what());
      }
    }

#if SANDWICH_BT_HAS_GROOT
    try {
      groot_publisher.reset();
    } catch (const std::exception& exc) {
      if (ros_context_active) {
        RCLCPP_WARN(node->get_logger(), "Exception while stopping Groot publisher: %s", exc.what());
      }
    }
#endif

    if (rclcpp::ok()) {
      rclcpp::shutdown();
    }
  };

  try {
    // Main BT loop: each tick may trigger one service-backed leaf execution.
    while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
      status = tree.tickOnce();
      if (rclcpp::ok()) {
        rclcpp::spin_some(node);
      }
      rate.sleep();
    }

    if (rclcpp::ok()) {
      rclcpp::spin_some(node);
    }
  } catch (const std::exception& exc) {
    RCLCPP_ERROR(node->get_logger(), "Behavior tree runner caught exception: %s", exc.what());
    cleanup("exception");
    return 1;
  }

  if (!rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
    cleanup("interrupt requested");
    return 130;
  }
  if (status == BT::NodeStatus::SUCCESS) {
    RCLCPP_INFO(node->get_logger(), "Behavior tree completed with SUCCESS.");
    cleanup("tree completed with SUCCESS");
    return 0;
  }

  RCLCPP_ERROR(node->get_logger(), "Behavior tree completed with FAILURE.");
  cleanup("tree completed with FAILURE");
  return 1;
}
