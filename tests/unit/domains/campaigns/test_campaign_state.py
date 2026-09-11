"""
tests/unit/domains/campaigns/test_campaign_state.py
───────────────────────────────────────────────────────────────────────────────
Unit tests for CampaignState data model (TCK-20260619-E32B-CAMPAIGN-STATE).

Coverage: construction, immutability, mutability, JSON round-trip, JSON safety,
dead/destroyed record representability, AST import guard.
"""

from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from src.domains.campaigns.state import (
    CampaignState,
    EntityCarryForward,
    EpisodeSummary,
    FactionCarryForward,
    NarrativeLedgerEntry,
    WorldTimelineEntry,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

EQUIPMENT_FULL = {
    "slots": {"MAIN_HAND": "sword_iron", "HEAD": "iron_helm"},
    "durability": {"MAIN_HAND": 0.9, "HEAD": 0.75},
}


def _make_entity(entity_id: int = 1, alive: bool = True) -> EntityCarryForward:
    return EntityCarryForward(
        entity_id=entity_id,
        level=5,
        xp=1200,
        equipment=EQUIPMENT_FULL,
        reputation=1.3,
        alive=alive,
    )


def _make_faction(faction_id: str = "faction_1", alive: bool = True) -> FactionCarryForward:
    return FactionCarryForward(faction_id=faction_id, alive=alive, tension=0.4)


def _make_campaign_state() -> CampaignState:
    entity = _make_entity(entity_id=42)
    dead_entity = _make_entity(entity_id=99, alive=False)
    faction = _make_faction("faction_1", alive=True)
    dead_faction = _make_faction("faction_2", alive=False)
    episode = EpisodeSummary(episode_index=0, completed_tick=500)
    timeline_entry = WorldTimelineEntry(tick=250, episode_index=0, description="calamity:drought")
    ledger_entry = NarrativeLedgerEntry(
        episode=0, tick=100, event_type="entity_death",
        subject_id="entity_42", payload={"damage": 50.0}, significance=0.5,
        entry_id="0:100:entity_death:entity_42",
    )

    return CampaignState(
        campaign_id="campaign-abc",
        episode_index=1,
        episode_history=[episode],
        persistent_entities={42: entity, 99: dead_entity},
        persistent_factions={"faction_1": faction, "faction_2": dead_faction},
        world_timeline=[timeline_entry],
        narrative_ledger=[ledger_entry],
    )


# ---------------------------------------------------------------------------
# AC-1: EntityCarryForward constructs with valid fields
# ---------------------------------------------------------------------------

def test_entity_carry_forward_fields():
    entity = _make_entity()
    assert entity.entity_id == 1
    assert entity.level == 5
    assert entity.xp == 1200
    assert entity.equipment == EQUIPMENT_FULL
    assert entity.reputation == pytest.approx(1.3)
    assert entity.alive is True


# ---------------------------------------------------------------------------
# AC-2: EntityCarryForward is immutable (frozen)
# ---------------------------------------------------------------------------

def test_entity_carry_forward_is_frozen():
    entity = _make_entity()
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        entity.level = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC-3: EntityCarryForward round-trips through to_dict()/from_dict()
# ---------------------------------------------------------------------------

def test_entity_carry_forward_round_trip():
    entity = _make_entity()
    restored = EntityCarryForward.from_dict(entity.to_dict())
    assert restored == entity


# ---------------------------------------------------------------------------
# AC-4: Dead entity (alive=False) representable and survives round-trip
# ---------------------------------------------------------------------------

def test_entity_carry_forward_dead():
    dead = _make_entity(alive=False)
    assert dead.alive is False
    restored = EntityCarryForward.from_dict(dead.to_dict())
    assert restored.alive is False
    assert restored == dead


# ---------------------------------------------------------------------------
# TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION:
# EntityCarryForward.last_position round-trips, including the None case for
# pre-existing carry-forward records serialized before this field existed.
# ---------------------------------------------------------------------------

def test_entity_carry_forward_last_position_defaults_to_none():
    entity = _make_entity()
    assert entity.last_position is None


def test_entity_carry_forward_last_position_round_trip():
    entity = dataclasses.replace(_make_entity(), last_position=(12.0, -3.0))
    restored = EntityCarryForward.from_dict(entity.to_dict())
    assert restored.last_position == (12.0, -3.0)
    assert restored == entity


def test_entity_carry_forward_last_position_none_round_trip():
    entity = _make_entity()
    d = entity.to_dict()
    assert d["last_position"] is None
    restored = EntityCarryForward.from_dict(d)
    assert restored.last_position is None


def test_entity_carry_forward_from_dict_missing_last_position_key():
    """Pre-existing serialized records from before this field existed have no
    "last_position" key at all -- from_dict() must not KeyError on them."""
    entity = _make_entity()
    d = entity.to_dict()
    del d["last_position"]
    restored = EntityCarryForward.from_dict(d)
    assert restored.last_position is None


# ---------------------------------------------------------------------------
# TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION:
# EntityCarryForward.kind/role/faction/properties/traits/personality round-trip,
# including the missing-key case for pre-existing records.
# ---------------------------------------------------------------------------

def test_entity_carry_forward_identity_fields_default():
    entity = _make_entity()
    assert entity.kind == ""
    assert entity.role == 0
    assert entity.faction == 0
    assert entity.properties == {}
    assert entity.traits == ()
    assert entity.personality == {}


def test_entity_carry_forward_identity_fields_round_trip():
    entity = dataclasses.replace(
        _make_entity(),
        kind="goblin",
        role=2,
        faction=3,
        properties={"archetype_id": "goblin_raider", "faction_id": "monster_horde"},
        traits=("brave", "cunning"),
        personality={"greed": 0.4, "bravery": 0.7, "sociability": 0.1, "industry": 0.2},
    )
    restored = EntityCarryForward.from_dict(entity.to_dict())
    assert restored.kind == "goblin"
    assert restored.role == 2
    assert restored.faction == 3
    assert restored.properties == {"archetype_id": "goblin_raider", "faction_id": "monster_horde"}
    assert restored.traits == ("brave", "cunning")
    assert restored.personality == {"greed": 0.4, "bravery": 0.7, "sociability": 0.1, "industry": 0.2}
    assert restored == entity


def test_entity_carry_forward_traits_serialized_sorted_for_determinism():
    entity = dataclasses.replace(_make_entity(), traits=("zebra", "alpha", "mid"))
    d = entity.to_dict()
    assert d["traits"] == ["alpha", "mid", "zebra"]


def test_entity_carry_forward_from_dict_missing_identity_keys():
    """Pre-existing serialized records from before these fields existed have none of these
    keys at all -- from_dict() must not KeyError, and must fall back to the same defaults a
    bare EntityCarryForward construction would use."""
    entity = _make_entity()
    d = entity.to_dict()
    for key in ("kind", "role", "faction", "properties", "traits", "personality"):
        del d[key]
    restored = EntityCarryForward.from_dict(d)
    assert restored.kind == ""
    assert restored.role == 0
    assert restored.faction == 0
    assert restored.properties == {}
    assert restored.traits == ()
    assert restored.personality == {}


# ---------------------------------------------------------------------------
# AC-5: FactionCarryForward constructs and round-trips
# ---------------------------------------------------------------------------

def test_faction_carry_forward_round_trip():
    faction = _make_faction()
    restored = FactionCarryForward.from_dict(faction.to_dict())
    assert restored == faction


# ---------------------------------------------------------------------------
# AC-6: Destroyed faction (alive=False) representable
# ---------------------------------------------------------------------------

def test_faction_carry_forward_destroyed():
    dead_faction = _make_faction(alive=False)
    assert dead_faction.alive is False
    restored = FactionCarryForward.from_dict(dead_faction.to_dict())
    assert restored.alive is False
    assert restored == dead_faction


# ---------------------------------------------------------------------------
# AC-7: FactionCarryForward is immutable (frozen)
# ---------------------------------------------------------------------------

def test_faction_carry_forward_is_frozen():
    faction = _make_faction()
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        faction.alive = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC-8: EpisodeSummary constructs and round-trips
# ---------------------------------------------------------------------------

def test_episode_summary_round_trip():
    ep = EpisodeSummary(episode_index=2, completed_tick=1000)
    restored = EpisodeSummary.from_dict(ep.to_dict())
    assert restored == ep


# ---------------------------------------------------------------------------
# AC-9: WorldTimelineEntry constructs and round-trips
# ---------------------------------------------------------------------------

def test_world_timeline_entry_round_trip():
    entry = WorldTimelineEntry(tick=300, episode_index=1, description="calamity:flood")
    restored = WorldTimelineEntry.from_dict(entry.to_dict())
    assert restored == entry


# ---------------------------------------------------------------------------
# AC-10: NarrativeLedgerEntry constructs and round-trips
# ---------------------------------------------------------------------------

def test_narrative_ledger_entry_round_trip():
    entry = NarrativeLedgerEntry(
        episode=1,
        tick=50,
        event_type="quest_completed",
        subject_id="quest_main_01",
        payload={"xp_reward": 200.0},
        significance=0.7,
        entry_id="1:50:quest_completed:quest_main_01",
    )
    restored = NarrativeLedgerEntry.from_dict(entry.to_dict())
    assert restored == entry
    # Verify all fields survive round-trip
    assert restored.episode == 1
    assert restored.tick == 50
    assert restored.event_type == "quest_completed"
    assert restored.subject_id == "quest_main_01"
    assert restored.payload == {"xp_reward": 200.0}
    assert restored.significance == pytest.approx(0.7)
    assert restored.entry_id == "1:50:quest_completed:quest_main_01"


# ---------------------------------------------------------------------------
# AC-11: CampaignState constructs with all sub-records and round-trips
# ---------------------------------------------------------------------------

def test_campaign_state_constructs():
    cs = _make_campaign_state()
    assert cs.campaign_id == "campaign-abc"
    assert cs.episode_index == 1
    assert len(cs.episode_history) == 1
    assert len(cs.persistent_entities) == 2
    assert len(cs.persistent_factions) == 2
    assert len(cs.world_timeline) == 1
    assert len(cs.narrative_ledger) == 1


def test_campaign_state_json_round_trip():
    cs = _make_campaign_state()
    d = cs.to_dict()
    restored = CampaignState.from_dict(d)

    assert restored.campaign_id == cs.campaign_id
    assert restored.episode_index == cs.episode_index
    assert restored.episode_history == cs.episode_history
    assert restored.persistent_entities == cs.persistent_entities
    assert restored.persistent_factions == cs.persistent_factions
    assert restored.world_timeline == cs.world_timeline
    assert restored.narrative_ledger == cs.narrative_ledger


# ---------------------------------------------------------------------------
# AC-12: CampaignState.to_dict() entity keys are strings (JSON safety)
# ---------------------------------------------------------------------------

def test_campaign_state_to_dict_entity_keys_are_strings():
    cs = _make_campaign_state()
    d = cs.to_dict()
    for key in d["persistent_entities"]:
        assert isinstance(key, str), f"Expected str key, got {type(key)}: {key!r}"


# ---------------------------------------------------------------------------
# AC-13: CampaignState is mutable (can append, update dicts, etc.)
# ---------------------------------------------------------------------------

def test_campaign_state_is_mutable():
    cs = CampaignState(campaign_id="test", episode_index=0)
    new_ep = EpisodeSummary(episode_index=0, completed_tick=200)
    cs.episode_history.append(new_ep)
    assert len(cs.episode_history) == 1

    entity = _make_entity(entity_id=7)
    cs.persistent_entities[7] = entity
    assert 7 in cs.persistent_entities

    cs.episode_index = 1
    assert cs.episode_index == 1


# ---------------------------------------------------------------------------
# AC-14: CampaignState.to_dict() output passes json.dumps without custom encoder
# ---------------------------------------------------------------------------

def test_campaign_state_to_dict_is_json_safe():
    cs = _make_campaign_state()
    d = cs.to_dict()
    encoded = json.dumps(d)
    decoded = json.loads(encoded)
    assert decoded["campaign_id"] == "campaign-abc"
    assert "42" in decoded["persistent_entities"]


# ---------------------------------------------------------------------------
# AC-15: All types importable from src.domains.campaigns.state
# ---------------------------------------------------------------------------

def test_campaign_state_importable():
    assert CampaignState is not None
    assert EntityCarryForward is not None
    assert FactionCarryForward is not None
    assert EpisodeSummary is not None
    assert WorldTimelineEntry is not None
    assert NarrativeLedgerEntry is not None


# ---------------------------------------------------------------------------
# Guard 4: state.py has no imports from src.engine.* or src.systems.*
# ---------------------------------------------------------------------------

def test_campaign_state_module_has_no_engine_imports():
    state_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "domains" / "campaigns" / "state.py"
    source = state_path.read_text()
    tree = ast.parse(source)

    forbidden_prefixes = ("src.engine", "src.systems")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"state.py must not import from {prefix!r}; found: {node.module!r}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        assert not alias.name.startswith(prefix), (
                            f"state.py must not import from {prefix!r}; found: {alias.name!r}"
                        )
