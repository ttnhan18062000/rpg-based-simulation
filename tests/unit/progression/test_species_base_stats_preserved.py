"""
TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS

A `stats_dirty` recalculation must reproduce an entity's spawned combat stats (stat profiles
declare FINAL spawned values, the derivation treats its base as a term attributes are added to),
and a near-death hardening grant must survive it.

The stored base is the per-entity RESIDUAL `spawned stat - attribute contribution`. It is
unclamped and may be negative. Expected values below are written out by hand: 112 is the original
bug (generic 100 baseline) and 47 is the trap (profile value passed through as the base).
"""
from __future__ import annotations

import os
from dataclasses import fields, replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.derived_stats import attribute_stat_terms, residual_base_terms
from src.core.state import AuthoritativeState, CombatComponent
from src.core.updates import AttributeUpdate, CombatUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase
from src.engine.rpg_depth import SkillScalingService
from src.progression.leveling import LevelingService

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
SEED = 42
GOBLIN_ID = 1


def _compile(world_id: str):
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(world_id)
    state, _ = WorldCompiler.compile(spec, SEED, context=context)
    return state


@pytest.fixture(scope="module")
def goblin_state():
    return _compile(WORLD_ID)


def _recalc(entity, update: EntityUpdate):
    """Run one entity through the real apply path and return its resulting CombatComponent."""
    from src.config.profiles import PROD_SMALL

    state = AuthoritativeState(tick=0, seed=SEED, entities={entity.id: entity})
    changes = ApplyPath._compute_entity_changes(
        entity, update, 1, PROD_SMALL.cadence, False, False, [], state
    )
    return changes.get("combat", entity.combat)


def _from_scratch_max_hp(entity, combat) -> int:
    return SkillScalingService.get_effective_stats(
        entity.attributes, entity.equipment,
        wounds=combat.wounds, scars=combat.scars,
        learned_skills=entity.identity.learned_skills, traits=entity.identity.traits,
        current_role=combat.tactical_role,
        base_hp=combat.base_hp, base_atk=combat.base_atk,
        base_def=combat.base_def, base_evasion=combat.base_evasion,
        permanent_max_hp_bonus=combat.permanent_max_hp_bonus,
    )["max_hp"]


# --- T1 / T2: spawn is unchanged and the stored base is the residual -------------------------

def test_goblin_scout_spawn_stats_unchanged_and_base_is_residual(goblin_state):
    c = goblin_state.entities[GOBLIN_ID].combat
    assert (c.max_hp, c.atk, c.def_stat, c.evasion) == (35, 8, 2, 0.05)
    # vitality=endurance=strength=agility=5 -> contributions 12 / 2 / 1 / 0.005
    assert (c.base_hp, c.base_atk, c.base_def) == (23, 6, 1)
    assert c.base_evasion == pytest.approx(0.045)
    assert c.permanent_max_hp_bonus == 0


def test_derivation_inverts_the_residual(goblin_state):
    e = goblin_state.entities[GOBLIN_ID]
    c = e.combat
    out = LevelingService.recalculate_combat_stats(
        e.attributes, base_hp=c.base_hp, base_atk=c.base_atk,
        base_def=c.base_def, base_evasion=c.base_evasion,
    )
    assert out["max_hp"] == 35
    assert out["atk"] == 8
    assert out["def_stat"] == 2
    assert out["evasion"] == pytest.approx(0.05)


# --- T3: REGRESSION-CRITICAL — a stats_dirty trigger no longer erodes the species base -------

def test_stats_dirty_trigger_does_not_erode_species_base(goblin_state):
    e = goblin_state.entities[GOBLIN_ID]
    out = _recalc(e, EntityUpdate(entity_id=e.id, attributes=AttributeUpdate()))
    assert out.max_hp not in (112, 47)  # 112 = original bug, 47 = profile-value-as-base trap
    assert out.max_hp == 35
    assert (out.atk, out.def_stat) == (8, 2)
    assert out.evasion == pytest.approx(0.05)


# --- T4: attribute changes now propagate against the species base ----------------------------

def test_vitality_change_propagates_against_species_base(goblin_state):
    e = goblin_state.entities[GOBLIN_ID]
    out = _recalc(e, EntityUpdate(entity_id=e.id, attributes=AttributeUpdate(vitality_delta=2)))
    assert out.max_hp == 35 + 4  # base 23 + vit(7)*2 + int(end 5*0.5)=2 -> 39, not 112-ish
    assert out.max_hp not in (112, 47)


# --- T5: REGRESSION-CRITICAL — hardening grants +5, accumulates, and survives a recalc -------

