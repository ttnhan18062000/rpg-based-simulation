---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER
date: 2026-10-09
tags: [performance, determinism, testing]
---

# Plan: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER

Docs only. No `src/` or test edit, no rerun, no measurement.

1. Write `docs/performance/baseline_invalidation_ledger.md`: definitions of the three statuses, the change table with merge commits, one row per artifact (grouped, every file counted), the consumer effects, the rerun plan with contract, and the search commands.
2. No machine-readable twin: no test or tool reads one.
3. Update the M1 epic's T05 row and the roadmap's M1 status to done, with the ledger pointer.
4. Ticket and staging artifacts completed; regenerate `docs/REGISTRY.yaml`; run `tests/docs`, `tests/unit/tools`, frontmatter validators, `generate_registry --check`.
5. Tell perf-planner before each commit; no push.

Status vocabulary: valid (comparable after M1), rerun (not comparable, artifact stays in use, needs a new capture), incomparable (not comparable, not refreshed in place; replaced under the M2 identity schema or kept as history).
