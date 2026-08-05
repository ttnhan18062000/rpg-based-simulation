---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP
artifact_type: plan
tags: [cognition, observability, simulation-quality]
---

# plan.md — TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP

## Ordered Steps

1. **Fix `CognitionCapturePolicy.should_capture()`'s mode branching** (`src/observability/
   cognition/recorder.py`) — add NORMAL/FULL/RESEARCH to the state-change-capturing mode tuple,
   matching DEBUG/CERTIFICATION's existing behavior. Simplest, most consistent fix: makes actual
   behavior match what `ObservabilityConfig`'s flag table already implies for these modes.
   - Files: `src/observability/cognition/recorder.py`.
2. **Add a regression test** covering NORMAL/FULL/RESEARCH capture behavior, parametrized, mirroring
   the existing `test_debug_mode_captures_all_reasons` test shape.
   - Files: `tests/unit/observability/cognition/test_cognition_capture_policy.py`.
3. **Measure real corpus-wide cost** at 2+ real tiers (not extrapolated from one point) using
   `SIM_OBS_MODE=DEBUG` (equivalent capture to the now-fixed NORMAL/FULL/RESEARCH) against a
   short/unit-tier scenario and a long/stress-tier scenario.
   - No files changed — measurement only, results recorded in investigation.md.
4. **Decide and document the capture-scope recommendation** based on step 3's real numbers — do
   NOT proceed to implement a corpus-wide mode change or a new SimQ-specific capture policy unless
   the measured cost justifies it.
   - No files changed if the decision is "do not adopt" (this plan's expected outcome, pending
     step 3's actual numbers).
5. **Correct `docs/audits/D15_entity_decision_inspection.md`'s Gap 6** — the stale "RESOLVED"
   annotation conflated `TCK-20260619-E22-DECISION-EXPLAIN`'s real `decision_trace.jsonl` fix with
   the still-open `cognition_graph_snapshots.jsonl` half of the same gap; also update the
   capture-policy table to reflect step 1's fix.
   - Files: `docs/audits/D15_entity_decision_inspection.md`.
6. **Update `docs/simulation_quality/extension_points.md`'s axis 9** if step 4's decision changes
   what that axis currently says (it does not — axis 9 already correctly described this as
   DEBUG/CERTIFICATION-only prior to this ticket's fix; the fix extends that, worth a one-line
   note only if the axis text becomes stale).
   - Files: `docs/simulation_quality/extension_points.md` (conditional on step 4's outcome).

## Scope Guards

- Do NOT change SimQ's calibration harness's (`tools/calibrate_simq.py`) observability mode
  without a data-backed justification from step 3.
- Do NOT touch `EntityBehaviorScorecard`/`BehaviorWorker` — explicitly a different ticket's scope
  (`TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION`).
- Do NOT build the larger analytics-pipeline integration
  (`docs/plans/idea_cognition_graph_analytics_pipeline.md`) — separate, unscheduled, out of scope.

## Dependency Map

Step 1 must land before step 2 (test needs the fix to pass). Step 3 is independent of 1/2 (measures
existing DEBUG-mode behavior, which was already correct pre-fix). Step 4 depends on step 3's real
numbers. Steps 5/6 are independent of 1-4's code work, can happen in parallel.

## Acceptance Criteria Map

- AC1 (mode handling fixed or mismatch explicitly resolved) → Step 1.
- AC2 (D15 Gap 6 annotation corrected) → Step 5.
- AC3 (cost measurement justifies the capture-scope decision) → Steps 3-4.
- AC4 (calibration harness still completes, anchors unaffected, if mode changes) → N/A if step 4's
  decision is "do not change harness mode" (this plan's expected outcome).

No unresolved questions requiring human review — the cost investigation (step 3) will produce a
concrete, evidenced answer before step 4 commits to a recommendation.
