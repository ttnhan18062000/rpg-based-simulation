import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction, ReasonCode
from src.engine.apply import ApplyPath
from src.engine.legality import LegalityServiceV2
from src.content_semantics.relation import RelationContext


def _build(e_id, pos, readiness=0.0, readiness_speed=10.0, faction=Faction.HERO_GUILD, role=EntityRole.HERO):
    return (V2EntityBuilder(e_id)
            .kind("actor")
            .location(*pos)
            .identity(faction=faction)
            .identity(role=role)
            .combat(hp=100, atk=10, def_stat=5, attack_range=1,
                    readiness=readiness, readiness_speed=readiness_speed)
            .build())


def test_readiness_regenerates_passively_per_tick():
    """TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION: docs/engine/contracts/
    minimal_kernel.md Section 5 documents passive readiness accumulation via readiness_speed;
    previously no code path implemented it (readiness only ever decreased)."""
    ent = _build(1, (0.0, 0.0), readiness=50.0, readiness_speed=10.0)
    state = AuthoritativeState(tick=1, seed=42, entities={1: ent})

    next_state = ApplyPath.apply_generation(state, StateUpdate(), 2, 2)

    assert next_state.entities[1].combat.readiness == 60.0


def test_readiness_regen_clamps_at_100():
    ent = _build(1, (0.0, 0.0), readiness=95.0, readiness_speed=10.0)
    state = AuthoritativeState(tick=1, seed=42, entities={1: ent})

    next_state = ApplyPath.apply_generation(state, StateUpdate(), 2, 2)

    assert next_state.entities[1].combat.readiness == 100.0


def test_readiness_speed_zero_disables_regen():
    ent = _build(1, (0.0, 0.0), readiness=50.0, readiness_speed=0.0)
    state = AuthoritativeState(tick=1, seed=42, entities={1: ent})

    next_state = ApplyPath.apply_generation(state, StateUpdate(), 2, 2)

    assert next_state.entities[1].combat.readiness == 50.0


def test_readiness_speed_survives_to_readonly_reconstruction():
    """EntityState.to_readonly() rebuilds CombatComponent via an explicit hardcoded kwarg
    list (CORE-PERF-010); previously it silently dropped readiness_speed, resetting any
    non-default value back to the dataclass default on every readonly-conversion pass."""
    ent = _build(1, (0.0, 0.0), readiness=50.0, readiness_speed=37.0)
    # Force the wounds/scars-not-tuple branch that triggers CombatComponent reconstruction.
    dirty_combat = replace(ent.combat, wounds=[], scars=[])
    ent = replace(ent, combat=dirty_combat)

    readonly_ent = ent.to_readonly()

    assert readonly_ent.combat.readiness_speed == 37.0


def test_contextual_intruder_group_hostility_not_hardcoded_neutral():
    """Regression for the intruding=False hardcode in verify_attack_legality/tactical.py:
    RelationProjectionService treats an explicit False (not None) as a confirmed non-intrusion,
    permanently forcing contextual_intruder_groups relationships to 'neutral' regardless of
    real combat engagement. wild_beast_pack's real content perspective (data/content/social/
    perspectives.yaml) lists town_council/hero_guild/etc under contextual_intruder_groups."""
    attacker = (V2EntityBuilder(1).kind("actor").location(0.0, 0.0)
                .identity(faction=Faction.MONSTER_HORDE)
                .identity(role=EntityRole.MONSTER)
                .identity(properties={"faction_id": "wild_beast_pack"})
                .combat(hp=100, atk=10, def_stat=5, attack_range=1, readiness=100.0)
                .build())
    target = (V2EntityBuilder(2).kind("actor").location(1.0, 0.0)
              .identity(faction=Faction.HERO_GUILD)
              .identity(role=EntityRole.HERO)
              .identity(properties={"faction_id": "hero_guild"})
              .combat(hp=100, atk=10, def_stat=5, attack_range=1, readiness=100.0)
              .build())
    # Mutual engagement: attacker's task already targets the defender.
    from src.core.state import TaskComponent
    attacker = replace(attacker, task=TaskComponent(payload={"target_id": 2}))
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    ok, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert ok is True
    assert reason == ReasonCode.LEGAL
