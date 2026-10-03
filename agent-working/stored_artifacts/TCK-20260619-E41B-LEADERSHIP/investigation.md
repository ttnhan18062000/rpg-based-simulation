---
ticket_id: TCK-20260619-E41B-LEADERSHIP
phase: investigation
date: 2026-06-21
---

# Investigation — TCK-20260619-E41B-LEADERSHIP

## Summary

This ticket implements `PartyLifecycleService` with periodic leadership election based on the OCEAN `sociability` personality trait, and emits a `LeadershipChangedEvent` SimulationEvent on leader transitions. It depends on TCK-20260619-E41A-GROUP-LIFECYCLE (GroupRecord lifecycle fields already added).

---

## Key Files Examined

### State Layer
- `src/core/state.py` — `GroupRecord` (frozen dataclass, `slots=True`) already carries `last_leadership_check_tick: int = 0` and `leader_id: int`. `PersonalityComponent` carries `sociability: float = 0.0`. `EntityState.personality` is a `PersonalityComponent` field.
- `src/core/updates.py` — `StateUpdate.groups_add_or_update: List[GroupRecord]` is the authoritative channel for group mutations. No `GroupUpdate` dataclass exists; groups are updated by submitting a modified `GroupRecord` in `groups_add_or_update`.

### Pipeline
- `src/engine/pipeline.py` line 257: `run_phase("groups", update, lambda u: AuthoritativeApplyPipeline._resolve_groups(state, u))` — this is the authoritative group resolution phase.
- `src/engine/pipeline_phases/groups.py` — `GroupPhase.resolve()` calls `GroupSystem.update_groups()`, merges results, and returns an updated `StateUpdate`. This is where leadership election logic should be called, inside the groups phase.
- `src/systems/world_systems/groups.py` — `GroupSystem.update_groups()` handles group cohesion, member filtering, role assignment, and anchor updates. Leadership election should integrate here or be called from `GroupPhase.resolve()`.

### Observability
- `src/observability/events.py` — `SimulationEvent` base class (Pydantic `BaseModel`). Pattern for new event types: subclass `SimulationEvent`, set `event_type`, `event_category`, `severity`, `source_system` as class fields with string defaults, add domain-specific fields, and override `__init__` to auto-generate `message`. All existing events follow this pattern.

### Existing Social Tests
- `tests/unit/social/test_group_lifecycle_fields.py` — test pattern for GroupRecord field round-trips via `ApplyPath`.
- `tests/unit/social/test_party_coordination.py` — test pattern for party system using `V2EntityBuilder`.
- `tests/unit/social/` directory has no `test_party_lifecycle.py` yet — must be created.

---

## Architecture Findings

1. **No `GroupUpdate` dataclass**: Groups are mutated by placing a new `GroupRecord` in `StateUpdate.groups_add_or_update`. The ticket spec refers to `GroupUpdate(group_id=..., new_leader_id=..., leadership_changed=True)` — this is a conceptual return type, not an existing class. Implementation must return a `StateUpdate` containing a modified `GroupRecord`.

2. **Tick check location**: `last_leadership_check_tick` is already a field on `GroupRecord` (added by E41A). The service must check `tick - group.last_leadership_check_tick >= LEADERSHIP_CHECK_INTERVAL` before running the election, and update it regardless.

3. **Member lookup**: Members must be filtered to those present in `state.entities` and alive. The `sociability` field is at `entity.personality.sociability`.

4. **Wiring point**: The cleanest integration point is inside `GroupPhase.resolve()` — after `GroupSystem.update_groups()` runs (which handles cohesion/dissolution), call `PartyLifecycleService.run_lifecycle_checks()` on each surviving group, merging the resulting `StateUpdate`.

