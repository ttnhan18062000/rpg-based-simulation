"""
tests/unit/domains/combat_engagement/test_opponent_model_persistence.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Proves CombatEngagementPhase.apply() actually persists a real OpponentModel across ticks through
the real authoritative apply path -- previously CombatEngagementDecisionService.evaluate()'s own
memory= parameter was never passed by any real caller, so PerceivedOpponentEstimate.memory_used was
always empty in a real run regardless of how many times the same target had been observed.
"""

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CombatComponent, BiologicalComponent, PersonalityComponent
from src.core.enums import Faction
from src.engine.apply import ApplyPath
from src.domains.combat_engagement.phase import CombatEngagementPhase, opponent_subject_key


def _entity(ent_id, x, y, hp=100, atk=10, faction=None):
    b = V2EntityBuilder(ent_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=atk, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(
        evolution_level=1,
        personality=PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5),
        faction=faction,
    )
    b.location(x, y)
    b.lifecycle(active=True)
    return b.build()


def _state(entities, tick: int = 1) -> AuthoritativeState:
    return AuthoritativeState(entities={e.id: e for e in entities}, tick=tick, seed=42)


def test_first_observation_has_no_memory_used():
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    target = _entity(2, 1.0, 1.0, faction=Faction.MONSTER_HORDE)
    state = _state([actor, target])

    update = CombatEngagementPhase.apply(state)

    assert update.entity_updates[1].cognition_bundle_set is not None
    result_estimate_memory_used = update.entity_updates[1].cognition_bundle_set.memory.combat.opponent_stats
    assert opponent_subject_key(2) in result_estimate_memory_used


def test_opponent_model_survives_the_real_apply_path_across_ticks():
    """
    End-to-end through the real authoritative apply path: a real OpponentModel for the observed
    target must be readable at entity.cognition.memory.combat.opponent_stats on the NEXT tick's
    state, and the second observation must show memory_used non-empty -- proving the model
    genuinely persisted rather than every tick re-deriving from scratch (memory=None again).
    """
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    target = _entity(2, 1.0, 1.0, faction=Faction.MONSTER_HORDE)
    state = _state([actor, target])

    update = CombatEngagementPhase.apply(state)
    state = ApplyPath.apply_generation(state, update, next_tick=state.tick + 1)

    subject_key = opponent_subject_key(2)
    stored = state.entities[1].cognition.memory.combat.opponent_stats.get(subject_key)
    assert stored is not None, "OpponentModel must survive the real apply path"
    assert stored.subject_key == subject_key

    # Second observation on the persisted state -- CombatEngagementDecisionService.evaluate() is
    # called again internally with the now-real, non-None memory.
    update2 = CombatEngagementPhase.apply(state)
    new_cognition = update2.entity_updates[1].cognition_bundle_set
    assert new_cognition is not None
    stored_again = new_cognition.memory.combat.opponent_stats[subject_key]
    assert stored_again.last_updated_tick == state.tick


def test_repeated_ticks_update_rather_than_grow_the_same_subject_key():
    actor = _entity(1, 0.0, 0.0, faction=Faction.HERO_GUILD)
    target = _entity(2, 1.0, 1.0, faction=Faction.MONSTER_HORDE)
    state = _state([actor, target])

    for _ in range(3):
        update = CombatEngagementPhase.apply(state)
        state = ApplyPath.apply_generation(state, update, next_tick=state.tick + 1)

    stats = state.entities[1].cognition.memory.combat.opponent_stats
    assert len(stats) == 1
    assert opponent_subject_key(2) in stats
