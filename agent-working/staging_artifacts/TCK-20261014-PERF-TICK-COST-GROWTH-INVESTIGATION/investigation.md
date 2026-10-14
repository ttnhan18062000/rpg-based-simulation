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

**Possible overlap (lead-planner):** asset's sample-map render (19 s, 640 MB) ran just before the hold and may have overlapped one or two of the earliest runs (the batch started 23:45:06). The first no-sampler run is the highest of its three (102.6 ms against 94.9 and 87.9), which fits a small overlap and would lower, not raise, the idle 250 Hz ratio; I did not repeat it (ratios at 250 Hz stay within the 0.94 to 1.04 noise band either way). Timestamps are in `reports/perf/tick_cost/overhead/log.tsv`.

## Preliminary synthetic profiles (2026-10-15 00:15-00:19 local; 15 runs, 250 Hz py-spy, 3 warmup + 30 measured ticks, loaded host: 1-min load 2.8 to 6.4, so absolute ms are loaded-host values; the SHARES are the finding)
Raw: `reports/perf/tick_cost/synthetic/<scenario>_<entities>_<contract>/{phases.md,phases.json,profile.folded}`; log with available memory, swap and load before each run: `log.tsv`. The combat_20 pinned run failed (`No sampled stack contained the measured-ticks frame`, to be re-run).
| profile | mean tick ms | mode sequence | top phases (pinned run) |
|---|---|---|---|
| idle_100 pinned / canonical / live | 126 / 125 / 119 | NORMAL / NORMAL / NORMAL, DEGRADED, SURVIVAL | combat_engagement 43 ms 34 %, collection 33 ms 26 %, resolution_overhead 33 ms 26 % |
| mixed_200 (140 entities) pinned / canonical | 233 / 261 | NORMAL / CONSTRAINED | cooperation 72 ms 31 %, combat_engagement 50 ms 21 %, resolution_overhead 38 ms 16 % |
| strategic_100 pinned / canonical / live / audit | 615 / 604 / 639 / 615 | NORMAL / SURVIVAL / NORMAL, SURVIVAL / NORMAL | cooperation 365 ms 59 %, resolution_overhead 94 ms 15 %, combat_engagement 48 ms 8 % |
| movement_100 pinned / canonical | 160 / 156 | NORMAL / NORMAL | combat_engagement 55 ms 35 %, resolution_overhead 52 ms 33 % |
| movement_500 pinned / canonical | 1611 / 1573 | NORMAL / SURVIVAL | combat_engagement 989 ms 61 %, resolution_overhead 291 ms 18 %, collection 220 ms 14 % |
Observations (to be confirmed by the remaining curve points, the corpus worlds and the old-commit profiles):
1. **The governor mode barely changes the work**: pinned, canonical and live means agree within 4 to 12 % for the same scenario, so the growth is not a governor artefact; `mixed_200` canonical (CONSTRAINED) is the one visible mode effect (+12 %).
2. **`combat_engagement` is a per-entity-pair cost, present even for idle entities**: 34 % (43 ms) of an idle_100 tick, 35 % (55 ms) at movement_100, and 61 % (989 ms) at movement_500: 55 ms to 989 ms for 5x the entities is a factor 18, a scaling exponent of about 1.8 (nearly quadratic). Its leaf frames are `is_hostile_compat` (`faction.py:206/207/226`) and `project_relation` (`relation.py:75/76/190`): about 43 % of all samples in the movement_500 profile are self-time in those two functions, which is the held ticket `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` confirmed by call-site evidence, now also at 100 to 500 entities.
3. **`cooperation` dominates strategic_100 (59 to 65 %, 365 to 417 ms)**; leaf frames include `cooperation/providers.py:53 get_candidates` (4.3 %) and `identity_resolver.resolve` (4.3 % self, 6.3 % as the first domain frame); the already-closed `find_pending_incoming_offer` item (#394) is no longer the cost, something else in cooperation is.
4. **`resolution_overhead` is 15 to 33 % of every tick** even at idle; that phase is the sum of what `refine` does after the domain phases (DEV-017 corrected how it is counted) and needs its own attribution (not done yet).
5. **audit mode does not cost more than pinned here** (615 vs 615 ms): the start/end fingerprint is not visible in the strategic_100 audit profile at 20 to 30 ticks; to be checked in the folded stacks, not concluded.
6. Scaling check against the held ticket: movement_100 160 ms, movement_500 1611 ms gives an exponent of about 1.44 for the whole tick; 5000 entities would then be about 44 s per tick, against the 11.9 to 16.5 s that `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` measured in August with the then-current builder on a different box. A power-law extrapolation over one decade is weak evidence; the 1000 and 2000 points decide it and I will send the extrapolated values for 5000 to perf-planner and lead-planner before any 5000 run.
