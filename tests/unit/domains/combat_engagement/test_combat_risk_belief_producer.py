"""
tests/unit/domains/combat_engagement/test_combat_risk_belief_producer.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

Covers the real producer for entity.strategic.beliefs["combat_risk"] -- previously a tested
consumer (HelpNeedEvaluator.evaluate()) with no production writer at all.

Three layers:
  1. death_risk -> RiskLevel threshold mapping (boundary values, derived from
     EngagementRiskEvaluator's own live constants -- see the phase module's own comments).
  2. The producer really emits a BeliefEntry keyed "combat_risk" through a real
     CombatEngagementPhase.apply() call (not a hand-built StrategicUpdate).
  3. The consumer really parses that BeliefEntry back into a RiskLevel, including the
     defensive degrade-not-raise path for a malformed claim.
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import (
    AuthoritativeState, CombatComponent, BiologicalComponent, PersonalityComponent
)
from src.core.enums import Faction
from src.core.strategic import RiskLevel
from src.engine.apply import ApplyPath
from src.domains.combat_engagement.phase import (
    CombatEngagementPhase,
    COMBAT_RISK_BELIEF_ID,
    build_combat_risk_belief,
    death_risk_to_level,
)
from src.domains.cooperation.evaluators import HelpNeedEvaluator
from src.systems.strategic_systems.belief import BeliefEntry


def _entity(ent_id: int, x: float, y: float, hp: int = 100, atk: int = 10, bravery: float = 0.5,
            faction: Faction = None):
    b = V2EntityBuilder(ent_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=atk, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(
        evolution_level=1,
        personality=PersonalityComponent(
            greed=0.5, bravery=bravery, sociability=0.5, industry=0.5
        ),
        faction=faction,
    )
    b.location(x, y)
    b.lifecycle(active=True)
    return b.build()


def _state(entities, tick: int = 1) -> AuthoritativeState:
    return AuthoritativeState(
        entities={e.id: e for e in entities}, tick=tick, seed=42
    )


# ---------------------------------------------------------------------------
# 1. Threshold mapping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("death_risk,expected", [
    (0.0, RiskLevel.LOW),
    (0.20, RiskLevel.LOW),        # boundary: actor 2x stronger, inclusive
    (0.21, RiskLevel.NORMAL),
    (0.40, RiskLevel.NORMAL),     # boundary: evenly matched, inclusive
    (0.41, RiskLevel.HIGH),
    (0.80, RiskLevel.HIGH),       # boundary: the evaluator's own critical lock, inclusive
    (0.81, RiskLevel.EXTREME),
    (0.90, RiskLevel.EXTREME),    # near_death forces death_risk >= 0.9 -> must land EXTREME
    (1.0, RiskLevel.EXTREME),
])
def test_death_risk_maps_to_expected_risk_level(death_risk, expected):
    assert death_risk_to_level(death_risk) is expected


def test_near_death_floor_lands_in_extreme():
    """EngagementRiskEvaluator forces death_risk = max(0.9, ...) on near_death."""
    assert death_risk_to_level(0.9) is RiskLevel.EXTREME


def test_built_belief_has_producer_contract_shape():
    belief = build_combat_risk_belief(death_risk=0.6, current_tick=7)
    assert isinstance(belief, BeliefEntry)
    # The id IS the dict key merge_dict() will use -- must equal the consumer's lookup key.
    assert belief.id == COMBAT_RISK_BELIEF_ID == "combat_risk"
    assert belief.claim == RiskLevel.HIGH.value
    assert belief.certainty == 0.6          # raw death_risk preserved alongside the level
    assert belief.source == "observation"
    assert belief.created_tick == 7
    assert belief.last_refreshed_tick == 7


def test_built_belief_certainty_is_clamped():
    assert build_combat_risk_belief(death_risk=1.7, current_tick=1).certainty == 1.0
    assert build_combat_risk_belief(death_risk=-0.5, current_tick=1).certainty == 0.0


# ---------------------------------------------------------------------------
# 2. Real producer through CombatEngagementPhase.apply()
# ---------------------------------------------------------------------------

def test_phase_emits_combat_risk_belief_for_actor_near_hostile():
    """A real CombatEngagementPhase.apply() call must produce the belief, not a hand-built update.

    TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (correction, 2026-09-08): explicit hostile
    factions are required post-fix -- an unset (NEUTRAL) faction is never hostile to anything, so
    this scenario would silently produce zero targets without them.
    """
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    target = _entity(2, 1.0, 1.0, faction=Faction.MONSTER_HORDE)
    state = _state([actor, target])

    update = CombatEngagementPhase.apply(state)

    assert 1 in update.entity_updates, "actor should get an EntityUpdate when a hostile is nearby"
    strat = update.entity_updates[1].strategic
    assert strat is not None
    beliefs = [b for b in strat.beliefs_add_or_update if b.id == COMBAT_RISK_BELIEF_ID]
    assert len(beliefs) == 1, "exactly one combat_risk belief per actor per tick"
    assert beliefs[0].claim in {lvl.value for lvl in RiskLevel}


def test_combat_risk_is_written_from_the_nearest_hostile_not_an_arbitrary_neighbor():
    """
    TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (correction, 2026-09-08): a post-merge peer
    review found the original implementation had no hostility filter at all and only ever
    evaluated whichever entity happened to come first out of an unordered spatial query --
    meaning `combat_risk` could be written from a harmless (non-hostile) neighbor instead of a
    real threat, silently under-reporting risk. This is the exact regression scenario: a harmless
    NEUTRAL entity sits closer to the actor than a genuinely hostile, much-stronger MONSTER_HORDE
    entity. Pre-fix, the harmless neighbor (or whichever came first) could win and produce a LOW
    reading; post-fix, the harmless entity must be excluded entirely by the hostility filter, and
    `combat_risk` must reflect the real hostile threat instead.
    """
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    # Harmless, NOT hostile, and deliberately closer than the real threat.
    harmless_neighbor = _entity(2, 0.1, 0.1, faction=Faction.NEUTRAL)
    # Real hostile threat: much higher atk than the actor -> a real elevated death_risk.
    hostile_threat = _entity(3, 1.0, 1.0, atk=100, faction=Faction.MONSTER_HORDE)
    state = _state([actor, harmless_neighbor, hostile_threat])

    update = CombatEngagementPhase.apply(state)

    assert 1 in update.entity_updates
    prop_updates = update.entity_updates[1].property_updates
    assert prop_updates["last_combat_posture_target"] == 3, (
        "the harmless closer neighbor must not be selected -- only the hostile entity is a "
        "valid candidate at all, regardless of distance"
    )
    strat = update.entity_updates[1].strategic
    beliefs = [b for b in strat.beliefs_add_or_update if b.id == COMBAT_RISK_BELIEF_ID]
    assert len(beliefs) == 1
    # A much stronger hostile attacker must NOT read as LOW risk -- proves the belief was
    # genuinely sourced from the real threat, not silently defaulted from a harmless neighbor.
    assert beliefs[0].claim != RiskLevel.LOW.value


def test_phase_emits_no_belief_when_no_targets_nearby():
    """Isolated actor -> no evaluation happens -> no combat_risk belief written."""
    actor = _entity(1, 0.0, 0.0)
    far = _entity(2, 500.0, 500.0)
    state = _state([actor, far])

    update = CombatEngagementPhase.apply(state)

    for eu in update.entity_updates.values():
        if eu.strategic is not None:
            assert not [
                b for b in eu.strategic.beliefs_add_or_update
                if b.id == COMBAT_RISK_BELIEF_ID
            ]


def test_belief_lands_in_durable_state_under_the_consumer_lookup_key():
    """
    End-to-end through the real authoritative apply path: the belief must be readable at
    entity.strategic.beliefs["combat_risk"] -- proving merge_dict()'s `res[item.id] = item`
    keying really does line up with the consumer's lookup key.
    """
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    target = _entity(2, 1.0, 1.0, faction=Faction.MONSTER_HORDE)
    state = _state([actor, target])

    update = CombatEngagementPhase.apply(state)
    next_state = ApplyPath.apply_generation(state, update, next_tick=state.tick + 1)

    stored = next_state.entities[1].strategic.beliefs.get("combat_risk")
    assert stored is not None, "combat_risk belief must survive the real apply path"
    assert isinstance(stored, BeliefEntry)
    assert stored.claim in {lvl.value for lvl in RiskLevel}


def test_repeated_ticks_replace_rather_than_accumulate_the_belief():
    """Stable id => each tick replaces in place; the beliefs dict must not grow unbounded."""
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    target = _entity(2, 1.0, 1.0, faction=Faction.MONSTER_HORDE)
    state = _state([actor, target])

    for _ in range(3):
        update = CombatEngagementPhase.apply(state)
        state = ApplyPath.apply_generation(state, update, next_tick=state.tick + 1)

    combat_risk_keys = [
        k for k in state.entities[1].strategic.beliefs.keys() if k == COMBAT_RISK_BELIEF_ID
    ]
    assert len(combat_risk_keys) == 1
    assert state.entities[1].strategic.beliefs[COMBAT_RISK_BELIEF_ID].last_refreshed_tick >= 1


# ---------------------------------------------------------------------------
# 3. Consumer reads the real BeliefEntry
# ---------------------------------------------------------------------------

def _entity_with_active_objective(risk_belief):
    from src.core.strategic import ProjectState, ProjectKind, ObjectiveState, ObjectiveKind

    entity = _entity(1, 0.0, 0.0)
    obj = ObjectiveState(id="obj_1", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(
        id="proj_1", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id="obj_1"
    )
    entity.strategic.projects["proj_1"] = proj
    object.__setattr__(entity.strategic, "current_project_id", "proj_1")
    object.__setattr__(entity.strategic, "current_objective_id", "obj_1")
    if risk_belief is not None:
        entity.strategic.beliefs["combat_risk"] = risk_belief
    return entity


def test_consumer_raises_combat_support_need_from_real_belief_entry():
    entity = _entity_with_active_objective(
        build_combat_risk_belief(death_risk=0.6, current_tick=1)  # -> HIGH
    )
    needs = HelpNeedEvaluator.evaluate(entity, _state([entity]))
    assert any(n.key == "combat_support_needed" for n in needs)


def test_consumer_treats_low_risk_belief_as_no_combat_support_need():
    entity = _entity_with_active_objective(
        build_combat_risk_belief(death_risk=0.1, current_tick=1)  # -> LOW
    )
    needs = HelpNeedEvaluator.evaluate(entity, _state([entity]))
    assert not any(n.key == "combat_support_needed" for n in needs)


def test_consumer_degrades_to_normal_on_unparseable_claim_without_raising():
    """`beliefs` is generically typed -- a foreign/malformed entry must not blow up Phase 7."""
    bogus = BeliefEntry(id="combat_risk", subject="combat_risk", claim="not_a_risk_level")
    entity = _entity_with_active_objective(bogus)
    needs = HelpNeedEvaluator.evaluate(entity, _state([entity]))  # must not raise
    assert not any(n.key == "combat_support_needed" for n in needs)


def test_consumer_handles_absent_belief():
    entity = _entity_with_active_objective(None)
    needs = HelpNeedEvaluator.evaluate(entity, _state([entity]))
    assert not any(n.key == "combat_support_needed" for n in needs)
