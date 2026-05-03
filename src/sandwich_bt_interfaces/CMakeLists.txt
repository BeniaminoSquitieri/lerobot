cmake_minimum_required(VERSION 3.16)
project(sandwich_bt_interfaces)

# This package does not execute anything by itself.
# It only generates the ROS2 service types shared by:
# - the Python skill server
# - the C++ BT runtime

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Single contract used between BT orchestration and robot-facing execution.
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/RunNamedCommand.srv"
  "srv/PlanNextStep.srv"
  "srv/VerifyStep.srv"
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
