// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from sandwich_bt_interfaces:srv/GetSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/get_skill_verification.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__BUILDER_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "sandwich_bt_interfaces/srv/detail/get_skill_verification__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetSkillVerification_Request_skill_name
{
public:
  Init_GetSkillVerification_Request_skill_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Request skill_name(::sandwich_bt_interfaces::srv::GetSkillVerification_Request::_skill_name_type arg)
  {
    msg_.skill_name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::GetSkillVerification_Request>()
{
  return sandwich_bt_interfaces::srv::builder::Init_GetSkillVerification_Request_skill_name();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetSkillVerification_Response_message
{
public:
  explicit Init_GetSkillVerification_Response_message(::sandwich_bt_interfaces::srv::GetSkillVerification_Response & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Response message(::sandwich_bt_interfaces::srv::GetSkillVerification_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

class Init_GetSkillVerification_Response_status
{
public:
  explicit Init_GetSkillVerification_Response_status(::sandwich_bt_interfaces::srv::GetSkillVerification_Response & msg)
  : msg_(msg)
  {}
  Init_GetSkillVerification_Response_message status(::sandwich_bt_interfaces::srv::GetSkillVerification_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_GetSkillVerification_Response_message(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

class Init_GetSkillVerification_Response_attempt_id
{
public:
  explicit Init_GetSkillVerification_Response_attempt_id(::sandwich_bt_interfaces::srv::GetSkillVerification_Response & msg)
  : msg_(msg)
  {}
  Init_GetSkillVerification_Response_status attempt_id(::sandwich_bt_interfaces::srv::GetSkillVerification_Response::_attempt_id_type arg)
  {
    msg_.attempt_id = std::move(arg);
    return Init_GetSkillVerification_Response_status(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

class Init_GetSkillVerification_Response_has_attempt
{
public:
  Init_GetSkillVerification_Response_has_attempt()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetSkillVerification_Response_attempt_id has_attempt(::sandwich_bt_interfaces::srv::GetSkillVerification_Response::_has_attempt_type arg)
  {
    msg_.has_attempt = std::move(arg);
    return Init_GetSkillVerification_Response_attempt_id(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::GetSkillVerification_Response>()
{
  return sandwich_bt_interfaces::srv::builder::Init_GetSkillVerification_Response_has_attempt();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetSkillVerification_Event_response
{
public:
  explicit Init_GetSkillVerification_Event_response(::sandwich_bt_interfaces::srv::GetSkillVerification_Event & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Event response(::sandwich_bt_interfaces::srv::GetSkillVerification_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Event msg_;
};

class Init_GetSkillVerification_Event_request
{
public:
  explicit Init_GetSkillVerification_Event_request(::sandwich_bt_interfaces::srv::GetSkillVerification_Event & msg)
  : msg_(msg)
  {}
  Init_GetSkillVerification_Event_response request(::sandwich_bt_interfaces::srv::GetSkillVerification_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_GetSkillVerification_Event_response(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Event msg_;
};

class Init_GetSkillVerification_Event_info
{
public:
  Init_GetSkillVerification_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetSkillVerification_Event_request info(::sandwich_bt_interfaces::srv::GetSkillVerification_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_GetSkillVerification_Event_request(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::GetSkillVerification_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::GetSkillVerification_Event>()
{
  return sandwich_bt_interfaces::srv::builder::Init_GetSkillVerification_Event_info();
}

}  // namespace sandwich_bt_interfaces

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__BUILDER_HPP_
