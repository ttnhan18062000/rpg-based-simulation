---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
date: 2026-10-18
tags: [performance, benchmarking]
---

# Evidence: replay on versus off (PROVISIONAL: single host, src/ not lifted)

Tool: `tools/perf/profile_tick.py --replay` (commit f116fafba). `PROD_LARGE`, seed 42, 3 warmup + 30 measured ticks, `--sampler none` for tick time, one py-spy (250 Hz, nonblocking) run with `--replay` for shares. 33 runs in all (11 per scenario: 5 off, 5 on, 1 py-spy). Fresh process per run, one at a time under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, quiet window enforced (loadavg1 0.85 to 1.5 and 3.9 to 4.2 GB available at every start). Raw data in `reports/perf/fp_replay/<label>/<mode>_<i>/` (git-ignored).

| scenario (contract) | NORMAL? | replay allowed (on runs) | off median ms (middle-3 spread) | on median ms (middle-3 spread) | on/off |
|---|---|---|---|---|---|
| strategic_100 (canonical) | SURVIVAL x30 | **0 of 30 ticks, all 5 runs** (richness OFF) | 522.2 (7.9 %) | 547.3 (2.9 %) | +4.8 %, noise: replay never ran |
| strategic_100 (pinned, supplement; not the signal contract) | NORMAL x30 | 30 of 30, FULL | 512.6 (5.7 %) | 568.9 (12.2 %) | +11.0 % |
| corpus:frontier_extended (canonical) | NORMAL then CONSTRAINED | 30 of 30, FULL | 104.8 (8.1 %) | 129.9 (**16.8 %**, one run 245.8 ms) | +23.9 %; spread above 15 %, read with the shares |

Per-run averages (ms): strategic canonical off 522.2/543.2/497.1/568.4/503.3, on 558.8/543.2/491.7/547.3/576.2; strategic pinned off 534.6/559.6/505.8/496.5/512.6, on 568.9/618.3/551.2/549.1/618.7; frontier_extended off 112.4/104.8/95.1/112.0/103.6, on 130.0/129.9/245.8/111.2/108.3.

py-spy shares of tick-thread samples (replay on):

| scenario | samples | fingerprint (`kernel.py:664` to `state.py:1611`) | digest (`kernel.py:1131` to `checkpoint.py:208`) | replay emit / sink / buffer |
|---|---|---|---|---|
| strategic_100 canonical | 2963 | 0 | 0 (replay disallowed) | 0 |
| strategic_100 pinned | 2741 | 26 (0.95 %) | 251 (9.16 %) | 0 |
| frontier_extended canonical | 724 | 8 (1.10 %) | 196 (27.07 %) | 0 |

Replay manager stats at the end of every replay-on run: `dropped_events_count` 0, `buffer_utilization` 0.000126, `backlog_kb` 16.5 (0.0 on the disallowed runs), `total_bytes_written` 0 (the writer flushes after the measured loop), so no full buffer understates the writer cost. The writer's own thread is not on the measured stack; its cost does not show in tick time here.

Conclusion by the ticket's close rule: fingerprint + digest are 10.1 % and 28.2 % where replay is allowed, above the 2 % line at both scales: **material, but it is the phase-7 digest, not `fingerprint()` (about 1 %); the ticket closes and the digest goes to PERF-M5-T04 as evidence**. No fix proposed.
