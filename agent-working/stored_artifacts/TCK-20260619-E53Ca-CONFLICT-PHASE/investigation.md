# Investigation — TCK-20260619-E53Ca-CONFLICT-PHASE

## Current Behavior

### Pipeline wiring pattern (src/engine/pipeline.py)
Phase 8b–8d follow this exact pattern:
```python
t_start = time.perf_counter_ns()
from src.engine.X import Y
result = Y.execute(state, ...)
update = run_phase("name", update, lambda u: StateUpdate(...))
costs["name"] = (time.perf_counter_ns() - t_start) / 1e6
```
MilitaryConflictPhase inserts as Phase 8e immediately after Phase 8d (diplomatic_transitions, L213).

### FactionState (src/core/state.py:L570)
- `faction_id: str`
- `diplomatic_relations: Dict[str, DiplomaticState]`
- `military_strength: float`
- `territory: List[str]`

### RegionState (src/core/state.py:L208)
- `owner_faction_id: Optional[int]` — **TYPE MISMATCH**: int vs FactionState.faction_id:str

### AuthoritativeState.factions (src/core/state.py:L1115)
`Dict[str, FactionState]` — keyed by faction_id string. E53Ca only reads this.

### WorldEmergencePhase pattern (src/domains/world_emergence/phase.py:L21)
`@staticmethod execute(state, update, recent_events) -> tuple[StateUpdate, WorldEmergenceResult]`
MilitaryConflictPhase uses simpler signature: `execute(state) -> StateUpdate` (no update pass-through needed at this stage).

## Mechanics/Engine Constraints

- `docs/engine/authoritative_pipeline.md`: Phase 8e runs inside `refine()` — read-only on state, returns StateUpdate
- No direct mutation of AuthoritativeState — only through StateUpdate/apply-path
- Phase must be stateless (no instance variables, no caching)
- No imports from `src/domains/campaigns/` — keep engine layer clean

## Parity Ledger Overlap

None directly. `docs/parity_ledger/faction.yaml` will get FAC-008 when behavior is introduced in E53Cb+.

## Owner_faction_id Type Mismatch Resolution

`RegionState.owner_faction_id: Optional[int]` vs `FactionState.faction_id: str`.
**Decision**: E53Ca does NOT touch territory/region ownership. Record mismatch here; E53Cc will resolve by either:
  a. Casting to int when writing (if faction_id strings are numeric in practice), or
  b. Adding a parallel `owner_faction_str_id: Optional[str]` field on RegionState.
This is an open question for E53Cc — do not preempt it in E53Ca.

## Risks and Open Questions

1. **owner_faction_id int/str mismatch**: Documented above. Deferred to E53Cc.
2. **WAR pair iteration order**: Must be lexicographic to stay deterministic (same as diplomatic_state_machine.py).
3. **Empty factions guard**: Phase must be a no-op when `state.factions` is empty.

## Anti-Drift Hazards

- Existing `test_faction_decision_phase_returns_list_not_state_update` tests that execute() returns list not StateUpdate — MilitaryConflictPhase.execute() MUST return StateUpdate, not list.
- Do not import from src.engine inside MilitaryConflictPhase (to avoid circular imports) — use TYPE_CHECKING guard.
