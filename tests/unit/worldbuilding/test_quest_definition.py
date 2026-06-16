"""
Unit tests for QuestDefinition schema and WorldSpec.quest_definitions field.
TCK-20260614-WORLDMOD-QUEST-SCHEMA
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.worldbuilding.schema import QuestDefinition, WorldSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_world_spec_dict(**overrides) -> dict:
    """Return the minimum valid WorldSpec dict for testing."""
    base = {
        "schema_version": "worldspec.v1",
        "world_id": "test_world",
        "name": "Test World",
        "topology": {
            "width": 10,
            "height": 10,
            "coordinate_system": "grid",
        },
    }
    base.update(overrides)
    return base


def _minimal_quest_def_dict(**overrides) -> dict:
    """Return the minimum valid QuestDefinition dict for testing."""
    base = {"id": "q_test_hunt", "type": "hunt"}
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# QuestDefinition — valid construction
# ---------------------------------------------------------------------------

class TestQuestDefinitionValid:
    def test_minimal_construction_succeeds(self):
        q = QuestDefinition(id="q_escort_test", type="escort")
        assert q.id == "q_escort_test"
        assert q.type == "escort"

    def test_all_valid_types_accepted(self):
        valid_types = ["escort", "hunt", "fetch", "explore", "defend", "investigate"]
        for qt in valid_types:
            q = QuestDefinition(id=f"q_{qt}", type=qt)
            assert q.type == qt, f"Expected type '{qt}' to be accepted"

    def test_defaults_are_correct(self):
        q = QuestDefinition(id="q_defaults", type="explore")
        assert q.required_participant_tags == []
        assert q.required_location_tags == []
        assert q.reward_budget == 100
        assert q.procedural_hints == {}
        assert q.tags == []
        assert q.source_module is None

    def test_source_module_defaults_to_none(self):
        q = QuestDefinition(id="q_src", type="fetch")
        assert q.source_module is None

    def test_full_construction_with_all_fields(self):
        q = QuestDefinition(
            id="q_full",
            type="defend",
            required_participant_tags=["hostile", "humanoid"],
            required_location_tags=["wilderness"],
            reward_budget=250,
            procedural_hints={"difficulty": 3, "escalation": True},
            tags=["hard", "outdoor"],
            source_module="mod_bandits",
        )
        assert q.id == "q_full"
        assert q.type == "defend"
        assert q.required_participant_tags == ["hostile", "humanoid"]
        assert q.required_location_tags == ["wilderness"]
        assert q.reward_budget == 250
        assert q.procedural_hints == {"difficulty": 3, "escalation": True}
        assert q.tags == ["hard", "outdoor"]
        assert q.source_module == "mod_bandits"

    def test_reward_budget_zero_is_valid(self):
        q = QuestDefinition(id="q_zero_budget", type="investigate", reward_budget=0)
        assert q.reward_budget == 0


# ---------------------------------------------------------------------------
# QuestDefinition — invalid construction
# ---------------------------------------------------------------------------

class TestQuestDefinitionInvalid:
    def test_invalid_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            QuestDefinition(id="q_bad_type", type="raid")

    def test_empty_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            QuestDefinition(id="q_empty_type", type="")

    def test_missing_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            QuestDefinition(type="hunt")  # type: ignore[call-arg]

    def test_missing_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            QuestDefinition(id="q_no_type")  # type: ignore[call-arg]

    def test_negative_reward_budget_raises_validation_error(self):
        with pytest.raises(ValidationError):
            QuestDefinition(id="q_neg_budget", type="hunt", reward_budget=-1)


# ---------------------------------------------------------------------------
# QuestDefinition — immutability (frozen=True)
# ---------------------------------------------------------------------------

class TestQuestDefinitionFrozen:
    def test_assignment_raises_error(self):
        q = QuestDefinition(id="q_frozen", type="fetch")
        with pytest.raises((ValidationError, TypeError)):
            q.type = "hunt"  # type: ignore[misc]

    def test_field_mutation_raises_error(self):
        q = QuestDefinition(id="q_frozen2", type="explore")
        with pytest.raises((ValidationError, TypeError)):
            q.reward_budget = 999  # type: ignore[misc]


# ---------------------------------------------------------------------------
# WorldSpec — quest_definitions field
# ---------------------------------------------------------------------------

class TestWorldSpecQuestDefinitions:
    def test_world_spec_defaults_quest_definitions_to_empty(self):
        spec = WorldSpec.model_validate(_minimal_world_spec_dict())
        assert spec.quest_definitions == []

    def test_world_spec_with_single_quest_definition(self):
        data = _minimal_world_spec_dict(
            quest_definitions=[_minimal_quest_def_dict()]
        )
        spec = WorldSpec.model_validate(data)
        assert len(spec.quest_definitions) == 1
        assert spec.quest_definitions[0].id == "q_test_hunt"
        assert spec.quest_definitions[0].type == "hunt"

    def test_world_spec_with_multiple_quest_definitions(self):
        data = _minimal_world_spec_dict(
            quest_definitions=[
                {"id": "q_escort_1", "type": "escort"},
                {"id": "q_fetch_1", "type": "fetch"},
                {"id": "q_investigate_1", "type": "investigate"},
            ]
        )
        spec = WorldSpec.model_validate(data)
        assert len(spec.quest_definitions) == 3
        ids = [q.id for q in spec.quest_definitions]
        assert "q_escort_1" in ids
        assert "q_fetch_1" in ids
        assert "q_investigate_1" in ids

    def test_world_spec_quest_definitions_are_typed(self):
        data = _minimal_world_spec_dict(
            quest_definitions=[{"id": "q_typed", "type": "defend", "reward_budget": 200}]
        )
        spec = WorldSpec.model_validate(data)
        q = spec.quest_definitions[0]
        assert isinstance(q, QuestDefinition)
        assert q.reward_budget == 200

    def test_world_spec_invalid_quest_type_raises_validation_error(self):
        data = _minimal_world_spec_dict(
            quest_definitions=[{"id": "q_bad", "type": "invalid_type"}]
        )
        with pytest.raises(ValidationError):
            WorldSpec.model_validate(data)

    def test_world_spec_model_dump_contains_quest_definitions(self):
        data = _minimal_world_spec_dict(
            quest_definitions=[{"id": "q_dump", "type": "explore"}]
        )
        spec = WorldSpec.model_validate(data)
        dumped = spec.model_dump()
        assert "quest_definitions" in dumped
        assert len(dumped["quest_definitions"]) == 1
        assert dumped["quest_definitions"][0]["id"] == "q_dump"

    def test_world_spec_round_trip_serialization(self):
        data = _minimal_world_spec_dict(
            quest_definitions=[
                {
                    "id": "q_round_trip",
                    "type": "hunt",
                    "reward_budget": 150,
                    "tags": ["forest", "combat"],
                    "source_module": "mod_forest",
                }
            ]
        )
        spec = WorldSpec.model_validate(data)
        dumped = spec.model_dump()
        spec2 = WorldSpec.model_validate(dumped)
        assert spec2.quest_definitions[0].id == "q_round_trip"
        assert spec2.quest_definitions[0].reward_budget == 150
        assert spec2.quest_definitions[0].tags == ["forest", "combat"]
        assert spec2.quest_definitions[0].source_module == "mod_forest"


# ---------------------------------------------------------------------------
# Migration alias: old `quests:` key → `quest_definitions`
# ---------------------------------------------------------------------------

class TestQuestsMigrationAlias:
    def test_old_quests_key_empty_list_migrates(self):
        """Simulates data/worlds/sandbox_world/world.yaml with `quests: []`."""
        data = _minimal_world_spec_dict(quests=[])
        spec = WorldSpec.model_validate(data)
        assert spec.quest_definitions == []

    def test_old_quests_key_with_entries_migrates(self):
        data = _minimal_world_spec_dict(
            quests=[{"id": "q_legacy", "type": "escort"}]
        )
        spec = WorldSpec.model_validate(data)
        assert len(spec.quest_definitions) == 1
        assert spec.quest_definitions[0].id == "q_legacy"
        assert spec.quest_definitions[0].type == "escort"

    def test_quest_definitions_key_takes_precedence_when_both_present(self):
        """If both keys present, quest_definitions wins (no double migration)."""
        data = _minimal_world_spec_dict(
            quests=[{"id": "q_old", "type": "hunt"}],
            quest_definitions=[{"id": "q_new", "type": "explore"}],
        )
        spec = WorldSpec.model_validate(data)
        # migration only runs when quest_definitions is absent
        assert len(spec.quest_definitions) == 1
        assert spec.quest_definitions[0].id == "q_new"

    def test_old_quests_key_invalid_type_still_raises(self):
        data = _minimal_world_spec_dict(
            quests=[{"id": "q_bad_legacy", "type": "RAID"}]
        )
        with pytest.raises(ValidationError):
            WorldSpec.model_validate(data)
