---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260831-HABIT-BIAS-WIRING
phase: done
date: 2026-08-31
tags: [cognition]
---

# TCK-20260831-HABIT-BIAS-WIRING

## Title
Wire the existing HabitBiasService into ActionStyle bias (Earned Habits)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Earned Habits & Behavioral Tendencies. Investigation found the atlas card's premise ("no existing accumulation scaffolding") is factually outdated — HabitMemory and HabitBiasService already implement gradual-accumulation habit bias (±0.1 per outcome, bounded [0,1]) from the archived Phase 16 Emotion/Recovery/Habit domain, but have zero production call sites. It's cheaper and lower-risk to wire this existing service into the already-precedented ActionStyle bias point than to build a new mechanism as the atlas assumed.

## Scope
- Correct the atlas's "no scaffolding" premise in the ticket and scope this as wiring the existing HabitBiasService, not building new accumulation state.
- Add at least one real production consumer of HabitBiasService.apply_habit_bias at the ActionStyle bias point (src/content_semantics/personality.py's get_action_style_for_bravery), closing the current zero-call-site gap.
- Gate the mechanism behind a FeatureMode flag, default OFF.
- Apply habit-accumulation state changes only through the authoritative apply path; keep PersonalityComponent frozen/immutable.
- Make an explicit choice between gradual-accumulation-only vs. also supporting discrete milestone-event marks (e.g. "three near-deaths fighting alone"), since only the gradual variant currently exists in code.

## Out of Scope
- Re-touching the dead ActionStyle sub-branches already removed by TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES — re-check that ticket's rationale before wiring into the same function, do not duplicate its work.
- Building a new discrete milestone-event accumulation mechanism if the gradual-only variant is chosen.

## Acceptance Criteria
- [x] Ticket explicitly corrects the atlas's "no scaffolding" premise and scopes as WIRING HabitBiasService, not building new accumulation state.
- [x] HabitBiasService.apply_habit_bias gains at least one real production consumer at the ActionStyle bias point, closing the current zero-call-site gap.
- [x] Mechanism is gated behind a FeatureMode flag, default OFF.
- [x] PersonalityComponent stays frozen/immutable; habit-accumulation state (HabitMemory or its successor) is applied only through the authoritative apply path.
- [x] Ticket makes an explicit choice between gradual-accumulation-only vs. also supporting discrete milestone-event marks, not left ambiguous.

## Related Tickets
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION
- TCK-20260809-COMBAT-ACTIONSTYLE-WIRING
- TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/cognition.py
- src/domains/emotion/habit_service.py
- src/content_semantics/personality.py
- src/engine/tactical.py
- src/core/enums.py

## Assumptions / Open Questions
- The choice between gradual-accumulation-only and discrete-milestone variants is open and must be made explicit in this ticket.
- Must default OFF via FeatureMode per the Implementation Patterns table.

## Implementation Notes

Implemented per staging_artifacts/TCK-20260831-HABIT-BIAS-WIRING/plan.md, Steps 1-5, in order.

- **Step 1**: Added `"ENABLE_HABIT_BIAS_ACTION_STYLE": FeatureMode.OFF` to
  `FeatureFlagManager.__init__`'s `_flags` dict in `src/domains/optimization/feature_flags.py`,
  with a comment block matching the sibling `ENABLE_CREATURE_TERRITORY_LIFECYCLE`/
  `ENABLE_MEMORY_UPDATE` entries (DEV-002 default-OFF rationale).
- **Step 2**: Added `HABIT_PATTERN_COMBAT_ENGAGEMENT = "combat_engagement"` as a module-level
  constant directly in `src/domains/emotion/habit_service.py`, co-located with
  `HabitBiasService`, per the plan's explicit placement instruction.
- **Step 3**: Created `src/domains/emotion/habit_phase.py` (`HabitBiasUpdatePhase.apply()`),
  mirroring `NearDeathHardeningPhase.apply()`'s read-through-then-replace shape (reads
  `entity_update.cognition_bundle_set`, falling back to `entity.cognition`, before replacing) —
  NOT `MemoryUpdatePhase.run()`'s shape. Calls `HabitBiasService.record_outcome(..., success=False)`
  only, driven by the same `_memory_trigger_events` (`combat_loss`-kind) list `memory_update`
  already builds in `src/engine/pipeline.py`. Wired into
  `AuthoritativeApplyPipeline.refine()` via a new `run_phase("habit_bias_action_style", ...,
  "ENABLE_HABIT_BIAS_ACTION_STYLE")` call placed strictly **after** the existing `memory_update`
  call and **before** `self_model`, satisfying the ordering constraint (verified: it does not
  disturb `tests/architecture/test_memory_update_phase_pipeline_ordering.py`'s
  actor_validity < memory_update < self_model assertion, since that test only checks relative
  substring order of those three specific `run_phase(...)` calls).
