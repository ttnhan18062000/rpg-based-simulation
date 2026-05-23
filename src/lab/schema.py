# Compliance IDs: SCENARIO-001, SCENARIO-002, SCENARIO-003
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator, ValidationError

class InvalidScenarioSpecError(Exception):
    """Custom exception raised when a scenario specification is malformed or invalid."""
    pass

class IntentSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    primary_goal: str = Field(..., min_length=1, description="Primary goal identifier")
    description: Optional[str] = Field("", description="Human-readable description of the intent")

class ExpectedLimitSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    min: Optional[float] = Field(None, description="Minimum acceptable value of the metric")
    max: Optional[float] = Field(None, description="Maximum acceptable value of the metric")

    @model_validator(mode="after")
    def validate_limits(self) -> ExpectedLimitSpec:
        if self.min is None and self.max is None:
            raise ValueError("At least one of 'min' or 'max' limit must be specified.")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"Limit min ({self.min}) cannot be greater than max ({self.max})")
        return self

class RequiredSignalsSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    metrics: list[str] = Field(default_factory=list, description="Telemetry metrics to record")
    events: list[str] = Field(default_factory=list, description="Simulation events to record")
    cognition: list[str] = Field(default_factory=list, description="Cognition keys to record")

class ScenarioSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")
    
    schema_version: str = Field(..., description="Schema version, e.g. 'scenariospec.v1'")
    scenario_id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Unique alphanumeric identifier")
    name: str = Field(..., min_length=1, description="Human-readable scenario name")
    world_id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Associated world ID")
    scenario_type: str = Field(..., min_length=1, description="The category type of the scenario")
    
    intent: IntentSpec = Field(..., description="The objective and goal descriptions")
    expected_behavior: dict[str, ExpectedLimitSpec] = Field(default_factory=dict, description="Metric-based validation bounds")
    required_signals: RequiredSignalsSpec = Field(default_factory=RequiredSignalsSpec, description="Signals to monitor")
    allowed_anomalies: list[str] = Field(default_factory=list, description="Anomalies permitted to occur")
    critical_anomalies: list[str] = Field(default_factory=list, description="Anomalies that immediately trigger failure")
    tags: list[str] = Field(default_factory=list, description="Metadata tags")

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "scenariospec.v1":
            raise ValueError("schema_version must strictly be 'scenariospec.v1'")
        return v

def load_scenario_spec_from_yaml(path: str | Path) -> ScenarioSpec:
    """
    Safely loads, parses, and instantiates a ScenarioSpec from a YAML file.
    Raises InvalidScenarioSpecError if file is not found, YAML parser fails, or schema validation fails.
    """
    p = Path(path)
    if not p.is_file():
        raise InvalidScenarioSpecError(f"Scenario spec file not found: {p}")
        
    try:
        with open(p, "r") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise InvalidScenarioSpecError(f"YAML parser error loading '{p}': {e}") from e
    except Exception as e:
        raise InvalidScenarioSpecError(f"Failed to read file '{p}': {e}") from e

    if not isinstance(raw_data, dict):
        raise InvalidScenarioSpecError(f"Scenario spec YAML must root in a dictionary element: '{p}'")

    try:
        return ScenarioSpec(**raw_data)
    except ValidationError as e:
        raise InvalidScenarioSpecError(f"Scenario spec validation failed for '{p}':\n{e}") from e
