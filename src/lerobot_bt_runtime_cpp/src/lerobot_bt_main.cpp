/**
 * @file lerobot_bt_main.cpp
 * @brief Entry point for the BehaviorTree.CPP LeRobot BT runner.
 *
 * This executable loads a BT XML file, registers custom BT nodes, ticks the tree,
 * and exposes optional Groot monitoring when supported.
 */
// Comment: includes a dependency required for compilation.
#include <chrono>
// Comment: includes a dependency required for compilation.
#include <exception>
// Comment: includes a dependency required for compilation.
#include <memory>
// Comment: includes a dependency required for compilation.
#include <string>

// Comment: includes a dependency required for compilation.
#include <ament_index_cpp/get_package_share_directory.hpp>
// Comment: includes a dependency required for compilation.
#include <rclcpp/rclcpp.hpp>

// Comment: selects code based on the macros available at compile time.
#if __has_include(<behaviortree_cpp/bt_factory.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp/blackboard.h>
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp/bt_factory.h>
// Comment: selects code based on the macros available at compile time.
#elif __has_include(<behaviortree_cpp_v3/bt_factory.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp_v3/blackboard.h>
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp_v3/bt_factory.h>
// Comment: uses the fallback branch of the compilation configuration.
#else
// Comment: forces a compilation error when a required dependency is missing.
#error "BehaviorTree.CPP headers were not found."
// Comment: closes the conditional compilation block.
#endif

// Comment: selects code based on the macros available at compile time.
#if __has_include(<behaviortree_cpp/loggers/groot2_publisher.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp/loggers/groot2_publisher.h>
// Compatibility with the available Groot publisher variants.
// Comment: defines a type alias or imports a symbol into the current namespace.
using GrootPublisherT = BT::Groot2Publisher;
// Comment: defines a macro used by the C++ code.
#define LEROBOT_BT_HAS_GROOT 1
// Comment: defines a macro used by the C++ code.
#define LEROBOT_BT_HAS_GROOT2_PUBLISHER 1
// Comment: selects code based on the macros available at compile time.
#elif __has_include(<behaviortree_cpp/loggers/bt_zmq_publisher.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp/loggers/bt_zmq_publisher.h>
// ZMQ publisher used by Groot v1.
// Comment: defines a type alias or imports a symbol into the current namespace.
using GrootPublisherT = BT::PublisherZMQ;
// Comment: defines a macro used by the C++ code.
#define LEROBOT_BT_HAS_GROOT 1
// Comment: selects code based on the macros available at compile time.
#elif __has_include(<behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>
// Compatibility with BehaviorTree.CPP v3.
// Comment: defines a type alias or imports a symbol into the current namespace.
using GrootPublisherT = BT::PublisherZMQ;
// Comment: defines a macro used by the C++ code.
#define LEROBOT_BT_HAS_GROOT 1
// Comment: uses the fallback branch of the compilation configuration.
#else
// Comment: defines a macro used by the C++ code.
#define LEROBOT_BT_HAS_GROOT 0
// Comment: closes the conditional compilation block.
#endif

// Comment: selects code based on the macros available at compile time.
#ifndef LEROBOT_BT_HAS_GROOT2_PUBLISHER
// Comment: defines a macro used by the C++ code.
#define LEROBOT_BT_HAS_GROOT2_PUBLISHER 0
// Comment: closes the conditional compilation block.
#endif

// Comment: includes a dependency required for compilation.
#include "lerobot_bt_runtime_cpp/await_scene_node.hpp"
// Comment: includes a dependency required for compilation.
#include "lerobot_bt_runtime_cpp/run_named_command_node.hpp"

// Comment: executes this BT logic statement in C++.
namespace
// Comment: opens a new C++ code block.
{

/**
 * @brief Returns the installed default make-sandwich behavior-tree XML path.
 */
// Comment: executes this BT logic statement in C++.
std::string default_tree_xml_path()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return ament_index_cpp::get_package_share_directory("lerobot_bt_runtime_cpp") + "/trees/make_sandwich.xml";
// Comment: closes the current C++ code block.
}

/**
 * @brief Declare a ROS2 parameter if absent, then return its typed value.
 *
 * Parameters may come from a task profile YAML, launch overrides, or the
 * default values below. This helper keeps that lookup pattern consistent for
 * every BT runtime setting.
 */
