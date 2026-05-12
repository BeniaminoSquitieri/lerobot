/**
 * @file lerobot_bt_main.cpp
 * @brief Entry point for the BehaviorTree.CPP LeRobot BT runner.
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
#define LEROBOT_BT_HAS_GROOT 1
#define LEROBOT_BT_HAS_GROOT2_PUBLISHER 1
#elif __has_include(<behaviortree_cpp/loggers/bt_zmq_publisher.h>)
#include <behaviortree_cpp/loggers/bt_zmq_publisher.h>
using GrootPublisherT = BT::PublisherZMQ;
#define LEROBOT_BT_HAS_GROOT 1
#elif __has_include(<behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>)
#include <behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>
using GrootPublisherT = BT::PublisherZMQ;
#define LEROBOT_BT_HAS_GROOT 1
#else
#define LEROBOT_BT_HAS_GROOT 0
#endif

#ifndef LEROBOT_BT_HAS_GROOT2_PUBLISHER
#define LEROBOT_BT_HAS_GROOT2_PUBLISHER 0
#endif

#include "lerobot_bt_runtime_cpp/run_named_command_node.hpp"
#include "lerobot_bt_runtime_cpp/verify_skill_outcome_node.hpp"

namespace
{

/**
 * @brief Returns the installed default make-sandwich behavior-tree XML path.
 */
std::string default_tree_xml_path()
{
  return ament_index_cpp::get_package_share_directory("lerobot_bt_runtime_cpp") + "/trees/make_sandwich.xml";
}

/**
 * @brief Declare a ROS2 parameter if absent, then return its typed value.
 *
 * Parameters may come from a task profile YAML, launch overrides, or the
 * default values below. This helper keeps that lookup pattern consistent for
 * every BT runtime setting.
 */
template <typename ParameterT>
ParameterT declareOrGetParameter(
  const rclcpp::Node::SharedPtr& node,
  const std::string& name,
  const ParameterT& default_value)
{
  if (!node->has_parameter(name)) {
    node->declare_parameter<ParameterT>(name, default_value);
  }
  return node->get_parameter(name).get_value<ParameterT>();
}

/**
 * @brief Copy task-profile `bt.*` ROS2 parameters into the BT blackboard.
 *
 * The XML trees use placeholders such as `{place_first_toast_skill}`. The
 * corresponding values live in YAML profiles and become blackboard entries
 * before the tree is instantiated.
 */
void setBtBlackboardEntries(
  const rclcpp::Node::SharedPtr& node,
  const std::shared_ptr<BT::Blackboard>& blackboard)
{
  // Task YAML files place all tree variables under `bt.*`; only those
  // parameters are copied into the BehaviorTree.CPP blackboard.
  const auto bt_parameters = node->list_parameters({"bt"}, 10);
  int loaded_count = 0;

  for (const auto& parameter_name : bt_parameters.names) {
    constexpr const char* bt_prefix = "bt.";
    if (parameter_name.rfind(bt_prefix, 0) != 0) {
      continue;
    }

    const auto blackboard_key = parameter_name.substr(std::string(bt_prefix).size());
    const auto parameter = node->get_parameter(parameter_name);
    switch (parameter.get_type()) {
      case rclcpp::ParameterType::PARAMETER_STRING:
        blackboard->set(blackboard_key, parameter.as_string());
        ++loaded_count;
        break;
      case rclcpp::ParameterType::PARAMETER_DOUBLE:
        blackboard->set(blackboard_key, parameter.as_double());
        ++loaded_count;
        break;
      case rclcpp::ParameterType::PARAMETER_INTEGER:
        blackboard->set(blackboard_key, static_cast<int>(parameter.as_int()));
        ++loaded_count;
        break;
      case rclcpp::ParameterType::PARAMETER_BOOL:
        blackboard->set(blackboard_key, parameter.as_bool());
        ++loaded_count;
        break;
      default:
        RCLCPP_WARN(
          node->get_logger(),
          "Skipping unsupported BT parameter '%s' of type '%s'.",
          parameter_name.c_str(),
          parameter.get_type_name().c_str());
        break;
    }
  }

  RCLCPP_INFO(node->get_logger(), "Loaded %d BT blackboard parameter(s) from the 'bt.*' namespace.", loaded_count);
}

}  // namespace

