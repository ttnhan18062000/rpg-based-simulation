---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
artifact_type: test_plan
tags: [architecture, testing]
---

# Test Plan — TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET

## Coverage-honesty requirement (matches this repo's established convention, e.g.
`test_workflow_meta_conformance.py`'s own docstring): every check the tool claims to compute needs
at least one fixture proving it computes correctly, not just that it runs without error.

## Tests to add (e.g. `tests/tools/test_codebase_health_baseline.py`)
1. **Exclusion correctness**: a fixture repo/mock where `agent-monitoring/*.jsonl`,
   `tickets/working_log.csv`, and `docs/REGISTRY.yaml` have heavy synthetic churn — assert the
   computed churn metric does NOT reflect that noise (the specific bug this whole item exists to
   prevent).
2. **Source/test split correctness**: assert `src/` files count toward "source" and `tests/`
   files count toward "test," not conflated.
3. **`make codebase-health-baseline` runs successfully** against the real repo and produces
   non-zero, plausible values for every metric in the table (a smoke test, not a golden-value
   pin — the whole point is these numbers change over time).
4. **Live re-run sanity check**: confirm the tool's fresh numbers differ meaningfully from D24
   §C's stale, hardcoded numbers (e.g., zero dead-bytecode files now, vs. §C's recorded 601) —
   proves the tool measures live state, doesn't accidentally echo a cached/stale value.

## Acceptance-criteria mapping
| Acceptance criterion | Verified by |
|---|---|
| `make codebase-health-baseline` exists and runs | Test 3 |
| Bookkeeping-file churn is excluded | Test 1 |
| Metrics reflect live state, not a stale snapshot | Test 4 |
