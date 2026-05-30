/**
 * @file await_scene_node.cpp
 * @brief Merged BT leaves: AwaitScene (gate+verify) and DoSkill (skill+verify).
 */
// Comment: includes a dependency required for compilation.
#include "lerobot_bt_runtime_cpp/await_scene_node.hpp"

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

// =====================================================================
// MergedRunAndVerifyNode – shared two-phase state machine
// =====================================================================

// Comment: executes this BT logic statement in C++.
MergedRunAndVerifyNode::MergedRunAndVerifyNode(
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const BT::NodeConfiguration& config,
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& ros_node,
  // Comment: executes this BT logic statement in C++.
  const std::string& command_service,
  // Comment: executes this BT logic statement in C++.
  const std::string& vlm_service,
  // Comment: executes this BT logic statement in C++.
  std::string fixed_kind)
// Comment: executes this BT logic statement in C++.
: BT::StatefulActionNode(name, config),
  // Comment: executes this BT logic statement in C++.
  ros_node_(ros_node),
  // Comment: creates a ROS2 client to call an external service.
  cmd_client_(ros_node_->create_client<CommandService>(command_service)),
  // Comment: creates a ROS2 client to call an external service.
  vlm_client_(ros_node_->create_client<VlmService>(vlm_service)),
  // Comment: executes this BT logic statement in C++.
  command_service_(command_service),
  // Comment: executes this BT logic statement in C++.
  vlm_service_(vlm_service),
  // Comment: executes this BT logic statement in C++.
  fixed_kind_(std::move(fixed_kind))
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

// ---- Phase 1: send the command ----------------------------------------

// Comment: executes this BT logic statement in C++.
BT::NodeStatus MergedRunAndVerifyNode::onStart()
// Comment: opens a new C++ code block.
{
  // Comment: evaluates a condition and chooses the branch to run.
  if (!rclcpp::ok()) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // Comment: assigns or initializes a value used by the BT runtime.
  check_name_ = readNamePort();

  // Comment: evaluates a condition and chooses the branch to run.
  if (!cmd_client_->wait_for_service(std::chrono::seconds(5))) {
    // Comment: evaluates a condition and chooses the branch to run.
    if (!rclcpp::ok()) {
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::RUNNING;
    // Comment: closes the current C++ code block.
    }
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(ros_node_->get_logger(),
                 // Comment: executes this BT logic statement in C++.
                 "Command service '%s' not available for '%s'.",
                 // Comment: executes this BT logic statement in C++.
                 command_service_.c_str(), check_name_.c_str());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }

  // Comment: assigns or initializes a value used by the BT runtime.
  auto request = std::make_shared<CommandService::Request>();
  // Comment: assigns or initializes a value used by the BT runtime.
  request->kind = fixed_kind_;
  // Comment: assigns or initializes a value used by the BT runtime.
  request->name = check_name_;
  // Comment: assigns or initializes a value used by the BT runtime.
  request->timeout_s = static_cast<float>(readTimeoutPort());

  // Comment: sends an asynchronous ROS2 request without blocking the BT tick.
  auto future_and_id = cmd_client_->async_send_request(request);
  // Comment: assigns or initializes a value used by the BT runtime.
  cmd_future_ = future_and_id.future.share();
  // Comment: assigns or initializes a value used by the BT runtime.
  cmd_pending_ = true;
  // Comment: assigns or initializes a value used by the BT runtime.
  phase_ = MergedPhase::SEND_COMMAND;

  // Comment: writes a diagnostic message to the ROS2 logger.
  RCLCPP_INFO(ros_node_->get_logger(),
              // Comment: assigns or initializes a value used by the BT runtime.
              "Merged node '%s' → sent command kind='%s' name='%s'.",
              // Comment: executes this BT logic statement in C++.
              this->name().c_str(), fixed_kind_.c_str(), check_name_.c_str());
  // Comment: returns the value or status to the caller.
  return BT::NodeStatus::RUNNING;
// Comment: closes the current C++ code block.
}

// ---- Tick: wait for command, then poll VLM ----------------------------

