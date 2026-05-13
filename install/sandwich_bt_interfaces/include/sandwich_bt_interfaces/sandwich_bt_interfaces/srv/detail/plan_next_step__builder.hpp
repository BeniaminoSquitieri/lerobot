// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from sandwich_bt_interfaces:srv/PlanNextStep.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/plan_next_step.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__BUILDER_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "sandwich_bt_interfaces/srv/detail/plan_next_step__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_PlanNextStep_Request_second_toast_on_top
{
public:
  explicit Init_PlanNextStep_Request_second_toast_on_top(::sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request second_toast_on_top(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_second_toast_on_top_type arg)
  {
    msg_.second_toast_on_top = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

class Init_PlanNextStep_Request_ingredient_on_first_toast
{
public:
  explicit Init_PlanNextStep_Request_ingredient_on_first_toast(::sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Request_second_toast_on_top ingredient_on_first_toast(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_ingredient_on_first_toast_type arg)
  {
    msg_.ingredient_on_first_toast = std::move(arg);
    return Init_PlanNextStep_Request_second_toast_on_top(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

class Init_PlanNextStep_Request_first_toast_on_plate
{
public:
  explicit Init_PlanNextStep_Request_first_toast_on_plate(::sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Request_ingredient_on_first_toast first_toast_on_plate(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_first_toast_on_plate_type arg)
  {
    msg_.first_toast_on_plate = std::move(arg);
    return Init_PlanNextStep_Request_ingredient_on_first_toast(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

class Init_PlanNextStep_Request_available_human_skills
{
public:
  explicit Init_PlanNextStep_Request_available_human_skills(::sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Request_first_toast_on_plate available_human_skills(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_available_human_skills_type arg)
  {
    msg_.available_human_skills = std::move(arg);
    return Init_PlanNextStep_Request_first_toast_on_plate(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

class Init_PlanNextStep_Request_available_robot_skills
{
public:
  explicit Init_PlanNextStep_Request_available_robot_skills(::sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Request_available_human_skills available_robot_skills(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_available_robot_skills_type arg)
  {
    msg_.available_robot_skills = std::move(arg);
    return Init_PlanNextStep_Request_available_human_skills(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

class Init_PlanNextStep_Request_current_task
{
public:
  explicit Init_PlanNextStep_Request_current_task(::sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Request_available_robot_skills current_task(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_current_task_type arg)
  {
    msg_.current_task = std::move(arg);
    return Init_PlanNextStep_Request_available_robot_skills(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

class Init_PlanNextStep_Request_goal
{
public:
  Init_PlanNextStep_Request_goal()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlanNextStep_Request_current_task goal(::sandwich_bt_interfaces::srv::PlanNextStep_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return Init_PlanNextStep_Request_current_task(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::PlanNextStep_Request>()
{
  return sandwich_bt_interfaces::srv::builder::Init_PlanNextStep_Request_goal();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_PlanNextStep_Response_confidence
{
public:
  explicit Init_PlanNextStep_Response_confidence(::sandwich_bt_interfaces::srv::PlanNextStep_Response & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::PlanNextStep_Response confidence(::sandwich_bt_interfaces::srv::PlanNextStep_Response::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Response msg_;
};

class Init_PlanNextStep_Response_expected_state
{
public:
  explicit Init_PlanNextStep_Response_expected_state(::sandwich_bt_interfaces::srv::PlanNextStep_Response & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Response_confidence expected_state(::sandwich_bt_interfaces::srv::PlanNextStep_Response::_expected_state_type arg)
  {
    msg_.expected_state = std::move(arg);
    return Init_PlanNextStep_Response_confidence(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Response msg_;
};

class Init_PlanNextStep_Response_reason
{
public:
  explicit Init_PlanNextStep_Response_reason(::sandwich_bt_interfaces::srv::PlanNextStep_Response & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Response_expected_state reason(::sandwich_bt_interfaces::srv::PlanNextStep_Response::_reason_type arg)
  {
    msg_.reason = std::move(arg);
    return Init_PlanNextStep_Response_expected_state(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Response msg_;
};

class Init_PlanNextStep_Response_actor
{
public:
  explicit Init_PlanNextStep_Response_actor(::sandwich_bt_interfaces::srv::PlanNextStep_Response & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Response_reason actor(::sandwich_bt_interfaces::srv::PlanNextStep_Response::_actor_type arg)
  {
    msg_.actor = std::move(arg);
    return Init_PlanNextStep_Response_reason(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Response msg_;
};

class Init_PlanNextStep_Response_step_name
{
public:
  Init_PlanNextStep_Response_step_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlanNextStep_Response_actor step_name(::sandwich_bt_interfaces::srv::PlanNextStep_Response::_step_name_type arg)
  {
    msg_.step_name = std::move(arg);
    return Init_PlanNextStep_Response_actor(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::PlanNextStep_Response>()
{
  return sandwich_bt_interfaces::srv::builder::Init_PlanNextStep_Response_step_name();
}

}  // namespace sandwich_bt_interfaces


namespace sandwich_bt_interfaces
{

namespace srv
{

namespace builder
{

class Init_PlanNextStep_Event_response
{
public:
  explicit Init_PlanNextStep_Event_response(::sandwich_bt_interfaces::srv::PlanNextStep_Event & msg)
  : msg_(msg)
  {}
  ::sandwich_bt_interfaces::srv::PlanNextStep_Event response(::sandwich_bt_interfaces::srv::PlanNextStep_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Event msg_;
};

class Init_PlanNextStep_Event_request
{
public:
  explicit Init_PlanNextStep_Event_request(::sandwich_bt_interfaces::srv::PlanNextStep_Event & msg)
  : msg_(msg)
  {}
  Init_PlanNextStep_Event_response request(::sandwich_bt_interfaces::srv::PlanNextStep_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_PlanNextStep_Event_response(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Event msg_;
};

class Init_PlanNextStep_Event_info
{
public:
  Init_PlanNextStep_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlanNextStep_Event_request info(::sandwich_bt_interfaces::srv::PlanNextStep_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_PlanNextStep_Event_request(msg_);
  }

private:
  ::sandwich_bt_interfaces::srv::PlanNextStep_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::sandwich_bt_interfaces::srv::PlanNextStep_Event>()
{
  return sandwich_bt_interfaces::srv::builder::Init_PlanNextStep_Event_info();
}

}  // namespace sandwich_bt_interfaces

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__BUILDER_HPP_
