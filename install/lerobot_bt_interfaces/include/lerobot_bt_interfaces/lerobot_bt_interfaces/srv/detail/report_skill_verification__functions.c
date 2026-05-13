// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from lerobot_bt_interfaces:srv/ReportSkillVerification.idl
// generated code does not contain a copyright notice
#include "lerobot_bt_interfaces/srv/detail/report_skill_verification__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `skill_name`
// Member `status`
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__init(lerobot_bt_interfaces__srv__ReportSkillVerification_Request * msg)
{
  if (!msg) {
    return false;
  }
  // skill_name
  if (!rosidl_runtime_c__String__init(&msg->skill_name)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(msg);
    return false;
  }
  // attempt_id
  // status
  if (!rosidl_runtime_c__String__init(&msg->status)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(msg);
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(msg);
    return false;
  }
  return true;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(lerobot_bt_interfaces__srv__ReportSkillVerification_Request * msg)
{
  if (!msg) {
    return;
  }
  // skill_name
  rosidl_runtime_c__String__fini(&msg->skill_name);
  // attempt_id
  // status
  rosidl_runtime_c__String__fini(&msg->status);
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__are_equal(const lerobot_bt_interfaces__srv__ReportSkillVerification_Request * lhs, const lerobot_bt_interfaces__srv__ReportSkillVerification_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // skill_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->skill_name), &(rhs->skill_name)))
  {
    return false;
  }
  // attempt_id
  if (lhs->attempt_id != rhs->attempt_id) {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->status), &(rhs->status)))
  {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__copy(
  const lerobot_bt_interfaces__srv__ReportSkillVerification_Request * input,
  lerobot_bt_interfaces__srv__ReportSkillVerification_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // skill_name
  if (!rosidl_runtime_c__String__copy(
      &(input->skill_name), &(output->skill_name)))
  {
    return false;
  }
  // attempt_id
  output->attempt_id = input->attempt_id;
  // status
  if (!rosidl_runtime_c__String__copy(
      &(input->status), &(output->status)))
  {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

lerobot_bt_interfaces__srv__ReportSkillVerification_Request *
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Request * msg = (lerobot_bt_interfaces__srv__ReportSkillVerification_Request *)allocator.allocate(sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Request));
  bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__destroy(lerobot_bt_interfaces__srv__ReportSkillVerification_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__init(lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Request * data = NULL;

  if (size) {
    data = (lerobot_bt_interfaces__srv__ReportSkillVerification_Request *)allocator.zero_allocate(size, sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__fini(lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence *
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * array = (lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence *)allocator.allocate(sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__destroy(lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__are_equal(const lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * lhs, const lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__copy(
  const lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * input,
  lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    lerobot_bt_interfaces__srv__ReportSkillVerification_Request * data =
      (lerobot_bt_interfaces__srv__ReportSkillVerification_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          lerobot_bt_interfaces__srv__ReportSkillVerification_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__init(lerobot_bt_interfaces__srv__ReportSkillVerification_Response * msg)
{
  if (!msg) {
    return false;
  }
  // accepted
  // applied_attempt_id
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Response__fini(msg);
    return false;
  }
  return true;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__fini(lerobot_bt_interfaces__srv__ReportSkillVerification_Response * msg)
{
  if (!msg) {
    return;
  }
  // accepted
  // applied_attempt_id
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__are_equal(const lerobot_bt_interfaces__srv__ReportSkillVerification_Response * lhs, const lerobot_bt_interfaces__srv__ReportSkillVerification_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // accepted
  if (lhs->accepted != rhs->accepted) {
    return false;
  }
  // applied_attempt_id
  if (lhs->applied_attempt_id != rhs->applied_attempt_id) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__copy(
  const lerobot_bt_interfaces__srv__ReportSkillVerification_Response * input,
  lerobot_bt_interfaces__srv__ReportSkillVerification_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // accepted
  output->accepted = input->accepted;
  // applied_attempt_id
  output->applied_attempt_id = input->applied_attempt_id;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

lerobot_bt_interfaces__srv__ReportSkillVerification_Response *
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Response * msg = (lerobot_bt_interfaces__srv__ReportSkillVerification_Response *)allocator.allocate(sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Response));
  bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__destroy(lerobot_bt_interfaces__srv__ReportSkillVerification_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__init(lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Response * data = NULL;

  if (size) {
    data = (lerobot_bt_interfaces__srv__ReportSkillVerification_Response *)allocator.zero_allocate(size, sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        lerobot_bt_interfaces__srv__ReportSkillVerification_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__fini(lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      lerobot_bt_interfaces__srv__ReportSkillVerification_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence *
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * array = (lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence *)allocator.allocate(sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__destroy(lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__are_equal(const lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * lhs, const lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__copy(
  const lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * input,
  lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    lerobot_bt_interfaces__srv__ReportSkillVerification_Response * data =
      (lerobot_bt_interfaces__srv__ReportSkillVerification_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          lerobot_bt_interfaces__srv__ReportSkillVerification_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
#include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "lerobot_bt_interfaces/srv/detail/report_skill_verification__functions.h"

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__init(lerobot_bt_interfaces__srv__ReportSkillVerification_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(msg);
    return false;
  }
  // request
  if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__init(&msg->request, 0)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(msg);
    return false;
  }
  // response
  if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__init(&msg->response, 0)) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(msg);
    return false;
  }
  return true;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(lerobot_bt_interfaces__srv__ReportSkillVerification_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__fini(&msg->request);
  // response
  lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__fini(&msg->response);
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__are_equal(const lerobot_bt_interfaces__srv__ReportSkillVerification_Event * lhs, const lerobot_bt_interfaces__srv__ReportSkillVerification_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__copy(
  const lerobot_bt_interfaces__srv__ReportSkillVerification_Event * input,
  lerobot_bt_interfaces__srv__ReportSkillVerification_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

lerobot_bt_interfaces__srv__ReportSkillVerification_Event *
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Event * msg = (lerobot_bt_interfaces__srv__ReportSkillVerification_Event *)allocator.allocate(sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Event));
  bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__destroy(lerobot_bt_interfaces__srv__ReportSkillVerification_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__init(lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Event * data = NULL;

  if (size) {
    data = (lerobot_bt_interfaces__srv__ReportSkillVerification_Event *)allocator.zero_allocate(size, sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__fini(lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence *
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * array = (lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence *)allocator.allocate(sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__destroy(lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__are_equal(const lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * lhs, const lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence__copy(
  const lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * input,
  lerobot_bt_interfaces__srv__ReportSkillVerification_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(lerobot_bt_interfaces__srv__ReportSkillVerification_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    lerobot_bt_interfaces__srv__ReportSkillVerification_Event * data =
      (lerobot_bt_interfaces__srv__ReportSkillVerification_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          lerobot_bt_interfaces__srv__ReportSkillVerification_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!lerobot_bt_interfaces__srv__ReportSkillVerification_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
