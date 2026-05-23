# Compliance IDs: SCENARIO-004, SCENARIO-005, SCENARIO-006
from __future__ import annotations

from typing import Optional, Any
from src.worldbuilding.validator import ValidationIssue
from src.worldbuilding.repository import WorldRepository
from src.lab.schema import (
    ScenarioSpec,
    InvalidScenarioSpecError,
    ExperimentSpec,
    InvalidExperimentSpecError,
    MutationSpec,
    InvalidMutationSpecError
)


class ScenarioValidationRule:
    """Base class for all pluggable scenario specification validation rules."""
    rule_id: str
    severity: str
    description: str

    def validate(self, spec: ScenarioSpec, world_repo: Optional[WorldRepository] = None) -> list[ValidationIssue]:
        raise NotImplementedError

class WorldExistenceRule(ScenarioValidationRule):
    rule_id = "SCENARIO-REF-001"
    severity = "ERROR"
    description = "Verify that the referenced world_id exists in the current repository."

    def validate(self, spec: ScenarioSpec, world_repo: Optional[WorldRepository] = None) -> list[ValidationIssue]:
        if world_repo is None:
            # If no repo is provided, we skip for structural-only checks
            return []
            
        if spec.world_id not in world_repo.list_worlds():
            return [ValidationIssue(
                rule_id=self.rule_id,
                severity=self.severity,
                message=f"Scenario references a non-existent world_id: '{spec.world_id}'",
                path="world_id"
            )]
        return []

STANDARD_METRICS = {
    "hard_law_violations",
    "resource_production_rate",
    "stuck_entity_ratio",
    "active_worker_count",
    "inventory_full_ratio"
}

class ExpectedBehaviorRule(ScenarioValidationRule):
    rule_id = "SCENARIO-LIMIT-001"
    severity = "WARNING"
    description = "Validate expected_behavior metrics structures and flag unrecognized metrics."

    def validate(self, spec: ScenarioSpec, world_repo: Optional[WorldRepository] = None) -> list[ValidationIssue]:
        issues = []
        for metric_name in spec.expected_behavior.keys():
            if metric_name not in STANDARD_METRICS:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message=f"Metric '{metric_name}' is unrecognized by standard engine. Proceeding under custom telemetry model.",
                    path=f"expected_behavior.{metric_name}"
                ))
        return issues

STANDARD_EVENTS = {
    "ResourceNodeDepleted",
    "NavigationStuck",
    "ResourceTargetSelected",
    "HardLawViolationDetected",
    "ResourceProductionZero"
}

STANDARD_COGNITION = {
    "current_project",
    "active_blockers"
}

class RequiredSignalsRule(ScenarioValidationRule):
    rule_id = "SCENARIO-SIGNAL-001"
    severity = "WARNING"
    description = "Verify required signals references against standard telemetry keys."

    def validate(self, spec: ScenarioSpec, world_repo: Optional[WorldRepository] = None) -> list[ValidationIssue]:
        issues = []
        # Check metrics
        for i, m in enumerate(spec.required_signals.metrics):
            if m not in STANDARD_METRICS:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message=f"Required metric '{m}' is unrecognized.",
                    path=f"required_signals.metrics.{i}"
                ))
        # Check events
        for i, ev in enumerate(spec.required_signals.events):
            if ev not in STANDARD_EVENTS:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message=f"Required event '{ev}' is unrecognized.",
                    path=f"required_signals.events.{i}"
                ))
        # Check cognition
        for i, cog in enumerate(spec.required_signals.cognition):
            if cog not in STANDARD_COGNITION:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message=f"Required cognition key '{cog}' is unrecognized.",
                    path=f"required_signals.cognition.{i}"
                ))
        return issues

STANDARD_ANOMALIES = {
    "NavigationStuckBasic",
    "HardLawViolationDetected",
    "ResourceProductionZero"
}

class AnomalyReferencesRule(ScenarioValidationRule):
    rule_id = "SCENARIO-ANOMALY-001"
    severity = "WARNING"
    description = "Verify anomaly references against engine standard dictionaries."

    def validate(self, spec: ScenarioSpec, world_repo: Optional[WorldRepository] = None) -> list[ValidationIssue]:
        issues = []
        for i, anomaly in enumerate(spec.allowed_anomalies):
            if anomaly not in STANDARD_ANOMALIES:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message=f"Allowed anomaly '{anomaly}' is unrecognized.",
                    path=f"allowed_anomalies.{i}"
                ))
        for i, anomaly in enumerate(spec.critical_anomalies):
            if anomaly not in STANDARD_ANOMALIES:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message=f"Critical anomaly '{anomaly}' is unrecognized.",
                    path=f"critical_anomalies.{i}"
                ))
        return issues

