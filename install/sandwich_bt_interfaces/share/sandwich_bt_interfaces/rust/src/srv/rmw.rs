#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__RunNamedCommand_Request() -> *const std::ffi::c_void;
}

#[link(name = "sandwich_bt_interfaces__rosidl_generator_c")]
extern "C" {
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Request__init(msg: *mut RunNamedCommand_Request) -> bool;
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RunNamedCommand_Request>, size: usize) -> bool;
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RunNamedCommand_Request>);
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RunNamedCommand_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<RunNamedCommand_Request>) -> bool;
}

// Corresponds to sandwich_bt_interfaces__srv__RunNamedCommand_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RunNamedCommand_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub kind: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub timeout_s: f32,

}



impl Default for RunNamedCommand_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sandwich_bt_interfaces__srv__RunNamedCommand_Request__init(&mut msg as *mut _) {
        panic!("Call to sandwich_bt_interfaces__srv__RunNamedCommand_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RunNamedCommand_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__RunNamedCommand_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__RunNamedCommand_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__RunNamedCommand_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RunNamedCommand_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RunNamedCommand_Request where Self: Sized {
  const TYPE_NAME: &'static str = "sandwich_bt_interfaces/srv/RunNamedCommand_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__RunNamedCommand_Request() }
  }
}


#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__RunNamedCommand_Response() -> *const std::ffi::c_void;
}

#[link(name = "sandwich_bt_interfaces__rosidl_generator_c")]
extern "C" {
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Response__init(msg: *mut RunNamedCommand_Response) -> bool;
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RunNamedCommand_Response>, size: usize) -> bool;
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RunNamedCommand_Response>);
    fn sandwich_bt_interfaces__srv__RunNamedCommand_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RunNamedCommand_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<RunNamedCommand_Response>) -> bool;
}

// Corresponds to sandwich_bt_interfaces__srv__RunNamedCommand_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RunNamedCommand_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub elapsed_s: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for RunNamedCommand_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sandwich_bt_interfaces__srv__RunNamedCommand_Response__init(&mut msg as *mut _) {
        panic!("Call to sandwich_bt_interfaces__srv__RunNamedCommand_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RunNamedCommand_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__RunNamedCommand_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__RunNamedCommand_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__RunNamedCommand_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RunNamedCommand_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RunNamedCommand_Response where Self: Sized {
  const TYPE_NAME: &'static str = "sandwich_bt_interfaces/srv/RunNamedCommand_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__RunNamedCommand_Response() }
  }
}


#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__PlanNextStep_Request() -> *const std::ffi::c_void;
}

#[link(name = "sandwich_bt_interfaces__rosidl_generator_c")]
extern "C" {
    fn sandwich_bt_interfaces__srv__PlanNextStep_Request__init(msg: *mut PlanNextStep_Request) -> bool;
    fn sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PlanNextStep_Request>, size: usize) -> bool;
    fn sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PlanNextStep_Request>);
    fn sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PlanNextStep_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<PlanNextStep_Request>) -> bool;
}

// Corresponds to sandwich_bt_interfaces__srv__PlanNextStep_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlanNextStep_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub current_task: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub available_robot_skills: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub available_human_skills: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub first_toast_on_plate: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ingredient_on_first_toast: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub second_toast_on_top: bool,

}



impl Default for PlanNextStep_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sandwich_bt_interfaces__srv__PlanNextStep_Request__init(&mut msg as *mut _) {
        panic!("Call to sandwich_bt_interfaces__srv__PlanNextStep_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PlanNextStep_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__PlanNextStep_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PlanNextStep_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PlanNextStep_Request where Self: Sized {
  const TYPE_NAME: &'static str = "sandwich_bt_interfaces/srv/PlanNextStep_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__PlanNextStep_Request() }
  }
}


#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__PlanNextStep_Response() -> *const std::ffi::c_void;
}

#[link(name = "sandwich_bt_interfaces__rosidl_generator_c")]
extern "C" {
    fn sandwich_bt_interfaces__srv__PlanNextStep_Response__init(msg: *mut PlanNextStep_Response) -> bool;
    fn sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PlanNextStep_Response>, size: usize) -> bool;
    fn sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PlanNextStep_Response>);
    fn sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PlanNextStep_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<PlanNextStep_Response>) -> bool;
}

// Corresponds to sandwich_bt_interfaces__srv__PlanNextStep_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlanNextStep_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub step_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub actor: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub reason: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub expected_state: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,

}



