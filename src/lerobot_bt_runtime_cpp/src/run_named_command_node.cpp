/**
 * @file run_named_command_node.cpp
 * @brief BehaviorTree.CPP node bridging BT leaves to Python command server.
 */
// Comment: includes a dependency required for compilation.
#include "lerobot_bt_runtime_cpp/run_named_command_node.hpp"

// Comment: includes a dependency required for compilation.
#include <exception>
// Comment: includes a dependency required for compilation.
#include <future>
// Comment: includes a dependency required for compilation.
#include <utility>

// Comment: opens or declares the BT package namespace.
namespace lerobot_bt_runtime_cpp
// Comment: opens a new C++ code block.
{

/**
 * @brief Stores the BT and ROS2 dependencies required by the command leaf.
 *
 * The constructor does not send traffic. It only creates a typed service client
 * so that the first BT tick can dispatch the request with XML-provided inputs.
 */
// Comment: executes this BT logic statement in C++.
RunNamedCommandNode::RunNamedCommandNode(
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const BT::NodeConfiguration& config,
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& ros_node,
  // Comment: executes this BT logic statement in C++.
  const std::string& bt_command_service)
// Comment: executes this BT logic statement in C++.
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "", "command_name", "timeout_s")
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
RunNamedCommandNode::RunNamedCommandNode(
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
  std::string timeout_port)
// Comment: executes this BT logic statement in C++.
: BT::StatefulActionNode(name, config),
  // Comment: executes this BT logic statement in C++.
  ros_node_(ros_node),
  // Comment: creates a ROS2 client to call an external service.
  client_(ros_node_->create_client<ServiceT>(bt_command_service)),
  // Comment: executes this BT logic statement in C++.
  bt_command_service_(bt_command_service),
  // Comment: executes this BT logic statement in C++.
  fixed_kind_(std::move(fixed_kind)),
  // Comment: executes this BT logic statement in C++.
  command_name_port_(std::move(command_name_port)),
  // Comment: executes this BT logic statement in C++.
  timeout_port_(std::move(timeout_port))
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

/**
 * @brief Defines the input ports read by the generic command node.
 */
// Comment: executes this BT logic statement in C++.
BT::PortsList RunNamedCommandNode::providedPorts()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return {
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<std::string>("kind"),
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<std::string>("command_name"),
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds")
  // Comment: closes the current C++ code block.
  };
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
RunRobotSkillNode::RunRobotSkillNode(
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const BT::NodeConfiguration& config,
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& ros_node,
  // Comment: executes this BT logic statement in C++.
  const std::string& bt_command_service)
// Comment: executes this BT logic statement in C++.
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "skill", "skill_name", "timeout_s")
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
BT::PortsList RunRobotSkillNode::providedPorts()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return {
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<std::string>("skill_name"),
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds")
  // Comment: closes the current C++ code block.
  };
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
OpenVLMGateNode::OpenVLMGateNode(
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const BT::NodeConfiguration& config,
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& ros_node,
  // Comment: executes this BT logic statement in C++.
  const std::string& bt_command_service)
// Comment: executes this BT logic statement in C++.
: RunNamedCommandNode(name, config, ros_node, bt_command_service, "vlm_gate_pending", "gate_name", "")
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
BT::PortsList OpenVLMGateNode::providedPorts()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return {
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<std::string>("gate_name"),
  // Comment: closes the current C++ code block.
  };
// Comment: closes the current C++ code block.
}

/**
 * @brief Validates inputs, waits briefly for the server, and starts the call.
 */