def _harden(entity):
    state = AuthoritativeState(tick=0, seed=SEED, entities={entity.id: entity})
    # leave 1 HP: projected hp <= 10% of max_hp triggers hardening
    hp_delta = -(entity.combat.hp - 1)
    update = StateUpdate(entity_updates={
        entity.id: EntityUpdate(entity_id=entity.id, combat=CombatUpdate(hp_delta=hp_delta)),
    })
    refined = NearDeathHardeningPhase.apply(state, update)
    return refined.entity_updates[entity.id]


def _apply_combat(entity, combat_update: CombatUpdate):
    return _recalc(entity, EntityUpdate(entity_id=entity.id, combat=combat_update))


def test_hardening_grants_five_accumulates_and_survives_recalc(goblin_state):
    e = goblin_state.entities[GOBLIN_ID]
    e = replace(e, combat=replace(e.combat, hp=e.combat.max_hp))

    upd1 = _harden(e)
    assert upd1.combat.max_hp_delta == 5
    assert upd1.combat.permanent_max_hp_bonus_delta == 5
    c1 = _recalc(e, upd1)
    assert c1.max_hp == 40 and c1.permanent_max_hp_bonus == 5
    e1 = replace(e, combat=replace(c1, hp=c1.max_hp))

    upd2 = _harden(e1)
    c2 = _recalc(e1, upd2)
    assert c2.max_hp == 45 and c2.permanent_max_hp_bonus == 10
    e2 = replace(e1, combat=replace(c2, hp=c2.max_hp))

    # An unrelated dirty trigger must keep the accumulated grant: 23 + 12 + 10
    out = _recalc(e2, EntityUpdate(entity_id=e2.id, attributes=AttributeUpdate()))
    assert out.max_hp == 45
    assert out.permanent_max_hp_bonus == 10


# --- Redundancy-drift guard (the price of keeping max_hp_delta alongside the accumulator) ----

def test_from_scratch_derivation_equals_incrementally_maintained_max_hp(goblin_state):
    """
    Hardening writes max_hp_delta AND the accumulator; the derivation is the definition and the
    incremental max_hp is a maintained view of it. This test is what makes that agreement a
    checked invariant (OWN-01: no *independent* conflicting truth) rather than a hope.

    It holds ONLY because the accumulator enters the derivation as a linear additive term. If
    hardening ever becomes percentage-based, capped, or attribute-dependent, the materialised-view
    argument behind keeping both writers breaks: revisit the whole single-writer question
    (TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS), do not just update
    an expected number here.
    """
    e = goblin_state.entities[GOBLIN_ID]
    e = replace(e, combat=replace(e.combat, hp=e.combat.max_hp))
    assert _from_scratch_max_hp(e, e.combat) == e.combat.max_hp  # 0 grants

    c1 = _recalc(e, _harden(e))
    e1 = replace(e, combat=replace(c1, hp=c1.max_hp))
    assert _from_scratch_max_hp(e1, c1) == c1.max_hp  # 1 grant

    c2 = _recalc(e1, _harden(e1))
    assert _from_scratch_max_hp(e1, c2) == c2.max_hp  # 2 grants


# --- T6: the base is immutable and unclamped -------------------------------------------------

def test_base_terms_immutable_across_recalc_hardening_and_attribute_change(goblin_state):
    e = goblin_state.entities[GOBLIN_ID]
    before = (e.combat.base_hp, e.combat.base_atk, e.combat.base_def, e.combat.base_evasion)
    for upd in (
        EntityUpdate(entity_id=e.id, attributes=AttributeUpdate()),
        EntityUpdate(entity_id=e.id, attributes=AttributeUpdate(vitality_delta=3, strength_delta=2)),
        _harden(replace(e, combat=replace(e.combat, hp=e.combat.max_hp))),
    ):
        c = _recalc(e, upd)
        assert (c.base_hp, c.base_atk, c.base_def, c.base_evasion) == before


def test_residual_is_unclamped_and_round_trips_when_negative():
    e = (
        V2EntityBuilder(7).kind("worker")
        .attributes(vitality=5, endurance=5, strength=5, agility=5)
        .combat(hp=20, max_hp=20, atk=3, def_stat=0)
        .spawn_combat_stats_are_final()
        .build()
    )
    assert e.combat.base_def == -1  # worker: def 0 against int(5*0.3)=1 contribution
    out = LevelingService.recalculate_combat_stats(
        e.attributes, base_hp=e.combat.base_hp, base_atk=e.combat.base_atk,
        base_def=e.combat.base_def, base_evasion=e.combat.base_evasion,
    )
    assert out["def_stat"] == 0  # not 1: the clamp drift is gone


def test_residual_independent_of_builder_call_order():
    a = (V2EntityBuilder(1).attributes(vitality=9).combat(max_hp=50).spawn_combat_stats_are_final().build())
    b = (V2EntityBuilder(1).combat(max_hp=50).attributes(vitality=9).spawn_combat_stats_are_final().build())
    assert a.combat.base_hp == b.combat.base_hp == 50 - (9 * 2 + int(5 * 0.5))


