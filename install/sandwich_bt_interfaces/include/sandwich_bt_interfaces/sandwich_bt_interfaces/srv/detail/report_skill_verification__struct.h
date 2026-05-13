// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from sandwich_bt_interfaces:srv/ReportSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/report_skill_verification.h"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__STRUCT_H_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__STRUCT_H_

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
// Member 'status'
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ReportSkillVerification in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__ReportSkillVerification_Request
{
  rosidl_runtime_c__String skill_name;
  /// attempt_id selects a concrete attempt; 0 applies to the latest pending attempt.
  int32_t attempt_id;
  /// status is the verifier update:
  ///   PENDING/RUNNING/WAIT_HUMAN/MANUAL_INTERVENTION_REQUIRED keep the BT blocked
  ///   SUCCESS advances the BT
  ///   FAILURE triggers XML retry/failure logic
  rosidl_runtime_c__String status;
  /// message explains the verdict for logs, operators, and tests.
  rosidl_runtime_c__String message;
} sandwich_bt_interfaces__srv__ReportSkillVerification_Request;

// Struct for a sequence of sandwich_bt_interfaces__srv__ReportSkillVerification_Request.
typedef struct sandwich_bt_interfaces__srv__ReportSkillVerification_Request__Sequence
{
  sandwich_bt_interfaces__srv__ReportSkillVerification_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__ReportSkillVerification_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ReportSkillVerification in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__ReportSkillVerification_Response
{
  bool accepted;
  /// applied_attempt_id is the attempt updated when accepted is true.
  int32_t applied_attempt_id;
  /// message describes rejection or success details for tooling.
  rosidl_runtime_c__String message;
} sandwich_bt_interfaces__srv__ReportSkillVerification_Response;

// Struct for a sequence of sandwich_bt_interfaces__srv__ReportSkillVerification_Response.
typedef struct sandwich_bt_interfaces__srv__ReportSkillVerification_Response__Sequence
{
  sandwich_bt_interfaces__srv__ReportSkillVerification_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__ReportSkillVerification_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  sandwich_bt_interfaces__srv__ReportSkillVerification_Event__request__MAX_SIZE = 1
};
// response
enum
{
  sandwich_bt_interfaces__srv__ReportSkillVerification_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/ReportSkillVerification in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__ReportSkillVerification_Event
{
  service_msgs__msg__ServiceEventInfo info;
  sandwich_bt_interfaces__srv__ReportSkillVerification_Request__Sequence request;
  sandwich_bt_interfaces__srv__ReportSkillVerification_Response__Sequence response;
} sandwich_bt_interfaces__srv__ReportSkillVerification_Event;

// Struct for a sequence of sandwich_bt_interfaces__srv__ReportSkillVerification_Event.
typedef struct sandwich_bt_interfaces__srv__ReportSkillVerification_Event__Sequence
{
  sandwich_bt_interfaces__srv__ReportSkillVerification_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__ReportSkillVerification_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__STRUCT_H_
