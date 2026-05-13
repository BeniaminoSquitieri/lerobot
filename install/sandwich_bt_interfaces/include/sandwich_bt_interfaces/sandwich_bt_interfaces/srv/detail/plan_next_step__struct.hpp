// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from sandwich_bt_interfaces:srv/PlanNextStep.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/plan_next_step.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__STRUCT_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Request __attribute__((deprecated))
#else
# define DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Request __declspec(deprecated)
#endif

namespace sandwich_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct PlanNextStep_Request_
{
  using Type = PlanNextStep_Request_<ContainerAllocator>;

  explicit PlanNextStep_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->goal = "";
      this->current_task = "";
      this->first_toast_on_plate = false;
      this->ingredient_on_first_toast = false;
      this->second_toast_on_top = false;
    }
  }

  explicit PlanNextStep_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal(_alloc),
    current_task(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->goal = "";
      this->current_task = "";
      this->first_toast_on_plate = false;
      this->ingredient_on_first_toast = false;
      this->second_toast_on_top = false;
    }
  }

  // field types and members
  using _goal_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _goal_type goal;
  using _current_task_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _current_task_type current_task;
  using _available_robot_skills_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _available_robot_skills_type available_robot_skills;
  using _available_human_skills_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _available_human_skills_type available_human_skills;
  using _first_toast_on_plate_type =
    bool;
  _first_toast_on_plate_type first_toast_on_plate;
  using _ingredient_on_first_toast_type =
    bool;
  _ingredient_on_first_toast_type ingredient_on_first_toast;
  using _second_toast_on_top_type =
    bool;
  _second_toast_on_top_type second_toast_on_top;

  // setters for named parameter idiom
  Type & set__goal(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->goal = _arg;
    return *this;
  }
  Type & set__current_task(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->current_task = _arg;
    return *this;
  }
  Type & set__available_robot_skills(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->available_robot_skills = _arg;
    return *this;
  }
  Type & set__available_human_skills(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->available_human_skills = _arg;
    return *this;
  }
  Type & set__first_toast_on_plate(
    const bool & _arg)
  {
    this->first_toast_on_plate = _arg;
    return *this;
  }
  Type & set__ingredient_on_first_toast(
    const bool & _arg)
  {
    this->ingredient_on_first_toast = _arg;
    return *this;
  }
  Type & set__second_toast_on_top(
    const bool & _arg)
  {
    this->second_toast_on_top = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Request
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Request
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PlanNextStep_Request_ & other) const
  {
    if (this->goal != other.goal) {
      return false;
    }
    if (this->current_task != other.current_task) {
      return false;
    }
    if (this->available_robot_skills != other.available_robot_skills) {
      return false;
    }
    if (this->available_human_skills != other.available_human_skills) {
      return false;
    }
    if (this->first_toast_on_plate != other.first_toast_on_plate) {
      return false;
    }
    if (this->ingredient_on_first_toast != other.ingredient_on_first_toast) {
      return false;
    }
    if (this->second_toast_on_top != other.second_toast_on_top) {
      return false;
    }
    return true;
  }
  bool operator!=(const PlanNextStep_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PlanNextStep_Request_

// alias to use template instance with default allocator
using PlanNextStep_Request =
  sandwich_bt_interfaces::srv::PlanNextStep_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace sandwich_bt_interfaces


#ifndef _WIN32
# define DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Response __attribute__((deprecated))
#else
# define DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Response __declspec(deprecated)
#endif

namespace sandwich_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct PlanNextStep_Response_
{
  using Type = PlanNextStep_Response_<ContainerAllocator>;

  explicit PlanNextStep_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->step_name = "";
      this->actor = "";
      this->reason = "";
      this->expected_state = "";
      this->confidence = 0.0f;
    }
  }

  explicit PlanNextStep_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : step_name(_alloc),
    actor(_alloc),
    reason(_alloc),
    expected_state(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->step_name = "";
      this->actor = "";
      this->reason = "";
      this->expected_state = "";
      this->confidence = 0.0f;
    }
  }

  // field types and members
  using _step_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _step_name_type step_name;
  using _actor_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _actor_type actor;
  using _reason_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _reason_type reason;
  using _expected_state_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _expected_state_type expected_state;
  using _confidence_type =
    float;
  _confidence_type confidence;

  // setters for named parameter idiom
  Type & set__step_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->step_name = _arg;
    return *this;
  }
  Type & set__actor(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->actor = _arg;
    return *this;
  }
  Type & set__reason(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->reason = _arg;
    return *this;
  }
  Type & set__expected_state(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->expected_state = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Response
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Response
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PlanNextStep_Response_ & other) const
  {
    if (this->step_name != other.step_name) {
      return false;
    }
    if (this->actor != other.actor) {
      return false;
    }
    if (this->reason != other.reason) {
      return false;
    }
    if (this->expected_state != other.expected_state) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    return true;
  }
  bool operator!=(const PlanNextStep_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PlanNextStep_Response_

// alias to use template instance with default allocator
using PlanNextStep_Response =
  sandwich_bt_interfaces::srv::PlanNextStep_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace sandwich_bt_interfaces


// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Event __attribute__((deprecated))
#else
# define DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Event __declspec(deprecated)
#endif

namespace sandwich_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct PlanNextStep_Event_
{
  using Type = PlanNextStep_Event_<ContainerAllocator>;

  explicit PlanNextStep_Event_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit PlanNextStep_Event_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    service_msgs::msg::ServiceEventInfo_<ContainerAllocator>;
  _info_type info;
  using _request_type =
    rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>>;
  _request_type request;
  using _response_type =
    rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>>;
  _response_type response;

  // setters for named parameter idiom
  Type & set__info(
    const service_msgs::msg::ServiceEventInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__request(
    const rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::PlanNextStep_Request_<ContainerAllocator>>> & _arg)
  {
    this->request = _arg;
    return *this;
  }
  Type & set__response(
    const rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::PlanNextStep_Response_<ContainerAllocator>>> & _arg)
  {
    this->response = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator> *;
  using ConstRawPtr =
    const sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Event
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sandwich_bt_interfaces__srv__PlanNextStep_Event
    std::shared_ptr<sandwich_bt_interfaces::srv::PlanNextStep_Event_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PlanNextStep_Event_ & other) const
  {
    if (this->info != other.info) {
      return false;
    }
    if (this->request != other.request) {
      return false;
    }
    if (this->response != other.response) {
      return false;
    }
    return true;
  }
  bool operator!=(const PlanNextStep_Event_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PlanNextStep_Event_

// alias to use template instance with default allocator
using PlanNextStep_Event =
  sandwich_bt_interfaces::srv::PlanNextStep_Event_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace sandwich_bt_interfaces

namespace sandwich_bt_interfaces
{

namespace srv
{

struct PlanNextStep
{
  using Request = sandwich_bt_interfaces::srv::PlanNextStep_Request;
  using Response = sandwich_bt_interfaces::srv::PlanNextStep_Response;
  using Event = sandwich_bt_interfaces::srv::PlanNextStep_Event;
};

}  // namespace srv

}  // namespace sandwich_bt_interfaces

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__PLAN_NEXT_STEP__STRUCT_HPP_
