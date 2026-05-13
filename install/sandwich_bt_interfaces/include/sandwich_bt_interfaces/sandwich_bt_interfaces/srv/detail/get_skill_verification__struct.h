// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from sandwich_bt_interfaces:srv/GetSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/get_skill_verification.h"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__STRUCT_H_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'skill_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/GetSkillVerification in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__GetSkillVerification_Request
{
  rosidl_runtime_c__String skill_name;
} sandwich_bt_interfaces__srv__GetSkillVerification_Request;

// Struct for a sequence of sandwich_bt_interfaces__srv__GetSkillVerification_Request.
typedef struct sandwich_bt_interfaces__srv__GetSkillVerification_Request__Sequence
{
  sandwich_bt_interfaces__srv__GetSkillVerification_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__GetSkillVerification_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'status'
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/GetSkillVerification in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__GetSkillVerification_Response
{
  bool has_attempt;
  /// attempt_id is the monotonic identifier assigned by the Python server.
  int32_t attempt_id;
  /// status is one of UNKNOWN, PENDING, RUNNING, WAIT_HUMAN,
  /// MANUAL_INTERVENTION_REQUIRED, SUCCESS, or FAILURE.
  rosidl_runtime_c__String status;
  /// message provides human-readable status detail.
  rosidl_runtime_c__String message;
} sandwich_bt_interfaces__srv__GetSkillVerification_Response;

// Struct for a sequence of sandwich_bt_interfaces__srv__GetSkillVerification_Response.
typedef struct sandwich_bt_interfaces__srv__GetSkillVerification_Response__Sequence
{
  sandwich_bt_interfaces__srv__GetSkillVerification_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__GetSkillVerification_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  sandwich_bt_interfaces__srv__GetSkillVerification_Event__request__MAX_SIZE = 1
};
// response
enum
{
  sandwich_bt_interfaces__srv__GetSkillVerification_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/GetSkillVerification in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__GetSkillVerification_Event
{
  service_msgs__msg__ServiceEventInfo info;
  sandwich_bt_interfaces__srv__GetSkillVerification_Request__Sequence request;
  sandwich_bt_interfaces__srv__GetSkillVerification_Response__Sequence response;
} sandwich_bt_interfaces__srv__GetSkillVerification_Event;

// Struct for a sequence of sandwich_bt_interfaces__srv__GetSkillVerification_Event.
typedef struct sandwich_bt_interfaces__srv__GetSkillVerification_Event__Sequence
{
  sandwich_bt_interfaces__srv__GetSkillVerification_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__GetSkillVerification_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__STRUCT_H_
