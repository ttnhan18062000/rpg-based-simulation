---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79
artifact_type: plan
tags: []
---

# plan - TCK-20261014-LEVEL-UP-NO-LONGER-RENAMES-AN-ENTITY-KIND-D79

1. `EvolutionSystem.evaluate` stops writing `kind_set` and `previous_kind`; `_get_evolved_kind` is deleted. Levels, ability points, stats and hp still rise at the thresholds.
2. The goblin stage-gear branch stays as it was (planner ruling, D78): it reads the entity's own kind, is keyed on a digit in the kind, and is dead; the missing `chainmail` item goes on the after-v1 list.
3. Tests: new `test_level_up_keeps_kind.py`; five conversions (`test_progression_regression.py`, `test_recovery_gaps.py` hero and goblin, `test_evolution.py` goblin and the `entity_evolved` test).
4. Measure paired against rpg-next `f7d3c25a0` (3 worlds, seeds 42-46, 5000 ticks, `audit_mode`, `PYTHONHASHSEED=0`, base-vs-base repeat). Write divergence 2.133; mark parity ledger PROG-125 divergent; mark the Bible-adjacent world-rule docs and the event-coverage table as superseded.
