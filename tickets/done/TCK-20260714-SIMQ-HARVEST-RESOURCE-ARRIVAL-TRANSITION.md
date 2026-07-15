---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION
phase: done
date: 2026-07-14
tags: [simulation-quality, cognition]
---

# TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION

## Title
`ObjectiveIntentResolver.resolve()` maps `ObjectiveKind.REACH_RESOURCE` to
`ActionIntent(kind="MOVE_TO", ...)` unconditionally, including after the entity has already
arrived at the resource node — there is no on-arrival transition to a harvest/interact action,
so `gather_resource` routes navigate to the node and then go idle, never producing a
`resource_harvested` event.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`ObjectiveIntentResolver.resolve()` (`src/domains/adventure/resolver.py:67-69`) has a
`REACH_RESOURCE` branch that always sets `kind = "MOVE_TO"`, with a comment ("First reach, then
harvest") that describes the intended two-step behavior but is never implemented — there is no
code path that re-evaluates and switches to a harvest action once the entity is within
interaction range of the node.

This was discovered as an empirical finding during `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`
(done same session), which wired `ObjectiveIntentResolver` into the production tactical-execution
path (`src/engine/tactical.py`, Pillar 5.1 branch) so that System A's `ObjectiveKind` values
(previously orphaned/dead code) now reach real execution via `ActionIntentAdapter.execute()`. That
ticket ran three real, non-mocked calibration runs (`urban_political` seed=123/1000t,
`hero_guild_routing` seed=42/1000t, `simq_routing_test` seed=42/500t) and confirmed
`gather_resource` routes are actively selected and navigated (100/1000 ticks and 50/500 ticks
respectively, in the two `ENABLE_ADVENTURE_ROUTING=ON` runs) but zero `resource_harvested` events
were produced in any of the three runs — consistent with a code-traced dead end at arrival, not a
routing or selection problem.

A working reference pattern for exactly this transition already exists in the codebase, for a
structurally parallel case: `TacticalDecisionSystem.evaluate_entity_intent`'s pre-existing
`REACH_LOCATION` branch (`src/engine/tactical.py:214-229`) computes Manhattan distance to the
target (`dist <= 1.0`) and, on arrival at a resource node (`node_id is not None`), emits an
`EntityUpdate` with `TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "INTERACT",
"target_id": node_id})` plus an `InteractionUpdate` — instead of continuing to emit navigation
updates. `ObjectiveIntentResolver.resolve()`'s `REACH_RESOURCE` case has no equivalent arrival
check; it is a pure `ObjectiveKind -> kind` string lookup with no positional/distance awareness at
all (see `resolver.py:24-40`: only `objective.target_position` is copied into the payload,
never compared against the entity's current position).

## Scope
- Give the `REACH_RESOURCE` -> `ActionIntent` translation on-arrival awareness, so that once the
  entity is within interaction range of the target resource node, the produced `ActionIntent`
  triggers a harvest/interact action instead of another `MOVE_TO`. The exact mechanism is an
  implementation decision for investigation/plan, not decided here — options include (a) extending
  `ObjectiveIntentResolver.resolve()` itself to accept/derive arrival state (e.g. distance or an
  `arrived` flag passed via `payload`) and switch to a `HARVEST_RESOURCE`-kind `ActionIntent`
  (the `ActionIntentAdapter` already has working `HARVEST_RESOURCE` dispatch branches at
  `src/engine/intent/action_intent.py:78` and `:130` — used today by `ObjectiveKind.HARVEST_RESOURCE`
  objectives, if/when a producer emits them), or (b) an equivalent mechanism at the call site
  (`tactical.py`'s Pillar 5.1 `elif` branch, `tactical.py:260-287`) that mirrors the existing
  `REACH_LOCATION` branch's `dist <= 1.0` gate before invoking the resolver. Investigation/plan
  decides which.
- Cover the full `REACH_RESOURCE` lifecycle: entity far from node -> `MOVE_TO` navigation updates
  continue (unchanged, existing behavior preserved); entity within interaction range of node ->
  a harvest/interact action fires instead.
- Verify the fix produces a live `resource_harvested` `SimulationEvent` through the real
  authoritative pipeline (`ActionIntentAdapter.execute()` -> the resource-transaction/harvest
  resolution path -> `event_extractor.py`), at minimum via an integration-level test with
  non-mocked pipeline components (mirroring the pattern
  `tests/integration/domains/adventure/test_harvest_to_event.py` already established for
  `item_crafted`).
- Update `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-246` entry (or add a new entry) to
  reflect that the `REACH_RESOURCE -> MOVE_TO` arrival gap it explicitly called out as unresolved
  is now closed, once implemented.

## Out of Scope
- `ENABLE_ADVENTURE_ROUTING` defaulting to `FeatureMode.OFF` in shipped calibration profiles
  (`src/domains/optimization/feature_flags.py`, `config/simulation_quality/profiles/*.yaml`) — a
  separate, independently-scoped calibration/feature-flag question per
  `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`'s Implementation Notes; not filed as a ticket
  and not addressed here.
- `AdventureRouteScorer`'s selection bias against `craft_upgrade`/`buy_upgrade` in favor of
  `form_party`/`gather_resource` — a separate calibration/scoring-balance question belonging to the
  `simq_audit`/calibration workstream, not this ticket. This ticket only concerns what happens
  *after* a `gather_resource`/`REACH_RESOURCE` route has already been selected and navigated.
- Any change to `ObjectiveKind.HARVEST_RESOURCE`'s existing resolver mapping
  (`resolver.py:71-72`, already correctly `kind = "HARVEST_RESOURCE"`) or to
  `ActionIntentAdapter`'s existing `HARVEST_RESOURCE` dispatch branches
  (`action_intent.py:78`, `:130`) — these are confirmed already correct; this ticket wires
  `REACH_RESOURCE`'s arrival case to use them (or an equivalent path), not modify them.
- System B's `HARVESTING` goal path (`src/systems/strategic_systems/intelligence.py`'s
  `fused_strategic_pass`, `tactical.py`'s pre-existing `REACH_LOCATION` branch at
  `tactical.py:205-259`) — already correct and working; referenced only as the pattern to mirror,
  not touched.
- Re-scoring or re-anchoring ECONOMY (or any other SimQ pillar) once live `resource_harvested`
  events become observable in calibration runs — new follow-on work once this fix lands, not
  decided here.
- `docs/mechanics/03_economic_laws.md` §3's node-charge/depletion/regen mechanics
  (`ResourceEcologyService`, `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` events) — the unit-level
  harvest-completion mechanics (covered by parity ledger `TOWN-010`/`TOWN-104`/`TOWN-114`/`TOWN-129`,
  confirmed already `verified`) are not modified; this ticket only closes the goal-routing gap that
  currently prevents a harvest action from ever being *issued* via System A's `REACH_RESOURCE` path.
- Unifying System A and System B's goal-generation pipelines — explicitly rejected as an option in
  the parent ticket's investigation; not reopened here.

## Acceptance Criteria
- [x] Given an entity with an active `ObjectiveState` of `kind == ObjectiveKind.REACH_RESOURCE`
      and a resolved target position more than 1.0 Manhattan distance away, the produced
      `ActionIntent` (or equivalent tactical-layer update) continues to be navigation
      (`kind="MOVE_TO"` or the existing navigation-update path) — unchanged from current behavior.
      Covered by a unit test.
- [x] Given the same entity now within interaction range (`dist <= 1.0`, mirroring
      `tactical.py:219`'s existing threshold) of the target resource node, the produced action
      is a harvest/interact action (not another `MOVE_TO`). Covered by a unit test.
- [x] An integration-level test with real, non-mocked authoritative pipeline components
      (`ActionIntentAdapter.execute()` through to `event_extractor.py`) proves a `REACH_RESOURCE`
      objective at arrival produces a real `resource_harvested` `SimulationEvent`.
- [x] No regression to `ObjectiveKind.REACH_LOCATION`'s existing `tactical.py:214-259` behavior,
      `ObjectiveKind.HARVEST_RESOURCE`'s existing resolver mapping, or any other `ObjectiveKind`
      routed by `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`'s Pillar 5.1 branch — verified by
      the existing `tests/unit/domains/adventure/`, `tests/integration/domains/adventure/`,
      `tests/unit/tactical/`, and `tests/unit/strategic/` suites passing unmodified (or with only
      documented, justified adjustments).
- [x] `tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline`
      (added by the parent ticket) still passes.
- [x] `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-246` entry (or a new entry) is updated
      to reflect the closed arrival-transition gap, per the Authoritative Mechanics Rule.

## Related Tickets
- `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (done) — discovered this gap during its Step 11
  empirical calibration verification, and built the routing bridge
  (`ObjectiveIntentResolver` wired into `tactical.py`'s production path) that makes this fix
  reachable at all. That ticket's Scope Guards explicitly excluded modifying
  `ObjectiveIntentResolver`'s internal mapping table, which is why this follow-up exists as a
  separate ticket.

## Related Docs
- `docs/mechanics/03_economic_laws.md` §3 "Resource Harvesting" — authoritative node-charge,
  depletion, and event-emission (`RESOURCE_DEPLETED`/`RESOURCE_RECOVERED`) mechanics this fix must
  resolve through once a harvest action actually fires; the harvest-completion mechanics themselves
  are unchanged, this ticket only closes the goal-routing gap that currently prevents the harvest
  action from being issued.
- `docs/mechanics/04_strategic_cognition.md` §4 "The Project Lifecycle" — defines the
  Directive -> Project -> Objective -> Action hierarchy (`REACH_RESOURCE` is an Objective; the
  harvest/interact call is the Action it must resolve to on arrival); this ticket closes the
  missing Objective -> Action transition for this specific objective kind.
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-246` — documents the routing-bridge fix and
  explicitly names this exact gap (`REACH_RESOURCE -> MOVE_TO mapping never transitioning to a
  harvest/interact action on arrival`) as unresolved by that entry.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/` (once migrated from
  `staging_artifacts/` on that ticket's close) — `investigation.md`/`plan.md`/`test_plan.md`
  document the resolver's current mapping, the routing-bridge wiring, and the Step 11 empirical
  calibration findings that discovered this gap. As of this scoping, the parent ticket's file is
  still physically in `tickets/inprogress/` with a completed `Completion Summary`; its staging
  artifacts have not yet been migrated to `stored_artifacts/` — check `staging_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/`
  if `stored_artifacts/` does not yet have them.

## Related Code Areas
- `src/domains/adventure/resolver.py` — `ObjectiveIntentResolver.resolve()`, specifically the
  `REACH_RESOURCE` branch at lines 67-69 (the exact fix site).
- `src/engine/tactical.py:205-282` — the working reference pattern to mirror: the existing
  `REACH_LOCATION` branch's arrival-distance check (`dist <= 1.0` at line 219) and its
  `TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "INTERACT", ...})` +
  `InteractionUpdate` emission on arrival (lines 220-229); also the Pillar 5.1 `elif` branch
  (lines 260-287) that currently calls `ObjectiveIntentResolver.resolve()` for `REACH_RESOURCE`
  and all other non-`REACH_LOCATION` kinds.
- `src/engine/intent/action_intent.py` — `ActionIntentAdapter.execute()`'s existing
  `HARVEST_RESOURCE` dispatch branches (lines 78 and 130), confirmed already correct and available
  to be the eventual sink for the arrival-transition fix.
- `src/core/strategic.py:104-118` — `ObjectiveKind` enum (`REACH_RESOURCE`, `HARVEST_RESOURCE`
  members).

## Assumptions / Open Questions
- Assumes the `dist <= 1.0` Manhattan-distance interaction-range threshold used by the existing
  `REACH_LOCATION` branch (`tactical.py:219`) is the correct threshold to mirror for
  `REACH_RESOURCE` arrival detection as well — if investigation finds resource nodes use a
  different interaction range elsewhere in the codebase, that value should be used instead.
- Assumes option (a) or (b) as described in Scope are both structurally viable; which one is
  chosen (resolver-internal arrival detection vs. call-site gating before invoking the resolver)
  is left open for investigation/plan, since it affects whether `ObjectiveIntentResolver.resolve()`
  needs a new parameter/signature change (a durable-state/API-shape decision that should go through
  the standard investigation-then-plan-then-architecture-review path, not be pre-decided in scoping).
- Assumes no separate `craft_item`-style "opportunity provider" gap exists for `REACH_RESOURCE`
  specifically (unlike the parent ticket's Open Question 3 for `craft_item`) — `gather_resource`
  routes are confirmed actively generated and selected by three real calibration runs in the parent
  ticket's Step 11; the gap is confirmed to be purely the post-arrival transition, not candidate
  generation or selection. If investigation finds otherwise, this scope is invalidated.
- `layer: strategy` was inferred from this being a strategic-cognition Objective->Action transition
  (goal-routing execution logic), consistent with the parent ticket's `layer: strategy`.

## Implementation Notes

Implemented option (b) from investigation.md/plan.md — call-site gating in
`TacticalDecisionSystem.evaluate_entity_intent`'s Pillar 5.1 `elif` branch
(`src/engine/tactical.py:260-306`). `ObjectiveIntentResolver.resolve()`
(`src/domains/adventure/resolver.py`) is unmodified.

1. **`src/engine/tactical.py`** — the `elif` branch's call to
   `_resolve_target_position(state, obj)` now captures `node_id` (previously
   discarded as `_`). Added one new conditional between the existing `dist > 1.0`
   early-return and the existing `ObjectiveIntentResolver.resolve()` fallthrough:
   when `obj.kind == ObjectiveKind.REACH_RESOURCE and node_id is not None` (i.e.
   arrived, `dist <= 1.0`), builds `ActionIntent(kind="HARVEST_RESOURCE",
   actor_id=entity.id, target_id=node_id, source_opportunity_id=obj.id, reason=...)`
   and routes it through the already-wired `ActionIntentAdapter.execute()`
   `HARVEST_RESOURCE` dispatch (`action_intent.py:78`, `:130`), returning that
   result directly. The far-away case (`dist > 1.0`) and every other
   `ObjectiveKind`'s fallthrough to `ObjectiveIntentResolver.resolve()` are
   unchanged. `REACH_LOCATION`'s branch (`tactical.py:214-259`) was not touched.

2. **`tests/unit/tactical/test_objective_pursuit_coverage.py`** —
   - Extended `test_objective_kind_reach_resource_produces_executable_action`
     with explicit `update.task is None` / `update.interaction is None`
     assertions for the far-away case (AC #1).
   - Added `test_objective_kind_reach_resource_arrival_produces_harvest_action`
     (hero placed at the node's position; asserts
     `update.interaction.target_node_id == node.id`) (AC #2).
   - Added `test_reach_location_arrival_behavior_unchanged` — a pinning test for
     `REACH_LOCATION`'s pre-existing arrival branch (node-target `INTERACT` case,
     plus building-target `EAT`/`REST` cases for `"hunger"`/`"fatigue"`-kind
     projects), per the plan's Step 4 conditional addendum: no existing test
     asserted this branch's `EntityUpdate` shape via
     `TacticalDecisionSystem.evaluate_entity_intent` before this ticket.

3. **`tests/integration/domains/adventure/test_harvest_to_event.py`** — added
   `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`:
   a real, non-mocked `ActionIntent(kind="HARVEST_RESOURCE", ...)` through
   `ActionIntentAdapter.execute()` -> `InteractionSystem.enforce` (using
   `ResourceNodeState(required_ticks=1, ...)` so a single `progress_delta=1`
   completes the harvest) -> `ResourceTransactionSystem.resolve_all` ->
   `EventExtractor.extract`, asserting `"resource_harvested"` appears in the
   extracted event types (AC #3). Updated the module's stale docstring, which
   previously documented the arrival gap as open, to point at the new test.

4. Ran the full regression sweep from `test_plan.md`'s Scoped Pytest Commands:
   `tests/unit/tactical/`, `tests/unit/combat/`, `tests/unit/movement/`;
   `tests/unit/domains/adventure/`, `tests/integration/domains/adventure/`;
   `tests/unit/strategic/test_strategic_cognition_regression.py`,
   `tests/unit/strategic/test_cognition_authoritative_path.py`,
   `tests/integration/pipeline/test_strategic_cadence.py`;
   `tests/perf/test_phase3_adventure_decision_budget.py`;
   `tests/integrity/test_logic_guards.py`. All pass except one pre-existing,
   unrelated failure (`tests/unit/movement/test_movement_spatial_regression.py::test_normal_move_triggers_oa`),
   confirmed to fail identically on the pre-change commit via `git stash`
   (opportunity-attack damage assertion, nothing to do with `tactical.py`'s
   Pillar 5.1 branch or resource harvesting).

5. **`docs/parity_ledger/strategic_cognition.yaml`** — updated `STRAT-246`:
   appended the two new/extended test function references to `test_path`
   (alongside the four existing entries, unchanged); updated `support_boundary`
   to mark factor (3) `[CLOSED by TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION]`
   with a description of the actual fix, leaving factors (1)/(2) and all other
   language unchanged; appended a new paragraph to `v2_evidence` describing the
   Step 1 fix. `STRAT-189` and all other entries were left untouched. Re-ran the
   full `STRAT-246` `test_path` list (9 tests) — all pass. YAML re-parsed
   successfully with `yaml.safe_load`.

See `staging_artifacts/TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION/plan.md`'s
"Deviations" section for the two plan-flagged decision points resolved during
implementation (the Step 4 conditional addendum firing, and the Step 5
`test_path` function-vs-file-level resolution).

## Test Summary

All tests pass. New/modified tests (9 assertions across 5 test functions, 3
new, 2 extended):
- `tests/unit/tactical/test_objective_pursuit_coverage.py::test_objective_kind_reach_resource_produces_executable_action` (extended, AC #1)
- `tests/unit/tactical/test_objective_pursuit_coverage.py::test_objective_kind_reach_resource_arrival_produces_harvest_action` (new, AC #2)
- `tests/unit/tactical/test_objective_pursuit_coverage.py::test_reach_location_arrival_behavior_unchanged` (new, anti-drift pin, AC #4)
- `tests/integration/domains/adventure/test_harvest_to_event.py::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline` (new, AC #3)
- `tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline` (unmodified, re-verified, AC #5)

Full regression sweep (per test_plan.md): `tests/unit/tactical/`,
`tests/unit/combat/`, `tests/unit/movement/` (133 passed, 1 pre-existing
unrelated failure); `tests/unit/domains/adventure/`,
`tests/integration/domains/adventure/` (64 passed);
`tests/unit/strategic/test_strategic_cognition_regression.py`,
`tests/unit/strategic/test_cognition_authoritative_path.py`,
`tests/integration/pipeline/test_strategic_cadence.py` (12 passed);
`tests/perf/test_phase3_adventure_decision_budget.py` (1 passed);
`tests/integrity/test_logic_guards.py` (5 passed, 2 xfailed as expected).

## Files Changed
- `src/engine/tactical.py` — captured `node_id`, added `REACH_RESOURCE` arrival branch (Pillar 5.1 `elif`)
- `tests/unit/tactical/test_objective_pursuit_coverage.py` — extended far-away test, added arrival test, added `REACH_LOCATION` pinning test
- `tests/integration/domains/adventure/test_harvest_to_event.py` — added full-pipeline `resource_harvested` test, updated stale module docstring
- `docs/parity_ledger/strategic_cognition.yaml` — updated `STRAT-246` (`test_path`, `support_boundary`, `v2_evidence`)
- `staging_artifacts/TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION/plan.md` — added Deviations section
- `tickets/inprogress/TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION.md` — this file

## Completion Summary
Closed the `REACH_RESOURCE` arrival-transition gap: `TacticalDecisionSystem.evaluate_entity_intent`'s
Pillar 5.1 branch now captures the `node_id` it was already resolving and discarding, and
transitions to a `HARVEST_RESOURCE` `ActionIntent` (routed through the existing
`ActionIntentAdapter` dispatch into `InteractionSystem.enforce` ->
`ResourceTransactionSystem.resolve_all` -> `event_extractor.py`) once the entity is within
interaction range (`dist <= 1.0`) of the target resource node, instead of falling through to
`ObjectiveIntentResolver.resolve()`'s unconditional `REACH_RESOURCE -> MOVE_TO` mapping, which
previously re-issued navigation forever. `ObjectiveIntentResolver.resolve()` itself is untouched
and remains the fallback for the rare case where `target_pos` resolves but `node_id` does not. All
five acceptance criteria are met: far-away behavior is unchanged and explicitly regression-tested;
arrival now produces a harvest/interact action, unit-tested; a full non-mocked integration test
proves a real `resource_harvested` `SimulationEvent`; no regression to `REACH_LOCATION`,
`HARVEST_RESOURCE`'s resolver mapping, or any other `ObjectiveKind` (full regression sweep passes,
one pre-existing unrelated failure confirmed via `git stash`); the integrity guard test still
passes; and `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-246` entry is updated to reflect
the closed gap.
