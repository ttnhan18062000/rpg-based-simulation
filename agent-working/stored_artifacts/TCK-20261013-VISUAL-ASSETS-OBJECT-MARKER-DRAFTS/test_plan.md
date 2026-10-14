---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS
artifact_type: test_plan
tags: [architecture, testing, mcp]
---

# Test plan: TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS

- Full `tests/visual_assets` once after the registry edit: expected red = the tests that export or pin the current candidate (rc-0010) and the key counts; exact ids recorded in the ticket.
- `tests/visual_assets/test_object_marker_silhouettes.py` (new, 4 tests: slots match keys and specs, options, deterministic sheet, malformed row refused).
- `python -m visual_assets.review.icon_specs` (specs complete), the style-guide table test, `generate_registry.py --check`, `tests/unit/tools` + `tests/tools` before the PR.