class ScenarioValidator:
    """
    Orchestrates ScenarioValidationRule logic against loaded ScenarioSpec specifications.
    Blocks run configuration if validation errors occur.
    """
    def __init__(self, world_repo: Optional[WorldRepository] = None, rules: Optional[list[ScenarioValidationRule]] = None):
        self.world_repo = world_repo
        if rules is None:
            self.rules = [
                WorldExistenceRule(),
                ExpectedBehaviorRule(),
                RequiredSignalsRule(),
                AnomalyReferencesRule()
            ]
        else:
            self.rules = rules

    def validate(self, spec: ScenarioSpec, strict: bool = False) -> list[ValidationIssue]:
        issues = []
        for rule in self.rules:
            issues.extend(rule.validate(spec, self.world_repo))
            
        # Error / Strict validation policies
        errors = [x for x in issues if x.severity == "ERROR"]
        warnings = [x for x in issues if x.severity == "WARNING"]
        
        if errors:
            raise InvalidScenarioSpecError(f"Scenario validation failed with {len(errors)} errors: " + ", ".join(e.message for e in errors))
            
        if strict and warnings:
            raise InvalidScenarioSpecError(f"Scenario strict validation failed with {len(warnings)} warnings: " + ", ".join(w.message for w in warnings))
            
        return issues


class ExperimentValidationRule:
    """Base class for all pluggable experiment specification validation rules."""
    rule_id: str
    severity: str
    description: str

    def validate(self, spec: ExperimentSpec, scenario_repo: Optional[Any] = None) -> list[ValidationIssue]:
        raise NotImplementedError


class ScenarioExistenceRule(ExperimentValidationRule):
    rule_id = "EXPERIMENT-REF-001"
    severity = "ERROR"
    description = "Verify that the referenced scenario_id exists in the scenario repository."

    def validate(self, spec: ExperimentSpec, scenario_repo: Optional[Any] = None) -> list[ValidationIssue]:
        if scenario_repo is None:
            return []
            
        if spec.scenario_id not in scenario_repo.list_scenarios():
            return [ValidationIssue(
                rule_id=self.rule_id,
                severity=self.severity,
                message=f"Experiment references a non-existent scenario_id: '{spec.scenario_id}'",
                path="scenario_id"
            )]
        return []


class ExperimentParameterRule(ExperimentValidationRule):
    rule_id = "EXPERIMENT-PARAM-001"
    severity = "ERROR"
    description = "Verify execution constraints based on experiment type."

    def validate(self, spec: ExperimentSpec, scenario_repo: Optional[Any] = None) -> list[ValidationIssue]:
        issues = []
        
        # 1. same_seed_repeat checks
        if spec.experiment_type == "same_seed_repeat":
            if spec.run.repeat_count <= 1:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Experiment type 'same_seed_repeat' requires repeat_count to be greater than 1.",
                    path="run.repeat_count"
                ))
            if len(spec.run.seeds) != 1:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity="WARNING",
                    message="Experiment type 'same_seed_repeat' typically runs a single seed repeated. Found multiple seeds.",
                    path="run.seeds"
                ))

        # 2. baseline_comparison checks
        if spec.experiment_type == "baseline_comparison":
            if not spec.analysis.compare_baseline:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Experiment type 'baseline_comparison' requires analysis.compare_baseline to be set to True.",
                    path="analysis.compare_baseline"
                ))
            if not spec.analysis.baseline_id:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Experiment type 'baseline_comparison' requires analysis.baseline_id to be specified.",
                    path="analysis.baseline_id"
                ))

        return issues


VALID_OBSERVABILITY_MODES = {"LIGHTWEIGHT", "MINIMAL", "STANDARD", "LONG_RUN"}


class ExperimentObservabilityRule(ExperimentValidationRule):
    rule_id = "EXPERIMENT-OBS-001"
    severity = "ERROR"
    description = "Verify that the observability mode matches engine capabilities."

    def validate(self, spec: ExperimentSpec, scenario_repo: Optional[Any] = None) -> list[ValidationIssue]:
        if spec.observability.mode not in VALID_OBSERVABILITY_MODES:
            return [ValidationIssue(
                rule_id=self.rule_id,
                severity=self.severity,
                message=f"Observability mode '{spec.observability.mode}' is invalid. Must be one of: {sorted(list(VALID_OBSERVABILITY_MODES))}",
                path="observability.mode"
            )]
        return []


class ExperimentValidator:
    """
    Orchestrates ExperimentValidationRule logic against loaded ExperimentSpec specifications.
    Blocks run configuration if validation errors occur.
    """
    def __init__(self, scenario_repo: Optional[Any] = None, rules: Optional[list[ExperimentValidationRule]] = None):
        self.scenario_repo = scenario_repo
        if rules is None:
            self.rules = [
                ScenarioExistenceRule(),
                ExperimentParameterRule(),
                ExperimentObservabilityRule()
            ]
        else:
            self.rules = rules

    def validate(self, spec: ExperimentSpec, strict: bool = False) -> list[ValidationIssue]:
        issues = []
        for rule in self.rules:
            issues.extend(rule.validate(spec, self.scenario_repo))
            
        errors = [x for x in issues if x.severity == "ERROR"]
        warnings = [x for x in issues if x.severity == "WARNING"]
        
        if errors:
            raise InvalidExperimentSpecError(f"Experiment validation failed with {len(errors)} errors: " + ", ".join(e.message for e in errors))
            
        if strict and warnings:
            raise InvalidExperimentSpecError(f"Experiment strict validation failed with {len(warnings)} warnings: " + ", ".join(w.message for w in warnings))
            
        return issues


class MutationValidationRule:
    """Base class for all pluggable mutation specification validation rules."""
    rule_id: str
    severity: str  # "ERROR", "WARNING", "INFO"
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
    """
    Orchestrates MutationValidationRule checks against a loaded MutationSpec.
    Ensures structural and logical safety prior to mutation run execution.
    """
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


