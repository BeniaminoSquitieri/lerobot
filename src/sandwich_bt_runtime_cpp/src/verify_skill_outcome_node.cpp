/**
 * @file verify_skill_outcome_node.cpp
 * @brief BehaviorTree.CPP node that polls Python-side VLM check state.
 */
#include "sandwich_bt_runtime_cpp/verify_skill_outcome_node.hpp"

#include <chrono>
#include <exception>
#include <future>

namespace sandwich_bt_runtime_cpp
{

/**
 * @brief Stores the BT and ROS2 dependencies required by the VLM check leaf.
 */
VerifySkillOutcomeNode::VerifySkillOutcomeNode(
  const std::string& name,
  const BT::NodeConfiguration& config,
  const rclcpp::Node::SharedPtr& ros_node,
  const std::string& vlm_state_service)
: BT::StatefulActionNode(name, config),
  ros_node_(ros_node),
  client_(ros_node_->create_client<ServiceT>(vlm_state_service)),
  vlm_state_service_(vlm_state_service)
{
}

/**
 * @brief Defines the skill_name input port read from XML.
 */
BT::PortsList VerifySkillOutcomeNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("skill_name"),
  };
}

/**
 * @brief Dispatches one asynchronous VLM state lookup for the current skill.
 */
void VerifySkillOutcomeNode::startRequest()
{
  auto request = std::make_shared<ServiceT::Request>();
  request->skill_name = skill_name_;
  auto future_and_request_id = client_->async_send_request(request);
  future_ = future_and_request_id.future.share();
  request_pending_ = true;
}

/**
 * @brief Reads the skill name and starts polling the VLM state service.
 */
BT::NodeStatus VerifySkillOutcomeNode::onStart()
{
  if (!getInput("skill_name", skill_name_)) {
    throw BT::RuntimeError("VerifySkillOutcome missing required input port 'skill_name'");
  }

  if (!client_->wait_for_service(std::chrono::seconds(5))) {
    RCLCPP_ERROR(ros_node_->get_logger(), "Service '%s' not available.", vlm_state_service_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  startRequest();
  RCLCPP_INFO(
    ros_node_->get_logger(),
    "Started VLM check polling for skill '%s'.",
    skill_name_.c_str());
  return BT::NodeStatus::RUNNING;
}

/**
 * @brief Interprets VLM state responses and keeps polling while pending.
 */
BT::NodeStatus VerifySkillOutcomeNode::onRunning()
{
  if (!request_pending_) {
    return BT::NodeStatus::FAILURE;
  }

  // Poll without blocking so the BT executor can keep spinning ROS callbacks
  // and ticking other tree state while the VLM check is still pending.
  if (future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
    return BT::NodeStatus::RUNNING;
  }

  try {
    auto response = future_.get();
    request_pending_ = false;

    if (!response->has_attempt) {
      RCLCPP_ERROR(
        ros_node_->get_logger(),
        "VLM check for skill '%s' has no recorded attempt: %s",
        skill_name_.c_str(),
        response->message.c_str());
      return BT::NodeStatus::FAILURE;
    }

    if (response->status == "SUCCESS") {
      RCLCPP_INFO(
        ros_node_->get_logger(),
        "VLM check succeeded for skill '%s' attempt %d: %s",
        skill_name_.c_str(),
        response->attempt_id,
        response->message.c_str());
      return BT::NodeStatus::SUCCESS;
    }

    if (response->status == "FAILURE") {
      RCLCPP_ERROR(
        ros_node_->get_logger(),
        "VLM check failed for skill '%s' attempt %d: %s",
        skill_name_.c_str(),
        response->attempt_id,
        response->message.c_str());
      return BT::NodeStatus::FAILURE;
    }

    const bool status_waiting =
      response->status == "PENDING" ||
      response->status == "RUNNING" ||
      response->status == "WAIT_HUMAN" ||
      response->status == "MANUAL_INTERVENTION_REQUIRED";
    if (status_waiting) {
      // The verifier has seen the attempt but has not produced a final verdict
      // yet, or it explicitly requested waiting for human/manual progress.
      RCLCPP_DEBUG(
        ros_node_->get_logger(),
        "VLM check still waiting for skill '%s' attempt %d status='%s': %s",
        skill_name_.c_str(),
        response->attempt_id,
        response->status.c_str(),
        response->message.c_str());
      startRequest();
      return BT::NodeStatus::RUNNING;
    }

    RCLCPP_ERROR(
      ros_node_->get_logger(),
      "VLM check for skill '%s' returned unexpected status '%s': %s",
      skill_name_.c_str(),
      response->status.c_str(),
      response->message.c_str());
    return BT::NodeStatus::FAILURE;
  } catch (const std::exception& exc) {
    request_pending_ = false;
    RCLCPP_ERROR(ros_node_->get_logger(), "VLM state future failed with exception: %s", exc.what());
    return BT::NodeStatus::FAILURE;
  }
}

/**
 * @brief Stops local polling when BehaviorTree.CPP halts this VLM check leaf.
 */
void VerifySkillOutcomeNode::onHalted()
{
  request_pending_ = false;
  RCLCPP_WARN(
    ros_node_->get_logger(),
    "VerifySkillOutcome halted while polling service '%s'.",
    vlm_state_service_.c_str());
}

}  // namespace sandwich_bt_runtime_cpp
