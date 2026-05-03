// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from sandwich_bt_interfaces:srv/PlanNextStep.idl
// generated code does not contain a copyright notice
#include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `goal`
// Member `current_task`
// Member `available_robot_skills`
// Member `available_human_skills`
#include "rosidl_runtime_c/string_functions.h"

bool
sandwich_bt_interfaces__srv__PlanNextStep_Request__init(sandwich_bt_interfaces__srv__PlanNextStep_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal
  if (!rosidl_runtime_c__String__init(&msg->goal)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(msg);
    return false;
  }
  // current_task
  if (!rosidl_runtime_c__String__init(&msg->current_task)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(msg);
    return false;
  }
  // available_robot_skills
  if (!rosidl_runtime_c__String__Sequence__init(&msg->available_robot_skills, 0)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(msg);
    return false;
  }
  // available_human_skills
  if (!rosidl_runtime_c__String__Sequence__init(&msg->available_human_skills, 0)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(msg);
    return false;
  }
  // first_toast_on_plate
  // ingredient_on_first_toast
  // second_toast_on_top
  return true;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(sandwich_bt_interfaces__srv__PlanNextStep_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal
  rosidl_runtime_c__String__fini(&msg->goal);
  // current_task
  rosidl_runtime_c__String__fini(&msg->current_task);
  // available_robot_skills
  rosidl_runtime_c__String__Sequence__fini(&msg->available_robot_skills);
  // available_human_skills
  rosidl_runtime_c__String__Sequence__fini(&msg->available_human_skills);
  // first_toast_on_plate
  // ingredient_on_first_toast
  // second_toast_on_top
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Request__are_equal(const sandwich_bt_interfaces__srv__PlanNextStep_Request * lhs, const sandwich_bt_interfaces__srv__PlanNextStep_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->goal), &(rhs->goal)))
  {
    return false;
  }
  // current_task
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->current_task), &(rhs->current_task)))
  {
    return false;
  }
  // available_robot_skills
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->available_robot_skills), &(rhs->available_robot_skills)))
  {
    return false;
  }
  // available_human_skills
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->available_human_skills), &(rhs->available_human_skills)))
  {
    return false;
  }
  // first_toast_on_plate
  if (lhs->first_toast_on_plate != rhs->first_toast_on_plate) {
    return false;
  }
  // ingredient_on_first_toast
  if (lhs->ingredient_on_first_toast != rhs->ingredient_on_first_toast) {
    return false;
  }
  // second_toast_on_top
  if (lhs->second_toast_on_top != rhs->second_toast_on_top) {
    return false;
  }
  return true;
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Request__copy(
  const sandwich_bt_interfaces__srv__PlanNextStep_Request * input,
  sandwich_bt_interfaces__srv__PlanNextStep_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal
  if (!rosidl_runtime_c__String__copy(
      &(input->goal), &(output->goal)))
  {
    return false;
  }
  // current_task
  if (!rosidl_runtime_c__String__copy(
      &(input->current_task), &(output->current_task)))
  {
    return false;
  }
  // available_robot_skills
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->available_robot_skills), &(output->available_robot_skills)))
  {
    return false;
  }
  // available_human_skills
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->available_human_skills), &(output->available_human_skills)))
  {
    return false;
  }
  // first_toast_on_plate
  output->first_toast_on_plate = input->first_toast_on_plate;
  // ingredient_on_first_toast
  output->ingredient_on_first_toast = input->ingredient_on_first_toast;
  // second_toast_on_top
  output->second_toast_on_top = input->second_toast_on_top;
  return true;
}

