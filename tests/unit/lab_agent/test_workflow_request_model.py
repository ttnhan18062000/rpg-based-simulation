import pytest
from pydantic import ValidationError
from src.lab.request import WorkflowRequest

def test_generic_request_validation():
    """Verify that generic mode request requires user_goal and accepts standard constraints."""
    req = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="Create a high economy stress setup",
        constraints={"max_ticks": 10000}
    )
    assert req.workflow == "GenerateSimulationSetup"
    assert req.mode == "generic"
    assert req.user_goal == "Create a high economy stress setup"
    assert req.constraints == {"max_ticks": 10000}

def test_generic_request_missing_goal_rejected():
    """Verify that generic mode request throws ValidationError when user_goal is missing or empty."""
    with pytest.raises(ValidationError) as excinfo:
        WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="generic"
        )
    assert "user_goal is required" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="generic",
            user_goal="  "
        )
    assert "user_goal is required" in str(excinfo.value)

def test_specific_request_validation():
    """Verify that specific mode request requires specific_inputs and preserves constraints."""
    req = WorkflowRequest(
        workflow="PrepareSimulationExecution",
        mode="specific",
        specific_inputs={"world_type": "resource_valley", "workers": 200},
        constraints={"budget_profile": "local_dev"}
    )
    assert req.workflow == "PrepareSimulationExecution"
    assert req.mode == "specific"
    assert req.specific_inputs == {"world_type": "resource_valley", "workers": 200}
    assert req.constraints == {"budget_profile": "local_dev"}

def test_specific_request_missing_inputs_rejected():
    """Verify that specific mode request throws ValidationError when specific_inputs is empty."""
    with pytest.raises(ValidationError) as excinfo:
        WorkflowRequest(
            workflow="PrepareSimulationExecution",
            mode="specific",
            specific_inputs={}
        )
    assert "specific_inputs is required and cannot be empty" in str(excinfo.value)

def test_missing_workflow_rejected():
    """Verify that empty/None workflow throws ValidationError."""
    with pytest.raises(ValidationError):
        WorkflowRequest(
            workflow="",
            mode="generic",
            user_goal="A setup"
        )

def test_unknown_mode_rejected():
    """Verify that unknown mode literals are rejected."""
    with pytest.raises(ValidationError):
        WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="invalid_mode",
            user_goal="A setup"
        )

def test_generic_does_not_require_detailed_fields():
    """Verify that generic mode doesn't require specific inputs."""
    req = WorkflowRequest(
        workflow="GenerateSimulationSetup",
        mode="generic",
        user_goal="A high scale world"
    )
    assert req.specific_inputs == {}
