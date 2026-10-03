# Implementation Sequence — python-code-craft-gates

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Hand-written 2026-10-03 by codebase-planner from
`docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md`.

`TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC` is scope-only and is not in the order.

## Order

1. TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB  (no deps; starts the soak)
2. TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK  (depends on: 1)
3. TCK-20261003-MYPY-BASELINE-ADVISORY  (no deps; may run alongside 1, and should merge within the soak window)
4. TCK-20261003-PREK-GIT-HOOKS-OPT-IN  (depends on: 1)
5. TCK-20261003-TYPE-CHECKER-TRIAL  (no deps; report only)
6. TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING  (BLOCKED until the soak end date recorded by 1; needs 1, 2, 3)

Tickets 1 to 4 and 6 each need a real PR run to close. Ticket 3 should merge early in the soak so mypy
gets its full two weeks advisory before 6 flips it.
