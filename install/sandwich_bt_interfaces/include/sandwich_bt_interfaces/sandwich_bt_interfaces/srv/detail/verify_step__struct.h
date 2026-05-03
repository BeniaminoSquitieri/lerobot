// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from sandwich_bt_interfaces:srv/VerifyStep.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/verify_step.h"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__VERIFY_STEP__STRUCT_H_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__VERIFY_STEP__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'step_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/VerifyStep in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__VerifyStep_Request
{
  rosidl_runtime_c__String step_name;
  bool first_toast_on_plate;
  bool ingredient_on_first_toast;
  bool second_toast_on_top;
} sandwich_bt_interfaces__srv__VerifyStep_Request;

// Struct for a sequence of sandwich_bt_interfaces__srv__VerifyStep_Request.
typedef struct sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence
{
  sandwich_bt_interfaces__srv__VerifyStep_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'observed_state'
// Member 'failure_reason'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/VerifyStep in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__VerifyStep_Response
{
  bool success;
  rosidl_runtime_c__String observed_state;
  rosidl_runtime_c__String failure_reason;
  float confidence;
} sandwich_bt_interfaces__srv__VerifyStep_Response;

// Struct for a sequence of sandwich_bt_interfaces__srv__VerifyStep_Response.
typedef struct sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence
{
  sandwich_bt_interfaces__srv__VerifyStep_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  sandwich_bt_interfaces__srv__VerifyStep_Event__request__MAX_SIZE = 1
};
// response
enum
{
  sandwich_bt_interfaces__srv__VerifyStep_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/VerifyStep in the package sandwich_bt_interfaces.
typedef struct sandwich_bt_interfaces__srv__VerifyStep_Event
{
  service_msgs__msg__ServiceEventInfo info;
  sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence request;
  sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence response;
} sandwich_bt_interfaces__srv__VerifyStep_Event;

// Struct for a sequence of sandwich_bt_interfaces__srv__VerifyStep_Event.
typedef struct sandwich_bt_interfaces__srv__VerifyStep_Event__Sequence
{
  sandwich_bt_interfaces__srv__VerifyStep_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sandwich_bt_interfaces__srv__VerifyStep_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__VERIFY_STEP__STRUCT_H_
