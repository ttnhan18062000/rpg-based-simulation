---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK
artifact_type: plan
tags: [mcp, live-map, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK

1. Measure sizes; ask the owner to approve the retention number and name the rollback owner (blocking questions).
2. gc: age rule on PASSED never-adopted intakes (with their review exports), report-only `tracked_unreferenced`, CLI dry-run report line; tests and mutants.
3. Budgets row, store_contract rule for future tracked-object deletion, parity test updated.
4. Rollback drill in the harness (previous build = rehearsal export, new = pilot export), mid-load switch test and the mixed-snapshot mutant.
