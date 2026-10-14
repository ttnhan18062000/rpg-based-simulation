---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan: TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN

Docs-only change plus a measurement. Run: `tests/visual_assets/test_budgets_parity.py` (the new section must not touch the Bounds table), `tests/docs`, the frontmatter validator on the three staging files and the ticket, `generate_registry.py --check` after `make docs-registry`. No code under `visual_assets/` changes.
