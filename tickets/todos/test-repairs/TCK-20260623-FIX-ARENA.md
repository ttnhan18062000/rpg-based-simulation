---
status: open
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260623-FIX-ARENA
phase: open
date: 2026-06-23
tags: [test-repair, arena, quest, simulation, teardown, P2]
---

# TCK-20260623-FIX-ARENA

## Title
Fix arena simulation behavioral regression + teardown OSError (~5 failures)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Arena tests show two distinct failure patterns after excluding content-cascade failures
(which will be resolved by TCK-20260623-FIX-WORLDASSEMBLY):

**Pattern 1 — Quest/economy behavioral regression:**
```
test_arena_quests.py:      assert quest.current_value == 1.0   (got 0.0)
test_arena_quests.py:      assert hero.inventory.gold == 103   (got 98.0)
test_arena_regional_control.py  (2 failures)
test_arena_stop_conditions.py::test_arena_stop_condition_timeout
```
Quest completion isn't registering, and gold accumulation is off. This may be a cascade
from inventory defaults (TCK-20260623-FIX-INVENTORY-DEFAULTS) or reward label rename
(TCK-20260623-FIX-COMBAT-QUEST) — investigate after those P1 tickets land.

**Pattern 2 — Teardown OSError (leftover run data):**
```
OSError: [Errno 39] Directory not empty: 'data/runs/run_1782230444_5169'
ERROR at teardown of test_arena_stress_50v50
```
Arena stress test creates a run directory in `data/runs/` but teardown fails to clean it.
This is a test isolation issue — the arena test should use `tmp_path` or clean up its
own run directory in a `finally` block.

**Note:** `test_arena_startup.py` and `test_arena_stress.py` content errors will be
fixed by TCK-20260623-FIX-WORLDASSEMBLY (river_ford terrain reference).

## Scope
- Fix teardown OSError: add cleanup of `data/runs/` run directory in arena stress test teardown
  (use `shutil.rmtree` in a `finally` block or `autouse` fixture)
- Investigate quest/gold assertion failures AFTER TCK-20260623-FIX-INVENTORY-DEFAULTS and
  TCK-20260623-FIX-COMBAT-QUEST land; if still failing, trace the quest completion path
  in arena context
- Fix `test_arena_stop_conditions.py::test_arena_stop_condition_timeout` — check if timeout
  logic changed or if this is a cascade from quest failures

## Out of Scope
- Arena logic changes
- New arena scenarios
- Performance of arena runs

## Acceptance Criteria
- `tests/arena/test_arena_quests.py::test_arena_quest_progression` passes
- `tests/arena/test_arena_regional_control.py` — both tests pass
- `tests/arena/test_arena_stop_conditions.py::test_arena_stop_condition_timeout` passes
- No `OSError: Directory not empty` at teardown of `test_arena_stress_50v50`
- Depends on: TCK-20260623-FIX-WORLDASSEMBLY, TCK-20260623-FIX-INVENTORY-DEFAULTS,
  TCK-20260623-FIX-COMBAT-QUEST (implement those first)

## Related Tickets
- TCK-20260623-FIX-WORLDASSEMBLY (content errors in arena startup/stress — prerequisite)
- TCK-20260623-FIX-INVENTORY-DEFAULTS (gold/inventory mismatch — may cascade-fix arena)
- TCK-20260623-FIX-COMBAT-QUEST (quest reward labels — may cascade-fix arena)

## Related Docs
- `docs/mechanics/02_combat_laws.md`
- `docs/mechanics/03_economic_laws.md`

## Related Code Areas
- `tests/arena/test_arena_quests.py`
- `tests/arena/test_arena_regional_control.py`
- `tests/arena/test_arena_stop_conditions.py`
- `tests/arena/test_arena_stress.py` (teardown cleanup)
- `tests/arena/conftest.py` (if exists — add cleanup fixture here)

## Assumptions / Open Questions
- Will quest/gold failures resolve automatically once P1 tickets land?
  (Check arena tests again after TCK-20260623-FIX-INVENTORY-DEFAULTS + FIX-COMBAT-QUEST)
- Does arena stress test have a conftest or fixture for run cleanup?

## Implementation Notes
Start this ticket AFTER TCK-20260623-FIX-WORLDASSEMBLY, FIX-INVENTORY-DEFAULTS, and
FIX-COMBAT-QUEST are complete — some arena failures may resolve as cascades.

Teardown fix is independent and can be done immediately:
- Find where arena stress test creates `data/runs/` directory
- Add `shutil.rmtree(run_dir, ignore_errors=True)` in test teardown

## Test Summary
Run: `pytest tests/arena/ -m "not slow" --tb=short`

## Files Changed
_To be filled during implementation._

## Completion Summary
_To be filled on completion._
