// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from lerobot_bt_interfaces:srv/GetSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "lerobot_bt_interfaces/srv/get_skill_verification.hpp"


#ifndef LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__STRUCT_HPP_
#define LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Request __attribute__((deprecated))
#else
# define DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Request __declspec(deprecated)
#endif

namespace lerobot_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetSkillVerification_Request_
{
  using Type = GetSkillVerification_Request_<ContainerAllocator>;

  explicit GetSkillVerification_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->skill_name = "";
    }
  }

  explicit GetSkillVerification_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : skill_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->skill_name = "";
    }
  }

  // field types and members
  using _skill_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _skill_name_type skill_name;

  // setters for named parameter idiom
  Type & set__skill_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->skill_name = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Request
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Request
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetSkillVerification_Request_ & other) const
  {
    if (this->skill_name != other.skill_name) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetSkillVerification_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetSkillVerification_Request_

// alias to use template instance with default allocator
using GetSkillVerification_Request =
  lerobot_bt_interfaces::srv::GetSkillVerification_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace lerobot_bt_interfaces


#ifndef _WIN32
# define DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Response __attribute__((deprecated))
#else
# define DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Response __declspec(deprecated)
#endif

namespace lerobot_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetSkillVerification_Response_
{
  using Type = GetSkillVerification_Response_<ContainerAllocator>;

  explicit GetSkillVerification_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->has_attempt = false;
      this->attempt_id = 0l;
      this->status = "";
      this->message = "";
    }
  }

  explicit GetSkillVerification_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : status(_alloc),
    message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->has_attempt = false;
      this->attempt_id = 0l;
      this->status = "";
      this->message = "";
    }
  }

  // field types and members
  using _has_attempt_type =
    bool;
  _has_attempt_type has_attempt;
  using _attempt_id_type =
    int32_t;
  _attempt_id_type attempt_id;
  using _status_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _status_type status;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__has_attempt(
    const bool & _arg)
  {
    this->has_attempt = _arg;
    return *this;
  }
  Type & set__attempt_id(
    const int32_t & _arg)
  {
    this->attempt_id = _arg;
    return *this;
  }
  Type & set__status(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Response
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Response
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetSkillVerification_Response_ & other) const
  {
    if (this->has_attempt != other.has_attempt) {
      return false;
    }
    if (this->attempt_id != other.attempt_id) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetSkillVerification_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetSkillVerification_Response_

// alias to use template instance with default allocator
using GetSkillVerification_Response =
  lerobot_bt_interfaces::srv::GetSkillVerification_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace lerobot_bt_interfaces


// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Event __attribute__((deprecated))
#else
# define DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Event __declspec(deprecated)
#endif

namespace lerobot_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetSkillVerification_Event_
{
  using Type = GetSkillVerification_Event_<ContainerAllocator>;

  explicit GetSkillVerification_Event_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit GetSkillVerification_Event_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    service_msgs::msg::ServiceEventInfo_<ContainerAllocator>;
  _info_type info;
  using _request_type =
    rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>>;
  _request_type request;
  using _response_type =
    rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>>;
  _response_type response;

  // setters for named parameter idiom
  Type & set__info(
    const service_msgs::msg::ServiceEventInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__request(
    const rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::GetSkillVerification_Request_<ContainerAllocator>>> & _arg)
  {
    this->request = _arg;
    return *this;
  }
  Type & set__response(
    const rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::GetSkillVerification_Response_<ContainerAllocator>>> & _arg)
  {
    this->response = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator> *;
  using ConstRawPtr =
    const lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Event
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__lerobot_bt_interfaces__srv__GetSkillVerification_Event
    std::shared_ptr<lerobot_bt_interfaces::srv::GetSkillVerification_Event_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetSkillVerification_Event_ & other) const
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
  bool operator!=(const GetSkillVerification_Event_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetSkillVerification_Event_

// alias to use template instance with default allocator
using GetSkillVerification_Event =
  lerobot_bt_interfaces::srv::GetSkillVerification_Event_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace lerobot_bt_interfaces

namespace lerobot_bt_interfaces
{

namespace srv
{

struct GetSkillVerification
{
  using Request = lerobot_bt_interfaces::srv::GetSkillVerification_Request;
  using Response = lerobot_bt_interfaces::srv::GetSkillVerification_Response;
  using Event = lerobot_bt_interfaces::srv::GetSkillVerification_Event;
};

}  // namespace srv

}  // namespace lerobot_bt_interfaces

#endif  // LEROBOT_BT_INTERFACES__SRV__DETAIL__GET_SKILL_VERIFICATION__STRUCT_HPP_
