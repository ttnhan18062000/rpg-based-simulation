"""Tactical-path wiring test for RelationContext.source_race (Step 8).

TCK-20260831-RACE-RELATIONS-MATRIX: proves TacticalDecisionSystem.evaluate_entity_intent()'s
hostile-scan loop now populates RelationContext.source_race, so an authored race_relations
entry can pull a neighbor into the `hostiles` list (upstream of target_score()'s sort tuple,
which this ticket does not touch -- see test_capability_driven_targeting.py).
"""
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.engine.tactical import TacticalDecisionSystem


def _make_entity(eid: int, faction_id: str, race_id: str, pos=(0.0, 0.0)):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .properties({"faction_id": faction_id, "race_id": race_id})
        .combat(hp=100, max_hp=100, atk=10, attack_range=1, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def test_tactical_hostile_scan_race_hostility_affects_target_pool():
    """swamp_tribe (goblin) vs forest_wardens (elf): no perspective/relationship label,
    but an authored goblin_to_elf race_relations entry (hostility: high) escalates the
    pair to hostile, so the target is selected as the hostiles-list combat target."""
    attacker = _make_entity(1, "swamp_tribe", "goblin", (0.0, 0.0))
    enemy = _make_entity(2, "forest_wardens", "elf", (1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: enemy})
    result = TacticalDecisionSystem.evaluate_entity_intent(state, attacker, neighbors=[enemy])

    assert result.task is not None
    assert result.task.payload_set.get("target_id") == 2


def test_tactical_hostile_scan_no_race_entry_stays_non_hostile():
    """Same faction pair, races with no authored race_relations entry (human/spirit) —
    baseline behavior (no escalation, no perspective/relationship label either) means the
    neighbor is never added to the hostiles list."""
    attacker = _make_entity(1, "swamp_tribe", "human", (0.0, 0.0))
    other = _make_entity(2, "forest_wardens", "spirit", (1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: other})
    result = TacticalDecisionSystem.evaluate_entity_intent(state, attacker, neighbors=[other])

    payload = result.task.payload_set if result.task else {}
    assert payload.get("target_id") != 2
