# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
from __future__ import annotations

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from src.worldbuilding.schema import WorldSpec, load_world_spec_from_yaml, InvalidWorldSpecError

class ValidationContext(str, Enum):
    """Scoped contexts mapping different validator evaluation scopes."""
    CATALOG = "CATALOG"
    MODULE = "MODULE"
    COMPOSITION = "COMPOSITION"
    ASSEMBLY = "ASSEMBLY"
    GENERATED_WORLD = "GENERATED_WORLD"
    WORLD = "WORLD"
    COMPILE = "COMPILE"
    EXPERIMENT = "EXPERIMENT"

class ValidationIssue(BaseModel):
    """Represents a diagnostic result of a validation check."""
    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: str  # "ERROR", "WARNING", "INFO"
    message: str
    path: Optional[str] = None

class WorldValidationRule:
    """Base class for all pluggable world specification validation rules."""
    rule_id: str
    severity: str
    description: str
    applicable_contexts: set[ValidationContext] = {
        ValidationContext.WORLD,
        ValidationContext.ASSEMBLY,
        ValidationContext.GENERATED_WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT
    }
    severity_overrides: dict[ValidationContext, str] = {}

    def is_applicable(self, context: ValidationContext) -> bool:
        """Determines if the rule should run for a given validation context."""
        return context in self.applicable_contexts

    def get_severity(self, context: ValidationContext) -> str:
        """Resolves the context-sensitive severity, falling back to rule default."""
        return self.severity_overrides.get(context, self.severity)

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        raise NotImplementedError

class FactionExistenceRule(WorldValidationRule):
    rule_id = "WORLD-REF-001"
    severity = "ERROR"
    description = "Verify that all entities (populations) affiliate with an existing faction."
    applicable_contexts = {
        ValidationContext.MODULE,
        ValidationContext.COMPOSITION,
        ValidationContext.ASSEMBLY,
        ValidationContext.GENERATED_WORLD,
        ValidationContext.WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT
    }

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        faction_ids = {f.id for f in spec.factions}
        sev = self.get_severity(context)
        for i, ent in enumerate(spec.entities):
            if ent.faction not in faction_ids:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"Entity population '{ent.id}' affiliates with non-existent faction '{ent.faction}'",
                    path=f"entities.{i}.faction"
                ))
        return issues

class SpawnRegionExistenceRule(WorldValidationRule):
    rule_id = "WORLD-REF-002"
    severity = "ERROR"
    description = "Verify that all entities spawn inside a defined region."
    applicable_contexts = {
        ValidationContext.ASSEMBLY,
        ValidationContext.GENERATED_WORLD,
        ValidationContext.WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT
    }

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        region_ids = {r.id for r in spec.regions}
        sev = self.get_severity(context)
        for i, ent in enumerate(spec.entities):
            if ent.spawn_region not in region_ids:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"Entity population '{ent.id}' spawn region '{ent.spawn_region}' does not exist",
                    path=f"entities.{i}.spawn_region"
                ))
        return issues

class ResourceRegionExistenceRule(WorldValidationRule):
    rule_id = "WORLD-REF-003"
    severity = "ERROR"
    description = "Verify that all resource nodes reside in a defined region."
    applicable_contexts = {
        ValidationContext.ASSEMBLY,
        ValidationContext.GENERATED_WORLD,
        ValidationContext.WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT
    }

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        region_ids = {r.id for r in spec.regions}
        sev = self.get_severity(context)
        for i, res in enumerate(spec.resources):
            if res.region not in region_ids:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"Resource node '{res.id}' region '{res.region}' does not exist",
                    path=f"resources.{i}.region"
                ))
        return issues

class BuildingRegionExistenceRule(WorldValidationRule):
    rule_id = "WORLD-REF-004"
    severity = "ERROR"
    description = "Verify that all buildings reside in a defined region."
    applicable_contexts = {
        ValidationContext.ASSEMBLY,
        ValidationContext.GENERATED_WORLD,
        ValidationContext.WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT
    }

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        region_ids = {r.id for r in spec.regions}
        sev = self.get_severity(context)
        for i, bld in enumerate(spec.buildings):
            if bld.region not in region_ids:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"Building '{bld.id}' region '{bld.region}' does not exist",
                    path=f"buildings.{i}.region"
                ))
        return issues

