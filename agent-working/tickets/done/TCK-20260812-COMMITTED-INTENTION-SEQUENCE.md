---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260812-COMMITTED-INTENTION-SEQUENCE
phase: done
date: 2026-08-12
tags: [cognition, strategy, progression]
---

# TCK-20260812-COMMITTED-INTENTION-SEQUENCE

## Title
Implement `CommittedIntention` durable multi-step planning model

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Follow-up implementation ticket for the accepted design in
`docs/architecture/2026-08-12-multi-step-persistent-planning-design.md`
(`TCK-20260811-MULTI-STEP-PLANNING-DESIGN`, decision: GO). That ticket was design-scoping only —
no production code — and produced a fully-specified but unimplemented model: a new
`CommittedIntention` durable typed record letting an entity commit to a short (2-4 step) ordered
sequence of future intentions (e.g. train -> craft -> quest) rather than re-deciding the single
next action every eligible tick, materialized one step at a time as an ordinary tier-5
`GoalRegistry` candidate through the existing, **unmodified** `evaluate_project_switch()` arbiter.

## Scope
- Add `CommittedIntention` frozen dataclass (`intention_id`, `goal_kind`, `target_hint`,
  `sequence_index`, `status`) and a `committed_intentions: Tuple[CommittedIntention, ...]` field on
  `StrategicComponent` (`src/core/strategic.py`), per the design doc's Design §2
- Add `max_committed_intentions: int = 3` to `CognitionProfile` (`src/core/strategic.py`), per
  Design §2
- Add the materialization hook that feeds `committed_intentions[0]` into `evaluate_strategic_intent()`'s
  tier-5 candidate field when due (current project absent/abandoned/completed), using the same
  per-`goal_kind` mapping pattern already established for tier-5 winners (`RouteToProjectMapper`
  precedent) -- per Design §4
- Implement "losing candidate stays queued, doesn't get discarded" retry semantics: a committed
  intention that loses one tick's arbitration remains at `sequence_index` 0 and re-competes next
  eligible tick until it wins, is explicitly abandoned, or is skipped -- per Design §4. This
  bookkeeping lives entirely in the new `committed_intentions` tracking, not inside
  `evaluate_project_switch()` itself
- Add the Mechanics Bible update (`docs/mechanics/04_strategic_cognition.md`) and a new parity
  ledger entry (`docs/parity_ledger/strategic_cognition.yaml`) documenting the landed mechanism,
  per Design §7 (deferred, not performed by the design-scoping ticket)
