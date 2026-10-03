---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE
artifact_type: investigation
tags: [observability, strategy, trace, decision-trace, duplicate-check]
---

# Investigation — TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE

## Context Scan Performed

1. `mcp__knowledge-search__search_docs` (query: "goal score history runner-up candidate scores
   cognition trace decision_trace EntityInspectionSnapshot") — top hits:
   - `docs/plans/audit_fix_plan.md` P1-H, marked **OPEN (confirmed still open 2026-07-03)**
   - `docs/observability/decision_trace_contract.md` §"Goal Score Cache (EntityInspector
     integration)" — describes exactly the feature this ticket asks for, already documented
   - `tickets/done/TCK-20260627-P1H-GOAL-RUNNERUP.md` — a **DONE** ticket (2026-06-27) whose
     title and acceptance criteria are near-verbatim identical to this ticket's
   - `docs/audits/D15_entity_decision_inspection.md` Gap 1 — marked **RESOLVED by
     TCK-20260619-E22A-TRACE-WRITER**
2. `graphify query "execute_brain goal scoring candidate EntityInspectionSnapshot decision_trace"`
   — returned the broad state/update/domain node graph; no direct new lead beyond confirming
   `EntityInspectionSnapshot` lives in `src/observability/live/entity_inspector.py` (community 12/observability).

**This context scan surfaced a direct conflict that required resolution before any implementation
work: a DONE ticket appears to have already implemented this exact feature, while the audit
tracking doc says the finding is still open.** Per CLAUDE.md's Context Scan / Clarification Rule
("Detect and stop on duplicate work"), the rest of this investigation resolves that conflict
against current source rather than assuming either doc is correct.

## Finding 1 — The feature is already fully implemented and tested

`git log`/ticket history: `TCK-20260627-P1H-GOAL-RUNNERUP` (status: historical, phase: done,
2026-06-27) implemented precisely this scope:

- `src/observability/cognition/decision_trace_writer.py::DecisionTraceWriter.write_trace()`
  (lines 84–133) sorts `scored_routes` descending by score, builds a `top3` slice, and emits:
  - `source_goal_score` — winner's score (rank 1)
  - `runner_up_scores` — `[{"goal_id", "score", "rank"}]` for ranks 2–3 (empty/truncated
    gracefully when fewer than 3 candidates exist)
  - a per-entity cache `_latest_goal_scores: Dict[int, List[Dict]]`, exposed via
    `get_latest_goal_scores(entity_id)`
- `src/observability/live/entity_inspector.py` — `EntityInspectionSnapshot.goal_scores:
  List[Dict[str, Any]]` (line 31) is populated from `_writer.get_latest_goal_scores(entity_id)`
  (line 142) inside `EntityInspector.inspect_entity()`.
- `docs/observability/decision_trace_contract.md` documents the full schema, including the new
  `runner_up_scores` field in the JSON schema block and a dedicated "Goal Score Cache" section.
- Tests exist and **pass now**: `tests/unit/observability/test_decision_trace.py` —
  `test_decision_trace_runner_up_scores_present`, `test_decision_trace_source_goal_score_present`,
  `test_decision_trace_runner_up_fewer_than_3`, `test_decision_trace_runner_up_single_candidate`,
  plus `test_decision_trace_routes_sorted_descending` and others (24 tests total in this file).
  Ran `pytest tests/unit/observability/test_decision_trace.py -q -m "not slow"` →
  **24 passed, 0 failed.**

Conclusion for Scope item 1 ("re-verify runner-up scores are still discarded"): **the
characterization is NOT accurate against current source.** Runner-up scores are retained,
serialized, cached, and tested today.

## Finding 2 — Why `docs/plans/audit_fix_plan.md` still says "OPEN"

The P1-H entry's `**Files:**` line lists `src/domains/adventure/phase.py`,
`src/observability/cognition/recorder.py` — these are the file names from the **original**
D15 finding (pre-fix). The 2026-07-03 re-check note says: *"No `runner_up`/`top_3`/
`candidate_scores` pattern found in `recorder.py` or `phase.py`."* That statement is literally
true but searches the wrong files:

