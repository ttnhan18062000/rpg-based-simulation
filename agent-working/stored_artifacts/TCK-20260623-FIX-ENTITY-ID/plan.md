# Plan — TCK-20260623-FIX-ENTITY-ID

## Summary

Production bug in `src/engine/pipeline.py`. Three phase lambdas return a fresh
`StateUpdate(...)` instead of merging into the accumulated `u`, wiping entity_updates
built by earlier phases. `StateUpdate.merge()` already exists in src/core/updates.py.

## Root Cause

`run_phase` assigns `update = phase_fn(upd)` directly. Three phases ignore `u`:

| Line | Phase | Bug |
|---|---|---|
| ~181 | faction_awareness | Returns `StateUpdate(faction_updates=...)` — wipes entity_updates |
| ~211 | diplomatic_transitions | Returns `StateUpdate(faction_updates=..., world_events_add=...)` — wipes again |
| ~221 | military_conflict | Returns `MilitaryConflictPhase.execute(state)` ignoring u — wipes again |

## Fix

Change all three from `lambda u: StateUpdate(...)` to `lambda u: u.merge(StateUpdate(...))`:

1. faction_awareness: `lambda u: u.merge(StateUpdate(faction_updates=...))`
2. diplomatic_transitions: `lambda u: u.merge(StateUpdate(faction_updates=..., world_events_add=...))`
3. military_conflict: `lambda u: u.merge(MilitaryConflictPhase.execute(state))`

## Parity Ledger

Check substrate.yaml and infrastructure.yaml for pipeline update accumulation entries.
No entity ID type change — fix preserves existing behavioral contract.

## Test Commands

```bash
pytest tests/unit/core/test_hardening_e5.py -x -q
pytest tests/integration/domains/test_fused_loop.py::test_belief_assimilation_persists_facts -x -q
pytest tests/integration/pipeline/test_recovery_gaps.py::test_building_sabotage -x -q
pytest tests/unit/engine/ tests/integration/pipeline/ -q --tb=no
```
