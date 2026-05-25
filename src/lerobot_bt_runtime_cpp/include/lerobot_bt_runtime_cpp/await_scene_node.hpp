#pragma once

/**
 * @file await_scene_node.hpp
 * @brief Merged BT leaves that combine action execution with VLM verification.
 *
 * The original design used separate OpenVLMGate+WaitForVLMVerdict (or
 * RunRobotSkill+WaitForVLMVerdict) pairs wrapped in a Sequence.  Those pairs
 * are always used together, so this header provides two single-leaf
 * replacements that halve the node count and flatten the XML trees.
 *
 *   - AwaitSceneNode  replaces  OpenVLMGate + WaitForVLMVerdict
 *   - DoSkillNode     replaces  RunRobotSkill  + WaitForVLMVerdict
 *
 * Both nodes follow the same two-phase state machine internally:
 *   1. Send the command (gate or skill) to the Python server.
 *   2. Poll the VLM state service until a terminal verdict arrives.
 */

#include <chrono>
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

#include <lerobot_bt_interfaces/srv/get_skill_verification.hpp>
#include <lerobot_bt_interfaces/srv/run_named_command.hpp>

namespace lerobot_bt_runtime_cpp
{

/**
 * @brief Internal phases of the merged action+verify lifecycle.
 */
enum class MergedPhase
{
  SEND_COMMAND,  ///< The command (skill or gate) is in flight.
  POLL_VLM,      ///< The command completed; now waiting for VLM verdict.
};

/**
 * @brief Base class for merged "do something then wait for VLM" leaves.
 *
 * Subclasses fix the ROS command kind ("vlm_gate_pending" or "skill") and
 * declare XML ports.  The base class owns the two-phase state machine, both
 * ROS2 service clients, and the retry-safe halting logic.
 */
class MergedRunAndVerifyNode : public BT::StatefulActionNode
{
public:
  using CommandService = lerobot_bt_interfaces::srv::RunNamedCommand;
  using VlmService = lerobot_bt_interfaces::srv::GetSkillVerification;

  /**
   * @brief Construct with ROS2 plumbing and the fixed command kind.
   */
  MergedRunAndVerifyNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& command_service,
    const std::string& vlm_service,
    std::string fixed_kind);

  /** @brief First tick: send the command to the Python server. */
  BT::NodeStatus onStart() override;

  /** @brief Subsequent ticks: wait for command, then poll VLM. */
  BT::NodeStatus onRunning() override;

  /** @brief Clean up pending state if the BT halts this leaf. */
  void onHalted() override;

protected:
  /** @brief Read the primary name port (scene_name or skill_name). */
  virtual std::string readNamePort() = 0;

  /** @brief Read the optional timeout port (only meaningful for skills). */
  virtual double readTimeoutPort();

  // ---- ROS2 transport ------------------------------------------------
  rclcpp::Node::SharedPtr ros_node_;
  rclcpp::Client<CommandService>::SharedPtr cmd_client_;
  rclcpp::Client<VlmService>::SharedPtr vlm_client_;
  std::string command_service_;
  std::string vlm_service_;
  std::string fixed_kind_;

  // ---- State machine ------------------------------------------------
  MergedPhase phase_{MergedPhase::SEND_COMMAND};
  std::string check_name_;   ///< The gate/skill name used for VLM polling.
  rclcpp::Client<CommandService>::SharedFuture cmd_future_;
  rclcpp::Client<VlmService>::SharedFuture vlm_future_;
  bool cmd_pending_{false};
  bool vlm_pending_{false};

private:
  /** @brief Dispatch one asynchronous VLM state request. */
  void startVlmRequest();

  /** @brief Interpret the VLM response into a BT status. */
  BT::NodeStatus handleVlmResponse(
    lerobot_bt_interfaces::srv::GetSkillVerification::Response::SharedPtr response);
};

// =====================================================================
// AwaitSceneNode  –  OpenVLMGate + WaitForVLMVerdict  in one leaf
// =====================================================================

/**
 * @brief Single BT leaf that opens a scene gate and waits for VLM OK.
 *
 * XML port: scene_name  – the gate identifier (e.g. "drawer_open_ready").
 *
 * Equivalent to the old pair:
 *   <OpenVLMGate gate_name="..."/> <WaitForVLMVerdict check_name="..."/>
 */
class AwaitSceneNode : public MergedRunAndVerifyNode
{
public:
  AwaitSceneNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& command_service,
    const std::string& vlm_service);

  static BT::PortsList providedPorts();

protected:
  std::string readNamePort() override;
};

// =====================================================================
// DoSkillNode  –  RunRobotSkill + WaitForVLMVerdict  in one leaf
// =====================================================================

/**
 * @brief Single BT leaf that runs a robot BC skill and waits for VLM OK.
 *
 * XML ports: skill_name, timeout_s (optional).
 *
 * Equivalent to the old pair:
 *   <RunRobotSkill skill_name="..." timeout_s="..."/>
 *   <WaitForVLMVerdict check_name="..."/>
 */
class DoSkillNode : public MergedRunAndVerifyNode
{
public:
  DoSkillNode(
    const std::string& name,
    const BT::NodeConfiguration& config,
    const rclcpp::Node::SharedPtr& ros_node,
    const std::string& command_service,
    const std::string& vlm_service);

  static BT::PortsList providedPorts();

protected:
  std::string readNamePort() override;
  double readTimeoutPort() override;
};

}  // namespace lerobot_bt_runtime_cpp
