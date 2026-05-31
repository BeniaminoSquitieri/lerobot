cmake_minimum_required(VERSION 3.16)
project(lerobot_bt_interfaces)

# @file CMakeLists.txt
# @brief Builds the ROS2 service interface package for LeRobot BT.
#
# This package has no executable target. Its only job is generating strongly
# typed service bindings shared by the C++ behavior-tree runtime, the Python
# skill executor, and the VLM/manual verifier.

# ament_cmake provides the package/build lifecycle macros.
find_package(ament_cmake REQUIRED)
# rosidl_cmake provides rosidl_generate_interfaces().
find_package(rosidl_cmake REQUIRED)
# The generated services must be usable from C, C++, and Python nodes.
find_package(rosidl_generator_c REQUIRED)
find_package(rosidl_generator_cpp REQUIRED)
find_package(rosidl_generator_py REQUIRED)

# Generate all service contracts from srv/*.srv files in one interface package.
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/RunNamedCommand.srv"
  "srv/GetSkillVerification.srv"
  "srv/ReportSkillVerification.srv"
  "srv/GenerateTaskPlan.srv"
)

# Downstream ROS2 packages need runtime access to the generated type support.
ament_export_dependencies(rosidl_default_runtime)

# Register the package with the ament index so other packages can depend on it.
ament_package()
