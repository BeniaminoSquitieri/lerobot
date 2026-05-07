#pragma once

/**
 * @file verify_skill_outcome_node.hpp
 * @brief Declares the BehaviorTree.CPP leaf that waits for skill verification.
 *
 * @details After a robot skill returns, this BT node repeatedly asks the Python
 * verification registry for the latest result of that skill attempt. A SUCCESS
 * verification lets the tree continue, a FAILURE verification triggers XML
 * retry/failure logic, and a PENDING verification keeps the node RUNNING.
 */

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

#include <sandwich_bt_interfaces/srv/get_skill_verification.hpp>

namespace sandwich_bt_runtime_cpp
{

/**
 * @brief BehaviorTree.CPP stateful action node for polling skill outcome state.
 *
 * @details The node keeps no image-processing or policy logic locally. It only
 * queries the ROS2 GetSkillVerification service and translates the returned
 * status string into BehaviorTree.CPP control-flow statuses.
 */
class VerifySkillOutcomeNode : public BT::StatefulActionNode
{
public:
  /// ROS2 service type used to fetch the latest verification snapshot.
  using ServiceT = sandwich_bt_interfaces::srv::GetSkillVerification;

  /**
   * @brief Builds a verification leaf bound to a shared ROS2 node and service.
   * @param name Runtime instance name assigned by BehaviorTree.CPP.
   * @param config Input/output port configuration supplied by the BT factory.
   * @param ros_node Shared ROS2 node used to create the service client.
   * @param service_name Fully qualified verification service endpoint to call.
   */
  VerifySkillOutcomeNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& service_name);

  /**
   * @brief Declares the XML input port consumed by this BT leaf.
   * @return A single required skill_name input port.
   */
  static BT::PortsList providedPorts();

  /**
   * @brief Reads the skill name and starts the first verification request.
   * @return RUNNING after dispatch, FAILURE if the service cannot be reached.
   */
  BT::NodeStatus onStart() override;

  /**
   * @brief Polls verification responses and re-requests while status is PENDING.
   * @return RUNNING, SUCCESS, or FAILURE according to the verification state.
   */
  BT::NodeStatus onRunning() override;

  /// Stops local polling if BehaviorTree.CPP halts this leaf.
  void onHalted() override;

private:
  /// Sends one asynchronous GetSkillVerification request for skill_name_.
  void startRequest();

  rclcpp::Node::SharedPtr ros_node_;            ///< Shared ROS2 node used for logging and service transport.
  rclcpp::Client<ServiceT>::SharedPtr client_;  ///< Client that sends GetSkillVerification requests.
  std::string service_name_;                    ///< Service endpoint name reported in diagnostics.
  std::string skill_name_;                      ///< Skill currently being verified.
  rclcpp::Client<ServiceT>::SharedFuture future_;  ///< Future holding the in-flight verification response.
  bool request_pending_{false};                 ///< True while a verification request is awaiting completion.
};

}  // namespace sandwich_bt_runtime_cpp
