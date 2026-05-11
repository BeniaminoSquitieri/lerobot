#pragma once

/**
 * @file run_named_command_node.hpp
 * @brief Declares BehaviorTree.CPP leaves that start robot skills or VLM gates.
 *
 * @details The XML trees use readable tags such as RunRobotSkill and
 * OpenVLMGate. Internally they all send one asynchronous
 * sandwich_bt_interfaces::srv::RunNamedCommand request to the Python execution
 * server, return BT::NodeStatus::RUNNING while the request is in flight, and
 * map the server response back to BT success or failure.
 */

#include <chrono>
#include <memory>
#include <string>

#include <rclcpp/rclcpp.hpp>

#if __has_include(<behaviortree_cpp/action_node.h>)
#include <behaviortree_cpp/action_node.h>
#elif __has_include(<behaviortree_cpp_v3/action_node.h>)
#include <behaviortree_cpp_v3/action_node.h>
#else
#error "BehaviorTree.CPP action_node.h header was not found."
#endif

#include <sandwich_bt_interfaces/srv/run_named_command.hpp>

namespace sandwich_bt_runtime_cpp
{

/**
 * @brief BehaviorTree.CPP stateful action node for executing a named command.
 *
 * @details The node is intentionally thin: BehaviorTree.CPP owns ticking and
 * halting, ROS2 owns service transport, and the Python server owns the actual
 * robot or simulated command execution.
 */
class RunNamedCommandNode : public BT::StatefulActionNode
{
public:
  /// ROS2 service type used to send the command name and receive the outcome.
  using ServiceT = sandwich_bt_interfaces::srv::RunNamedCommand;

  /**
   * @brief Builds a BT node bound to a shared ROS2 node and service name.
   * @param name Runtime instance name assigned by BehaviorTree.CPP.
   * @param config Input/output port configuration supplied by the BT factory.
   * @param ros_node Shared ROS2 node used to create the service client.
   * @param bt_command_service Fully qualified service endpoint to call.
   */
  RunNamedCommandNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& bt_command_service);

  /**
   * @brief Declares the XML input ports consumed by this BT leaf.
   * @return Ports for command kind, command name, and optional timeout.
   */
  static BT::PortsList providedPorts();

  /**
   * @brief Starts one asynchronous service request on the first tick.
   * @return RUNNING when the request was accepted, FAILURE on setup errors.
   */
  BT::NodeStatus onStart() override;

  /**
   * @brief Polls the outstanding service future on later ticks.
   * @return RUNNING while waiting, SUCCESS/FAILURE after the response arrives.
   */
  BT::NodeStatus onRunning() override;

  /// Marks the local request state as halted if BehaviorTree.CPP aborts the leaf.
  void onHalted() override;

protected:
  /**
   * @brief Builds a command node with the ROS command kind fixed by the BT tag.
   */
  RunNamedCommandNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& bt_command_service,
    std::string fixed_kind,
    std::string command_name_port,
    std::string timeout_port);

private:
  rclcpp::Node::SharedPtr ros_node_;            ///< Shared ROS2 node used for logging and service transport.
  rclcpp::Client<ServiceT>::SharedPtr client_;  ///< Client that sends RunNamedCommand requests.
  std::string bt_command_service_;                    ///< Service endpoint name reported in diagnostics.
  std::string fixed_kind_;                      ///< Non-empty when the BT tag fixes the Python command kind.
  std::string command_name_port_;               ///< XML port that provides request.name.
  std::string timeout_port_;                    ///< Optional XML port that provides request.timeout_s.
  rclcpp::Client<ServiceT>::SharedFuture future_;  ///< Future holding the in-flight service response.
  bool request_pending_{false};                 ///< True while a service request is awaiting completion.
};

/**
 * @brief BT leaf that runs one configured robot skill and opens its VLM check.
 */
class RunRobotSkillNode : public RunNamedCommandNode
{
public:
  RunRobotSkillNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& bt_command_service);

  static BT::PortsList providedPorts();
};

/**
 * @brief BT leaf that opens a VLM/manual gate without robot motion.
 */
class OpenVLMGateNode : public RunNamedCommandNode
{
public:
  OpenVLMGateNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& bt_command_service);

  static BT::PortsList providedPorts();
};

/**
 * @brief BT leaf for bring-up trees that mark a skill as completed without motion.
 */
class SimulateRobotSkillNode : public RunNamedCommandNode
{
public:
  SimulateRobotSkillNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& bt_command_service);

  static BT::PortsList providedPorts();
};

}  // namespace sandwich_bt_runtime_cpp
