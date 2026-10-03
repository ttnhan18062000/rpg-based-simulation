---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-LIFE-STAGE-TRANSITIONS
phase: done
date: 2026-08-24
tags: [cognition]
---

# TCK-20260824-LIFE-STAGE-TRANSITIONS

## Title
Implement Life Stage Transitions (Life Stages & Rites of Passage)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
LifeStageService.get_goal_multipliers() already runs unflagged, consumes identity.life_stage, but nothing ever writes that field -- no life_stage_set field exists on IdentityUpdate today. The author wants a new typed field added plus the apply-path work to make it real.

## Scope
- Add IdentityUpdate.life_stage_set: Optional[LifeStage]=None following the exact typed-field pattern of role_set/faction_set/evolution_level_set (not IdentityPatch's generic property_updates dict)
- Implement IdentityPatch.apply() to apply life_stage_set into IdentityComponent.life_stage, and verify ApplyPath._fast_replace_identity does not silently drop it on the fast path
- Implement a concrete age-based transition trigger that fires deterministically; add a test asserting identity.life_stage flips at the defined boundary
- Explicitly resolve (or explicitly defer with rationale) whether the age-based trigger reuses/aligns with cohort.py's get_age_bracket() thresholds (young/adult/elder string brackets) versus the separate LifeStage(str,Enum) (CHILD/ADULT/ELDER) -- the roadmap itself flags this as a blocking duplicate-representation question that must be settled before implementation
- Decide whether compute_elder_attribute_update() (cohort.py, currently a second independent orphan 'elder' stat-penalty mechanism with zero callers) should be wired to the same age signal or remain deliberately separate from LifeStageService's ELDER goal multipliers

## Out of Scope
- The cohort-level aggregate demographics system tested by test_demographics.py -- this ticket concerns per-entity IdentityComponent.life_stage only

## Acceptance Criteria
- [x] IdentityUpdate gains life_stage_set: Optional[LifeStage]=None following the role_set/faction_set precedent exactly
- [x] IdentityPatch.apply() applies life_stage_set into IdentityComponent.life_stage, and ApplyPath._fast_replace_identity is verified not to silently drop it on the fast path
- [x] A concrete age-based transition trigger fires deterministically; a test asserts identity.life_stage flips at the defined boundary
- [x] The investigation/plan explicitly resolves (or explicitly defers with rationale) whether the trigger reuses/aligns with cohort.py's get_age_bracket() thresholds

## Related Tickets
None.

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/ai/life_stage.py
- src/ai/score_modifiers.py
- src/engine/patches.py
- src/engine/apply.py
- src/domains/demographics/cohort.py
- src/core/builder.py

## Assumptions / Open Questions
- The duplicate-representation question (LifeStage enum vs. get_age_bracket() string tiers) must be settled before implementation per the roadmap's own explicit instruction, not discovered mid-ticket
- Whether compute_elder_attribute_update() should be wired to the same age signal as this trigger, or remain a deliberately separate mechanism, is an open decision this ticket must make explicit
- layer set to `strategy` (AI goal hierarchy / bounded cognition) since the driving consumer is LifeStageService.get_goal_multipliers(); the change also touches core/engine apply-path files, but no combined layer exists in the registry

## Implementation Notes

Implemented all 5 plan steps exactly as specified:

1. **`src/core/updates.py`** — Added `LifeStage` to the `src.core.state` import; added
   `IdentityUpdate.life_stage_set: Optional[LifeStage] = None` immediately after
   `evolution_level_set`; updated `is_noop()` to also check `life_stage_set is None`; updated
   `merge()` with the same last-write-wins line pattern used by `role_set`/`faction_set`.
2. **`src/engine/patches.py`** — Added a `ls = new_id.life_stage` local in `IdentityPatch.apply()`
   alongside the other component locals; added `if u_id.life_stage_set is not None: ls =
   u_id.life_stage_set` inside the `if self.identity:` block; added `life_stage=ls` to the final
   `replace()` call kwargs (the branch that previously silently dropped it). **Independently
   confirmed `ApplyPath._fast_replace_identity` (`src/engine/apply.py:512-532`) needs no change**:
   read it directly — it already has a correct `life_stage=id_comp.life_stage` passthrough, and by
   reading the guard condition at `patches.py:218` (`if not self.identity and ...`), confirmed a
   populated `IdentityUpdate` instance has no custom `__bool__` so is always truthy, meaning that
   fast-path branch is provably unreachable whenever `life_stage_set` is populated — the `else`
   `replace()` branch always runs instead, which is exactly what step 2's fix targets.
3. **`src/ai/life_stage.py`** — Added a module-level `_STAGE_ORDINAL` dict (CHILD=0, ADULT=1,
   ELDER=2) and two new static methods on `LifeStageService`: `get_stage_for_age(age_ticks)`
   (duplicates `get_age_bracket()`'s 3000/7000 literals locally, no import from
   `src/domains/demographics/cohort.py`) and `is_forward_transition(current, target)` (ordinal
   comparison, strictly-greater). `get_goal_multipliers()` body untouched.
4. **`src/systems/lifecycle_systems/lifecycle.py`** — Added `IdentityUpdate` to the existing
   `src.core.updates` import and a new `from src.ai.life_stage import LifeStageService` import.
   Inserted the age-based transition check inside the per-entity loop in `resolve_lifecycle()`,
   right after `ent_upd = refined_entity_updates.get(e_id)` and before the death checks: computes
   `target_stage` via `get_stage_for_age(entity.lifecycle.age_ticks)`, gates on
   `is_forward_transition(entity.identity.life_stage, target_stage)`, and if true sets
   `ent_upd.identity.life_stage_set` via `replace()` (never mutates state directly). Verified no
   other writer in this function touches `ent_upd.identity`, so there's no collision with the
   death/succession/heir blocks that follow.
5. **Docs** — Added parity ledger entry `COMB-313` to `docs/parity_ledger/combat_movement.yaml`
   (confirmed `COMB-312` was the live max before writing; `status: verified`, `priority: P1`,
   `test_path` cites the new boundary-flip test). Rewrote the "One possible duplicate system, not
   yet reconciled" bullet in `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (former line
   284) to record the resolution instead of presenting it as still-open, cross-referencing
   COMB-313 and the stored investigation.

