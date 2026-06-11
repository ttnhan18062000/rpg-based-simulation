---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 8 — Documentation and Checklist Reconciliation

## Goal

Make the checklist honest.

Right now, many PERF items are marked `[x]`, but some are not proven strongly enough under the stricter standard. The checklist itself says partial implementation does not count and bypassed/contradicted behavior must remain unchecked. 

## Tasks

| Task                                        | Narrow implementation logic                                                             |
| ------------------------------------------- | --------------------------------------------------------------------------------------- |
| M8.1 Reclassify profiler-related PERF items | Downgrade anything not proven by new tests.                                             |
| M8.2 Reclassify DirtySet PERF items         | Keep `[x]` only after Milestone 2 and 3 pass.                                           |
| M8.3 Add proof links                        | Every PERF item must reference exact test file and proof type.                          |
| M8.4 Add “known intentional limits” section | Example: benchmark numbers are machine-sensitive; CI uses smoke thresholds only.        |
| M8.5 Add developer guide                    | Explain benchmark flags, DirtySet lifecycle, full-scan reference mode, baseline policy. |

## Acceptance checklist

```text
[ ] Checklist status matches actual proof.
[ ] No PERF item is marked complete without a passing test.
[ ] DirtySet laws mention lifecycle/recompute requirement.
[ ] Benchmark laws mention no_replay and no_frame_pacing.
[ ] Developer docs explain how to add future optimizations safely.
```

## Exit condition

The checklist stops being decorative and becomes an enforceable engineering ledger.

---

# Suggested Milestone Order

```text
M0 Baseline freeze
M1 Profiler truth
M2 DirtySet lifecycle correctness
M3 O(Dirty) vs O(N) parity
M4 Local vs concurrent parity
M5 Benchmark matrix
M6 Regression gate
M7 Real optimization cleanup
M8 Documentation/checklist reconciliation
```

Do not reorder M1 and M2 below M7. That would be backwards.

---

# Overall Acceptance Criteria

The implementation is complete only when all of these are true:

```text
[ ] Profiler reports compute-only metrics separately from wall-clock metrics.
[ ] Benchmark mode disables replay/hash overhead unless explicitly requested.
[ ] Benchmark mode disables frame pacing unless explicitly requested.
[ ] Phase timings include all authoritative tick phases.
[ ] DirtySet is refreshed/merged after every phase that mutates StateUpdate.
[ ] Every O(Dirty) consumer has an O(N) reference parity test.
[ ] Local and concurrent execution produce identical canonical final state.
[ ] Worker chunk boundary cases are deterministic.
[ ] Perf matrix covers local/concurrent and multiple memory profiles.
[ ] CI regression gate uses committed baselines.
[ ] Missing baseline fails in CI.
[ ] Checklist PERF items are updated to reflect actual proof.
```