class RegionBoundsWithinTopologyRule(WorldValidationRule):
    rule_id = "WORLD-TOPO-001"
    severity = "ERROR"
    description = "Verify that all region boundaries reside completely inside the topology coordinates."
    applicable_contexts = {
        ValidationContext.WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT
    }

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        w = spec.topology.width
        h = spec.topology.height
        sev = self.get_severity(context)
        for i, reg in enumerate(spec.regions):
            min_x, min_y, max_x, max_y = reg.bounds
            if min_x < 0 or max_x >= w or min_y < 0 or max_y >= h:
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"Region '{reg.id}' bounds {reg.bounds} exceed topology dimensions {w}x{h}",
                    path=f"regions.{i}.bounds"
                ))
        return issues

class NoResourcesWarningRule(WorldValidationRule):
    rule_id = "WORLD-WARN-001"
    severity = "WARNING"
    description = "Warning check flagging if a world defines zero resource nodes."

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        if not spec.resources:
            sev = self.get_severity(context)
            return [ValidationIssue(
                rule_id=self.rule_id,
                severity=sev,
                message="World spec defines zero resource nodes.",
                path="resources"
            )]
        return []

class HighEntityDensityWarningRule(WorldValidationRule):
    rule_id = "WORLD-WARN-002"
    severity = "WARNING"
    description = "Warning check flagging if the combined count of entities exceeds 50% of map area."

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        total_pop = sum(e.count for e in spec.entities)
        map_area = spec.topology.width * spec.topology.height
        sev = self.get_severity(context)
        if map_area > 0 and total_pop > (map_area * 0.5):
            return [ValidationIssue(
                rule_id=self.rule_id,
                severity=sev,
                message=f"High entity spawn density: total population count ({total_pop}) exceeds 50% of map tile area ({map_area})",
                path="entities"
            )]
        return []

BUDGET_PROFILES = {
    "local_dev": {
        "max_entities": 1000,
        "max_regions": 50,
        "max_resource_nodes": 500,
        "max_buildings": 100,
        "max_expected_artifact_mb": 500.0,
    },
    "ci": {
        "max_entities": 500,
        "max_regions": 20,
        "max_resource_nodes": 100,
        "max_buildings": 20,
        "max_expected_artifact_mb": 100.0,
    },
    "long_run_lab": {
        "max_entities": 10000,
        "max_regions": 200,
        "max_resource_nodes": 2000,
        "max_buildings": 500,
        "max_expected_artifact_mb": 2000.0,
    }
}