- **Step 4a**: `src/engine/tactical.py`'s `TacticalDecisionSystem.evaluate_entity_intent` — added
  a flag-gated live re-derivation of the local `style` variable (feeding the existing
  SKIRMISHER kiting-distance branch) immediately after `style = entity.combat.action_style`,
  using the same direct `state.feature_flags` dict-read pattern already established at
  `src/ai/goals/scorers.py:253` (`GuildNeedScorer.score()`).
- **Step 4b**: `src/engine/movement.py`'s `MovementSystem.resolve_move` — added the identical
  flag-gated live re-derivation immediately before the existing `mode == RETREAT and
  action_style == 2` (EVASIVE) opportunity-attack-suppression check, reading
  `state_or_context.feature_flags` defensively via `getattr(..., None) or {}` since that
  parameter is typed `Any`. Both 4a and 4b landed together in this same run, per the plan's
  explicit requirement that shipping only one recreates the exact flag-ON inconsistency the
  architecture review caught.
- **Step 5**: Added `tests/architecture/test_habit_bias_personality_frozen.py` — confirms no
  `PersonalityUpdate` type exists anywhere in `src/core/updates.py`, `PersonalityComponent`
  stays a frozen dataclass, and neither `tactical.py`'s nor `movement.py`'s changed functions
  construct a `PersonalityComponent`.

**Deviation from the plan's literal Step 4 code snippets**: the plan's Step 2 explicitly places
`HABIT_PATTERN_COMBAT_ENGAGEMENT` in `habit_service.py`, but its Step 4a/4b code snippets show
`from src.domains.emotion.habit_phase import HABIT_PATTERN_COMBAT_ENGAGEMENT` — a plan-internal
inconsistency (habit_phase.py never re-exports the constant in the plan's own Step 3 code). Kept
the constant's single source of truth in `habit_service.py` per Step 2's explicit instruction and
imported it from there in `tactical.py`, `movement.py`, and `habit_phase.py` alike — avoids a
redundant re-export layer with no behavioral difference. Recorded in staging_artifacts's
`plan.md` Deviations section.

All 6 new/extended test files pass; full regression surface named in test_plan.md (habit/emotion
domain, personality/worldbuilding construction-time behavior, tactical/movement/combat suites,
memory pipeline ordering, feature-flag defaults) re-run and green — see Test Summary.

## Test Summary

New tests added (all pass):
- `tests/unit/domains/optimization/` / `tests/unit/config/test_phase10_feature_flags.py` — the
  existing generic `test_all_enhancement_flags_default_to_off_or_shadow` loop test already
  covers the new flag's default-OFF requirement automatically (no new test function needed; no
  count/allowlist assertion required updating).
- `tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py` (new file, 3 tests):
  `test_record_outcome_wired_through_authoritative_pipeline`,
  `test_habit_bias_update_phase_preserves_prior_cognition_bundle_write`,
  `test_habit_bias_action_style_flag_gates_pipeline_phase`.
- `tests/unit/tactical/test_habit_bias_action_style_wiring.py` (new file, 2 tests):
  `test_habit_bias_shifts_action_style_when_flag_on`,
  `test_habit_bias_flag_off_preserves_construction_time_action_style`.
- `tests/unit/movement/test_tactical_movement.py` (extended, 2 new tests):
  `test_habit_bias_shifts_movement_oa_suppression_when_flag_on`,
  `test_habit_bias_flag_off_preserves_movement_oa_suppression`.