# --- T7: the residual and the derivation share one attribute-term definition -----------------

def test_residual_and_derivation_share_attribute_terms():
    e = V2EntityBuilder(3).attributes(strength=11, vitality=13, endurance=7, agility=9).combat(
        max_hp=77, atk=19, def_stat=6, evasion=0.11).spawn_combat_stats_are_final().build()
    hp_t, atk_t, def_t, eva_t = attribute_stat_terms(e.attributes)
    assert residual_base_terms(e.combat, e.attributes) == (
        77 - hp_t, 19 - atk_t, 6 - def_t, 0.11 - eva_t)
    out = LevelingService.recalculate_combat_stats(
        e.attributes, base_hp=e.combat.base_hp, base_atk=e.combat.base_atk,
        base_def=e.combat.base_def, base_evasion=e.combat.base_evasion,
    )
    assert (out["max_hp"], out["atk"], out["def_stat"]) == (77, 19, 6)
    assert out["evasion"] == pytest.approx(0.11)


@pytest.mark.parametrize("world_id", [
    "frontier_living_world", "crowded_frontier", "quest_dense_frontier",
])
def test_round_trip_identity_for_every_entity(world_id):
    """The derivation reproduces max_hp/atk/def/evasion of EVERY spawned entity exactly."""
    state = _compile(world_id)
    assert state.entities
    for e in state.entities.values():
        c = e.combat
        out = LevelingService.recalculate_combat_stats(
            e.attributes, base_hp=c.base_hp, base_atk=c.base_atk,
            base_def=c.base_def, base_evasion=c.base_evasion,
            permanent_max_hp_bonus=c.permanent_max_hp_bonus,
        )
        assert out["max_hp"] == c.max_hp, (e.id, e.kind)
        assert out["atk"] == c.atk, (e.id, e.kind)
        assert out["def_stat"] == c.def_stat, (e.id, e.kind)
        assert out["evasion"] == pytest.approx(c.evasion, abs=1e-12), (e.id, e.kind)


# --- T8: serialization / freeze / canonical --------------------------------------------------

def test_new_fields_in_canonical_dict_and_hash_stable(goblin_state):
    from src.engine.checkpoint import CanonicalStateHasher

    c = goblin_state.entities[GOBLIN_ID].combat
    d = c.to_canonical_dict()
    for k in ("base_hp", "base_atk", "base_def", "base_evasion", "permanent_max_hp_bonus"):
        assert d[k] == getattr(c, k)
    h1 = CanonicalStateHasher.get_hash(goblin_state)
    h2 = CanonicalStateHasher.get_hash(_compile(WORLD_ID))
    assert h1 == h2


def test_every_combat_component_field_survives_to_readonly():
    """EntityState.to_readonly() re-lists CombatComponent fields by hand: a field added to the
    component and not carried there is silently reset. Set every field to a non-default value."""
    sentinel = {
        "hp": 11, "max_hp": 12, "atk": 13, "def_stat": 14, "speed": 15, "range": 16,
        "evasion": 0.17, "move_cost": 18.0, "tactical_role": "SKIRMISHER", "action_style": 2,
        "alive": False, "readiness": 19.0, "readiness_speed": 20.0,
        "base_hp": -21, "base_atk": 22, "base_def": -23, "base_evasion": 0.24,
        "permanent_max_hp_bonus": 25,
    }
    skip = {"wounds", "scars", "status_effects", "latest_result", "_canonical_cache"}
    assert {f.name for f in fields(CombatComponent)} - skip == set(sentinel), "update sentinel"
    e = V2EntityBuilder(9).build()
    e = replace(e, combat=replace(e.combat, **sentinel))  # list wounds -> to_readonly() rebuilds
    frozen = e.to_readonly()
    for k, v in sentinel.items():
        assert getattr(frozen.combat, k) == v, k


# --- T9: the hardening event reports the entity's real post-tick max_hp ----------------------

def test_hardening_event_max_hp_matches_actual(goblin_state):
    e = goblin_state.entities[GOBLIN_ID]
    e = replace(e, combat=replace(e.combat, hp=e.combat.max_hp))
    upd = _harden(e)
    actual = _recalc(e, upd).max_hp
    # event_shapers reconstructs max_hp as prior + CombatUpdate.max_hp_delta; hardening still writes it
    assert e.combat.max_hp + upd.combat.max_hp_delta == actual


def test_builder_without_spawn_opt_in_keeps_generic_baseline():
    """Tests/scenarios/generators declare base terms, not final spawned values: no residual."""
    e = V2EntityBuilder(5).combat(hp=100, max_hp=100, atk=10, def_stat=5).build()
    c = e.combat
    assert (c.base_hp, c.base_atk, c.base_def, c.base_evasion) == (100, 10, 5, 0.05)
