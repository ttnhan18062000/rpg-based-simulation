---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER
phase: open
date: 2026-10-09
tags: [testing, determinism]
---

# Plan

1. After #457 merges, merge origin/main.
2. Add `tests/helpers/kernel_pinning.py` with `PinnedNormalGovernor(ResourceGovernor)` (docstring: host-speed independence, wall-clock throttle, names this ticket).
3. Replace each local class with an import; delete the class, keep every other line (assertions, seeds, ticks, worlds, executors, budgets) unchanged. Copy 2 keeps its monkeypatch and swaps the class only.
4. Add `tests/architecture/test_no_local_pinned_governor_copies.py`: AST scan of `tests/**/*.py` outside `tests/helpers/`, flag class with `ResourceGovernor` base (Name or Attribute), `_get_indicated_mode` body a single `return RuntimeMode.NORMAL`, `force_mode` body bare `return None`/`return`/`pass`. Message names the file and the helper. Scan logic in a function taking source text so unit fixtures can test it.
5. Fixtures: one positive copy, two negatives (DEGRADED pin; recording force_mode with super()).
No `src/` change.
