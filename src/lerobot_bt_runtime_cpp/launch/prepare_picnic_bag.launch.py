# Comment: executes this BT logic statement.
"""Launch the LeRobot BT runner with the prepare_picnic_bag task profile."""

# Comment: imports dependencies or symbols required by the module.
from launch import LaunchDescription
# Comment: imports dependencies or symbols required by the module.
from launch.actions import DeclareLaunchArgument
# Comment: imports dependencies or symbols required by the module.
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
# Comment: imports dependencies or symbols required by the module.
from launch_ros.actions import Node
# Comment: imports dependencies or symbols required by the module.
from launch_ros.substitutions import FindPackageShare


# Comment: defines the function or method generate_launch_description.
def generate_launch_description():
    # Comment: executes this BT logic statement.
    """Build the ROS2 launch description for this task-specific BT profile."""
    # Comment: assigns or prepares a value used by later statements.
    pkg_share = FindPackageShare("lerobot_bt_runtime_cpp")
    # Comment: assigns or prepares a value used by later statements.
    params_file = LaunchConfiguration("params_file")
    # Comment: assigns or prepares a value used by later statements.
    tree_xml_path = LaunchConfiguration("tree_xml_path")

    # Comment: returns the computed value to the caller.
    return LaunchDescription(
        # Comment: executes this BT logic statement.
        [
            # Comment: executes this BT logic statement.
            DeclareLaunchArgument(
                # Comment: executes this BT logic statement.
                "params_file",
                # Comment: assigns or prepares a value used by later statements.
                default_value=PathJoinSubstitution(
                    # Comment: closes a call, data structure, or multiline block.
                    [pkg_share, "config", "prepare_picnic_bag_bt.yaml"]
                # Comment: executes this BT logic statement.
                ),
            # Comment: executes this BT logic statement.
            ),
            # Comment: executes this BT logic statement.
            DeclareLaunchArgument(
                # Comment: executes this BT logic statement.
                "tree_xml_path",
                # Comment: assigns or prepares a value used by later statements.
                default_value=PathJoinSubstitution(
                    # Comment: closes a call, data structure, or multiline block.
                    [pkg_share, "trees", "prepare_picnic_bag.xml"]
                # Comment: executes this BT logic statement.
                ),
            # Comment: executes this BT logic statement.
            ),
            # Comment: executes this BT logic statement.
            Node(
                # Comment: assigns or prepares a value used by later statements.
                package="lerobot_bt_runtime_cpp",
                # Comment: assigns or prepares a value used by later statements.
                executable="lerobot_bt_runner",
                # Comment: assigns or prepares a value used by later statements.
                name="lerobot_bt_runner",
                # Comment: assigns or prepares a value used by later statements.
                output="screen",
                # Comment: assigns or prepares a value used by later statements.
                parameters=[
                    # Comment: executes this BT logic statement.
                    params_file,
                    # Comment: executes this BT logic statement.
                    {"tree_xml_path": tree_xml_path},
                # Comment: executes this BT logic statement.
                ],
            # Comment: executes this BT logic statement.
            ),
        # Comment: closes a call, data structure, or multiline block.
        ]
    # Comment: closes a call, data structure, or multiline block.
    )
