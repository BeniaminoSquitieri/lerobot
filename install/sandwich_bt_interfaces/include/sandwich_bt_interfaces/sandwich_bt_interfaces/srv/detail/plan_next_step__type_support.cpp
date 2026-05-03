// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from sandwich_bt_interfaces:srv/PlanNextStep.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"
#include "sandwich_bt_interfaces/srv/detail/plan_next_step__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace sandwich_bt_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void PlanNextStep_Request_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) sandwich_bt_interfaces::srv::PlanNextStep_Request(_init);
}

void PlanNextStep_Request_fini_function(void * message_memory)
{
  auto typed_message = static_cast<sandwich_bt_interfaces::srv::PlanNextStep_Request *>(message_memory);
  typed_message->~PlanNextStep_Request();
}

size_t size_function__PlanNextStep_Request__available_robot_skills(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return member->size();
}

const void * get_const_function__PlanNextStep_Request__available_robot_skills(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void * get_function__PlanNextStep_Request__available_robot_skills(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void fetch_function__PlanNextStep_Request__available_robot_skills(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const std::string *>(
    get_const_function__PlanNextStep_Request__available_robot_skills(untyped_member, index));
  auto & value = *reinterpret_cast<std::string *>(untyped_value);
  value = item;
}

void assign_function__PlanNextStep_Request__available_robot_skills(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<std::string *>(
    get_function__PlanNextStep_Request__available_robot_skills(untyped_member, index));
  const auto & value = *reinterpret_cast<const std::string *>(untyped_value);
  item = value;
}

void resize_function__PlanNextStep_Request__available_robot_skills(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<std::string> *>(untyped_member);
  member->resize(size);
}

size_t size_function__PlanNextStep_Request__available_human_skills(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return member->size();
}

const void * get_const_function__PlanNextStep_Request__available_human_skills(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void * get_function__PlanNextStep_Request__available_human_skills(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void fetch_function__PlanNextStep_Request__available_human_skills(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const std::string *>(
    get_const_function__PlanNextStep_Request__available_human_skills(untyped_member, index));
  auto & value = *reinterpret_cast<std::string *>(untyped_value);
  value = item;
}

void assign_function__PlanNextStep_Request__available_human_skills(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<std::string *>(
    get_function__PlanNextStep_Request__available_human_skills(untyped_member, index));
  const auto & value = *reinterpret_cast<const std::string *>(untyped_value);
  item = value;
}

void resize_function__PlanNextStep_Request__available_human_skills(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<std::string> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember PlanNextStep_Request_message_member_array[7] = {
  {
    "goal",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, goal),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "current_task",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, current_task),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "available_robot_skills",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, available_robot_skills),  // bytes offset in struct
    nullptr,  // default value
    size_function__PlanNextStep_Request__available_robot_skills,  // size() function pointer
    get_const_function__PlanNextStep_Request__available_robot_skills,  // get_const(index) function pointer
    get_function__PlanNextStep_Request__available_robot_skills,  // get(index) function pointer
    fetch_function__PlanNextStep_Request__available_robot_skills,  // fetch(index, &value) function pointer
    assign_function__PlanNextStep_Request__available_robot_skills,  // assign(index, value) function pointer
    resize_function__PlanNextStep_Request__available_robot_skills  // resize(index) function pointer
  },
  {
    "available_human_skills",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, available_human_skills),  // bytes offset in struct
    nullptr,  // default value
    size_function__PlanNextStep_Request__available_human_skills,  // size() function pointer
    get_const_function__PlanNextStep_Request__available_human_skills,  // get_const(index) function pointer
    get_function__PlanNextStep_Request__available_human_skills,  // get(index) function pointer
    fetch_function__PlanNextStep_Request__available_human_skills,  // fetch(index, &value) function pointer
    assign_function__PlanNextStep_Request__available_human_skills,  // assign(index, value) function pointer
    resize_function__PlanNextStep_Request__available_human_skills  // resize(index) function pointer
  },
  {
    "first_toast_on_plate",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, first_toast_on_plate),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "ingredient_on_first_toast",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, ingredient_on_first_toast),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "second_toast_on_top",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Request, second_toast_on_top),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers PlanNextStep_Request_message_members = {
  "sandwich_bt_interfaces::srv",  // message namespace
  "PlanNextStep_Request",  // message name
  7,  // number of fields
  sizeof(sandwich_bt_interfaces::srv::PlanNextStep_Request),
  false,  // has_any_key_member_
  PlanNextStep_Request_message_member_array,  // message members
  PlanNextStep_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  PlanNextStep_Request_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t PlanNextStep_Request_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &PlanNextStep_Request_message_members,
  get_message_typesupport_handle_function,
  &sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_hash,
  &sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_description,
  &sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace sandwich_bt_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Request>()
{
  return &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_Request_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, sandwich_bt_interfaces, srv, PlanNextStep_Request)() {
  return &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "array"
// already included above
// #include "cstddef"
// already included above
// #include "string"
// already included above
// #include "vector"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"
// already included above
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/field_types.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace sandwich_bt_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void PlanNextStep_Response_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) sandwich_bt_interfaces::srv::PlanNextStep_Response(_init);
}

