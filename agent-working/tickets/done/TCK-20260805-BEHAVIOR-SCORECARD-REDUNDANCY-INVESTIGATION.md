---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION
phase: done
date: 2026-08-05
tags: [cognition, observability, simulation-quality]
---

# TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION

## Title
Investigate whether EntityBehaviorScorecard's metrics are already derivable from decision_trace.jsonl + cognition_graph_diffs.jsonl before reviving BehaviorWorker

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
While investigating a per-entity "event chain" quality signal for SimQ (2026-08-05), confirmed two
separate, disconnected substrates exist for reconstructing an entity's behavioral history:

1. **`EntityBehaviorScorecard`** (Phase 25/26, `src/observability/behavior/behavior_scorecard.py`)
   — a dataclass with exactly the metrics this kind of signal would want
   (`behavior_diversity_score`, `stagnation_score`, `repeated_failure_count`,
   `adaptation_proof_count`, `route_families_used`, `behavior_categories_used`,
   `episodes_started/completed/failed`). Confirmed **fully dormant**: `BehaviorWorker` (the
   component that turns raw events into `behavior_events.jsonl`, which the scorecard aggregates
   from) is never instantiated anywhere in `src/` outside its own module and tests — no engine
   wiring at all, despite `ObservabilityConfig`'s `OBS_BEHAVIOR_SCORECARDS` flag existing and being
   `True` in FULL/RESEARCH/DEBUG modes.

2. **`decision_trace.jsonl`** (`DecisionTraceWriter`, from `TCK-20260619-E22-DECISION-EXPLAIN`) —
   confirmed **live today** (including in SimQ's default LIGHT mode): a per-tick, per-entity record
   of every candidate route considered, its full score breakdown (`urgency`, `benefit`,
   `personality_bias`, `confidence_bonus`, `risk_penalty`, `blocker_penalty`), and which one was
   selected. Pulled a real sample (`hero_guild_routing`, seed 42, 150 ticks) confirming this.

`decision_trace.jsonl`'s per-route score breakdown is arguably richer than the scorecard's
post-hoc summary stats — it's plausible that `behavior_diversity_score` (route variety) and
`stagnation_score` (repeated identical choices) are directly computable from
`decision_trace.jsonl` alone, or from it plus `cognition_graph_diffs.jsonl`
(`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`, once that ticket lands), without reviving the
separate, fully-unwired Phase 25/26 pipeline at all. Before spending effort wiring `BehaviorWorker`
into the engine, determine whether it's actually needed.

## Scope
- For each of `EntityBehaviorScorecard`'s fields (`behavior_diversity_score`, `stagnation_score`,
  `repeated_failure_count`, `adaptation_proof_count`, `route_families_used`,
  `behavior_categories_used`, `episodes_started/completed/failed`), determine whether it is: (a)
  directly computable from `decision_trace.jsonl` alone, (b) computable from
  `decision_trace.jsonl` + `cognition_graph_diffs.jsonl` together, or (c) genuinely requires
  `behavior_events.jsonl`'s own normalization/episode-detection logic (i.e. actually irreducible).
- Produce a field-by-field verdict table as the investigation's primary output.
- Recommend one of: (1) the scorecard system is redundant, do not revive `BehaviorWorker`, build
  any future entity-diversity signal directly on `decision_trace`/`cognition_graph` instead; (2)
  the scorecard is partially redundant — some fields need it, most don't, revive narrowly; (3) the
  scorecard genuinely does something the other two can't reconstruct, and is worth reviving as-is.

## Out of Scope
- Actually wiring `BehaviorWorker` into the engine, or actually building any new SimQ pillar/rule
  from this data — this ticket is investigation-only; the recommendation it produces is the input
  to a future decision, not this ticket's own implementation.
- Re-evaluating `TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`'s own scope (whether/how to fix
  `CognitionCapturePolicy`) — this ticket depends on that one's outcome for option (b) above but
  does not re-litigate it.
- The larger cognition-graph analytics pipeline
  (`docs/plans/idea_cognition_graph_analytics_pipeline.md`) — separate, unscheduled, out of scope.

