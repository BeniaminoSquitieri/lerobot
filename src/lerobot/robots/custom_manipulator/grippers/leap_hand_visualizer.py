# pyright: reportMissingImports=false

from __future__ import annotations

from lerobot.robots.custom_manipulator.rerun_blueprint_utils import (
    send_leap_hand_blueprint,
)


def transform_leap_target_positions(
    target_positions: dict[str, list[float]],
    *,
    base_rotation: list[list[float]] | None = None,
) -> dict[str, list[float]]:
    if not target_positions:
        return {}

    transformed = {name: [float(v) for v in pos] for name, pos in target_positions.items()}

    if "wrist" in transformed:
        wrist = transformed["wrist"]
        transformed = {
            name: [float(v - w) for v, w in zip(pos, wrist, strict=True)]
            for name, pos in transformed.items()
        }

    if base_rotation is not None:
        rot_t = [
            [float(base_rotation[row][col]) for row in range(3)]
            for col in range(3)
        ]
        transformed = {
            name: [
                float(sum(rot_t[row][col] * pos[col] for col in range(3)))
                for row in range(3)
            ]
            for name, pos in transformed.items()
        }

    y_neg_90 = (
        (0.0, 0.0, -1.0),
        (0.0, 1.0, 0.0),
        (1.0, 0.0, 0.0),
    )
    return {
        name: [
            float(sum(y_neg_90[row][col] * pos[col] for col in range(3)))
            for row in range(3)
        ]
        for name, pos in transformed.items()
    }


class LeapHandDebugTools:
    def __init__(
        self,
        urdf_path: str,
        enable_rerun_visualization: bool,
        palm_link_name: str,
        root_link_name: str,
        palm_to_root_offset: list[float] | tuple[float, float, float] | None = None,
        base_rotation: list[list[float]] | None = None,
    ):
        self.enable_rerun_visualization = enable_rerun_visualization
        self.step = 0
        self.root_entity_path = f"/leap_hand/{root_link_name}"
        self.palm_frame_id = f"tf#/leap_hand/{palm_link_name}"
        self.root_frame_id = f"tf#/leap_hand/{root_link_name}"
        self._palm_to_root_offset = [float(v) for v in (palm_to_root_offset or (0.0, 0.0, 0.0))]
        self._base_rotation = (
            [[float(v) for v in row] for row in base_rotation] if base_rotation is not None else None
        )
        self.urdf_tree = None
        self.rr = None

        if not self.enable_rerun_visualization:
            return

        import rerun as rr
        from rerun.urdf import UrdfTree

        self.rr = rr

        created_rerun_session = False
        if not rr.is_enabled():
            rr.init("leap_hand_debug", spawn=True)
            created_rerun_session = True

        self.urdf_tree = UrdfTree.from_file_path(
            urdf_path,
            entity_path_prefix="leap_hand",
            frame_prefix="tf#/leap_hand/",
        )
        self.urdf_tree.log_urdf_to_recording()
        if base_rotation is not None:
            rr.log(
                self.root_entity_path,
                rr.Transform3D(
                    translation=[0.0, 0.0, 0.0],
                    mat3x3=base_rotation,
                    relation=rr.TransformRelation.ParentFromChild,
                ),
                static=True,
            )
        # Set the initial view so +X is up, +Y points toward the viewer, +Z points right.
        rr.log(self.root_entity_path, rr.ViewCoordinates.UBR, static=True)
        if created_rerun_session:
            send_leap_hand_blueprint(
                hand_view_name="LeapHand",
                hand_contents=["/leap_hand/**", "/leap_targets/**", "/leap_tips/**"],
                hand_target_frame=self.root_frame_id,
            )

    def close(self):
        return None

    def log_state(self, joints: dict[str, float], tip_positions: dict[str, list[float]]):
        if not self.enable_rerun_visualization or self.urdf_tree is None or self.rr is None:
            return

        rr = self.rr

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

    def log_targets(self, target_positions: dict[str, list[float]], already_transformed: bool = False):
        if not self.enable_rerun_visualization or self.urdf_tree is None or self.rr is None:
            return

        rr = self.rr

        if not target_positions:
            return

        if not already_transformed:
            target_positions = transform_leap_target_positions(
                target_positions,
                base_rotation=self._base_rotation,
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
