---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-COGNITION-PATTERN-CI-GATE
phase: open
date: 2026-08-22
tags: [testing, observability, cognition]
---

# TCK-20260822-COGNITION-PATTERN-CI-GATE

## Title
Add cognition pattern counts as a CI regression gate in the balance regression suite

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The idea doc proposes gating CI on cognition pattern counts (e.g., ProjectChurn==0, StrategicOverload<2) inside the existing balance regression test suite. Investigation found CognitionPatternMiner.mine_patterns() is never invoked in any production/pipeline code path today (only in tests), that test_balance_regression.py's 100-tick urban_political run does not enable observability mode or touch cognition recording/pattern mining at all, that zero cognition_patterns.json files exist anywhere in the repo (the miner has never been run against real simulation data), and that mine_patterns() returns a List[Dict] rather than a pattern_counts dict, so the proposal's exact assert syntax requires new aggregation code that doesn't exist. This ticket wires observability mode and pattern mining into the existing balance regression test, adds the missing List[Dict]-to-pattern_counts aggregation step, and sets thresholds from an actual measured run of the test's own scenario/seed -- not the proposal's unverified guessed values -- following the same evidence-based-baseline precedent test_balance_regression.py already uses elsewhere (e.g. ATTRITION_CAP).

## Scope
- Enable observability mode in test_balance_regression.py's 100-tick urban_political run so cognition_graph_snapshots.jsonl/diffs.jsonl are actually written during that test.
- After the tick loop, call CognitionPatternMiner.mine_patterns(run_dir, spec_data=...) and add the missing aggregation step converting its List[Dict] return into a pattern_counts dict keyed by pattern_type.
- Handle the empty/unmodified-run_dir case: a second mine_patterns() call on an unmodified/empty run_dir returns []/writes cognition_patterns.json with [], and the gate assertion must not KeyError on a missing pattern type.
- Derive ProjectChurn/StrategicOverload (or whichever patterns are gated) thresholds from an actual measured run of the test's own urban_political/seed=42 scenario, not asserted blind before any real corpus data exists.

## Out of Scope
- Building the general-purpose post-run pipeline wiring (the sibling pipeline-wiring ticket) -- this ticket absorbs only the minimal mine_patterns() call and aggregation needed inside this one test file, not the broader Kernel.shutdown()/AnalysisPipeline hook, Parquet conversion, or DuckDB querying.
- viz_strategy.html playback, the HTML report, and the DuckDB/decision_trace join (separate tickets in this batch).
- Calibrating thresholds for any scenario other than test_balance_regression.py's own urban_political/seed=42 run.

## Acceptance Criteria
- [ ] test_balance_regression.py's 100-tick urban_political run enables observability mode so cognition_graph_snapshots.jsonl/diffs.jsonl are actually written.
- [ ] After the tick loop, the test explicitly calls CognitionPatternMiner.mine_patterns(run_dir, spec_data=...) and aggregates the returned List[Dict] into a pattern_counts dict keyed by pattern_type -- this aggregation step is added, since it does not exist as an output shape today.
- [ ] Calling mine_patterns() a second time on an unmodified/empty run_dir returns []/writes cognition_patterns.json with [], and the gate assertion tolerates this without a KeyError on a missing pattern type.
- [ ] Chosen ProjectChurn/StrategicOverload thresholds are set from an actual measured run of the test's own urban_political/seed=42 scenario, not asserted blind at ==0/<2 before any real corpus data exists.

## Related Tickets
- TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/cognition/pattern_miner.py
- src/observability/cognition/feature_extractor.py
- src/engine/kernel.py
- src/observability/config.py
- tests/integration/scenarios/test_balance_regression.py
- src/observability/reporting/run_report.py

## Assumptions / Open Questions
- Depends on this ticket absorbing a minimal, test-local version of the mine_patterns() call itself, since production code never calls it today (staged rollout: this can land independent of the full pipeline-wiring ticket by scoping the call to this one test file only).
- Zero real corpus data currently exists to calibrate thresholds against; landing blind thresholds risks either blocking every build or being vacuously true -- thresholds must come from a real measured run captured as part of this ticket's implementation.
- test_balance_regression.py does not set SIM_OBS_MODE today; default mode may be OFF in a bare test process, requiring explicit setup rather than relying on ambient config.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
