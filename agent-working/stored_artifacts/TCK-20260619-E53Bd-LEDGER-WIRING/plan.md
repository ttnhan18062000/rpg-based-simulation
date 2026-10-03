# Plan — TCK-20260619-E53Bd-LEDGER-WIRING

## Approach

1. Add three `WorldEventCategory` enum members to `schema.py`
2. Add `events_from_transitions(transition_updates, alliance_updates, prior_factions, tick)` to `diplomatic_state_machine.py` — lazy-imports `WorldEvent`/`WorldEventCategory`, deduplicates via `frozenset` pairs, maps WAR/NEUTRAL(from WAR)/ALLIED to the three event categories
3. Split Phase 8d in `pipeline.py` into separate `_diplo_transition_updates` and `_diplo_alliance_updates` lists; call `events_from_transitions()` after both; include `world_events_add` in the `StateUpdate`
4. Add 3 entries to `_SIGNIFICANCE_MAP` in `orchestrator.py`
5. Add 5 tests

## Key Constraints

- `diplomatic_state_machine.py` cannot import from `src.engine` — WorldEvent imported lazily inside function body
- `WorldEvent.payload: Dict[str, float]` — faction IDs go in `subject` field, not payload
- Emit exactly one WorldEvent per faction pair per call (frozenset dedup)
