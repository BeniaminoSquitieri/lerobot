// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from lerobot_bt_interfaces:srv/GetSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "lerobot_bt_interfaces/srv/get_skill_verification.hpp"


#ifndef LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__TRAITS_HPP_
#define LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "lerobot_bt_interfaces/srv/detail/get_skill_verification__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace lerobot_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetSkillVerification_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: skill_name
  {
    out << "skill_name: ";
    rosidl_generator_traits::value_to_yaml(msg.skill_name, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetSkillVerification_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: skill_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "skill_name: ";
    rosidl_generator_traits::value_to_yaml(msg.skill_name, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetSkillVerification_Request & msg, bool use_flow_style = false)
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

}  // namespace lerobot_bt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use lerobot_bt_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const lerobot_bt_interfaces::srv::GetSkillVerification_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  lerobot_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use lerobot_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const lerobot_bt_interfaces::srv::GetSkillVerification_Request & msg)
{
  return lerobot_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<lerobot_bt_interfaces::srv::GetSkillVerification_Request>()
{
  return "lerobot_bt_interfaces::srv::GetSkillVerification_Request";
}

template<>
inline const char * name<lerobot_bt_interfaces::srv::GetSkillVerification_Request>()
{
  return "lerobot_bt_interfaces/srv/GetSkillVerification_Request";
}

template<>
struct has_fixed_size<lerobot_bt_interfaces::srv::GetSkillVerification_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<lerobot_bt_interfaces::srv::GetSkillVerification_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace lerobot_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetSkillVerification_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: has_attempt
  {
    out << "has_attempt: ";
    rosidl_generator_traits::value_to_yaml(msg.has_attempt, out);
    out << ", ";
  }

  // member: attempt_id
  {
    out << "attempt_id: ";
    rosidl_generator_traits::value_to_yaml(msg.attempt_id, out);
    out << ", ";
  }

  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetSkillVerification_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: has_attempt
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "has_attempt: ";
    rosidl_generator_traits::value_to_yaml(msg.has_attempt, out);
    out << "\n";
  }

  // member: attempt_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "attempt_id: ";
    rosidl_generator_traits::value_to_yaml(msg.attempt_id, out);
    out << "\n";
  }

  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetSkillVerification_Response & msg, bool use_flow_style = false)
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

}  // namespace lerobot_bt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use lerobot_bt_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const lerobot_bt_interfaces::srv::GetSkillVerification_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  lerobot_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use lerobot_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const lerobot_bt_interfaces::srv::GetSkillVerification_Response & msg)
{
  return lerobot_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<lerobot_bt_interfaces::srv::GetSkillVerification_Response>()
{
  return "lerobot_bt_interfaces::srv::GetSkillVerification_Response";
}

template<>
inline const char * name<lerobot_bt_interfaces::srv::GetSkillVerification_Response>()
{
  return "lerobot_bt_interfaces/srv/GetSkillVerification_Response";
}

template<>
struct has_fixed_size<lerobot_bt_interfaces::srv::GetSkillVerification_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<lerobot_bt_interfaces::srv::GetSkillVerification_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__traits.hpp"

namespace lerobot_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetSkillVerification_Event & msg,
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
  const GetSkillVerification_Event & msg,
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

inline std::string to_yaml(const GetSkillVerification_Event & msg, bool use_flow_style = false)
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

}  // namespace lerobot_bt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use lerobot_bt_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const lerobot_bt_interfaces::srv::GetSkillVerification_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  lerobot_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use lerobot_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const lerobot_bt_interfaces::srv::GetSkillVerification_Event & msg)
{
  return lerobot_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<lerobot_bt_interfaces::srv::GetSkillVerification_Event>()
{
  return "lerobot_bt_interfaces::srv::GetSkillVerification_Event";
}

template<>
inline const char * name<lerobot_bt_interfaces::srv::GetSkillVerification_Event>()
{
  return "lerobot_bt_interfaces/srv/GetSkillVerification_Event";
}

template<>
struct has_fixed_size<lerobot_bt_interfaces::srv::GetSkillVerification_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Event>
  : std::integral_constant<bool, has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Request>::value && has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<lerobot_bt_interfaces::srv::GetSkillVerification_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<lerobot_bt_interfaces::srv::GetSkillVerification>()
{
  return "lerobot_bt_interfaces::srv::GetSkillVerification";
}

template<>
inline const char * name<lerobot_bt_interfaces::srv::GetSkillVerification>()
{
  return "lerobot_bt_interfaces/srv/GetSkillVerification";
}

template<>
struct has_fixed_size<lerobot_bt_interfaces::srv::GetSkillVerification>
  : std::integral_constant<
    bool,
    has_fixed_size<lerobot_bt_interfaces::srv::GetSkillVerification_Request>::value &&
    has_fixed_size<lerobot_bt_interfaces::srv::GetSkillVerification_Response>::value
  >
{
};

template<>
struct has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification>
  : std::integral_constant<
    bool,
    has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Request>::value &&
    has_bounded_size<lerobot_bt_interfaces::srv::GetSkillVerification_Response>::value
  >
{
};

template<>
struct is_service<lerobot_bt_interfaces::srv::GetSkillVerification>
  : std::true_type
{
};

template<>
struct is_service_request<lerobot_bt_interfaces::srv::GetSkillVerification_Request>
  : std::true_type
{
};

template<>
struct is_service_response<lerobot_bt_interfaces::srv::GetSkillVerification_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__TRAITS_HPP_
