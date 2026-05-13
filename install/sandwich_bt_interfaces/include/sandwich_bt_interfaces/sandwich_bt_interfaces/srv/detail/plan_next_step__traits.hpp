// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from sandwich_bt_interfaces:srv/PlanNextStep.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/plan_next_step.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__TRAITS_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "sandwich_bt_interfaces/srv/detail/plan_next_step__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace sandwich_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const PlanNextStep_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: goal
  {
    out << "goal: ";
    rosidl_generator_traits::value_to_yaml(msg.goal, out);
    out << ", ";
  }

  // member: current_task
  {
    out << "current_task: ";
    rosidl_generator_traits::value_to_yaml(msg.current_task, out);
    out << ", ";
  }

  // member: available_robot_skills
  {
    if (msg.available_robot_skills.size() == 0) {
      out << "available_robot_skills: []";
    } else {
      out << "available_robot_skills: [";
      size_t pending_items = msg.available_robot_skills.size();
      for (auto item : msg.available_robot_skills) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: available_human_skills
  {
    if (msg.available_human_skills.size() == 0) {
      out << "available_human_skills: []";
    } else {
      out << "available_human_skills: [";
      size_t pending_items = msg.available_human_skills.size();
      for (auto item : msg.available_human_skills) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: first_toast_on_plate
  {
    out << "first_toast_on_plate: ";
    rosidl_generator_traits::value_to_yaml(msg.first_toast_on_plate, out);
    out << ", ";
  }

  // member: ingredient_on_first_toast
  {
    out << "ingredient_on_first_toast: ";
    rosidl_generator_traits::value_to_yaml(msg.ingredient_on_first_toast, out);
    out << ", ";
  }

  // member: second_toast_on_top
  {
    out << "second_toast_on_top: ";
    rosidl_generator_traits::value_to_yaml(msg.second_toast_on_top, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const PlanNextStep_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: goal
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "goal: ";
    rosidl_generator_traits::value_to_yaml(msg.goal, out);
    out << "\n";
  }

  // member: current_task
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "current_task: ";
    rosidl_generator_traits::value_to_yaml(msg.current_task, out);
    out << "\n";
  }

  // member: available_robot_skills
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.available_robot_skills.size() == 0) {
      out << "available_robot_skills: []\n";
    } else {
      out << "available_robot_skills:\n";
      for (auto item : msg.available_robot_skills) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: available_human_skills
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.available_human_skills.size() == 0) {
      out << "available_human_skills: []\n";
    } else {
      out << "available_human_skills:\n";
      for (auto item : msg.available_human_skills) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: first_toast_on_plate
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "first_toast_on_plate: ";
    rosidl_generator_traits::value_to_yaml(msg.first_toast_on_plate, out);
    out << "\n";
  }

  // member: ingredient_on_first_toast
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ingredient_on_first_toast: ";
    rosidl_generator_traits::value_to_yaml(msg.ingredient_on_first_toast, out);
    out << "\n";
  }

  // member: second_toast_on_top
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "second_toast_on_top: ";
    rosidl_generator_traits::value_to_yaml(msg.second_toast_on_top, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const PlanNextStep_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace sandwich_bt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use sandwich_bt_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const sandwich_bt_interfaces::srv::PlanNextStep_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  sandwich_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sandwich_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const sandwich_bt_interfaces::srv::PlanNextStep_Request & msg)
{
  return sandwich_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::PlanNextStep_Request>()
{
  return "sandwich_bt_interfaces::srv::PlanNextStep_Request";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::PlanNextStep_Request>()
{
  return "sandwich_bt_interfaces/srv/PlanNextStep_Request";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::PlanNextStep_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<sandwich_bt_interfaces::srv::PlanNextStep_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace sandwich_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const PlanNextStep_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: step_name
  {
    out << "step_name: ";
    rosidl_generator_traits::value_to_yaml(msg.step_name, out);
    out << ", ";
  }

  // member: actor
  {
    out << "actor: ";
    rosidl_generator_traits::value_to_yaml(msg.actor, out);
    out << ", ";
  }

  // member: reason
  {
    out << "reason: ";
    rosidl_generator_traits::value_to_yaml(msg.reason, out);
    out << ", ";
  }

  // member: expected_state
  {
    out << "expected_state: ";
    rosidl_generator_traits::value_to_yaml(msg.expected_state, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const PlanNextStep_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: step_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "step_name: ";
    rosidl_generator_traits::value_to_yaml(msg.step_name, out);
    out << "\n";
  }

  // member: actor
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "actor: ";
    rosidl_generator_traits::value_to_yaml(msg.actor, out);
    out << "\n";
  }

  // member: reason
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "reason: ";
    rosidl_generator_traits::value_to_yaml(msg.reason, out);
    out << "\n";
  }

  // member: expected_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "expected_state: ";
    rosidl_generator_traits::value_to_yaml(msg.expected_state, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const PlanNextStep_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace sandwich_bt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use sandwich_bt_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const sandwich_bt_interfaces::srv::PlanNextStep_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  sandwich_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sandwich_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const sandwich_bt_interfaces::srv::PlanNextStep_Response & msg)
{
  return sandwich_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::PlanNextStep_Response>()
{
  return "sandwich_bt_interfaces::srv::PlanNextStep_Response";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::PlanNextStep_Response>()
{
  return "sandwich_bt_interfaces/srv/PlanNextStep_Response";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::PlanNextStep_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<sandwich_bt_interfaces::srv::PlanNextStep_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__traits.hpp"

namespace sandwich_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const PlanNextStep_Event & msg,
  std::ostream & out)
{
  out << "{";
  // member: info
  {
    out << "info: ";
    to_flow_style_yaml(msg.info, out);
    out << ", ";
  }

  // member: request
  {
    if (msg.request.size() == 0) {
      out << "request: []";
    } else {
      out << "request: [";
      size_t pending_items = msg.request.size();
      for (auto item : msg.request) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: response
  {
    if (msg.response.size() == 0) {
      out << "response: []";
    } else {
      out << "response: [";
      size_t pending_items = msg.response.size();
      for (auto item : msg.response) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const PlanNextStep_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: info
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "info:\n";
    to_block_style_yaml(msg.info, out, indentation + 2);
  }

  // member: request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.request.size() == 0) {
      out << "request: []\n";
    } else {
      out << "request:\n";
      for (auto item : msg.request) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: response
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.response.size() == 0) {
      out << "response: []\n";
    } else {
      out << "response:\n";
      for (auto item : msg.response) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const PlanNextStep_Event & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace sandwich_bt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use sandwich_bt_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const sandwich_bt_interfaces::srv::PlanNextStep_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  sandwich_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sandwich_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const sandwich_bt_interfaces::srv::PlanNextStep_Event & msg)
{
  return sandwich_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::PlanNextStep_Event>()
{
  return "sandwich_bt_interfaces::srv::PlanNextStep_Event";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::PlanNextStep_Event>()
{
  return "sandwich_bt_interfaces/srv/PlanNextStep_Event";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::PlanNextStep_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Event>
  : std::integral_constant<bool, has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Request>::value && has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<sandwich_bt_interfaces::srv::PlanNextStep_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::PlanNextStep>()
{
  return "sandwich_bt_interfaces::srv::PlanNextStep";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::PlanNextStep>()
{
  return "sandwich_bt_interfaces/srv/PlanNextStep";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::PlanNextStep>
  : std::integral_constant<
    bool,
    has_fixed_size<sandwich_bt_interfaces::srv::PlanNextStep_Request>::value &&
    has_fixed_size<sandwich_bt_interfaces::srv::PlanNextStep_Response>::value
  >
{
};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep>
  : std::integral_constant<
    bool,
    has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Request>::value &&
    has_bounded_size<sandwich_bt_interfaces::srv::PlanNextStep_Response>::value
  >
{
};

template<>
struct is_service<sandwich_bt_interfaces::srv::PlanNextStep>
  : std::true_type
{
};

template<>
struct is_service_request<sandwich_bt_interfaces::srv::PlanNextStep_Request>
  : std::true_type
{
};

template<>
struct is_service_response<sandwich_bt_interfaces::srv::PlanNextStep_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__TRAITS_HPP_
