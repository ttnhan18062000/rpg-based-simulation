---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION
phase: done
date: 2026-09-11
tags: [observability, architecture]
---

# TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION

## Title
10 of `ObservabilityConfig`'s 17 feature-flag convenience methods are unused, and their own
underlying flags are never read anywhere else either — determine whether the subsystems they
name run ungated, never run, or have a real missing-gate bug

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (`docs/audits/
unreachable_code_inventory.md`, Cluster C2). `src/observability/config.py`'s `ObservabilityConfig`
declares 17 `is_X_enabled()`-shaped classmethods, each a thin wrapper
(`return cls.get_flag("OBS_X")`) around a named observability feature flag. 10 have zero real call
sites anywhere: `is_event_recorder_enabled`, `is_entity_timeline_enabled`,
`is_behavior_timeline_enabled`, `is_behavior_episodes_enabled`, `is_behavior_metrics_enabled`,
`is_behavior_patterns_enabled`, `is_behavior_scorecards_enabled`, `is_cohort_analysis_enabled`,
`is_run_comparison_enabled`, `is_insight_generation_enabled`, `is_warehouse_ingest_enabled`. 3
genuinely-similar siblings (`is_live_stream_enabled`, `is_behavior_normalization_enabled`,
`is_dashboard_export_enabled`) ARE real, live-called methods — ruling out "this whole cluster is a
naming artifact of the audit tool."

**Checked further, not assumed**: the underlying flag strings themselves (`OBS_EVENT_RECORDER`,
`OBS_ENTITY_TIMELINE`, `OBS_COHORT_ANALYSIS`, `OBS_WAREHOUSE_INGEST`, spot-checked) are not read
directly anywhere else in the codebase either. This rules out "the convenience method is unused but
some other code checks the same flag directly instead" — the underlying gate itself is never
consulted by anything, not just this one method.

This leaves three real possibilities, genuinely undetermined:
1. The observability subsystems these flags name (entity timeline, cohort analysis, warehouse
   ingest, behavior episodes/metrics/patterns/scorecards, run comparison, insight generation, the
   event recorder itself) run **unconditionally** — the flag is dead scaffolding for a future
   kill-switch that was never wired to the actual conditional, but the subsystem itself works fine
   without it.
2. The subsystems **never run at all** for some other reason (a separate wiring gap), making the
   missing gate moot either way.
3. There is a **real, missing gate check** — the subsystem should be conditionally running based on
   this flag and currently always runs (or never runs) regardless of what the flag is set to,
   which is a real correctness/resource-control bug, not dead code.

## Scope
- For each of the 10 unused flag names, identify the real subsystem it's meant to gate (the naming
  is suggestive — `OBS_ENTITY_TIMELINE` almost certainly gates `src/observability/live/` or
  similar entity-timeline machinery, `OBS_WAREHOUSE_INGEST` the warehouse ingestion pipeline, etc.
  — confirm each mapping directly, don't assume from the name alone).
- For each subsystem: determine whether it currently runs unconditionally, never runs, or should
  be conditionally gated and isn't. This determines which of the 3 possibilities above applies —
  do this per-flag, not as a single blanket answer, since different flags may land in different
  buckets.
