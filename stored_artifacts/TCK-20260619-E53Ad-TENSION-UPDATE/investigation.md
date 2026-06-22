# Investigation — TCK-20260619-E53Ad-TENSION-UPDATE

## Key Findings

### 1. WorldEvent.region_id confirmed
`WorldEvent(frozen=True, slots=True)` in `src/domains/world_emergence/schema.py`:
- `category: WorldEventCategory`
- `region_id: Optional[str] = None`
- `tick: int`
- `severity: float = 1.0`
`WorldEventCategory.RESOURCE_DEPLETED = "RESOURCE_DEPLETED"` confirmed.

### 2. Apply-path tension cap already in place (E53Aa)
`apply.py:345`: `tension_level=max(0.0, min(1.0, new_tension))` — existing ✓

### 3. faction_updates already processed in apply.py
`apply.py:330`: iterates `update.faction_updates` and applies each FactionUpdate ✓

### 4. recent_world_events access pattern
`getattr(state, "recent_world_events", [])` — standard pattern, safe (returns [] if field absent).
This is the bounded window from previous ticks stored on AuthoritativeState.

### 5. Wiring location
The faction_decision block in pipeline.py is the correct site.
FactionAwarenessService runs after FactionDecisionPhase in the same block.
Tension updates are merged into StateUpdate via StateUpdate.merge_many().

### 6. Placement of FactionAwarenessService
Goes in `src/engine/faction_decision.py` (same file as FactionDecisionPhase).

### 7. StateUpdate merging
StateUpdate.merge_many([update, awareness_upd]) or use run_phase with a lambda.
The faction_decision block is NOT wrapped in run_phase — merging must be done explicitly.
StateUpdate has merge_many classmethod.

### 8. RESOURCE_DEPLETED event filtering
Filter: `event.category == WorldEventCategory.RESOURCE_DEPLETED`
Region matching: `event.region_id in fs.territory` (string containment)
None guard: `event.region_id is not None` before checking

### 9. Parity ledger target
`docs/parity_ledger/faction.yaml` — existing file from E53Aa. Add FACTION-TENSION-001.
