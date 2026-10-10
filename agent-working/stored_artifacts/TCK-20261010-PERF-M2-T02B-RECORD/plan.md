---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T02B-RECORD
date: 2026-10-10
tags: [performance, benchmarking, schema, determinism]
---

# Plan: TCK-20261010-PERF-M2-T02B-RECORD

The work was pre-planned by perf-planner (the M2 epic's "Delivery plan", steps 1 to 3, #475; owner decisions OD-1 to OD-8
accepted 2026-10-09). This file records the order it was carried out in and the decisions taken where the ticket left a choice.
It was written at close, after the implementation, not before.

## Order

1. `src/perf/benchmark_record.py`: frozen dataclasses for schema 1.0, `to_dict`/`from_dict`, `nearest_rank`, the identity collector,
   `Thresholds`, `compare`.
2. `src/perf/bench_harness.py`: nearest-rank `_calculate_stats`, per-tick wall samples, `last_record`, extraction of `_collate`,
   `_enforce_phase_budgets` and `_build_record` (the code-health ratchet forbids growing `run_benchmark`).
3. `src/perf/profiles.py`: `detected_hardware_class()`; then T07's `canonical_variant` / `PERF_CANONICAL_PROFILES`.
4. Tests under `tests/unit/perf/`; `docs/performance/benchmark_identity_schema.md`; parity `INFRA-430`; `DEV-020`; regenerated
   `docs/performance/wall_clock_inventory.{json,md}`.

## Scope guard

`src/` edits only in the six files of the OD-8 lift (three were touched). `src/perf/regression_gate.py` is not deleted; its
disposition is recorded in the schema doc §6. No gate behaviour change, nothing becomes blocking.

## Decisions where the ticket left a choice

- **The record travels on `BenchHarness.last_record`, not in the result dict.** Adding a key would put it into every committed baseline
  written by `--commit` and into the F1 readers' key sets. The dict is byte-compatible; a test pins its key set.
- **`contract.signal_contract` (`live`/`canonical`) replaces the draft's `contract.determinism`.** The ticket and OD-3 say `live_bounded`
  for the non-canonical contract; the field's values are `live` and `canonical`, and the schema doc says `live_bounded` means `live`.
- **`samples` embeds two series**, `tick_wall_ms` (the schema's name) and `tick_compute_ms` (what `latency_ms` is computed from), so the
  embedded samples reproduce the stored percentiles.
- **Unknown identity values:** the sentinel `"unknown"`; `unknown == unknown` is comparable and a `PASS` reason lists the fields as
  unverified; `unknown` against a known value is a mismatch.
- **`run_benchmark` takes one `record_options` argument** (`RecordOptions`: tier, projection, samples directory) instead of three, and
  the collector takes a `RunSubject`, to stay inside the argument-count rule.
- **A failure to build the record is logged and never fails the benchmark.**
- **T07 variants carry the `_CANONICAL` name suffix** so a baseline that records only the profile name still tells the contracts apart,
  and live in `PERF_CANONICAL_PROFILES` keyed by the original name.
