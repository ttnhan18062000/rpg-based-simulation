---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER
phase: done
date: 2026-10-09
tags: [testing, determinism]
---

# Test plan

- Before change, at the head after #457: run each of the 4 files 3 times, record pass/fail and any asserted values printed.
- After change: same 4 files 3 times each, identical results.
- Guard test passes on the new head; fails on the positive fixture; passes on both negatives.
- Diff check: nothing under `src/`; no assertion/seed/tick/world id edited in the four files.
- Run via `../behavioral-5k-impl2/.venv/bin/python -m pytest <file>` (no venv in own worktrees).