- Decide the disposition per flag once its bucket is known: wire the gate check in (if the
  subsystem should genuinely be conditional and currently isn't), delete the unused convenience
  method (if the subsystem doesn't need gating at all and the method is pure vestigial scaffolding),
  or document (if there's a real reason the gate is deliberately not wired yet, e.g. the feature
  itself is still incomplete).

## Out of Scope
- The 3 confirmed-live sibling methods (`is_live_stream_enabled`, `is_behavior_normalization_enabled`,
  `is_dashboard_export_enabled`) — already working, not re-litigated here.
- Any other cluster from the same audit — each has, or will have, its own ticket.
- Full implementation of whatever wiring decision is made per flag — this ticket is the
  determination and, for clear-cut cases, the fix; a flag whose fix isn't trivial should route the
  decision through peer review before implementing, matching this whole follow-up arc's own
  precedent for design-level findings.

## Acceptance Criteria
- [x] Each of the 10 unused flags is mapped to its real intended subsystem, confirmed directly
      (not assumed from the flag's own name). Done — 3 map to real, live subsystems
      (`EventRecorder`, `EntityTimelineStore`, the warehouse CLI); 7 map to a single shared
      subsystem (`src/observability/behavior/`'s own analysis pipeline), not 7 independent ones.
- [x] Each flag's real bucket is determined with evidence, not guessed. 3 are "subsystem live,
      gated a different way" (the coarse `ObservabilityMode` directly, not this flag layer,
      confirmed via `kernel.py`/`cognition/recorder.py` reads). 8 are one shared "subsystem built
      and tested but never started in production" finding, not independently-bucketed.
- [x] A disposition (wire / delete / document) is recorded per flag, with rationale. 3 deleted
      (vestigial, confirmed). 8 NOT resolved here — their real disposition (wire the pipeline vs.
      formally defer it) is a genuine product decision, routed to
      `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT` rather than decided
      unilaterally, per this ticket's own precedent for design-level findings.
- [x] Any flag determined to be a real missing-gate bug has its fix-approach decision routed
      through peer review before implementation. Routed via the new ticket above, not implemented
      here.

## Related Tickets
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (origin — Cluster C2)
- `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT` (new, filed from this ticket's
  own investigation — the real 8-flag/7-endpoint disposition, a genuine product decision not
  resolved here)
- `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` (sibling finding,
  same shape — second instance in this batch, cross-referenced)
- `TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP` (already documents the coarse-vs-fine gating
  mismatch for its own consumer, corroborating this ticket's own structural finding)

## Related Docs
- `docs/audits/unreachable_code_inventory.md` (Cluster C2's own writeup)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION/`
  (`investigation.md`, `plan.md`, `test_plan.md`)

## Related Code Areas
- `src/observability/config.py` (`ObservabilityConfig`, all 17 `is_X_enabled` methods and their
  underlying `OBS_*` flag strings)
- `src/engine/kernel.py`, `src/observability/cognition/recorder.py` (the real coarse-mode gating
  pattern)
- `src/observability/behavior/` (the never-started pipeline, routed to the new ticket)

## Assumptions / Open Questions
- ~~Which of the 3 possible buckets each flag falls into is the central, deliberately-unresolved
  question this ticket exists to answer — not assumed uniformly across all 10.~~ Resolved: 3 land
  in "subsystem live, gated differently"; 8 land in one shared "subsystem never started" finding,
  not 8 independent buckets. The real disposition question for those 8 (wire vs. defer) is now its
  own ticket's open question, not this one's.

## Implementation Notes
Re-verified the ticket's own premise before trusting it — its claim of "3 confirmed-live sibling
flags" didn't hold literally on first narrow check; a broader re-check (including `tests/`) nearly
produced a false over-correction (test-file assertions on the flag's own value, mistaken for real
consumer usage) before re-narrowing to `src/`-only and confirming properly. Recorded as a
generalizable lesson alongside `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION`'s own `trace_governor.py` self-correction from earlier in this same batch — grep
scope can produce a confidently wrong answer in both directions, not just the narrow one.

Found the real structural reason the flags are unused while checking flag #1: real observability
consumers (`EventRecorder`, `EntityTimelineStore` in `kernel.py`; `cognition/recorder.py`'s own
`should_capture()`, which already documents the same mismatch via an existing ticket,
`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`) check the coarse `ObservabilityConfig.
get_mode()` directly, not the fine-grained `is_X_enabled()` convenience layer. Confirmed via a full
sweep of all 17 methods (not just the 10+3 named): only 2 are called by name anywhere in real code.
This generalizes past the 10 named flags — recorded, not chased further, since it's outside this
ticket's own AC.

3 of the 10 (`is_event_recorder_enabled`, `is_entity_timeline_enabled`, `is_warehouse_ingest_enabled`)
confirmed as genuinely vestigial — real, live subsystems, gated the coarse way instead — deleted.

The other 7 map to a single shared subsystem, not 7 independent findings: `src/observability/
behavior/`'s own analysis pipeline (`BehaviorWorker`, `EpisodeDetector`, `CohortAnalyzer`,
`RunBehaviorComparison`, `BehaviorMetricsAggregator`) — real, built, individually tested (a
dedicated test file per class), but `BehaviorWorker(` has zero real construction sites anywhere,
despite `kernel.py:1221`'s own comment implying it's wired in. Confirmed false — the fourth
instance this batch of a confident comment describing behavior that doesn't happen. Found this
backs 7 live `@router.get` endpoints in `src/api/routes/behavior.py`, all reading from a warehouse
store nothing populates — every real request returns empty/404, always. The second instance of this
exact shape in this batch (after `TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-
PRODUCTION`'s own 2 endpoints), suggesting the pattern may be systematic in this codebase rather
than isolated — cross-referenced both tickets in both directions and recorded the observation
explicitly, per peer review's instruction, so whoever picks up either checks for a third instance
before assuming these are the only two.

Filed `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT` for the real disposition
(wire the pipeline into the real lifecycle, or formally defer it and stop exposing endpoints that
cannot answer) — a genuine product decision, not resolved here, matching this whole batch's own
standing discipline for design-level findings.

## Test Summary
`tests/unit/config/` + `tests/unit/observability/` — 1078 passed, 1 skipped, no regression after
deleting the 3 confirmed-vestigial methods. Grep confirms zero remaining references to any of the
3 deleted methods anywhere in `src/`/`tests/`. `tests/integrity/test_no_duplicate_content_blocks.py`
and `validate_frontmatter.py --content-type ticket` passed on this ticket and the two ticket files
touched/filed.

## Files Changed
- `src/observability/config.py` — deleted `is_event_recorder_enabled()`/
  `is_entity_timeline_enabled()`/`is_warehouse_ingest_enabled()`.
- `tickets/todos/TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT.md` — new.
- `tickets/todos/TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION.md` —
  amended with the cross-reference to the new ticket.
- `stored_artifacts/TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION/{investigation.md,plan.md,test_plan.md}`
  — full evidence trail.
- `tickets/done/TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION.md` —
  this file, closed.

## Completion Summary
Determined all 10 named flags: 3 confirmed vestigial (real subsystems, gated the coarse
`ObservabilityMode` way instead of this fine-grained layer) and deleted; the other 7 turned out to
be one shared finding, not 7 independent buckets — a fully-built, individually-tested behavior-
analytics pipeline that was never started in production, backing 7 permanently-empty API endpoints.
Routed that real disposition (wire vs. defer) to its own ticket rather than deciding it here, per
standing discipline for genuine product decisions.

Along the way: caught and corrected a near-over-correction on the ticket's own premise (grep-scope
risk in the broad direction, the mirror image of this same batch's `trace_governor.py` narrow-grep
miss); confirmed the coarse-vs-fine gating mismatch generalizes past the 10 named flags (only 2 of
17 `is_X_enabled()` methods called anywhere); and identified this as the second instance in this
batch of a live public API surface backed by a store nothing populates, cross-referenced with the
campaigns/chronicle sibling finding in both directions, with an explicit note that a third instance
should be checked for before assuming these are the only two.