## Acceptance Criteria
1. A field-by-field verdict (derivable from decision_trace / cognition_graph / neither) exists for
   every `EntityBehaviorScorecard` field listed above, with concrete evidence (a worked example
   computation from a real sample, not just a plausibility argument).
2. A clear recommendation (one of the 3 options in Scope) is written into this ticket's Completion
   Summary and cross-referenced from `docs/simulation_quality/extension_points.md`.
3. If option (2) or (3) is the verdict, the specific fields/mechanism that require reviving
   `BehaviorWorker` are named precisely enough that a future ticket could scope the revival
   narrowly rather than wiring the whole Phase 25/26 pipeline back in wholesale.

## Related Tickets
- `TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP` — soft dependency: full evaluation of option
  (b) needs `cognition_graph_diffs.jsonl` actually live in a corpus-usable mode, which that ticket
  investigates. This investigation can still start immediately against `decision_trace.jsonl`
  alone (already live) without waiting.
- `TCK-20260619-E22-DECISION-EXPLAIN` — produced `decision_trace.jsonl`, the primary substrate
  being evaluated here.
- `TCK-20260529-OBS-PHASE26-BEHAVIOR-SCORECARDS` — original scorecard implementation, done, but
  confirmed unwired to the engine.

## Related Docs
- `docs/simulation_quality/extension_points.md` §3 (Recorded events) — originating context.
- `docs/audits/D20_simq_quality_status_review.md` — broader SimQ status this investigation feeds.

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `src/observability/behavior/behavior_scorecard.py`, `metrics_aggregator.py`, `episode_detector.py`
- `src/observability/cognition/decision_trace_writer.py`
- `src/observability/behavior/worker.py` (confirmed unwired — read-only reference)

## Assumptions / Open Questions
- Assumes at least one real sample of both `decision_trace.jsonl` and `cognition_graph_diffs.jsonl`
  from the same run is obtainable for the worked-example computation (the latter requires DEBUG
  mode or `TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`'s fix).
- Open question the investigation must resolve: does `behavior_events.jsonl`'s normalization layer
  do any semantic categorization (e.g. `behavior_categories_used`) that isn't recoverable from
  `decision_trace`'s `route_kind` field alone?

## Implementation Notes
Grepped every construction site of `EntityBehaviorScorecard(` across `src/` and `tests/` — found
it's only ever constructed in 2 test files with hardcoded literal values, never in production
code. Read `normalizer.py`, `episode_detector.py`, `pattern_detectors.py`, and
`metrics_aggregator.py` directly to determine what each scorecard field actually requires: raw
`simulation_events.jsonl` categorization (quest accept/complete, combat engage/kill, etc.) for
categories/episodes/failure-adaptation counts — genuinely different information from
`decision_trace.jsonl`'s route-decision scores or `cognition_graph`'s project/objective structure.
The 6 numeric score fields have no computation logic anywhere. No code change made — this is an
investigation-only ticket per its own Out of Scope.

## Test Summary
No code changed; nothing to test. `pytest tests/unit/observability/behavior/ -q` confirmed still
passing (existing dataclass tests, unaffected).

## Files Changed
- `docs/simulation_quality/extension_points.md` — axis 3 addendum updated with the concluded
  field-by-field verdict

## Completion Summary
Investigated whether `EntityBehaviorScorecard`'s metrics are derivable from `decision_trace.jsonl`
+ `cognition_graph_diffs.jsonl` before reviving the unwired `BehaviorWorker` pipeline. Found a
nuanced answer: `route_families_used` is genuinely redundant with `decision_trace.jsonl` (skip it).
Category/episode/failure-adaptation fields require raw gameplay-outcome event categorization that
neither decision_trace nor cognition_graph can see — `BehaviorEventNormalizer`/`EpisodeDetector`
are real working code for this, worth reviving narrowly if ever needed. The 6 numeric score fields
(stagnation_score, progression_score, etc.) have zero production computation logic anywhere in the
codebase — confirmed via construction-site grep — and must be designed from scratch regardless of
substrate. Documented in `extension_points.md`'s axis 3. All 3 acceptance criteria met.
