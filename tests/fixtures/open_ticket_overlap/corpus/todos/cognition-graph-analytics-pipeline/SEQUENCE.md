# Implementation Sequence — cognition-graph-analytics-pipeline

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260822-COGNITION-STORAGE-BUDGET  (no deps in this batch)
2. TCK-20260822-COGNITION-VIEWER-TEMPORAL-PLAYBACK  (no deps in this batch — independent, pure client-side)
3. TCK-20260822-COGNITION-PATTERN-CI-GATE  (no hard deps in this batch — absorbs its own minimal, test-local mine_patterns() call rather than waiting on the full pipeline wiring)
4. TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING  (depends on: TCK-20260822-COGNITION-STORAGE-BUDGET)
5. TCK-20260822-RUN-COGNITION-HEALTH-REPORT  (depends on: TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING)
6. TCK-20260822-COGNITION-DECISION-TRACE-JOIN  (depends on: TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING)

## Why This Order Matters

**Written by hand, not auto-generated** — same reason as the `semantic-entity-index`,
`world-grammar-semantic-constraints`, and `agent-monitoring-active-duration` batches earlier
this session: several tickets' own `## Related Tickets` sections forward-reference their
consumers (e.g. `COGNITION-ANALYTICS-PIPELINE-WIRING` lists `RUN-COGNITION-HEALTH-REPORT`,
`COGNITION-DECISION-TRACE-JOIN`, and `COGNITION-PATTERN-CI-GATE` as related, even though those
three depend on it, not the reverse). A naive "any batch ID mentioned is a prerequisite"
heuristic would misread this batch as circular.

The real, unambiguous dependency chain: `COGNITION-STORAGE-BUDGET` must land first since its own
investigation found the pipeline-wiring ticket's raw-capture scope inherits whatever cost policy
it decides. `COGNITION-ANALYTICS-PIPELINE-WIRING` is the foundational concern — `CognitionFeatureExtractor`/
`CognitionPatternMiner` are confirmed never called from any real production post-run hook today
(only from tests), so `RUN-COGNITION-HEALTH-REPORT` and `COGNITION-DECISION-TRACE-JOIN` are both
hard-blocked on it landing first (each ticket's own investigation independently confirmed this).
`COGNITION-VIEWER-TEMPORAL-PLAYBACK` is genuinely independent — it reads
`cognition_graph_snapshots.jsonl`/`diffs.jsonl`, which are already written today by
`ObservabilityCognitionRecorder` regardless of any pipeline-wiring work. `COGNITION-PATTERN-CI-GATE`
is also not hard-blocked: its own investigation found it can absorb a minimal, test-local
`mine_patterns()` call scoped to one test file, rather than waiting on the general-purpose
post-run hook — placement here reflects that self-sufficiency, not a real dependency.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
