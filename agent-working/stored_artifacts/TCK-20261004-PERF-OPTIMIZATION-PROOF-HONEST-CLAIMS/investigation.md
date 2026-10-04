---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS
date: 2026-10-04
tags: [performance, benchmarking]
---

# Investigation: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS

## Findings
- The three defects in the ticket are confirmed in the code read before editing: `.get(..., 1.0)` fallbacks for TPS, p95 and RSS, ratio lines that fall back to `1.0` on a non-positive divisor, and fixed conclusion text in the markdown.
- Alignment gap (recorded, not changed): the proof runs `PROD_DEFAULT` (four scenarios) and `PROD_LARGE` (`MIXED_1000`) at 50 sample ticks and 20 warmup ticks, with `no_replay` and `no_frame_pacing` set. `tools/perf/run_perf_baseline.py` runs the same scenario names under `PERF_2GB_LOCAL` and `PERF_4GB_CONC`, 50 sample ticks, 10 warmup ticks, default flags, and a `{"resolution": 100.0}` phase budget. So every scenario is `not_comparable` on profile as configured.
- A second gap the comparison cannot see: `RESOURCE_1000` is built with 700 entities and 300 nodes in the proof and 1000 entities and 500 nodes in the baseline run. The harness dict carries no workload cardinality, so a matching profile and tick count would still not make that scenario like for like. The provisional schema's `workload.entity_count` is what would catch it.
- Ledgers: `docs/optimization_audit_ledger.md` and `docs/parity_ledger/infrastructure.yaml` contain no entry that cites this report. Docs that mention the generator by name (`docs/plans/scripts_tools_governance_epic.md`, `docs/archive/profiling_performance/perf_plan_v2.md`) do not present its output as evidence; the archive document is left alone.

## What alignment would take (for perf-planner)
1. Same profile name on both sides: change `SCENARIO_CONFIGS` profiles or the baseline run's profiles (the owner's choice; this ticket changes neither).
2. Same warmup and flags: the baseline run would need the proof's flags, or the reverse.
3. Same workload: align `RESOURCE_1000`'s counts, or record cardinality in the harness dict so the comparison can check it (a `src/` change, frozen).
4. A baseline taken after the entry gate lifts; until then every number is provisional anyway.