- `tests/architecture/test_habit_bias_personality_frozen.py` (new file, 3 tests):
  `test_no_personality_update_type_exists`, `test_personality_component_stays_frozen_dataclass`,
  `test_habit_bias_wiring_never_constructs_personality_component`.

Regression suites re-run, all green (repo-root `.venv`, run from the worktree root):
- `tests/unit/domains/emotion/ tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` — 10 passed
- `tests/unit/content_semantics/test_personality.py tests/unit/worldbuilding/test_world_compiler.py` — 50 passed
- `tests/unit/engine/ tests/unit/combat/ tests/unit/tactical/` — 305 passed, 1 skipped
- `tests/unit/movement/` — 54 passed
- `tests/integration/domains/memory/` — 4 passed
- `tests/integration/pipeline/test_combat_legality_matrix.py` — 14 passed
- `tests/architecture/ -k "habit or personality"` — 3 passed
- `tests/architecture/test_memory_update_phase_pipeline_ordering.py` — 1 passed
- `tests/unit/domains/optimization/ tests/unit/config/test_phase10_feature_flags.py` — 130 passed

Never ran the full suite (`pytest tests/`) per repo convention — scoped to the domains touched.

## Files Changed

- `src/domains/optimization/feature_flags.py` — new `ENABLE_HABIT_BIAS_ACTION_STYLE` flag, default OFF.
- `src/domains/emotion/habit_service.py` — new `HABIT_PATTERN_COMBAT_ENGAGEMENT` constant.
- `src/domains/emotion/habit_phase.py` — new file, `HabitBiasUpdatePhase`.
- `src/engine/pipeline.py` — new `habit_bias_action_style` phase wired after `memory_update`, before `self_model`.
- `src/engine/tactical.py` — live habit-biased `ActionStyle` re-derivation in `evaluate_entity_intent` (Step 4a).
- `src/engine/movement.py` — live habit-biased `ActionStyle` re-derivation in `resolve_move` (Step 4b).
- `docs/mechanics/04_strategic_cognition.md` — §6.3 documents both live ActionStyle consumers and the monotonic-decay-no-recovery behavior (added by Document-Update phase).
- `docs/simulation/domains/emotion_contract.md` — corrected pre-existing `record_outcome` inaccuracy, added production call sites and Domain Interactions rows (added by Document-Update phase).
- `tests/architecture/test_habit_bias_personality_frozen.py` — new file.
- `tests/unit/tactical/test_habit_bias_action_style_wiring.py` — new file.
- `tests/unit/movement/test_tactical_movement.py` — extended with 2 new tests.
- `tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py` — new file.
- `staging_artifacts/TCK-20260831-HABIT-BIAS-WIRING/plan.md` — Deviations section added.
- `tickets/inprogress/TCK-20260831-HABIT-BIAS-WIRING.md` — this file (Implementation Notes, Test Summary, Files Changed, Completion Summary, Status, Acceptance Criteria).

## Completion Summary

Wired the previously-dormant `HabitBiasService` (Phase 16 Emotion/Recovery/Habit domain) into a
real, observable ActionStyle bias: a new `HabitBiasUpdatePhase` records `combat_loss` outcomes
into `HabitMemory.patterns` through the authoritative `entity_update.cognition_bundle_set` apply
path (placed strictly after `memory_update`, before `self_model`, using the same
read-through-then-replace discipline as `NearDeathHardeningPhase`), and both real runtime
`ActionStyle` consumers — `tactical.py`'s SKIRMISHER kiting distance and `movement.py`'s
opportunity-attack suppression on an EVASIVE retreat — now live-re-derive `ActionStyle` from
habit-biased bravery in sync with each other. Everything is gated behind a single new
`ENABLE_HABIT_BIAS_ACTION_STYLE` flag, default OFF, so shipped construction-time behavior is
bit-identical when the flag is off (the default); `PersonalityComponent` remains untouched and
frozen, and no new WorldEventCategory, milestone-event mechanism, or PersonalityUpdate type was
introduced. All 5 acceptance criteria are satisfied; parity ledger and mechanics-doc updates are
deferred to the Parity/Docs-Update phases per the plan's own routing.
