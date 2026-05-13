// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from sandwich_bt_interfaces:srv/PlanNextStep.idl
// generated code does not contain a copyright notice

#include "sandwich_bt_interfaces/srv/detail/plan_next_step__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__PlanNextStep__get_type_hash(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x80, 0xf5, 0xf2, 0x9b, 0xc5, 0x02, 0xd8, 0x15,
      0x4d, 0xdb, 0xd6, 0xc7, 0x7c, 0x3d, 0x55, 0xe8,
      0x5f, 0xb5, 0x50, 0x04, 0x7c, 0x0c, 0x47, 0x09,
      0x29, 0x71, 0x3f, 0x56, 0xe2, 0x8a, 0x07, 0x79,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x53, 0x10, 0x2c, 0x10, 0x3b, 0x15, 0xef, 0x56,
      0x8e, 0x34, 0xa7, 0xea, 0xc5, 0x4f, 0x2a, 0x02,
      0xd1, 0x86, 0x9b, 0x32, 0x7b, 0x77, 0x04, 0xa1,
      0xbd, 0xcd, 0x9c, 0xef, 0xd0, 0x50, 0x16, 0xf0,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xb5, 0x42, 0x8d, 0x5b, 0xca, 0x2a, 0x56, 0xb1,
      0x89, 0xcb, 0x64, 0xa5, 0x21, 0x83, 0x31, 0x02,
      0xd5, 0x17, 0xbe, 0x20, 0xeb, 0x58, 0xad, 0x10,
      0xd1, 0x85, 0xbe, 0x3a, 0x83, 0x70, 0x28, 0x43,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xe9, 0x29, 0x71, 0x8b, 0x27, 0x2d, 0x30, 0xf6,
      0xb7, 0x73, 0x74, 0xc6, 0x0c, 0xa8, 0xee, 0xba,
      0x6e, 0x13, 0x71, 0x1b, 0x12, 0xaa, 0x98, 0x57,
      0xe8, 0x23, 0xfa, 0xac, 0x14, 0xca, 0xcf, 0x69,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "service_msgs/msg/detail/service_event_info__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t service_msgs__msg__ServiceEventInfo__EXPECTED_HASH = {1, {
    0x41, 0xbc, 0xbb, 0xe0, 0x7a, 0x75, 0xc9, 0xb5,
    0x2b, 0xc9, 0x6b, 0xfd, 0x5c, 0x24, 0xd7, 0xf0,
    0xfc, 0x0a, 0x08, 0xc0, 0xcb, 0x79, 0x21, 0xb3,
    0x37, 0x3c, 0x57, 0x32, 0x34, 0x5a, 0x6f, 0x45,
  }};
#endif

static char sandwich_bt_interfaces__srv__PlanNextStep__TYPE_NAME[] = "sandwich_bt_interfaces/srv/PlanNextStep";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char sandwich_bt_interfaces__srv__PlanNextStep_Event__TYPE_NAME[] = "sandwich_bt_interfaces/srv/PlanNextStep_Event";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME[] = "sandwich_bt_interfaces/srv/PlanNextStep_Request";
static char sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME[] = "sandwich_bt_interfaces/srv/PlanNextStep_Response";
static char service_msgs__msg__ServiceEventInfo__TYPE_NAME[] = "service_msgs/msg/ServiceEventInfo";

// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__PlanNextStep__FIELD_NAME__request_message[] = "request_message";
static char sandwich_bt_interfaces__srv__PlanNextStep__FIELD_NAME__response_message[] = "response_message";
static char sandwich_bt_interfaces__srv__PlanNextStep__FIELD_NAME__event_message[] = "event_message";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__PlanNextStep__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__PlanNextStep__FIELD_NAME__request_message, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME, 47, 47},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep__FIELD_NAME__response_message, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME, 48, 48},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep__FIELD_NAME__event_message, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__PlanNextStep_Event__TYPE_NAME, 45, 45},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription sandwich_bt_interfaces__srv__PlanNextStep__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Event__TYPE_NAME, 45, 45},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME, 47, 47},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME, 48, 48},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__PlanNextStep__get_type_description(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__PlanNextStep__TYPE_NAME, 39, 39},
      {sandwich_bt_interfaces__srv__PlanNextStep__FIELDS, 3, 3},
    },
    {sandwich_bt_interfaces__srv__PlanNextStep__REFERENCED_TYPE_DESCRIPTIONS, 5, 5},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[3].fields = sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[4].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__goal[] = "goal";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__current_task[] = "current_task";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__available_robot_skills[] = "available_robot_skills";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__available_human_skills[] = "available_human_skills";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__first_toast_on_plate[] = "first_toast_on_plate";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__ingredient_on_first_toast[] = "ingredient_on_first_toast";