- `phase.py` (`AdventureDecisionPhase.apply()`) only *calls* `_writer.write_trace(...)` — it never
  contained the sorting/runner-up logic itself (this is explicitly noted in the 2026-06-27
  ticket's Implementation Notes: *"`phase.py` was NOT modified — all sorting logic lives in the
  writer, not the call site."*).
- `src/observability/cognition/recorder.py` is a **different, parallel** observability channel
  (the cognition **graph snapshot/diff** recorder — feeds `CognitionGraphExporter`,
  `CognitionGraphDiffBuilder`, `event_mapper.py`, narrative diffing). It has its own,
  much narrower `source_goal_score` (recorder.py lines 232–256) copied straight from
  `entity.strategic.projects[current_project_id].score` — single value, no runner-up concept,
  and it was never in scope for the 2026-06-27 fix (that fix targeted `decision_trace.jsonl` +
  `EntityInspectionSnapshot`, not the graph-snapshot file).
- The actual fix landed in `decision_trace_writer.py` and `entity_inspector.py` — neither of
  which the audit re-check grepped.

This is a **false negative in the audit doc**, not a real regression. `docs/plans/audit_fix_plan.md`
P1-H should be corrected to RESOLVED with a reference to `TCK-20260627-P1H-GOAL-RUNNERUP` and the
correct file list, so future re-checks don't repeat the same miss.

## Finding 3 — `execute_brain()` is not where any of this scoring happens (ticket's own premise is imprecise)

Both this ticket and the original D15/P1-H finding say candidate scores are "computed transiently
inside `execute_brain()`." Current source has two `execute_brain()` implementations:

- `src/engine/domain/cognition.py::CognitionDomain.execute_brain()` — RPG **tactical** cognition
  (emotional appraisal + tactical intent only). Its own class docstring states: *"Strategic
  project and goal choice occurs exclusively inside the pipeline-level
  `StrategicIntelligenceSystem.fused_strategic_pass()`."* It does not score multiple named goals
  against each other.
- `src/engine/domain_logic.py::SimulationDomainLogic.execute_brain()` — a one-line delegation
  wrapper to the above.

Neither computes the "goal X vs goal Y" candidate scores this ticket is about. The actual
candidate-scoring system is `AdventureDecisionService.decide()` (`src/domains/adventure/service.py`),
called from `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py:104`), which returns
`result.trace["scored_candidates"]` — the list `DecisionTraceWriter.write_trace()` consumes. This
appears to be a naming/architecture drift between the original D15 audit (written against an
earlier code shape) and the current split-out `src/domains/adventure/` module. Not a blocker —
just worth recording so the next audit refresh doesn't cite `execute_brain()` again.

There is a second, narrower "candidate vs current" comparison at the **strategic project**
level: `src/systems/strategic_systems/intelligence.py:925`
(`if candidate_project.score > effective_current_score`) — this evaluates one interrupt candidate
against the currently active project (detour/danger interruption logic), not an N-way tournament
across multiple named goals. It has no "runner-up" concept because there is normally only one
challenger evaluated per tick. This is out of scope per the ticket's own "Out of Scope" section
(no change to scoring/selection logic) and was not touched by the 2026-06-27 fix; it is a
legitimately different mechanism from the RouteFamily scoring this ticket's acceptance criteria
describe (`EntityInspectionSnapshot.goal_scores`, `decision_trace.jsonl`).

## Finding 4 — Candidate count / "top-3" cutoff sanity check

`src/domains/adventure/schema.py::RouteFamily` enumerates 16 possible route families. 
`src/domains/adventure/generator.py::AdventureRouteGenerator.generate()` conditionally appends a
subset depending on visible opportunities/entity state — realistically anywhere from 1 (fallback
`DEFER_WITH_REASON` only) up to double digits when several opportunity kinds are visible
simultaneously. The existing `routes` field in `decision_trace.jsonl` already caps at **top-5**
(documented in `docs/observability/decision_trace_contract.md`, enforced at
`decision_trace_writer.py:109`, `sorted_routes[:5]`). The `goal_scores`/`runner_up_scores` cap at
**top-3** is a narrower, purpose-specific summary (winner + first two runner-ups) nested inside
that same top-5 payload — consistent with, not arbitrary relative to, the pre-existing top-5
cap. It is not an independent design decision; it inherits the existing bound.

## Finding 5 — Memory-boundedness mechanism (precedent check)

`docs/guidelines/intentional_divergences.md` §2.16 "O(1) Memory Boundedness (LEG-RPG-039, 040,
110, 149)" — *"Cognitive intake, leads, concerns, and attention are profile-capped to preserve
performance."* — and §2.10 "Cognitive Boundedness (Attention & Detours)" — *"Attention is limited
to N nearest neighbors; detours are capped at depth 3."* Both establish the repo's existing
pattern for this class of problem: **cap the live-memory structure to a small fixed size per
entity, rely on the append-only trace file for full history.**