- Cap sequences at `max_committed_intentions=3` entries -- no branching, no conditional sequences
  (MVP scope, not the design doc's full illustrative generality)

## Out of Scope
- Any change to `evaluate_project_switch()`'s own code, signature, or the STRAT-236
  `_threat_resolved()` lock-expiry check -- the design's central premise is that committed
  intentions compete as an ordinary, unmodified tier-5 candidate; changing the arbiter itself would
  invalidate that premise and require re-verifying STRAT-185/186/187
- Any change to `ProgressionPlan.goal_queue`, `PlanRevisionService`, or
  `ProgressionPlanExporter`/`Importer` -- the design doc's Design §3 establishes these coexist with
  clearly separated, non-overlapping responsibility; this ticket does not blur that boundary
- Any new `GoalKind`/`GoalScorer` -- committed intentions reuse the existing `GoalKind` vocabulary
  per Design §2
- UI/observability surface beyond the Durable State Rule's minimum (inspection/debug visibility) --
  the exact surface shape (EntityInspector field, decision-trace entry, dedicated debug endpoint)
  is one of the design doc's own genuinely-open implementation questions, not pre-decided here
- Repurposing `CognitionProfile.reserved_detour_depth` -- the design doc's Design §5 confirmed this
  field is unrelated (bounds reactive detour-chain nesting, not proactive intention sequencing)

## Acceptance Criteria
- [x] `CommittedIntention` dataclass and `committed_intentions` field added to `StrategicComponent`,
      matching the design doc's Design §2 sketch (frozen, `slots=True`-consistent pattern)
- [x] `max_committed_intentions` field added to `CognitionProfile`, defaulting to 3
- [x] `evaluate_strategic_intent()` materializes `committed_intentions[0]` (when due) into tier 5's
      candidate field as one ordinary candidate -- no new tier, no bypass, `evaluate_project_switch()`
      itself byte-identical (verify via `git diff --stat -- src/systems/strategic_systems/intelligence.py`
      touching only the materialization/injection point, not the arbiter function's own body)
- [x] Losing committed intentions are retried next eligible tick, not discarded -- regression test
      proves a losing candidate's `sequence_index`/status persist across a tick where it loses
      arbitration
- [x] `docs/mechanics/04_strategic_cognition.md` and `docs/parity_ledger/strategic_cognition.yaml`
      updated in the same session, per CLAUDE.md's Authoritative Mechanics Rule
- [x] STRAT-185/186/187 (`docs/parity_ledger/strategic_cognition.yaml`) re-run and confirmed still
      passing unmodified, since this ticket's design explicitly claims no new arbiter path requires
      their re-verification -- confirm that claim empirically, not just by citation
- [x] The genuinely-open implementation questions from the design doc are resolved with explicit,
      documented decisions (not silently defaulted): the `max_committed_intentions=3` cap's
      validation, mid-sequence-skip abandonment semantics, `target_hint` re-resolution-failure
      handling, whether `ProgressionPlan.goal_queue` should auto-seed `committed_intentions`, and the
      observability-surface shape

## Related Tickets
- TCK-20260811-MULTI-STEP-PLANNING-DESIGN (DONE -- the design-scoping ticket that produced the
  accepted design this ticket implements)
- TCK-20260619-E61-PROGRESSION

## Related Docs
- docs/architecture/2026-08-12-multi-step-persistent-planning-design.md (the accepted design this
  ticket implements)
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml
- docs/simulation/domains/progression_planner_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/core/strategic.py (`StrategicComponent`, `CognitionProfile`)
- src/systems/strategic_systems/intelligence.py (`evaluate_strategic_intent()`'s tier-5
  materialization point)

## Assumptions / Open Questions
- The design doc's own "Open Questions For Implementation" section lists 5 genuinely-unresolved
  details this ticket's Investigate/Plan phases must resolve with real implementation-time
  judgment, not treat as pre-decided: (1) whether `max_committed_intentions=3` is empirically
  right, (2) mid-sequence-skip abandonment semantics, (3) `target_hint` re-resolution-failure
  handling, (4) whether `goal_queue` should auto-seed `committed_intentions`, (5) the
  observability-surface shape
- The design doc traced and confirmed a duplicate-`GoalKind` coexistence scenario (a committed
  intention reusing a kind with a currently-registered live scorer) is structurally harmless against
  current code (`intelligence.py:1393-1408`'s two `.kind` consumers are both duplicate-tolerant) --
  this ticket's Investigate phase should re-verify this trace still holds against the code as it
  exists when this ticket is actually implemented, not assume it's still true unchanged

## Implementation Notes

Implemented all 14 steps of `staging_artifacts/TCK-20260812-COMMITTED-INTENTION-SEQUENCE/plan.md`
exactly as designed. No deviations from the plan's Steps 1-11 code changes; test placement choices
used the plan's explicitly stated flexibility (see below). Key points:

- **`evaluate_project_switch()` is provably byte-identical.** Golden SHA-256 hash
  (`635bc4f274f3110c8bd0c130a85bc548e517b4247df33cf426bcec81e6eb80f3`) was computed directly from
  the pre-implementation repo state and pinned in
  `tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py`, added *before*
  Step 7's edits and re-verified passing *after* all steps landed. `git diff --stat -- src/systems/
  strategic_systems/intelligence.py` hunks fall at lines ~52-99 (module constants/imports),
  ~1392-1436 (materialization hook, inside `evaluate_strategic_intent()`), and ~1565-1620
  (win-transition block, also inside `evaluate_strategic_intent()`) -- all strictly outside
  `evaluate_project_switch()`'s own line range (originally 972-1067).
- **Retry-on-loss (AC4, Step 8) required zero new code**, exactly as Design Decision 4/5
  predicted: the win-transition block only executes inside `if switch_up:`, so a losing
  arbitration leaves `committed_intentions` completely untouched. Proven end-to-end (not just by
  inspection) by `test_losing_committed_intention_retries_next_eligible_tick`, which runs the
  entity through two real ticks via the authoritative `StrategicPatch.apply()` path.
  `_COMMITTED_INTENTION_ELIGIBLE_KINDS` frozenset restricts materialization to the 10 pre-epic
  generic `GoalKind` values (Design Decision 2) -- an epic kind on the head is silently treated as
  not-due, never crashes (tested).
- **Win transition materializes via the generic branch** (`intelligence.py:1540-1558`,
  unmodified) because all 10 eligible kinds are `GoalKind` instances, never `ProjectKind` --
  `ProjectState.score == best_candidate.utility` is therefore scale-consistent by construction
  (Design Decision 5), NOT the `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`
  defect class recurring. This corrects test_plan.md's originally-proposed New Test 4 per plan.md
  Design Decision 6 -- implemented as
  `test_committed_intention_materializes_via_generic_branch_with_scale_consistent_score`, asserting
  `score == utility` (the opposite assertion of the three special-branch tests, correctly so for
  this feature).
- **Consume-side only (Out of Scope, honored).** No production write path was added anywhere in
  this ticket -- `committed_intentions` is fully wired through the authoritative apply path
  (`StrategicPatch.apply()`), replay fingerprinting, capacity enforcement, and observability, and
  will materialize correctly the instant any entity's `committed_intentions` tuple is populated,
  but nothing in production populates it. This is stated explicitly here, not left implicit, per
  the ticket's own Out of Scope and plan.md's Scope Guards.
- **All 5 previously-open design questions resolved** (plan.md Design Decisions 2, 7, 8, 9, 10,
  11) and each has a corresponding regression test: cap enforcement uses `CapacityService.trim_list`
  with an order-encoding `score_func=lambda ci: -ci.sequence_index` (never `trim_dict`, since
  `committed_intentions` is an ordered `Tuple`, not a `Dict`); mid-sequence-skip/auto-advance is
  explicitly NOT implemented (only `committed_intentions[0]` is ever read); `target_hint=None`
  reuses the arbiter's own existing target-floor check for a free "no-op, retry forever" (harmless
  since no write path in this ticket can ever produce one); `goal_queue` auto-seed is explicitly
  deferred to a future ticket (documented in the Mechanics Bible update, not silently dropped);
  observability surface added to the existing `EntityInspector.strategic_summary` dict (no new
  pydantic field, no new endpoint).
- **AC6 (STRAT-185/186/187) confirmed empirically, with the two different evidence types kept
  separate as required:** STRAT-186's `test_locked_system_a_current_interrupted_by_high_urgency_
  system_b_candidate` and STRAT-187's `test_locked_system_a_current_still_blocks_low_urgency_
  system_b_candidate` (both in `tests/unit/strategic/test_score_normalization.py`) were re-run
  after all 11 implementation steps landed and both PASS. STRAT-185 has no `test_path` (a
  pre-existing gap, not introduced by this ticket) -- its "still passing" claim is confirmed by
  inspection only: the golden-hash guard test passing proves `evaluate_project_switch()`'s
  retention-margin/`effective_current_score` computation is byte-identical to the
  pre-implementation state, which is the logic STRAT-185 covers.
- **Test placement choices** (all within plan.md's explicitly stated flexibility, not deviations):
  New Test 9 (cap enforcement) and New Test 11 (builder round-trip) both live in the new
  `tests/unit/strategic/test_committed_intention_model.py` rather than a separate
  `tests/unit/core/` builder-test file (none existed to extend). New Test 12 (observability
  surface) was added to the existing `tests/unit/observability/test_entity_inspector.py` rather
  than a new file, reusing that file's `_simple_entity`/`_dummy_manager` helpers. New Test 10
  (replay fingerprint) was added to the existing `tests/integration/kernel/test_p1_replay_fidelity.py`,
  exactly as plan.md recommended.
- **Beyond the plan's minimum test list**, three additional small regression tests were added in
  `test_committed_intention_materialization.py` to lock in Design Decisions 2/8/9 behaviorally
  (epic-kind no-op, `target_hint=None` no-op, non-`"pending"` head no-op) -- additive coverage, not
  a scope change.

## Test Summary

Full scoped regression run (per test_plan.md's Scoped Pytest Commands, all commands combined into
one run): 365 passed, 0 failed.

```
pytest tests/unit/strategic/ \
       tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py \
       tests/integration/kernel/test_p1_replay_fidelity.py \
       tests/unit/domains/adventure/ tests/integration/domains/adventure/ \
       tests/integration/pipeline/test_strategic_cadence.py \
       tests/unit/observability/test_entity_inspector.py \
       tests/unit/strategic/test_score_normalization.py -q
# 365 passed
```

STRAT-185/186/187 specific re-run (AC6), isolated:
```
pytest tests/unit/strategic/test_score_normalization.py -v
# test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current PASSED
# test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current PASSED
# test_locked_system_a_current_now_reachable_by_system_b_candidate_fix_confirmed PASSED
# test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate PASSED  (STRAT-186)
# test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate PASSED  (STRAT-187)
```

Architecture guard, run both before Step 7's edits and after all 11 steps landed -- passed both
times:
```
pytest tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py -v
# test_evaluate_project_switch_source_hash_unchanged PASSED
```

Also ran (not in test_plan.md's list, extra safety net since `StrategicComponent`/`StrategicUpdate`
gained new fields): `tests/unit/quest/`, `tests/unit/resource/`, `tests/unit/cognition/`,
`tests/unit/domains/information/` -- 282 passed, 0 failed.

New tests added: 8 in `test_committed_intention_model.py`, 8 in
`test_committed_intention_materialization.py`, 1 in `test_p1_replay_fidelity.py`, 2 in
`test_entity_inspector.py`, 1 architecture guard. Total 20 new tests, all passing.

`docs/parity_ledger/strategic_cognition.yaml`'s new `STRAT-256` entry was individually validated
against `docs/parity_ledger/schema.json` (passes; a pre-existing unrelated schema violation on
`FACTION-DIR-001` elsewhere in the file predates this ticket and is out of scope).

## Files Changed

Source:
- `src/core/strategic.py` -- `CommittedIntention` dataclass, `StrategicComponent.committed_intentions`,
  `CognitionProfile.max_committed_intentions`, `Tuple` import fix
- `src/core/builder.py` -- `V2EntityBuilder.strategic(committed_intentions=...)`, `CommittedIntention`/
  `Tuple` import fixes
- `src/core/updates.py` -- `StrategicUpdate.committed_intentions_add_or_update`/`_remove`,
  `is_noop()`/`merge()` updated, `CommittedIntention` `TYPE_CHECKING` import fix
- `src/engine/patches.py` -- `StrategicPatch.apply()`'s new `merge_committed_intentions()` helper
- `src/replay/fingerprint.py` -- `StateFingerprinter._strategic_identity()` includes
  `committed_intentions`
- `src/systems/strategic_systems/intelligence.py` -- materialization hook + win-transition block in
  `evaluate_strategic_intent()`; two new module-level constants; new `GoalScore` import;
  `evaluate_project_switch()` itself untouched (golden-hash-verified)
- `src/engine/pipeline_phases/capacity_enforcement.py` -- 7th enforcement block for
  `committed_intentions`, order-preserving `trim_list`
- `src/observability/live/entity_inspector.py` -- `strategic_summary` gains
  `committed_intentions_count`/`committed_intention_head`

Tests (new files):
- `tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py`
- `tests/unit/strategic/test_committed_intention_model.py`
- `tests/unit/strategic/test_committed_intention_materialization.py`

Tests (extended existing files):
- `tests/integration/kernel/test_p1_replay_fidelity.py`
- `tests/unit/observability/test_entity_inspector.py`

Docs:
- `docs/mechanics/04_strategic_cognition.md` -- new "Committed Intentions (Multi-Step Planning)"
  subsection under §4
- `docs/parity_ledger/strategic_cognition.yaml` -- new `STRAT-256` entry (P0, `status: verified`,
  populated `test_path`)

Graph:
- `graphify-out/` regenerated via `graphify update .` (AST-only, no doc/paper content changed)

## Completion Summary

Implemented the `CommittedIntention` durable multi-step planning model end-to-end on the
consume side: a new frozen dataclass and `StrategicComponent.committed_intentions` field,
threaded through every layer the Durable State Rule requires (authoritative merge via
`StrategicPatch.apply()`, replay fingerprinting, order-preserving capacity enforcement, debug
observability, and test-fixture construction), and materialized one step at a time as an
ordinary tier-5 `GoalScore` candidate that competes through the completely unmodified
`evaluate_project_switch()` arbiter (proven byte-identical via a golden-hash architecture guard
test). A losing committed intention is retried automatically the next eligible tick as a
structural consequence of the design (zero new "retry" code), and all 5 previously-open
implementation questions from the design doc are resolved with explicit, tested decisions. This
ticket implements no production write path -- the mechanism is fully wired but inert until a
future ticket seeds `committed_intentions` for real entities (e.g. from `ProgressionPlan.goal_queue`,
deliberately not touched here). All 20 new tests pass, the full regression surface (365 tests)
passes, and STRAT-185/186/187 are confirmed unregressed both empirically (186/187) and by
inspection (185, which has no `test_path`).
