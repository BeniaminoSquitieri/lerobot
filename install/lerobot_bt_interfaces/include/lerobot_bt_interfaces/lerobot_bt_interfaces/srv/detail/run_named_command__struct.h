// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from lerobot_bt_interfaces:srv/RunNamedCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "lerobot_bt_interfaces/srv/run_named_command.h"


#ifndef LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__STRUCT_H_
#define LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'kind'
// Member 'name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/RunNamedCommand in the package lerobot_bt_interfaces.
typedef struct lerobot_bt_interfaces__srv__RunNamedCommand_Request
{
  rosidl_runtime_c__String kind;
  /// name must match one configured command entry on the Python side.
  rosidl_runtime_c__String name;
  /// timeout_s optionally overrides the command duration; 0 lets the server decide.
  float timeout_s;
} lerobot_bt_interfaces__srv__RunNamedCommand_Request;

// Struct for a sequence of lerobot_bt_interfaces__srv__RunNamedCommand_Request.
typedef struct lerobot_bt_interfaces__srv__RunNamedCommand_Request__Sequence
{
  lerobot_bt_interfaces__srv__RunNamedCommand_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} lerobot_bt_interfaces__srv__RunNamedCommand_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'status'
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/RunNamedCommand in the package lerobot_bt_interfaces.
typedef struct lerobot_bt_interfaces__srv__RunNamedCommand_Response
{
  bool success;
  /// status is the detailed executor state, for example SUCCESS, FAILURE, or TIMEOUT.
  rosidl_runtime_c__String status;
  /// elapsed_s reports how long the Python command spent executing.
  float elapsed_s;
  /// message carries human-readable diagnostics for logs and tests.
  rosidl_runtime_c__String message;
} lerobot_bt_interfaces__srv__RunNamedCommand_Response;

// Struct for a sequence of lerobot_bt_interfaces__srv__RunNamedCommand_Response.
typedef struct lerobot_bt_interfaces__srv__RunNamedCommand_Response__Sequence
{
  lerobot_bt_interfaces__srv__RunNamedCommand_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} lerobot_bt_interfaces__srv__RunNamedCommand_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  lerobot_bt_interfaces__srv__RunNamedCommand_Event__request__MAX_SIZE = 1
};
// response
enum
{
  lerobot_bt_interfaces__srv__RunNamedCommand_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/RunNamedCommand in the package lerobot_bt_interfaces.
typedef struct lerobot_bt_interfaces__srv__RunNamedCommand_Event
{
  service_msgs__msg__ServiceEventInfo info;
  lerobot_bt_interfaces__srv__RunNamedCommand_Request__Sequence request;
  lerobot_bt_interfaces__srv__RunNamedCommand_Response__Sequence response;
} lerobot_bt_interfaces__srv__RunNamedCommand_Event;

// Struct for a sequence of lerobot_bt_interfaces__srv__RunNamedCommand_Event.
typedef struct lerobot_bt_interfaces__srv__RunNamedCommand_Event__Sequence
{
  lerobot_bt_interfaces__srv__RunNamedCommand_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} lerobot_bt_interfaces__srv__RunNamedCommand_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__STRUCT_H_
