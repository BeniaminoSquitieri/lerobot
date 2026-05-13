// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from lerobot_bt_interfaces:srv/RunNamedCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "lerobot_bt_interfaces/srv/run_named_command.hpp"


#ifndef LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__BUILDER_HPP_
#define LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "lerobot_bt_interfaces/srv/detail/run_named_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace lerobot_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_RunNamedCommand_Request_timeout_s
{
public:
  explicit Init_RunNamedCommand_Request_timeout_s(::lerobot_bt_interfaces::srv::RunNamedCommand_Request & msg)
  : msg_(msg)
  {}
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Request timeout_s(::lerobot_bt_interfaces::srv::RunNamedCommand_Request::_timeout_s_type arg)
  {
    msg_.timeout_s = std::move(arg);
    return std::move(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Request msg_;
};

class Init_RunNamedCommand_Request_name
{
public:
  explicit Init_RunNamedCommand_Request_name(::lerobot_bt_interfaces::srv::RunNamedCommand_Request & msg)
  : msg_(msg)
  {}
  Init_RunNamedCommand_Request_timeout_s name(::lerobot_bt_interfaces::srv::RunNamedCommand_Request::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_RunNamedCommand_Request_timeout_s(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Request msg_;
};

class Init_RunNamedCommand_Request_kind
{
public:
  Init_RunNamedCommand_Request_kind()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RunNamedCommand_Request_name kind(::lerobot_bt_interfaces::srv::RunNamedCommand_Request::_kind_type arg)
  {
    msg_.kind = std::move(arg);
    return Init_RunNamedCommand_Request_name(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::lerobot_bt_interfaces::srv::RunNamedCommand_Request>()
{
  return lerobot_bt_interfaces::srv::builder::Init_RunNamedCommand_Request_kind();
}

}  // namespace lerobot_bt_interfaces


namespace lerobot_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_RunNamedCommand_Response_message
{
public:
  explicit Init_RunNamedCommand_Response_message(::lerobot_bt_interfaces::srv::RunNamedCommand_Response & msg)
  : msg_(msg)
  {}
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Response message(::lerobot_bt_interfaces::srv::RunNamedCommand_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Response msg_;
};

class Init_RunNamedCommand_Response_elapsed_s
{
public:
  explicit Init_RunNamedCommand_Response_elapsed_s(::lerobot_bt_interfaces::srv::RunNamedCommand_Response & msg)
  : msg_(msg)
  {}
  Init_RunNamedCommand_Response_message elapsed_s(::lerobot_bt_interfaces::srv::RunNamedCommand_Response::_elapsed_s_type arg)
  {
    msg_.elapsed_s = std::move(arg);
    return Init_RunNamedCommand_Response_message(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Response msg_;
};

class Init_RunNamedCommand_Response_status
{
public:
  explicit Init_RunNamedCommand_Response_status(::lerobot_bt_interfaces::srv::RunNamedCommand_Response & msg)
  : msg_(msg)
  {}
  Init_RunNamedCommand_Response_elapsed_s status(::lerobot_bt_interfaces::srv::RunNamedCommand_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_RunNamedCommand_Response_elapsed_s(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Response msg_;
};

class Init_RunNamedCommand_Response_success
{
public:
  Init_RunNamedCommand_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RunNamedCommand_Response_status success(::lerobot_bt_interfaces::srv::RunNamedCommand_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_RunNamedCommand_Response_status(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::lerobot_bt_interfaces::srv::RunNamedCommand_Response>()
{
  return lerobot_bt_interfaces::srv::builder::Init_RunNamedCommand_Response_success();
}

}  // namespace lerobot_bt_interfaces


namespace lerobot_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_RunNamedCommand_Event_response
{
public:
  explicit Init_RunNamedCommand_Event_response(::lerobot_bt_interfaces::srv::RunNamedCommand_Event & msg)
  : msg_(msg)
  {}
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Event response(::lerobot_bt_interfaces::srv::RunNamedCommand_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Event msg_;
};

class Init_RunNamedCommand_Event_request
{
public:
  explicit Init_RunNamedCommand_Event_request(::lerobot_bt_interfaces::srv::RunNamedCommand_Event & msg)
  : msg_(msg)
  {}
  Init_RunNamedCommand_Event_response request(::lerobot_bt_interfaces::srv::RunNamedCommand_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_RunNamedCommand_Event_response(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Event msg_;
};

class Init_RunNamedCommand_Event_info
{
public:
  Init_RunNamedCommand_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RunNamedCommand_Event_request info(::lerobot_bt_interfaces::srv::RunNamedCommand_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_RunNamedCommand_Event_request(msg_);
  }

private:
  ::lerobot_bt_interfaces::srv::RunNamedCommand_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::lerobot_bt_interfaces::srv::RunNamedCommand_Event>()
{
  return lerobot_bt_interfaces::srv::builder::Init_RunNamedCommand_Event_info();
}

}  // namespace lerobot_bt_interfaces

#endif  // LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__BUILDER_HPP_
