---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Plan: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION

Investigation only. No `src/` edit; tests and docs only.

1. **Reader inventory (AC2).** List every `work_debt` / `work_debt_total` / `work_debt_updates` reference in `src/` (git grep after `search_docs` and `graphify query`), classify each as writer, reader, pass-through or reporting, and say what is constant because debt is empty.
2. **Confirming test (AC1).** New `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`: real runs of each non-combat perf scenario at a tight profile (tiny tick budget, `audit_mode` off where needed) with a recording `Kernel` subclass. Precondition asserted in the same test: `status.total_dropped_work > 0`. Claim asserted: `state.work_debt == {}` after every tick, and the governor's `work_debt_total` signal is 0 every tick.
3. **Intent (history and docs).** `git log -S work_debt`, `-S drain_debt`, `-S work_debt_updates`; read `resource_governor_contract.md`, `scheduler_work_model_matrix.md`, `scheduler_test_matrix.md`, the M4/M5 stored artifacts and PERF-D3.
4. **Recommendation (AC3).** Producer / retire / certification-only, with evidence, written in the ticket and sent to perf-planner for the owner. Not implemented.
5. Docs: record the finding where it belongs (an investigation note or the PERF-D3 evidence line) only if the owner-facing recommendation needs a durable home; do not edit contracts.

Scope guard: if any step needs a `src/` edit, stop and report.
