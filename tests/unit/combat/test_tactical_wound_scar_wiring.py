"""
TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

Verifies TacticalDecisionSystem.evaluate_entity_intent reads structured
WoundState/ScarState data (via WoundService.get_wound_stat_penalties/
get_scar_stat_penalties) as an independent decision-making signal, additive to
the existing hp_percent/hp_ratio-only checks.
"""
from unittest.mock import patch

from src.core.state import (
    AuthoritativeState, GroupRecord, WoundState, ScarState,
)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.engine.tactical import TacticalDecisionSystem
from src.engine.rpg_depth import WoundService


def _build_entity(
    eid,
    faction,
    *,
    hp=100,
    max_hp=100,
    pos=(0.0, 0.0),
    attack_range=1,
    tactical_role=None,
    wounds=None,
    scars=None,
    group_id=None,
):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    builder = (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(*pos)
        .identity(role=role, faction=faction, group_id=group_id)
        .combat(
            hp=hp,
            max_hp=max_hp,
            attack_range=attack_range,
            readiness=100.0,
            alive=hp > 0,
            tactical_role=tactical_role or "VANGUARD",
            wounds=wounds if wounds is not None else [],
            scars=scars if scars is not None else [],
        )
        .lifecycle(active=True)
    )
    return builder.build()


# The cover-seeking gate's ranged-threat branch needs a candidate tile with no
# line-of-sight to the threat. `terrain[(0, 1)] = "WALL"` blocks the path from
# both (-1, 0) and (0, -1) to a threat at (0, 3) -- (-1, 0) is discovered first
# (dx=-1 sweeps to completion before dx=0 starts in
# PositioningService.find_nearest_cover's dx-major iteration), so cover_pos
# resolves deterministically to (-1.0, 0.0), distinct from the entity's own
# (0.0, 0.0) position.
_COVER_TERRAIN = {(0, 1): "WALL"}
_THREAT_POS = (0.0, 3.0)


def _cover_seeking_state(entity):
    threat = _build_entity(2, Faction.MONSTER_HORDE, pos=_THREAT_POS, attack_range=3)
    return AuthoritativeState(
        tick=1, seed=42, world_time=1,
        entities={entity.id: entity, threat.id: threat},
        terrain=dict(_COVER_TERRAIN),
    )


def test_severe_wound_triggers_cover_seeking_at_high_hp():
    # severity=0.6 wound, matching WoundService.create_wound(damage=60, max_hp=100, ...)'s
    # real output: atk=1, def=1, speed=1, max_hp=6 -> distress sum = 9.0 (>= threshold).
    wound = WoundState(
        id="w1", kind="SLASH", severity=0.6, tick_inflicted=0,
        atk_penalty=1.0, def_penalty=1.0, speed_penalty=1.0, max_hp_penalty=6.0,
    )
    entity = _build_entity(1, Faction.HERO_GUILD, hp=90, max_hp=100, wounds=[wound])
    state = _cover_seeking_state(entity)

    update = TacticalDecisionSystem.evaluate_entity_intent(state, entity)

    assert update.task.payload_set["reason"] == "SEEK_COVER"
    assert update.task.payload_set["target_position"] == (-1.0, 0.0)


def test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch():
    entity = _build_entity(1, Faction.HERO_GUILD, hp=90, max_hp=100, wounds=[])
    state = _cover_seeking_state(entity)

    update = TacticalDecisionSystem.evaluate_entity_intent(state, entity)

    assert update.task.payload_set.get("reason") not in ("SEEK_COVER", "PANIC_RETREAT")