class BudgetGuardrailRule(WorldValidationRule):
    rule_id = "WORLD-BUDGET-GP"
    severity = "ERROR"
    description = "Verify that world dimensions, entities, regions, resources, buildings, and estimated artifact sizes fit the profile budgets."

    def __init__(self, profile: str = "local_dev"):
        super().__init__()
        self.profile = profile

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        profile_limits = BUDGET_PROFILES.get(self.profile, BUDGET_PROFILES["local_dev"])
        sev = self.get_severity(context)

        def get_limit(field_name: str) -> Any:
            if spec.budgets is not None:
                val = getattr(spec.budgets, field_name, None)
                if val is not None:
                    return val
            return profile_limits.get(field_name)

        # 1. Entity population count check
        max_entities = get_limit("max_entities")
        total_entities = sum(e.count for e in spec.entities)
        if max_entities is not None and total_entities > max_entities:
            issues.append(ValidationIssue(
                rule_id="WORLD-BUDGET-001",
                severity=sev,
                message=f"Total entities count ({total_entities}) exceeds maximum allowed budget ({max_entities}) under '{self.profile}' profile.",
                path="entities"
            ))

        # 2. Regions count check
        max_regions = get_limit("max_regions")
        total_regions = len(spec.regions)
        if max_regions is not None and total_regions > max_regions:
            issues.append(ValidationIssue(
                rule_id="WORLD-BUDGET-002",
                severity=sev,
                message=f"Total regions count ({total_regions}) exceeds maximum allowed budget ({max_regions}) under '{self.profile}' profile.",
                path="regions"
            ))

        # 3. Resource nodes count check
        max_resources = get_limit("max_resource_nodes")
        total_resources = len(spec.resources)
        if max_resources is not None and total_resources > max_resources:
            issues.append(ValidationIssue(
                rule_id="WORLD-BUDGET-003",
                severity=self.severity_overrides.get(context, "WARNING"),
                message=f"Total resource nodes count ({total_resources}) exceeds maximum allowed budget ({max_resources}) under '{self.profile}' profile.",
                path="resources"
            ))

        # 4. Buildings count check
        max_buildings = get_limit("max_buildings")
        total_buildings = len(spec.buildings)
        if max_buildings is not None and total_buildings > max_buildings:
            issues.append(ValidationIssue(
                rule_id="WORLD-BUDGET-004",
                severity=self.severity_overrides.get(context, "WARNING"),
                message=f"Total buildings count ({total_buildings}) exceeds maximum allowed budget ({max_buildings}) under '{self.profile}' profile.",
                path="buildings"
            ))

        # 5. World Area topology check (WARNING if area > 1,000,000)
        map_area = spec.topology.width * spec.topology.height
        if map_area > 1000000:
            issues.append(ValidationIssue(
                rule_id="WORLD-BUDGET-005",
                severity=self.severity_overrides.get(context, "WARNING"),
                message=f"World topology area ({map_area} tiles) is very large and may cause performance slowdowns.",
                path="topology"
            ))

        # 6. Estimated artifact size check
        max_expected_artifact_mb = get_limit("max_expected_artifact_mb")
        expected_ticks = 1000
        expected_size_mb = (total_entities * expected_ticks * 0.0001) + (total_resources * expected_ticks * 0.00005)
        if max_expected_artifact_mb is not None and expected_size_mb > max_expected_artifact_mb:
            issues.append(ValidationIssue(
                rule_id="WORLD-BUDGET-006",
                severity=self.severity_overrides.get(context, "WARNING"),
                message=f"Estimated artifact size ({expected_size_mb:.2f} MB) exceeds maximum allowed budget ({max_expected_artifact_mb} MB) under '{self.profile}' profile.",
                path="budgets.max_expected_artifact_mb"
            ))

        return issues

class WorldValidator:
    """
    Orchestrates validation rules against a loaded WorldSpec, verifying integrity,
    categorizing issues by severity, and blocking compilation when failures occur.
    """

    def __init__(self, rules: list[WorldValidationRule] = None, profile: str = "local_dev"):
        self.profile = profile
        if rules is None:
            self.rules = [
                FactionExistenceRule(),
                SpawnRegionExistenceRule(),
                ResourceRegionExistenceRule(),
                BuildingRegionExistenceRule(),
                RegionBoundsWithinTopologyRule(),
                NoResourcesWarningRule(),
                HighEntityDensityWarningRule(),
                BudgetGuardrailRule(profile=profile)
            ]
        else:
            self.rules = rules

    def validate(self, spec: WorldSpec, raw_data: dict = None, strict: bool = False, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        """
        Runs all registered rules against the spec and returns a sorted list of validation issues.
        Raises InvalidWorldSpecError on ERROR level violations (or on WARNING if strict is enabled).
        """
        issues = []
        
        # 1. Pluggable spec evaluation
        for rule in self.rules:
            if rule.is_applicable(context):
                issues.extend(rule.validate(spec, context=context))

        # 2. Check for unknown/unexpected top-level sections
        if raw_data is not None:
            known_fields = set(WorldSpec.model_fields.keys())
            for key in raw_data.keys():
                if key not in known_fields:
                    issues.append(ValidationIssue(
                        rule_id="WORLD-UNEXPECTED-SECTION",
                        severity="WARNING",
                        message=f"Unexpected top-level section found in YAML: '{key}'",
                        path=key
                    ))

        # 3. Handle strict mode elevation & failure enforcement
        errors = [issue for issue in issues if issue.severity == "ERROR"]
        warnings = [issue for issue in issues if issue.severity == "WARNING"]

        if errors:
            msgs = "; ".join(f"[{err.rule_id}] {err.message}" for err in errors)
            raise InvalidWorldSpecError(f"World validation failed: {msgs}")
        
        if strict and warnings:
            msgs = "; ".join(f"[{warn.rule_id}] {warn.message}" for warn in warnings)
            raise InvalidWorldSpecError(f"World validation failed under strict mode: {msgs}")

        return sorted(issues, key=lambda x: (x.severity, x.rule_id, x.path or ""))
