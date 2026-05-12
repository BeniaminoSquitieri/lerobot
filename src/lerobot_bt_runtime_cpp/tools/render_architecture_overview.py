#!/usr/bin/env python3
"""Render the repository-level LeRobot BT architecture overview PNG.

The checked-in `src/Architecture.png` is a visual summary used during bring-up.
Keeping the source in this script prevents the image from drifting when ROS2
package names, services, or task profiles change.
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

DOT_SOURCE = r"""
digraph LeRobotBTArchitecture {
  graph [
    rankdir=LR,
    bgcolor="white",
    pad="0.4",
    nodesep="0.55",
    ranksep="0.75",
    fontname="DejaVu Sans",
    labelloc="t",
    label=<
      <B>LEROBOT BT ARCHITECTURE OVERVIEW</B><BR/>
      <FONT POINT-SIZE="18">Generic BehaviorTree.CPP stack for multiple manipulation BTs</FONT>
    >
  ];
  node [
    shape=box,
    style="rounded,filled",
    fontname="DejaVu Sans",
    fontsize=15,
    margin="0.14,0.10",
    color="#334155",
    fillcolor="#f8fafc"
  ];
  edge [
    color="#1f2937",
    arrowsize=0.8,
    fontname="DejaVu Sans",
    fontsize=12
  ];

  subgraph cluster_assets {
    label="Task assets in src/lerobot_bt_runtime_cpp";
    color="#60a5fa";
    style="rounded";
    fillcolor="#eff6ff";
    trees [label=<BT XML trees<BR/><FONT POINT-SIZE="12">make_sandwich, grocery_bagging,<BR/>items_in_drawer, lunch_table_bussing,<BR/>make_coffee</FONT>>, fillcolor="#dbeafe"];
    profiles [label=<Task YAML profiles<BR/><FONT POINT-SIZE="12">config/*_bt.yaml writes bt.*<BR/>blackboard values</FONT>>, fillcolor="#dbeafe"];
    diagrams [label=<Rendered BT diagrams<BR/><FONT POINT-SIZE="12">diagrams/*_bt.png generated<BR/>from XML + YAML</FONT>>, fillcolor="#dbeafe"];
  }

  subgraph cluster_runtime {
    label="ROS2 runtime package: lerobot_bt_runtime_cpp";
    color="#22c55e";
    style="rounded";
    runtime [label=<lerobot_bt_runner<BR/><FONT POINT-SIZE="12">loads XML, initializes blackboard,<BR/>ticks the tree</FONT>>, fillcolor="#dcfce7"];
    factory [label=<BehaviorTree.CPP factory<BR/><FONT POINT-SIZE="12">registers RunRobotSkill,<BR/>OpenVLMGate, verdict nodes</FONT>>, fillcolor="#dcfce7"];
    groot [label=<Optional Groot publisher<BR/><FONT POINT-SIZE="12">live BT visualization</FONT>>, fillcolor="#dcfce7"];
  }

  subgraph cluster_interfaces {
    label="ROS2 service contracts: lerobot_bt_interfaces";
    color="#f59e0b";
    style="rounded";
    run_srv [label=<RunNamedCommand<BR/><FONT POINT-SIZE="12">kind, name, timeout_s</FONT>>, fillcolor="#fef3c7"];
    state_srv [label=<GetSkillVerification<BR/><FONT POINT-SIZE="12">latest VLM attempt state</FONT>>, fillcolor="#fef3c7"];
    legacy_srv [label=<ReportSkillVerification<BR/><FONT POINT-SIZE="12">legacy verifier service</FONT>>, fillcolor="#fef3c7"];
  }

  subgraph cluster_python {
    label="Python execution package: lerobot_bt_python";
    color="#a855f7";
    style="rounded";
    server [label=<SkillCommandServer<BR/><FONT POINT-SIZE="12">/lerobot_bt/run<BR/>/lerobot_bt/vlm_state<BR/>/lerobot_bt/vlm_result_legacy</FONT>>, fillcolor="#f3e8ff"];
    executor [label=<SkillCommandExecutor<BR/><FONT POINT-SIZE="12">serializes robot access and<BR/>runs configured BC policies</FONT>>, fillcolor="#f3e8ff"];
    registry [label=<VlmCheckRegistry<BR/><FONT POINT-SIZE="12">PENDING, RUNNING,<BR/>WAIT_HUMAN, SUCCESS, FAILURE</FONT>>, fillcolor="#f3e8ff"];
    exec_profiles [label=<Executor YAML profiles<BR/><FONT POINT-SIZE="12">src/lerobot_bt_python/*_executor.yaml</FONT>>, fillcolor="#f3e8ff"];
  }

  subgraph cluster_robot {
    label="LeRobot robot and policy layer";
    color="#64748b";
    style="rounded";
    robot [label=<CustomManipulator<BR/><FONT POINT-SIZE="12">Panda arm, gripper, cameras</FONT>>, fillcolor="#f1f5f9"];
    policy [label=<LeRobot policies<BR/><FONT POINT-SIZE="12">ACT / Diffusion / GROOT configs,<BR/>pre/post processors</FONT>>, fillcolor="#f1f5f9"];
  }

  subgraph cluster_verifier {
    label="VLM or manual verifier";
    color="#ef4444";
    style="rounded";
    request_topic [label=</lerobot_bt/vlm_request<BR/><FONT POINT-SIZE="12">server asks for a scene verdict</FONT>>, fillcolor="#fee2e2"];
    result_topic [label=</lerobot_bt/vlm_result<BR/><FONT POINT-SIZE="12">verifier reports waiting,<BR/>success, failure, or next_action</FONT>>, fillcolor="#fee2e2"];
  }

  subgraph cluster_flow {
    label="Execution rule";
    color="#0f172a";
    style="rounded";
    flow [label=<
      1. BT opens a gate or runs a named skill<BR ALIGN="LEFT"/>
      2. Python opens a VLM check attempt<BR ALIGN="LEFT"/>
      3. Waiting statuses keep the BT RUNNING<BR ALIGN="LEFT"/>
      4. SUCCESS advances the tree<BR ALIGN="LEFT"/>
      5. FAILURE retries through XML retry nodes
    >, fillcolor="#e2e8f0"];
  }

  trees -> runtime [label="tree_xml_path"];
  profiles -> runtime [label="bt.* params"];
  trees -> diagrams [label="rendered from"];
  runtime -> factory;
  runtime -> groot [style=dashed, label="monitor"];
  factory -> run_srv [label="skill/gate command"];
  factory -> state_srv [label="poll verdict"];
  run_srv -> server;
  state_srv -> server;
  legacy_srv -> server [style=dashed];
  exec_profiles -> server [label="config_path"];
  server -> executor [label="kind=skill"];
  executor -> policy [label="predict_action"];
  executor -> robot [label="send_action"];
  server -> registry [label="begin/report attempts"];
  server -> request_topic [label="publish"];
  result_topic -> server [label="consume"];
  request_topic -> result_topic [style=dashed, label="external verifier"];
  registry -> state_srv [style=dashed, label="status response"];
  registry -> flow [style=dashed];
}
"""


def render_architecture(output_path: Path) -> None:
    """Render the architecture overview DOT source to a PNG file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".dot", encoding="utf-8", delete=False) as dot_file:
        dot_file.write(DOT_SOURCE)
        dot_path = Path(dot_file.name)
    try:
        subprocess.run(["dot", "-Tpng", str(dot_path), "-o", str(output_path)], check=True)
    finally:
        dot_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    """Parse the optional output path used by local documentation refreshes."""
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=repo_root / "src" / "Architecture.png")
    return parser.parse_args()


def main() -> None:
    """Console entry point for regenerating `src/Architecture.png`."""
    args = parse_args()
    render_architecture(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
