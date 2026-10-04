# Implementation Sequence — test-architecture-maintenance-2

No epic parent: three independent maintenance tickets, one PR for the batch. Scale-out stays PAUSED by
the owner; the user chose "Small maintenance-2" (2026-10-03). No RPG test or `src/` change, no new domain
batch.

Each ticket's plan goes to test-architecture-reviewer for review BEFORE implementation.

Binding for the batch: `git diff --name-only origin/main...HEAD` shows `tests/` paths ONLY under
`tests/unit/tools/`, and no `src/` or `docs/parity_ledger/` path. No new tool: tooling follows evidence.

## Order

1. `TCK-20261003-TEST-ARCH-MAINT2-EPIC-B-COST-ROW-304`  (hotfix; records only; do it last in time so any PR merged after #304 is included)
2. `TCK-20261003-TEST-ARCH-MAINT2-ESCAPED-DEFECT-SEPTEMBER-COUNT`  (hotfix; runs the existing report; no code)
3. `TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN`  (standard; the only code change; its report run supplies the social row)

Numbers 1 and 2 are independent of 3. The cost-record ticket is filed first because it is short; its rows
are written at the end of the batch, immediately before the PR, so a PR merged in between is not missed.
