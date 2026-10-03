---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-BUDGETS
artifact_type: plan
tags: [performance, testing, mcp]
---

# Plan — TCK-20261003-VISUAL-ASSETS-BUDGETS

1. Inventory every bound (grep found three beyond the ticket's list: `readmodel.DEFAULT_LIMIT`/`MAX_LIMIT`, `intake.aseprite.MAX_PALETTE_ENTRIES`).
2. `tools/visual_assets_measure_budgets.py`: one measurement per process (`--only`), `--all` under the 2 GB cap. Outside `visual_assets/`, so no `STORE_ALLOWED` row.
3. Run the measurements one at a time (decode scaling and the at-bound decode are slow: pure Python, minutes).
4. `docs/assets/budgets.md`: one row per bound, rule R0-R4, flags F1-F6 where the rule gives a silly or conflicting answer (value kept).
5. Apply proposed values; replace "provisional (U-05)" comments with "budget: docs/assets/budgets.md".
6. `tests/visual_assets/test_budgets_parity.py` (doc rows vs code, missing rows, missing attributes, leftover comments); mutation-prove.
7. Update `store_contract.md`, the Aseprite plan README; fold planner's wording fix into ticket 1's Test Summary and `drawing_tools.md`.
8. Run `tests/visual_assets` without Aseprite, the strict target, static/architecture/docs; close.

Scope guard: no new bounds, no retention numbers, no decoder optimization.
