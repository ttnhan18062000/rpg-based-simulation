---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS
date: 2026-10-14
tags: [performance, benchmarking, regression]
---

# Evidence: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS

Copied from `reports/perf/t08/` and `reports/perf/t08_retry/` (git-ignored). Host `ubuntu`, Intel i5-11400H, 6 vCPU, loaded (swap 5.7 to 6.8 GB used); main 06aa3a20c (the two mixed_200 records: main 4b5d1bdfb, engine commit a002cc1dd). Each row: 3 fresh-process runs; `avg ms` per run, `load` = 1-min loadavg at the start of each run, `swap MB` at the start, `peak RSS` of the worker process, `wall` per run.

| window | record | spread % | NOISY | off-NORMAL | avg ms (run 1/2/3) | load (1/2/3) | swap MB | peak RSS MB | wall s |
|---|---|---|---|---|---|---|---|---|---|
| first | combat_10_concurrent | 137.4 | True | - | 46.6 / 110.7 / 53.5 | 5.29 / 5.35 / 5.16 | 6811 | 74.5 | 3.67 / 4.21 / 2.87 |
| first | combat_10_local | 43.3 | True | - | 47.3 / 67.8 / 64.5 | 2.41 / 2.41 / 2.22 | 6820 | 64.5 | 3.21 / 2.5 / 3.18 |
| first | idle_100_concurrent | 12.2 | False | - | 62.2 / 69.8 / 64.7 | 1.61 / 1.64 / 1.3 | 6820 | 62.8 | 3.05 / 16.96 / 3.4 |
| first | idle_100_local | 35.3 | True | - | 62.4 / 61.0 / 46.1 | 2.39 / 2.44 / 2.48 | 6823 | 64.2 | 5.23 / 4.86 / 3.97 |
| first | mixed_200_concurrent | 13.8 | False | CONSTRAINED | 166.2 / 189.1 / 182.3 | 1.2 / 1.18 / 1.15 | 6523 | 79.0 | 5.41 / 6.86 / 6.49 |
| first | mixed_200_local | 4.3 | False | CONSTRAINED | 171.2 / 167.5 / 164.1 | 1.18 / 1.16 / 1.23 | 6523 | 78.5 | 5.98 / 6.07 / 5.93 |
| first | movement_100_concurrent | 12.1 | False | - | 102.3 / 101.2 / 91.3 | 4.16 / 3.83 / 3.68 | 6820 | 75.2 | 4.29 / 4.34 / 9.16 |
| first | movement_100_local | 16.6 | True | - | 126.6 / 108.6 / 109.9 | 2.69 / 2.66 / 2.48 | 6821 | 78.3 | 8.96 / 8.97 / 8.15 |
| first | resource_100_concurrent | 73.8 | True | - | 233.1 / 370.0 / 212.9 | 5.06 / 4.82 / 5.67 | 6813 | 82.5 | 8.09 / 10.97 / 6.62 |
| first | resource_100_local | 7.3 | False | - | 129.4 / 138.8 / 129.8 | 2.48 / 2.52 / 2.45 | 6820 | 77.3 | 5.2 / 5.5 / 4.47 |
| first | simq_corpus_crowded_frontier | 35.8 | True | - | 69.7 / 58.8 / 51.3 | 0.62 / 1.49 / 2.32 | 5755 | 799.3 | 77.18 / 65.48 / 57.25 |
| first | simq_corpus_frontier_extended | 7.8 | False | CONSTRAINED,DEGRADED,SURVIVAL | 167.9 / 165.9 / 155.8 | 3.72 / 2.49 / 2.13 | 5876 | 1703.0 | 179.64 / 178.52 / 169.64 |
| first | simq_corpus_frontier_marches | 19.6 | True | CONSTRAINED | 100.9 / 84.4 / 97.9 | 3.1 / 1.94 / 1.92 | 6811 | 1568.3 | 112.26 / 95.36 / 107.72 |
| first | strategic_100_concurrent | 19.9 | True | SURVIVAL | 398.1 / 398.9 / 477.2 | 4.75 / 4.58 / 4.1 | 6811 | 91.3 | 13.15 / 12.23 / 13.95 |
| first | strategic_100_local | 10.6 | False | CONSTRAINED | 478.6 / 495.8 / 529.2 | 2.2 / 2.1 / 1.71 | 6820 | 80.6 | 14.1 / 14.06 / 16.84 |
| retry | combat_10_concurrent | 9.6 | False | - | 64.6 / 58.9 / 60.7 | 1.12 / 1.11 / 1.11 | 6568 | 64.5 | 2.91 / 2.4 / 2.85 |
| retry | combat_10_local | 96.9 | True | - | 30.7 / 59.8 / 30.4 | 1.23 / 1.13 / 1.12 | 6568 | 64.3 | 1.75 / 2.83 / 1.76 |
| retry | idle_100_local | 22.1 | True | - | 32.2 / 35.8 / 39.3 | 0.64 / 0.59 / 0.62 | 6571 | 64.0 | 2.72 / 3.49 / 3.38 |
| retry | movement_100_local | 28.8 | True | - | 134.9 / 126.8 / 104.8 | 0.73 / 0.78 / 1.25 | 6571 | 76.7 | 9.36 / 9.06 / 7.49 |
| retry | resource_100_concurrent | 12.5 | False | - | 236.3 / 218.5 / 210.0 | 1.18 / 1.15 / 1.2 | 6568 | 82.6 | 7.89 / 7.13 / 7.03 |
| retry | simq_corpus_crowded_frontier | 32.8 | True | - | 91.5 / 83.9 / 68.9 | 1.19 / 1.7 / 1.45 | 6568 | 796.9 | 99.16 / 94.31 / 78.55 |
