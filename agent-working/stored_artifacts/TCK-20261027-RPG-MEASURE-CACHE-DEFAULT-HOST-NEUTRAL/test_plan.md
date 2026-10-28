---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL
artifact_type: test_plan
tags: [benchmarking]
---

# Test plan

- Variable set: `resolve_cache()` returns that path, ahead of XDG.
- Fallback: variable unset gives `$XDG_CACHE_HOME/rpg-measure`; both unset gives `~/.cache/rpg-measure`.
- Unwritable: `main` exits 2 with one stderr line naming `RPG_MEASURE_CACHE` and the path, and `run_one` / `subprocess` are never called.
- Existing `test_rpg_measure.py` tests stay green; `tests/unit/tools` serial under MemoryMax=3G; `make code-health`; `make lint-imports`.
