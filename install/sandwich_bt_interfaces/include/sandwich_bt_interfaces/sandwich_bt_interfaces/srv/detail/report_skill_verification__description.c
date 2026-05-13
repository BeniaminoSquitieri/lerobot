// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from sandwich_bt_interfaces:srv/ReportSkillVerification.idl
// generated code does not contain a copyright notice

#include "sandwich_bt_interfaces/srv/detail/report_skill_verification__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__ReportSkillVerification__get_type_hash(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x65, 0xfe, 0xd8, 0xef, 0xcd, 0xdc, 0xf6, 0x1d,
      0x76, 0x59, 0xa5, 0x7d, 0x9d, 0x7c, 0x60, 0x28,
      0x19, 0xd9, 0x4e, 0x46, 0x21, 0xf4, 0x03, 0x1a,
      0x34, 0x7b, 0xc8, 0x06, 0xf6, 0x2f, 0xa1, 0x59,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x00, 0x82, 0xce, 0xe3, 0x29, 0xc3, 0xae, 0xa6,
      0x9f, 0x55, 0xdd, 0x6c, 0xe6, 0x62, 0xd3, 0xbf,
      0xd7, 0xa1, 0x76, 0x7b, 0xc3, 0x4e, 0xe9, 0x58,
      0x32, 0x9d, 0x53, 0xad, 0xc3, 0x05, 0x89, 0x59,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xa5, 0x70, 0xf7, 0x77, 0x0e, 0x8e, 0x53, 0x45,
      0xb0, 0xe2, 0x9b, 0x4e, 0xcb, 0x07, 0xbe, 0xe8,
      0xf6, 0xf0, 0xa8, 0x56, 0xe4, 0x59, 0xa8, 0x88,
      0xa3, 0x4b, 0xb6, 0x0c, 0xcf, 0x82, 0xf3, 0x76,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_sandwich_bt_interfaces
const rosidl_type_hash_t *
sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x8a, 0xe2, 0x60, 0x1c, 0x35, 0xef, 0x92, 0xc7,
      0xfb, 0x6f, 0xc4, 0xa7, 0x1b, 0xb1, 0xf2, 0xec,
      0x87, 0x41, 0xd0, 0x90, 0x4e, 0x09, 0x65, 0xad,
      0xe0, 0x8d, 0x30, 0xaa, 0xb7, 0x4c, 0x1e, 0x14,
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

static char sandwich_bt_interfaces__srv__ReportSkillVerification__TYPE_NAME[] = "sandwich_bt_interfaces/srv/ReportSkillVerification";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Event__TYPE_NAME[] = "sandwich_bt_interfaces/srv/ReportSkillVerification_Event";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME[] = "sandwich_bt_interfaces/srv/ReportSkillVerification_Request";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME[] = "sandwich_bt_interfaces/srv/ReportSkillVerification_Response";
static char service_msgs__msg__ServiceEventInfo__TYPE_NAME[] = "service_msgs/msg/ServiceEventInfo";

// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__ReportSkillVerification__FIELD_NAME__request_message[] = "request_message";
static char sandwich_bt_interfaces__srv__ReportSkillVerification__FIELD_NAME__response_message[] = "response_message";
static char sandwich_bt_interfaces__srv__ReportSkillVerification__FIELD_NAME__event_message[] = "event_message";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__ReportSkillVerification__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification__FIELD_NAME__request_message, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME, 58, 58},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification__FIELD_NAME__response_message, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME, 59, 59},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification__FIELD_NAME__event_message, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__TYPE_NAME, 56, 56},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription sandwich_bt_interfaces__srv__ReportSkillVerification__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__TYPE_NAME, 56, 56},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME, 58, 58},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME, 59, 59},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__ReportSkillVerification__get_type_description(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__ReportSkillVerification__TYPE_NAME, 50, 50},
      {sandwich_bt_interfaces__srv__ReportSkillVerification__FIELDS, 3, 3},
    },
    {sandwich_bt_interfaces__srv__ReportSkillVerification__REFERENCED_TYPE_DESCRIPTIONS, 5, 5},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[3].fields = sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[4].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__skill_name[] = "skill_name";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__attempt_id[] = "attempt_id";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__status[] = "status";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__message[] = "message";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__skill_name, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__attempt_id, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__status, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELD_NAME__message, 7, 7},
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
sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME, 58, 58},
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__FIELDS, 4, 4},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELD_NAME__accepted[] = "accepted";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELD_NAME__applied_attempt_id[] = "applied_attempt_id";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELD_NAME__message[] = "message";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELD_NAME__accepted, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELD_NAME__applied_attempt_id, 18, 18},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELD_NAME__message, 7, 7},
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
sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME, 59, 59},
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELD_NAME__info[] = "info";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELD_NAME__request[] = "request";
static char sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELD_NAME__response[] = "response";

static rosidl_runtime_c__type_description__Field sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELDS[] = {
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELD_NAME__info, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELD_NAME__request, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME, 58, 58},
    },
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELD_NAME__response, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME, 59, 59},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription sandwich_bt_interfaces__srv__ReportSkillVerification_Event__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME, 58, 58},
    {NULL, 0, 0},
  },
  {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME, 59, 59},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__TYPE_NAME, 56, 56},
      {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__FIELDS, 3, 3},
    },
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# @file ReportSkillVerification.srv\n"
  "# @brief Legacy external verifier to Python VLM-check-registry update boundary.\n"
  "#\n"
  "# Request fields:\n"
  "# skill_name identifies the primitive whose attempt is being judged.\n"
  "string skill_name\n"
  "# attempt_id selects a concrete attempt; 0 applies to the latest pending attempt.\n"
  "int32 attempt_id\n"
  "# status is the verifier update:\n"
  "#   PENDING/RUNNING/WAIT_HUMAN/MANUAL_INTERVENTION_REQUIRED keep the BT blocked\n"
  "#   SUCCESS advances the BT\n"
  "#   FAILURE triggers XML retry/failure logic\n"
  "string status\n"
  "# message explains the verdict for logs, operators, and tests.\n"
  "string message\n"
  "---\n"
  "# Response fields:\n"
  "# accepted is true when the registry applied the report.\n"
  "bool accepted\n"
  "# applied_attempt_id is the attempt updated when accepted is true.\n"
  "int32 applied_attempt_id\n"
  "# message describes rejection or success details for tooling.\n"
  "string message";

static char srv_encoding[] = "srv";
static char implicit_encoding[] = "implicit";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__ReportSkillVerification__get_individual_type_description_source(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__ReportSkillVerification__TYPE_NAME, 50, 50},
    {srv_encoding, 3, 3},
    {toplevel_type_raw_source, 863, 863},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Request__TYPE_NAME, 58, 58},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Response__TYPE_NAME, 59, 59},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {sandwich_bt_interfaces__srv__ReportSkillVerification_Event__TYPE_NAME, 56, 56},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__ReportSkillVerification__get_type_description_sources(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[6];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 6, 6};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__ReportSkillVerification__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_individual_type_description_source(NULL);
    sources[3] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_individual_type_description_source(NULL);
    sources[4] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_individual_type_description_source(NULL);
    sources[5] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Event__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Request__get_individual_type_description_source(NULL);
    sources[3] = *sandwich_bt_interfaces__srv__ReportSkillVerification_Response__get_individual_type_description_source(NULL);
    sources[4] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