void PlanNextStep_Response_fini_function(void * message_memory)
{
  auto typed_message = static_cast<sandwich_bt_interfaces::srv::PlanNextStep_Response *>(message_memory);
  typed_message->~PlanNextStep_Response();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember PlanNextStep_Response_message_member_array[5] = {
  {
    "step_name",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Response, step_name),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "actor",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Response, actor),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "reason",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Response, reason),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "expected_state",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Response, expected_state),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "confidence",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Response, confidence),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers PlanNextStep_Response_message_members = {
  "sandwich_bt_interfaces::srv",  // message namespace
  "PlanNextStep_Response",  // message name
  5,  // number of fields
  sizeof(sandwich_bt_interfaces::srv::PlanNextStep_Response),
  false,  // has_any_key_member_
  PlanNextStep_Response_message_member_array,  // message members
  PlanNextStep_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  PlanNextStep_Response_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t PlanNextStep_Response_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &PlanNextStep_Response_message_members,
  get_message_typesupport_handle_function,
  &sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_hash,
  &sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_description,
  &sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace sandwich_bt_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Response>()
{
  return &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_Response_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, sandwich_bt_interfaces, srv, PlanNextStep_Response)() {
  return &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "array"
// already included above
// #include "cstddef"
// already included above
// #include "string"
// already included above
// #include "vector"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"
// already included above
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/field_types.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace sandwich_bt_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void PlanNextStep_Event_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) sandwich_bt_interfaces::srv::PlanNextStep_Event(_init);
}

void PlanNextStep_Event_fini_function(void * message_memory)
{
  auto typed_message = static_cast<sandwich_bt_interfaces::srv::PlanNextStep_Event *>(message_memory);
  typed_message->~PlanNextStep_Event();
}

size_t size_function__PlanNextStep_Event__request(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Request> *>(untyped_member);
  return member->size();
}

const void * get_const_function__PlanNextStep_Event__request(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Request> *>(untyped_member);
  return &member[index];
}

void * get_function__PlanNextStep_Event__request(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Request> *>(untyped_member);
  return &member[index];
}

void fetch_function__PlanNextStep_Event__request(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const sandwich_bt_interfaces::srv::PlanNextStep_Request *>(
    get_const_function__PlanNextStep_Event__request(untyped_member, index));
  auto & value = *reinterpret_cast<sandwich_bt_interfaces::srv::PlanNextStep_Request *>(untyped_value);
  value = item;
}

void assign_function__PlanNextStep_Event__request(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<sandwich_bt_interfaces::srv::PlanNextStep_Request *>(
    get_function__PlanNextStep_Event__request(untyped_member, index));
  const auto & value = *reinterpret_cast<const sandwich_bt_interfaces::srv::PlanNextStep_Request *>(untyped_value);
  item = value;
}

void resize_function__PlanNextStep_Event__request(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Request> *>(untyped_member);
  member->resize(size);
}

size_t size_function__PlanNextStep_Event__response(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Response> *>(untyped_member);
  return member->size();
}

const void * get_const_function__PlanNextStep_Event__response(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Response> *>(untyped_member);
  return &member[index];
}

void * get_function__PlanNextStep_Event__response(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Response> *>(untyped_member);
  return &member[index];
}

void fetch_function__PlanNextStep_Event__response(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const sandwich_bt_interfaces::srv::PlanNextStep_Response *>(
    get_const_function__PlanNextStep_Event__response(untyped_member, index));
  auto & value = *reinterpret_cast<sandwich_bt_interfaces::srv::PlanNextStep_Response *>(untyped_value);
  value = item;
}

void assign_function__PlanNextStep_Event__response(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<sandwich_bt_interfaces::srv::PlanNextStep_Response *>(
    get_function__PlanNextStep_Event__response(untyped_member, index));
  const auto & value = *reinterpret_cast<const sandwich_bt_interfaces::srv::PlanNextStep_Response *>(untyped_value);
  item = value;
}

