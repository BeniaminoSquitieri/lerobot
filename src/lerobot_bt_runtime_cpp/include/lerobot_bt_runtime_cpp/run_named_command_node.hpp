// Comment: executes this BT logic statement in C++.
#pragma once

/**
 * @file run_named_command_node.hpp
 * @brief Declares BehaviorTree.CPP leaves that start robot skills or VLM gates.
 *
 * @details The XML trees use readable tags such as RunRobotSkill and
 * OpenVLMGate. Internally they all send one asynchronous
 * lerobot_bt_interfaces::srv::RunNamedCommand request to the Python execution
 * server, return BT::NodeStatus::RUNNING while the request is in flight, and
 * map the server response back to BT success or failure.
 */

// Comment: includes a dependency required for compilation.
#include <chrono>
// Comment: includes a dependency required for compilation.
#include <memory>
// Comment: includes a dependency required for compilation.
#include <string>

// Comment: includes a dependency required for compilation.
#include <rclcpp/rclcpp.hpp>

// Comment: selects code based on the macros available at compile time.
#if __has_include(<behaviortree_cpp/action_node.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp/action_node.h>
// Comment: selects code based on the macros available at compile time.
#elif __has_include(<behaviortree_cpp_v3/action_node.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp_v3/action_node.h>
// Comment: uses the fallback branch of the compilation configuration.
#else
// Comment: forces a compilation error when a required dependency is missing.
#error "BehaviorTree.CPP action_node.h header was not found."
// Comment: closes the conditional compilation block.
#endif

// Comment: includes a dependency required for compilation.
#include <lerobot_bt_interfaces/srv/run_named_command.hpp>

