# Compliance IDs: SCENARIO-001, SCENARIO-002, SCENARIO-003
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional, Any, Annotated, Literal, Union
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


class InvalidExperimentSpecError(Exception):
    """Custom exception raised when an experiment specification is malformed or invalid."""
    pass


class ExperimentRunSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    ticks: int = Field(..., gt=0, description="Number of simulation ticks to run")
    seeds: list[int] = Field(..., min_length=1, description="List of random seed values")
    repeat_count: int = Field(1, gt=0, description="Times to repeat each seed execution")
    max_parallel_runs: int = Field(1, ge=1, description="Concurrency factor for execution")


class ExperimentObservabilitySpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    mode: str = Field(..., description="Observability detail mode, e.g. 'LONG_RUN'")
    record_events: bool = Field(True, description="Whether to store raw event logs")
    record_metric_windows: bool = Field(True, description="Whether to record windowed metrics")
    record_cognition: bool = Field(False, description="Whether to record cognition graph snapshots")


class ExperimentAnalysisSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    run_post_analysis: bool = Field(True, description="Execute post-run metric analyzers")
    generate_report: bool = Field(True, description="Compile MD report profiles")
    run_mining: bool = Field(False, description="Run pattern mining checks")
    compare_baseline: bool = Field(False, description="Compare against a baseline run")
    baseline_id: Optional[str] = Field(None, description="The baseline ID to compare against")


class ExperimentRetentionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    keep_raw_events: bool = Field(True, description="Retain heavy events files")
    keep_reports: bool = Field(True, description="Retain markdown reports")
    max_artifact_mb: int = Field(500, ge=0, description="Max disk space allowed per single run")


class ExperimentBudgetsSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    max_runtime_minutes: int = Field(60, gt=0, description="Max total runtime allowed for this lab run")
    max_total_artifact_mb: int = Field(2000, gt=0, description="Max accumulated storage budget across all runs")
    max_runs: Optional[int] = Field(100, gt=0, description="Max allowed execution runs count in matrix")
    max_total_ticks: Optional[int] = Field(10000000, gt=0, description="Max allowed total tick accumulation count")
    max_parallel_runs: Optional[int] = Field(4, ge=1, description="Max concurrency level allowed")


VALID_EXPERIMENT_TYPES = {
    "single_run",
    "multi_seed_sweep",
    "same_seed_repeat",
    "baseline_generation",
    "baseline_comparison"
}


class ExperimentSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")
    
    schema_version: str = Field(..., description="Schema version, e.g. 'experimentspec.v1'")
    experiment_id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Unique alphanumeric identifier")
    scenario_id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Associated scenario ID")
    experiment_type: str = Field(..., description="Explicit execution type mode")
    
    run: ExperimentRunSpec = Field(..., description="Execution configurations")
    observability: ExperimentObservabilitySpec = Field(..., description="Observability targets")
    analysis: ExperimentAnalysisSpec = Field(..., description="Analysis and mining tasks")
    retention: ExperimentRetentionSpec = Field(..., description="Artifact retention policy")
    budgets: ExperimentBudgetsSpec = Field(..., description="Lab safety resource bounds")

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "experimentspec.v1":
            raise ValueError("schema_version must strictly be 'experimentspec.v1'")
        return v

    @field_validator("experiment_type")
    @classmethod
    def validate_experiment_type(cls, v: str) -> str:
        if v not in VALID_EXPERIMENT_TYPES:
            raise ValueError(f"experiment_type must be one of: {sorted(list(VALID_EXPERIMENT_TYPES))}")
        return v