// Comment: executes this BT logic statement in C++.
BT::NodeStatus RunNamedCommandNode::onStart()
// Comment: opens a new C++ code block.
{
  // Comment: evaluates a condition and chooses the branch to run.
  if (!rclcpp::ok()) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // These variables mirror the XML attributes; missing required inputs mean
  // the tree definition is invalid and should fail loudly during execution.
  // Comment: executes this BT logic statement in C++.
  std::string kind;
  // Comment: executes this BT logic statement in C++.
  std::string name;
  // Comment: assigns or initializes a value used by the BT runtime.
  double timeout_s = 0.0;

  // Comment: evaluates a condition and chooses the branch to run.
  if (!fixed_kind_.empty()) {
    // Comment: assigns or initializes a value used by the BT runtime.
    kind = fixed_kind_;
  // Comment: opens a new C++ code block.
  } else if (!getInput("kind", kind)) {
    // Comment: throws an error to report a problem that cannot be recovered here.
    throw BT::RuntimeError("RunNamedCommand missing required input port 'kind'");
  // Comment: closes the current C++ code block.
  }
  // Comment: evaluates a condition and chooses the branch to run.
  if (!getInput(command_name_port_, name)) {
    // Comment: throws an error to report a problem that cannot be recovered here.
    throw BT::RuntimeError("Command node missing required input port '" + command_name_port_ + "'");
  // Comment: closes the current C++ code block.
  }
  // Comment: evaluates a condition and chooses the branch to run.
  if (!timeout_port_.empty()) {
    // Comment: executes this BT logic statement in C++.
    getInput(timeout_port_, timeout_s);
  // Comment: closes the current C++ code block.
  }

  // Comment: evaluates a condition and chooses the branch to run.
  if (!client_->wait_for_service(std::chrono::seconds(5))) {
    // Comment: evaluates a condition and chooses the branch to run.
    if (!rclcpp::ok()) {
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::RUNNING;
    // Comment: closes the current C++ code block.
    }
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(ros_node_->get_logger(), "Service '%s' not available.", bt_command_service_.c_str());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }

  // The request object is shared because rclcpp keeps it alive until the
  // asynchronous send has been accepted by the middleware.
  // Comment: assigns or initializes a value used by the BT runtime.
  auto request = std::make_shared<ServiceT::Request>();
  // Comment: assigns or initializes a value used by the BT runtime.
  request->kind = kind;
  // Comment: assigns or initializes a value used by the BT runtime.
  request->name = name;
  // Comment: assigns or initializes a value used by the BT runtime.
  request->timeout_s = static_cast<float>(timeout_s);

  // Store the shared future so later ticks can poll without blocking the BT
  // thread; blocking here would freeze the whole control tree.
  // Comment: sends an asynchronous ROS2 request without blocking the BT tick.
  auto future_and_request_id = client_->async_send_request(request);
  // Comment: assigns or initializes a value used by the BT runtime.
  future_ = future_and_request_id.future.share();
  // Comment: assigns or initializes a value used by the BT runtime.
  request_pending_ = true;
  // Comment: writes a diagnostic message to the ROS2 logger.
  RCLCPP_INFO(
    // Comment: executes this BT logic statement in C++.
    ros_node_->get_logger(),
    // Comment: assigns or initializes a value used by the BT runtime.
    "Started command kind='%s' name='%s' timeout=%.2f",
    // Comment: executes this BT logic statement in C++.
    kind.c_str(),
    // Comment: executes this BT logic statement in C++.
    name.c_str(),
    // Comment: executes this BT logic statement in C++.
    timeout_s);
  // Comment: returns the value or status to the caller.
  return BT::NodeStatus::RUNNING;
// Comment: closes the current C++ code block.
}

/**
 * @brief Converts the completed ROS2 future into a BehaviorTree.CPP status.
 */
// Comment: executes this BT logic statement in C++.
BT::NodeStatus RunNamedCommandNode::onRunning()
// Comment: opens a new C++ code block.
{
  // Comment: evaluates a condition and chooses the branch to run.
  if (!rclcpp::ok()) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // Comment: evaluates a condition and chooses the branch to run.
  if (!request_pending_) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }

  // A zero-duration wait is a non-blocking readiness check; this keeps the BT
  // tick loop responsive while the Python side executes the skill.
  // Comment: evaluates a condition and chooses the branch to run.
  if (future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // Comment: opens a protected block to catch C++ exceptions.
  try {
    // Comment: assigns or initializes a value used by the BT runtime.
    auto response = future_.get();
    // Comment: assigns or initializes a value used by the BT runtime.
    request_pending_ = false;
    // Comment: evaluates a condition and chooses the branch to run.
    if (response->success) {
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_INFO(
        // Comment: executes this BT logic statement in C++.
        ros_node_->get_logger(),
        // Comment: assigns or initializes a value used by the BT runtime.
        "Command succeeded status='%s' elapsed=%.2fs message='%s'",
        // Comment: executes this BT logic statement in C++.
        response->status.c_str(),
        // Comment: executes this BT logic statement in C++.
        response->elapsed_s,
        // Comment: executes this BT logic statement in C++.
        response->message.c_str());
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::SUCCESS;
    // Comment: closes the current C++ code block.
    }

    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(
      // Comment: executes this BT logic statement in C++.
      ros_node_->get_logger(),
      // Comment: assigns or initializes a value used by the BT runtime.
      "Command failed status='%s' elapsed=%.2fs message='%s'",
      // Comment: executes this BT logic statement in C++.
      response->status.c_str(),
      // Comment: executes this BT logic statement in C++.
      response->elapsed_s,
      // Comment: executes this BT logic statement in C++.
      response->message.c_str());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: opens a new C++ code block.
  } catch (const std::exception& exc) {
    // Comment: assigns or initializes a value used by the BT runtime.
    request_pending_ = false;
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(ros_node_->get_logger(), "Command future failed with exception: %s", exc.what());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }
// Comment: closes the current C++ code block.
}

/**
 * @brief Clears local pending state when BehaviorTree.CPP aborts this action.
 */
// Comment: executes this BT logic statement in C++.
void RunNamedCommandNode::onHalted()
// Comment: opens a new C++ code block.
{
  // The BT can halt this node, but the server-side command may already be running.
  // Comment: assigns or initializes a value used by the BT runtime.
  request_pending_ = false;
  // Comment: evaluates a condition and chooses the branch to run.
  if (rclcpp::ok()) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_WARN(
      // Comment: executes this BT logic statement in C++.
      ros_node_->get_logger(),
      // Comment: executes this BT logic statement in C++.
      "RunNamedCommand halted while service '%s' may still be executing server-side.",
      // Comment: executes this BT logic statement in C++.
      bt_command_service_.c_str());
  // Comment: closes the current C++ code block.
  }
// Comment: closes the current C++ code block.
}

// Comment: closes the current C++ code block.
}  // namespace lerobot_bt_runtime_cpp
