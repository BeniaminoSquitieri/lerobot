// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from lerobot_bt_interfaces:srv/GetSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "lerobot_bt_interfaces/srv/get_skill_verification.hpp"


#ifndef LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__BUILDER_HPP_
#define LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "lerobot_bt_interfaces/srv/detail/get_skill_verification__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace lerobot_bt_interfaces
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
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Request skill_name(::lerobot_bt_interfaces::srv::GetSkillVerification_Request::_skill_name_type arg)
  {
    msg_.skill_name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::lerobot_bt_interfaces::srv::GetSkillVerification_Request>()
{
  return lerobot_bt_interfaces::srv::builder::Init_GetSkillVerification_Request_skill_name();
}

}  // namespace lerobot_bt_interfaces


namespace lerobot_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetSkillVerification_Response_message
{
public:
  explicit Init_GetSkillVerification_Response_message(::lerobot_bt_interfaces::srv::GetSkillVerification_Response & msg)
  : msg_(msg)
  {}
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Response message(::lerobot_bt_interfaces::srv::GetSkillVerification_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

class Init_GetSkillVerification_Response_status
{
public:
  explicit Init_GetSkillVerification_Response_status(::lerobot_bt_interfaces::srv::GetSkillVerification_Response & msg)
  : msg_(msg)
  {}
  Init_GetSkillVerification_Response_message status(::lerobot_bt_interfaces::srv::GetSkillVerification_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_GetSkillVerification_Response_message(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

class Init_GetSkillVerification_Response_attempt_id
{
public:
  explicit Init_GetSkillVerification_Response_attempt_id(::lerobot_bt_interfaces::srv::GetSkillVerification_Response & msg)
  : msg_(msg)
  {}
  Init_GetSkillVerification_Response_status attempt_id(::lerobot_bt_interfaces::srv::GetSkillVerification_Response::_attempt_id_type arg)
  {
    msg_.attempt_id = std::move(arg);
    return Init_GetSkillVerification_Response_status(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

class Init_GetSkillVerification_Response_has_attempt
{
public:
  Init_GetSkillVerification_Response_has_attempt()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetSkillVerification_Response_attempt_id has_attempt(::lerobot_bt_interfaces::srv::GetSkillVerification_Response::_has_attempt_type arg)
  {
    msg_.has_attempt = std::move(arg);
    return Init_GetSkillVerification_Response_attempt_id(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::lerobot_bt_interfaces::srv::GetSkillVerification_Response>()
{
  return lerobot_bt_interfaces::srv::builder::Init_GetSkillVerification_Response_has_attempt();
}

}  // namespace lerobot_bt_interfaces


namespace lerobot_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetSkillVerification_Event_response
{
public:
  explicit Init_GetSkillVerification_Event_response(::lerobot_bt_interfaces::srv::GetSkillVerification_Event & msg)
  : msg_(msg)
  {}
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Event response(::lerobot_bt_interfaces::srv::GetSkillVerification_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Event msg_;
};

class Init_GetSkillVerification_Event_request
{
public:
  explicit Init_GetSkillVerification_Event_request(::lerobot_bt_interfaces::srv::GetSkillVerification_Event & msg)
  : msg_(msg)
  {}
  Init_GetSkillVerification_Event_response request(::lerobot_bt_interfaces::srv::GetSkillVerification_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_GetSkillVerification_Event_response(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Event msg_;
};

class Init_GetSkillVerification_Event_info
{
public:
  Init_GetSkillVerification_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetSkillVerification_Event_request info(::lerobot_bt_interfaces::srv::GetSkillVerification_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_GetSkillVerification_Event_request(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::GetSkillVerification_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::lerobot_bt_interfaces::srv::GetSkillVerification_Event>()
{
  return lerobot_bt_interfaces::srv::builder::Init_GetSkillVerification_Event_info();
}

}  // namespace lerobot_bt_interfaces

#endif  // LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__BUILDER_HPP_
