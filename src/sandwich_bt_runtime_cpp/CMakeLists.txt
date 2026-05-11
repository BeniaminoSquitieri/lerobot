cmake_minimum_required(VERSION 3.16)
project(sandwich_bt_runtime_cpp)

# @file CMakeLists.txt
# @brief Builds and installs the C++ BehaviorTree.CPP sandwich runtime.

# BehaviorTree.CPP and ROS2 dependencies used here are available with C++17.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Core ROS2 build/runtime dependencies.
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(sandwich_bt_interfaces REQUIRED)

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
add_executable(sandwich_bt_runner
  src/run_named_command_node.cpp
  src/sandwich_bt_main.cpp
  src/verify_skill_outcome_node.cpp
)

# Public headers live under include/sandwich_bt_runtime_cpp.
target_include_directories(sandwich_bt_runner PRIVATE include)

# Link ROS2, generated services, and the detected BT.CPP implementation.
ament_target_dependencies(sandwich_bt_runner
  rclcpp
  ament_index_cpp
  sandwich_bt_interfaces
  ${BTCPP_DEPENDENCY}
)

# Install the executable where ros2 run can discover it.
install(TARGETS sandwich_bt_runner
  DESTINATION lib/${PROJECT_NAME}
)

# Install headers so downstream packages can reuse custom node declarations.
install(DIRECTORY include/
  DESTINATION include
)

# Explicit tree list prevents accidentally installing scratch or duplicate XML.
set(SANDWICH_BT_TREE_FILES
  trees/grocery_bagging.xml
  trees/items_in_drawer.xml
  trees/lunch_table_bussing.xml
  trees/make_coffee.xml
  trees/makesandwitch.xml
)
set(SANDWICH_BT_CONFIG_FILES
  config/grocery_bagging_bt.yaml
  config/items_in_drawer_bt.yaml
  config/lunch_table_bussing_bt.yaml
  config/make_coffee_bt.yaml
  config/makesandwitch_bt.yaml
)
set(SANDWICH_BT_DIAGRAM_FILES
  diagrams/grocery_bagging_bt.png
  diagrams/items_in_drawer_bt.png
  diagrams/lunch_table_bussing_bt.png
  diagrams/make_coffee_bt.png
  diagrams/makesandwitch_bt.png
)

# Install only the curated tree/subtree XML files into the package share path.
install(FILES ${SANDWICH_BT_TREE_FILES}
  DESTINATION share/${PROJECT_NAME}/trees
)

# Install task-level BT parameter profiles.
install(FILES ${SANDWICH_BT_CONFIG_FILES}
  DESTINATION share/${PROJECT_NAME}/config
)

# Install rendered BT diagrams for reports and quick inspection.
install(FILES ${SANDWICH_BT_DIAGRAM_FILES}
  DESTINATION share/${PROJECT_NAME}/diagrams
)

# Install launch files for one-command BT runner startup.
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Register this package and its installed resources with the ament index.
ament_package()
