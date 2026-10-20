---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE
phase: done
date: 2026-10-19
tags: [observability]
---

# TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE

## Title
SimQ reads the run's lossless simulation_events.jsonl offline, never the live stream (D80 C)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Decision 80 (C). The live stream (redis or in-process) is sampled under queue pressure, so scores depend on host speed (v1_disclosure Q3). The lossless file is EventRecorder's simulation_events.jsonl (src/observability/event_recorder.py:103; TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER, #645). This is step 2 after v1, following D80B.

## Scope
- An offline SimQ entry point that takes a run dir and replays its simulation_events.jsonl through the scorers.
- The calibration and compare tools use it.
- The live dashboard stream stays display-only.
- Per-type event counts are an output, because memo row 82's per-repair criterion reads them.

## Out of Scope
- Grades (D77).
- The observer hook (D80B).

## Acceptance Criteria
- The same run dir gives a byte-identical report on two hosts, or under artificial load.
- The run_determinism sidecar is honoured (#649).
- A run without the lossless file is refused.
- The simulation hash is identical to v1.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (must land first)
- TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK, TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE, TCK-20261019-D80D-UNGRADED-SIMQ-DATA-REVIEW-ON-THE-V1-RECORD (order B, C, D, then D73)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (testing)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md rows 77, 80, 82 (82 on rpg-designer-after-v1 ff0a4a9df until it merges)
- docs/plans/systemic_world/v1_disclosure.md (E, Q sections)

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/event_recorder.py
- src/simulation_quality/
- tools/ (calibrate_simq, simq compare)

## Assumptions / Open Questions
- Order and guards per memo row 82 (rpg-designer, user-confirmed 2026-10-19). B, C and D73 may share batch 1 under the PR size rule, each as its own measured step.

## Implementation Notes
- `src/simulation_quality/offline.py`: `require_replayable` (refuses a run dir with no `simulation_events.jsonl`), `iter_envelopes`, `replay_run_dir(run_dir, hub)` (file order; returns `ReplayResult` with event_count, skipped_lines and `event_counts_by_type`, keyed by the type in the file before SimQ's own vocabulary translation), `build_hub`, `score_run_dir(run_dir, weights, out_dir, require_host_independent=False)` (refuses when `QUALITY_SCORING_DISABLED=1`; optional refusal of a run whose manifest does not record `signals_zeroed`).
- Byte-identical report: `QualityReport.generated_at` was the wall clock; the offline report carries the fixed marker `offline-replay` (`QualityReportBuilder.build` and `QualityHub.get_quality_report` take an optional `generated_at`; the live report is unchanged). Reports measured before this change differ from offline ones in that one field only.
- The old calibration replay dropped `related_entity_ids` and returned 0 events for a missing file; the new one keeps the ids (no scorer reads them) and refuses a missing file.
- `tools/calibrate_simq.py` and `tools/simq_long_run_observation.py` score through it (the private `_build_hub` / `_replay_jsonl_through_hub` are gone); calibrate writes `event_counts_by_type.json` beside the report and still writes the run_determinism sidecar. New entry point `python -m tools.simq_score_run RUN_DIR --out OUT`. The compare/anchor tools read calibration output, which is now offline-scored. The live feed (in-process and broker) is unchanged and display-only.
- Engine and simulation hash untouched (no engine file changed).

## Test Summary
tests/simulation_quality/test_offline_replay.py (7): refusal without the file, byte-identical report/scores on two replays, per-type counts, unreadable lines counted, offline == live hub on the same events, scoring-off refusal, host-independence refusal. With test_calibrate_simq, test_report, test_evaluate_harness, test_calibrate_world_loading: 71 passed, serial. Real run: a 15000-line frozen prefix of a 3-world measurement run (rpgm_frontier_living_world_48) scored twice by `tools.simq_score_run`: quality_report.json, quality_scores.jsonl and event_counts_by_type.json byte-identical; the empty run dir is refused (exit 2).

## Files Changed
src/simulation_quality/{offline,quality_hub,quality_report}.py, tools/{calibrate_simq,simq_long_run_observation,simq_score_run}.py, tests/simulation_quality/test_offline_replay.py

## Completion Summary
SimQ now scores a run from its lossless event file through one offline module; calibration, the long-run observation and a new run-dir CLI use it. The simulation hash is untouched (no engine change).
