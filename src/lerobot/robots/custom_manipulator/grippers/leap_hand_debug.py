import numpy as np

from ..rerun_blueprint_utils import send_custom_manipulator_blueprint


class LeapHandDebugTools:
    def __init__(
        self,
        urdf_path: str,
        tip_names: tuple[str, ...],
        tip_scale_factors: dict[str, float],
        enable_tip_scale_tuner: bool,
        enable_rerun_visualization: bool,
        palm_frame,
        root_frame,
        palm_center_offset: np.ndarray,
        tips,
        palm_to_target_rot: np.ndarray,
        entity_path: str = "leap_hand",
    ):
        self.tip_names = tip_names
        self.tip_scale_factors = tip_scale_factors
        self._step = 0
        self._tip_scale_root = None
        self._enable_rerun_visualization = enable_rerun_visualization
        self._rr = None
        self.palm_frame = palm_frame
        self.root_frame = root_frame
        self.palm_center_offset = np.asarray(palm_center_offset, dtype=float)
        self.tips = tips
        self.urdf_tree = None
        self.palm_to_target_rot = np.array(palm_to_target_rot, dtype=float, copy=True)
        self._entity_path = entity_path
        self._root_frame_id = f"tf#/{entity_path}/palm_center"
        self._root_link_frame_id = f"{self._root_frame_id}/{root_frame.getName()}"

        if self._enable_rerun_visualization:
            try:
                import rerun as rr
                from rerun.urdf import UrdfTree
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "LEAP hand visualization requires the optional `rerun` package."
                ) from exc

            self._rr = rr
            if not rr.is_enabled():
                rr.init("custom_manipulator_debug", spawn=True)
            self.urdf_tree = UrdfTree.from_file_path(
                urdf_path,
                entity_path_prefix=entity_path,
                frame_prefix=f"{self._root_frame_id}/",
            )
            self.urdf_tree.log_urdf_to_recording()
            self._log_root_link_offset()
            send_custom_manipulator_blueprint(
                hand_view_name="Leap Hand",
                hand_contents=[f"/{entity_path}/**", "/tips/**", "/targets/**", "/forces/**"],
                hand_target_frame=self._root_frame_id,
            )

        if enable_tip_scale_tuner:
            import tkinter as tk

            self._tip_scale_root = tk.Tk()
            self._tip_scale_root.title("leap_hand_tip_scales")
            for tip in self.tip_names:
                scale = tk.Scale(
                    self._tip_scale_root,
                    from_=0,
                    to=300,
                    orient=tk.HORIZONTAL,
                    label=tip,
                    command=lambda value, tip_name=tip: self.tip_scale_factors.__setitem__(
                        tip_name, float(value) / 100.0
                    ),
                )
                scale.set(int(self.tip_scale_factors[tip] * 100))
                scale.pack(fill="x")
            self.poll()

    def poll(self):
        if self._tip_scale_root is not None:
            self._tip_scale_root.update_idletasks()
            self._tip_scale_root.update()

    def close(self):
        if self._tip_scale_root is not None:
            self._tip_scale_root.destroy()
            self._tip_scale_root = None

    def log_state(
        self,
        joints: dict[str, float],
        fingertip_values: dict[str, float],
        forces: dict[str, float] | None = None,
    ):
        del forces
        if not self._enable_rerun_visualization or self.urdf_tree is None or self._rr is None:
            return

        self._step += 1
        self._rr.set_time("step", sequence=self._step)
        self._log_root_link_offset()

        for i, joint in enumerate(self.urdf_tree.joints()):
            if joint.child_link not in joints:
                continue

            value = joints[joint.child_link]
            if hasattr(value, "getValue"):
                value = value.getValue()
            self._rr.log(f"{self._entity_path}/transforms", joint.compute_transform(value))
            self._rr.log(f"/{self._entity_path}/joints/{i}", self._rr.Scalars([value]))

        root_tip_positions = {
            tip: [
                float(v)
                for v in (
                    self.palm_to_target_rot
                    @ (
                        np.array(
                            [fingertip_values[f"{tip}.position.{axis}"] for axis in "xyz"],
                            dtype=float,
                        )
                        * self.tip_scale_factors[tip]
                    )
                ).tolist()
            ]
            for tip in self.tip_names
            if all(f"{tip}.position.{axis}" in fingertip_values for axis in "xyz")
        }
        self._log_points("/tips", root_tip_positions, "tip", [80, 170, 255], 0.004)

    def log_targets(self, target_positions: dict[str, list[float]] | None):
        if not self._enable_rerun_visualization or self.urdf_tree is None or self._rr is None or not target_positions:
            return

        self._log_root_link_offset()
        self._log_points("/targets", target_positions, "target", [255, 80, 80], 0.005)

    def _log_points(
        self,
        path: str,
        points_by_tip: dict[str, list[float]],
        prefix: str,
        color: list[int],
        radius: float,
    ):
        if not points_by_tip or self._rr is None:
            return

        visible_tips = [tip for tip in self.tip_names if tip in points_by_tip]
        self._rr.log(
            path,
            self._rr.Points3D(
                [points_by_tip[tip] for tip in visible_tips],
                labels=[f"{prefix}_{tip}" for tip in visible_tips],
                radii=radius,
                colors=color,
            ),
            self._rr.CoordinateFrame(self._root_frame_id),
        )

    def _log_root_link_offset(self):
        if self._rr is None:
            return

        self._rr.log(
            self._root_link_frame_id,
            self._rr.Transform3D(translation=(-self.palm_center_offset).tolist()),
        )
