"""Runtime-evidence program, value-differential axis (TCK-20260921-MECHANISM-PROGRESSION-VALUE-
DIFFERENTIAL-INSTRUMENT): the calibration instrument for the new value-differential methodology
(docs/plans/mechanic_verification_scenarios_proposal.md, new section) -- a distinct axis from
Program A's reachability harness (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-
VERIFICATION). There, both arms differed on whether a precondition was present or absent; here,
both arms run the identical real code path -- only the mechanism's own input value differs -- and
the question is whether that input has any purchase on the outcome.

There is no known "value that provably doesn't matter" for this axis the way
`quest_generation_sourcing` supplied a reachability negative for Program A, so this instrument
must supply its own calibration: a positive control (an input certain to affect the outcome) and a
negative control (an input that provably does NOT feed the mechanism under test), both run before
any real verdict. `LevelingService.recalculate_combat_stats()` (src/progression/leveling.py:76-180)
was chosen as the calibration mechanism because it is read, in full, to be a PURE function of
`AttributeComponent` fields (strength/agility/vitality/endurance), equipment, skills, and traits --
no RNG call anywhere in the function body -- so it structurally cannot hit the determinism/seed-
sensitivity trap peer named (varying one attribute cannot perturb an RNG draw order that doesn't
exist).

Dispatch: `ApplyPath._apply_entity_update()` (src/engine/apply.py:575), a single-entity-scoped call
into the SAME authoritative merge code (`_apply_entity_update_to_dict`, apply.py:583-624) that a
full Kernel tick would run for any entity update -- unlike Program A's `evolution` mechanism (where
the level-up logic lives in a SEPARATE phase, `EvolutionSystem.evaluate()`, that this same direct-
call technique was previously shown to wrongly bypass), `recalculate_combat_stats`'s own
`stats_dirty` trigger and recalculation call (apply.py:593-624) live INSIDE this exact function --
there is no separate phase being skipped. `update.attributes is not None` (apply.py:596) is the
real, unconditional stats_dirty trigger for this update shape.

Three real arms, one baseline:
- Arm A (baseline): AttributeUpdate with all deltas 0 (still triggers stats_dirty -- `attributes is
  not None`, not "attributes changed" -- confirming a same-value update is itself inert).
- Arm B (agility +10 only): readiness_speed_scaling's own positive control (readiness_speed must
  move by the documented formula) and derived_stats's own negative control (max_hp/atk/def_stat
  must NOT move -- agility is not an input to any of those three formulas).
- Arm C (vitality +10, strength +10, agility fixed): derived_stats's own positive control (max_hp
  and atk must move by the documented formulas) and readiness_speed_scaling's own negative control
  (readiness_speed must NOT move -- neither vitality nor strength is an input to that formula).
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.apply import ApplyPath
from src.core.updates import EntityUpdate, AttributeUpdate

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _apply_attribute_delta(*, agility_delta=0, vitality_delta=0, strength_delta=0):
    state = _compile_world()
    goblin = state.entities[GOBLIN_ID]
    update = EntityUpdate(
        entity_id=GOBLIN_ID,
        attributes=AttributeUpdate(
            agility_delta=agility_delta,
            vitality_delta=vitality_delta,
            strength_delta=strength_delta,
        ),
    )
    return ApplyPath._apply_entity_update(goblin, update)


def test_baseline_zero_delta_attribute_update_is_deterministic_and_repeatable():
    """Sanity check before any real differential claim: two independent zero-delta apply calls
    against the same compiled entity must produce IDENTICAL combat stats -- confirms the harness
    itself introduces no non-determinism before any control is read as meaningful.

    Note (real, separate finding, NOT re-tested here -- see
    TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS): a zero-delta apply does NOT
    reproduce the entity's own AS-SPAWNED combat stats. `apply.py`'s stats_dirty call site
    (apply.py:616-624) calls `SkillScalingService.get_effective_stats()` without ever passing
    base_hp/base_atk/base_def, so recalculation always uses the function's generic defaults
    (100/10/5) -- this goblin's own spawned max_hp=35 (a species-specific base) is silently
    replaced with 112 the moment ANY stats_dirty trigger fires. This does not affect the
    arm-to-arm delta assertions below (both arms of every comparison go through the identical
    default-base recalculation), so this instrument's own value-differential verdicts are sound;
    it is a materially different, real defect, filed separately rather than fixed here."""
    result_a = _apply_attribute_delta()
    result_b = _apply_attribute_delta()

    assert result_a.combat.readiness_speed == result_b.combat.readiness_speed
    assert result_a.combat.max_hp == result_b.combat.max_hp
    assert result_a.combat.atk == result_b.combat.atk
    assert result_a.combat.def_stat == result_b.combat.def_stat


def test_agility_changes_readiness_speed_by_the_documented_formula():
    """Positive control, readiness_speed_scaling: readiness_speed = max(1.0, 10.0 + (agility -
    5) * 1.0) -- a +10 agility delta must move readiness_speed by exactly +10.0."""
    baseline = _apply_attribute_delta()
    varied = _apply_attribute_delta(agility_delta=10)

    assert varied.combat.readiness_speed == baseline.combat.readiness_speed + 10.0, (
        f"readiness_speed_scaling mechanic: expected +10 agility to move readiness_speed by "
        f"exactly +10.0 (baseline {baseline.combat.readiness_speed}), got "
        f"{varied.combat.readiness_speed}."
    )


def test_agility_does_not_change_derived_combat_stats():
    """Negative control, derived_stats: agility is not an input to max_hp/atk/def_stat's own
    formulas -- varying it must leave all three unchanged, proving this instrument does not report
    a difference whenever anything is perturbed."""
    baseline = _apply_attribute_delta()
    varied = _apply_attribute_delta(agility_delta=10)

    assert varied.combat.max_hp == baseline.combat.max_hp, (
        "derived_stats mechanic negative control: agility delta must not move max_hp, but it did "
        f"({baseline.combat.max_hp} -> {varied.combat.max_hp})."
    )
    assert varied.combat.atk == baseline.combat.atk, (
        "derived_stats mechanic negative control: agility delta must not move atk, but it did "
        f"({baseline.combat.atk} -> {varied.combat.atk})."
    )
    assert varied.combat.def_stat == baseline.combat.def_stat, (
        "derived_stats mechanic negative control: agility delta must not move def_stat, but it "
        f"did ({baseline.combat.def_stat} -> {varied.combat.def_stat})."
    )


def test_vitality_and_strength_change_derived_combat_stats_by_the_documented_formula():
    """Positive control, derived_stats: max_hp = base_hp + (vitality * 2) + int(endurance * 0.5);
    atk = base_atk + int(strength * 0.5). A +10 vitality delta must move max_hp by exactly +20; a
    +10 strength delta must move atk by exactly +5 (int(10 * 0.5))."""
    baseline = _apply_attribute_delta()
    varied = _apply_attribute_delta(vitality_delta=10, strength_delta=10)

    assert varied.combat.max_hp == baseline.combat.max_hp + 20, (
        f"derived_stats mechanic: expected +10 vitality to move max_hp by exactly +20 (baseline "
        f"{baseline.combat.max_hp}), got {varied.combat.max_hp}."
    )
    assert varied.combat.atk == baseline.combat.atk + 5, (
        f"derived_stats mechanic: expected +10 strength to move atk by exactly +5 (baseline "
        f"{baseline.combat.atk}), got {varied.combat.atk}."
    )


def test_vitality_and_strength_do_not_change_readiness_speed():
    """Negative control, readiness_speed_scaling: neither vitality nor strength is an input to
    readiness_speed's own formula -- varying both together must leave it unchanged."""
    baseline = _apply_attribute_delta()
    varied = _apply_attribute_delta(vitality_delta=10, strength_delta=10)

    assert varied.combat.readiness_speed == baseline.combat.readiness_speed, (
        "readiness_speed_scaling mechanic negative control: vitality/strength deltas must not "
        f"move readiness_speed, but it did ({baseline.combat.readiness_speed} -> "
        f"{varied.combat.readiness_speed})."
    )