sandwich_bt_interfaces__srv__PlanNextStep_Request *
sandwich_bt_interfaces__srv__PlanNextStep_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Request * msg = (sandwich_bt_interfaces__srv__PlanNextStep_Request *)allocator.allocate(sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Request));
  bool success = sandwich_bt_interfaces__srv__PlanNextStep_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Request__destroy(sandwich_bt_interfaces__srv__PlanNextStep_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__init(sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Request * data = NULL;

  if (size) {
    data = (sandwich_bt_interfaces__srv__PlanNextStep_Request *)allocator.zero_allocate(size, sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = sandwich_bt_interfaces__srv__PlanNextStep_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(&data[i - 1]);
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
sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__fini(sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * array)
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
      sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(&array->data[i]);
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

sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * array = (sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence *)allocator.allocate(sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__destroy(sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__are_equal(const sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * lhs, const sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!sandwich_bt_interfaces__srv__PlanNextStep_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__copy(
  const sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * input,
  sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    sandwich_bt_interfaces__srv__PlanNextStep_Request * data =
      (sandwich_bt_interfaces__srv__PlanNextStep_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!sandwich_bt_interfaces__srv__PlanNextStep_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          sandwich_bt_interfaces__srv__PlanNextStep_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!sandwich_bt_interfaces__srv__PlanNextStep_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `step_name`
// Member `actor`
// Member `reason`
// Member `expected_state`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
sandwich_bt_interfaces__srv__PlanNextStep_Response__init(sandwich_bt_interfaces__srv__PlanNextStep_Response * msg)
{
  if (!msg) {
    return false;
  }
  // step_name
  if (!rosidl_runtime_c__String__init(&msg->step_name)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(msg);
    return false;
  }
  // actor
  if (!rosidl_runtime_c__String__init(&msg->actor)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(msg);
    return false;
  }
  // reason
  if (!rosidl_runtime_c__String__init(&msg->reason)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(msg);
    return false;
  }
  // expected_state
  if (!rosidl_runtime_c__String__init(&msg->expected_state)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(msg);
    return false;
  }
  // confidence
  return true;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(sandwich_bt_interfaces__srv__PlanNextStep_Response * msg)
{
  if (!msg) {
    return;
  }
  // step_name
  rosidl_runtime_c__String__fini(&msg->step_name);
  // actor
  rosidl_runtime_c__String__fini(&msg->actor);
  // reason
  rosidl_runtime_c__String__fini(&msg->reason);
  // expected_state
  rosidl_runtime_c__String__fini(&msg->expected_state);
  // confidence
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Response__are_equal(const sandwich_bt_interfaces__srv__PlanNextStep_Response * lhs, const sandwich_bt_interfaces__srv__PlanNextStep_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // step_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->step_name), &(rhs->step_name)))
  {
    return false;
  }
  // actor
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->actor), &(rhs->actor)))
  {
    return false;
  }
  // reason
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->reason), &(rhs->reason)))
  {
    return false;
  }
  // expected_state
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->expected_state), &(rhs->expected_state)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  return true;
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Response__copy(
  const sandwich_bt_interfaces__srv__PlanNextStep_Response * input,
  sandwich_bt_interfaces__srv__PlanNextStep_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // step_name
  if (!rosidl_runtime_c__String__copy(
      &(input->step_name), &(output->step_name)))
  {
    return false;
  }
  // actor
  if (!rosidl_runtime_c__String__copy(
      &(input->actor), &(output->actor)))
  {
    return false;
  }
  // reason
  if (!rosidl_runtime_c__String__copy(
      &(input->reason), &(output->reason)))
  {
    return false;
  }
  // expected_state
  if (!rosidl_runtime_c__String__copy(
      &(input->expected_state), &(output->expected_state)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  return true;
}

sandwich_bt_interfaces__srv__PlanNextStep_Response *
sandwich_bt_interfaces__srv__PlanNextStep_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Response * msg = (sandwich_bt_interfaces__srv__PlanNextStep_Response *)allocator.allocate(sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Response));
  bool success = sandwich_bt_interfaces__srv__PlanNextStep_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Response__destroy(sandwich_bt_interfaces__srv__PlanNextStep_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__init(sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Response * data = NULL;

  if (size) {
    data = (sandwich_bt_interfaces__srv__PlanNextStep_Response *)allocator.zero_allocate(size, sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = sandwich_bt_interfaces__srv__PlanNextStep_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(&data[i - 1]);
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
sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__fini(sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * array)
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
      sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(&array->data[i]);
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

sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * array = (sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence *)allocator.allocate(sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__destroy(sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__are_equal(const sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * lhs, const sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!sandwich_bt_interfaces__srv__PlanNextStep_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__copy(
  const sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * input,
  sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    sandwich_bt_interfaces__srv__PlanNextStep_Response * data =
      (sandwich_bt_interfaces__srv__PlanNextStep_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!sandwich_bt_interfaces__srv__PlanNextStep_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          sandwich_bt_interfaces__srv__PlanNextStep_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!sandwich_bt_interfaces__srv__PlanNextStep_Response__copy(
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
// #include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"

bool
sandwich_bt_interfaces__srv__PlanNextStep_Event__init(sandwich_bt_interfaces__srv__PlanNextStep_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(msg);
    return false;
  }
  // request
  if (!sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__init(&msg->request, 0)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(msg);
    return false;
  }
  // response
  if (!sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__init(&msg->response, 0)) {
    sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(msg);
    return false;
  }
  return true;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(sandwich_bt_interfaces__srv__PlanNextStep_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__fini(&msg->request);
  // response
  sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__fini(&msg->response);
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Event__are_equal(const sandwich_bt_interfaces__srv__PlanNextStep_Event * lhs, const sandwich_bt_interfaces__srv__PlanNextStep_Event * rhs)
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
  if (!sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Event__copy(
  const sandwich_bt_interfaces__srv__PlanNextStep_Event * input,
  sandwich_bt_interfaces__srv__PlanNextStep_Event * output)
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
  if (!sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

sandwich_bt_interfaces__srv__PlanNextStep_Event *
sandwich_bt_interfaces__srv__PlanNextStep_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Event * msg = (sandwich_bt_interfaces__srv__PlanNextStep_Event *)allocator.allocate(sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Event));
  bool success = sandwich_bt_interfaces__srv__PlanNextStep_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Event__destroy(sandwich_bt_interfaces__srv__PlanNextStep_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__init(sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Event * data = NULL;

  if (size) {
    data = (sandwich_bt_interfaces__srv__PlanNextStep_Event *)allocator.zero_allocate(size, sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = sandwich_bt_interfaces__srv__PlanNextStep_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(&data[i - 1]);
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
sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__fini(sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * array)
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
      sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(&array->data[i]);
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

sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * array = (sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence *)allocator.allocate(sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__destroy(sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__are_equal(const sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * lhs, const sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!sandwich_bt_interfaces__srv__PlanNextStep_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence__copy(
  const sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * input,
  sandwich_bt_interfaces__srv__PlanNextStep_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(sandwich_bt_interfaces__srv__PlanNextStep_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    sandwich_bt_interfaces__srv__PlanNextStep_Event * data =
      (sandwich_bt_interfaces__srv__PlanNextStep_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!sandwich_bt_interfaces__srv__PlanNextStep_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          sandwich_bt_interfaces__srv__PlanNextStep_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!sandwich_bt_interfaces__srv__PlanNextStep_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
