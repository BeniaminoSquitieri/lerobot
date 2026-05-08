# pyright: reportMissingImports=false

from __future__ import annotations

from collections.abc import Mapping, Sequence

from lerobot.robots.custom_manipulator.grippers.leap_hand_target_transforms import (
    transform_targets_for_leap_retargeting,
)
from lerobot.robots.custom_manipulator.rerun_blueprint_utils import (
    send_leap_hand_blueprint,
)


class LeapHandDebugTools:
    def __init__(
        self,
        urdf_path: str,
        enable_rerun_visualization: bool,
        palm_link_name: str,
        root_link_name: str,
        command_index_by_link_name: Mapping[str, int] | None = None,
        quest_palm_from_leap_palm: list[list[float]] | None = None,
    ):
        self.enable_rerun_visualization = enable_rerun_visualization
        self.step = 0
        self.root_entity_path = f"/leap_hand/{root_link_name}"
        self.palm_frame_id = f"tf#/leap_hand/{palm_link_name}"
        self.root_frame_id = f"tf#/leap_hand/{root_link_name}"
        self.command_index_by_link_name = dict(command_index_by_link_name or {})
        self._quest_palm_from_leap_palm = (
            [[float(v) for v in row] for row in quest_palm_from_leap_palm]
            if quest_palm_from_leap_palm is not None
            else None
        )
        self.urdf_tree = None
        self.rr = None

        if not self.enable_rerun_visualization:
            return

        import rerun as rr
        from rerun.urdf import UrdfTree

        self.rr = rr

        if not rr.is_enabled():
            rr.init("leap_hand_debug", spawn=True)

        self.urdf_tree = UrdfTree.from_file_path(
            urdf_path,
            entity_path_prefix="leap_hand",
            frame_prefix="tf#/leap_hand/",
        )
        self.urdf_tree.log_urdf_to_recording()
        if quest_palm_from_leap_palm is not None:
            rr.log(
                self.root_entity_path,
                rr.Transform3D(
                    translation=[0.0, 0.0, 0.0],
                    mat3x3=quest_palm_from_leap_palm,
                    relation=rr.TransformRelation.ParentFromChild,
                ),
                static=True,
            )
        # Set the initial view so +X is up, +Y points toward the viewer, +Z points right.
        rr.log(self.root_entity_path, rr.ViewCoordinates.UBR, static=True)
        send_leap_hand_blueprint(
            hand_view_name="LeapHand",
            hand_contents=["/leap_hand/**", "/leap_targets/**", "/leap_tips/**"],
            hand_target_frame=self.root_frame_id,
        )

    def close(self):
        return None

    def log_state(
        self,
        joints: Mapping[str, float] | None = None,
        tip_positions: Mapping[str, Sequence[float]] | None = None,
        *,
        qpos: Sequence[float] | None = None,
    ):
        if not self.enable_rerun_visualization or self.urdf_tree is None or self.rr is None:
            return

        rr = self.rr
        joints = dict(joints or self._joints_from_qpos(qpos))

        self.step += 1
        rr.set_time("step", sequence=self.step)

        for i, joint in enumerate(self.urdf_tree.joints()):
            if joint.child_link not in joints:
                continue
            value = joints[joint.child_link]
            rr.log("leap_hand/transforms", joint.compute_transform(float(value)))
            rr.log(f"/leap_hand/joints/{i}", rr.Scalars([float(value)]))

        if tip_positions:
            rr.log(
                "/leap_tips",
                rr.Points3D(
                    [tip_positions[name] for name in tip_positions],
                    labels=[f"tip_{name}" for name in tip_positions],
                    radii=0.005,
                    colors=[80, 170, 255],
                ),
                rr.CoordinateFrame(self.palm_frame_id),
            )

    def log_targets(
        self,
        target_positions: Mapping[str, Sequence[float]] | Sequence[Sequence[float]],
        *,
        names: Sequence[str] | None = None,
        already_transformed: bool = False,
    ):
        if not self.enable_rerun_visualization or self.urdf_tree is None or self.rr is None:
            return

        rr = self.rr
        target_positions = self._positions_by_name(target_positions, names)

        if not target_positions:
            return

        if not already_transformed:
            target_positions = transform_targets_for_leap_retargeting(
                target_positions,
                quest_palm_from_leap_palm=self._quest_palm_from_leap_palm,
            )

        rr.log(
            "/leap_targets",
            rr.Points3D(
                [target_positions[name] for name in target_positions],
                labels=[f"target_{name}" for name in target_positions],
                radii=0.006,
                colors=[255, 80, 80],
            ),
            rr.CoordinateFrame(self.root_frame_id),
        )

    def _joints_from_qpos(self, qpos: Sequence[float] | None) -> dict[str, float]:
        if qpos is None:
            return {}
        return {link_name: float(qpos[i]) for link_name, i in self.command_index_by_link_name.items()}

    @staticmethod
    def _positions_by_name(
        positions: Mapping[str, Sequence[float]] | Sequence[Sequence[float]],
        names: Sequence[str] | None,
    ) -> dict[str, list[float]]:
        if isinstance(positions, Mapping):
            return {str(name): [float(v) for v in point] for name, point in positions.items()}

        if names is None:
            names = tuple(str(i) for i in range(len(positions)))
        return {
            str(name): [float(v) for v in point]
            for name, point in zip(names, positions, strict=True)
        }
