"""
tests/unit/engine/test_combat_actions_learning_wiring.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Proves CombatActions.execute_attack() (src/engine/domain/combat_actions.py) -- the real
ATTACK_TARGET action handler -- wires src.domains.combat_engagement.learning_outcome.
apply_combat_learning() into a real, legal attack resolution, updating both real participants'
OpponentModel via the declared Sec 13.5a mapping. Not a hand-built CombatUpdate: this goes through
the real LegalityServiceV2.verify_attack_legality() + CombatResolutionSystem.resolve_attack() path.
"""

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.enums import Faction, EntityRole
from src.core.builder import V2EntityBuilder
from src.engine.domain.combat_actions import CombatActions
from src.domains.combat_engagement.phase import opponent_subject_key


def _entity(e_id, pos, hp=100, atk=10, faction=Faction.HERO_GUILD):
    b = (
        V2EntityBuilder(e_id)
        .kind("ACTOR")
        .location(*pos)
        .identity(role=EntityRole.HERO, faction=faction, evolution_level=1)
        .combat(hp=hp, max_hp=100, atk=atk, attack_range=1, alive=hp > 0, readiness=100.0)
        .biological(hunger=0.0, sleep_debt=0.0)
        .lifecycle(active=True)
    )
    return b.build()


def _state(entities, tick=1):
    return AuthoritativeState(entities={e.id: e for e in entities}, tick=tick, seed=42)


def test_real_kill_updates_both_participants_via_execute_attack():
    attacker = _entity(1, (10, 10), hp=15, atk=100, faction=Faction.HERO_GUILD)  # near-death, hard-won
    defender = _entity(2, (10, 11), hp=1, faction=Faction.MONSTER_HORDE)  # one hit from death
    state = _state([attacker, defender])

    updates = CombatActions.execute_attack(
        attacker, payload={"target_id": defender.id}, current_tick=state.tick,
        context=state,
    )

    assert attacker.id in updates
    assert defender.id in updates

    attacker_up = updates[attacker.id]
    defender_up = updates[defender.id]

    # Real KILL outcome, low attacker HP -> NEAR_DEATH for the attacker's own model of the defender.
    assert attacker_up.cognition_bundle_set is not None
    attacker_stats = attacker_up.cognition_bundle_set.memory.combat.opponent_stats
    assert opponent_subject_key(defender.id) in attacker_stats
    assert attacker_stats[opponent_subject_key(defender.id)].outcomes[-1] == "NEAR_DEATH"

    # The defender died -> LOST for the defender's own model of the attacker.
    assert defender_up.cognition_bundle_set is not None
    defender_stats = defender_up.cognition_bundle_set.memory.combat.opponent_stats
    assert opponent_subject_key(attacker.id) in defender_stats
    assert defender_stats[opponent_subject_key(attacker.id)].outcomes[-1] == "LOST"


def test_real_kill_at_high_attacker_hp_learns_won_easy():
    attacker = _entity(1, (10, 10), hp=95, atk=100, faction=Faction.HERO_GUILD)  # barely scratched
    defender = _entity(2, (10, 11), hp=1, faction=Faction.MONSTER_HORDE)
    state = _state([attacker, defender])

    updates = CombatActions.execute_attack(
        attacker, payload={"target_id": defender.id}, current_tick=state.tick,
        context=state,
    )

    attacker_up = updates[attacker.id]
    attacker_stats = attacker_up.cognition_bundle_set.memory.combat.opponent_stats
    assert attacker_stats[opponent_subject_key(defender.id)].outcomes[-1] == "WON_EASY"


def test_real_non_lethal_hit_produces_no_learning():
    """A SURVIVE outcome (defender takes damage but lives) is inconclusive for either side."""
    attacker = _entity(1, (10, 10), hp=100, atk=5, faction=Faction.HERO_GUILD)
    defender = _entity(2, (10, 11), hp=100, faction=Faction.MONSTER_HORDE)
    state = _state([attacker, defender])

    updates = CombatActions.execute_attack(
        attacker, payload={"target_id": defender.id}, current_tick=state.tick,
        context=state,
    )

    assert updates[attacker.id].cognition_bundle_set is None
    assert updates[defender.id].cognition_bundle_set is None


def test_illegal_attack_produces_no_learning():
    """An out-of-range (illegal) attack never reaches real combat resolution -- no learning."""
    attacker = _entity(1, (0, 0), hp=100, faction=Faction.HERO_GUILD)
    defender = _entity(2, (50, 50), hp=100, faction=Faction.MONSTER_HORDE)  # far out of range
    state = _state([attacker, defender])

    updates = CombatActions.execute_attack(
        attacker, payload={"target_id": defender.id}, current_tick=state.tick,
        context=state,
    )

    assert defender.id not in updates
    assert updates[attacker.id].cognition_bundle_set is None