/**
 * @brief Runs the ROS2 node that loads, registers, and ticks the LeRobot BT.
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
  const auto node_options = rclcpp::NodeOptions()
                              .allow_undeclared_parameters(true)
                              .automatically_declare_parameters_from_overrides(true);
  auto node = std::make_shared<rclcpp::Node>("lerobot_bt_runner", node_options);
  const auto tree_xml_path = declareOrGetParameter<std::string>(node, "tree_xml_path", default_tree_xml_path());
  const auto bt_command_service = declareOrGetParameter<std::string>(node, "bt_command_service", "/lerobot_bt/run");
  const auto vlm_state_service = declareOrGetParameter<std::string>(node, "vlm_state_service", "/lerobot_bt/vlm_state");
  const auto tick_ms = declareOrGetParameter<int>(node, "tick_ms", 100);
  const auto enable_groot = declareOrGetParameter<bool>(node, "enable_groot_publisher", true);
  const auto groot_port = declareOrGetParameter<int>(node, "groot_publisher_port", 1667);

  // Keep default make-sandwich values available when no params file is passed.
  declareOrGetParameter<std::string>(node, "bt.initial_scene_ready_gate", "initial_scene_ready");
  declareOrGetParameter<std::string>(node, "bt.place_first_toast_skill", "place_first_toast");
  declareOrGetParameter<double>(node, "bt.place_first_toast_timeout_s", 120.0);
  declareOrGetParameter<std::string>(node, "bt.pour_ingredient_gate", "pour_ingredient");
  declareOrGetParameter<std::string>(node, "bt.second_toast_ready_gate", "second_toast_ready");
  declareOrGetParameter<std::string>(node, "bt.place_second_toast_skill", "place_second_toast");
  declareOrGetParameter<double>(node, "bt.place_second_toast_timeout_s", 30.0);

  // Register each custom XML tag with a lambda that injects the already-created
  // ROS2 node and service name into the BT node constructor.
  BT::BehaviorTreeFactory factory;
  const auto robot_skill_builder =
    [node, bt_command_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::RunRobotSkillNode>(
        instance_name,
        config,
        node,
        bt_command_service);
    };
  const auto vlm_gate_builder =
    [node, bt_command_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::OpenVLMGateNode>(
        instance_name,
        config,
        node,
        bt_command_service);
    };
  factory.registerBuilder<lerobot_bt_runtime_cpp::RunRobotSkillNode>(
    "RunRobotSkill",
    robot_skill_builder);
  factory.registerBuilder<lerobot_bt_runtime_cpp::OpenVLMGateNode>(
    "OpenVLMGate",
    vlm_gate_builder);
  factory.registerBuilder<lerobot_bt_runtime_cpp::OpenVLMGateNode>(
    "PrepareInitialScene",
    vlm_gate_builder);
  factory.registerBuilder<lerobot_bt_runtime_cpp::OpenVLMGateNode>(
    "PrepareSecondToast",
    vlm_gate_builder);
  factory.registerBuilder<lerobot_bt_runtime_cpp::RunRobotSkillNode>(
    "PlaceFirstToast",
    robot_skill_builder);
  factory.registerBuilder<lerobot_bt_runtime_cpp::RunRobotSkillNode>(
    "PlaceSecondToast",
    robot_skill_builder);
  factory.registerBuilder<lerobot_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "VerifySkillOutcome",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  factory.registerBuilder<lerobot_bt_runtime_cpp::WaitForGateVerdictNode>(
    "WaitForGateVerdict",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::WaitForGateVerdictNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  factory.registerBuilder<lerobot_bt_runtime_cpp::WaitForSkillVerdictNode>(
    "WaitForSkillVerdict",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::WaitForSkillVerdictNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  // These aliases use the same ROS2 VLM state service but make the XML/Groot
  // graph show whether a node is a waiting gate or a post-skill retry decision.
  factory.registerBuilder<lerobot_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "WaitForVLMDecision",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });
  factory.registerBuilder<lerobot_bt_runtime_cpp::VerifySkillOutcomeNode>(
    "VLMReplanningDecision",
    [node, vlm_state_service](const std::string& instance_name, const BT::NodeConfiguration& config) {
      return std::make_unique<lerobot_bt_runtime_cpp::VerifySkillOutcomeNode>(
        instance_name,
        config,
        node,
        vlm_state_service);
    });

  auto blackboard = BT::Blackboard::create();
  setBtBlackboardEntries(node, blackboard);

  // Loading from file keeps the BT topology editable without recompiling this
  // executable; malformed XML or missing node tags will fail at this point.
  BT::Tree tree = factory.createTreeFromFile(tree_xml_path, blackboard);

#if LEROBOT_BT_HAS_GROOT
  std::unique_ptr<GrootPublisherT> groot_publisher;
  if (enable_groot) {
    try {
#if LEROBOT_BT_HAS_GROOT2_PUBLISHER
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
        "If this says 'Address already in use', another lerobot_bt_runner may still be running "
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

#if LEROBOT_BT_HAS_GROOT
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