Test additions (step 6): new `tests/unit/core/test_identity_update.py` (is_noop/merge coverage
for `life_stage_set`); `test_identity_patch_apply_sets_life_stage` added to
`tests/unit/domains/optimization/test_component_patches.py`;
`test_life_stage_set_survives_full_apply_pipeline` added to
`tests/integration/optimization/test_component_patch_apply_parity.py`;
`test_life_stage_flips_at_age_boundary` and `test_life_stage_transition_is_monotonic_forward_only`
added to `tests/unit/progression/test_lifecycle.py`; new
`tests/unit/strategic/test_life_stage_transitions.py` covering `get_stage_for_age()` boundaries,
`is_forward_transition()` forward/backward/same cases (including the explicit
already-ELDER-fed-a-lower-candidate non-regression case), and a parametrized cross-check against
`get_age_bracket()`'s numeric transition points.

`make knowledge-index-update` could not be run to completion in this sandbox (pre-existing,
already-documented environment gap: no network access to download the HuggingFace embedding
model, plus `tools/knowledge_search.py` lacking the executable bit) — see plan.md Deviations.
`graphify update .` was run successfully instead as the available code-graph refresh.

## Test Summary

Ran the two `test_plan.md`-scoped pytest commands plus the broader `resolve_lifecycle()`-touching
regression surface (observability/event_shapers, event_extractor_world, regional_sovereignty,
force_full_scan_phase_compliance, logic_guards) — all green, no regressions:

- `pytest tests/unit/strategic/ tests/unit/progression/test_lifecycle.py tests/unit/core/
  test_rpg_depth.py tests/unit/core/test_domain_6_hardening.py tests/unit/domains/optimization/
  tests/unit/world/test_demographics.py tests/unit/core/test_identity_update.py -m "not slow"` —
  506 passed.
- `pytest tests/integration/optimization/ tests/integration/pipeline/test_recovery_gaps.py
  tests/integration/pipeline/test_transaction_completion.py
  tests/integration/kernel/test_snapshot_integrity.py -m "not slow"` — 45 passed, 2 deselected.
- `pytest tests/unit/observability/test_event_extractor_world.py
  tests/unit/observability/test_event_shapers.py tests/integration/world/
  test_regional_sovereignty.py tests/integration/optimization/
  test_force_full_scan_phase_compliance.py tests/integrity/test_logic_guards.py -m "not slow"` —
  77 passed, 1 deselected, 1 xfailed.
- All 16 new/changed tests targeted at this ticket individually re-verified passing.

## Files Changed

- `src/core/updates.py`
- `src/engine/patches.py`
- `src/ai/life_stage.py`
- `src/systems/lifecycle_systems/lifecycle.py`
- `docs/parity_ledger/combat_movement.yaml`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`
- `tests/unit/core/test_identity_update.py` (new)
- `tests/unit/domains/optimization/test_component_patches.py`
- `tests/integration/optimization/test_component_patch_apply_parity.py`
- `tests/unit/progression/test_lifecycle.py`
- `tests/unit/strategic/test_life_stage_transitions.py` (new)
- `staging_artifacts/TCK-20260824-LIFE-STAGE-TRANSITIONS/investigation.md` (pre-existing from this
  run's Investigate phase)
- `staging_artifacts/TCK-20260824-LIFE-STAGE-TRANSITIONS/plan.md` (pre-existing from this run's
  Plan phase; Deviations section added during Implement)
- `staging_artifacts/TCK-20260824-LIFE-STAGE-TRANSITIONS/test_plan.md` (pre-existing from this
  run's Plan phase)
- `tickets/inprogress/TCK-20260824-LIFE-STAGE-TRANSITIONS.md` (this file)

## Completion Summary

Made `LifeStageService.get_goal_multipliers()`'s existing but previously-dead
`identity.life_stage` consumer reachable end-to-end. Added a typed
`IdentityUpdate.life_stage_set` field (with correct `is_noop()`/`merge()` handling) and fixed
`IdentityPatch.apply()`'s final `replace()` call, which previously silently dropped any incoming
`life_stage_set` because it never passed `life_stage=...` through to the new `IdentityComponent`.
Added two new pure functions to `LifeStageService` (`get_stage_for_age()`, deliberately
duplicating `get_age_bracket()`'s 3000/7000 tick boundaries rather than importing across the
strategy/demographics layer boundary, and `is_forward_transition()`, an ordinal guard) and wired a
deterministic, monotonic forward-only age-based life-stage trigger into
`LifecycleSystem.resolve_lifecycle()`, the same call site the prior permadeath-lifecycle hotfix
used. `compute_elder_attribute_update()` was deliberately left unwired (Design Decision 2, already
resolved in investigation.md — a real, separate idempotency-guard problem, out of this ticket's
scope). All new and existing regression-surface tests pass; parity ledger entry COMB-313 and the
roadmap's "duplicate system" open item were both updated to record the resolution.