// Comment: executes this BT logic statement in C++.
BT::NodeStatus MergedRunAndVerifyNode::onRunning()
// Comment: opens a new C++ code block.
{
  // Comment: evaluates a condition and chooses the branch to run.
  if (!rclcpp::ok()) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // --- Phase 1: still waiting for the command to finish -----------------
  // Comment: evaluates a condition and chooses the branch to run.
  if (phase_ == MergedPhase::SEND_COMMAND) {
    // Comment: evaluates a condition and chooses the branch to run.
    if (!cmd_pending_) {
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::FAILURE;
    // Comment: closes the current C++ code block.
    }
    // Comment: evaluates a condition and chooses the branch to run.
    if (cmd_future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::RUNNING;
    // Comment: closes the current C++ code block.
    }

    // Comment: opens a protected block to catch C++ exceptions.
    try {
      // Comment: assigns or initializes a value used by the BT runtime.
      auto response = cmd_future_.get();
      // Comment: assigns or initializes a value used by the BT runtime.
      cmd_pending_ = false;

      // Comment: evaluates a condition and chooses the branch to run.
      if (!response->success) {
        // Comment: writes a diagnostic message to the ROS2 logger.
        RCLCPP_ERROR(ros_node_->get_logger(),
                     // Comment: executes this BT logic statement in C++.
                     "Command '%s' failed: %s", check_name_.c_str(), response->message.c_str());
        // Comment: returns the value or status to the caller.
        return BT::NodeStatus::FAILURE;
      // Comment: closes the current C++ code block.
      }

      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_INFO(ros_node_->get_logger(),
                  // Comment: executes this BT logic statement in C++.
                  "Command '%s' completed (%.2fs). Switching to VLM polling.",
                  // Comment: executes this BT logic statement in C++.
                  check_name_.c_str(), response->elapsed_s);
    // Comment: opens a new C++ code block.
    } catch (const std::exception& exc) {
      // Comment: assigns or initializes a value used by the BT runtime.
      cmd_pending_ = false;
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_ERROR(ros_node_->get_logger(),
                   // Comment: executes this BT logic statement in C++.
                   "Command future failed: %s", exc.what());
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::FAILURE;
    // Comment: closes the current C++ code block.
    }

    // Command succeeded → move to VLM polling phase.
    // Comment: evaluates a condition and chooses the branch to run.
    if (!vlm_client_->wait_for_service(std::chrono::seconds(5))) {
      // Comment: evaluates a condition and chooses the branch to run.
      if (!rclcpp::ok()) {
        // Comment: returns the value or status to the caller.
        return BT::NodeStatus::RUNNING;
      // Comment: closes the current C++ code block.
      }
      // Comment: writes a diagnostic message to the ROS2 logger.
      RCLCPP_ERROR(ros_node_->get_logger(),
                   // Comment: executes this BT logic statement in C++.
                   "VLM service '%s' not available.", vlm_service_.c_str());
      // Comment: returns the value or status to the caller.
      return BT::NodeStatus::FAILURE;
    // Comment: closes the current C++ code block.
    }

    // Comment: assigns or initializes a value used by the BT runtime.
    phase_ = MergedPhase::POLL_VLM;
    // Comment: executes this BT logic statement in C++.
    startVlmRequest();
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // --- Phase 2: polling VLM verdict ------------------------------------
  // Comment: evaluates a condition and chooses the branch to run.
  if (!vlm_pending_) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }
  // Comment: evaluates a condition and chooses the branch to run.
  if (vlm_future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // Comment: opens a protected block to catch C++ exceptions.
  try {
    // Comment: assigns or initializes a value used by the BT runtime.
    auto response = vlm_future_.get();
    // Comment: assigns or initializes a value used by the BT runtime.
    vlm_pending_ = false;
    // Comment: returns the value or status to the caller.
    return handleVlmResponse(response);
  // Comment: opens a new C++ code block.
  } catch (const std::exception& exc) {
    // Comment: assigns or initializes a value used by the BT runtime.
    vlm_pending_ = false;
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(ros_node_->get_logger(),
                 // Comment: executes this BT logic statement in C++.
                 "VLM future failed for '%s': %s", check_name_.c_str(), exc.what());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }
// Comment: closes the current C++ code block.
}

// ---- VLM polling helpers ----------------------------------------------

// Comment: executes this BT logic statement in C++.
void MergedRunAndVerifyNode::startVlmRequest()
// Comment: opens a new C++ code block.
{
  // Comment: assigns or initializes a value used by the BT runtime.
  auto request = std::make_shared<VlmService::Request>();
  // Comment: assigns or initializes a value used by the BT runtime.
  request->skill_name = check_name_;
  // Comment: sends an asynchronous ROS2 request without blocking the BT tick.
  auto future_and_id = vlm_client_->async_send_request(request);
  // Comment: assigns or initializes a value used by the BT runtime.
  vlm_future_ = future_and_id.future.share();
  // Comment: assigns or initializes a value used by the BT runtime.
  vlm_pending_ = true;
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
BT::NodeStatus MergedRunAndVerifyNode::handleVlmResponse(
  // Comment: executes this BT logic statement in C++.
  lerobot_bt_interfaces::srv::GetSkillVerification::Response::SharedPtr response)
// Comment: opens a new C++ code block.
{
  // Comment: evaluates a condition and chooses the branch to run.
  if (!response->has_attempt) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(ros_node_->get_logger(),
                 // Comment: executes this BT logic statement in C++.
                 "VLM check '%s' has no recorded attempt: %s",
                 // Comment: executes this BT logic statement in C++.
                 check_name_.c_str(), response->message.c_str());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }

  // Comment: evaluates a condition and chooses the branch to run.
  if (response->status == "SUCCESS") {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_INFO(ros_node_->get_logger(),
                // Comment: executes this BT logic statement in C++.
                "VLM check '%s' SUCCESS (attempt %d): %s",
                // Comment: executes this BT logic statement in C++.
                check_name_.c_str(), response->attempt_id, response->message.c_str());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::SUCCESS;
  // Comment: closes the current C++ code block.
  }

  // Comment: evaluates a condition and chooses the branch to run.
  if (response->status == "FAILURE") {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_ERROR(ros_node_->get_logger(),
                 // Comment: executes this BT logic statement in C++.
                 "VLM check '%s' FAILURE (attempt %d): %s",
                 // Comment: executes this BT logic statement in C++.
                 check_name_.c_str(), response->attempt_id, response->message.c_str());
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::FAILURE;
  // Comment: closes the current C++ code block.
  }

  // RUNNING keeps polling.
  // Comment: executes this BT logic statement in C++.
  const bool waiting = response->status == "RUNNING";
  // Comment: evaluates a condition and chooses the branch to run.
  if (waiting) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_DEBUG(ros_node_->get_logger(),
                 // Comment: assigns or initializes a value used by the BT runtime.
                 "VLM check '%s' waiting (attempt %d, status='%s'): %s",
                 // Comment: executes this BT logic statement in C++.
                 check_name_.c_str(), response->attempt_id,
                 // Comment: executes this BT logic statement in C++.
                 response->status.c_str(), response->message.c_str());
    // Comment: executes this BT logic statement in C++.
    startVlmRequest();
    // Comment: returns the value or status to the caller.
    return BT::NodeStatus::RUNNING;
  // Comment: closes the current C++ code block.
  }

  // Comment: writes a diagnostic message to the ROS2 logger.
  RCLCPP_ERROR(ros_node_->get_logger(),
               // Comment: executes this BT logic statement in C++.
               "VLM check '%s' unexpected status '%s': %s",
               // Comment: executes this BT logic statement in C++.
               check_name_.c_str(), response->status.c_str(), response->message.c_str());
  // Comment: returns the value or status to the caller.
  return BT::NodeStatus::FAILURE;
// Comment: closes the current C++ code block.
}