// Comment: opens or declares the BT package namespace.
namespace lerobot_bt_runtime_cpp
// Comment: opens a new C++ code block.
{

/**
 * @brief BehaviorTree.CPP stateful action node for executing a named command.
 *
 * @details The node is intentionally thin: BehaviorTree.CPP owns ticking and
 * halting, ROS2 owns service transport, and the Python server owns the actual
 * robot command execution or VLM/manual gate handling.
 */
// Comment: declares a C++ class for the BT runtime.
class RunNamedCommandNode : public BT::StatefulActionNode
// Comment: opens a new C++ code block.
{
// Comment: changes the visibility of the class members.
public:
  /// ROS2 service type used to send the command name and receive the outcome.
  // Comment: defines a type alias or imports a symbol into the current namespace.
  using ServiceT = lerobot_bt_interfaces::srv::RunNamedCommand;

  /**
   * @brief Builds a BT node bound to a shared ROS2 node and service name.
   * @param name Runtime instance name assigned by BehaviorTree.CPP.
   * @param config Input/output port configuration supplied by the BT factory.
   * @param ros_node Shared ROS2 node used to create the service client.
   * @param bt_command_service Fully qualified service endpoint to call.
   */
  // Comment: executes this BT logic statement in C++.
  RunNamedCommandNode(
    // Comment: executes this BT logic statement in C++.
    const std::string& name,
    // Comment: executes this BT logic statement in C++.
    const BT::NodeConfiguration& config,
    // Comment: executes this BT logic statement in C++.
    const rclcpp::Node::SharedPtr& ros_node,
    // Comment: executes this BT logic statement in C++.
    const std::string& bt_command_service);

  /**
   * @brief Declares the XML input ports consumed by this BT leaf.
   * @return Ports for command kind, command name, and optional timeout.
   */
  // Comment: executes this BT logic statement in C++.
  static BT::PortsList providedPorts();

  /**
   * @brief Starts one asynchronous service request on the first tick.
   * @return RUNNING when the request was accepted, FAILURE on setup errors.
   */
  // Comment: executes this BT logic statement in C++.
  BT::NodeStatus onStart() override;

  /**
   * @brief Polls the outstanding service future on later ticks.
   * @return RUNNING while waiting, SUCCESS/FAILURE after the response arrives.
   */
  // Comment: executes this BT logic statement in C++.
  BT::NodeStatus onRunning() override;

  /// Marks the local request state as halted if BehaviorTree.CPP aborts the leaf.
  // Comment: executes this BT logic statement in C++.
  void onHalted() override;

// Comment: changes the visibility of the class members.
protected:
  /**
   * @brief Builds a command node with the ROS command kind fixed by the BT tag.
   */
  // Comment: executes this BT logic statement in C++.
  RunNamedCommandNode(
    // Comment: executes this BT logic statement in C++.
    const std::string& name,
    // Comment: executes this BT logic statement in C++.
    const BT::NodeConfiguration& config,
    // Comment: executes this BT logic statement in C++.
    const rclcpp::Node::SharedPtr& ros_node,
    // Comment: executes this BT logic statement in C++.
    const std::string& bt_command_service,
    // Comment: executes this BT logic statement in C++.
    std::string fixed_kind,
    // Comment: executes this BT logic statement in C++.
    std::string command_name_port,
    // Comment: executes this BT logic statement in C++.
    std::string timeout_port);

// Comment: changes the visibility of the class members.
private:
  // Comment: executes this BT logic statement in C++.
  rclcpp::Node::SharedPtr ros_node_;            ///< Shared ROS2 node used for logging and service transport.
  // Comment: executes this BT logic statement in C++.
  rclcpp::Client<ServiceT>::SharedPtr client_;  ///< Client that sends RunNamedCommand requests.
  // Comment: executes this BT logic statement in C++.
  std::string bt_command_service_;                    ///< Service endpoint name reported in diagnostics.
  // Comment: executes this BT logic statement in C++.
  std::string fixed_kind_;                      ///< Non-empty when the BT tag fixes the Python command kind.
  // Comment: executes this BT logic statement in C++.
  std::string command_name_port_;               ///< XML port that provides request.name.
  // Comment: executes this BT logic statement in C++.
  std::string timeout_port_;                    ///< Optional XML port that provides request.timeout_s.
  // Comment: executes this BT logic statement in C++.
  rclcpp::Client<ServiceT>::SharedFuture future_;  ///< Future holding the in-flight service response.
  // Comment: executes this BT logic statement in C++.
  bool request_pending_{false};                 ///< True while a service request is awaiting completion.
// Comment: closes the current C++ code block.
};

/**
 * @brief BT leaf that runs one configured robot skill and opens its VLM check.
 */
// Comment: declares a C++ class for the BT runtime.
class RunRobotSkillNode : public RunNamedCommandNode
// Comment: opens a new C++ code block.
{
// Comment: changes the visibility of the class members.
public:
  // Comment: executes this BT logic statement in C++.
  RunRobotSkillNode(
    // Comment: executes this BT logic statement in C++.
    const std::string& name,
    // Comment: executes this BT logic statement in C++.
    const BT::NodeConfiguration& config,
    // Comment: executes this BT logic statement in C++.
    const rclcpp::Node::SharedPtr& ros_node,
    // Comment: executes this BT logic statement in C++.
    const std::string& bt_command_service);

  // Comment: executes this BT logic statement in C++.
  static BT::PortsList providedPorts();
// Comment: closes the current C++ code block.
};

/**
 * @brief BT leaf that opens a VLM/manual gate without robot motion.
 */
// Comment: declares a C++ class for the BT runtime.
class OpenVLMGateNode : public RunNamedCommandNode
// Comment: opens a new C++ code block.
{
// Comment: changes the visibility of the class members.
public:
  // Comment: executes this BT logic statement in C++.
  OpenVLMGateNode(
    // Comment: executes this BT logic statement in C++.
    const std::string& name,
    // Comment: executes this BT logic statement in C++.
    const BT::NodeConfiguration& config,
    // Comment: executes this BT logic statement in C++.
    const rclcpp::Node::SharedPtr& ros_node,
    // Comment: executes this BT logic statement in C++.
    const std::string& bt_command_service);

  // Comment: executes this BT logic statement in C++.
  static BT::PortsList providedPorts();
// Comment: closes the current C++ code block.
};

// Comment: closes the current C++ code block.
}  // namespace lerobot_bt_runtime_cpp
