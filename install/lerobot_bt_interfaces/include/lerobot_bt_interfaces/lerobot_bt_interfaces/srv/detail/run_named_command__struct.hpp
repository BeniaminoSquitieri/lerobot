// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from lerobot_bt_interfaces:srv/RunNamedCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "lerobot_bt_interfaces/srv/run_named_command.hpp"


#ifndef LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__STRUCT_HPP_
#define LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Request __attribute__((deprecated))
#else
# define DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Request __declspec(deprecated)
#endif

namespace lerobot_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct RunNamedCommand_Request_
{
  using Type = RunNamedCommand_Request_<ContainerAllocator>;

  explicit RunNamedCommand_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->kind = "";
      this->name = "";
      this->timeout_s = 0.0f;
    }
  }

  explicit RunNamedCommand_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : kind(_alloc),
    name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->kind = "";
      this->name = "";
      this->timeout_s = 0.0f;
    }
  }

  // field types and members
  using _kind_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _kind_type kind;
  using _name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _name_type name;
  using _timeout_s_type =
    float;
  _timeout_s_type timeout_s;

  // setters for named parameter idiom
  Type & set__kind(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->kind = _arg;
    return *this;
  }
  Type & set__name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->name = _arg;
    return *this;
  }
  Type & set__timeout_s(
    const float & _arg)
  {
    this->timeout_s = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Request
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Request
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RunNamedCommand_Request_ & other) const
  {
    if (this->kind != other.kind) {
      return false;
    }
    if (this->name != other.name) {
      return false;
    }
    if (this->timeout_s != other.timeout_s) {
      return false;
    }
    return true;
  }
  bool operator!=(const RunNamedCommand_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RunNamedCommand_Request_

// alias to use template instance with default allocator
using RunNamedCommand_Request =
  lerobot_bt_interfaces::srv::RunNamedCommand_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace lerobot_bt_interfaces


#ifndef _WIN32
# define DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Response __attribute__((deprecated))
#else
# define DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Response __declspec(deprecated)
#endif

namespace lerobot_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct RunNamedCommand_Response_
{
  using Type = RunNamedCommand_Response_<ContainerAllocator>;

  explicit RunNamedCommand_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->status = "";
      this->elapsed_s = 0.0f;
      this->message = "";
    }
  }

  explicit RunNamedCommand_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : status(_alloc),
    message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->status = "";
      this->elapsed_s = 0.0f;
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _status_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _status_type status;
  using _elapsed_s_type =
    float;
  _elapsed_s_type elapsed_s;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__status(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__elapsed_s(
    const float & _arg)
  {
    this->elapsed_s = _arg;
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
    lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Response
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Response
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RunNamedCommand_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    if (this->elapsed_s != other.elapsed_s) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const RunNamedCommand_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RunNamedCommand_Response_

// alias to use template instance with default allocator
using RunNamedCommand_Response =
  lerobot_bt_interfaces::srv::RunNamedCommand_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace lerobot_bt_interfaces


// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Event __attribute__((deprecated))
#else
# define DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Event __declspec(deprecated)
#endif

namespace lerobot_bt_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct RunNamedCommand_Event_
{
  using Type = RunNamedCommand_Event_<ContainerAllocator>;

  explicit RunNamedCommand_Event_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit RunNamedCommand_Event_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    service_msgs::msg::ServiceEventInfo_<ContainerAllocator>;
  _info_type info;
  using _request_type =
    rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>>;
  _request_type request;
  using _response_type =
    rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>>;
  _response_type response;

  // setters for named parameter idiom
  Type & set__info(
    const service_msgs::msg::ServiceEventInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__request(
    const rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::RunNamedCommand_Request_<ContainerAllocator>>> & _arg)
  {
    this->request = _arg;
    return *this;
  }
  Type & set__response(
    const rosidl_runtime_cpp::BoundedVector<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<lerobot_bt_interfaces::srv::RunNamedCommand_Response_<ContainerAllocator>>> & _arg)
  {
    this->response = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator> *;
  using ConstRawPtr =
    const lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Event
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__lerobot_bt_interfaces__srv__RunNamedCommand_Event
    std::shared_ptr<lerobot_bt_interfaces::srv::RunNamedCommand_Event_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RunNamedCommand_Event_ & other) const
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
  bool operator!=(const RunNamedCommand_Event_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RunNamedCommand_Event_

// alias to use template instance with default allocator
using RunNamedCommand_Event =
  lerobot_bt_interfaces::srv::RunNamedCommand_Event_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace lerobot_bt_interfaces

namespace lerobot_bt_interfaces
{

namespace srv
{

struct RunNamedCommand
{
  using Request = lerobot_bt_interfaces::srv::RunNamedCommand_Request;
  using Response = lerobot_bt_interfaces::srv::RunNamedCommand_Response;
  using Event = lerobot_bt_interfaces::srv::RunNamedCommand_Event;
};

}  // namespace srv

}  // namespace lerobot_bt_interfaces

#endif  // LEROBOT_BT_INTERFACES__SRV__DETAIL__RUN_NAMED_COMMAND__STRUCT_HPP_
