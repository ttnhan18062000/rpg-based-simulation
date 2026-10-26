---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS
date: 2026-10-27
tags: [performance, determinism, benchmarking]
---

# Evidence: F1 proofs and the v3 digest cost (PROVISIONAL: single host, src/ not fully lifted)

## 1. Cross-PYTHONHASHSEED determinism
Seeds 1 and 12345, one process each, 3 worlds (frontier_living_world, urban_political, crowded_frontier) x seed 42 x 300 ticks, audit_mode. The start, tick-100, tick-200 and final `flat-sha256-v3` digests are identical across the two seeds on all 3 worlds; no TypeError (so `_plain` met no unhandled type and no mixed-key sort). 00:32:46 to 00:36:38.

## 2. `paired --neutral` (rpg-planner's amended condition 2, option A; relayed by lead-planner 2026-10-26, rpg's own #593 post pending)
`python -m tools.rpg_measure.paired --neutral --base 3533fde71 --new 564b5bb57 --seeds 42 --ticks 1000 --jobs 1`, 3 worlds x s42 x 1000 ticks, 00:37:14 to 00:54:41. Printed as is: DIFFERENT on all 3 worlds, `NEUTRAL FAIL`, exit 1, verdict STOP. Expected: the digest scheme moves from v2 to flat-sha256-v3. This run is not identical and not neutral at the hash level.
From the cached arms: `final` (per-entity fates; 55, 30 and 38 entities), `start`, `counters`, `adds` and `perception_samples` are identical on all 3 worlds x s42: outcomes identical, only digests differ. A neutrality measure, not behaviour coverage. The cached arms hold only the start and final digests, so "differs" is shown at those two points only; the t100/t200 values of section 1 exist for the new scheme only. The optional v2-form digest from the v3 arm was skipped (it needs tool code). The tool's default cache `/mnt/data` does not exist on this host; the run used `RPG_MEASURE_CACHE`.

## 3. Phase-7 digest cost (PERF-M5-T04 evidence; PROVISIONAL)
Setup, #641's shape: `profile_tick.py --scenario corpus:frontier_extended --replay --contract canonical --profile PROD_LARGE --seed 42 --warmup 3 --ticks 30`; base = `git archive 3533fde71` (flat-sha256-v2), head = 564b5bb57 (v3); fresh process per run, one at a time under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, 2 min gap, arms alternating. Every run went NORMAL -> CONSTRAINED while replay stayed allowed on 30 of 30 ticks at richness FULL, so no work was shed (both arms).
Gate used (a deviation from the perf rule of loadavg1 < 1.5 before each run, under lead-planner's GO): CPU idle >= 70 % and available memory >= 2.5 GB, with loadavg1 logged and not gated.

| run | arm | start (gate: load1 / idle / avail MB) | tick ms | persistence ms | persistence share |
|---|---|---|---|---|---|
| pair1 | v2 | 01:33:29 (0.39 / 97 % / 5867) | 188.3 | 41.8 | 22.2 % |
| pair1 | v3 | 01:35:46 (0.11 / 98 % / 5893) | 186.7 | 44.2 | 23.7 % |
| pair2 | v2 | 01:38:02 (0.12 / 99 % / 5928) | 132.8 | 32.7 | 24.6 % |
| pair2 | v3 | 01:40:16 (0.07 / 99 % / 5942) | 180.9 | 41.8 | 23.1 % |
| pair3 | v2 | 01:42:32 (0.18 / 99 % / 5954) | 189.4 | 43.7 | 23.1 % |
| pair3 | v3 | 01:44:47 (0.14 / 99 % / 5963) | 165.2 | 41.1 | 24.9 % |

Headline: no increase in persistence-phase cost detectable at n=3 matched pairs. Medians: persistence 41.8 vs 41.8 ms per tick (v2 vs v3); share of the tick 23.1 % vs 23.7 %; tick 188.3 vs 180.9 ms. Ranges: v2 persistence 32.7 to 43.7 ms, v3 41.1 to 44.2 ms; v2 tick 132.8 to 189.4 ms. A difference smaller than about the v2 spread (about 10 ms) cannot be resolved here.
py-spy (250 Hz), one run per arm, treated as single runs: `compute_digest` is 13.7 % of tick-thread samples at v2 (175 of 1280; start 01:30:02, gate 0.16 / 97 %) and 7.5 % at v3 (85 of 1133; start 01:32:18, gate 0.04 / 98 %). The direction (v3 lower) is the opposite of what a wider digest predicts and is treated as noise.
This window does not reproduce #641's 27.1 % `compute_digest` share at v2 (here: 23.1 % phase-7 share, 13.7 % `compute_digest`). The cause is not established: this is a different commit (post-H1 and post-step-B) and a different window.

## 4. Exclusions and the script bug (disclosure)
- Pass 1 (01:16 to 01:32) is excluded from the figures above. Its first run (base none_1, 01:16:13) started with load1 4.91 and 73 % idle: excluded, host busy at the start (242.9 ms tick, 55.0 ms persistence); head none_1 is excluded with it so that the medians come from matched alternating pairs. The other pass-1 `--sampler none` runs (base none_2 204.5 / 51.1 ms, none_3 139.9 / 33.1 ms; head 170.7 / 41.2 ms) are not used.
- A bug in my script: `gate()` reused the loop variable `i`, so every head run in pass 1 was written to `head/none_1` and overwrote the last; only the final head run survived, leaving the base runs without matched head partners. They were discarded and pass 2 (6 runs, fixed) was run in the same slot. The two py-spy runs had distinct labels and were not affected.
- perf-planner's own cProfile (about 01:16:39 to 01:17:20) overlapped the first pass-1 window only; no pass-2 or py-spy run overlapped it.
