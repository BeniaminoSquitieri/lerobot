#pragma once

// BT leaf node declaration.
//
// Flow role:
// 1. The XML tree instantiates this node.
// 2. On tick, the node sends a ROS2 service request to the Python server.
// 3. The node returns RUNNING until the reply arrives.
// 4. The reply is converted into BT SUCCESS/FAILURE.

#include <chrono>
#include <memory>
#include <string>

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

#include <sandwich_bt_interfaces/srv/run_named_command.hpp>

namespace sandwich_bt_runtime_cpp
{

class RunNamedCommandNode : public BT::StatefulActionNode
{
public:
  using ServiceT = sandwich_bt_interfaces::srv::RunNamedCommand;

  RunNamedCommandNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& service_name);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  // Shared ROS2 node used to talk to the Python execution server.
  rclcpp::Node::SharedPtr ros_node_;
  rclcpp::Client<ServiceT>::SharedPtr client_;
  std::string service_name_;
  rclcpp::Client<ServiceT>::SharedFuture future_;
  bool request_pending_{false};
};

}  // namespace sandwich_bt_runtime_cpp