The existing `DecisionTraceWriter._latest_goal_scores: Dict[int, List[Dict]]` cache follows this
pattern exactly: one entry per entity, each a fixed-length list of ≤3 small dicts, overwritten
(not appended) on every `write_trace()` call — O(1) per entity, bounded by `len(state.entities)`
total, never grows across ticks. The `decision_trace.jsonl` file itself is where the ticks-over-time
history lives (append-only, one line per entity per tick) — exactly separating "cheap bounded
live cache for last-tick inspection" from "full durable history in the trace file," matching the
2.16 divergence's rationale. **No new mechanism is needed — the one added by
TCK-20260627-P1H-GOAL-RUNNERUP already satisfies the "O(1) memory" concern this ticket's Scope
item 3 asks about.**

## Finding 6 — Test coverage of existing single-score behavior

`test_decision_trace_source_goal_score_present` (line ~489) locks in that `source_goal_score`
still equals the winner's score for a single-candidate case, and
`test_decision_trace_runner_up_single_candidate` / `test_decision_trace_runner_up_fewer_than_3`
lock in graceful truncation. `test_adventure_decision_phase_wires_writer` and
`test_decision_trace_writer_does_not_import_engine_cognition` guard the wiring boundary
(`phase.py` calling the writer without importing engine cognition internals). All 24 tests in
`tests/unit/observability/test_decision_trace.py` pass today
(`pytest tests/unit/observability/test_decision_trace.py -q -m "not slow"` → 24 passed).
No existing test asserts the *old* (single-score-only, no runner-up) behavior — i.e. there is
nothing left to regress against; the "old" behavior has already been fully replaced everywhere
this ticket's acceptance criteria target.

## Overall Conclusion

**This ticket's acceptance criteria are already 100% satisfied by prior work
(`TCK-20260627-P1H-GOAL-RUNNERUP`, done 2026-06-27):**

| Acceptance Criterion | Status |
|---|---|
| Top-3 candidate goal scores retained at tick commit, not discarded | ✅ Done — `DecisionTraceWriter.write_trace()` |
| `EntityInspectionSnapshot.goal_scores` includes runner-up data | ✅ Done — populated from writer cache |
| `decision_trace.jsonl` schema extended to carry the new data | ✅ Done — `source_goal_score` + `runner_up_scores` fields, documented in contract |
| Test confirms runner-up scores captured and distinguishable from winner in multi-goal scenario | ✅ Done — `test_decision_trace_runner_up_scores_present` (5 candidates, asserts 2 runner-ups at ranks [2,3], distinct from `source_goal_score`) |
| No change to actual goal-selection behavior | ✅ Confirmed — `phase.py` untouched by the fix; writer only sorts a copy for serialization |

This is a **duplicate-work situation**, not a genuine implementation gap. The root cause is a
stale/mis-targeted line in `docs/plans/audit_fix_plan.md` (P1-H marked OPEN based on grepping the
wrong files during the 2026-07-03 refresh). The corrective action is a **documentation fix**, not
a feature re-implementation:

1. Update `docs/plans/audit_fix_plan.md` P1-H to **RESOLVED**, citing
   `TCK-20260627-P1H-GOAL-RUNNERUP`, and correct the `Files:` line to the actual implementation
   files (`decision_trace_writer.py`, `entity_inspector.py`) so future greps don't repeat the miss.
2. Update the "Suggested Fix Order" section (lines 617–646) which currently lists P1-H as
   "still open, no ticket exists yet" — this ticket (`TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE`) is the
   ticket that now exists; it should close as "resolved via prior work, doc corrected" rather than
   implement new code.
3. No source code change is required. No parity ledger entry needs updating (INFRA-211 was
   already updated by the 2026-06-27 ticket).

## Open Questions Requiring Human Decision

None that block closing this ticket. One judgment call made autonomously (does not need human
input, but is stated for traceability): treating this as a "correct the tracking doc and close as
duplicate" ticket rather than silently closing it with no artifact trail — this preserves the
audit-trail requirement (Hard Rules: "Do not leave changes untested or untraceable") by leaving a
clear record of why no new code was written.

If a human wants to *expand* scope beyond what's written (e.g., add runner-up tracking to the
**separate** strategic-project-level candidate comparison at
`src/systems/strategic_systems/intelligence.py:925`, or to the cognition graph-snapshot recorder's
`source_goal_score` in `recorder.py`), that would be new work requiring its own ticket — it is
explicitly a different subsystem than what this ticket's Scope/Acceptance Criteria describe, and
this ticket's "Out of Scope" section already excludes changes to selection logic.
