// Comment: executes this BT logic statement in C++.
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

// Comment: includes a dependency required for compilation.
#include <chrono>
// Comment: includes a dependency required for compilation.
#include <memory>
// Comment: includes a dependency required for compilation.
#include <string>

// Comment: includes a dependency required for compilation.
#include <rclcpp/rclcpp.hpp>

// Comment: selects code based on the macros available at compile time.
#if __has_include(<behaviortree_cpp/action_node.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp/action_node.h>
// Comment: selects code based on the macros available at compile time.
#elif __has_include(<behaviortree_cpp_v3/action_node.h>)
// Comment: includes a dependency required for compilation.
#include <behaviortree_cpp_v3/action_node.h>
// Comment: uses the fallback branch of the compilation configuration.
#else
// Comment: forces a compilation error when a required dependency is missing.
#error "BehaviorTree.CPP action_node.h header was not found."
// Comment: closes the conditional compilation block.
#endif

// Comment: includes a dependency required for compilation.
#include <lerobot_bt_interfaces/srv/get_skill_verification.hpp>
// Comment: includes a dependency required for compilation.
#include <lerobot_bt_interfaces/srv/run_named_command.hpp>

// Comment: opens or declares the BT package namespace.
namespace lerobot_bt_runtime_cpp
// Comment: opens a new C++ code block.
{

/**
 * @brief Internal phases of the merged action+verify lifecycle.
 */
// Comment: declares a set of states or enumerated values.
enum class MergedPhase
// Comment: opens a new C++ code block.
{
  // Comment: executes this BT logic statement in C++.
  SEND_COMMAND,  ///< The command (skill or gate) is in flight.
  // Comment: executes this BT logic statement in C++.
  POLL_VLM,      ///< The command completed; now waiting for VLM verdict.
// Comment: closes the current C++ code block.
};

/**
 * @brief Base class for merged "do something then wait for VLM" leaves.
 *
 * Subclasses fix the ROS command kind ("vlm_gate" or "skill") and
 * declare XML ports.  The base class owns the two-phase state machine, both
 * ROS2 service clients, and the retry-safe halting logic.
 */
// Comment: declares a C++ class for the BT runtime.
class MergedRunAndVerifyNode : public BT::StatefulActionNode
// Comment: opens a new C++ code block.
{
// Comment: changes the visibility of the class members.
public:
  // Comment: defines a type alias or imports a symbol into the current namespace.
  using CommandService = lerobot_bt_interfaces::srv::RunNamedCommand;
  // Comment: defines a type alias or imports a symbol into the current namespace.
  using VlmService = lerobot_bt_interfaces::srv::GetSkillVerification;

  /**
   * @brief Construct with ROS2 plumbing and the fixed command kind.
   */
  // Comment: executes this BT logic statement in C++.
  MergedRunAndVerifyNode(
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
    std::string fixed_kind);

  /** @brief First tick: send the command to the Python server. */
  // Comment: executes this BT logic statement in C++.
  BT::NodeStatus onStart() override;

  /** @brief Subsequent ticks: wait for command, then poll VLM. */
  // Comment: executes this BT logic statement in C++.
  BT::NodeStatus onRunning() override;

  /** @brief Clean up pending state if the BT halts this leaf. */
  // Comment: executes this BT logic statement in C++.
  void onHalted() override;

// Comment: changes the visibility of the class members.
protected:
  /** @brief Read the primary name port (scene_name or skill_name). */
  // Comment: assigns or initializes a value used by the BT runtime.
  virtual std::string readNamePort() = 0;

  /** @brief Read the optional timeout port (only meaningful for skills). */
  // Comment: executes this BT logic statement in C++.
  virtual double readTimeoutPort();

  // ---- ROS2 transport ------------------------------------------------
  // Comment: executes this BT logic statement in C++.
  rclcpp::Node::SharedPtr ros_node_;
  // Comment: executes this BT logic statement in C++.
  rclcpp::Client<CommandService>::SharedPtr cmd_client_;
  // Comment: executes this BT logic statement in C++.
  rclcpp::Client<VlmService>::SharedPtr vlm_client_;
  // Comment: executes this BT logic statement in C++.
  std::string command_service_;
  // Comment: executes this BT logic statement in C++.
  std::string vlm_service_;
  // Comment: executes this BT logic statement in C++.
  std::string fixed_kind_;

  // ---- State machine ------------------------------------------------
  // Comment: executes this BT logic statement in C++.
  MergedPhase phase_{MergedPhase::SEND_COMMAND};
  // Comment: executes this BT logic statement in C++.
  std::string check_name_;   ///< The gate/skill name used for VLM polling.
  // Comment: executes this BT logic statement in C++.
  rclcpp::Client<CommandService>::SharedFuture cmd_future_;
  // Comment: executes this BT logic statement in C++.
  rclcpp::Client<VlmService>::SharedFuture vlm_future_;
  // Comment: executes this BT logic statement in C++.
  bool cmd_pending_{false};
  // Comment: executes this BT logic statement in C++.
  bool vlm_pending_{false};

// Comment: changes the visibility of the class members.
private:
  /** @brief Dispatch one asynchronous VLM state request. */
  // Comment: executes this BT logic statement in C++.
  void startVlmRequest();

  /** @brief Interpret the VLM response into a BT status. */
  // Comment: executes this BT logic statement in C++.
  BT::NodeStatus handleVlmResponse(
    // Comment: executes this BT logic statement in C++.
    lerobot_bt_interfaces::srv::GetSkillVerification::Response::SharedPtr response);
// Comment: closes the current C++ code block.
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
// Comment: declares a C++ class for the BT runtime.
class AwaitSceneNode : public MergedRunAndVerifyNode
// Comment: opens a new C++ code block.
{
// Comment: changes the visibility of the class members.
public:
  // Comment: executes this BT logic statement in C++.
  AwaitSceneNode(
    // Comment: executes this BT logic statement in C++.
    const std::string& name,
    // Comment: executes this BT logic statement in C++.
    const BT::NodeConfiguration& config,
    // Comment: executes this BT logic statement in C++.
    const rclcpp::Node::SharedPtr& ros_node,
    // Comment: executes this BT logic statement in C++.
    const std::string& command_service,
    // Comment: executes this BT logic statement in C++.
    const std::string& vlm_service);

  // Comment: executes this BT logic statement in C++.
  static BT::PortsList providedPorts();

// Comment: changes the visibility of the class members.
protected:
  // Comment: executes this BT logic statement in C++.
  std::string readNamePort() override;
// Comment: closes the current C++ code block.
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
// Comment: declares a C++ class for the BT runtime.
class DoSkillNode : public MergedRunAndVerifyNode
// Comment: opens a new C++ code block.
{
// Comment: changes the visibility of the class members.
public:
  // Comment: executes this BT logic statement in C++.
  DoSkillNode(
    // Comment: executes this BT logic statement in C++.
    const std::string& name,
    // Comment: executes this BT logic statement in C++.
    const BT::NodeConfiguration& config,
    // Comment: executes this BT logic statement in C++.
    const rclcpp::Node::SharedPtr& ros_node,
    // Comment: executes this BT logic statement in C++.
    const std::string& command_service,
    // Comment: executes this BT logic statement in C++.
    const std::string& vlm_service);

  // Comment: executes this BT logic statement in C++.
  static BT::PortsList providedPorts();

// Comment: changes the visibility of the class members.
protected:
  // Comment: executes this BT logic statement in C++.
  std::string readNamePort() override;
  // Comment: executes this BT logic statement in C++.
  double readTimeoutPort() override;
// Comment: closes the current C++ code block.
};

// Comment: closes the current C++ code block.
}  // namespace lerobot_bt_runtime_cpp
