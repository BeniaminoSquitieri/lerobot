"""Launch the LeRobot BT runner with generated XML/YAML artifacts."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build a ROS2 launch description for a generated BT artifact pair."""

    params_file = LaunchConfiguration("params_file")
    tree_xml_path = LaunchConfiguration("tree_xml_path")
    bt_command_service = LaunchConfiguration("bt_command_service")
    vlm_state_service = LaunchConfiguration("vlm_state_service")
    tick_ms = LaunchConfiguration("tick_ms")
    enable_groot_publisher = LaunchConfiguration("enable_groot_publisher")
    groot_publisher_port = LaunchConfiguration("groot_publisher_port")

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file"),
            DeclareLaunchArgument("tree_xml_path"),
            DeclareLaunchArgument("bt_command_service", default_value="/lerobot_bt/run"),
            DeclareLaunchArgument("vlm_state_service", default_value="/lerobot_bt/vlm_state"),
            DeclareLaunchArgument("tick_ms", default_value="100"),
            DeclareLaunchArgument("enable_groot_publisher", default_value="true"),
            DeclareLaunchArgument("groot_publisher_port", default_value="1667"),
            Node(
                package="lerobot_bt_runtime_cpp",
                executable="lerobot_bt_runner",
                name="lerobot_bt_runner",
                output="screen",
                parameters=[
                    params_file,
                    {
                        "tree_xml_path": tree_xml_path,
                        "bt_command_service": bt_command_service,
                        "vlm_state_service": vlm_state_service,
                        "tick_ms": ParameterValue(tick_ms, value_type=int),
                        "enable_groot_publisher": ParameterValue(
                            enable_groot_publisher,
                            value_type=bool,
                        ),
                        "groot_publisher_port": ParameterValue(
                            groot_publisher_port,
                            value_type=int,
                        ),
                    },
                ],
            ),
        ]
    )
