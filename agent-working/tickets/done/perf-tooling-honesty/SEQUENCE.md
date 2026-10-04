# Implementation Sequence — perf-tooling-honesty

Owner-approved 2026-10-04. Fixes findings 1, 3 and 5 of `docs/performance/benchmark_identity_schema.md`
§1 in tools only. The RPG-core entry gate and the `src/` freeze both stay in force: no ticket edits
`src/`, runs a benchmark, or commits anything under `reports/`.

## Order

1. TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER  (no deps in this batch)
2. TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS  (depends on: 1, the writer side of the same file)
3. TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS  (no deps in this batch)

## Why This Order Matters

1 makes `baseline.json` well-formed at the source; 2 then validates it at the reader. 1 and 3 both
edit `_TOOLS_PERF_BASENAME_MAP` and the `test-scoper.md` `tools/perf` row, so they land in sequence
to avoid conflicting edits. One PR for the batch, including the planning commit.
