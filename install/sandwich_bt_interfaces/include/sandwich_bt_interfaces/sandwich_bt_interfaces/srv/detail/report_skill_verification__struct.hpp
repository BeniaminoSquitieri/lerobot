// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from sandwich_bt_interfaces:srv/ReportSkillVerification.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "sandwich_bt_interfaces/srv/report_skill_verification.hpp"


#ifndef SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__STRUCT_HPP_
#define SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Request __attribute__((deprecated))
#else
# define DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Request __declspec(deprecated)
#endif

namespace sandwich_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ReportSkillVerification_Request_
{
  using Type = ReportSkillVerification_Request_<ContainerAllocator>;

  explicit ReportSkillVerification_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->skill_name = "";
      this->attempt_id = 0l;
      this->status = "";
      this->message = "";
    }
  }

  explicit ReportSkillVerification_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : skill_name(_alloc),
    status(_alloc),
    message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->skill_name = "";
      this->attempt_id = 0l;
      this->status = "";
      this->message = "";
    }
  }

  // field types and members
  using _skill_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _skill_name_type skill_name;
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
  Type & set__skill_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->skill_name = _arg;
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
    sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Request
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Request
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ReportSkillVerification_Request_ & other) const
  {
    if (this->skill_name != other.skill_name) {
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
  bool operator!=(const ReportSkillVerification_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ReportSkillVerification_Request_

// alias to use template instance with default allocator
using ReportSkillVerification_Request =
  sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace sandwich_bt_interfaces


#ifndef _WIN32
# define DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Response __attribute__((deprecated))
#else
# define DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Response __declspec(deprecated)
#endif

namespace sandwich_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ReportSkillVerification_Response_
{
  using Type = ReportSkillVerification_Response_<ContainerAllocator>;

  explicit ReportSkillVerification_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
      this->applied_attempt_id = 0l;
      this->message = "";
    }
  }

  explicit ReportSkillVerification_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
      this->applied_attempt_id = 0l;
      this->message = "";
    }
  }

  // field types and members
  using _accepted_type =
    bool;
  _accepted_type accepted;
  using _applied_attempt_id_type =
    int32_t;
  _applied_attempt_id_type applied_attempt_id;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__accepted(
    const bool & _arg)
  {
    this->accepted = _arg;
    return *this;
  }
  Type & set__applied_attempt_id(
    const int32_t & _arg)
  {
    this->applied_attempt_id = _arg;
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
    sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Response
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Response
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ReportSkillVerification_Response_ & other) const
  {
    if (this->accepted != other.accepted) {
      return false;
    }
    if (this->applied_attempt_id != other.applied_attempt_id) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const ReportSkillVerification_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ReportSkillVerification_Response_

// alias to use template instance with default allocator
using ReportSkillVerification_Response =
  sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace sandwich_bt_interfaces


// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Event __attribute__((deprecated))
#else
# define DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Event __declspec(deprecated)
#endif

namespace sandwich_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ReportSkillVerification_Event_
{
  using Type = ReportSkillVerification_Event_<ContainerAllocator>;

  explicit ReportSkillVerification_Event_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit ReportSkillVerification_Event_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    service_msgs::msg::ServiceEventInfo_<ContainerAllocator>;
  _info_type info;
  using _request_type =
    rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>>;
  _request_type request;
  using _response_type =
    rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>>;
  _response_type response;

  // setters for named parameter idiom
  Type & set__info(
    const service_msgs::msg::ServiceEventInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__request(
    const rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::ReportSkillVerification_Request_<ContainerAllocator>>> & _arg)
  {
    this->request = _arg;
    return *this;
  }
  Type & set__response(
    const rosidl_runtime_cpp::BoundedVector<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sandwich_bt_interfaces::srv::ReportSkillVerification_Response_<ContainerAllocator>>> & _arg)
  {
    this->response = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator> *;
  using ConstRawPtr =
    const sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Event
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sandwich_bt_interfaces__srv__ReportSkillVerification_Event
    std::shared_ptr<sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ReportSkillVerification_Event_ & other) const
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
  bool operator!=(const ReportSkillVerification_Event_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ReportSkillVerification_Event_

// alias to use template instance with default allocator
using ReportSkillVerification_Event =
  sandwich_bt_interfaces::srv::ReportSkillVerification_Event_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace sandwich_bt_interfaces

namespace sandwich_bt_interfaces
{

namespace srv
{

struct ReportSkillVerification
{
  using Request = sandwich_bt_interfaces::srv::ReportSkillVerification_Request;
  using Response = sandwich_bt_interfaces::srv::ReportSkillVerification_Response;
  using Event = sandwich_bt_interfaces::srv::ReportSkillVerification_Event;
};

}  // namespace srv

}  // namespace sandwich_bt_interfaces

#endif  // SANDWICH_BT_INTERFACES__SRV__DETAIL__REPORT_SKILL_VERIFICATION__STRUCT_HPP_
