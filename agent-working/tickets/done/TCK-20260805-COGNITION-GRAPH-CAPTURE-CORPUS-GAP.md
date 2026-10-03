---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP
phase: done
date: 2026-08-05
tags: [cognition, observability, simulation-quality]
---

# TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP

## Title
Cognition-graph state-change capture is DEBUG/CERTIFICATION-only; investigate enabling it for SimQ's calibration corpus without prohibitive cost

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
While investigating a per-entity "event chain" quality signal for SimQ (diversity/depth/repetition
across an entity's full decision history), confirmed directly against source and a live run that
`ObservabilityCognitionRecorder`'s `CognitionCapturePolicy.should_capture()`
(`src/observability/cognition/recorder.py`) only captures ordinary strategic state changes
(project/objective/blocker changes) in **DEBUG** and **CERTIFICATION** modes. LIGHT (SimQ's actual
default) and LONG_RUN capture anomalies only; **NORMAL, FULL, and RESEARCH modes fall through the
policy's mode branching to `return False`** for state-change reasons too, despite their
`ObservabilityConfig` flag table marking them as progressively richer
(`OBS_BEHAVIOR_SCORECARDS`/`OBS_BEHAVIOR_PATTERNS`/etc. all `True`) — this looks like an
unintentional gap in the policy's mode handling, not a deliberate design choice.

**This directly contradicts a "RESOLVED" claim already in the repo.**
`docs/audits/D15_entity_decision_inspection.md`'s Gap 6 ("Default mode (LIGHT) severely limits
cognition capture") carries the annotation *"RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN
(2026-06-20): ... tick index and LIGHT-mode capture added."* Verified directly (2026-08-05, live
LIGHT-mode calibration run of `hero_guild_routing`): `decision_trace.jsonl` **is** genuinely
populated in LIGHT mode — E22's fix is real for that artifact. But
`cognition_graph_snapshots.jsonl`/`cognition_graph_diffs.jsonl` (a separate artifact, written by
`ObservabilityCognitionRecorder`, not `DecisionTraceWriter`) produced **zero output files** in the
same LIGHT-mode run. E22 fixed the decision-trace half of Gap 6 and the audit's "RESOLVED" tag
conflates that with the cognition-graph half, which remains exactly as originally described.

Confirmed empirically with a DEBUG-mode run of `hero_guild_routing` (seed 42, 150 ticks): capture
does work correctly in DEBUG mode, producing real per-entity project→objective graphs (e.g.
`ProjectKind.HARVESTING (ACTIVE)` → `ObjectiveKind.REACH_RESOURCE`) and diffs — but the volume is
non-trivial: 3.4 MB of snapshots + 2.5 MB of diffs for one 150-tick, ~30-entity unit-tier world.
SimQ's corpus includes stress-tier worlds up to 2000 ticks; naively switching SimQ's calibration
harness to DEBUG mode corpus-wide has not been evaluated for cost.

## Scope
- Fix `CognitionCapturePolicy.should_capture()`'s mode branching so NORMAL/FULL/RESEARCH modes
  behave consistently with what their `ObservabilityConfig` flags imply (either capture
  state-changes like DEBUG/CERTIFICATION, or the policy's mode table is updated to honestly reflect
  what each mode does — a real decision point for the investigation phase, not assumed here).
- Correct `docs/audits/D15_entity_decision_inspection.md`'s Gap 6 "RESOLVED" annotation to
  precisely scope what E22 actually fixed (decision_trace only) vs. what remains open
  (cognition_graph_snapshots/diffs).
- Investigate the real storage/perf cost of enabling richer cognition-graph capture across SimQ's
  full calibration corpus (18 worlds, 4 tiers up to 2000 ticks) and recommend either: (a) a mode
  change for the whole corpus, (b) a scoped opt-in for specific worlds/tiers, or (c) a cheaper
  capture policy tailored to SimQ's actual needs (e.g. periodic snapshot instead of every
  state-change) — pick one, justified by measured cost, not assumed.
- If a change is implemented, verify SimQ's calibration harness (`tools/calibrate_simq.py`,
  `make simq-full-audit-full`) still completes in reasonable time and `data/calibration/` artifact
  size stays sane.

## Out of Scope
- The larger cognition-graph analytics pipeline (Parquet conversion, DuckDB queries,
  `viz_strategy.html` temporal playback, cross-entity comparison views) described in
  `docs/plans/idea_cognition_graph_analytics_pipeline.md` — that's a separate, unscheduled IDEA-
  maturity proposal layered *on top of* capture; this ticket only concerns whether the raw capture
  itself happens, not what's built on top of it once it does.
- `EntityBehaviorScorecard`/`RunBehaviorScorecard` (Phase 25/26, `src/observability/behavior/`) —
  confirmed separately (2026-08-05) to be fully dormant: `BehaviorWorker` is never instantiated
  anywhere in `src/` outside its own module and tests, so `behavior_events.jsonl` is never written
  by any real run. This is a materially different, larger gap (no engine wiring at all, vs. a
  narrow capture-policy branch here) and is not addressed by this ticket.
- Building any new SimQ pillar or scoring rule from this data — this ticket only makes the raw
  per-entity event-chain data actually available; whether/how to turn it into a scored signal is a
  separate future decision.
