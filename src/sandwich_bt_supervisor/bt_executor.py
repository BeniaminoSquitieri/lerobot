"""Execute robot subtasks through BT XML subtrees and RunNamedCommand requests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from .named_command_backends import NamedCommandBackend, NamedCommandRequest, NamedCommandResult
from .planner_schema import StepExecutionResult, TaskPrimitive


def default_subtree_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[1] / "sandwich_bt_runtime_cpp" / "trees" / filename


@dataclass(frozen=True)
class ExecutedBtCommand:
    tree_xml_path: str
    attempt_index: int
    request: NamedCommandRequest
    result: NamedCommandResult


class BtXmlRobotExecutor:
    """Minimal BT interpreter for the hardware-free contract tests.

    It supports only the subtree shapes used in this repository:
    - `RetryUntilSuccessful`
    - `Sequence`
    - `RunNamedCommand`
    """

    def __init__(
        self,
        *,
        command_backend: NamedCommandBackend,
        on_step_success: Callable[[str], None] | None = None,
    ) -> None:
        self._command_backend = command_backend
        self._on_step_success = on_step_success or (lambda _step_name: None)
        self.command_history: list[ExecutedBtCommand] = []

    def execute(self, primitive: TaskPrimitive) -> StepExecutionResult:
        if primitive.bt_xml_path is None:
            raise ValueError(f"Robot primitive '{primitive.name}' does not define bt_xml_path.")

        tree_xml_path = Path(primitive.bt_xml_path)
        root = ElementTree.parse(tree_xml_path).getroot()
        tree_root = self._main_tree_root(root)
        success, elapsed_s, message = self._execute_node(
            tree_root,
            tree_xml_path=tree_xml_path,
            attempt_index=1,
        )

        if success:
            self._on_step_success(primitive.name)
            return StepExecutionResult(
                step_name=primitive.name,
                actor="robot",
                success=True,
                status="SUCCESS",
                elapsed_s=elapsed_s,
                message=message,
            )

        return StepExecutionResult(
            step_name=primitive.name,
            actor="robot",
            success=False,
            status="FAILURE",
            elapsed_s=elapsed_s,
            message=message,
        )

    def _main_tree_root(self, root: ElementTree.Element) -> ElementTree.Element:
        main_tree_id = root.attrib.get("main_tree_to_execute")
        behavior_trees = [child for child in root if self._tag(child) == "BehaviorTree"]
        if not behavior_trees:
            raise ValueError("BT XML does not contain any <BehaviorTree> definition.")

        if main_tree_id is None:
            selected_tree = behavior_trees[0]
        else:
            matching_trees = [tree for tree in behavior_trees if tree.attrib.get("ID") == main_tree_id]
            if not matching_trees:
                raise ValueError(f"BT XML does not define BehaviorTree ID '{main_tree_id}'.")
            selected_tree = matching_trees[0]

        executable_children = [child for child in selected_tree if isinstance(child.tag, str)]
        if len(executable_children) != 1:
            raise ValueError("Expected the selected BehaviorTree to contain exactly one executable child.")
        return executable_children[0]

    def _execute_node(
        self,
        node: ElementTree.Element,
        *,
        tree_xml_path: Path,
        attempt_index: int,
    ) -> tuple[bool, float, str]:
        tag = self._tag(node)
        if tag == "Sequence":
            return self._execute_sequence(node, tree_xml_path=tree_xml_path, attempt_index=attempt_index)
        if tag == "RetryUntilSuccessful":
            return self._execute_retry(node, tree_xml_path=tree_xml_path)
        if tag == "RunNamedCommand":
            return self._execute_command(node, tree_xml_path=tree_xml_path, attempt_index=attempt_index)
        raise ValueError(f"Unsupported BT node '{tag}' in '{tree_xml_path}'.")

    def _execute_sequence(
        self,
        node: ElementTree.Element,
        *,
        tree_xml_path: Path,
        attempt_index: int,
    ) -> tuple[bool, float, str]:
        elapsed_s = 0.0
        last_message = f"Sequence '{node.attrib.get('name', '')}' completed."
        for child in node:
            if not isinstance(child.tag, str):
                continue
            success, child_elapsed_s, child_message = self._execute_node(
                child,
                tree_xml_path=tree_xml_path,
                attempt_index=attempt_index,
            )
            elapsed_s += child_elapsed_s
            last_message = child_message
            if not success:
                return False, elapsed_s, child_message
        return True, elapsed_s, last_message

    def _execute_retry(
        self,
        node: ElementTree.Element,
        *,
        tree_xml_path: Path,
    ) -> tuple[bool, float, str]:
        child_nodes = [child for child in node if isinstance(child.tag, str)]
        if len(child_nodes) != 1:
            raise ValueError(f"RetryUntilSuccessful in '{tree_xml_path}' must wrap exactly one child.")

        child = child_nodes[0]
        num_attempts = int(node.attrib["num_attempts"])
        total_elapsed_s = 0.0
        last_message = "Retry subtree did not execute."

        for attempt_index in range(1, num_attempts + 1):
            success, elapsed_s, message = self._execute_node(
                child,
                tree_xml_path=tree_xml_path,
                attempt_index=attempt_index,
            )
            total_elapsed_s += elapsed_s
            last_message = message
            if success:
                return True, total_elapsed_s, message

        return (
            False,
            total_elapsed_s,
            f"BT subtree '{tree_xml_path.name}' failed after {num_attempts} attempts. Last error: {last_message}",
        )

    def _execute_command(
        self,
        node: ElementTree.Element,
        *,
        tree_xml_path: Path,
        attempt_index: int,
    ) -> tuple[bool, float, str]:
        request = NamedCommandRequest(
            kind=node.attrib["kind"],
            name=node.attrib["command_name"],
            timeout_s=float(node.attrib.get("timeout_s", 0.0)),
        )
        result = self._command_backend.run_named_command(
            kind=request.kind,
            name=request.name,
            timeout_s=request.timeout_s,
        )
        self.command_history.append(
            ExecutedBtCommand(
                tree_xml_path=str(tree_xml_path),
                attempt_index=attempt_index,
                request=request,
                result=result,
            )
        )
        return result.success, result.elapsed_s, result.message

    @staticmethod
    def _tag(node: ElementTree.Element) -> str:
        return node.tag.rsplit("}", 1)[-1]
