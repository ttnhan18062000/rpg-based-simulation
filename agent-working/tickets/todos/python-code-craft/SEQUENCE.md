# Implementation Sequence — python-code-craft

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

**Corrected by hand 2026-10-02 (codebase-planner).** The generated order contained a cycle between
the two uv tickets and listed tickets ahead of their prerequisites, because it read every "Related
Tickets" entry as a dependency. This order follows the dependency table in
`TCK-20261002-PYTHON-CODE-CRAFT-EPIC` and each ticket's own "Depends on" statement.

`TCK-20261002-PYTHON-CODE-CRAFT-EPIC` is scope-only and is not in the order. It closes when the seven
tickets below are in `tickets/done/`.

## Order

1. TCK-20261002-PYTHON-CODE-STANDARD-DOC  (no deps in this batch)
2. TCK-20261002-UV-DECLARE-AND-LOCK  (no deps in this batch)
3. TCK-20261002-UV-FIRST-CI-JOB  (depends on: TCK-20261002-UV-DECLARE-AND-LOCK)
4. TCK-20261002-CODE-HEALTH-TOOL-CONFIG  (depends on: TCK-20261002-UV-DECLARE-AND-LOCK, TCK-20261002-PYTHON-CODE-STANDARD-DOC)
5. TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY  (depends on: TCK-20261002-CODE-HEALTH-TOOL-CONFIG)
6. TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS  (depends on: TCK-20261002-CODE-HEALTH-TOOL-CONFIG, TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY)

7. TCK-20261002-UV-REMAINING-CI-JOBS  (depends on: TCK-20261002-UV-FIRST-CI-JOB closed with a green PR run)

Tickets 1 and 2 are independent and can run in either order. Tickets 3 and 7 each need a real PR
run to close, so they cannot close on local evidence. Ticket 7 is independent of 4 to 6 and may run
as soon as ticket 3 is closed; it was written by hand after the scoping run (owner decision
2026-10-02 that this batch may edit the tests pinning CI and the Makefile).

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
