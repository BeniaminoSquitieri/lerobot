cmake_minimum_required(VERSION 3.16)
project(sandwich_bt_runtime_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(sandwich_bt_interfaces REQUIRED)

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

add_executable(sandwich_bt_runner
  src/run_named_command_node.cpp
  src/sandwich_bt_main.cpp
  src/verify_skill_outcome_node.cpp
)

target_include_directories(sandwich_bt_runner PRIVATE include)

ament_target_dependencies(sandwich_bt_runner
  rclcpp
  ament_index_cpp
  sandwich_bt_interfaces
  ${BTCPP_DEPENDENCY}
)

install(TARGETS sandwich_bt_runner
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY trees
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
