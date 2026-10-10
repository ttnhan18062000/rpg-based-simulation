---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP
artifact_type: test_plan
tags: [architecture, security, testing]
---

# Test plan
- tests/visual_assets/store/unit/test_pixels_unfilter.py: random equivalence (every filter, 1-4 channels, widths 1-33, mixed), extreme bytes, unknown filter refused in both, `_add_bytes` wrap, whole-corpus equality, real-decoder round trip, memo (decoded once, refusal not cached, bound is part of the key, at most four entries).
- tests/visual_assets/store/unit/test_pixels.py (existing): malformed/oversized/truncated/APNG/etc. refusals unchanged.
- Regression: tests/visual_assets (store, boundaries, budgets parity), tests/unit/tools, tests/tools before the PR.
