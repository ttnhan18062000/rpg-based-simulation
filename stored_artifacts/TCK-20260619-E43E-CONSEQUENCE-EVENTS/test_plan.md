# Test Plan — TCK-20260619-E43E-CONSEQUENCE-EVENTS

## Test locations

- Unit: `tests/unit/social/test_social_memory.py` (append)

## Test cases

### Acceptance criteria tests (named in ticket)

| Test | AC | What it verifies |
|---|---|---|
| `test_known_traitor_event_fires_on_encounter` | AC-1 | `KnownTraitorSpottedEvent` fires when `entity_hostility[entity.id] >= 0.5` |
| `test_faction_memory_survives_episode_without_member_npcs` | AC-2 | Already covered by E43D test; passes via existing implementation |
| `test_all_three_event_kinds_importable` | AC-3 | `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED` importable from events.py |

### Coverage tests

| Test | What it verifies |
|---|---|
| `test_legendary_arrival_event_fires` | `LegendaryArrivalEvent` fires when `faction_reputation["default"] >= 0.9` |
| `test_old_debt_collected_event_fires` | `OldDebtCollectedEvent` fires when `relationship_scores[other] >= 0.5` |
| `test_no_events_when_no_faction_memory` | No events returned when campaign_state has no faction memory for the faction |
| `test_no_traitor_event_below_threshold` | `KnownTraitorSpottedEvent` does NOT fire when `entity_hostility < 0.5` |
| `test_evaluate_returns_list` | `evaluate_social_consequence` return type is always a list (never None) |
| `test_event_classes_are_simulation_events` | All 3 event classes are subclasses of `SimulationEvent` |
| `test_event_kinds_are_string_constants` | All 3 kind constants are strings |

## Run command

```bash
pytest tests/unit/social/test_social_memory.py -x -v -m "not slow"
```

## Determinism contract

`evaluate_social_consequence()` is a pure function — same inputs always produce same outputs. No random numbers, no IO. Threshold comparisons are deterministic float operations.

## Architecture test

- Verify `consequence_events.py` does not import from `src.engine` or `src.core.state` at module level
- Verify events returned are `SimulationEvent` instances (not raw dicts or domain objects)
