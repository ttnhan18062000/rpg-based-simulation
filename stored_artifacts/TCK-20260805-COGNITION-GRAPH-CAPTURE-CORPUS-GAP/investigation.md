---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP
artifact_type: investigation
tags: [cognition, observability, simulation-quality]
---

# investigation.md — TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP

## Current Behavior (file:line refs)

`CognitionCapturePolicy.should_capture()` (`src/observability/cognition/recorder.py:31-52`, before
this ticket's fix): mode branching handled OFF, LIGHT/LONG_RUN (anomaly-only), and DEBUG/
CERTIFICATION (state-change capture) explicitly — NORMAL/FULL/RESEARCH fell through to `return
False` for non-anomaly reasons, despite `ObservabilityConfig`'s flag table (`src/observability/
config.py`) marking them progressively richer than LIGHT (`OBS_BEHAVIOR_NORMALIZATION`,
`OBS_BEHAVIOR_SCORECARDS`, etc. all `True` by FULL). Confirmed via direct source read and a live
LIGHT-mode run producing zero `cognition_graph_snapshots.jsonl` output.

`docs/audits/D15_entity_decision_inspection.md`'s Gap 6 carried a "RESOLVED" annotation
(`TCK-20260619-E22-DECISION-EXPLAIN`) that conflated two separate artifacts: E22 genuinely added
LIGHT-mode capture for `decision_trace.jsonl` (`DecisionTraceWriter`, verified live), but never
touched `cognition_graph_snapshots.jsonl`/diffs (`ObservabilityCognitionRecorder`, a separate
recorder) — that half of the gap remained open, incorrectly marked resolved.

## Fix Applied

Extended `should_capture()`'s mode tuple to include NORMAL/FULL/RESEARCH alongside DEBUG/
CERTIFICATION — the simplest, most consistent resolution: these modes now behave identically to
DEBUG/CERTIFICATION for cognition-graph capture (all/selected entities on state change), matching
what their `ObservabilityConfig` flags already implied. New parametrized regression test added
(`tests/unit/observability/cognition/test_cognition_capture_policy.py::
test_normal_full_research_modes_capture_state_changes`). No existing test asserted the old
(incorrect) behavior — confirmed by reading the full existing test file before making the change.

## Corpus-Wide Cost Investigation (the ticket's central open question)

Measured real cost at 2 real tiers (not extrapolated from one point, per this ticket's own
Assumptions section):

| Sample | Ticks | `cognition_graph_snapshots.jsonl` | `cognition_graph_diffs.jsonl` | Total run dir |
|---|---|---|---|---|
| `hero_guild_routing` seed42 (unit/end-to-end tier, ~30 entities) | 150 | 3.4 MB | 2.5 MB | ~5.9 MB combined |
| `sandbox_world` seed42 (stress tier) | 2000 | 84 MB | 24 MB | **143 MB** |

Both measured in DEBUG mode (equivalent capture behavior to the now-fixed NORMAL/FULL/RESEARCH
modes) via `SIM_OBS_MODE=DEBUG tools/calibrate_simq.py`. The 2000-tick sample alone produced 108 MB
of cognition-graph data for a single scenario. SimQ's corpus has 76 scenarios spanning 200t/500t/
1000t/2000t tiers (`docs/simulation_quality/corpus_tier_taxonomy.md`); even a conservative
extrapolation (most scenarios are shorter than 2000t, but several 1000t/2000t stress/regression
scenarios exist) puts corpus-wide cognition-graph capture at **multiple gigabytes per full
`make simq-full-audit-full` run**, plus the added I/O overhead of writing that volume, which would
materially slow calibration runtime beyond its current ~15-20 minutes.

**Recommendation: do NOT change SimQ's calibration harness's observability mode.** Leave
`tools/calibrate_simq.py` at its current default (LIGHT, unspecified) — cost is prohibitive at
corpus scale for a signal no SimQ pillar currently consumes (per `TCK-20260805-BEHAVIOR-SCORECARD-
REDUNDANCY-INVESTIGATION`'s sibling scope, decision_trace.jsonl already covers much of the same
ground more cheaply, at LIGHT-mode cost, for entity-diversity purposes). This is a deliberate,
evidenced decision, not a silent drop of the ticket's own aspiration — matches Scope's option
"(c)" only in the negative: no cheaper SimQ-specific capture policy is proposed either, since no
concrete downstream consumer of cognition-graph data in SimQ exists yet to justify building one.

## Docs Requiring Update
- `docs/audits/D15_entity_decision_inspection.md`: Gap 6's stale "RESOLVED" annotation and the
  capture-policy table.
- `docs/simulation_quality/extension_points.md`: axis 3's 2026-08-05 addendum cites this ticket
  and needs its capture-gating description and cost-investigation outcome updated to match what
  this ticket actually did.

## Parity Ledger Overlap

None — this is observability-layer capture policy, not a parity-ledger-tracked subsystem.

## Prior Work

- `TCK-20260619-E22-DECISION-EXPLAIN` — added LIGHT-mode `decision_trace.jsonl` capture (the half
  of Gap 6 actually resolved by that ticket).
- `docs/plans/idea_cognition_graph_analytics_pipeline.md` — separate, unscheduled idea for building
  an analytics layer *on top of* capture once it's reliably available; not affected by this
  ticket's decision not to expand capture corpus-wide.

## Risks and Open Questions

None outstanding — the cost investigation reached a clear, evidenced conclusion (do not adopt
corpus-wide), and the capture-policy bug fix is narrow and test-covered.
