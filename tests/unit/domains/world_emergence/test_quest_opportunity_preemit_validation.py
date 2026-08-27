# tests/unit/domains/world_emergence/test_quest_opportunity_preemit_validation.py
"""Pre-emit grammar validation for QuestOpportunity admission (TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION)."""
import pytest
from src.core.state import AuthoritativeState, FactionState, ResourceNodeState
from src.core.updates import StateUpdate
from src.core.models.quests import QuestOpportunity
from src.domains.world_emergence import quest_grammar
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.domains.world_emergence.services import QuestOpportunityGenerator
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory


def _make_opportunity(faction_source=None, objective_chain=("fetch:iron_ore:3",)):
    return QuestOpportunity(
        id="opp_test_1",
        kind="resource_crisis",
        trigger_condition="test",
        objective_chain=objective_chain,
        reward_spec={"gold": 50, "xp": 100, "faction_rep": 0.1},
        faction_source=faction_source,
        expiry_ticks=200,
        source_event_id="evt_test_1",
    )


def _make_node(node_id, yields_item, remaining_charges, max_charges=10):
    return ResourceNodeState(
        id=node_id,
        kind="ore_vein",
        position=(0.0, 0.0),
        yields_item=yields_item,
        remaining_charges=remaining_charges,
        max_charges=max_charges,
        required_ticks=5,
    )


# --- Faction coherence ---

def test_faction_coherence_rejects_zero_territory_faction():
    state_absent = AuthoritativeState(tick=1, seed=0)
    assert quest_grammar.check_faction_coherence("ghost_faction", state_absent) is False

    state_empty_territory = AuthoritativeState(
        tick=1, seed=0,
        factions={"empty_faction": FactionState(faction_id="empty_faction", territory=())},
    )
    assert quest_grammar.check_faction_coherence("empty_faction", state_empty_territory) is False

    opp = _make_opportunity(faction_source="ghost_faction")
    assert quest_grammar.validate_quest_opportunity(opp, state_absent) == "faction_zero_territory"


def test_faction_coherence_accepts_faction_with_territory():
    state = AuthoritativeState(
        tick=1, seed=0,
        factions={"holders": FactionState(faction_id="holders", territory=("north",))},
    )
    assert quest_grammar.check_faction_coherence("holders", state) is True

    opp = _make_opportunity(faction_source="holders", objective_chain=())
    assert quest_grammar.validate_quest_opportunity(opp, state) is None


def test_faction_coherence_passes_when_faction_source_is_none():
    state = AuthoritativeState(tick=42, seed=1)
    assert quest_grammar.check_faction_coherence(None, state) is True

    depleted_event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=42, region_id="old_mine", subject="iron_ore", severity=1.0,
    )
    opp = QuestOpportunityGenerator.from_resource_depleted(depleted_event, tick=42, seed=1)
    assert opp.faction_source is None

    threat_event = WorldEvent(
        category=WorldEventCategory.ENTITY_DEATH,
        tick=55, region_id="dark_forest", subject="hero", severity=0.9,
    )
    threat_opp = QuestOpportunityGenerator.from_threat_signal(threat_event, tick=55, seed=1)
    assert threat_opp.faction_source is None


# --- Resource availability ---

def test_resource_availability_rejects_when_all_matching_nodes_depleted():
    state = AuthoritativeState(
        tick=1, seed=0,
        resource_nodes={
            1: _make_node(1, "iron_ore", remaining_charges=0),
            2: _make_node(2, "iron_ore", remaining_charges=0),
        },
    )
    opp = _make_opportunity(objective_chain=("fetch:iron_ore:3",))
    assert quest_grammar.check_resource_availability(opp.objective_chain, state) is False
    assert quest_grammar.validate_quest_opportunity(opp, state) == "resource_depleted"


def test_resource_availability_passes_when_any_matching_node_has_charges():
    state = AuthoritativeState(
        tick=1, seed=0,
        resource_nodes={
            1: _make_node(1, "iron_ore", remaining_charges=0),
            2: _make_node(2, "iron_ore", remaining_charges=5),
        },
    )
    opp = _make_opportunity(objective_chain=("fetch:iron_ore:3",))
    assert quest_grammar.check_resource_availability(opp.objective_chain, state) is True
    assert quest_grammar.validate_quest_opportunity(opp, state) is None


def test_resource_availability_passes_when_no_matching_node_exists():
    state = AuthoritativeState(tick=1, seed=0)
    opp = _make_opportunity(objective_chain=("fetch:iron_ore:3",))
    assert quest_grammar.check_resource_availability(opp.objective_chain, state) is True
    assert quest_grammar.validate_quest_opportunity(opp, state) is None

    non_fetch_opp = _make_opportunity(objective_chain=("eliminate:threat:1",))
    assert quest_grammar.check_resource_availability(non_fetch_opp.objective_chain, state) is True


# --- Determinism / read-only / no-uuid-or-time contract ---

def test_preemit_validation_is_deterministic_and_read_only():
    state = AuthoritativeState(
        tick=7, seed=3,
        factions={"holders": FactionState(faction_id="holders", territory=("north",))},
        resource_nodes={1: _make_node(1, "iron_ore", remaining_charges=0)},
    )
    opp = _make_opportunity(faction_source="holders", objective_chain=("fetch:iron_ore:3",))

    before = state.to_canonical_dict() if hasattr(state, "to_canonical_dict") else None

    verdict_1 = quest_grammar.validate_quest_opportunity(opp, state)
    verdict_2 = quest_grammar.validate_quest_opportunity(opp, state)

    assert verdict_1 == verdict_2 == "resource_depleted"
    assert state.tick == 7
    assert state.seed == 3
    if before is not None:
        assert state.to_canonical_dict() == before


def test_preemit_check_does_not_call_uuid_or_time_based_seeding():
    state = AuthoritativeState(
        tick=100, seed=9,
        factions={"holders": FactionState(faction_id="holders", territory=("north",))},
    )
    opp = _make_opportunity(faction_source="holders", objective_chain=())

    results = {quest_grammar.validate_quest_opportunity(opp, state) for _ in range(5)}
    assert results == {None}


# --- Phase wiring ---

def test_passing_opportunity_reaches_quest_registry_add_unfiltered():
    depleted_event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=5, region_id="north", subject="iron_ore", severity=0.8,
    )
    state = AuthoritativeState(tick=5, seed=1)
    update = StateUpdate()

    new_update, result = WorldEmergencePhase.execute(state, update, recent_events=[depleted_event])

    assert len(new_update.quest_registry_add) == 1
    assert new_update.quest_registry_add[0].kind == "resource_crisis"
    assert new_update.metric_counters.get("quest_opportunities_rejected") == 0


def test_rejected_opportunity_excluded_from_quest_registry_add():
    depleted_event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=5, region_id="north", subject="iron_ore", severity=0.8,
    )
    state = AuthoritativeState(
        tick=5, seed=1,
        resource_nodes={1: _make_node(1, "iron_ore", remaining_charges=0)},
    )
    update = StateUpdate()

    new_update, result = WorldEmergencePhase.execute(state, update, recent_events=[depleted_event])

    assert new_update.quest_registry_add == []
    assert new_update.metric_counters.get("quest_opportunities_rejected") == 1
    # result.quest_opportunities remains unfiltered per scope
    assert len(result.quest_opportunities) == 1
