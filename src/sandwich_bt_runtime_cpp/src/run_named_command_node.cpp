#include "sandwich_bt_runtime_cpp/run_named_command_node.hpp"

// BT leaf node implementation.
//
// This file is the direct bridge between:
// - BehaviorTree.CPP ticking logic
// - the Python ROS2 skill server

#include <exception>
#include <future>

namespace sandwich_bt_runtime_cpp
{

RunNamedCommandNode::RunNamedCommandNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& service_name)
: BT::StatefulActionNode(name, config),
  ros_node_(ros_node),
  client_(ros_node_->create_client<ServiceT>(service_name)),
  service_name_(service_name)
{
}

BT::PortsList RunNamedCommandNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("kind"),
    BT::InputPort<std::string>("command_name"),
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds")
  };
}

BT::NodeStatus RunNamedCommandNode::onStart()
{
  // First BT tick for this node:
  // build the service request and start the asynchronous call.
  std::string kind;
  std::string name;
  double timeout_s = 0.0;

  if (!getInput("kind", kind)) {
    throw BT::RuntimeError("RunNamedCommand missing required input port 'kind'");
  }
  if (!getInput("command_name", name)) {
    throw BT::RuntimeError("RunNamedCommand missing required input port 'command_name'");
  }
  getInput("timeout_s", timeout_s);

  if (!client_->wait_for_service(std::chrono::seconds(1))) {
    RCLCPP_ERROR(ros_node_->get_logger(), "Service '%s' not available.", service_name_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  auto request = std::make_shared<ServiceT::Request>();
  request->kind = kind;
  request->name = name;
  request->timeout_s = static_cast<float>(timeout_s);

  future_ = client_->async_send_request(request);
  request_pending_ = true;
  RCLCPP_INFO(
    ros_node_->get_logger(),
    "Started command kind='%s' name='%s' timeout=%.2f",
    kind.c_str(),
    name.c_str(),
    timeout_s);
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus RunNamedCommandNode::onRunning()
{
  // Subsequent BT ticks:
  // keep returning RUNNING until the Python server replies.
  if (!request_pending_) {
    return BT::NodeStatus::FAILURE;
  }

  if (future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
    return BT::NodeStatus::RUNNING;
  }

  try {
    auto response = future_.get();
    request_pending_ = false;
    if (response->success) {
      RCLCPP_INFO(
        ros_node_->get_logger(),
        "Command succeeded status='%s' elapsed=%.2fs message='%s'",
        response->status.c_str(),
        response->elapsed_s,
        response->message.c_str());
      return BT::NodeStatus::SUCCESS;
    }

    RCLCPP_ERROR(
      ros_node_->get_logger(),
      "Command failed status='%s' elapsed=%.2fs message='%s'",
      response->status.c_str(),
      response->elapsed_s,
      response->message.c_str());
    return BT::NodeStatus::FAILURE;
  } catch (const std::exception& exc) {
    request_pending_ = false;
    RCLCPP_ERROR(ros_node_->get_logger(), "Command future failed with exception: %s", exc.what());
    return BT::NodeStatus::FAILURE;
  }
}

void RunNamedCommandNode::onHalted()
{
  // The BT can halt this node, but the server-side command may already be running.
  request_pending_ = false;
  RCLCPP_WARN(
    ros_node_->get_logger(),
    "RunNamedCommand halted while service '%s' may still be executing server-side.",
    service_name_.c_str());
}

}  // namespace sandwich_bt_runtime_cpp
