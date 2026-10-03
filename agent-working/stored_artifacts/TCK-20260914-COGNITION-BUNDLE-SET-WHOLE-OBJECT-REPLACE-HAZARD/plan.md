# Plan — TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD

Decision (peer-approved, see investigation.md's "Recommendation" section): **Option 2 (mandatory
typed write helper) + Option 3 (architecture-test guardrail), not Option 1 (recursive per-subfield
merge)**. Option 1 is not warranted: its one concrete justification (two writers racing different
keys of the same `opponent_stats` dict in the same tick) was verified empirically to already be
handled correctly by Option 2, because every real writer today shares the pipeline's single,
linearly-threaded `update`/`tick_update` accumulator.

## Step 1 — Recommended first action (not conditional on the option decision)
`src/domains/memory/phase.py::MemoryUpdatePhase.apply()` reads through any `cognition_bundle_set`
an earlier phase already staged this same tick, closing the one remaining "safe only by ordering"
writer. **Done** in commit `6817f9d9e`.

## Step 2 — Verify the dict-key-collision claim empirically (peer's direct challenge)
Built a real 3-entity pipeline-level probe (`AuthoritativeApplyPipeline.refine()`, a real `ATTACK`
task through `action_routing` + a passive nearest-hostile evaluation through `combat_engagement`,
same tick, same attacker, two different opponent ids) to test whether two writers touching
different keys of the same `opponent_stats` dict actually collide. Result: both keys landed
correctly — `_read_through_cognition()` alone handles it, because `action_routing` and
`combat_engagement` share the same pipeline-threaded accumulator. **Done**; investigation.md
corrected accordingly in commit `a8c425dc7`.

## Step 3 — Build Option 2: `src/core/cognition_write.py::read_through_cognition()`
A single, minimal, shape-agnostic helper: `read_through_cognition(fallback_cognition,
*candidate_updates)` returns the first non-`None` `cognition_bundle_set` among the given
`Optional[EntityUpdate]` candidates (priority order = argument order), else the fallback. Callers
do their own `.get(entity_id)` lookups against whatever accumulator shape they hold — the helper
stays agnostic to that shape rather than guessing it (`combat_engagement/phase.py`'s own two-level
accumulator vs. the single flat `dict(update.entity_updates)` every other writer uses).

Migrate every real writer to call it instead of hand-rolling the same lookup:
- `src/domains/memory/phase.py::MemoryUpdatePhase.apply()`
- `src/domains/combat_engagement/phase.py::_read_through_cognition()` (now a thin, shape-specific
  wrapper delegating to the shared helper)
- `src/domains/emotion/habit_phase.py::HabitBiasUpdatePhase.apply()`
- `src/engine/pipeline_phases/hardening.py::NearDeathHardeningPhase.apply()`
- `src/systems/lifecycle_systems/lifecycle.py::LifecycleSystem._seed_dying_wish()`
- `src/strategy/role_model_phase.py::RoleModelSelectionPhase.apply()`
- `src/engine/pipeline_phases/movement.py::MovementPhase.route_movement_intent()`
- `src/engine/quests.py::QuestSystem.enforce()` (ESCORT reputation write) — found during this
  build, not in the ticket's original enumeration: uses a `replace_kwargs["cognition_bundle_set"]
  = ...` dict-splat shape rather than a literal keyword, so it was invisible to a naive
  keyword-only AST check (see Step 4). Already safe before this change; migrated for consistency
  and so Option 3's guardrail has exactly one sanctioned shape to point to.

Deliberately NOT touched: `src/engine/domain/combat_actions.py` and
`src/domains/combat_engagement/learning_outcome.py` — these are safe by a different, real
mechanism (`ActionRoutingPhase`'s own sliding-state materialization patches the entity before these
functions ever see it), not by an explicit read-through call, and don't need one.
`src/engine/patches.py::CognitionPatch.merge()` stays untouched and dormant, per the investigation's
own recommendation (no live collision site to fix).

## Step 4 — Build Option 3: architecture-test guardrail
`tests/architecture/test_cognition_bundle_set_read_through_guard.py`: an AST walk over every
function under `src/`, flagging one that both (a) stages a `cognition_bundle_set` write (keyword
argument OR the quests.py-style dict-subscript build-up) and (b) reads `.cognition` directly,
without calling `read_through_cognition()` (or a function that itself transitively calls it,
computed rather than hardcoded, so `combat_engagement/phase.py`'s own wrapper is picked up
automatically). One documented allowlist entry: `MovementSystem.resolve_move()`, safe because its
caller pre-patches `.cognition` before invoking it. A second test guards the allowlist itself from
going silently stale.

## Step 5 — Regression + finalize
Run the affected unit/integration/architecture suites (see test_plan.md), commit, update the
ticket to DONE with the real acceptance-criteria mapping, move to `tickets/done/`, migrate staging
artifacts to `stored_artifacts/`.
