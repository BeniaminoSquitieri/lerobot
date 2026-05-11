/**
 * @file run_named_command_node.cpp
 * @brief BehaviorTree.CPP node bridging BT leaves to Python command server.
 */
#include "sandwich_bt_runtime_cpp/run_named_command_node.hpp"

#include <exception>
#include <future>
#include <utility>

namespace sandwich_bt_runtime_cpp
{

/**
 * @brief Stores the BT and ROS2 dependencies required by the command leaf.
 *
 * The constructor does not send traffic. It only creates a typed service client
 * so that the first BT tick can dispatch the request with XML-provided inputs.
 */
RunNamedCommandNode::RunNamedCommandNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& bt_command_service)
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "", "command_name", "timeout_s")
{
}

RunNamedCommandNode::RunNamedCommandNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& bt_command_service,
  std::string fixed_kind,
  std::string command_name_port,
  std::string timeout_port)
: BT::StatefulActionNode(name, config),
  ros_node_(ros_node),
  client_(ros_node_->create_client<ServiceT>(bt_command_service)),
  bt_command_service_(bt_command_service),
  fixed_kind_(std::move(fixed_kind)),
  command_name_port_(std::move(command_name_port)),
  timeout_port_(std::move(timeout_port))
{
}

/**
 * @brief Defines the input ports read from legacy command XML elements.
 */
BT::PortsList RunNamedCommandNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("kind"),
    BT::InputPort<std::string>("command_name"),
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds")
  };
}

RunRobotSkillNode::RunRobotSkillNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& bt_command_service)
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "skill", "skill_name", "timeout_s")
{
}

BT::PortsList RunRobotSkillNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("skill_name"),
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds")
  };
}

OpenVLMGateNode::OpenVLMGateNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& bt_command_service)
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "vlm_gate_pending", "gate_name", "")
{
}

BT::PortsList OpenVLMGateNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("gate_name"),
  };
}

SimulateRobotSkillNode::SimulateRobotSkillNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& bt_command_service)
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "no_motion_skill", "skill_name", "")
{
}

BT::PortsList SimulateRobotSkillNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("skill_name"),
  };
}

/**
 * @brief Validates inputs, waits briefly for the server, and starts the call.
 */
BT::NodeStatus RunNamedCommandNode::onStart()
{
  if (!rclcpp::ok()) {
    return BT::NodeStatus::RUNNING;
  }

  // These variables mirror the XML attributes; missing required inputs mean
  // the tree definition is invalid and should fail loudly during execution.
  std::string kind;
  std::string name;
  double timeout_s = 0.0;

  if (!fixed_kind_.empty()) {
    kind = fixed_kind_;
  } else if (!getInput("kind", kind)) {
    throw BT::RuntimeError("RunNamedCommand missing required input port 'kind'");
  }
  if (!getInput(command_name_port_, name)) {
    throw BT::RuntimeError("Command node missing required input port '" + command_name_port_ + "'");
  }
  if (!timeout_port_.empty()) {
    getInput(timeout_port_, timeout_s);
  }

  if (!client_->wait_for_service(std::chrono::seconds(5))) {
    if (!rclcpp::ok()) {
      return BT::NodeStatus::RUNNING;
    }
    RCLCPP_ERROR(ros_node_->get_logger(), "Service '%s' not available.", bt_command_service_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  // The request object is shared because rclcpp keeps it alive until the
  // asynchronous send has been accepted by the middleware.
  auto request = std::make_shared<ServiceT::Request>();
  request->kind = kind;
  request->name = name;
  request->timeout_s = static_cast<float>(timeout_s);

  // Store the shared future so later ticks can poll without blocking the BT
  // thread; blocking here would freeze the whole control tree.
  auto future_and_request_id = client_->async_send_request(request);
  future_ = future_and_request_id.future.share();
  request_pending_ = true;
  RCLCPP_INFO(
    ros_node_->get_logger(),
    "Started command kind='%s' name='%s' timeout=%.2f",
    kind.c_str(),
    name.c_str(),
    timeout_s);
  return BT::NodeStatus::RUNNING;
}

/**
 * @brief Converts the completed ROS2 future into a BehaviorTree.CPP status.
 */
BT::NodeStatus RunNamedCommandNode::onRunning()
{
  if (!rclcpp::ok()) {
    return BT::NodeStatus::RUNNING;
  }

  if (!request_pending_) {
    return BT::NodeStatus::FAILURE;
  }

  // A zero-duration wait is a non-blocking readiness check; this keeps the BT
  // tick loop responsive while the Python side executes the skill.
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

/**
 * @brief Clears local pending state when BehaviorTree.CPP aborts this action.
 */
void RunNamedCommandNode::onHalted()
{
  // The BT can halt this node, but the server-side command may already be running.
  request_pending_ = false;
  if (rclcpp::ok()) {
    RCLCPP_WARN(
      ros_node_->get_logger(),
      "RunNamedCommand halted while service '%s' may still be executing server-side.",
      bt_command_service_.c_str());
  }
}

}  // namespace sandwich_bt_runtime_cpp
