# Compliance IDs: SCENARIO-004, SCENARIO-005, SCENARIO-006
from __future__ import annotations

from typing import Optional, Any
from src.worldbuilding.validator import ValidationIssue
from src.worldbuilding.repository import WorldRepository
from src.lab.schema import ScenarioSpec, InvalidScenarioSpecError

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
