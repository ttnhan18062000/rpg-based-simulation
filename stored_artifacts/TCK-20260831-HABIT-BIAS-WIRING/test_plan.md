---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-HABIT-BIAS-WIRING
artifact_type: test_plan
tags: [cognition]
---

# Test Plan — TCK-20260831-HABIT-BIAS-WIRING

## Regression Surface

Existing tests that must keep passing, verified running today (`.venv` at repo root, run from the
worktree root):

**Unit — habit/emotion domain (all 5 currently pass, confirmed via a scoped run this session):**
- `tests/unit/domains/emotion/test_phase16_habit_bias_service.py::test_habit_bias_service`
- `tests/unit/domains/emotion/test_phase16_habit_memory_model.py::test_habit_memory_model`
- `tests/unit/domains/emotion/test_phase16_emotion_update_service.py`
- `tests/unit/domains/emotion/test_phase16_recovery_readiness_service.py`
- `tests/unit/domains/emotion/test_phase16_emotional_model.py`

**Integration — habit/emotion scenarios:**
- `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py`
  (`test_near_death_prevents_immediate_retry`, `test_repeated_failure_causes_route_switch`,
  `test_opportunity_cost_prevents_selling_needed_material`)

**Unit — ActionStyle/personality (must stay unaffected when the new flag is OFF, the default):**
- `tests/unit/content_semantics/test_personality.py::test_get_action_style_for_bravery_thresholds`
- `tests/unit/worldbuilding/test_world_compiler.py::test_get_action_style_for_bravery_thresholds`
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_faction_bravery_bias_produces_real_action_style_skew`
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_faction_bravery_bias_produces_real_population_skew`

**Unit/Combat — tactical kiting (the real runtime consumer this ticket touches):**
- `tests/unit/combat/test_tactical_legality.py::test_tactical_legality_filtering`
- Any existing kiting-distance tests under `tests/unit/tactical/` /
  `tests/unit/combat/` that assert `MovementMode.RETREAT`/kite-position behavior for
  `SKIRMISHER`-role entities by `ActionStyle` — locate via
  `grep -rl "kite\|KITING" tests/unit/tactical/ tests/unit/combat/` before implementation and
  confirm the exact file set (not enumerated exhaustively here; the investigation did not find a
  test file matching this pattern by name alone).

**Architecture guard:**
- `tests/architecture/test_memory_update_phase_pipeline_ordering.py` — must keep passing unchanged;
  if `HabitMemory`'s write-back follows the `MemoryUpdatePhase`/`cognition_bundle_set` precedent,
  this guard's pipeline-ordering assumptions are directly relevant to where the new phase (or new
  logic inside an existing phase) is inserted.

**Feature flag regression:**
- Any existing test asserting `FeatureFlagManager.get_all_flags()` count/contents (if one exists,
  locate via `grep -rl "get_all_flags" tests/`) will need updating for the new flag — flag as a
  regression-surface touch point, not a behavior bug.

## New Tests Required

Per acceptance criteria:

- **Test name**: `test_habit_bias_service_zero_production_callers_gap_closed` (or equivalent
  assertion embedded in an integration test) — **Category**: unit — **Verifies**: after wiring,
  `HabitBiasService.apply_habit_bias` (and, per the investigation's recommendation,
  `record_outcome`) has at least one real, non-test call site; can be asserted either via a direct
  behavioral test (below) or, if the team wants a structural guard, an architecture-style grep-test
  analogous to other "confirmed zero call sites" checks in this repo. — **Location**:
  `tests/unit/domains/emotion/test_phase16_habit_bias_service.py` (extend) or
  `tests/architecture/`.

