---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
artifact_type: test_plan
tags: [combat]
---

# Test Plan — TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Regression Surface

Existing tests that must keep passing (all directly exercise `TacticalDecisionSystem.
evaluate_entity_intent` or the `WoundService`/`SkillScalingService` aggregators this ticket must
reuse without modifying):

**Unit — tactical decision:**
- `tests/unit/combat/test_engagement_behavior.py` — `test_attack_vs_pursuit_intent`,
  `test_retreat_behavior` (the existing hp_percent<0.15 `PANIC_RETREAT` path — must still fire for
  an unwounded entity at low HP, unchanged), `test_target_stickiness`
- `tests/unit/combat/test_tactical_hardening.py` — `test_frozen_state_mutation_tripwire`,
  `test_tactical_legality_envelope_mock`
- `tests/unit/combat/test_tactical_legality.py`
- `tests/unit/combat/test_target_selection_contract.py::test_target_selection_priority`
- `tests/unit/combat/test_anti_stalemate.py` — `test_stalemate_break`,
  `test_stale_ticks_increment`
- `tests/unit/movement/test_tactical_movement.py`
- `tests/unit/movement/test_mob_leashing.py`
- `tests/unit/tactical/test_target_stickiness.py`
- `tests/unit/tactical/test_objective_pursuit_coverage.py`
- `tests/unit/social/test_domain_7_social.py` — `test_protector_guarding` (the *different*,
  no-hostiles PROTECTOR guard branch at `tactical.py:312-331` — must remain unaffected by any new
  logic added to the 492-519 branch)

**Unit — wound/scar aggregators (must not be modified, only reused):**
- `tests/unit/core/test_rpg_depth.py::TestWoundInfliction` (`test_wound_stat_impact`,
  `test_wound_cumulative_penalties`, `test_healed_wound_not_penalized`)
- `tests/unit/core/test_rpg_depth.py::TestScarPermanence` (`test_scar_permanence`,
  `test_scar_lesser_penalty`, `test_scar_cumulative_penalties`)
- `tests/unit/core/test_rpg_depth.py::TestEffectiveStats` (`test_effective_stats_with_wounds`,
  `test_effective_stats_with_scars`, `test_evasion_capped`,
  `test_get_effective_stats_applies_breakthrough_attribute_bonus`,
  `test_get_effective_stats_no_breakthroughs_unchanged`)

**Integration — combat/wound production path (must stay unaffected, this ticket is decision-only):**
- `tests/integration/combat/test_wound_healing_permanence.py`
- `tests/unit/combat/test_direct_combat_outcomes.py` —
  `test_wound_penalties_scale_with_severity_through_live_combat_path`,
  `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path`

**Architecture / read-only guards:**
- `tests/unit/core/test_read_only_guard.py`
- `tests/integrity/test_logic_guards.py`

## New Tests Required

Per acceptance criteria, add to `tests/unit/combat/test_engagement_behavior.py` (or a new sibling
file if the planner prefers, e.g. `tests/unit/combat/test_tactical_wound_scar_wiring.py` — follow
whatever the plan.md decides; either location keeps these in the existing tactical-decision test
family):