def load_experiment_spec_from_yaml(path: str | Path) -> ExperimentSpec:
    """
    Safely loads, parses, and instantiates an ExperimentSpec from a YAML file.
    Raises InvalidExperimentSpecError if file is not found, YAML parser fails, or schema validation fails.
    """
    p = Path(path)
    if not p.is_file():
        raise InvalidExperimentSpecError(f"Experiment spec file not found: {p}")
        
    try:
        with open(p, "r") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise InvalidExperimentSpecError(f"YAML parser error loading '{p}': {e}") from e
    except Exception as e:
        raise InvalidExperimentSpecError(f"Failed to read file '{p}': {e}") from e

    if not isinstance(raw_data, dict):
        raise InvalidExperimentSpecError(f"Experiment spec YAML must root in a dictionary element: '{p}'")

    try:
        return ExperimentSpec(**raw_data)
    except ValidationError as e:
        raise InvalidExperimentSpecError(f"Experiment spec validation failed for '{p}':\n{e}") from e


class InvalidLabRunManifestError(Exception):
    """Custom exception raised when a lab run manifest is malformed or invalid."""
    pass


VALID_LABRUN_STATUSES = {
    "CREATED",
    "VALIDATING",
    "COMPILING",
    "RUNNING",
    "ANALYZING",
    "COMPLETED",
    "FAILED",
    "PARTIAL",
    "CANCELLED"
}


class LabRunManifest(BaseModel):
    model_config = ConfigDict(frozen=False, extra="allow")
    
    lab_run_id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Unique alphanumeric identifier")
    world_id: str = Field(..., min_length=1, description="Associated world ID")
    scenario_id: str = Field(..., min_length=1, description="Associated scenario ID")
    experiment_id: str = Field(..., min_length=1, description="Associated experiment ID")
    status: str = Field("CREATED", description="Current execution state")
    started_at: str = Field(..., description="ISO 8601 timestamp at initialization")
    ended_at: Optional[str] = Field(None, description="ISO 8601 timestamp at termination")
    run_count: int = Field(0, ge=0, description="Total planned runs")
    completed_run_count: int = Field(0, ge=0, description="Successful runs")
    failed_run_count: int = Field(0, ge=0, description="Failed runs")
    artifact_root: str = Field(..., description="Canonical path to run folder")
    schema_versions: dict[str, str] = Field(default_factory=dict, description="Metadata schema tracking")
    budgets: dict[str, Any] = Field(default_factory=dict, description="Resource bounds")
    storage_usage_mb: float = Field(0.0, ge=0.0, description="Calculated folder disk footprint")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_LABRUN_STATUSES:
            raise ValueError(f"status must be one of: {sorted(list(VALID_LABRUN_STATUSES))}")
        return v


# --- Mutation Spec ---

class InvalidMutationSpecError(Exception):
    """Custom exception raised when a mutation specification is structurally invalid or missing files."""
    pass


