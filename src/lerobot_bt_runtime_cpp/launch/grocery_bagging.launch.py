"""Launch the LeRobot BT runner with the grocery_bagging task profile."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Build the ROS2 launch description for this task-specific BT profile."""
    pkg_share = FindPackageShare("lerobot_bt_runtime_cpp")
    params_file = LaunchConfiguration("params_file")
    tree_xml_path = LaunchConfiguration("tree_xml_path")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [pkg_share, "config", "grocery_bagging_bt.yaml"]
                ),
            ),
            DeclareLaunchArgument(
                "tree_xml_path",
                default_value=PathJoinSubstitution(
                    [pkg_share, "trees", "grocery_bagging.xml"]
                ),
            ),
            Node(
                package="lerobot_bt_runtime_cpp",
                executable="lerobot_bt_runner",
                name="lerobot_bt_runner",
                output="screen",
                parameters=[
                    params_file,
                    {"tree_xml_path": tree_xml_path},
                ],
            ),
        ]
    )
