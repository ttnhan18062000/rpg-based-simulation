# Implementation Sequence — test-architecture-maintenance-1

No epic parent: two independent maintenance tickets, one PR for the batch. Scale-out stays PAUSED by
the owner (2026-10-03), so this batch is test-architecture MAINTENANCE only: no RPG code or tests, no new
domain, no new tool or script.

Each ticket's plan goes to test-architecture-reviewer for review BEFORE implementation.

Binding for the batch (reviewer, relaying the owner's "continue, fold multiple tickets to next batch"):
no edit under `tests/` at all, no `docs/parity_ledger/` change, no `src/` change. Gate on the PR:
`git diff --name-only origin/main...HEAD` shows no `tests/` path.

## Order

1. `TCK-20261003-TEST-ARCH-MAINT-EPIC-B-COST-ROWS-292-302`  (hotfix; records only; no dependency)
2. `TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC`  (standard; docs only; no dependency)

The order is a convenience: M1 reads the jobs API and is short; M2 carries the doc, two small links and
`make knowledge-index-update`.
