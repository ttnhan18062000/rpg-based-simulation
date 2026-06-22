# Test Plan — TCK-20260619-E53Ca-CONFLICT-PHASE

## Regression Surface
- tests/unit/faction/ (all existing faction tests)
- tests/unit/faction/test_faction_directive_propagation.py (anti-drift guards)

## New Tests Required
tests/unit/faction/test_military_conflict_phase.py:
- `test_military_conflict_phase_detects_war_pairs` (AC: phase identifies WAR pairs, returns StateUpdate)
- `test_military_conflict_phase_noop_on_peace` (AC: no WAR → empty StateUpdate)
- `test_military_conflict_phase_noop_empty_factions` (AC: empty state.factions → no error)

## Scoped Pytest Commands
```bash
pytest tests/unit/faction/test_military_conflict_phase.py -x -v
pytest tests/unit/faction/ -x -v
```

## Anti-Drift Test Guards
- MilitaryConflictPhase.execute() must return StateUpdate (not list) — check isinstance
