---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE
artifact_type: plan
tags: [cognition, adventure]
---

# Implementation Plan — TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE

## Summary

**This ticket does not "switch on" `AdventureGoalScorer` for the first time — it is already
live and already wins tier-5 arbitration today.** Traced through the real merge/ordering
machinery (investigation.md, confirmed independently in this planning pass): `GoalRegistry
.get_all_scores()` (`src/ai/goals/base.py:17`) has zero flag-gating and scores every registered
scorer unconditionally; `AdventureGoalScorer` is registered unconditionally
(`src/ai/goals/__init__.py:21`); the `strategic_intelligence` pipeline phase
(`src/engine/pipeline.py:347`) runs unconditionally every tick, strictly *after*
`adventure_decision` (`src/engine/pipeline.py:236-247`) in the same `apply()` method body; and
both `StrategicUpdate.merge()` (`src/core/updates.py:530-566`) and `EntityUpdate.merge()`
resolve later-merged-wins. So for any non-cadence-skipped adventure-eligible entity, the tier-5
`AdventureGoalScorer` decision already overwrites `AdventureDecisionPhase`'s decision in the
same tick. Deleting the phase therefore removes (a) now-wasted duplicate route-generation +
scoring compute that gets silently overwritten every tick, and (b) the one case where the old
phase's decision still lands uncontested — cadence-skipped entities, which after deletion get no
adventure-routing decision that tick at all. That second effect is a real, disclosed frequency
reduction, but it is the design's own literal, stated Goal #3 (adventure becomes subject to the
same strategic hierarchy/cadence every other decision already respects), not a new risk this
ticket introduces. This reclassifies the ticket's real risk profile: it is a cleanup/removal of
dead-weight compute plus closing two real, newly-found observability gaps — not a first-time
behavior flip.

