"""Launch the sandwich BT runner with the lunch_table_bussing task profile."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("sandwich_bt_runtime_cpp")
    params_file = LaunchConfiguration("params_file")
    tree_xml_path = LaunchConfiguration("tree_xml_path")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [pkg_share, "config", "lunch_table_bussing_bt.yaml"]
                ),
            ),
            DeclareLaunchArgument(
                "tree_xml_path",
                default_value=PathJoinSubstitution(
                    [pkg_share, "trees", "lunch_table_bussing.xml"]
                ),
            ),
            Node(
                package="sandwich_bt_runtime_cpp",
                executable="sandwich_bt_runner",
                name="sandwich_bt_runner",
                output="screen",
                parameters=[
                    params_file,
                    {"tree_xml_path": tree_xml_path},
                ],
            ),
        ]
    )