// ---- Cleanup ----------------------------------------------------------

// Comment: executes this BT logic statement in C++.
void MergedRunAndVerifyNode::onHalted()
// Comment: opens a new C++ code block.
{
  // Comment: assigns or initializes a value used by the BT runtime.
  cmd_pending_ = false;
  // Comment: assigns or initializes a value used by the BT runtime.
  vlm_pending_ = false;
  // Comment: evaluates a condition and chooses the branch to run.
  if (rclcpp::ok()) {
    // Comment: writes a diagnostic message to the ROS2 logger.
    RCLCPP_WARN(ros_node_->get_logger(),
                // Comment: executes this BT logic statement in C++.
                "Merged node '%s' halted.", this->name().c_str());
  // Comment: closes the current C++ code block.
  }
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
double MergedRunAndVerifyNode::readTimeoutPort()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return 0.0;  // gates have no timeout
// Comment: closes the current C++ code block.
}

// =====================================================================
// AwaitSceneNode
// =====================================================================

// Comment: executes this BT logic statement in C++.
AwaitSceneNode::AwaitSceneNode(
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const BT::NodeConfiguration& config,
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& ros_node,
  // Comment: executes this BT logic statement in C++.
  const std::string& command_service,
  // Comment: executes this BT logic statement in C++.
  const std::string& vlm_service)