1. **`test_severe_wound_triggers_cover_seeking_or_retreat_at_high_hp`**
   - Category: unit
   - Verifies AC #1: an entity with `hp_percent` well above 0.4 (e.g. hp=90/max_hp=100) but a
     `WoundState` at/above whatever severity threshold `plan.md` selects (built via
     `V2EntityBuilder(...).combat(hp=90, max_hp=100, wounds=[WoundState(...)])`) still triggers the
     cover-seeking (`SEEK_COVER`) or retreat (`PANIC_RETREAT`/equivalent new reason) branch when a
     ranged hostile is present — proving the new branch fires independently of/earlier than the
     existing `hp_percent < 0.4` gate, not merely alongside it once HP also happens to be low.
   - Where: `tests/unit/combat/test_engagement_behavior.py` (or the planner's chosen new file)

2. **`test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch`** (negative control, guards
   against a threshold that's actually just re-deriving hp_percent)
   - Category: unit
   - Verifies the new branch does not fire for an entity with identical HP/max_hp but an empty
     `wounds` list — isolates that the new trigger is genuinely wound-driven, not accidentally
     re-implementing the existing hp_percent check under a new name.
   - Where: same file as test 1

3. **`test_protector_guards_wounded_ally_over_healthier_higher_hp_ratio_ally`**
   - Category: unit
   - Verifies AC #2: with hostiles present (reaching the `tactical.py:492-519` branch, not the
     312-331 no-hostiles branch — see investigation.md's Anti-Drift Hazards), a PROTECTOR entity in
     a `GroupRecord` chooses to guard an ally whose `hp_ratio` alone would *not* cross the existing
     0.7/0.8 thresholds but who carries a wound/scar of sufficient severity, over an ally with a
     lower raw `hp_ratio` but no wounds/scars — proving wound/scar severity is consulted as an
     "additional signal," not just `hp_ratio`.
   - Where: same file as test 1 (or `tests/unit/social/test_domain_7_social.py` if the planner
     prefers to keep it beside the existing `test_protector_guarding`, given the GroupRecord
     pattern is copied from there — planner's call)

4. **`test_scarred_entity_differs_from_unwounded_entity_at_same_hp_ratio`**
   - Category: unit
   - Verifies AC #3: two entities with identical `hp`/`max_hp` (so identical `hp_percent`), one with
     a hand-constructed `ScarState` (via `V2EntityBuilder(...).combat(scars=[ScarState(...)])`,
     since scars have zero production producers — see investigation.md) and one without, produce a
     measurably different tactical decision/outcome (different `work_kind_set`/`payload_set["reason"]`,
     or the scarred entity reaching the wound/scar branch while the unscarred one does not).
   - Where: same file as test 1

5. **`test_wound_scar_tactical_reads_reuse_woundservice_aggregators`**
   - Category: unit (architecture-guard-flavored — asserts reuse, not re-derivation)
   - Verifies AC #4: patches/spies on `WoundService.get_wound_stat_penalties` and
     `WoundService.get_scar_stat_penalties` (e.g. via `unittest.mock.patch` on
     `src.engine.rpg_depth.WoundService`) and asserts at least one is actually called when
     `evaluate_entity_intent` runs against a wounded/scarred entity — guards against a future edit
     silently swapping back to an inline re-derivation that happens to produce the same test output.
   - Where: same file as test 1

## Scoped Pytest Commands

```
pytest tests/unit/combat/ tests/unit/movement/ tests/unit/tactical/ tests/unit/social/test_domain_7_social.py tests/unit/core/test_rpg_depth.py tests/unit/core/test_read_only_guard.py -v -m "not slow"
```

Follow-up wider check (integration layer, confirms the producer pipeline this ticket depends on but
does not modify is still intact):

```
pytest tests/integration/combat/ -v -m "not slow"
```

Never: `pytest tests/` (repo-wide) — scoped per project Testing Rule to the combat/tactical/social
domains touched by this ticket.

## Anti-Drift Test Guards

- **`test_retreat_behavior`** (`tests/unit/combat/test_engagement_behavior.py`, existing, hp=10 /
  hp_percent=0.1, no wounds) must still return `PANIC_RETREAT` to `(0.0, 0.0)` unchanged — proves
  the new wound/scar branch is additive, not a replacement of the existing hp_percent gate (guards
  AC #1's "independently of" language from silently becoming "instead of").
- **`test_protector_guarding`** (`tests/unit/social/test_domain_7_social.py`, existing, no
  hostiles) must still return `CONTRACT_OBLIGATION_GUARD`/leader `target_id` unchanged — proves the
  312-331 no-hostiles PROTECTOR branch is untouched by changes scoped to the 492-519
  hostiles-present branch.
- **Test 2 above** (`test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch`) is itself an
  anti-drift guard: it would catch an implementation that quietly widens the existing hp_percent
  threshold (e.g. from `< 0.4` to `< 0.5`) instead of genuinely adding a wound-driven trigger.
- **`TestWoundInfliction`/`TestScarPermanence`/`TestEffectiveStats`** (`tests/unit/core/
  test_rpg_depth.py`) passing unmodified guards against accidental edits to
  `WoundService.create_wound()`/`get_wound_stat_penalties()`/`get_scar_stat_penalties()`/
  `SkillScalingService.get_effective_stats()` — none of which this ticket is scoped to touch.
- **`test_wound_penalties_scale_with_severity_through_live_combat_path`** and
  `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path`
  (`tests/unit/combat/test_direct_combat_outcomes.py`) passing unmodified guards the producer
  pipeline (`combat.py::_get_wound_infliction`) this ticket must not touch.
- **Test 5 above** (aggregator-reuse spy test) is the direct machine check for AC #4 — without it,
  a future refactor could silently reintroduce inline penalty math in `tactical.py` and no other
  test in this plan would necessarily catch it (output-equivalent inline math would still pass
  tests 1-4).
- **`tests/unit/core/test_read_only_guard.py`** / **`tests/integrity/test_logic_guards.py`** guard
  against the new branches accidentally mutating `entity.combat.wounds`/`.scars` or any other
  passed-in state instead of staying strictly read-only, per the Core Boundaries architecture rule.
