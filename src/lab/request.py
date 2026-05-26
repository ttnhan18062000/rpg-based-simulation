from __future__ import annotations

from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

class WorkflowRequest(BaseModel):
    """Pydantic model representing a verified input request for Phase 14 workflows."""
    model_config = ConfigDict(frozen=True, extra="allow")

    workflow: str = Field(..., min_length=1, description="Target workflow name")
    mode: Literal["generic", "specific"] = Field("generic", description="Workflow execution mode")
    user_goal: Optional[str] = Field(None, description="High-level user goal, required in generic mode")
    specific_inputs: Dict[str, Any] = Field(default_factory=dict, description="Exact parameters, required in specific mode")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Validation constraints like budgets and ticks")

    @model_validator(mode="after")
    def validate_mode_requirements(self) -> WorkflowRequest:
        """Enforces mode-specific required fields directly during Pydantic instantiation."""
        if self.mode == "generic":
            if not self.user_goal or not self.user_goal.strip():
                raise ValueError("user_goal is required and cannot be empty when mode is 'generic'.")
        elif self.mode == "specific":
            # For specific mode, specific_inputs must be provided and not empty
            if not self.specific_inputs:
                raise ValueError("specific_inputs is required and cannot be empty when mode is 'specific'.")
        return self
