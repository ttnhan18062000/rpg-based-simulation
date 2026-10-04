# Implementation Sequence — perf-m1-partial-lift

M1 work released by the owner's partial lift of the RPG-core entry gate (2026-10-04,
`performance_optimization_roadmap.md`, "Gate definition and partial lift"). Allowed `src/` edits:
`src/engine/worker_manager.py`, `src/engine/checkpoint.py`, `src/perf/long_run_harness.py`,
`src/core/protocol_validator.py`. Gated, no edit: `src/core/state.py`, `src/engine/apply.py`,
`src/engine/pipeline.py`, `src/engine/kernel.py`, `src/engine/governor.py`. Any ticket that finds
it needs a gated file stops and reports; it does not edit the file.

## Order

1. TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN  (no deps in this batch; hotfix)
2. TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS  (no deps in this batch)
3. TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE  (depends on: TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN, which adds the inventory --check test this ticket must keep green)
4. TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION  (depends on: TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE, for the named proof digest)

## Not in this batch

- PERF-M1-T01 (zero-capacity signal semantics): needs `governor.py`, held until the root cause of
  `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` is known.
- PERF-M1-T03b (kernel and certification-harness half of PERF-D5): needs `kernel.py`, gated.
- PERF-M1-T05 (invalidation ledger): after T01-T04.

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
