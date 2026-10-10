---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T02B-RECORD
date: 2026-10-10
tags: [performance, benchmarking, schema, determinism]
---

# Investigation: TCK-20261010-PERF-M2-T02B-RECORD

Search order followed: `search_docs`, then `graphify query "BenchHarness run_benchmark consumers"`, then targeted reads.

## Findings

1. **Detected hardware class changes behaviour on small hosts.** `OptimizationProfileResolver.resolve` (`src/config/optimization_profiles.py`)
   returns `LOW_MEMORY` for `hardware_class == CLASS_C`, and `Kernel` resolves it from the profile. With the hard-coded `CLASS_A` removed,
   a `PERF_*` run on a host under 4 cores or 8 GB now gets `LOW_MEMORY`. This host (6 cores, 11 GB) detects `CLASS_B`, so nothing changed
   here, and it was not measured on a `CLASS_C` host. Recorded as `DEV-020`, and as a risk for the CI tripwire (`PERF-M2-T03`).
2. **Two `HardwareClass` enums**: `src.config.profiles.HardwareClass` (what `RuntimeProfile` takes) and
   `src.certification.models.HardwareClass` (what `HardwareClassifier` returns), same values. `detected_hardware_class()` converts by value.
3. **The ticket names `signal_source_for()`; the function is `select_signal_source(profile, audit_mode)`** in `src/engine/signal_source.py`. The
   T07 routing test uses the real name.
4. **Nearest-rank can only lower a percentile** relative to `sorted[int(n*q)]`, so against old-method baselines the per-phase p95 check can
   only get more lenient (see `DEV-020`). Float noise matters: `0.07 * 100 == 7.000000000000001`, so the rank rounds before `ceil`.
5. **The wall-clock inventory is a committed gate** (`tests/tools/test_perf_inventories_committed_in_sync.py`). The five new reads
   (two `perf_counter`, `cpu_count`, `virtual_memory`, `datetime.now`) are measurement-side; the inventory was regenerated with its own tool.
6. **The code-health ratchet is strict for new code** (C901 10, args 5, branches 12, docstrings, cognitive complexity 15, function length 80,
   `run_benchmark` ceiling 151). The first version failed 9 new and 2 worse; the final one has 0 new, 0 worse. The ratchet's baseline was not
   touched; several `bench_harness.py` rows now read lower than their ceilings (`tighten` is the codebase domain's).
7. `graphify query` returned a generic neighbourhood, not consumers of `BenchHarness`; the consumers came from `grep`.

## Not verified

- No `CLASS_C` host run. No timing comparison before and after (the per-tick `perf_counter` pair adds roughly 100 ns per tick).
- `check_perf_regression.py` was not re-run through the old percentile method on committed data.
