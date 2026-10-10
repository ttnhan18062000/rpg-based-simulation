---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, testing]
---

# Test plan

`tests/visual_assets/test_key_usage.py` (8): scan finds plain literals of a registered family and labels app/harness; scan ignores tests, fixtures, other families, partial matches and other suffixes; template literals with interpolation are dynamic references; every finding classified from planted references (alias resolved, harness-only never fallback-only); no candidate; real report deterministic and shaped; the command exits 0 and changes nothing (git status unchanged). Mutants M1-M8. Boundary: `catalog` added to the review layer's allowed store layers (planted violations still caught).