class BaseMutation(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Unique ID for this mutation variant segment")
    target: str = Field(..., min_length=1, description="Dot-notation path targeting WorldSpec or ScenarioSpec")


class NumericMutation(BaseMutation):
    value: float = Field(..., description="Numeric operand value")


class SetMutation(BaseMutation):
    operation: Literal["set"] = "set"
    value: Any = Field(..., description="Value to replace target with")


class AddMutation(NumericMutation):
    operation: Literal["add"] = "add"


class MultiplyMutation(NumericMutation):
    operation: Literal["multiply"] = "multiply"


class ToggleMutation(BaseMutation):
    operation: Literal["toggle"] = "toggle"
    value: Optional[bool] = Field(None, description="Optional target boolean state override")


class RemoveMutation(BaseMutation):
    operation: Literal["remove"] = "remove"


class DuplicateMutation(BaseMutation):
    operation: Literal["duplicate"] = "duplicate"
    value: str = Field(..., min_length=1, description="New identifier for the duplicated object")


MutationItem = Annotated[
    Union[
        SetMutation,
        AddMutation,
        MultiplyMutation,
        ToggleMutation,
        RemoveMutation,
        DuplicateMutation
    ],
    Field(discriminator="operation")
]


class MatrixSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    mode: str = Field(..., description="Matrix sweep mode: 'one_at_a_time', 'combined', or 'factorial_limited'")
    max_variants: int = Field(50, gt=0, description="Hard ceiling on generated variants count to prevent combinatorial explosion")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid_modes = {"one_at_a_time", "combined", "factorial_limited"}
        if v not in valid_modes:
            raise ValueError(f"mode must be one of {sorted(list(valid_modes))}")
        return v


class ExpectedRelationshipSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(..., min_length=1, description="Unique relationship expectation identifier")
    type: str = Field(..., description="Metamorphic rule type")
    metric: str = Field(..., min_length=1, description="Observability metric name to monitor")
    baseline_variant: str = Field("base", description="Variant ID serving as the baseline")
    compared_variant: str = Field(..., description="Variant ID to compare against baseline")
    tolerance: Optional[float] = Field(None, ge=0.0, description="Tolerance band for 'within_tolerance'")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {
            "monotonic_non_decreasing",
            "monotonic_non_increasing",
            "within_tolerance",
            "expected_worse",
            "expected_better",
            "no_new_hard_law_violation"
        }
        if v not in valid_types:
            raise ValueError(f"type must be one of {sorted(list(valid_types))}")
        return v


class MutationBudgetsSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_variant_count: int = Field(20, gt=0, description="Maximum variants permitted across this lab run")
    max_total_ticks: int = Field(100000, gt=0, description="Cumulative tick limit allowed for all runs combined")


class MutationSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")
    
    schema_version: str = Field(..., description="Schema version identifier, strictly 'mutationspec.v1'")
    mutation_id: str = Field(..., min_length=1, pattern="^[a-zA-Z0-9_-]+$", description="Unique mutation matrix identifier")
    name: str = Field(..., min_length=1, description="Human-readable description of this mutation sweep")
    
    base_world_id: str = Field(..., min_length=1, description="Target base world template identifier")
    base_scenario_id: str = Field(..., min_length=1, description="Target base scenario configuration")
    
    mutations: list[MutationItem] = Field(default_factory=list, description="List of mutations to apply")
    matrix: MatrixSpec = Field(..., description="Variant matrix configuration")
    expected_relationships: list[ExpectedRelationshipSpec] = Field(default_factory=list, description="Metamorphic assertions")
    budgets: Optional[MutationBudgetsSpec] = Field(None, description="Optional safety guardrail budgets")
    tags: list[str] = Field(default_factory=list, description="Optional metadata search tags")

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "mutationspec.v1":
            raise ValueError("schema_version must strictly be 'mutationspec.v1'")
        return v


def load_mutation_spec_from_yaml(path: str | Path) -> MutationSpec:
    """
    Safely opens, parses, and validates a MutationSpec from a YAML file.
    """
    p = Path(path)
    if not p.is_file():
        raise InvalidMutationSpecError(f"Mutation spec file not found: {p}")
        
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise InvalidMutationSpecError(f"YAML parsing error loading '{p}': {e}") from e
    except Exception as e:
        raise InvalidMutationSpecError(f"Failed to read file '{p}': {e}") from e

    if not isinstance(raw_data, dict):
        raise InvalidMutationSpecError(f"Mutation spec YAML must root in a dictionary element: '{p}'")

    try:
        return MutationSpec.model_validate(raw_data)
    except ValidationError as e:
        errors_summary = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors_summary.append(f"Field '{loc}': {msg}")
        joined_errors = "; ".join(errors_summary)
        raise InvalidMutationSpecError(
            f"MutationSpec validation failed for '{p}':\n{joined_errors}"
        ) from e


class VariantManifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    variant_id: str = Field(..., description="Unique generated variant identifier")
    base_world_id: str = Field(..., description="Referenced baseline world spec ID")
    base_scenario_id: str = Field(..., description="Referenced baseline scenario spec ID")
    applied_mutations: list[str] = Field(default_factory=list, description="List of mutation IDs applied to this variant")
    world_spec_path: str = Field(..., description="Path to the mutated world specification file")
    scenario_spec_path: str = Field(..., description="Path to the mutated scenario specification file")
    status: str = Field(..., description="Outcome status, strictly 'VALIDATED' or 'FAILED'")
    validation_result: Optional[dict] = Field(None, description="Detailed validation error dictionary if status is FAILED")