static char sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__second_toast_on_top[] = "second_toast_on_top";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__goal, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__current_task, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__available_robot_skills, 22, 22},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__available_human_skills, 22, 22},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__first_toast_on_plate, 20, 20},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__ingredient_on_first_toast, 25, 25},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELD_NAME__second_toast_on_top, 19, 19},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME, 47, 47},
      {sandwich_bt_interfaces__srv__PlanNextStep_Request__FIELDS, 7, 7},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__step_name[] = "step_name";
static char sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__actor[] = "actor";
static char sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__reason[] = "reason";
static char sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__expected_state[] = "expected_state";
static char sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__confidence[] = "confidence";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__step_name, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__actor, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__reason, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__expected_state, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELD_NAME__confidence, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME, 48, 48},
      {sandwich_bt_interfaces__srv__PlanNextStep_Response__FIELDS, 5, 5},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELD_NAME__info[] = "info";
static char sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELD_NAME__request[] = "request";
static char sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELD_NAME__response[] = "response";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELD_NAME__info, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELD_NAME__request, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME, 47, 47},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELD_NAME__response, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME, 48, 48},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription sandwich_bt_interfaces__srv__PlanNextStep_Event__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME, 47, 47},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME, 48, 48},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__PlanNextStep_Event__TYPE_NAME, 45, 45},
      {sandwich_bt_interfaces__srv__PlanNextStep_Event__FIELDS, 3, 3},
    },
    {sandwich_bt_interfaces__srv__PlanNextStep_Event__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# Plan the next closed-set sandwich step.\n"
  "#\n"
  "# This is the runner -> supervisor planning boundary.\n"
  "# Request sent by the collaborative supervisor client.\n"
  "string goal\n"
  "string current_task\n"
  "string[] available_robot_skills\n"
  "string[] available_human_skills\n"
  "bool first_toast_on_plate\n"
  "bool ingredient_on_first_toast\n"
  "bool second_toast_on_top\n"
  "---\n"
  "# Response returned by the collaborative supervisor.\n"
  "string step_name\n"
  "string actor\n"
  "string reason\n"
  "string expected_state\n"
  "float32 confidence";

static char srv_encoding[] = "srv";
static char implicit_encoding[] = "implicit";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__PlanNextStep__get_individual_type_description_source(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__PlanNextStep__TYPE_NAME, 39, 39},
    {srv_encoding, 3, 3},
    {toplevel_type_raw_source, 473, 473},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__PlanNextStep_Request__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__PlanNextStep_Request__TYPE_NAME, 47, 47},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__PlanNextStep_Response__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__PlanNextStep_Response__TYPE_NAME, 48, 48},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__PlanNextStep_Event__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__PlanNextStep_Event__TYPE_NAME, 45, 45},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep__get_type_description_sources(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[6];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 6, 6};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__PlanNextStep__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *sandwich_bt_interfaces__srv__PlanNextStep_Event__get_individual_type_description_source(NULL);
    sources[3] = *sandwich_bt_interfaces__srv__PlanNextStep_Request__get_individual_type_description_source(NULL);
    sources[4] = *sandwich_bt_interfaces__srv__PlanNextStep_Response__get_individual_type_description_source(NULL);
    sources[5] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep_Request__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__PlanNextStep_Request__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep_Response__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__PlanNextStep_Response__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__PlanNextStep_Event__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__PlanNextStep_Event__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *sandwich_bt_interfaces__srv__PlanNextStep_Request__get_individual_type_description_source(NULL);
    sources[3] = *sandwich_bt_interfaces__srv__PlanNextStep_Response__get_individual_type_description_source(NULL);
    sources[4] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
