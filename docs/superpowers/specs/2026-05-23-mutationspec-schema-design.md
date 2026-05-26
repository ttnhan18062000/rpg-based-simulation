# MutationSpec Schema Design Spec (Milestone 84)

This specification defines the schema, Pydantic models, file parser loader, and pluggable validator framework for `MutationSpec` (Milestone 84 under Phase 13 - Mutation and Balance Lab). 

---

## 1. Architectural Boundaries and Core Principle

The MutationSpec represents a controlled variation parameter matrix. Following the Core Boundaries of the RPG Engine architecture:
1. **Separation of Concerns:** The schema parsing and logical specification must remain decoupled from the active simulation loop.
2. **Immutable base specs:** The baseline `WorldSpec` and `ScenarioSpec` are strictly read-only and must never be modified in place.
3. **Pluggable and Rule-based verification:** Sanity checks are orchestrated via pluggable, isolated verification rules returning distinct `ValidationIssue` models.

---

## 2. Pydantic Spec Schema Models

We implement **Approach B (Strongly-Typed Polymorphic Operations)** using Pydantic's discriminated unions (`Field(..., discriminator="operation")`) to provide load-time type verification.

```python
from __future__ import annotations
from typing import Literal, Optional, Any, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- 1. Mutation Operation Subclasses (Polymorphic Union) ---
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

# The Discriminated Union definition
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

# --- 2. Supporting Specs ---
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
    type: str = Field(..., description="Metamorphic rule type: monotonic_non_decreasing, monotonic_non_increasing, within_tolerance, expected_worse, expected_better, no_new_hard_law_violation")
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

# --- 3. Root Specification ---
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
```

---

## 3. Safe Parser & Loading Function

`load_mutation_spec_from_yaml` encapsulates parsing logic to block raw traceback leakage:

```python
class InvalidMutationSpecError(Exception):
    """Custom exception raised when a mutation specification is structurally invalid or missing files."""
    pass


def load_mutation_spec_from_yaml(path: str | Path) -> MutationSpec:
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
```

---

## 4. Pluggable Validator Framework

Pluggable validation rules ensure robust sanity checking prior to simulation execution.

```python
class MutationValidationRule:
    """Base class for all pluggable mutation specification validation rules."""
    rule_id: str
    severity: str
    description: str

    def validate(
        self, 
        spec: MutationSpec, 
        world_repo: Optional[WorldRepository] = None, 
        scenario_repo: Optional[Any] = None
    ) -> list[ValidationIssue]:
        raise NotImplementedError


class BaseReferencesRule(MutationValidationRule):
    rule_id = "MUTATION-REF-001"
    severity = "ERROR"
    description = "Verify that the base world and scenario specs referenced actually exist."

    def validate(
        self, 
        spec: MutationSpec, 
        world_repo: Optional[WorldRepository] = None, 
        scenario_repo: Optional[Any] = None
    ) -> list[ValidationIssue]:
        issues = []
        if world_repo is not None:
            if spec.base_world_id not in world_repo.list_worlds():
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"MutationSpec references a non-existent base_world_id: '{spec.base_world_id}'",
                    path="base_world_id"
                ))
        if scenario_repo is not None:
            if spec.base_scenario_id not in scenario_repo.list_scenarios():
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"MutationSpec references a non-existent base_scenario_id: '{spec.base_scenario_id}'",
                    path="base_scenario_id"
                ))
        return issues


class MetamorphicRelationshipRule(MutationValidationRule):
    rule_id = "MUTATION-META-001"
    severity = "ERROR"
    description = "Verify that metamorphic rules reference known variant IDs and valid standard metrics."

    def validate(
        self, 
        spec: MutationSpec, 
        world_repo: Optional[WorldRepository] = None, 
        scenario_repo: Optional[Any] = None
    ) -> list[ValidationIssue]:
        issues = []
        defined_mutation_ids = {m.id for m in spec.mutations}
        defined_mutation_ids.add("base")

        for i, rel in enumerate(spec.expected_relationships):
            if rel.baseline_variant not in defined_mutation_ids:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="ERROR",
                    message=f"Metamorphic rule '{rel.id}' references an undefined baseline variant ID: '{rel.baseline_variant}'",
                    path=f"expected_relationships.{i}.baseline_variant"
                ))
            if rel.compared_variant not in defined_mutation_ids:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="ERROR",
                    message=f"Metamorphic rule '{rel.id}' references an undefined compared variant ID: '{rel.compared_variant}'",
                    path=f"expected_relationships.{i}.compared_variant"
                ))
            if rel.metric not in STANDARD_METRICS:
                issues.append(ValidationIssue(
                    rule_id="MUTATION-META-WARN",
                    severity="WARNING",
                    message=f"Metamorphic rule '{rel.id}' references unrecognized metric '{rel.metric}'. Metamorphic validation may result in INSUFFICIENT_DATA if telemetry is missing.",
                    path=f"expected_relationships.{i}.metric"
                ))
        return issues


class MutationValidator:
    def __init__(
        self, 
        world_repo: Optional[WorldRepository] = None, 
        scenario_repo: Optional[Any] = None, 
        rules: Optional[list[MutationValidationRule]] = None
    ):
        self.world_repo = world_repo
        self.scenario_repo = scenario_repo
        if rules is None:
            self.rules = [
                BaseReferencesRule(),
                MetamorphicRelationshipRule()
            ]
        else:
            self.rules = rules

    def validate(self, spec: MutationSpec, strict: bool = False) -> list[ValidationIssue]:
        issues = []
        for rule in self.rules:
            issues.extend(rule.validate(spec, self.world_repo, self.scenario_repo))
            
        errors = [x for x in issues if x.severity == "ERROR"]
        warnings = [x for x in issues if x.severity == "WARNING"]
        
        if errors:
            raise InvalidMutationSpecError(
                f"MutationSpec validation failed with {len(errors)} errors: " + 
                ", ".join(e.message for e in errors)
            )
        if strict and warnings:
            raise InvalidMutationSpecError(
                f"MutationSpec strict validation failed with {len(warnings)} warnings: " + 
                ", ".join(w.message for w in warnings)
            )
        return issues
```

---

## 5. Verification Plan (Testing Strategy)

### Automated Test Cases (`tests/unit/lab/test_mutationspec_schema.py` & `test_mutationspec_validator.py`):
1. **`test_valid_mutationspec_loads`**: Standard, complex `MutationSpec` YAML with all polymorphic operation types (`set`, `add`, `multiply`, `toggle`, `remove`, `duplicate`) parses successfully.
2. **`test_missing_id_and_ids_rejected`**: Ensures missing `mutation_id` or base identifiers trigger Pydantic parse failure.
3. **`test_invalid_operation_rejected`**: Ensuring invalid operation literals (e.g. `operation: "divide"`) are rejected immediately.
4. **`test_matrix_validation_modes`**: Matrix sweeps reject invalid mode names but pass valid ones (`one_at_a_time`, `combined`).
5. **`test_validator_base_references`**: Verifies `MutationValidator` blocks specs referencing non-existent base worlds or scenarios when repos are supplied.
6. **`test_validator_metamorphic_variant_existence`**: Verifies that metamorphic rules referencing undefined variant IDs are caught and blocked.
7. **`test_validator_unrecognized_metric_warning`**: Warns when metamorphic rules assert conditions on unrecognized metrics.
8. **`test_strict_mode_warnings_elevated`**: Verifies that `strict=True` elevates unrecognized metric warnings into errors.
9. **`test_future_fields_preserved`**: Ensures other top-level metadata fields or configuration variations not yet hard-supported are preserved in `model_extra`.