def test_scarred_entity_differs_from_unwounded_entity_at_same_hp_ratio():
    # hp_percent = 0.44: sits above the unscarred 0.4 threshold (A must not trigger)
    # but below the bumped threshold once B's scar_distress = 5.0 -> scar_hp_bump = 0.05
    # -> effective threshold 0.45 > 0.44 (B must trigger).
    scars = [
        ScarState(id="s1", wound_kind="SLASH", tick_created=0, atk_penalty=2.0, def_penalty=2.0, speed_penalty=1.0),
    ]
    assert sum(WoundService.get_scar_stat_penalties(scars).values()) == 5.0

    entity_a = _build_entity(1, Faction.HERO_GUILD, hp=44, max_hp=100, scars=[])
    state_a = _cover_seeking_state(entity_a)
    update_a = TacticalDecisionSystem.evaluate_entity_intent(state_a, entity_a)
    assert update_a.task.payload_set.get("reason") not in ("SEEK_COVER", "PANIC_RETREAT")

    entity_b = _build_entity(1, Faction.HERO_GUILD, hp=44, max_hp=100, scars=scars)
    state_b = _cover_seeking_state(entity_b)
    update_b = TacticalDecisionSystem.evaluate_entity_intent(state_b, entity_b)
    assert update_b.task.payload_set["reason"] == "SEEK_COVER"


def test_protector_guards_wound_distressed_ally_over_healthier_ally():
    protector = _build_entity(1, Faction.HERO_GUILD, pos=(0.0, 0.0), tactical_role="PROTECTOR", group_id=100)
    leader = _build_entity(10, Faction.HERO_GUILD, pos=(5.0, 5.0))

    # Ally X: hp_ratio=0.75 (would not qualify by hp_ratio<0.7 alone), but wound distress
    # at severity=0.4 (atk=1, def=0, speed=0, max_hp=4 -> sum=5.0) meets the guard threshold.
    wound = WoundState(
        id="wX", kind="PIERCE", severity=0.4, tick_inflicted=0,
        atk_penalty=1.0, def_penalty=0.0, speed_penalty=0.0, max_hp_penalty=4.0,
    )
    ally_x = _build_entity(2, Faction.HERO_GUILD, hp=75, max_hp=100, pos=(1.0, 1.0), wounds=[wound])

    # Ally Y: hp_ratio=0.72 (also not <0.7), zero wounds/scars -- must not qualify.
    ally_y = _build_entity(3, Faction.HERO_GUILD, hp=72, max_hp=100, pos=(1.0, 2.0))

    hostile = _build_entity(99, Faction.MONSTER_HORDE, pos=(0.0, 1.0))

    group = GroupRecord(id=100, leader_id=10, member_ids={1, 2, 3, 10}, anchor=(0.0, 0.0), roles={1: "PROTECTOR"})
    state = AuthoritativeState(
        tick=1, seed=1, world_time=1,
        entities={1: protector, 10: leader, 2: ally_x, 3: ally_y, 99: hostile},
        groups={100: group},
    )

    update = TacticalDecisionSystem.evaluate_entity_intent(state, protector)

    assert update.task.payload_set["reason"] == "GUARDING_ALLY"
    assert update.task.payload_set["target_id"] == 2


def test_wound_scar_tactical_reads_reuse_woundservice_aggregators():
    wound = WoundState(
        id="w1", kind="SLASH", severity=0.6, tick_inflicted=0,
        atk_penalty=1.0, def_penalty=1.0, speed_penalty=1.0, max_hp_penalty=6.0,
    )
    scar = ScarState(id="s1", wound_kind="SLASH", tick_created=0, atk_penalty=1.0, def_penalty=1.0, speed_penalty=1.0)
    entity = _build_entity(1, Faction.HERO_GUILD, hp=90, max_hp=100, wounds=[wound], scars=[scar])
    state = _cover_seeking_state(entity)

    with patch.object(
        WoundService, "get_wound_stat_penalties", wraps=WoundService.get_wound_stat_penalties
    ) as wound_spy, patch.object(
        WoundService, "get_scar_stat_penalties", wraps=WoundService.get_scar_stat_penalties
    ) as scar_spy:
        update = TacticalDecisionSystem.evaluate_entity_intent(state, entity)

    assert wound_spy.call_count >= 1
    assert scar_spy.call_count >= 1
    assert update.task.payload_set["reason"] == "SEEK_COVER"