// Comment: executes this BT logic statement in C++.
template <typename ParameterT>
// Comment: executes this BT logic statement in C++.
ParameterT declareOrGetParameter(
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& node,
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const ParameterT& default_value)
// Comment: opens a new C++ code block.
{
  // Comment: evaluates a condition and chooses the branch to run.
  if (!node->has_parameter(name)) {
    // Comment: executes this BT logic statement in C++.
    node->declare_parameter<ParameterT>(name, default_value);
  // Comment: closes the current C++ code block.
  }
  // Comment: returns the value or status to the caller.
  return node->get_parameter(name).get_value<ParameterT>();
// Comment: closes the current C++ code block.
}

/**
 * @brief Copy task-profile `bt.*` ROS2 parameters into the BT blackboard.
 *
 * The XML trees use placeholders such as `{place_first_toast_skill}`. The
 * corresponding values live in YAML profiles and become blackboard entries
 * before the tree is instantiated.
 */
// Comment: executes this BT logic statement in C++.
void setBtBlackboardEntries(
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& node,
  // Comment: executes this BT logic statement in C++.
  const std::shared_ptr<BT::Blackboard>& blackboard)
// Comment: opens a new C++ code block.
{
  // Task YAML files place all tree variables under `bt.*`; only those
  // parameters are copied into the BehaviorTree.CPP blackboard.
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto bt_parameters = node->list_parameters({"bt"}, 10);
  // Comment: assigns or initializes a value used by the BT runtime.
  int loaded_count = 0;

  // Comment: iterates over the selected elements or indexes.
  for (const auto& parameter_name : bt_parameters.names) {
    // Comment: assigns or initializes a value used by the BT runtime.
    constexpr const char* bt_prefix = "bt.";
    // Comment: evaluates a condition and chooses the branch to run.
    if (parameter_name.rfind(bt_prefix, 0) != 0) {
      // Comment: executes this BT logic statement in C++.
      continue;
    // Comment: closes the current C++ code block.
    }

    // Blackboard key without the "bt." prefix.
    // Comment: assigns or initializes a value used by the BT runtime.
    const auto blackboard_key = parameter_name.substr(std::string(bt_prefix).size());
    // Comment: assigns or initializes a value used by the BT runtime.
    const auto parameter = node->get_parameter(parameter_name);
    // Comment: selects a branch based on the given value.
    switch (parameter.get_type()) {
      // Comment: handles a specific value in the switch statement.
      case rclcpp::ParameterType::PARAMETER_STRING:
        // Comment: executes this BT logic statement in C++.
        blackboard->set(blackboard_key, parameter.as_string());
        // Comment: executes this BT logic statement in C++.
        ++loaded_count;
        // Comment: terminates the current loop or switch branch.
        break;
      // Comment: handles a specific value in the switch statement.
      case rclcpp::ParameterType::PARAMETER_DOUBLE:
        // Comment: executes this BT logic statement in C++.
        blackboard->set(blackboard_key, parameter.as_double());
        // Comment: executes this BT logic statement in C++.
        ++loaded_count;
        // Comment: terminates the current loop or switch branch.
        break;
      // Comment: handles a specific value in the switch statement.
      case rclcpp::ParameterType::PARAMETER_INTEGER:
        // Comment: executes this BT logic statement in C++.
        blackboard->set(blackboard_key, static_cast<int>(parameter.as_int()));
        // Comment: executes this BT logic statement in C++.
        ++loaded_count;
        // Comment: terminates the current loop or switch branch.
        break;
      // Comment: handles a specific value in the switch statement.
      case rclcpp::ParameterType::PARAMETER_BOOL:
        // Comment: executes this BT logic statement in C++.
        blackboard->set(blackboard_key, parameter.as_bool());
        // Comment: executes this BT logic statement in C++.
        ++loaded_count;
        // Comment: terminates the current loop or switch branch.
        break;
      // Comment: handles the case not covered by the other branches.
      default:
        // Comment: writes a diagnostic message to the ROS2 logger.
        RCLCPP_WARN(
          // Comment: executes this BT logic statement in C++.
          node->get_logger(),
          // Comment: executes this BT logic statement in C++.
          "Skipping unsupported BT parameter '%s' of type '%s'.",
          // Comment: executes this BT logic statement in C++.
          parameter_name.c_str(),
          // Comment: executes this BT logic statement in C++.
          parameter.get_type_name().c_str());
        // Comment: terminates the current loop or switch branch.
        break;
    // Comment: closes the current C++ code block.
    }
  // Comment: closes the current C++ code block.
  }

  // Comment: writes a diagnostic message to the ROS2 logger.
  RCLCPP_INFO(node->get_logger(), "Loaded %d BT blackboard parameter(s) from the 'bt.*' namespace.", loaded_count);
// Comment: closes the current C++ code block.
}

