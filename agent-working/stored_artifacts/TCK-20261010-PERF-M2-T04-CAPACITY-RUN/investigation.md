---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T04-CAPACITY-RUN
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Investigation: TCK-20261010-PERF-M2-T04-CAPACITY-RUN

Search order: `search_docs`, then targeted reads (the harness, the long-run harness, the certification test).

## Findings
1. **`BenchHarness` statistics covered only the last 100 ticks** for any run over 100 sampled ticks (`RuntimeStatus.signal_history` is `deque(maxlen=100)`;
   the harness read `get_recent_history(sample_ticks)`), and `compute_tps` was overstated by `sample_ticks / 100`. Found because a real 1000-tick repetition
   recorded 100 compute samples against 1000 wall samples. Fixed in the harness (every tick's signals are collected in the loop). DEV-021. The committed
   `simq_corpus_crowded_frontier.json` shows `compute_tps` 945.43 for 1000 ticks. `runtime_status.py` (a core file) was not touched.
2. On a 20-tick probe, kernel-reported compute and measured wall agree to 1.0 under both the live and canonical contracts, so `latency_ms` from the compute series is a sound basis.
3. At 100 entities the `movement` scenario under the canonical contract is slow on this VM (an average of 582 ms of wall time per tick over 1000 ticks, rising as the run goes); the first
   attempt at the default protocol did not finish in 15 minutes. The verification run uses 20 entities.
4. `PERF_*` profiles under `live` left `NORMAL` within 20 ticks on this VM (`SURVIVAL`, `DEGRADED`); the canonical variants stayed `NORMAL`. That is the reason the tool defaults to the canonical contract.
5. **A first test of mine depended on the working tree being clean** (T05's `candidate()` read the live git state): fixed to be explicit.
6. `docs/engine/performance_contract.md` §3.3 is rpg-owned P1; handled as a PR-body proposal.

## A real run (provisional, this VM, no claim)

`python3 tools/perf/capacity_run.py --entities 20 --repetitions 3` on a clean tree (class_b host, 6 vCPU VM, `movement`, `PERF_1GB_LOCAL_CANONICAL`, 100 warmup, 1000 sampled ticks), 2m10s in total:

| Repetition | avg ms | p50 | p95 | p99 | max | RSS high-water MB |
|---|---|---|---|---|---|---|
| 1 | 40.135 | 43.188 | 71.708 | 95.788 | 160.918 | 141.84 |
| 2 | 38.751 | 42.107 | 69.562 | 90.812 | 129.061 | 141.61 |
| 3 | 38.768 | 43.009 | 66.976 | 83.756 | 132.289 | 141.37 |

Outcome `NOT_APPLICABLE` (coefficient of variation 0.020, limit 0.10; no comparison made; no capacity claim). Every repetition: schema 1.1, `runner.controlled = false`, one `NORMAL` run, 1000 compute and
1000 wall samples in its pointed-to file (this is the DEV-021 fix working on real data; before it the compute series held 100). These numbers describe one VM on one day; they are not a baseline and were not promoted.

## Not verified
- The two `extra_slow` certification tests (`tests/certification/test_cert_long_run_stability.py`, 5000 ticks on 1000 entities) were edited to assert `outcome` but not run.
- No controlled runner exists, so nothing here is a capacity measurement.
