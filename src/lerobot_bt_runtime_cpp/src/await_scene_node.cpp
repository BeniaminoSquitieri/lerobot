/**
 * @file await_scene_node.cpp
 * @brief Merged BT leaves: AwaitScene (gate+verify) and DoSkill (skill+verify).
 */
#include "lerobot_bt_runtime_cpp/await_scene_node.hpp"

#include <exception>
#include <future>
#include <utility>

namespace lerobot_bt_runtime_cpp
{

// =====================================================================
// MergedRunAndVerifyNode – shared two-phase state machine
// =====================================================================

MergedRunAndVerifyNode::MergedRunAndVerifyNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& command_service,
  const std::string& vlm_service,
  std::string fixed_kind)
: BT::StatefulActionNode(name, config),
  ros_node_(ros_node),
  cmd_client_(ros_node_->create_client<CommandService>(command_service)),
  vlm_client_(ros_node_->create_client<VlmService>(vlm_service)),
  command_service_(command_service),
  vlm_service_(vlm_service),
  fixed_kind_(std::move(fixed_kind))
{
}

// ---- Phase 1: send the command ----------------------------------------

BT::NodeStatus MergedRunAndVerifyNode::onStart()
{
  if (!rclcpp::ok()) {
    return BT::NodeStatus::RUNNING;
  }

  check_name_ = readNamePort();

  if (!cmd_client_->wait_for_service(std::chrono::seconds(5))) {
    if (!rclcpp::ok()) {
      return BT::NodeStatus::RUNNING;
    }
    RCLCPP_ERROR(ros_node_->get_logger(),
                 "Command service '%s' not available for '%s'.",
                 command_service_.c_str(), check_name_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  auto request = std::make_shared<CommandService::Request>();
  request->kind = fixed_kind_;
  request->name = check_name_;
  request->timeout_s = static_cast<float>(readTimeoutPort());

  auto future_and_id = cmd_client_->async_send_request(request);
  cmd_future_ = future_and_id.future.share();
  cmd_pending_ = true;
  phase_ = MergedPhase::SEND_COMMAND;

  RCLCPP_INFO(ros_node_->get_logger(),
              "Merged node '%s' → sent command kind='%s' name='%s'.",
              this->name().c_str(), fixed_kind_.c_str(), check_name_.c_str());
  return BT::NodeStatus::RUNNING;
}

// ---- Tick: wait for command, then poll VLM ----------------------------

BT::NodeStatus MergedRunAndVerifyNode::onRunning()
{
  if (!rclcpp::ok()) {
    return BT::NodeStatus::RUNNING;
  }

  // --- Phase 1: still waiting for the command to finish -----------------
  if (phase_ == MergedPhase::SEND_COMMAND) {
    if (!cmd_pending_) {
      return BT::NodeStatus::FAILURE;
    }
    if (cmd_future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
      return BT::NodeStatus::RUNNING;
    }

    try {
      auto response = cmd_future_.get();
      cmd_pending_ = false;

      if (!response->success) {
        RCLCPP_ERROR(ros_node_->get_logger(),
                     "Command '%s' failed: %s", check_name_.c_str(), response->message.c_str());
        return BT::NodeStatus::FAILURE;
      }

      RCLCPP_INFO(ros_node_->get_logger(),
                  "Command '%s' completed (%.2fs). Switching to VLM polling.",
                  check_name_.c_str(), response->elapsed_s);
    } catch (const std::exception& exc) {
      cmd_pending_ = false;
      RCLCPP_ERROR(ros_node_->get_logger(),
                   "Command future failed: %s", exc.what());
      return BT::NodeStatus::FAILURE;
    }

    // Command succeeded → move to VLM polling phase.
    if (!vlm_client_->wait_for_service(std::chrono::seconds(5))) {
      if (!rclcpp::ok()) {
        return BT::NodeStatus::RUNNING;
      }
      RCLCPP_ERROR(ros_node_->get_logger(),
                   "VLM service '%s' not available.", vlm_service_.c_str());
      return BT::NodeStatus::FAILURE;
    }

    phase_ = MergedPhase::POLL_VLM;
    startVlmRequest();
    return BT::NodeStatus::RUNNING;
  }

  // --- Phase 2: polling VLM verdict ------------------------------------
  if (!vlm_pending_) {
    return BT::NodeStatus::FAILURE;
  }
  if (vlm_future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
    return BT::NodeStatus::RUNNING;
  }

  try {
    auto response = vlm_future_.get();
    vlm_pending_ = false;
    return handleVlmResponse(response);
  } catch (const std::exception& exc) {
    vlm_pending_ = false;
    RCLCPP_ERROR(ros_node_->get_logger(),
                 "VLM future failed for '%s': %s", check_name_.c_str(), exc.what());
    return BT::NodeStatus::FAILURE;
  }
}

// ---- VLM polling helpers ----------------------------------------------

void MergedRunAndVerifyNode::startVlmRequest()
{
  auto request = std::make_shared<VlmService::Request>();
  request->skill_name = check_name_;
  auto future_and_id = vlm_client_->async_send_request(request);
  vlm_future_ = future_and_id.future.share();
  vlm_pending_ = true;
}

BT::NodeStatus MergedRunAndVerifyNode::handleVlmResponse(
  lerobot_bt_interfaces::srv::GetSkillVerification::Response::SharedPtr response)
{
  if (!response->has_attempt) {
    RCLCPP_ERROR(ros_node_->get_logger(),
                 "VLM check '%s' has no recorded attempt: %s",
                 check_name_.c_str(), response->message.c_str());
    return BT::NodeStatus::FAILURE;
  }

  if (response->status == "SUCCESS") {
    RCLCPP_INFO(ros_node_->get_logger(),
                "VLM check '%s' SUCCESS (attempt %d): %s",
                check_name_.c_str(), response->attempt_id, response->message.c_str());
    return BT::NodeStatus::SUCCESS;
  }

  if (response->status == "FAILURE") {
    RCLCPP_ERROR(ros_node_->get_logger(),
                 "VLM check '%s' FAILURE (attempt %d): %s",
                 check_name_.c_str(), response->attempt_id, response->message.c_str());
    return BT::NodeStatus::FAILURE;
  }

  // Waiting statuses: keep polling.
  const bool waiting = response->status == "PENDING" ||
                       response->status == "RUNNING" ||
                       response->status == "WAIT_HUMAN" ||
                       response->status == "MANUAL_INTERVENTION_REQUIRED";
  if (waiting) {
    RCLCPP_DEBUG(ros_node_->get_logger(),
                 "VLM check '%s' waiting (attempt %d, status='%s'): %s",
                 check_name_.c_str(), response->attempt_id,
                 response->status.c_str(), response->message.c_str());
    startVlmRequest();
    return BT::NodeStatus::RUNNING;
  }

  RCLCPP_ERROR(ros_node_->get_logger(),
               "VLM check '%s' unexpected status '%s': %s",
               check_name_.c_str(), response->status.c_str(), response->message.c_str());
  return BT::NodeStatus::FAILURE;
}

// ---- Cleanup ----------------------------------------------------------

void MergedRunAndVerifyNode::onHalted()
{
  cmd_pending_ = false;
  vlm_pending_ = false;
  if (rclcpp::ok()) {
    RCLCPP_WARN(ros_node_->get_logger(),
                "Merged node '%s' halted.", this->name().c_str());
  }
}

double MergedRunAndVerifyNode::readTimeoutPort()
{
  return 0.0;  // gates have no timeout
}

// =====================================================================
// AwaitSceneNode
// =====================================================================

AwaitSceneNode::AwaitSceneNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& command_service,
  const std::string& vlm_service)
: MergedRunAndVerifyNode(name, config, ros_node, command_service, vlm_service, "vlm_gate_pending")
{
}

BT::PortsList AwaitSceneNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("scene_name"),
  };
}

std::string AwaitSceneNode::readNamePort()
{
  std::string name;
  if (!getInput("scene_name", name)) {
    throw BT::RuntimeError("AwaitScene missing required input port 'scene_name'");
  }
  return name;
}

// =====================================================================
// DoSkillNode
// =====================================================================

DoSkillNode::DoSkillNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& command_service,
  const std::string& vlm_service)
: MergedRunAndVerifyNode(name, config, ros_node, command_service, vlm_service, "skill")
{
}

BT::PortsList DoSkillNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("skill_name"),
    BT::InputPort<double>("timeout_s", 0.0, "Optional timeout override in seconds"),
  };
}

std::string DoSkillNode::readNamePort()
{
  std::string name;
  if (!getInput("skill_name", name)) {
    throw BT::RuntimeError("DoSkill missing required input port 'skill_name'");
  }
  return name;
}

double DoSkillNode::readTimeoutPort()
{
  double timeout = 0.0;
  getInput("timeout_s", timeout);
  return timeout;
}

}  // namespace lerobot_bt_runtime_cpp