void resize_function__PlanNextStep_Event__response(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<sandwich_bt_interfaces::srv::PlanNextStep_Response> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember PlanNextStep_Event_message_member_array[3] = {
  {
    "info",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<service_msgs::msg::ServiceEventInfo>(),  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Event, info),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "request",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Request>(),  // members of sub message
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Event, request),  // bytes offset in struct
    nullptr,  // default value
    size_function__PlanNextStep_Event__request,  // size() function pointer
    get_const_function__PlanNextStep_Event__request,  // get_const(index) function pointer
    get_function__PlanNextStep_Event__request,  // get(index) function pointer
    fetch_function__PlanNextStep_Event__request,  // fetch(index, &value) function pointer
    assign_function__PlanNextStep_Event__request,  // assign(index, value) function pointer
    resize_function__PlanNextStep_Event__request  // resize(index) function pointer
  },
  {
    "response",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Response>(),  // members of sub message
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(sandwich_bt_interfaces::srv::PlanNextStep_Event, response),  // bytes offset in struct
    nullptr,  // default value
    size_function__PlanNextStep_Event__response,  // size() function pointer
    get_const_function__PlanNextStep_Event__response,  // get_const(index) function pointer
    get_function__PlanNextStep_Event__response,  // get(index) function pointer
    fetch_function__PlanNextStep_Event__response,  // fetch(index, &value) function pointer
    assign_function__PlanNextStep_Event__response,  // assign(index, value) function pointer
    resize_function__PlanNextStep_Event__response  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers PlanNextStep_Event_message_members = {
  "sandwich_bt_interfaces::srv",  // message namespace
  "PlanNextStep_Event",  // message name
  3,  // number of fields
  sizeof(sandwich_bt_interfaces::srv::PlanNextStep_Event),
  false,  // has_any_key_member_
  PlanNextStep_Event_message_member_array,  // message members
  PlanNextStep_Event_init_function,  // function to initialize message memory (memory has to be allocated)
  PlanNextStep_Event_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t PlanNextStep_Event_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &PlanNextStep_Event_message_members,
  get_message_typesupport_handle_function,
  &sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_hash,
  &sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_description,
  &sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace sandwich_bt_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Event>()
{
  return &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_Event_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, sandwich_bt_interfaces, srv, PlanNextStep_Event)() {
  return &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_Event_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"
// already included above
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"
// already included above
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/service_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/service_type_support_decl.hpp"

namespace sandwich_bt_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

// this is intentionally not const to allow initialization later to prevent an initialization race
static ::rosidl_typesupport_introspection_cpp::ServiceMembers PlanNextStep_service_members = {
  "sandwich_bt_interfaces::srv",  // service namespace
  "PlanNextStep",  // service name
  // the following fields are initialized below on first access
  // see get_service_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep>()
  nullptr,  // request message
  nullptr,  // response message
  nullptr,  // event message
};

static const rosidl_service_type_support_t PlanNextStep_service_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &PlanNextStep_service_members,
  get_service_typesupport_handle_function,
  ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Request>(),
  ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Response>(),
  ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep_Event>(),
  &::rosidl_typesupport_cpp::service_create_event_message<sandwich_bt_interfaces::srv::PlanNextStep>,
  &::rosidl_typesupport_cpp::service_destroy_event_message<sandwich_bt_interfaces::srv::PlanNextStep>,
  &sandwich_bt_interfaces__srv__PlanNextStep__get_type_hash,
  &sandwich_bt_interfaces__srv__PlanNextStep__get_type_description,
  &sandwich_bt_interfaces__srv__PlanNextStep__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace sandwich_bt_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep>()
{
  // get a handle to the value to be returned
  auto service_type_support =
    &::sandwich_bt_interfaces::srv::rosidl_typesupport_introspection_cpp::PlanNextStep_service_type_support_handle;
  // get a non-const and properly typed version of the data void *
  auto service_members = const_cast<::rosidl_typesupport_introspection_cpp::ServiceMembers *>(
    static_cast<const ::rosidl_typesupport_introspection_cpp::ServiceMembers *>(
      service_type_support->data));
  // make sure all of the service_members are initialized
  // if they are not, initialize them
  if (
    service_members->request_members_ == nullptr ||
    service_members->response_members_ == nullptr ||
    service_members->event_members_ == nullptr)
  {
    // initialize the request_members_ with the static function from the external library
    service_members->request_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::sandwich_bt_interfaces::srv::PlanNextStep_Request
      >()->data
      );
    // initialize the response_members_ with the static function from the external library
    service_members->response_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::sandwich_bt_interfaces::srv::PlanNextStep_Response
      >()->data
      );
    // initialize the event_members_ with the static function from the external library
    service_members->event_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::sandwich_bt_interfaces::srv::PlanNextStep_Event
      >()->data
      );
  }
  // finally return the properly initialized service_type_support handle
  return service_type_support;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, sandwich_bt_interfaces, srv, PlanNextStep)() {
  return ::rosidl_typesupport_introspection_cpp::get_service_type_support_handle<sandwich_bt_interfaces::srv::PlanNextStep>();
}

#ifdef __cplusplus
}
#endif