The plan: (1) relocate `_resolve_cognition_profile_id`/`_supports_adventure_routing` from
`src/domains/adventure/phase.py` (current re-verified lines 27-58 and 61-74) into
`src/ai/goals/adventure_scorer.py`, byte-identical internally; (2) delete `AdventureDecisionPhase`
and its `pipeline.py` registration; (3) port the decision-trace-writer call into
`AdventureGoalScorer.score()` (Risk #1 — a clean, isolated port, no other writers to
`decision_trace.jsonl` exist once phase.py's copy is deleted); (4) record the
`last_defer_reason`/`defer_with_reason` gap (Risk #0) as an **intentional, disclosed divergence**
rather than porting it — direct tracing in this planning pass (re-confirmed against current
source during this revision) shows the signal is discarded by the shared tier-5 utility-floor
check (`src/systems/strategic_systems/intelligence.py:1412`, `if g_score.utility < 20.0:
continue`) before any `StrategicUpdate`-returning site in `evaluate_strategic_intent()` is ever
reached, since `AdventureGoalScorer`'s DEFER_WITH_REASON branch always scores `utility=0.0` by
design (`src/ai/goals/adventure_scorer.py:99-109`); a real port would require special-casing
sub-floor scores inside the shared tier-5 scoring loop itself
(`intelligence.py:1394-1414`, a P0-adjacent function STRAT-185/186/187 directly test) — a change
that touches every `GoalKind` scorer's ineligible/deferred case, not just adventure's, which is
materially larger and riskier than this ticket's stated narrow scope and would duplicate
goal-scoring compute if done as a thin wrapper instead; (5) migrate all 9 files with real
code-level dependencies on
`AdventureDecisionPhase` (corrected blast radius from investigation.md, verified against live
`grep` in this planning pass) to exercise the surviving tier-5 path; (6) delete
`test_adventure_shadow_migration_parity.py` only after porting its
`_diff_routes()` helper + `test_shadow_diff_report_separates_raw_score_from_utility_mismatches`
assertion into `test_adventure_route_materialization.py`; (7) update STRAT-236, STRAT-252,
STRAT-253, `adventure_contract.md`, and `04_strategic_cognition.md` (the last is not in the
ticket's own Related Docs list but investigation.md confirms this ticket's deletion makes its
tier-5 claim newly/differently wrong, and CLAUDE.md's parity rule requires the fix land in the
same session); (8) re-run the targeted SimQ regression surface in Verify as a named, non-optional
step per design doc §7 step 4's obligation.

## Steps

### Step 1 — Relocate `_resolve_cognition_profile_id` and `_supports_adventure_routing` into `adventure_scorer.py`

**Files:** `src/ai/goals/adventure_scorer.py`, `src/domains/adventure/phase.py`

**Change:**
- Confirmed by direct read this session: `src/domains/adventure/phase.py:27-58` defines
  `_resolve_cognition_profile_id(entity)` and `src/domains/adventure/phase.py:61-74` defines
  `_supports_adventure_routing(entity, cache)`. These are the current, re-verified line ranges
  (the ticket's own Scope text cites stale lines 49-96, which predate ticket 2's removal of
  `_threat_resolved` from this file — do not use the ticket's own citation).
- Copy both function bodies byte-identical (including docstrings) into
  `src/ai/goals/adventure_scorer.py`, placed after the module's existing imports (ending line 7)
  and after the `_PROFILE_ELIGIBILITY_CACHE` module-level dict (line 18), immediately before the
  `AdventureGoalScorer` class definition (line 21) — confirmed by direct read this session: line 7
  is the last import (`from src.domains.adventure.schema import RouteFamily`), line 18 is
  `_PROFILE_ELIGIBILITY_CACHE: Dict[str, bool] = {}`, and line 21 is
  `class AdventureGoalScorer(GoalScorer):`.
- Required new imports at the top of `adventure_scorer.py` to support the relocated functions'
  own bodies (confirmed by reading `phase.py:10-19`): `from typing import Dict` (already present
  at `adventure_scorer.py:2`, extend to include `Optional` if not already — confirmed present at
  line 2), `from src.core.enums import EntityRole`, `from src.engine.behavior_consumers import
  get_cognition_profile_definition, get_role_definition`.
- Remove `AdventureGoalScorer.score()`'s existing lazy function-local import at
  `adventure_scorer.py:48` (`from src.domains.adventure.phase import
  _supports_adventure_routing`) — the function is now in the same module, call it directly with
  no import.
- **Do NOT** make this import eager-turned-something-else by association: the constants import at
  `adventure_scorer.py:62-65` (`from src.systems.strategic_systems.intelligence import
  _ADVENTURE_ROUTE_SCORE_MAX, _GOAL_UTILITY_SCORE_MAX`) stays exactly as-is, function-local, for
  its own independent, still-valid circular-import reason (documented in the surrounding comment,
  `adventure_scorer.py:53-61`) — do not touch it.
- `_PROFILE_ELIGIBILITY_CACHE` (module-level, `adventure_scorer.py:18`, persists across ticks) is
  the cache instance the relocated `_supports_adventure_routing` now uses directly at its call
  site inside `score()` (`adventure_scorer.py:50`, already passing this exact cache object) — no
  change needed to the call site itself, only to where the function it calls is defined.
- **Do NOT** change `_PROFILE_ELIGIBILITY_CACHE`'s lifetime to a per-tick cache — this is a
  deliberate, already-reviewed prior decision (documented at `adventure_scorer.py:9-17`), not a
  defect.
**Do NOT touch:** `phase.py:1-24` module imports besides what Step 2 removes; the
`AdventureDecisionPhase` class body itself (deleted whole in Step 2, not edited piecemeal here).
**Verify:** `test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source`
(new, Step 8) plus the migrated `test_eligibility_cognition_profile.py` suite (Step 5, item 2).

### Step 2 — Delete `AdventureDecisionPhase` and its `pipeline.py` registration

**Files:** `src/domains/adventure/phase.py`, `src/engine/pipeline.py`

**Change:**
- In `src/engine/pipeline.py`, remove lines 236-247 in full — the entire "Enhanced RPG Phase 3:
  Adventure Routing" block: the function-local import
  `from src.domains.adventure.phase import AdventureDecisionPhase` (line 237), the `run_phase(
  "adventure_decision", update, lambda u: u.merge(AdventureDecisionPhase.apply(state,
  faction_directives=faction_directives, factions=state.factions)), "ENABLE_ADVENTURE_ROUTING")`
  call, and the `costs["adventure_decision"] = ...` timing line. Confirmed by direct read this
  session — no other reference to `AdventureDecisionPhase` exists anywhere else in
  `pipeline.py`.
- **Do NOT** touch `pipeline.py:347` (`run_phase("strategic_intelligence", ...)`,
  unconditional, no flag) or any phase registration adjacent to the deleted block (e.g. the
  `military_conflict` block immediately above at lines 225-233) — only the named block is
  in scope.
- In `src/domains/adventure/phase.py`, after Step 1 has relocated the two module-level functions,
  delete: the entire `AdventureDecisionPhase` class (current lines 77-198, confirmed by direct
  read this session — `class AdventureDecisionPhase:` through the final `return update`), and any
  now-unused imports whose only consumer was the deleted class or the relocated functions (after
  Step 1's relocation, verify each of `phase.py:10-24`'s imports against what remains in the
  file — if the file becomes fully empty of live code, delete the file entirely rather than leave
  a dead module; confirm no other module still imports `src.domains.adventure.phase` for
  anything else before deleting the file outright — `adventure_scorer.py`'s own import at
  line 48 is being removed by Step 1, so check for any other importer via
  `grep -rn "from src.domains.adventure.phase import\|domains.adventure.phase" src/` before
  deleting the file).
- Retiring `ENABLE_ADVENTURE_ROUTING` to a dead flag is an accepted, disclosed side effect (its
  only remaining live use anywhere is the `run_phase` call being removed) — **do not** remove the
  flag's own definition (`src/domains/optimization/feature_flags.py`) or its default-value config
  (`rollout_profiles.py`) in this ticket; that is out of scope (a future cleanup ticket's job).
**Do NOT touch:** `_threat_resolved` (already relocated by a prior ticket, imported not defined
in `phase.py`), `evaluate_project_switch()`'s signature (belongs to
`THREAT-RESOLVED-ARBITER-RELOCATION`, already landed and explicitly out of scope here).
**Verify:** `test_pipeline_module_has_no_adventure_decision_phase_reference` (new, Step 8).

### Step 3 — Port the decision-trace-writer call into `AdventureGoalScorer.score()` (Risk #1 resolution: PORT)

**Decision:** Port. This is a P1 authoritative observability contract
(`docs/observability/decision_trace_contract.md`), the port site is architecturally clean (a
single isolated side-effect call, not a durable-state mutation — the writer's own docstring,
`src/observability/cognition/decision_trace_writer.py:16-21`, confirms `write_trace()` is a
bounded in-memory enqueue only, no file I/O on the call path, matching the class of side effect
`AdventureDecisionPhase.apply()` itself already performed directly inside `apply()`'s body
without going through the `StateUpdate`/`EntityUpdate` mechanism — establishing this as an
accepted exception to the Durable State Rule, not a new one), and **no other writer** to
`decision_trace.jsonl` exists in the codebase today besides the one being deleted in Step 2
(confirmed: `docs/observability/decision_trace_contract.md:95` cites exactly one "Wired at" site,
`AdventureDecisionPhase.apply()`) — so this is a clean 1:1 relocation with zero ordering/race
risk against any other writer.

**Files:** `src/ai/goals/adventure_scorer.py`

**Change:**
- Add a module-level import: `from src.observability.cognition.decision_trace_writer import
  get_active_writer as _get_active_writer`. Confirmed safe as a top-level (not lazy) import by
  direct read of `src/observability/cognition/decision_trace_writer.py:23-33` — it imports only
  from `src.observability.config`, `src.observability.cognition.tick_index`, and
  `src.observability.queue`, none of which touch `src.ai.goals` or `src.systems.strategic*`, so
  no circular-import risk exists (unlike the `_supports_adventure_routing`/intelligence.py path
  documented at `adventure_scorer.py:31-47`, which is a genuinely different, unrelated concern —
  do not conflate the two or make this import lazy "to match the file's style").
- `get_active_writer()` itself (`decision_trace_writer.py:56-58`) is a trivial O(1) global lookup
  (`return _active_writer`), not the expensive operation — the expense phase.py's own comment
  (`phase.py:115-117`) warns about is the one-time module *import* cost (Pydantic model
  construction), which happens once at process/module load with a top-level import, not per
  call. Calling `_get_active_writer()` once per `score()` invocation (once per entity per tick,
  the same effective frequency phase.py achieved by resolving it once per `apply()` call across
  all heroes) is cheap and does not reintroduce the O(n) cost the original comment flagged.
- Inside `AdventureGoalScorer.score()`, immediately after the existing `result =
  AdventureDecisionService.decide(...)` call (`adventure_scorer.py:89-96`) and before the
  `selected = result.selected` line, add:
  ```python
  _writer = _get_active_writer()
  if _writer is not None:
      scored_candidates = result.trace.get("scored_candidates", [])
      if scored_candidates:
          _writer.write_trace(entity.id, state.tick, scored_candidates)
  ```
  This mirrors `phase.py:147-152` exactly (confirmed by direct read: `result.trace` is a dict
  with a `"scored_candidates"` key populated by `AdventureDecisionService.decide()`,
  `src/domains/adventure/service.py:152-160`). Writing before the DEFER_WITH_REASON/target
  resolution branches means the trace is recorded for every entity `score()` evaluates — the same
  behavior as before (`phase.py`'s old loop wrote the trace before checking whether the result
  was DEFER_WITH_REASON, not only for winners).
- `AdventureGoalScorer.score()`'s signature stays `score(self, entity: EntityState, state:
  AuthoritativeState) -> GoalScore` — the `GoalScorer` Protocol
  (`src/ai/goals/base.py:16-17`) does not accept a third parameter, so there is no
  `trace_writer=` override parameter in the new path (unlike `AdventureDecisionPhase.apply()`,
  which accepted one for testability). Tests must patch `_get_active_writer` at the
  `src.ai.goals.adventure_scorer` module path instead (see Step 5, item 1).
**Do NOT touch:** `EntityInspector.goal_scores` (`src/observability/live/entity_inspector.py:
136-140`) — it reads from the same writer's cache generically and needs no change, since the
writer instance and its cache are unchanged, only the call site that feeds it moved.
**Verify:** `test_adventure_goal_scorer_wires_writer` (migrated, Step 5 item 1).

### Step 4 — Document the `last_defer_reason`/`defer_with_reason` gap as an intentional divergence (Risk #0 resolution: DO NOT PORT)

**Decision:** Do not port in this ticket. Document as an intentional, disclosed divergence.

**Reasoning (traced directly in this planning pass; re-verified against current source during
this revision, correcting an earlier mischaracterization of the mechanism):**
`event_extractor.py:620-626` reads `prop.get("last_defer_reason")` from an entity's **committed
`EntityUpdate.property_updates`** dict to emit `defer_with_reason`. `EntityUpdate
.property_updates` is not populated from `StrategicUpdate` today at the **one live call site**
that constructs the entity's final `EntityUpdate` from `evaluate_strategic_intent()`'s return
value — `intelligence.py:555`, inside `fused_strategic_pass()` (confirmed by direct read this
session: this is `evaluate_strategic_intent()`'s only caller reachable from the pipeline; no
`property_updates` is threaded from the `StrategicUpdate` result into the `EntityUpdate` being
built there). A second apparent call site, `evaluate_all_strategic_intents()`
(`intelligence.py:867-910`, call at line 905), is **dead code** — confirmed by repo-wide `grep`
this session, `evaluate_all_strategic_intents` has zero callers anywhere in `src/` or `tests/` —
so it is not part of the live signal path and is not relevant to this decision.

The reason a port is out of scope is **not** the number of return statements in
`evaluate_strategic_intent()` — it's that the DEFER_WITH_REASON signal never survives long enough
to reach any of them. `GoalRegistry.get_all_scores(entity, state)` (`intelligence.py:1394`)
collects every registered scorer's `GoalScore`, including `AdventureGoalScorer`'s. But
`AdventureGoalScorer.score()`'s `DEFER_WITH_REASON` branch always returns `utility=0.0` by
explicit design (`src/ai/goals/adventure_scorer.py:99-109`; the code's own comment reads "AC5:
ineligible/DEFER_WITH_REASON never clear the 20.0 tier-5 floor"). The tier-5 selection loop
immediately after (`intelligence.py:1410-1414`) discards any score below the floor before it can
ever become `best_candidate`:
```python
for g_score in modified_scores:
    if g_score.utility < 20.0 or (g_score.target_id is None and g_score.target_pos is None):
        continue
    best_candidate = g_score
    break
```
Every `StrategicUpdate`-constructing return site inside `evaluate_strategic_intent()`
(`intelligence.py:1428` onward, confirmed by direct read of the full function body this session)
branches on `best_candidate` — so a `DEFER_WITH_REASON` adventure score is filtered out by the
utility floor **before** any construction/return site is ever reached, regardless of how many
such sites exist or how a new field would be threaded through them. Widening `StrategicUpdate`
and threading a `property_updates` field through those return sites alone would therefore not
actually port the signal — it would still never arrive.

A faithful port instead requires special-casing sub-floor scores **inside the shared tier-5
scoring loop itself** (around `intelligence.py:1394-1414`), before the floor filter discards the
entry — a loop every `GoalKind` scorer's score passes through, not just adventure's. That is a
structurally different, and arguably *more* invasive change than "widen a dataclass and thread N
returns": it touches shared arbitration logic used by every tier-5 goal, inside a function
STRAT-185/STRAT-236/STRAT-186/STRAT-187 (P0/P1) directly test, and is explicitly adjacent to (but
distinct from) `evaluate_project_switch()`'s signature, which the ticket's own Out of Scope
section already excludes as belonging to a different ticket (C2). A cheaper alternative —
wrapping `evaluate_strategic_intent()` and re-deriving the defer condition by calling
`GoalRegistry.get_all_scores()` a second time — would duplicate goal-scoring compute, reproducing
exactly the wasted-duplicate-compute problem this ticket exists to eliminate. Given the ticket's
own scope boundary and the review history on this epic (3 real blocking bugs caught by
architecture-reviewer on prior tickets, each time from scope creep or unverified claims), this
plan does not attempt the shared-loop special-casing change here.

**Files:** `docs/guidelines/intentional_divergences.md`

**Change:**
- Add a new row to the Divergence Summary Table (§1, after the existing
  `Engine / Combat-Progression` rows): `| **Engine / Cognition-Strategy** | Adventure-Route
  Defer-Reason Observability Gap | **Bounded** | RATIFIED |`.
- Add a new `§2.x` detailed record (numbered following the file's existing sequence):
  - **Subsystem**: Engine / Cognition-Strategy
  - **Old Behavior**: `AdventureDecisionPhase.apply()` wrote
    `property_updates={"last_defer_reason": result.selected.reason or "unknown",
    "last_defer_tick": tick}` on an entity's `EntityUpdate` whenever
    `AdventureDecisionService.decide()` returned `RouteFamily.DEFER_WITH_REASON`
    (`src/domains/adventure/phase.py:157-165`, pre-deletion). `event_extractor.py:620-626` read
    this key to emit a `defer_with_reason` SimulationEvent (`event_category: "strategy"`), feeding
    the AGENCY SimQ pillar.
  - **New Behavior**: `AdventureGoalScorer.score()` (`src/ai/goals/adventure_scorer.py`) carries
    the same DEFER_WITH_REASON signal only as `GoalScore.metadata` (`route_family`, `raw_score`)
    — it does not write `last_defer_reason`/`last_defer_tick` to any `EntityUpdate
    .property_updates`, and the tier-5 arbitration path
    (`StrategicIntelligenceSystem.evaluate_strategic_intent()`) has no site that threads this
    metadata into a committed `EntityUpdate` without a larger `StrategicUpdate`
    schema change. `defer_with_reason` events no longer fire for adventure-routing deferrals.
  - **Rationale**: **Bounded**. The DEFER_WITH_REASON signal is discarded by the shared tier-5
    utility-floor check (`intelligence.py:1412`, `if g_score.utility < 20.0: continue`) before
    any `StrategicUpdate`-returning site inside `evaluate_strategic_intent()` is ever reached —
    `AdventureGoalScorer`'s DEFER_WITH_REASON branch always scores `utility=0.0` by design
    (`adventure_scorer.py:99-109`). Porting this signal for real therefore requires
    special-casing sub-floor scores inside the shared tier-5 scoring loop itself
    (`intelligence.py:1394-1414`), a change that affects every `GoalKind` scorer's
    ineligible/deferred case, not just adventure's — deliberately bounded out of
    `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s narrow relocate-and-delete scope. A future
    ticket should design how sub-floor scorer signals surface (e.g., a `StrategicUpdate
    .property_updates` field populated from inside the shared loop before the floor filter runs,
    not merely threaded through the existing return sites) as its own reviewed change.
  - **Verification**: `test_defer_property_name_constant_matches_phase_and_extractor` (migrated,
    Step 5 item 9) — asserts the current, disclosed absence of `last_defer_reason` wiring in the
    adventure-scoring path, and references this divergence entry so a future edit that
    reintroduces partial wiring is caught for review.
**Do NOT touch:** `event_extractor.py:620-626` itself — the extractor logic is correct and stays
unchanged; only the upstream write is missing, which is the documented gap.
**Verify:** `test_defer_property_name_constant_matches_phase_and_extractor` (Step 5 item 9).

### Step 5 — Migrate the 9 files with real code-level dependencies on `AdventureDecisionPhase`

**Files:** see per-item list below (all paths confirmed present via direct `grep` this session).

**Change:** One sub-step per file, in this order (independent of each other, may be done in any
order relative to one another, but all must land before Step 2's deletion is considered complete
for AC purposes — practically, do Steps 1-4 first, then this step, then finalize Step 2's
deletion, since several of these tests currently import the live class and would fail mid-way
otherwise; see Dependency Map):

1. **`tests/unit/observability/test_decision_trace.py`** — `test_adventure_decision_phase_wires_writer`
   (confirmed at line 312, current body at lines 312-354). Rewrite as
   `test_adventure_goal_scorer_wires_writer`: replace the `AdventureDecisionPhase.apply(state,
   trace_writer=mock_writer)` call with a call to `AdventureGoalScorer().score(entity, state)`
   using a real (non-Mock) minimal `EntityState`/`AuthoritativeState` (the current test's
   `MagicMock()`-based `state`/`hero` will not survive `_supports_adventure_routing`'s catalog
   lookups once it runs the relocated logic — build via the same real-entity pattern
   `test_adventure_route_materialization.py`'s `_entity()`/`_state()` helpers already use), patch
   `AdventureRouteGenerator.generate`, `AdventureDecisionService.decide`, and
   `ResourceOpportunityProvider.get_opportunities` at their `src.ai.goals.adventure_scorer`-qualified
   paths (not `src.domains.adventure.phase`), and patch
   `src.ai.goals.adventure_scorer._get_active_writer` to return `mock_writer` instead of passing
   `trace_writer=` (Step 3 confirmed the scorer has no such parameter). Assert
   `mock_writer.write_trace.assert_called_once_with(<entity_id>, <tick>, [scored_route])`.
2. **`tests/unit/domains/adventure/test_eligibility_cognition_profile.py`** — 4 tests
   (`test_eligibility_resolves_via_cognition_profile_not_role`,
   `test_hero_role_with_ineligible_profile_excluded`,
   `test_cognition_profile_id_missing_does_not_crash`,
   `test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero`). Rewrite each to
   import `_resolve_cognition_profile_id`/`_supports_adventure_routing` from
   `src.ai.goals.adventure_scorer` (their new home per Step 1) and call them directly on a built
   entity + cache dict, replacing the current pattern of calling
   `AdventureDecisionPhase.apply(state)` and inspecting `update.entity_updates`.
3. **`tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py`** —
   `test_three_production_call_sites_thread_state_argument` (confirmed at lines 35-53). Remove
   the `from src.domains.adventure.phase import AdventureDecisionPhase` import (line 14) and the
   `apply_calls = _find_evaluate_project_switch_calls(inspect.getsource(
   AdventureDecisionPhase.apply))` computation; keep only `intent_calls` (from
   `StrategicIntelligenceSystem.evaluate_strategic_intent`). Change the asserted count from
   `3` to `2` (line 49's `assert len(all_calls) == 3` becomes `assert len(all_calls) == 2`), and
   update the docstring/assert message (lines 36-40, 49-53) to describe only
   `evaluate_strategic_intent()`'s 2 call sites. **Do not loosen the assertion to `>=`** — keep it
   an exact equality guard.
4. **`tests/unit/systems/test_spawn_lock_condition.py`** — 6 call sites (confirmed at lines 132,
   154, 166, 178, 189, 208, spanning `TestLockEarlyRelease`/`TestLockHeldWhenThreatActive` and
   related classes), including `test_lock_released_when_hp_high_and_no_hostiles` — the test
   STRAT-236's `test_path` currently cites. Retarget each `AdventureDecisionPhase.apply(state)`
   call to `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)` (single-entity
   signature, confirmed at `intelligence.py:1173-1178`), asserting on the returned
   `StrategicUpdate.current_project_id_set`/lock-respecting behavior directly. This is a stronger
   assertion than the current near-vacuous placeholder in some of these tests (per
   investigation.md) — acceptable as a side effect of equivalent-coverage migration, not a
   separate quality initiative. STRAT-236's `test_path` (Step 7) must be re-pointed to whichever
   test name/class survives this migration.
5. **`tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`** — 2 tests
   (confirmed at lines 19 `test_apply_commit_branch_does_not_construct_strategic_update_directly`
   and 57 `test_apply_module_imports_strategic_intelligence_system`). Retarget the AST walk from
   `inspect.getsource(AdventureDecisionPhase.apply)` to
   `inspect.getsource(StrategicIntelligenceSystem.evaluate_strategic_intent)`, scoped to (or
   noting) the `ADVENTURE_ROUTE` branch specifically (`intelligence.py:1440-1467`), asserting it
   does not construct `StrategicUpdate(` with `current_project_id_set=` directly and does reach
   the shared `evaluate_project_switch()` call at `intelligence.py:1494` (confirmed: every
   `best_candidate.kind` branch, including `ADVENTURE_ROUTE`, falls through to this same call —
   no separate commit path exists for adventure routing).
6. **`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`** — 6 test
   functions (confirmed: `test_filters_out_locked_projects`,
   `test_apply_respects_active_system_b_lock`, `test_apply_switches_when_candidate_clears_bar`,
   `test_zero_regression_human_practical_humanoid_hero_archetype_native`,
   `test_zero_regression_human_practical_humanoid_hero_legacy_guard_shape`,
   `test_adventure_decision_does_not_discard_earlier_phase_updates`). Retarget each
   `AdventureDecisionPhase.apply(state)` call to
   `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)` (or
   `fused_strategic_pass(state, StateUpdate(), cadence=None)` for whichever test iterates
   multiple entities at once), asserting on the resulting `StrategicUpdate`/`StateUpdate`'s
   `current_project_id_set`/`projects_add_or_update` instead of the old
   `update.entity_updates`-shaped assertions.
7. **`tests/perf/test_phase3_adventure_decision_budget.py`** —
   `test_phase3_adventure_decision_perf_budget` (confirmed at line 57, 105 entities at line 63,
   70.0ms budget at line 88). Retarget to loop `AdventureGoalScorer().score(entity, state)` over
   the same 105 entities (isolating adventure-scoring cost specifically, the fairest analog to the
   old phase's per-tick loop cost, rather than the much broader `evaluate_strategic_intent()`
   which includes tiers 1-4). **Remeasure and set the budget from the real measurement** — do not
   assume the existing 70.0ms threshold transfers unchanged to the new call path.
8. **`tests/unit/observability/test_event_extractor_agency2.py`** —
   `test_defer_property_name_constant_matches_phase_and_extractor` (confirmed at lines 432-439,
   `TestAntiDriftGuards` class). Since Step 4 resolves Risk #0 as an accepted divergence (not
   ported), rewrite this test to assert the current, disclosed state honestly rather than delete
   it: assert `"last_defer_reason"` does **not** appear in
   `inspect.getsource(AdventureGoalScorer.score)` (documenting the gap exists), and add a
   docstring/comment referencing `docs/guidelines/intentional_divergences.md`'s new
   "Adventure-Route Defer-Reason Observability Gap" entry (Step 4) by name, so a future engineer
   who adds partial wiring here is prompted to update that doc entry too. Keep the existing
   assertion that `"last_defer_reason"` still appears in `inspect.getsource(EventExtractor
   .extract)` unchanged (line 438-439) — the extractor side is untouched and correct.
9. **`tests/unit/content/test_content_usage_matrix.py`** —
   `test_living_family_marked_resolved_partially_until_runtime_consumer` (confirmed: comment at
   line 209, real assertion at line 222 `assert "AdventureDecisionPhase" in
   cognition_entry.runtime_consumer_evidence`). This requires the underlying content metadata's
   `runtime_consumer_evidence` string (source: wherever `CONTENT_USAGE_MATRIX["living/
   cognition_profiles"]` is declared — locate via `grep -rn "living/cognition_profiles"
   src/content/` before editing) to be updated to reference `AdventureGoalScorer` instead of
   `AdventureDecisionPhase`, then update this test's assertion to match
   (`assert "AdventureGoalScorer" in cognition_entry.runtime_consumer_evidence`). Update the
   line-209 comment too (currently "AdventureDecisionPhase.apply() reads
   supports_adventure_routing").

**6 comment-only files require no code change** (confirmed via investigation.md's grep context,
not independently re-verified line-by-line in this planning pass since they carry no executable
dependency): `test_craft_upgrade_execution.py`, `test_threat_resolved_lock_release.py`,
`test_event_extractor_social_faction.py`, `test_resource_region_coverage_corpus.py`,
`test_scenario_feature_flag_defaults.py`. Do not edit these files' code; a stale docstring/comment
mentioning the deleted class name is not an AC violation.

**Do NOT touch:** any test file's assertions or fixtures beyond what's needed to retarget the
call site named above — do not use this migration as an opportunity to also refactor unrelated
parts of these files.
**Verify:** each item's own migrated test(s), run via the Scoped Pytest Command in
test_plan.md.

### Step 6 — Port one assertion from, then delete, the shadow-migration-parity test file

**Files:** `tests/unit/strategic/test_adventure_route_materialization.py`,
`tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

**Change — strict order, do not reverse:**
1. **First**, port into `test_adventure_route_materialization.py` (append near the end of the
   file, after its existing tests): the `_diff_routes(phase_family, phase_raw_score,
   scorer_family, scorer_raw_score, phase_utility=None, scorer_utility=None)` helper function,
   copied verbatim from `test_adventure_shadow_migration_parity.py:99-116` (confirmed by direct
   read — a small, self-contained, test-local pure function with no production-code dependency,
   so it must be copied, not imported, since it lives only in the file being deleted), and the
   test `test_shadow_diff_report_separates_raw_score_from_utility_mismatches` (confirmed at
   lines 372-398), unchanged in body — it exercises `_diff_routes()`'s own report *shape*
   (`raw_score_mismatches`/`family_mismatches`/`utility_mismatches` kept separate), which is a
   real, independently-valuable regression guard against the scale-mismatch defect class
   `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` fixed, and does not depend on
   having two live decision paths to diff.
2. **Only after** step 1 lands and passes, delete
   `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py` in full (all
   24 tests, including `test_delete_adventure_decision_phase_ac1_already_encodes_the_gate` and
   `test_shadow_scenario_neither_path_mutates_state` — their premise, diffing two coexisting
   decision paths, no longer applies once `AdventureDecisionPhase` does not exist; they were
   explicitly transitional scaffolding per the design doc §7 step 2's own framing, not intended
   permanent coverage).
**Do NOT touch:** `test_adventure_route_materialization.py`'s existing tests (imports at
lines 1-21, entity/state helpers) — only append the new helper + test.
**Verify:** `test_shadow_diff_report_separates_raw_score_from_utility_mismatches` passes in its
new location; `test_adventure_shadow_migration_parity.py` no longer exists (`test -f` returns
false).

### Step 7 — Update parity ledger entries (STRAT-236, STRAT-252, STRAT-253)

**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:**
- **STRAT-236** (`- id: STRAT-236` at line 2708 through line 2737, confirmed via `grep -n "^- id:
  STRAT-236\|^- id: STRAT-237"`; P1, verified): its `v2_evidence` block (starts line 2721) ends
  "...the widened lock-expiry condition inside evaluate_project_switch()'s locked-branch gate.
  AdventureDecisionPhase's own pre-filter at src/domains/adventure/phase.py:129 remains a
  separate, still-active gate." (lines 2725-2726, confirmed by direct read this session). Remove
  that sentence entirely (that gate no longer exists post-deletion) — end the `v2_evidence`
  clause after "...locked-branch gate," plus the existing cap citation that follows (lines
  2727-2730). Update `test_path` (block starts line 2732, three `|`-separated entries at lines
  2733-2735): the third cited test,
  `tests/unit/systems/test_spawn_lock_condition.py::TestLockEarlyRelease
  ::test_lock_released_when_hp_high_and_no_hostiles`, must be re-pointed to whatever test
  name/class Step 5 item 4's migration produces (confirm the exact surviving name once Step 5
  item 4 is implemented — do not guess it here).
- **STRAT-252** (lines 3255-3318, P2, verified): `text` currently ends "This is NOT yet the
  live/wired decision path. `AdventureDecisionPhase` (src/domains/adventure/phase.py, registered
  in src/engine/pipeline.py) is completely unmodified and remains the sole active
  adventure-decision mechanism in a live simulation run." — this sentence is now false. Replace
  with a sentence stating `AdventureGoalScorer` is now the sole live adventure-decision mechanism,
  `AdventureDecisionPhase` has been deleted (cite this ticket ID), and its own prior
  `v2_evidence` citations (all `src/ai/goals/adventure_scorer.py`/`intelligence.py` references)
  remain valid unchanged (confirmed by investigation.md: no `phase.py` citations exist in
  STRAT-252's own `v2_evidence`, only in its `text`).
- **STRAT-253** (`- id: STRAT-253` at line 3319 through end-of-file at line 3394, confirmed via
  `grep -n "^- id: STRAT-253"` plus `wc -l` showing no further `- id:` entry follows it, P1,
  verified): this entry needs updates in **four** fields, not just `text`/`test_path` —
  confirmed by direct read of the full entry this session:
  - `text` (from line 3320) narrates "the not-yet-wired path" (line 3323) — update to past
    tense / resolved framing (`AdventureGoalScorer`/tier-5 materialization is now the sole live
    path).
  - `test_path` (block starting ~line 3366) is **entirely** the file being deleted in Step 6 —
    since the shadow suite's premise (proving two live paths agree) is retired, not merely
    relocated, update `status` (currently `verified`, line ~3345) to reflect that this entry now
    documents *historical* migration evidence rather than live-passing coverage: set `status:
    legacy_verified` (per CLAUDE.md's status enum: `verified`/`divergent`/`missing`/
    `unsupported`/`legacy_verified`) and rewrite `test_path` to point at the one assertion that
    survives (Step 6): `tests/unit/strategic/test_adventure_route_materialization.py
    ::test_shadow_diff_report_separates_raw_score_from_utility_mismatches`.
  - `v2_evidence` (from line ~3348): update to note the other 23 tests' evidence is historical
    (this ticket's own commit is the record) and no longer independently re-run.
  - `divergence_note` (from line 3376, confirmed by direct read): currently states "this entry
    documents a parity proof between two co-existing, currently-non-live-switched decision paths
    (`AdventureDecisionPhase` is still the sole live path; see STRAT-252)" — this sentence is now
    false post-deletion and **must** be updated (found independently in this planning pass, not
    called out by investigation.md's own Docs Requiring Update list — a real gap that list
    missed). Rewrite to state the two paths no longer co-exist; `AdventureGoalScorer` is now sole
    live.
  - `support_boundary` (from line 3385, confirmed by direct read): currently states "`
    AdventureDecisionPhase` remains the sole active adventure-decision mechanism in a live tick
    (STRAT-252), and `AdventureGoalScorer` is reachable only through test harnesses/direct calls"
    — also now false, also **must** be updated (same independent finding). Rewrite to state
    `AdventureGoalScorer` is reachable through the live tier-5 pipeline path, not only test
    harnesses; keep the rest of the field's STRAT-185 disclaimer unchanged (still accurate — this
    entry still does not close STRAT-185).
**Do NOT touch:** any other `STRAT-*` entry in this file, including STRAT-185/186/187 (P0) — Step
9 only re-runs their existing `test_path`s as a sanity check, does not edit their ledger text.
**Verify:** `test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase` (new,
Step 8).

### Step 8 — Add the new architecture/doc guard tests

**Files:** new test additions, location per test_plan.md.

**Change:**
- `test_pipeline_module_has_no_adventure_decision_phase_reference` — asserts
  `"AdventureDecisionPhase"` does not appear in `inspect.getsource(src.engine.pipeline)`. Place
  in `tests/unit/systems/` or alongside the routing-guard tests in
  `tests/unit/domains/adventure/`.
- `test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source` — asserts
  `_resolve_cognition_profile_id`/`_supports_adventure_routing` exist in
  `src.ai.goals.adventure_scorer` with the identical `inspect.signature` as before relocation
  (byte-identical internals proven by the behavioral tests in Step 5 item 2 passing, since the
  functions physically moved files and cannot be textually diffed against deleted source).
- `test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase` — loads
  `docs/parity_ledger/strategic_cognition.yaml`, finds the `STRAT-236` entry, asserts
  `"AdventureDecisionPhase"` and `"phase.py:129"` do not appear in its `v2_evidence`. Mirrors the
  existing pattern `test_content_usage_matrix.py` already uses for ledger-adjacent string
  assertions.
- `test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase` — reads
  `docs/simulation/domains/adventure_contract.md`, asserts the "Engine Phase" section text
  (Step 9) does not contain `"AdventureDecisionPhase"`.
**Do NOT touch:** existing passing tests outside the scope of this ticket's own AC checks.
**Verify:** all four tests pass; these are also the AC2/AC3/AC5 regression guards.

### Step 9 — Update docs: `adventure_contract.md` and `04_strategic_cognition.md`

**Files:** `docs/simulation/domains/adventure_contract.md`,
`docs/mechanics/04_strategic_cognition.md`

**Change:**
- `adventure_contract.md`'s "Engine Phase" section (confirmed at lines 23-36): currently titled
  "Adventure Decision stage — `AdventureDecisionPhase.apply(state, context)`" with its own
  eligibility/lock table. Rewrite to describe the tier-5 `GoalRegistry`/`AdventureGoalScorer`
  mechanism as the live path: `AdventureGoalScorer.score(entity, state)`, invoked via
  `GoalRegistry.get_all_scores()` inside `StrategicIntelligenceSystem
  .evaluate_strategic_intent()`, subject to the same tier-5 utility floor (20.0) and
  `SystemCadence` throttling every other `GoalKind` scorer respects. Keep the eligibility
  criteria table's content (cognition profile / alive / active / project lock) — those checks
  are unchanged, only their call site changed.
- `04_strategic_cognition.md` line 30 (confirmed current text: "**New tier-5 candidate, not yet
  live...** ... `AdventureDecisionPhase`, described above, remains the sole active/wired
  adventure-decision mechanism. The tier-5 cutover (retiring `AdventureDecisionPhase`) is a
  separate, later, explicitly-gated ticket.") — this is stale even pre-deletion (investigation.md
  confirms it was already false before this ticket, since `AdventureGoalScorer` already won
  tier-5 arbitration whenever it was evaluated), and definitely false post-deletion. Rewrite to
  state `AdventureGoalScorer` is the sole live adventure-decision mechanism, registered
  unconditionally in `GoalRegistry`, cite this ticket ID as the cutover. **Do not** use this as
  license to audit/fix other potentially-stale claims elsewhere in this chapter — only this
  passage and line 311, which this ticket's own deletion makes newly/differently wrong.
- `04_strategic_cognition.md` line 311 (confirmed current text: "`FactionDecisionPhase.execute()`
  runs every tick before `AdventureDecisionPhase` in the pipeline, producing a
  `list[FactionDirective]`..."): the referenced phase no longer exists. Rewrite to describe how
  `faction_directives` reaches `AdventureRouteScorer.score()`'s §2b block now — confirmed by
  direct read of `adventure_scorer.py:73-83`: **it does not** reach the scorer today
  (`AdventureGoalScorer.score()` passes `faction_directives=None` to `decide()`, disclosed as a
  known simplification since this scorer is not the pipeline-wired-with-faction-directives
  ticket's job) — state this honestly rather than imply parity that doesn't exist.
**Do NOT touch:** any other section of either doc.
**Verify:** `test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase`
(Step 8).

### Step 10 — Verify-phase SimQ regression re-check (non-optional)

**Files:** none changed; verification-only step.

**Change:** After Steps 1-9 land, re-run:
```
pytest tests/simulation_quality/test_grade_regression.py -k "simq_routing_test or hero_guild_routing" -m "not slow" -q
```
Per investigation.md's resolution: this discharges design doc §7 step 4's "full-corpus SimQ
re-run to catch any behavior regression the shadow test's synthetic scenarios missed" obligation
for *this* ticket's own cutover action. Ticket 3
(`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`) already tracks a
pre-existing, non-regressing `ANCHORS_STILL_FAILING` finding from before this ticket's action —
this re-run's job is only to confirm no **new** failures appear beyond that already-disclosed set.
If new failures appear, report them truthfully in the ticket's Completion Summary and do not fold
them silently into the existing follow-up ticket's scope (per CLAUDE.md's Gate Integrity rule) —
flag for a decision on whether a new ticket is needed.
**Do NOT touch:** `tests/simulation_quality/test_grade_regression.py` itself, `score_ceilings
.json`, or `grade_anchors.json` — those belong to
`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`'s own scope, not this
ticket.
**Verify:** re-run output recorded in the ticket's Test Summary/Completion Summary.

### Step 11 — Full scoped regression run

**Files:** none changed; verification-only step.

**Change:** Run the full scoped pytest command from test_plan.md (covers all touched unit/
integration/perf files from Steps 1-9), plus a sanity re-run of STRAT-185/186/187's own
`test_path`s (`tests/unit/strategic/test_score_normalization.py
::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate` and
`::test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`) to confirm they
still pass post-deletion — a sanity check only, since `evaluate_project_switch()`'s locked-branch
logic no longer has `AdventureDecisionPhase.apply()` as one of its callers, but this ticket does
not re-derive their proofs.
**Verify:** all listed tests pass; record pass/fail counts in the ticket's Test Summary.

## Scope Guards

- **Do not** touch `_threat_resolved()`'s relocation or `evaluate_project_switch()`'s signature —
  that is `THREAT-RESOLVED-ARBITER-RELOCATION`'s already-landed work; this ticket only calls the
  already-relocated helper, never redefines it.
- **Do not** touch STRAT-185, STRAT-186, or STRAT-187 (P0) ledger entries — Step 11 only re-runs
  their existing `test_path`s as a sanity check.
- **Do not** touch the SimQ audit follow-up ticket's own scope
  (`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`'s
  `tests/simulation_quality/test_grade_regression.py`'s `_within_band()`/`FAST_ANCHOR_KEYS`,
  `score_ceilings.json`, `grade_anchors.json`) — Step 10 only re-runs its test target, never edits
  it.
- **Do not** re-litigate or re-verify ticket 1's (`ADVENTURE-GOAL-SCORER`) or ticket 2's
  (`THREAT-RESOLVED-ARBITER-RELOCATION`) already-landed work beyond what's needed to confirm this
  ticket's own citations are current (e.g., re-verifying line numbers is in scope; re-deriving
  their design decisions, such as the `_resolve_placeholder_target_pos()` fix or the
  raw_score-vs-utility scale fix, is not).
- **Do not** remove `ENABLE_ADVENTURE_ROUTING`'s own definition
  (`src/domains/optimization/feature_flags.py`) or default-value config (`rollout_profiles.py`) —
  only its `pipeline.py` registration use.
- **Do not** widen `StrategicUpdate`'s schema to add `property_updates` in this ticket (Step 4's
  explicit decision) — that is future-ticket work, not this one's.
- **Do not** use the Mechanics Bible doc-staleness discovery (line 30/311) as license to audit or
  fix other potentially-stale content in `04_strategic_cognition.md` beyond those two passages.
- **Do not** delete `test_adventure_shadow_migration_parity.py` before porting the
  `_diff_routes()`/assertion pair into `test_adventure_route_materialization.py` (Step 6's
  sequencing is mandatory, not a suggestion).
- **Do not** silently delete `test_decision_trace.py`'s or `test_event_extractor_agency2.py`'s
  coverage for the two observability gaps — Steps 3/4/5(items 1,8) require either a working
  migrated test (decision trace) or an honest gap-documenting test (defer reason), never a
  silent removal.

## Dependency Map

- Step 1 (relocate helpers) must land before Step 2 (delete class) — Step 2's deletion assumes
  the helpers already live in `adventure_scorer.py`.
- Step 1 must land before Step 3 (port decision trace) and Step 5 item 2 (eligibility test
  migration) — both call the relocated functions directly.
- Step 3 must land before Step 5 item 1 (decision-trace test migration) — the test exercises the
  ported call.
- Step 4 (divergence doc) must land before Step 5 item 8 (defer-reason guard test migration) —
  the test references the divergence entry by name.
- Step 5 (all 9 file migrations) should land before Step 2's deletion is finalized in the working
  tree, in practice: since several of these tests currently import `AdventureDecisionPhase`
  directly, a strict "delete first" ordering would leave the test suite broken mid-implementation.
  Recommended sequencing: implement Steps 1, 3, 4 (additive), then Step 5 (migrate tests to the
  new path while the old class still exists, confirming the new path already produces equivalent
  behavior), then Step 2 (delete), then Step 6 (shadow-file port+delete), then re-run the full
  suite.
- Step 6's port-then-delete ordering is internally sequenced (see Step 6 itself) and does not
  depend on Steps 1-5 beyond `test_adventure_route_materialization.py` already existing (it does,
  pre-ticket).
- Step 7 (parity ledger) depends on Step 5 item 4's surviving test name (STRAT-236's `test_path`
  re-point) and Step 6 (STRAT-253's `test_path` re-point) — do Step 7 last among the doc/ledger
  steps.
- Step 8 (new guard tests) depends on Steps 1, 2, 7 being complete (asserts their end states).
- Step 9 (docs) depends on Step 2 (describes the post-deletion mechanism) and can be done in
  parallel with Step 7/8.
- Step 10 and Step 11 (Verify-phase) must run last, after all other steps land.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — Implement doesn't proceed until C1 (`ADVENTURE-GOAL-SCORER`) and C4 (`ADVENTURE-SHADOW-MIGRATION-GATE`) are both in `tickets/done/` | Pre-condition, checked at Scope (not a Plan step — both are confirmed DONE per investigation.md's Prior Work section) | N/A — Scope-phase gate, not a test |
| AC2 — `AdventureDecisionPhase` class and its `pipeline.py` registration removed; grep returns no matches | Step 2 | `test_pipeline_module_has_no_adventure_decision_phase_reference` (Step 8) |
| AC3 — `_resolve_cognition_profile_id`/`_supports_adventure_routing` exist byte-identical in `AdventureGoalScorer`'s module, same inputs/outputs | Step 1 | `test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source` (Step 8) + migrated `test_eligibility_cognition_profile.py` (Step 5 item 2) |
| AC4 — all dependent tests (corrected: 9, not 5-6) migrated with equivalent coverage | Steps 5, 6 | Full scoped pytest run (Step 11) + each item's own migrated test |
| AC5 — STRAT-236 + `adventure_contract.md`'s Engine Phase section no longer reference `AdventureDecisionPhase`/`phase.py` as live | Steps 7 (STRAT-236, plus STRAT-252/253 as directly-entangled parity entries), 9 (`adventure_contract.md`, plus `04_strategic_cognition.md` since investigation confirms this ticket's action makes it newly wrong) | `test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase`, `test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase` (Step 8) |

## Anti-Drift Notes

- **The "already live" finding is load-bearing for how this ticket should be reviewed**: this is
  not a first-time behavior flip, so a reviewer should not expect (or require) the kind of
  pre/post behavior-diff evidence a genuine cutover would need — the shadow-parity suite (Step 6)
  already proved the two paths agree before this ticket touched anything, and Step 10's SimQ
  re-check is the correct scoped verification for what actually changes (removing duplicate
  compute + cadence-skipped-entity coverage), not a full behavior-parity re-proof.
- **`_PROFILE_ELIGIBILITY_CACHE`'s module-level (cross-tick) lifetime in `adventure_scorer.py`
  vs. `phase.py`'s old per-`apply()`-call (fresh-per-tick) lifetime is a deliberate, already-
  reviewed prior decision** (ticket 1's own design) — do not "fix" this into a per-tick cache
  during Step 1's relocation.
- **Risk #0 (`last_defer_reason`) is deliberately NOT ported** — do not let Implement quietly
  attempt a partial port (e.g., threading a `property_updates` field only through
  `evaluate_strategic_intent()`'s existing return sites, without also modifying the shared tier-5
  floor-filter loop itself at `intelligence.py:1394-1414`) without also either (a) doing the full
  shared-loop special-casing plus the `StrategicUpdate` schema widening properly, or (b) sticking
  with Step 4's divergence-doc decision. A half-done port is worse than either extreme — since the
  signal is discarded by the utility-floor check (`intelligence.py:1412`) upstream of every one of
  `evaluate_strategic_intent()`'s return sites (Step 4), a change confined only to those return
  sites would silently do nothing for any entity, which is exactly the kind of undisclosed
  durable-state inconsistency CLAUDE.md's Durable State Rule forbids.
- **Risk #1 (decision trace) IS ported, but only inside `AdventureGoalScorer.score()`'s own
  method body** — do not also add a second write site anywhere in `intelligence.py`'s
  materialization branch; the scorer-level site (Step 3) already covers every entity `score()`
  evaluates, matching the old phase's per-hero-loop coverage exactly. A second write site would
  double-write the same trace.
- **STRAT-236's `test_path` re-point (Step 7) depends on knowing the exact surviving test
  name/class from Step 5 item 4's migration** — do not guess or pre-fill this ledger citation
  before Step 5 item 4 is actually implemented; verify the real final test name at that point.
- **The `04_strategic_cognition.md` line-30 doc-staleness predates this ticket** (investigation.md
  confirms it was already false before this ticket's own action) — Step 9 fixes it because this
  ticket's Related Docs already touch this exact subsystem and deletion makes the doc's framing
  fully obsolete either way, not because this ticket is retroactively responsible for the
  pre-existing gap. Do not expand Step 9 into a broader Mechanics-Bible-parity audit ticket.
- **Faction directives are not threaded into `AdventureGoalScorer.score()`'s `decide()` call**
  (confirmed `faction_directives=None` at `adventure_scorer.py:94`, disclosed simplification per
  ticket 1's own comment at lines 73-83) — this is unrelated to this ticket's own scope (wiring
  faction directives into the tier-5 path belongs to whatever ticket eventually threads it, not
  named in this epic's 4 tickets) and Step 9's doc update should state this honestly rather than
  imply the new path already has faction-directive parity with the old one.

## Deviations (recorded during Implement, per CLAUDE.md's Workflow Rule)

1. **2 additional real-dependency test files beyond the 9 named in Step 5**, found during
   implementation: `tests/unit/ai/goals/test_adventure_goal_scorer.py` and
   `tests/unit/strategic/test_adventure_route_materialization.py` both monkeypatched
   `"src.domains.adventure.phase._supports_adventure_routing"` by string path — a dependency on
   the deleted module's *import path*, not on the `AdventureDecisionPhase` *class name* the
   investigation's grep specifically searched for, so it escaped the 9-file blast-radius count.
   Fixed mechanically by retargeting both monkeypatch strings to
   `"src.ai.goals.adventure_scorer._supports_adventure_routing"` — a direct, unavoidable
   consequence of Step 1's relocation, not a scope expansion.
2. **Step 3's suggested patch targets for `test_decision_trace.py`'s migrated test
   (`"src.ai.goals.adventure_scorer.AdventureRouteGenerator.generate"` etc.) do not work as
   literally stated** — `AdventureRouteGenerator`/`AdventureDecisionService`/opportunity
   providers are function-local imports inside `score()` (deliberately kept lazy per Step 1's own
   Anti-Drift Hazard for the constants import), so they never become module-level attributes of
   `adventure_scorer` for a string-path `patch()` to resolve. Implemented instead by importing
   the real classes in the test and patching them directly via `patch.object(ClassObj, "method",
   ...)` — the same pattern `test_adventure_route_materialization.py` already uses via
   `monkeypatch.setattr(ClassObj, ...)` — which patches the shared class object regardless of
   which module holds a (lazy) reference to it.
3. **`test_spawn_lock_condition.py`'s migration needed explicit profile/score calibration, not
   just a call-site swap.** Under the default `CognitionProfile` (`resistance_multiplier=30.0`),
   `effective_current_score >= 9.0` always, which no ADVENTURE_ROUTE-scale raw score (ceiling
   2.9) can ever exceed in `evaluate_project_switch()`'s final unconditional raw-score check —
   and a near-ceiling synthetic candidate's `candidate_pct` always clears the 0.8 urgency floor
   regardless of `_threat_resolved`, independent of lock status. Either property alone would make
   "lock released" indistinguishable from "lock held" by a `current_project_id_set` assertion.
   Fixed by giving `_make_locked_hero` a zero-margin `CognitionProfile` and calibrating the
   injected candidate's `raw_score` (1.5) to sit strictly between the urgency-floor cutover and
   the (now small) `effective_current_score`, isolating the `_threat_resolved` mechanism the test
   actually targets.
4. **`test_filters_out_locked_projects` (`test_phase3_adventure_decision_phase.py`) required a
   test-setup fix, not just a call-site swap.** `b.replace_self_model(None)` — an unrelated
   pre-existing artifact in the test's own setup — crashed
   `AdventureRouteGenerator.generate()`'s real `entity.self_model.self_awareness` read once route
   generation became reachable for a locked entity (the deleted phase's own pre-filter used to
   prevent this entity from ever reaching the generator at all when locked; the surviving tier-5
   path runs the scorer unconditionally). Removed the unnecessary `replace_self_model(None)`
   call; `V2EntityBuilder`'s own default (`SelfModelBundle()`) is what the test's comment
   ("simple default self model") already intended.
5. **STRAT-252's `support_boundary` field was also updated**, not only `text` as Step 7 literally
   enumerated for this entry — left unmodified it would state "no pipeline.py phase currently
   drives a live tick through this path," which is false post-deletion. Same shape of gap the
   plan itself already found and fixed for STRAT-253's `divergence_note`/`support_boundary`
   ("found independently in this planning pass, not called out by investigation.md's own list").
6. **STRAT-236's `test_path` needed no re-pointing** — the migrated
   `test_lock_released_when_hp_high_and_no_hostiles` kept its exact pre-migration name (only
   gained a `monkeypatch` fixture parameter), so Step 7's anticipated re-point was unnecessary;
   the existing citation is already correct.
7. **Step 10's SimQ re-check surfaced 2 additional failures beyond the 4 items
   `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` discloses**
   (`simq_routing_test_seed123_500t`, `hero_guild_routing_seed123_500t`, both score-tolerance
   failures, not grade-band crossings). Confirmed NOT a regression from this ticket: the
   underlying `data/calibration/{run_key}/quality_report.json` files these tests read (this
   ticket never runs calibration/simulation generation) have mtimes ~5.7 hours before this
   implementation session started. Reported per Step 10's own instruction rather than folded
   into the existing follow-up ticket's scope or fixed by touching the explicitly out-of-scope
   `FAST_ANCHOR_KEYS`/`grade_anchors.json`/`score_ceilings.json`.
8. **A 3rd, wholly unrelated test failure was discovered during the Step 11 full scoped run**:
   `tests/integration/test_scenario_feature_flag_defaults.py::test_feature_flag_defaults_are_stable_across_instances`
   fails because `ENABLE_PUSH_EVENT_SHAPERS` has been hardcoded to `FeatureMode.ON` in
   `src/domains/optimization/feature_flags.py` since commit `11b83f37` (2026-08-08, an unrelated
   push-event-shaper epic) — confirmed pre-existing via `git log`/`git blame`, fails even in
   complete file isolation, and touches no file this ticket's diff modifies. Reported, not fixed
   (fixing would mean altering either a deliberate-looking production default or the test's own
   assertion, both outside this ticket's scope and risk).
9. **Post-Verify cleanup pass (5 findings from a follow-up Architecture-Verify NEEDS_CHANGES),
   not part of the original 11-step plan**: an orphaned `"adventure_decision"` entry in
   `PhaseDependencyGraph.PHASES` (`src/engine/phase_graph.py:66`), a stale phase-name reference in
   `faction_decision.py`'s module docstring, a stale phase-table row + count (32->31) in
   `docs/engine/authoritative_pipeline.md` (this ticket's own Step 9 doc-update pass missed this
   file despite touching 9 other closely-related docs), a false "gates behavior" claim about
   `ENABLE_ADVENTURE_ROUTING` in `docs/engine/known_limitations.md` §1.5, and a stale
   "unwired from pipeline.py, C3 must decide" comment in `adventure_scorer.py` (~lines 105-117)
   that this ticket's own diff directly contradicted. All 5 are cleanup gaps left behind by the
   deletion, not problems with the deletion logic itself — fixed in a follow-up pass, scoped
   regression re-run confirmed no new failures (149 passed, 2 pre-existing
   `test_harvest_to_event.py` failures already tracked above, reconfirmed unrelated via
   stash-and-rerun).
