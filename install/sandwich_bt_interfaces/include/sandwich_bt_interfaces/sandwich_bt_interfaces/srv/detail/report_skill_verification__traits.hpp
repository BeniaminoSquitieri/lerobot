// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from sandwich_bt_interfaces:srv/ReportSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/report_skill_verification.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__TRAITS_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "sandwich_bt_interfaces/srv/detail/report_skill_verification__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace sandwich_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ReportSkillVerification_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: skill_name
  {
    out << "skill_name: ";
    rosidl_generator_traits::value_to_yaml(msg.skill_name, out);
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
  const ReportSkillVerification_Request & msg,
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

inline std::string to_yaml(const ReportSkillVerification_Request & msg, bool use_flow_style = false)
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
  const sandwich_bt_interfaces::srv::ReportSkillVerification_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  sandwich_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sandwich_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const sandwich_bt_interfaces::srv::ReportSkillVerification_Request & msg)
{
  return sandwich_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>()
{
  return "sandwich_bt_interfaces::srv::ReportSkillVerification_Request";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>()
{
  return "sandwich_bt_interfaces/srv/ReportSkillVerification_Request";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace sandwich_bt_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ReportSkillVerification_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: accepted
  {
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << ", ";
  }

  // member: applied_attempt_id
  {
    out << "applied_attempt_id: ";
    rosidl_generator_traits::value_to_yaml(msg.applied_attempt_id, out);
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
  const ReportSkillVerification_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: accepted
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "accepted: ";
    rosidl_generator_traits::value_to_yaml(msg.accepted, out);
    out << "\n";
  }

  // member: applied_attempt_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "applied_attempt_id: ";
    rosidl_generator_traits::value_to_yaml(msg.applied_attempt_id, out);
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

inline std::string to_yaml(const ReportSkillVerification_Response & msg, bool use_flow_style = false)
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
  const sandwich_bt_interfaces::srv::ReportSkillVerification_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  sandwich_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sandwich_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const sandwich_bt_interfaces::srv::ReportSkillVerification_Response & msg)
{
  return sandwich_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>()
{
  return "sandwich_bt_interfaces::srv::ReportSkillVerification_Response";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>()
{
  return "sandwich_bt_interfaces/srv/ReportSkillVerification_Response";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>
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
  const ReportSkillVerification_Event & msg,
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
  const ReportSkillVerification_Event & msg,
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

inline std::string to_yaml(const ReportSkillVerification_Event & msg, bool use_flow_style = false)
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
  const sandwich_bt_interfaces::srv::ReportSkillVerification_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  sandwich_bt_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sandwich_bt_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const sandwich_bt_interfaces::srv::ReportSkillVerification_Event & msg)
{
  return sandwich_bt_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::ReportSkillVerification_Event>()
{
  return "sandwich_bt_interfaces::srv::ReportSkillVerification_Event";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::ReportSkillVerification_Event>()
{
  return "sandwich_bt_interfaces/srv/ReportSkillVerification_Event";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Event>
  : std::integral_constant<bool, has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>::value && has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<sandwich_bt_interfaces::srv::ReportSkillVerification_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<sandwich_bt_interfaces::srv::ReportSkillVerification>()
{
  return "sandwich_bt_interfaces::srv::ReportSkillVerification";
}

template<>
inline const char * name<sandwich_bt_interfaces::srv::ReportSkillVerification>()
{
  return "sandwich_bt_interfaces/srv/ReportSkillVerification";
}

template<>
struct has_fixed_size<sandwich_bt_interfaces::srv::ReportSkillVerification>
  : std::integral_constant<
    bool,
    has_fixed_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>::value &&
    has_fixed_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>::value
  >
{
};

template<>
struct has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification>
  : std::integral_constant<
    bool,
    has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>::value &&
    has_bounded_size<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>::value
  >
{
};

template<>
struct is_service<sandwich_bt_interfaces::srv::ReportSkillVerification>
  : std::true_type
{
};

template<>
struct is_service_request<sandwich_bt_interfaces::srv::ReportSkillVerification_Request>
  : std::true_type
{
};

template<>
struct is_service_response<sandwich_bt_interfaces::srv::ReportSkillVerification_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__TRAITS_HPP_