5. **Event emission**: `LeadershipChangedEvent` must be a `SimulationEvent` subclass in `events.py`, category `"social"`. Events are normally generated in `EventExtractor.extract()` but for direct emission from the pipeline the returned `StateUpdate` can carry a `world_events_add` entry OR the kernel dispatches via `_event_listeners`. The cleanest approach matching the ticket spec ("emit `leadership_changed` SimulationEvent") is to add the event to `StateUpdate.world_events_add` — however, `world_events_add` holds `WorldEvent` objects, not `SimulationEvent` objects. Instead, the pipeline's `_phase_observability` uses `EventExtractor.extract()` which inspects state diffs. The simplest correct approach for this ticket is to define `LeadershipChangedEvent` and emit it via the existing `StateUpdate.world_events_add` if `WorldEvent` is compatible — but on inspection, `WorldEvent` is a domain schema object. The correct pattern is to store the leadership-changed fact in the updated `GroupRecord` (e.g. no separate flag needed — the change in `leader_id` is evidence) and let `EventExtractor` detect it, OR return the events directly from the phase as a list to be added to the kernel's event list. Looking at how this is done in the pipeline: the pipeline phases return a `StateUpdate`, and the kernel's `_phase_observability` calls `EventExtractor.extract()`. For E41B scope, the simplest path that satisfies the acceptance criterion ("emits `leadership_changed` SimulationEvent") is: define `LeadershipChangedEvent` in `events.py`, create it in `PartyLifecycleService.check_leadership()`, and thread it through by adding a `pending_events` list to the returned state update. However `StateUpdate` has no `pending_events` field. The correct approach is to collect events from `PartyLifecycleService` and dispatch them via the kernel's `_event_listeners` by making `GroupPhase.resolve()` return them as `world_events_add` if `WorldEvent`-compatible, or by adding a `leadership_events` mechanism. Given the scope of this ticket, the pragmatic solution is: define `LeadershipChangedEvent`, call `_event_listeners` via a module-level collector, OR simply emit via `StateUpdate.world_events_add` using the `WorldEvent` dataclass. On closer inspection, `WorldEvent` (from `src/domains/world_emergence/schema.py`) is unrelated. The cleanest, lowest-coupling approach: return events from `PartyLifecycleService` as a list and dispatch them from within `GroupPhase.resolve()` via `state`'s event_listeners — but state doesn't own listeners. **Final decision**: `GroupPhase.resolve()` collects `SimulationEvent` instances from `PartyLifecycleService`, and calls `kernel._event_listeners` is not accessible from here. Instead, append events via a simple registry accessor function that the tests can also verify. Since the kernel dispatches `generated_events = EventExtractor.extract(...)` and then calls `_event_listeners`, and the ticket says "emit leadership_changed SimulationEvent", the correct minimal implementation is: define `LeadershipChangedEvent`, instantiate it in `PartyLifecycleService.check_leadership()`, and return it alongside the state update as a tuple. `GroupPhase.resolve()` collects those events and stores them in a module-level buffer (observable from tests) — OR, more cleanly, `GroupPhase.resolve()` calls a `SimulationEventBus.emit()` if one exists. Given this codebase's pattern, the most robust approach without invasive changes: the `LeadershipChangedEvent` is created in `PartyLifecycleService`, returned alongside the `StateUpdate`, and `GroupPhase.resolve()` dispatches it via the existing observability event recorder if accessible — or, since the pipeline doesn't have direct event recorder access, the events are stored in a thread-local / process-global buffer that tests can inspect. **Revised final decision**: Follow the kernel pattern: `_event_listeners` are called from within `_phase_observability`. Therefore, the correct approach for non-extractor events is to use `StateUpdate.world_events_add`. But `WorldEvent` is from `world_emergence`. The **simplest correct solution** consistent with the codebase is: have `PartyLifecycleService.check_leadership()` return a tuple `(Optional[GroupRecord], Optional[LeadershipChangedEvent])`, wire the group update into `groups_add_or_update`, and dispatch the event via a simple module-level event sink that tests can hook. This is the most test-friendly and architecturally clean path.

---

## Dependency Status

- TCK-20260619-E41A-GROUP-LIFECYCLE: DONE — `last_leadership_check_tick` field present on `GroupRecord`.
- `PersonalityComponent.sociability` field: present in `src/core/state.py`.
- `EntityState.personality`: confirmed field at line 446 of state.py.
