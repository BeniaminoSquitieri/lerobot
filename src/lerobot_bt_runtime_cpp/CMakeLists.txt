cmake_minimum_required(VERSION 3.16)
project(lerobot_bt_runtime_cpp)

# @file CMakeLists.txt
# @brief Builds and installs the C++ BehaviorTree.CPP LeRobot BT runtime.

# BehaviorTree.CPP and ROS2 dependencies used here are available with C++17.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Core ROS2 build/runtime dependencies.
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(lerobot_bt_interfaces REQUIRED)

# Support both BehaviorTree.CPP package names used across ROS distributions.
find_package(behaviortree_cpp QUIET)
if(behaviortree_cpp_FOUND)
  set(BTCPP_DEPENDENCY behaviortree_cpp)
else()
  find_package(behaviortree_cpp_v3 QUIET)
  if(behaviortree_cpp_v3_FOUND)
    set(BTCPP_DEPENDENCY behaviortree_cpp_v3)
  else()
    message(FATAL_ERROR
      "BehaviorTree.CPP was not found. Install the ROS package for your distro, for example "
      "'ros-${ROS_DISTRO}-behaviortree-cpp' or 'ros-${ROS_DISTRO}-behaviortree-cpp-v3', "
      "then source the ROS workspace again. If apt has no package for your ROS/Ubuntu combination, "
      "clone and build BehaviorTree.CPP from source in this workspace. You can check available packages with: "
      "apt-cache search ros-${ROS_DISTRO}-behaviortree")
  endif()
endif()

# The runner contains two custom BT leaves and the executable entry point.
add_executable(lerobot_bt_runner
  src/run_named_command_node.cpp
  src/await_scene_node.cpp
  src/lerobot_bt_main.cpp
)

# Public headers live under include/lerobot_bt_runtime_cpp.
target_include_directories(lerobot_bt_runner PRIVATE include)

# Link ROS2, generated services, and the detected BT.CPP implementation.
ament_target_dependencies(lerobot_bt_runner
  rclcpp
  lerobot_bt_interfaces
  ${BTCPP_DEPENDENCY}
)

# Install the executable where ros2 run can discover it.
install(TARGETS lerobot_bt_runner
  DESTINATION lib/${PROJECT_NAME}
)

# Install headers so downstream packages can reuse custom node declarations.
install(DIRECTORY include/
  DESTINATION include
)

# Install the generated-BT launch wrapper. XML/YAML artifacts are produced at
# runtime by lerobot_bt_python.bt_generation and are not installed here.
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Register this package and its installed resources with the ament index.
ament_package()