- `decision_trace.jsonl`'s own capture behavior — already correctly LIGHT-mode-capable per E22;
  not touched here.

## Acceptance Criteria
1. `CognitionCapturePolicy.should_capture()`'s mode handling is either fixed to match its documented
   intent, or the mismatch is explicitly resolved and documented (not left silently inconsistent).
2. `docs/audits/D15_entity_decision_inspection.md`'s Gap 6 annotation accurately reflects that
   `cognition_graph_snapshots.jsonl`/diffs remain state-change-capture-limited (scope corrected to
   whatever the fix in AC1 actually changes).
3. A cost measurement (real file sizes / runtime delta from an actual calibration run, not an
   estimate) justifies whichever capture-scope decision is made in Scope's 3rd bullet.
4. If SimQ's calibration harness's observability mode changes, `make simq-full-audit-full` still
   completes and existing `test_grade_regression.py` anchors are unaffected (this ticket does not
   change scoring, only observability capture).

## Related Tickets
- `TCK-20260619-E22-DECISION-EXPLAIN` — fixed the `decision_trace.jsonl` half of the same D15 Gap
  6; this ticket picks up the remaining `cognition_graph_snapshots`/diffs half.
- `TCK-20260412-STRAT-GRAPH-EXPORT` — original cognition-graph exporter (Milestone 6), still
  correct; this ticket doesn't touch the exporter itself, only the capture policy gating it.
- `TCK-20260523-COGNITION-DIFF-EVENTS` — cognition graph diffing, same subsystem.

## Related Docs
- `docs/audits/D15_entity_decision_inspection.md` — Gap 6, Gap 3 (both reference the same recorder)
- `docs/plans/idea_cognition_graph_analytics_pipeline.md` — related, larger, explicitly out of scope
- `docs/audits/D20_simq_quality_status_review.md` / `docs/simulation_quality/current_state.md` —
  originating context: this investigation started from a SimQ entity-diversity discussion

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `src/observability/cognition/recorder.py` (`CognitionCapturePolicy.should_capture()`)
- `src/observability/config.py` (`ObservabilityConfig`, `ObservabilityMode` flag table)
- `tools/calibrate_simq.py` (SimQ's calibration harness — observability mode currently unspecified,
  defaults to LIGHT)

## Assumptions / Open Questions
- Not yet determined whether the right fix is "make FULL/RESEARCH capture like DEBUG" (aligns with
  their flag table) or "give SimQ's corpus its own lighter capture policy" (avoids inheriting
  DEBUG's full cost) — this is the investigation phase's central open question.
- Cost figures cited above (3.4 MB/2.5 MB for one 150-tick unit-tier world) are from a single
  sample run; investigation must measure across corpus tiers, not extrapolate from one data point.

## Implementation Notes
Extended `CognitionCapturePolicy.should_capture()`'s mode-branching tuple to include NORMAL/FULL/
RESEARCH alongside DEBUG/CERTIFICATION — the simplest fix matching what `ObservabilityConfig`'s
flag table already implied for those modes. Measured real corpus-wide cost at 2 tiers
(hero_guild_routing 150t: 5.9MB; sandbox_world 2000t: 143MB, 108MB of which is cognition-graph
data alone) and concluded the cost is prohibitive for corpus-wide adoption — did NOT change
`tools/calibrate_simq.py`'s observability mode. Corrected `docs/audits/D15_entity_decision_inspection.md`'s
Gap 6, which incorrectly marked this half of the gap "RESOLVED" by conflating it with
`decision_trace.jsonl`'s real, separate fix.

## Test Summary
`pytest tests/unit/observability/cognition/test_cognition_capture_policy.py -v`: 7 passed (4
pre-existing + 3 new parametrized cases for NORMAL/FULL/RESEARCH). `pytest tests/simulation_quality/
test_grade_regression.py -m "not slow" -q`: 64 passed / 1 failed (same pre-existing, unrelated
`urban_political_seed42_200t` failure documented in the two prior tickets this session) — confirms
no impact on SimQ calibration, consistent with the decision not to change its observability mode.

## Files Changed
- `src/observability/cognition/recorder.py` — `should_capture()` mode fix
- `tests/unit/observability/cognition/test_cognition_capture_policy.py` — new parametrized test
- `docs/audits/D15_entity_decision_inspection.md` — Gap 6 annotation and capture-policy table
  corrected

## Completion Summary
Fixed a real gap in `CognitionCapturePolicy.should_capture()`: NORMAL/FULL/RESEARCH modes now
capture cognition-graph state changes like DEBUG/CERTIFICATION do, matching their
`ObservabilityConfig` flag table's documented intent. Measured real corpus-wide storage cost at 2
tiers (5.9MB for a 150-tick scenario, 143MB for a 2000-tick scenario) and concluded it's prohibitive
for SimQ's calibration harness to adopt corpus-wide — deliberately left `tools/calibrate_simq.py`
unchanged. Corrected `docs/audits/D15_entity_decision_inspection.md`'s Gap 6, which had incorrectly
carried a "RESOLVED" annotation conflating `TCK-20260619-E22-DECISION-EXPLAIN`'s real
`decision_trace.jsonl` fix with this still-partially-open gap. All 4 acceptance criteria met.
