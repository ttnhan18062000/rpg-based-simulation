# E53C — Territorial Conflict & War

**Parent epic:** TCK-20260619-E53C-WAR (EPIC_SCOPED)
**Inter-epic prerequisite:** E53B complete (DiplomaticStateMachine WAR state required)
**Inter-epic unlocks:** E53D-HISTORY (war events must be emitted before history integration)

## Sequence (linear)

1. **TCK-20260619-E53Ca-CONFLICT-PHASE** — `MilitaryConflictPhase` registered as INIT sub-phase (after FactionDecisionPhase); reads `DiplomaticRelationState` to identify active wars
2. **TCK-20260619-E53Cb-SIEGE-MODEL** — `SiegeState` frozen dataclass on `RegionState`; `military_strength` field on FactionState; squad commitment tracking
3. **TCK-20260619-E53Cc-TERRITORY-TRANSFER** — territory transfer via existing `WorldUpdate.owner_faction_id_set` (already in `apply_plan.py:L119`); emits `territory_transferred` NarrativeLedgerEntry; 3-faction integration test
4. **TCK-20260619-E53Cd-WAR-EXHAUSTION** — `military_strength` drain per tick; `SEEK_PEACE` directive triggers DiplomaticStateMachine WAR→NEUTRAL transition when exhaustion threshold reached; `test_war_exhaustion_ends_conflict`

## Key Notes

- `MilitaryConflictPhase` runs as INIT sub-phase — TickPhase is frozen, no new entries.
- Territory transfer reuses `WorldUpdate.owner_faction_id_set` — no new update type needed.
- `SiegeState` is a frozen dataclass added to `RegionState` (optional, None when no siege active).
- `SEEK_PEACE` directive from E53Ad delegates to `DiplomaticStateMachine` — not a direct state write.
