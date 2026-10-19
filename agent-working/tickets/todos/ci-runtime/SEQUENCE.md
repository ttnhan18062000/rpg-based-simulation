# Implementation Sequence — ci-runtime

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Hand-written 2026-10-19 by testing-planner.

`TCK-20261019-CI-RUNTIME-EPIC` is scope-only and is not in the order. Every child PR is reviewed by comment by
lead-planner-u24 as well as testing-planner (the user's ask, 2026-10-19); child 3 is also reviewed by lead-planner (ubuntu).

Queue position: after V8 AC4/AC5, TCK-20261019-TEST-YML-NODE-24-IN-FRONTEND-AND-JSCPD-LANES and TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK.

## Order

1. TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS  (no deps; fyi agent-working-planner before the Tools f–z part, #647)
2. TCK-20261019-CI-JOB-RUNTIME-BUDGET-WARN-ONLY  (depends on: 1; baseline also waits for test.yml on the Ubuntu 26 image)
3. TCK-20261019-CI-MAIN-PUSH-RERUN-TRIM  (no code deps; consultations with platform-planner and lead-planner (ubuntu) come first)
