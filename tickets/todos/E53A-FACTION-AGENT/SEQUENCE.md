# E53A — Faction Agent Autonomous Decision-Making

**Parent epic:** TCK-20260619-E53A-FACTION-AGENT (EPIC_SCOPED)
**Inter-epic prerequisite:** None (E53A is the first E53 child epic)
**Inter-epic unlocks:** E53B-DIPLOMACY (requires FactionState + directive types from E53Aa/Ab)

## Sequence (linear)

1. **TCK-20260619-E53Aa-FACTION-STATE** — `FactionState` frozen dataclass (string faction_id, not IntEnum) + `AuthoritativeState.faction_states` field + serialization
2. **TCK-20260619-E53Ab-DECISION-PHASE** — `FactionDecisionPhase` registered as INIT sub-phase (TickPhase is frozen — no new entries); reads FactionState, emits `FactionDirective` list
3. **TCK-20260619-E53Ac-DIRECTIVE-PROP** — `FactionDirectivePropagator` routes directives to matching entity goals; new `GoalKind.FACTION_DIRECTIVE`
4. **TCK-20260619-E53Ad-TENSION-UPDATE** — `FactionTensionService` updates `faction_tension` on RegionState each tick; emits `faction_tension_high` WorldEvent at threshold

## Key Notes

- `FactionState` uses `faction_id: str` (catalog string ID) — NOT `Faction(IntEnum)` from `src/core/enums.py`. These are separate concepts.
- `FactionDecisionPhase` runs as a sub-phase within existing `TickPhase.INIT` — do not add new TickPhase entries.
- `AuthoritativeState.faction_states` follows the same pattern as `population_cohorts` (added by E52A).
