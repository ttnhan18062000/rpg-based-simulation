---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT

1. Measure: `ast` scan of every tracked `.py` file for cross-package imports (src/ has namespace packages, so grimp sees 215 of 744 files and is not used); sizes from `git ls-files`.
2. Assign layers (extend D14's 8 packages to 36), decide per package, write `docs/plans/codebase_health/src_package_structure_audit.md`.
3. Write outbox notes (rpg-planner, testing-planner) with status: pending.
4. Roadmap 6.4 path update is ticket 2's, not this ticket's (planner review nit 2).
Docs only; no `src/` change; no code, so no new test (the registry validator in ticket 2 makes "one row per tracked package" checkable).
