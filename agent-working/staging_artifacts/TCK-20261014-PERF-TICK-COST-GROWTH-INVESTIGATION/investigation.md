---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION
date: 2026-10-14
tags: [performance, benchmarking, regression]
---

# Investigation: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION

Facts read before any run (2026-10-14, main 0fba246ed):
1. `Kernel.__init__(profile, state, rng, scheduler, governor, status, replay, executor, flags, ...)` takes a `governor` (`src/engine/kernel.py:58-70`), and `tests/helpers/kernel_pinning.py::PinnedNormalGovernor` returns `NORMAL` for every signal and ignores `force_mode`, so a pinned run needs no `src/` edit. Its docstring says the other wall-clock inputs outside `audit_mode` still move.
2. `_profiling_common.py` builds the child kernel with `flags={"no_replay": True, "no_frame_pacing": True, "audit_mode": False}` and a profile from `PROD_SMALL/PROD_DEFAULT/PROD_LARGE/PROD_STRESS` (`PROFILE_NAMES`); `canonical_variant(profile)` (`src/perf/profiles.py`) builds the canonical variant of any profile.
3. `tools/perf/profile_tick.py` takes `--scenario {idle,movement,resource,combat,strategic,mixed,metropolis}`, `--entities`, `--ticks`, `--warmup`, `--seed`, `--profile`, `--rate`, `--memory`, `--flag`; it has no world option and no contract option. `profile_diff.py` takes two folded files. `profile_memory.py` and `--memory` use memray.
4. py-spy and memray are declared in `pyproject.toml` (the `perf` group, lines 87-90) but are **not installed** in `.venv` (`import py_spy` fails; neither binary on `PATH`).
5. Old commits: `20f773dee` (2026-05-15), `c84352465` and `132bf09ca` all exist in this clone.
6. T08 measurements (evidence.md): `frontier_extended` wall 180 s per run for 1100 ticks, peak RSS 1703 MB, `rss_delta` 1587 MB; so a 33-tick profile run is about 6 s of ticks plus the world build.
7. The movement[5000] ticket measured 5000 entities (`build_movement_state(5000)`, 2026-08-26 builder, `PERF_2GB_LOCAL`); T08's `combat_engagement` 28-43 ms is at 100-140 entities. The scale differs by 35-50x, so the two are different points of one scaling curve until measured otherwise.
Open: whether importing a `tests/` helper into a `tools/` module is acceptable (alternative: a perf-owned copy in `src/perf/`, which duplicates the helper that a guard exists to keep single).

## Overhead of py-spy, measured (2026-10-14, pinned contract, 20 measured + 3 warmup ticks, 1 GB cap, swap off; host load 2.3 to 3.7 while the batch ran, so this is a loaded-host result)
Each variant 3 repetitions, interleaved (no sampler, 250 Hz, 100 Hz); mean tick wall ms over the measured ticks. Raw: `reports/perf/tick_cost/overhead/` (log.tsv has available memory, swap and load before every run).
| scenario | no sampler (3 runs, mean) | 250 Hz | ratio | 100 Hz | ratio |
|---|---|---|---|---|---|
| idle_100 | 102.6 / 94.9 / 87.9 (95.1) | 93.8 / 77.1 / 96.7 (89.2) | 0.94 | 87.8 / 112.3 (100.0, 2 of 3 completed) | 1.05 |
| strategic_100 | 365.3 / 425.0 / 432.8 (407.7) | 407.1 / 444.5 (425.8, 2 of 3 completed) | 1.04 | 456.0 / 407.3 / 981.1 (614.8) | 1.51 (one 981 ms outlier; the two others give 1.06) |
**Reading:** at 250 Hz the sampler costs within the run-to-run noise (0.94 and 1.04; the no-sampler runs alone vary by up to 18 % on the same code); the 100 Hz result for strategic_100 is dominated by one outlier run under load, without it 1.06. **Rate chosen: 250 Hz** (the tool's default), which gives the most samples per tick for the shares I report; absolute ms still come from the unsampled per-phase table, never from a sampled run, and the profile header says so.
**Three runs did not complete, all for tool reasons found here:** `idle_100_100_r1` (100 Hz, 20 idle ticks, "No sampled stack contained the measured-ticks frame": too few samples, so the idle floor profile uses 250 Hz and at least 30 ticks), `strategic_100_250_r2` (a torn byte, 0xff, in py-spy's nonblocking raw output made `read_text(encoding="utf-8")` raise `UnicodeDecodeError`; fixed in `profile_tick.py` with `read_folded_text`, which replaces a bad byte; unit test added). Both are counted as missing repetitions above, not retried silently.
