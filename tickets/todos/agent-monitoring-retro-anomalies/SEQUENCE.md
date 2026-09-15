# Sequence — agent-monitoring retro anomalies

Epic: `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC`

All eight children are independently investigable and independently landable. No child blocks
another, with one exception noted below. The order here is by leverage, not by dependency.

| # | Ticket | Why this order |
|---|---|---|
| 1 | `TCK-20260915-DUPLICATE-RUN-RECORDS` | 60 runs written twice with identical `execution_id` and `start_ts`. Inflates every run count, including the retro's own headline figure — so until this is understood, no throughput number is trustworthy. |
| 2 | `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` | 23.7% of tool rows carry neither `run_id` nor phase; `cost_proxy_score` covers 30.5% of events. The single change that would make the spend tables mean anything. |
| 3 | `TCK-20260915-TOOL-CALL-COUNT-MISMATCH` | 53 runs where the recorded count and the real rows differ >3x, 44 of them in Aug–Sep. Likely shares a cause with #2 — investigate after it, but do not assume. |
| 4 | `TCK-20260915-EVENT-SEQ-INTEGRITY` | 71 runs with duplicate `seq`, 46 with gaps. Breaks phase ordering, which several consumers rely on. |
| 5 | `TCK-20260915-EVENT-SUMMARY-TRUNCATION` | 47 summaries land on exactly 200 characters — silent information loss at write time. |
| 6 | `TCK-20260915-RETRO-INDEX-REPORTS-ZERO` | `index.md` shows 0 runs for reports containing 69/249/300. Cheap fix, high visibility: it is the first file a reader opens. |
| 7 | `TCK-20260915-MONITORING-INTEGRITY-BACKLOG` | The known-historical debt: 19 DONE runs with no working_log row (`agent-monitoring-validate` is red today), 34 September closures with no run record, 9 malformed working_log rows, 55 events / 66 runs with unusable `ts`, and the `unknown-week` shard. |
| 8 | `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` | **Scope this last.** Its checks should be written against the causes the other seven confirm, not against this epic's hypotheses. |
| 9 | `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` | Added 2026-09-15, after the hazard was hit during ticket 1's verification: regenerating a report destroys its hand-written `## Notes`, which the retro skill explicitly instructs a session to add and commit. Independent of the other eight — pick up whenever. |

## Ratchet discipline

Several of these counts are non-zero on a corpus nobody is going to retroactively clean. Any
detector introduced here **must ratchet from the measured baseline, never assert zero**, or it is
disabled on day one — the constraint established three times in
`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` and
`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`.

Baselines measured 2026-09-15, to be re-derived at implementation time rather than trusted:

| Signal | Baseline |
|---|---|
| duplicate run records (identical `execution_id` + `start_ts`) | 60 |
| runs with duplicate `seq` | 71 |
| runs with `seq` gaps | 46 |
| tool rows with no `run_id`/phase (14d window) | 12,033 of 50,696 (23.7%) |
| events with `cost_proxy_score` (14d window) | 579 of 1,897 (30.5%) |
| runs with >3x `tool_call_count` mismatch | 53 |
| summaries exactly 200 chars (14d window) | 47 |
| working_log rows off-schema | 9 of 2,013 |
| runs / events with unusable `ts` | 66 / 55 |

## Do not re-investigate

Checked during scoping and found healthy — see the epic's Request Summary for detail:

- 223 of 232 DONE-with-failed-event runs are healthy retries
- 345 bulk-identical-timestamp runs are orchestrator batch flushes, not hand-orchestration
- 82 of 142 duplicate `run_id`s are legitimate re-runs