impl Default for PlanNextStep_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sandwich_bt_interfaces__srv__PlanNextStep_Response__init(&mut msg as *mut _) {
        panic!("Call to sandwich_bt_interfaces__srv__PlanNextStep_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PlanNextStep_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__PlanNextStep_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PlanNextStep_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PlanNextStep_Response where Self: Sized {
  const TYPE_NAME: &'static str = "sandwich_bt_interfaces/srv/PlanNextStep_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__PlanNextStep_Response() }
  }
}


#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__VerifyStep_Request() -> *const std::ffi::c_void;
}

#[link(name = "sandwich_bt_interfaces__rosidl_generator_c")]
extern "C" {
    fn sandwich_bt_interfaces__srv__VerifyStep_Request__init(msg: *mut VerifyStep_Request) -> bool;
    fn sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<VerifyStep_Request>, size: usize) -> bool;
    fn sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<VerifyStep_Request>);
    fn sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<VerifyStep_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<VerifyStep_Request>) -> bool;
}

// Corresponds to sandwich_bt_interfaces__srv__VerifyStep_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct VerifyStep_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub step_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub first_toast_on_plate: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ingredient_on_first_toast: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub second_toast_on_top: bool,

}



impl Default for VerifyStep_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sandwich_bt_interfaces__srv__VerifyStep_Request__init(&mut msg as *mut _) {
        panic!("Call to sandwich_bt_interfaces__srv__VerifyStep_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for VerifyStep_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__VerifyStep_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for VerifyStep_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for VerifyStep_Request where Self: Sized {
  const TYPE_NAME: &'static str = "sandwich_bt_interfaces/srv/VerifyStep_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__VerifyStep_Request() }
  }
}


#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__VerifyStep_Response() -> *const std::ffi::c_void;
}

#[link(name = "sandwich_bt_interfaces__rosidl_generator_c")]
extern "C" {
    fn sandwich_bt_interfaces__srv__VerifyStep_Response__init(msg: *mut VerifyStep_Response) -> bool;
    fn sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<VerifyStep_Response>, size: usize) -> bool;
    fn sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<VerifyStep_Response>);
    fn sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<VerifyStep_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<VerifyStep_Response>) -> bool;
}

// Corresponds to sandwich_bt_interfaces__srv__VerifyStep_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct VerifyStep_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub observed_state: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub failure_reason: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,

}



impl Default for VerifyStep_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sandwich_bt_interfaces__srv__VerifyStep_Response__init(&mut msg as *mut _) {
        panic!("Call to sandwich_bt_interfaces__srv__VerifyStep_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for VerifyStep_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sandwich_bt_interfaces__srv__VerifyStep_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for VerifyStep_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for VerifyStep_Response where Self: Sized {
  const TYPE_NAME: &'static str = "sandwich_bt_interfaces/srv/VerifyStep_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sandwich_bt_interfaces__srv__VerifyStep_Response() }
  }
}






#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__sandwich_bt_interfaces__srv__RunNamedCommand() -> *const std::ffi::c_void;
}

// Corresponds to sandwich_bt_interfaces__srv__RunNamedCommand
#[allow(missing_docs, non_camel_case_types)]
pub struct RunNamedCommand;

impl rosidl_runtime_rs::Service for RunNamedCommand {
    type Request = RunNamedCommand_Request;
    type Response = RunNamedCommand_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__sandwich_bt_interfaces__srv__RunNamedCommand() }
    }
}




#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__sandwich_bt_interfaces__srv__PlanNextStep() -> *const std::ffi::c_void;
}

// Corresponds to sandwich_bt_interfaces__srv__PlanNextStep
#[allow(missing_docs, non_camel_case_types)]
pub struct PlanNextStep;

impl rosidl_runtime_rs::Service for PlanNextStep {
    type Request = PlanNextStep_Request;
    type Response = PlanNextStep_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__sandwich_bt_interfaces__srv__PlanNextStep() }
    }
}




#[link(name = "sandwich_bt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__sandwich_bt_interfaces__srv__VerifyStep() -> *const std::ffi::c_void;
}

// Corresponds to sandwich_bt_interfaces__srv__VerifyStep
#[allow(missing_docs, non_camel_case_types)]
pub struct VerifyStep;

impl rosidl_runtime_rs::Service for VerifyStep {
    type Request = VerifyStep_Request;
    type Response = VerifyStep_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__sandwich_bt_interfaces__srv__VerifyStep() }
    }
}


