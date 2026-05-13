// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from sandwich_bt_interfaces:srv/ReportSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/report_skill_verification.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__BUILDER_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "sandwich_bt_interfaces/srv/detail/report_skill_verification__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_ReportSkillVerification_Request_message
{
public:
  explicit Init_ReportSkillVerification_Request_message(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Request message(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Request msg_;
};

class Init_ReportSkillVerification_Request_status
{
public:
  explicit Init_ReportSkillVerification_Request_status(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request & msg)
  : msg_(msg)
  {}
  Init_ReportSkillVerification_Request_message status(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_ReportSkillVerification_Request_message(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Request msg_;
};

class Init_ReportSkillVerification_Request_attempt_id
{
public:
  explicit Init_ReportSkillVerification_Request_attempt_id(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request & msg)
  : msg_(msg)
  {}
  Init_ReportSkillVerification_Request_status attempt_id(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request::_attempt_id_type arg)
  {
    msg_.attempt_id = std::move(arg);
    return Init_ReportSkillVerification_Request_status(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Request msg_;
};

class Init_ReportSkillVerification_Request_skill_name
{
public:
  Init_ReportSkillVerification_Request_skill_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ReportSkillVerification_Request_attempt_id skill_name(::sandwich_bt_interfaces::srv::ReportSkillVerification_Request::_skill_name_type arg)
  {
    msg_.skill_name = std::move(arg);
    return Init_ReportSkillVerification_Request_attempt_id(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::ReportSkillVerification_Request>()
{
  return sandwich_bt_interfaces::srv::builder::Init_ReportSkillVerification_Request_skill_name();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_ReportSkillVerification_Response_message
{
public:
  explicit Init_ReportSkillVerification_Response_message(::sandwich_bt_interfaces::srv::ReportSkillVerification_Response & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Response message(::sandwich_bt_interfaces::srv::ReportSkillVerification_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Response msg_;
};

class Init_ReportSkillVerification_Response_applied_attempt_id
{
public:
  explicit Init_ReportSkillVerification_Response_applied_attempt_id(::sandwich_bt_interfaces::srv::ReportSkillVerification_Response & msg)
  : msg_(msg)
  {}
  Init_ReportSkillVerification_Response_message applied_attempt_id(::sandwich_bt_interfaces::srv::ReportSkillVerification_Response::_applied_attempt_id_type arg)
  {
    msg_.applied_attempt_id = std::move(arg);
    return Init_ReportSkillVerification_Response_message(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Response msg_;
};

class Init_ReportSkillVerification_Response_accepted
{
public:
  Init_ReportSkillVerification_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ReportSkillVerification_Response_applied_attempt_id accepted(::sandwich_bt_interfaces::srv::ReportSkillVerification_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_ReportSkillVerification_Response_applied_attempt_id(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::ReportSkillVerification_Response>()
{
  return sandwich_bt_interfaces::srv::builder::Init_ReportSkillVerification_Response_accepted();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_ReportSkillVerification_Event_response
{
public:
  explicit Init_ReportSkillVerification_Event_response(::sandwich_bt_interfaces::srv::ReportSkillVerification_Event & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Event response(::sandwich_bt_interfaces::srv::ReportSkillVerification_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Event msg_;
};

class Init_ReportSkillVerification_Event_request
{
public:
  explicit Init_ReportSkillVerification_Event_request(::sandwich_bt_interfaces::srv::ReportSkillVerification_Event & msg)
  : msg_(msg)
  {}
  Init_ReportSkillVerification_Event_response request(::sandwich_bt_interfaces::srv::ReportSkillVerification_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_ReportSkillVerification_Event_response(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Event msg_;
};

class Init_ReportSkillVerification_Event_info
{
public:
  Init_ReportSkillVerification_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ReportSkillVerification_Event_request info(::sandwich_bt_interfaces::srv::ReportSkillVerification_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_ReportSkillVerification_Event_request(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::ReportSkillVerification_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::ReportSkillVerification_Event>()
{
  return sandwich_bt_interfaces::srv::builder::Init_ReportSkillVerification_Event_info();
}

}  // namespace sandwich_bt_interfaces

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__BUILDER_HPP_
