// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from sandwich_bt_interfaces:srv/GetSkillVerification.idl
// generated code does not contain a copyright notice

#include "sandwich_bt_interfaces/srv/detail/get_skill_verification__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__GetSkillVerification__get_type_hash(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x00, 0x02, 0xf0, 0x7c, 0xcb, 0xe3, 0x56, 0xf4,
      0x47, 0xa0, 0xa9, 0x0e, 0x1a, 0x99, 0x73, 0x36,
      0xfd, 0xf1, 0xbe, 0x51, 0x4b, 0x2a, 0x1e, 0xfc,
      0xb8, 0xdd, 0xc9, 0x6c, 0xc8, 0xad, 0xf8, 0x99,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x36, 0xcb, 0x68, 0x4a, 0x17, 0x10, 0x8b, 0xe4,
      0x99, 0x05, 0xe2, 0xf7, 0x30, 0xd2, 0x1f, 0xe0,
      0x31, 0x2a, 0x6d, 0x66, 0xbf, 0x7d, 0x9c, 0x49,
      0xcb, 0xf0, 0xf1, 0x38, 0x61, 0x0f, 0x0e, 0xc1,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x96, 0xfc, 0x6f, 0x5b, 0x27, 0x98, 0x30, 0x46,
      0xb1, 0x69, 0x9f, 0x46, 0xb8, 0x99, 0x96, 0x55,
      0xc2, 0xae, 0xef, 0x8b, 0x87, 0x85, 0xfe, 0x9a,
      0xb6, 0x69, 0x07, 0x55, 0xeb, 0x7d, 0x54, 0xe1,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x5d, 0xe3, 0x1b, 0x13, 0x83, 0x70, 0x17, 0xf7,
      0x76, 0x5a, 0x9b, 0x7b, 0xb7, 0x3f, 0xaf, 0xdb,
      0xac, 0xd3, 0x6d, 0xff, 0x20, 0x5c, 0x24, 0x8f,
      0x02, 0xf2, 0xea, 0xba, 0x10, 0x1b, 0x98, 0xd7,
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

static char sandwich_bt_interfaces__srv__GetSkillVerification__TYPE_NAME[] = "sandwich_bt_interfaces/srv/GetSkillVerification";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Event__TYPE_NAME[] = "sandwich_bt_interfaces/srv/GetSkillVerification_Event";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME[] = "sandwich_bt_interfaces/srv/GetSkillVerification_Request";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME[] = "sandwich_bt_interfaces/srv/GetSkillVerification_Response";
static char service_msgs__msg__ServiceEventInfo__TYPE_NAME[] = "service_msgs/msg/ServiceEventInfo";

// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__GetSkillVerification__FIELD_NAME__request_message[] = "request_message";
static char sandwich_bt_interfaces__srv__GetSkillVerification__FIELD_NAME__response_message[] = "response_message";
static char sandwich_bt_interfaces__srv__GetSkillVerification__FIELD_NAME__event_message[] = "event_message";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__GetSkillVerification__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification__FIELD_NAME__request_message, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME, 55, 55},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification__FIELD_NAME__response_message, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME, 56, 56},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification__FIELD_NAME__event_message, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__GetSkillVerification_Event__TYPE_NAME, 53, 53},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription sandwich_bt_interfaces__srv__GetSkillVerification__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Event__TYPE_NAME, 53, 53},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME, 55, 55},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME, 56, 56},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__GetSkillVerification__get_type_description(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__GetSkillVerification__TYPE_NAME, 47, 47},
      {sandwich_bt_interfaces__srv__GetSkillVerification__FIELDS, 3, 3},
    },
    {sandwich_bt_interfaces__srv__GetSkillVerification__REFERENCED_TYPE_DESCRIPTIONS, 5, 5},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[3].fields = sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[4].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__GetSkillVerification_Request__FIELD_NAME__skill_name[] = "skill_name";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__GetSkillVerification_Request__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Request__FIELD_NAME__skill_name, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME, 55, 55},
      {sandwich_bt_interfaces__srv__GetSkillVerification_Request__FIELDS, 1, 1},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__has_attempt[] = "has_attempt";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__attempt_id[] = "attempt_id";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__status[] = "status";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__message[] = "message";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__has_attempt, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__attempt_id, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__status, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELD_NAME__message, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME, 56, 56},
      {sandwich_bt_interfaces__srv__GetSkillVerification_Response__FIELDS, 4, 4},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELD_NAME__info[] = "info";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELD_NAME__request[] = "request";
static char sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELD_NAME__response[] = "response";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELD_NAME__info, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELD_NAME__request, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME, 55, 55},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELD_NAME__response, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME, 56, 56},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription sandwich_bt_interfaces__srv__GetSkillVerification_Event__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME, 55, 55},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME, 56, 56},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__GetSkillVerification_Event__TYPE_NAME, 53, 53},
      {sandwich_bt_interfaces__srv__GetSkillVerification_Event__FIELDS, 3, 3},
    },
    {sandwich_bt_interfaces__srv__GetSkillVerification_Event__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# @file GetSkillVerification.srv\n"
  "# @brief BT runtime to Python VLM-check-registry query boundary.\n"
  "#\n"
  "# Request fields:\n"
  "# skill_name identifies the primitive whose latest attempt should be inspected.\n"
  "string skill_name\n"
  "---\n"
  "# Response fields:\n"
  "# has_attempt tells the BT whether the Python side has recorded this skill.\n"
  "bool has_attempt\n"
  "# attempt_id is the monotonic identifier assigned by the Python server.\n"
  "int32 attempt_id\n"
  "# status is one of UNKNOWN, PENDING, RUNNING, WAIT_HUMAN,\n"
  "# MANUAL_INTERVENTION_REQUIRED, SUCCESS, or FAILURE.\n"
  "string status\n"
  "# message provides human-readable status detail.\n"
  "string message";

static char srv_encoding[] = "srv";
static char implicit_encoding[] = "implicit";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__GetSkillVerification__get_individual_type_description_source(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__GetSkillVerification__TYPE_NAME, 47, 47},
    {srv_encoding, 3, 3},
    {toplevel_type_raw_source, 610, 610},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Request__TYPE_NAME, 55, 55},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Response__TYPE_NAME, 56, 56},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__GetSkillVerification_Event__TYPE_NAME, 53, 53},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__GetSkillVerification__get_type_description_sources(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[6];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 6, 6};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__GetSkillVerification__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_individual_type_description_source(NULL);
    sources[3] = *sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_individual_type_description_source(NULL);
    sources[4] = *sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_individual_type_description_source(NULL);
    sources[5] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__GetSkillVerification_Event__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *sandwich_bt_interfaces__srv__GetSkillVerification_Request__get_individual_type_description_source(NULL);
    sources[3] = *sandwich_bt_interfaces__srv__GetSkillVerification_Response__get_individual_type_description_source(NULL);
    sources[4] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
