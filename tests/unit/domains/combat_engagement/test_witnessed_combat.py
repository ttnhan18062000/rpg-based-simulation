"""
tests/unit/domains/combat_engagement/test_witnessed_combat.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Sec 13.7: a witness within perception radius of a real fight's own participants gains a real
OpponentModel entry for BOTH participants without ever fighting either one itself -- proven here
via the real CombatEngagementPhase.apply() call path, not a hand-built update.
"""

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CombatComponent, BiologicalComponent, PersonalityComponent
from src.core.enums import Faction
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate
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


def _state(entities, tick=1) -> AuthoritativeState:
    return AuthoritativeState(entities={e.id: e for e in entities}, tick=tick, seed=42)


def test_nearby_witness_gains_opponent_models_for_both_real_fight_participants():
    attacker = _entity(1, 0.0, 0.0, faction=Faction.MONSTER_HORDE)
    defender = _entity(2, 1.0, 1.0, faction=Faction.HERO_GUILD, hp=100)
    # A third entity, NOT hostile to anyone and far from either combatant's own faction concerns,
    # positioned within perception radius of the fight but not itself a participant.
    witness = _entity(3, 2.0, 2.0, faction=Faction.NEUTRAL)
    state = _state([attacker, defender, witness])

    # A real CombatUpdate for the defender this tick, as src/engine/combat.py's own
    # CombatResolutionSystem.resolve_attack() would have produced.
    tick_update = StateUpdate(entity_updates={
        defender.id: EntityUpdate(
            entity_id=defender.id,
            combat=CombatUpdate(damage_taken=30, hp_delta=-30, attacker_id=attacker.id, outcome_kind="SURVIVE"),
        )
    })

    update = CombatEngagementPhase.apply(state, tick_update=tick_update)

    assert witness.id in update.entity_updates
    witness_cognition = update.entity_updates[witness.id].cognition_bundle_set
    assert witness_cognition is not None

    stats = witness_cognition.memory.combat.opponent_stats
    assert opponent_subject_key(attacker.id) in stats
    assert opponent_subject_key(defender.id) in stats


def test_distant_entity_is_not_a_witness():
    attacker = _entity(1, 0.0, 0.0, faction=Faction.MONSTER_HORDE)
    defender = _entity(2, 1.0, 1.0, faction=Faction.HERO_GUILD)
    far_away = _entity(3, 500.0, 500.0, faction=Faction.NEUTRAL)
    state = _state([attacker, defender, far_away])

    tick_update = StateUpdate(entity_updates={
        defender.id: EntityUpdate(
            entity_id=defender.id,
            combat=CombatUpdate(damage_taken=30, hp_delta=-30, attacker_id=attacker.id, outcome_kind="SURVIVE"),
        )
    })

    update = CombatEngagementPhase.apply(state, tick_update=tick_update)

    assert far_away.id not in update.entity_updates


def test_rejected_combat_update_produces_no_witnesses():
    """
    A REJECTED outcome_kind never represents a real fight -- no witnessing should occur. The
    witness here (NEUTRAL) is independently hostile-compatible with MONSTER_HORDE under this
    repo's real faction semantics, so it may still get an EntityUpdate from the main per-actor
    loop's own unrelated hostile-scan (evaluating a posture toward the attacker directly) -- that
    loop can only ever produce a model of the ONE hostile it scanned (the attacker), never of the
    defender too. Only the witnessed-combat tier could add a model of the DEFENDER for a witness
    that never itself targeted the defender, so its absence is the precise, real proof REJECTED
    produced no witnessing.
    """
    attacker = _entity(1, 0.0, 0.0, faction=Faction.MONSTER_HORDE)
    defender = _entity(2, 1.0, 1.0, faction=Faction.HERO_GUILD)
    witness = _entity(3, 2.0, 2.0, faction=Faction.NEUTRAL)
    state = _state([attacker, defender, witness])

    tick_update = StateUpdate(entity_updates={
        defender.id: EntityUpdate(
            entity_id=defender.id,
            combat=CombatUpdate(attacker_id=attacker.id, outcome_kind="REJECTED"),
        )
    })

    update = CombatEngagementPhase.apply(state, tick_update=tick_update)

    witness_update = update.entity_updates.get(witness.id)
    if witness_update is not None and witness_update.cognition_bundle_set is not None:
        stats = witness_update.cognition_bundle_set.memory.combat.opponent_stats
        assert opponent_subject_key(defender.id) not in stats


def test_no_tick_update_means_no_witnessed_combat_but_no_crash():
    actor = _entity(1, 0.0, 0.0, faction=Faction.NEUTRAL)
    state = _state([actor])

    update = CombatEngagementPhase.apply(state, tick_update=None)

    assert isinstance(update, StateUpdate)


def test_witness_who_is_also_evaluating_its_own_hostile_gets_both_writes_merged():
    """
    A witness that is ALSO, separately, evaluating its own nearest hostile this same tick (the
    main per-actor loop) must not have that write clobbered by the witnessed-combat pass, or
    vice versa -- both must land on the same final EntityUpdate.
    """
    attacker = _entity(1, 0.0, 0.0, faction=Faction.MONSTER_HORDE)
    defender = _entity(2, 1.0, 1.0, faction=Faction.HERO_GUILD)
    # witness_actor is both a witness to the attacker/defender fight AND has its own separate
    # hostile nearby to evaluate a posture toward.
    witness_actor = _entity(3, 2.0, 2.0, faction=Faction.HERO_GUILD)
    own_hostile = _entity(4, 2.5, 2.5, faction=Faction.MONSTER_HORDE)
    state = _state([attacker, defender, witness_actor, own_hostile])

    tick_update = StateUpdate(entity_updates={
        defender.id: EntityUpdate(
            entity_id=defender.id,
            combat=CombatUpdate(damage_taken=30, hp_delta=-30, attacker_id=attacker.id, outcome_kind="SURVIVE"),
        )
    })

    update = CombatEngagementPhase.apply(state, tick_update=tick_update)

    assert witness_actor.id in update.entity_updates
    witness_update = update.entity_updates[witness_actor.id]
    # The main loop's own write (posture toward own_hostile).
    assert witness_update.property_updates.get("last_combat_posture_target") == own_hostile.id
    # The witnessed-combat pass's own write (OpponentModel for the attacker/defender pair).
    stats = witness_update.cognition_bundle_set.memory.combat.opponent_stats
    assert opponent_subject_key(attacker.id) in stats
    assert opponent_subject_key(defender.id) in stats
    # And the main loop's own passive observation of own_hostile must still be present too.
    assert opponent_subject_key(own_hostile.id) in stats
