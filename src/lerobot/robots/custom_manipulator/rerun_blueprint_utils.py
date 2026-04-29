def send_custom_manipulator_blueprint(
    *,
    hand_view_name: str = "xHand",
    hand_contents: list[str] | None = None,
    hand_target_frame: str = "tf#/xhand/right_hand_link",
):
    import rerun as rr
    import rerun.blueprint as rrb

    rr.send_blueprint(
        rrb.Blueprint(
            rrb.Horizontal(
                rrb.Spatial3DView(
                    name="Panda",
                    origin="/",
                    contents=["/panda/**", "/state_eef/**", "/target_eef/**"],
                    spatial_information=rrb.SpatialInformation(
                        target_frame="tf#/panda/panda_link0",
                        show_axes=True,
                        show_bounding_box=True,
                    ),
                ),
                rrb.Spatial3DView(
                    name=hand_view_name,
                    origin="/",
                    contents=hand_contents or ["/xhand/**", "/tips/**", "/targets/**", "/forces/**"],
                    spatial_information=rrb.SpatialInformation(
                        target_frame=hand_target_frame,
                        show_axes=True,
                        show_bounding_box=True,
                    ),
                ),
            ),
        ),
    )
