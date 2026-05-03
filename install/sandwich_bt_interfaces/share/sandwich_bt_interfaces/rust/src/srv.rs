#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to sandwich_bt_interfaces__srv__RunNamedCommand_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RunNamedCommand_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub kind: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub timeout_s: f32,

}



impl Default for RunNamedCommand_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::RunNamedCommand_Request::default())
  }
}

impl rosidl_runtime_rs::Message for RunNamedCommand_Request {
  type RmwMsg = super::srv::rmw::RunNamedCommand_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        kind: msg.kind.as_str().into(),
        name: msg.name.as_str().into(),
        timeout_s: msg.timeout_s,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        kind: msg.kind.as_str().into(),
        name: msg.name.as_str().into(),
      timeout_s: msg.timeout_s,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      kind: msg.kind.to_string(),
      name: msg.name.to_string(),
      timeout_s: msg.timeout_s,
    }
  }
}


// Corresponds to sandwich_bt_interfaces__srv__RunNamedCommand_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RunNamedCommand_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub elapsed_s: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for RunNamedCommand_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::RunNamedCommand_Response::default())
  }
}

impl rosidl_runtime_rs::Message for RunNamedCommand_Response {
  type RmwMsg = super::srv::rmw::RunNamedCommand_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        status: msg.status.as_str().into(),
        elapsed_s: msg.elapsed_s,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        status: msg.status.as_str().into(),
      elapsed_s: msg.elapsed_s,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      status: msg.status.to_string(),
      elapsed_s: msg.elapsed_s,
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to sandwich_bt_interfaces__srv__PlanNextStep_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlanNextStep_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub current_task: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub available_robot_skills: Vec<std::string::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub available_human_skills: Vec<std::string::String>,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::PlanNextStep_Request::default())
  }
}

impl rosidl_runtime_rs::Message for PlanNextStep_Request {
  type RmwMsg = super::srv::rmw::PlanNextStep_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal: msg.goal.as_str().into(),
        current_task: msg.current_task.as_str().into(),
        available_robot_skills: msg.available_robot_skills
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        available_human_skills: msg.available_human_skills
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        first_toast_on_plate: msg.first_toast_on_plate,
        ingredient_on_first_toast: msg.ingredient_on_first_toast,
        second_toast_on_top: msg.second_toast_on_top,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        goal: msg.goal.as_str().into(),
        current_task: msg.current_task.as_str().into(),
        available_robot_skills: msg.available_robot_skills
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        available_human_skills: msg.available_human_skills
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      first_toast_on_plate: msg.first_toast_on_plate,
      ingredient_on_first_toast: msg.ingredient_on_first_toast,
      second_toast_on_top: msg.second_toast_on_top,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      goal: msg.goal.to_string(),
      current_task: msg.current_task.to_string(),
      available_robot_skills: msg.available_robot_skills
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      available_human_skills: msg.available_human_skills
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      first_toast_on_plate: msg.first_toast_on_plate,
      ingredient_on_first_toast: msg.ingredient_on_first_toast,
      second_toast_on_top: msg.second_toast_on_top,
    }
  }
}


// Corresponds to sandwich_bt_interfaces__srv__PlanNextStep_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlanNextStep_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub step_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub actor: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub reason: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub expected_state: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,

}



impl Default for PlanNextStep_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::PlanNextStep_Response::default())
  }
}

impl rosidl_runtime_rs::Message for PlanNextStep_Response {
  type RmwMsg = super::srv::rmw::PlanNextStep_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        step_name: msg.step_name.as_str().into(),
        actor: msg.actor.as_str().into(),
        reason: msg.reason.as_str().into(),
        expected_state: msg.expected_state.as_str().into(),
        confidence: msg.confidence,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        step_name: msg.step_name.as_str().into(),
        actor: msg.actor.as_str().into(),
        reason: msg.reason.as_str().into(),
        expected_state: msg.expected_state.as_str().into(),
      confidence: msg.confidence,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      step_name: msg.step_name.to_string(),
      actor: msg.actor.to_string(),
      reason: msg.reason.to_string(),
      expected_state: msg.expected_state.to_string(),
      confidence: msg.confidence,
    }
  }
}


// Corresponds to sandwich_bt_interfaces__srv__VerifyStep_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct VerifyStep_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub step_name: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::VerifyStep_Request::default())
  }
}

impl rosidl_runtime_rs::Message for VerifyStep_Request {
  type RmwMsg = super::srv::rmw::VerifyStep_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        step_name: msg.step_name.as_str().into(),
        first_toast_on_plate: msg.first_toast_on_plate,
        ingredient_on_first_toast: msg.ingredient_on_first_toast,
        second_toast_on_top: msg.second_toast_on_top,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        step_name: msg.step_name.as_str().into(),
      first_toast_on_plate: msg.first_toast_on_plate,
      ingredient_on_first_toast: msg.ingredient_on_first_toast,
      second_toast_on_top: msg.second_toast_on_top,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      step_name: msg.step_name.to_string(),
      first_toast_on_plate: msg.first_toast_on_plate,
      ingredient_on_first_toast: msg.ingredient_on_first_toast,
      second_toast_on_top: msg.second_toast_on_top,
    }
  }
}


// Corresponds to sandwich_bt_interfaces__srv__VerifyStep_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct VerifyStep_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub observed_state: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub failure_reason: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,

}



impl Default for VerifyStep_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::VerifyStep_Response::default())
  }
}

impl rosidl_runtime_rs::Message for VerifyStep_Response {
  type RmwMsg = super::srv::rmw::VerifyStep_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        observed_state: msg.observed_state.as_str().into(),
        failure_reason: msg.failure_reason.as_str().into(),
        confidence: msg.confidence,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        observed_state: msg.observed_state.as_str().into(),
        failure_reason: msg.failure_reason.as_str().into(),
      confidence: msg.confidence,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      observed_state: msg.observed_state.to_string(),
      failure_reason: msg.failure_reason.to_string(),
      confidence: msg.confidence,
    }
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