- **Test name**: `test_habit_bias_shifts_action_style_when_flag_on` — **Category**: unit —
  **Verifies**: with the new flag set to `ON`, an entity whose `HabitMemory.patterns` contains a
  strongly positive bias for a tag matching an `AGGRESSIVE`-leaning route/action pattern produces a
  higher effective bravery/ActionStyle-favoring outcome than an entity with an empty or negative
  `HabitMemory`, all else equal (same raw `PersonalityComponent.bravery`). — **Location**:
  `tests/unit/content_semantics/test_personality.py` or a new
  `tests/unit/engine/test_habit_bias_action_style_wiring.py`, depending on where the plan phase
  places the re-derivation logic (see investigation's Risks section — recommend the runtime
  `tactical.py` read site, not `get_action_style_for_bravery`'s construction-time call sites).

- **Test name**: `test_habit_bias_flag_off_preserves_construction_time_action_style` —
  **Category**: unit — **Verifies**: with the new flag `OFF` (the default), an entity's ActionStyle
  behavior is bit-identical to current shipped behavior (`SUB-381`'s already-verified
  construction-time thresholds), regardless of what `HabitMemory.patterns` contains — a direct
  regression guard for "gate default OFF" and "do not change OFF-path behavior." — **Location**:
  same file as above.

- **Test name**: `test_record_outcome_wired_through_authoritative_pipeline` (only if the plan
  phase includes wiring `record_outcome`, per the investigation's recommendation) — **Category**:
  integration — **Verifies**: a real per-entity outcome event (e.g. combat loss) results in
  `entity.cognition.memory.habit.patterns` changing via `entity_update.cognition_bundle_set` (not a
  direct `state.entities` mutation), mirroring
  `tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py`'s own
  assertion shape for `CausalMemory`. — **Location**:
  `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` (extend) or a new
  `tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py`.

- **Test name**: `test_personality_component_stays_frozen_after_habit_bias_wiring` —
  **Category**: architecture guard — **Verifies**: `PersonalityComponent` is never constructed with
  altered field values as a side effect of habit-bias wiring (no new write path to
  `bravery`/`greed`/`sociability`/`industry`) — a direct check against the AC's frozen/immutable
  requirement, since there is currently no `PersonalityUpdate` type at all
  (confirmed by investigation) and none should be introduced. — **Location**: `tests/architecture/`.

- **Test name**: `test_habit_bias_action_style_flag_default_off` — **Category**: unit —
  **Verifies**: `FeatureFlagManager().get_flag_mode("<new flag name>") == FeatureMode.OFF` by
  default, matching every other newly-introduced flag except the pre-validated ON exceptions
  documented in `feature_flags.py`. — **Location**:
  `tests/unit/domains/optimization/` (locate existing `feature_flags.py` test file via
  `grep -rl "FeatureFlagManager" tests/unit/`) or a new test in the same suite as the flag list.

## Scoped Pytest Commands

```
# Habit/emotion domain (regression + new unit tests)
python3 -m pytest tests/unit/domains/emotion/ tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py -q

# ActionStyle/personality construction-time behavior (must be unaffected with flag OFF)
python3 -m pytest tests/unit/content_semantics/test_personality.py tests/unit/worldbuilding/test_world_compiler.py -q

# Tactical/combat consumer (the real runtime bias point)
python3 -m pytest tests/unit/tactical/ tests/unit/combat/ -q

# Feature flag manager
python3 -m pytest tests/unit/domains/optimization/ -q

# Architecture guards (memory pipeline ordering + any new frozen-personality guard)
python3 -m pytest tests/architecture/test_memory_update_phase_pipeline_ordering.py tests/architecture/ -k "habit or personality" -q
```

Run with the repo-root `.venv` interpreter from within the worktree
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest ...`) — the worktree's
own `python3` lacks `pydantic` and cannot even load `tests/conftest.py`, confirmed this session.

Never: `pytest tests/` (full-suite run) — always scope to the domains above.

## Anti-Drift Test Guards

- The flag-OFF regression tests above (`test_habit_bias_flag_off_preserves_construction_time_action_style`,
  the existing `test_get_action_style_for_bravery_thresholds` suite) are the primary guard against
  this ticket silently changing default-path gameplay behavior — `SUB-381`'s already-verified
  construction-time ActionStyle skew (e.g. `wild_beast_pack` ≈0.89 bravery → mostly AGGRESSIVE) must
  remain bit-identical with the new flag OFF.
- A guard against re-adding the dead `attack_range`/EVASIVE-reposition sub-branches
  `TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES` removed: re-run
  `tests/unit/combat/test_tactical_legality.py::test_tactical_legality_filtering` (the real
  replacement test cited in `COMB-301`'s own `v2_evidence`) and confirm no new local variable
  resembling the removed `attack_range` computation is introduced in the same function.
  `TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES`'s own re-verification methodology (live
  `is_attack_legal` probe rate, ~28.5%/36.6% on `dungeon_crawl`/`urban_political`) is the
  quantitative anchor if a deeper regression check is warranted.
- A guard against scope creep into the discrete milestone-event variant: no new test should
  reference event-counting/threshold-crossing state (e.g. "N near-deaths") for `HabitMemory` — if
  one appears, it signals the ticket silently expanded into the explicitly-out-of-scope discrete
  variant.
- A guard on `MemoryModel`'s sibling fields (`causal`, `spatial`, `experience`, `combat`, `social`):
  any new test touching `HabitMemory`/`habit_service.py` should not require changes to
  `tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py` or
  `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` — those cover a sibling
  `MemoryModel` field (`causal`) wired by a separate, already-shipped ticket
  (`TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING`) and must stay unaffected by this one.
