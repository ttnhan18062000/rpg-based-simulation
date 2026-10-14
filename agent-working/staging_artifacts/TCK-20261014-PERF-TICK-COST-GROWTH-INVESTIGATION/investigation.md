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
