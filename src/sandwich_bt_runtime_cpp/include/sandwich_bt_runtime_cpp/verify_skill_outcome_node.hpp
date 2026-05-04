#pragma once

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

class VerifySkillOutcomeNode : public BT::StatefulActionNode
{
public:
  using ServiceT = sandwich_bt_interfaces::srv::GetSkillVerification;

  VerifySkillOutcomeNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& service_name);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  void startRequest();

  rclcpp::Node::SharedPtr ros_node_;
  rclcpp::Client<ServiceT>::SharedPtr client_;
  std::string service_name_;
  std::string skill_name_;
  rclcpp::Client<ServiceT>::SharedFuture future_;
  bool request_pending_{false};
};

}  // namespace sandwich_bt_runtime_cpp
