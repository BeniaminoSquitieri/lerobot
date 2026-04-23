cmake_minimum_required(VERSION 3.16)
project(sandwich_bt_runtime_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(sandwich_bt_interfaces REQUIRED)

find_package(behaviortree_cpp QUIET)
set(BTCPP_DEPENDENCY behaviortree_cpp)
if(NOT behaviortree_cpp_FOUND)
  find_package(behaviortree_cpp_v3 REQUIRED)
  set(BTCPP_DEPENDENCY behaviortree_cpp_v3)
endif()

add_executable(sandwich_bt_runner
  src/run_named_command_node.cpp
  src/sandwich_bt_main.cpp
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
