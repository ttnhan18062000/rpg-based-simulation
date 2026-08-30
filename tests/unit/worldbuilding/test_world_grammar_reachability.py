"""Unit tests for WORLD-REACH-001 (src/worldbuilding/validator.py's
ParticipantReachabilityRule) and its supporting pure functions in
src/worldbuilding/reachability.py.
"""
from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.worldbuilding.reachability import is_reachable, resolve_population_tags
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.validator import (
    ParticipantReachabilityRule,
    ValidationContext,
    WorldValidator,
)


@pytest.fixture(scope="module")
def catalog_repo() -> CatalogRepository:
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def create_base_spec_dict() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "reach_test_world",
        "name": "Reach Test World",
        "topology": {"width": 100, "height": 100, "coordinate_system": "grid"},
        "regions": [
            {"id": "village", "type": "settlement", "bounds": [0, 0, 30, 30]}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"}
        ],
        "entities": [
            {
                "id": "workers",
                "count": 10,
                "role": "worker",
                "faction": "villagers",
                "spawn_region": "village",
                "archetype_id": "village_worker",
            }
        ],
        "resources": [
            {"id": "wood_node", "resource_type": "wood", "count": 10, "region": "village"}
        ],
        "quest_definitions": [],
    }


def test_reachability_rule_flags_unmatched_participant_tags(catalog_repo):
    data = create_base_spec_dict()
    data["quest_definitions"] = [
        {
            "id": "q_unreachable",
            "type": "hunt",
            "required_participant_tags": ["undead"],
            "source_module": "reach_test_module",
        }
    ]
    spec = WorldSpec.model_validate(data)
    rule = ParticipantReachabilityRule(catalog_repo=catalog_repo)

    issues = rule.validate(spec, context=ValidationContext.WORLD)

    assert len(issues) == 1
    issue = issues[0]
    assert issue.rule_id == "WORLD-REACH-001"
    assert issue.severity == "WARNING"
    assert issue.source_entity == "q_unreachable"
    assert issue.source_file == "reach_test_module"


def test_reachability_rule_passes_when_tags_satisfiable(catalog_repo):
    data = create_base_spec_dict()
    data["quest_definitions"] = [
        {
            "id": "q_reachable",
            "type": "fetch",
            "required_participant_tags": ["humanoid"],
            "source_module": "reach_test_module",
        }
    ]
    spec = WorldSpec.model_validate(data)
    rule = ParticipantReachabilityRule(catalog_repo=catalog_repo)

    issues = rule.validate(spec, context=ValidationContext.WORLD)

    assert issues == []


def test_reachability_rule_severity_elevation_under_gated_profile(catalog_repo):
    data = create_base_spec_dict()
    data["quest_definitions"] = [
        {
            "id": "q_unreachable",
            "type": "hunt",
            "required_participant_tags": ["undead"],
            "source_module": "reach_test_module",
        }
    ]
    spec = WorldSpec.model_validate(data)
    rule = ParticipantReachabilityRule(catalog_repo=catalog_repo)

    default_issues = rule.validate(spec, context=ValidationContext.WORLD)
    assert default_issues[0].severity == "WARNING"

    rule.severity_overrides = {ValidationContext.WORLD: "ERROR"}
    elevated_issues = rule.validate(spec, context=ValidationContext.WORLD)
    assert elevated_issues[0].severity == "ERROR"


def test_reachability_rule_not_applicable_at_module_context():
    rule = ParticipantReachabilityRule()
    assert rule.is_applicable(ValidationContext.MODULE) is False
    assert rule.is_applicable(ValidationContext.WORLD) is True


def test_reachability_rule_does_not_mutate_spec(catalog_repo):
    data = create_base_spec_dict()
    data["quest_definitions"] = [
        {
            "id": "q_unreachable",
            "type": "hunt",
            "required_participant_tags": ["undead"],
            "source_module": "reach_test_module",
        }
    ]
    spec = WorldSpec.model_validate(data)
    orig_quest_count = len(spec.quest_definitions)
    orig_entity_count = len(spec.entities)

    rule = ParticipantReachabilityRule(catalog_repo=catalog_repo)
    rule.validate(spec, context=ValidationContext.WORLD)

    assert len(spec.quest_definitions) == orig_quest_count
    assert len(spec.entities) == orig_entity_count


def test_reachability_rule_handles_missing_archetype_id_gracefully(catalog_repo):
    data = create_base_spec_dict()
    data["entities"][0]["archetype_id"] = None
    data["quest_definitions"] = [
        {
            "id": "q_no_archetype",
            "type": "fetch",
            "required_participant_tags": ["humanoid"],
            "source_module": "reach_test_module",
        }
    ]
    spec = WorldSpec.model_validate(data)
    assert spec.entities[0].archetype_id is None

    rule = ParticipantReachabilityRule(catalog_repo=catalog_repo)
    issues = rule.validate(spec, context=ValidationContext.WORLD)

    # archetype_id=None contributes no tags -- required humanoid tag is
    # unreachable, not silently skipped.
    assert len(issues) == 1
    assert issues[0].source_entity == "q_no_archetype"

    tags = resolve_population_tags(spec.entities[0], catalog_repo)
    assert tags == set()


def test_reachability_rule_handles_no_catalog_available():
    data = create_base_spec_dict()
    data["quest_definitions"] = [
        {
            "id": "q_no_catalog",
            "type": "hunt",
            "required_participant_tags": ["undead"],
            "source_module": "reach_test_module",
        }
    ]
    spec = WorldSpec.model_validate(data)

    validator = WorldValidator()
    issues = validator.validate(spec, context=ValidationContext.WORLD)

    reach_issues = [i for i in issues if i.rule_id == "WORLD-REACH-001"]
    assert reach_issues == []


def test_is_reachable_pure_function():
    assert is_reachable([], None) is True
    assert is_reachable([], {"humanoid"}) is True
    assert is_reachable(["humanoid"], None) is True
    assert is_reachable(["humanoid"], {"humanoid", "undead"}) is True
    assert is_reachable(["humanoid", "beast"], {"humanoid"}) is False
    assert is_reachable(["humanoid"], set()) is False


def test_default_rule_set_includes_all_expected_rule_ids():
    validator = WorldValidator()
    rule_ids = {rule.rule_id for rule in validator.rules}
    expected = {
        "WORLD-REF-001",
        "WORLD-REF-002",
        "WORLD-REF-003",
        "WORLD-REF-004",
        "WORLD-TOPO-001",
        "WORLD-WARN-001",
        "WORLD-WARN-002",
        "WORLD-BUDGET-GP",
        "WORLD-REACH-001",
    }
    assert expected.issubset(rule_ids)
