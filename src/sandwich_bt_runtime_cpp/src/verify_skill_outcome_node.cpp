/**
 * @file verify_skill_outcome_node.cpp
 * @brief BehaviorTree.CPP node that polls Python-side post-skill verification.
 */
#include "sandwich_bt_runtime_cpp/verify_skill_outcome_node.hpp"

#include <chrono>
#include <exception>
#include <future>

namespace sandwich_bt_runtime_cpp
{

/**
 * @brief Stores the BT and ROS2 dependencies required by the verification leaf.
 */
VerifySkillOutcomeNode::VerifySkillOutcomeNode(
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
 * @brief Dispatches one asynchronous verification lookup for the current skill.
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
 * @brief Reads the skill name and starts polling the verification service.
 */
BT::NodeStatus VerifySkillOutcomeNode::onStart()
{
  if (!getInput("skill_name", skill_name_)) {
    throw BT::RuntimeError("VerifySkillOutcome missing required input port 'skill_name'");
  }

  if (!client_->wait_for_service(std::chrono::seconds(5))) {
    RCLCPP_ERROR(ros_node_->get_logger(), "Service '%s' not available.", service_name_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  startRequest();
  RCLCPP_INFO(
    ros_node_->get_logger(),
    "Started verification polling for skill '%s'.",
    skill_name_.c_str());
  return BT::NodeStatus::RUNNING;
}

/**
 * @brief Interprets verification responses and keeps polling while pending.
 */
BT::NodeStatus VerifySkillOutcomeNode::onRunning()
{
  if (!request_pending_) {
    return BT::NodeStatus::FAILURE;
  }

  // Poll without blocking so the BT executor can keep spinning ROS callbacks
  // and ticking other tree state while verification is still pending.
  if (future_.wait_for(std::chrono::milliseconds(0)) != std::future_status::ready) {
    return BT::NodeStatus::RUNNING;
  }

  try {
    auto response = future_.get();
    request_pending_ = false;

    if (!response->has_attempt) {
      RCLCPP_ERROR(
        ros_node_->get_logger(),
        "Verification for skill '%s' has no recorded attempt: %s",
        skill_name_.c_str(),
        response->message.c_str());
      return BT::NodeStatus::FAILURE;
    }

    if (response->status == "SUCCESS") {
      RCLCPP_INFO(
        ros_node_->get_logger(),
        "Verification succeeded for skill '%s' attempt %d: %s",
        skill_name_.c_str(),
        response->attempt_id,
        response->message.c_str());
      return BT::NodeStatus::SUCCESS;
    }

    if (response->status == "FAILURE") {
      RCLCPP_ERROR(
        ros_node_->get_logger(),
        "Verification failed for skill '%s' attempt %d: %s",
        skill_name_.c_str(),
        response->attempt_id,
        response->message.c_str());
      return BT::NodeStatus::FAILURE;
    }

    if (response->status == "PENDING") {
      // The verifier has seen the attempt but has not produced a final verdict
      // yet, so issue a fresh lookup and keep the BT leaf RUNNING.
      startRequest();
      return BT::NodeStatus::RUNNING;
    }

    RCLCPP_ERROR(
      ros_node_->get_logger(),
      "Verification for skill '%s' returned unexpected status '%s': %s",
      skill_name_.c_str(),
      response->status.c_str(),
      response->message.c_str());
    return BT::NodeStatus::FAILURE;
  } catch (const std::exception& exc) {
    request_pending_ = false;
    RCLCPP_ERROR(ros_node_->get_logger(), "Verification future failed with exception: %s", exc.what());
    return BT::NodeStatus::FAILURE;
  }
}

/**
 * @brief Stops local polling when BehaviorTree.CPP halts this verification leaf.
 */
void VerifySkillOutcomeNode::onHalted()
{
  request_pending_ = false;
  RCLCPP_WARN(
    ros_node_->get_logger(),
    "VerifySkillOutcome halted while polling service '%s'.",
    service_name_.c_str());
}

}  // namespace sandwich_bt_runtime_cpp