// Comment: executes this BT logic statement in C++.
: MergedRunAndVerifyNode(name, config, ros_node, command_service, vlm_service, "vlm_gate")
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
BT::PortsList AwaitSceneNode::providedPorts()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return {
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<std::string>("scene_name"),
  // Comment: closes the current C++ code block.
  };
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
std::string AwaitSceneNode::readNamePort()
// Comment: opens a new C++ code block.
{
  // Comment: executes this BT logic statement in C++.
  std::string name;
  // Comment: evaluates a condition and chooses the branch to run.
  if (!getInput("scene_name", name)) {
    // Comment: throws an error to report a problem that cannot be recovered here.
    throw BT::RuntimeError("AwaitScene missing required input port 'scene_name'");
  // Comment: closes the current C++ code block.
  }
  // Comment: returns the value or status to the caller.
  return name;
// Comment: closes the current C++ code block.
}

// =====================================================================
// DoSkillNode
// =====================================================================

// Comment: executes this BT logic statement in C++.
DoSkillNode::DoSkillNode(
  // Comment: executes this BT logic statement in C++.
  const std::string& name,
  // Comment: executes this BT logic statement in C++.
  const BT::NodeConfiguration& config,
  // Comment: executes this BT logic statement in C++.
  const rclcpp::Node::SharedPtr& ros_node,
  // Comment: executes this BT logic statement in C++.
  const std::string& command_service,
  // Comment: executes this BT logic statement in C++.
  const std::string& vlm_service)
// Comment: executes this BT logic statement in C++.
: MergedRunAndVerifyNode(name, config, ros_node, command_service, vlm_service, "skill")
// Comment: opens a new C++ code block.
{
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
BT::PortsList DoSkillNode::providedPorts()
// Comment: opens a new C++ code block.
{
  // Comment: returns the value or status to the caller.
  return {
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<std::string>("skill_name"),
    // Comment: executes this BT logic statement in C++.
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds"),
  // Comment: closes the current C++ code block.
  };
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
std::string DoSkillNode::readNamePort()
// Comment: opens a new C++ code block.
{
  // Comment: executes this BT logic statement in C++.
  std::string name;
  // Comment: evaluates a condition and chooses the branch to run.
  if (!getInput("skill_name", name)) {
    // Comment: throws an error to report a problem that cannot be recovered here.
    throw BT::RuntimeError("DoSkill missing required input port 'skill_name'");
  // Comment: closes the current C++ code block.
  }
  // Comment: returns the value or status to the caller.
  return name;
// Comment: closes the current C++ code block.
}

// Comment: executes this BT logic statement in C++.
double DoSkillNode::readTimeoutPort()
// Comment: opens a new C++ code block.
{
  // Comment: assigns or initializes a value used by the BT runtime.
  double timeout = 0.0;
  // Comment: executes this BT logic statement in C++.
  getInput("timeout_s", timeout);
  // Comment: returns the value or status to the caller.
  return timeout;
// Comment: closes the current C++ code block.
}

// Comment: closes the current C++ code block.
}  // namespace lerobot_bt_runtime_cpp