// Comment: closes the current C++ code block.
}  // namespace

/**
 * @brief Runs the ROS2 node that loads, registers, and ticks the LeRobot BT.
 *
 * @param argc Process argument count forwarded to rclcpp.
 * @param argv Process argument vector forwarded to rclcpp.
 * @return 0 when the tree finishes with SUCCESS, 1 for FAILURE.
 */
// Comment: executes this BT logic statement in C++.
int main(int argc, char** argv)
// Comment: opens a new C++ code block.
{
  // Comment: executes this BT logic statement in C++.
  rclcpp::init(argc, argv);

  // Runtime parameters:
  // - which XML tree to load
  // - where the BT sends skill/gate commands
  // - where the BT polls VLM state
  // - BT tick period
  // - whether to publish to Groot
  // The ROS2 node hosts parameters, logger, and service access for BT leaf nodes.
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto node_options = rclcpp::NodeOptions()
                              // Comment: executes this BT logic statement in C++.
                              .allow_undeclared_parameters(true)
                              // Comment: executes this BT logic statement in C++.
                              .automatically_declare_parameters_from_overrides(true);
  // Comment: assigns or initializes a value used by the BT runtime.
  auto node = std::make_shared<rclcpp::Node>("lerobot_bt_runner", node_options);
  // Path to the behavior tree XML file.
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto tree_xml_path = declareOrGetParameter<std::string>(node, "tree_xml_path", default_tree_xml_path());
  // ROS2 service called by leaf nodes to run robot skills.
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto bt_command_service = declareOrGetParameter<std::string>(node, "bt_command_service", "/lerobot_bt/run");
  // ROS2 service used to query VLM state (gates/decisions).
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto vlm_state_service = declareOrGetParameter<std::string>(node, "vlm_state_service", "/lerobot_bt/vlm_state");
  // BT tick period.
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto tick_ms = declareOrGetParameter<int>(node, "tick_ms", 100);
  // Enables the Groot publisher (BT graphical monitoring).
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto enable_groot = declareOrGetParameter<bool>(node, "enable_groot_publisher", true);
  // Comment: assigns or initializes a value used by the BT runtime.
  const auto groot_port = declareOrGetParameter<int>(node, "groot_publisher_port", 1667);

  // Keep default make-sandwich values available when no params file is passed.
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<std::string>(node, "bt.initial_scene_ready_gate", "initial_scene_ready");
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<std::string>(node, "bt.place_first_toast_skill", "place_first_toast");
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<double>(node, "bt.place_first_toast_timeout_s", 120.0);
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<std::string>(node, "bt.pour_ingredient_gate", "pour_ingredient");
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<std::string>(node, "bt.place_second_toast_skill", "place_second_toast");
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<double>(node, "bt.place_second_toast_timeout_s", 30.0);
  // Comment: executes this BT logic statement in C++.
  declareOrGetParameter<std::string>(node, "bt.second_toast_placed_gate", "second_toast_placed");

  // ---- Merged leaves: one node = action + VLM verification ------------
  // These replace the old OpenVLMGate + WaitForVLMVerdict and
  // RunRobotSkill + WaitForVLMVerdict pairs.
  // Comment: executes this BT logic statement in C++.
  BT::BehaviorTreeFactory factory;
  // Comment: executes this BT logic statement in C++.
  factory.registerBuilder<lerobot_bt_runtime_cpp::AwaitSceneNode>(
    // Comment: executes this BT logic statement in C++.
    "AwaitScene",
    // Comment: executes this BT logic statement in C++.
    [node, bt_command_service, vlm_state_service](
      // Comment: opens a new C++ code block.
      const std::string& instance_name, const BT::NodeConfiguration& config) {
      // Comment: returns the value or status to the caller.
      return std::make_unique<lerobot_bt_runtime_cpp::AwaitSceneNode>(
        // Comment: executes this BT logic statement in C++.
        instance_name, config, node, bt_command_service, vlm_state_service);
    // Comment: executes this BT logic statement in C++.
    });
  // Comment: executes this BT logic statement in C++.
  factory.registerBuilder<lerobot_bt_runtime_cpp::DoSkillNode>(
    // Comment: executes this BT logic statement in C++.
    "DoSkill",
    // Comment: executes this BT logic statement in C++.
    [node, bt_command_service, vlm_state_service](
      // Comment: opens a new C++ code block.
      const std::string& instance_name, const BT::NodeConfiguration& config) {
      // Comment: returns the value or status to the caller.
      return std::make_unique<lerobot_bt_runtime_cpp::DoSkillNode>(
        // Comment: executes this BT logic statement in C++.
        instance_name, config, node, bt_command_service, vlm_state_service);
    // Comment: executes this BT logic statement in C++.
    });

  // Blackboard: shared key/value store across BT nodes (inputs/outputs).
  // Comment: assigns or initializes a value used by the BT runtime.
  auto blackboard = BT::Blackboard::create();
  // Comment: executes this BT logic statement in C++.
  setBtBlackboardEntries(node, blackboard);

  // Loading from file keeps the BT topology editable without recompiling this
  // executable; malformed XML or missing node tags will fail at this point.
  // Instantiate the BT from XML using the factory and populated blackboard.
  // Comment: assigns or initializes a value used by the BT runtime.
  BT::Tree tree = factory.createTreeFromFile(tree_xml_path, blackboard);

// Comment: selects code based on the macros available at compile time.
#if LEROBOT_BT_HAS_GROOT
  // Comment: executes this BT logic statement in C++.
  std::unique_ptr<GrootPublisherT> groot_publisher;
  // Comment: evaluates a condition and chooses the branch to run.
  if (enable_groot) {
    // Comment: opens a protected block to catch C++ exceptions.
    try {
// Comment: selects code based on the macros available at compile time.
#if LEROBOT_BT_HAS_GROOT2_PUBLISHER
      // Comment: assigns or initializes a value used by the BT runtime.
      groot_publisher = std::make_unique<GrootPublisherT>(tree, static_cast<unsigned>(groot_port));
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_INFO(node->get_logger(), "Groot publisher enabled on port %d.", groot_port);
      // Comment: prints copy/paste instructions so the user can attach Groot2.
      RCLCPP_INFO(
        // Comment: executes this BT logic statement in C++.
        node->get_logger(),
        // Comment: executes this BT logic statement in C++.
        "To watch the tree live: open the Groot2 desktop app -> 'Monitor' mode "
        "-> Connect, then enter Server IP '127.0.0.1' (or this machine's IP for "
        "a remote viewer) and Port '%d'.",
        // Comment: executes this BT logic statement in C++.
        groot_port);
// Comment: uses the fallback branch of the compilation configuration.
#else
      // Comment: assigns or initializes a value used by the BT runtime.
      groot_publisher = std::make_unique<GrootPublisherT>(tree);
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_INFO(
        // Comment: executes this BT logic statement in C++.
        node->get_logger(),
        // Comment: executes this BT logic statement in C++.
        "Groot publisher enabled. The 'groot_publisher_port' parameter is only supported with Groot2Publisher.");
// Comment: closes the conditional compilation block.
#endif
    // Comment: opens a new C++ code block.
    } catch (const std::exception& exc) {
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_WARN(
        // Comment: executes this BT logic statement in C++.
        node->get_logger(),
        // Comment: executes this BT logic statement in C++.
        "Could not start Groot publisher: %s. Continuing without Groot monitoring. "
        // Comment: executes this BT logic statement in C++.
        "If this says 'Address already in use', another lerobot_bt_runner may still be running "
        // Comment: assigns or initializes a value used by the BT runtime.
        "or the port is occupied; stop it or pass '-p enable_groot_publisher:=false'.",
        // Comment: executes this BT logic statement in C++.
        exc.what());
      // Comment: executes this BT logic statement in C++.
      groot_publisher.reset();
    // Comment: closes the current C++ code block.
    }
  // Comment: closes the current C++ code block.
  }
// Comment: uses the fallback branch of the compilation configuration.
#else
  // Comment: evaluates a condition and chooses the branch to run.
  if (enable_groot) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_WARN(node->get_logger(), "Groot publisher requested but no compatible BT.CPP publisher header was found.");
  // Comment: closes the current C++ code block.
  }
