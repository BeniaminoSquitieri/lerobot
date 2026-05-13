// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from sandwich_bt_interfaces:srv/VerifyStep.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/verify_step.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__VERIFY_STEP__BUILDER_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__VERIFY_STEP__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "sandwich_bt_interfaces/srv/detail/verify_step__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_VerifyStep_Request_second_toast_on_top
{
public:
  explicit Init_VerifyStep_Request_second_toast_on_top(::sandwich_bt_interfaces::srv::VerifyStep_Request & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::VerifyStep_Request second_toast_on_top(::sandwich_bt_interfaces::srv::VerifyStep_Request::_second_toast_on_top_type arg)
  {
    msg_.second_toast_on_top = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Request msg_;
};

class Init_VerifyStep_Request_ingredient_on_first_toast
{
public:
  explicit Init_VerifyStep_Request_ingredient_on_first_toast(::sandwich_bt_interfaces::srv::VerifyStep_Request & msg)
  : msg_(msg)
  {}
  Init_VerifyStep_Request_second_toast_on_top ingredient_on_first_toast(::sandwich_bt_interfaces::srv::VerifyStep_Request::_ingredient_on_first_toast_type arg)
  {
    msg_.ingredient_on_first_toast = std::move(arg);
    return Init_VerifyStep_Request_second_toast_on_top(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Request msg_;
};

class Init_VerifyStep_Request_first_toast_on_plate
{
public:
  explicit Init_VerifyStep_Request_first_toast_on_plate(::sandwich_bt_interfaces::srv::VerifyStep_Request & msg)
  : msg_(msg)
  {}
  Init_VerifyStep_Request_ingredient_on_first_toast first_toast_on_plate(::sandwich_bt_interfaces::srv::VerifyStep_Request::_first_toast_on_plate_type arg)
  {
    msg_.first_toast_on_plate = std::move(arg);
    return Init_VerifyStep_Request_ingredient_on_first_toast(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Request msg_;
};

class Init_VerifyStep_Request_step_name
{
public:
  Init_VerifyStep_Request_step_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VerifyStep_Request_first_toast_on_plate step_name(::sandwich_bt_interfaces::srv::VerifyStep_Request::_step_name_type arg)
  {
    msg_.step_name = std::move(arg);
    return Init_VerifyStep_Request_first_toast_on_plate(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::VerifyStep_Request>()
{
  return sandwich_bt_interfaces::srv::builder::Init_VerifyStep_Request_step_name();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_VerifyStep_Response_confidence
{
public:
  explicit Init_VerifyStep_Response_confidence(::sandwich_bt_interfaces::srv::VerifyStep_Response & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::VerifyStep_Response confidence(::sandwich_bt_interfaces::srv::VerifyStep_Response::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Response msg_;
};

class Init_VerifyStep_Response_failure_reason
{
public:
  explicit Init_VerifyStep_Response_failure_reason(::sandwich_bt_interfaces::srv::VerifyStep_Response & msg)
  : msg_(msg)
  {}
  Init_VerifyStep_Response_confidence failure_reason(::sandwich_bt_interfaces::srv::VerifyStep_Response::_failure_reason_type arg)
  {
    msg_.failure_reason = std::move(arg);
    return Init_VerifyStep_Response_confidence(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Response msg_;
};

class Init_VerifyStep_Response_observed_state
{
public:
  explicit Init_VerifyStep_Response_observed_state(::sandwich_bt_interfaces::srv::VerifyStep_Response & msg)
  : msg_(msg)
  {}
  Init_VerifyStep_Response_failure_reason observed_state(::sandwich_bt_interfaces::srv::VerifyStep_Response::_observed_state_type arg)
  {
    msg_.observed_state = std::move(arg);
    return Init_VerifyStep_Response_failure_reason(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Response msg_;
};

class Init_VerifyStep_Response_success
{
public:
  Init_VerifyStep_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VerifyStep_Response_observed_state success(::sandwich_bt_interfaces::srv::VerifyStep_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_VerifyStep_Response_observed_state(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::VerifyStep_Response>()
{
  return sandwich_bt_interfaces::srv::builder::Init_VerifyStep_Response_success();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_VerifyStep_Event_response
{
public:
  explicit Init_VerifyStep_Event_response(::sandwich_bt_interfaces::srv::VerifyStep_Event & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::VerifyStep_Event response(::sandwich_bt_interfaces::srv::VerifyStep_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Event msg_;
};

class Init_VerifyStep_Event_request
{
public:
  explicit Init_VerifyStep_Event_request(::sandwich_bt_interfaces::srv::VerifyStep_Event & msg)
  : msg_(msg)
  {}
  Init_VerifyStep_Event_response request(::sandwich_bt_interfaces::srv::VerifyStep_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_VerifyStep_Event_response(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Event msg_;
};

class Init_VerifyStep_Event_info
{
public:
  Init_VerifyStep_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VerifyStep_Event_request info(::sandwich_bt_interfaces::srv::VerifyStep_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_VerifyStep_Event_request(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::VerifyStep_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::VerifyStep_Event>()
{
  return sandwich_bt_interfaces::srv::builder::Init_VerifyStep_Event_info();
}

}  // namespace sandwich_bt_interfaces

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__VERIFY_STEP__BUILDER_HPP_