// Comment: closes the conditional compilation block.
#endif

  // Comment: assigns or initializes a value used by the BT runtime.
  BT::NodeStatus status = BT::NodeStatus::RUNNING;
  // WallRate controls the BT tick frequency.
  // Comment: executes this BT logic statement in C++.
  rclcpp::WallRate rate{std::chrono::milliseconds(tick_ms)};

  // Centralized cleanup to stop BT, publisher, and ROS2 safely.
  // Comment: opens a new C++ code block.
  const auto cleanup = [&](const char* reason) {
    // Comment: assigns or initializes a value used by the BT runtime.
    const bool ros_context_active = rclcpp::ok();
    // Comment: evaluates a condition and chooses the branch to run.
    if (ros_context_active) {
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_INFO(node->get_logger(), "Stopping behavior tree runner: %s", reason);
    // Comment: closes the current C++ code block.
    }
    // Comment: opens a protected block to catch C++ exceptions.
    try {
      // Comment: executes this BT logic statement in C++.
      tree.haltTree();
    // Comment: opens a new C++ code block.
    } catch (const std::exception& exc) {
      // Comment: evaluates a condition and chooses the branch to run.
      if (ros_context_active) {
        // Comment: writes a diagnostic message to the ROS2 logger.
        RCLCPP_WARN(node->get_logger(), "Exception while halting behavior tree: %s", exc.what());
      // Comment: closes the current C++ code block.
      }
    // Comment: closes the current C++ code block.
    }

// Comment: selects code based on the macros available at compile time.
#if LEROBOT_BT_HAS_GROOT
    // Comment: opens a protected block to catch C++ exceptions.
    try {
      // Comment: executes this BT logic statement in C++.
      groot_publisher.reset();
    // Comment: opens a new C++ code block.
    } catch (const std::exception& exc) {
      // Comment: evaluates a condition and chooses the branch to run.
      if (ros_context_active) {
        // Comment: writes a diagnostic message to the ROS2 logger.
        RCLCPP_WARN(node->get_logger(), "Exception while stopping Groot publisher: %s", exc.what());
      // Comment: closes the current C++ code block.
      }
    // Comment: closes the current C++ code block.
    }
// Comment: closes the conditional compilation block.
#endif

    // Comment: evaluates a condition and chooses the branch to run.
    if (rclcpp::ok()) {
      // Comment: executes this BT logic statement in C++.
      rclcpp::shutdown();
    // Comment: closes the current C++ code block.
    }
  // Comment: closes the current C++ code block.
  };

  // Comment: opens a protected block to catch C++ exceptions.
  try {
    // Main BT loop: each tick may trigger one service-backed leaf execution.
    // Comment: repeats the block while the condition remains true.
    while (rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
      // Comment: assigns or initializes a value used by the BT runtime.
      status = tree.tickOnce();
      // Comment: evaluates a condition and chooses the branch to run.
      if (rclcpp::ok()) {
        // Comment: executes this BT logic statement in C++.
        rclcpp::spin_some(node);
      // Comment: closes the current C++ code block.
      }
      // Comment: executes this BT logic statement in C++.
      rate.sleep();
    // Comment: closes the current C++ code block.
    }

    // Comment: evaluates a condition and chooses the branch to run.
    if (rclcpp::ok()) {
      // Comment: executes this BT logic statement in C++.
      rclcpp::spin_some(node);
    // Comment: closes the current C++ code block.
    }
  // Comment: opens a new C++ code block.
  } catch (const std::exception& exc) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(node->get_logger(), "Behavior tree runner caught exception: %s", exc.what());
    // Comment: executes this BT logic statement in C++.
    cleanup("exception");
    // Comment: returns the value or status to the caller.
    return 1;
  // Comment: closes the current C++ code block.
  }

  // Comment: evaluates a condition and chooses the branch to run.
  if (!rclcpp::ok() && status == BT::NodeStatus::RUNNING) {
    // Comment: executes this BT logic statement in C++.
    cleanup("interrupt requested");
    // Comment: returns the value or status to the caller.
    return 130;
  // Comment: closes the current C++ code block.
  }
  // Comment: evaluates a condition and chooses the branch to run.
  if (status == BT::NodeStatus::SUCCESS) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_INFO(node->get_logger(), "Behavior tree completed with SUCCESS.");
    // Comment: executes this BT logic statement in C++.
    cleanup("tree completed with SUCCESS");
    // Comment: returns the value or status to the caller.
    return 0;
  // Comment: closes the current C++ code block.
  }

  // Comment: writes a diagnostic message to the ROS2 logger.
  RCLCPP_ERROR(node->get_logger(), "Behavior tree completed with FAILURE.");
  // Comment: executes this BT logic statement in C++.
  cleanup("tree completed with FAILURE");
  // Comment: returns the value or status to the caller.
  return 1;
// Comment: closes the current C++ code block.
}
