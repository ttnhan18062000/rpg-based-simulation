---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Ca-CONFLICT-PHASE
phase: open
date: 2026-06-22
tags: [faction, war, military-conflict, phase, engine-wiring, phase-5]
---

# TCK-20260619-E53Ca-CONFLICT-PHASE

## Title
Epic 5.3Ca · MilitaryConflictPhase Registration + Engine Wiring

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Create the `MilitaryConflictPhase` stateless sub-phase class and wire it into the engine execution loop so it runs once per tick after `FactionDecisionPhase` within `TickPhase.INIT`. This ticket establishes the phase skeleton; siege logic is added in E53Cb–E53Cd.

**Requires:** TCK-20260619-E53Bc-STATE-MACHINE (DiplomaticState.WAR must be queryable), TCK-20260619-E53Ab-DECISION-PHASE (FactionDecisionPhase sub-phase pattern established)

## Scope

- Create `src/engine/military_conflict.py` with:
  - `MilitaryConflictPhase` class following the `WorldEmergencePhase` static pattern
  - `execute(state: AuthoritativeState, recent_events: List[WorldEvent]) -> StateUpdate` method
  - Phase detects faction pairs where `DiplomaticState.WAR` is active by reading `AuthoritativeState.factions`
  - Emits no-op `StateUpdate` for non-WAR pairs; logs faction pairs at WAR for observability
  - `WAR_DETECTED` log event per active war pair (not a `WorldEvent` — internal observability only at this stage)
- Wire `MilitaryConflictPhase.execute()` into the engine cadence immediately after `FactionDecisionPhase` within `TickPhase.INIT`; follow the exact wiring pattern used for `FactionDecisionPhase` (E53Ab)
- Add `from src.engine.military_conflict import MilitaryConflictPhase` import in the relevant kernel/cadence entry point

## Out of Scope
- Siege state model (E53Cb)
- Territory transfer (E53Cc)
- War exhaustion logic (E53Cd)
- Any mutation of `RegionState` or `FactionState` — this ticket only establishes the phase skeleton

## Acceptance Criteria
- `MilitaryConflictPhase.execute()` runs each tick in INIT without error when `AuthoritativeState.factions` is empty or contains no WAR-state pairs
- `MilitaryConflictPhase.execute()` correctly identifies faction pairs in `DiplomaticState.WAR` from `AuthoritativeState.factions`
- Unit test `test_military_conflict_phase_detects_war_pairs` passes: given two factions with `diplomatic_relations["other"] = DiplomaticState.WAR`, the phase execute returns a `StateUpdate` (may be empty) without raising
- Unit test `test_military_conflict_phase_noop_on_peace` passes: no WAR pairs → returns empty `StateUpdate`
- Engine integration: phase runs in correct order relative to `FactionDecisionPhase` in the authoritative tick loop

## Related Tickets
- TCK-20260619-E53C-WAR (parent epic)
- TCK-20260619-E53Bc-STATE-MACHINE (required — DiplomaticState.WAR)
- TCK-20260619-E53Ab-DECISION-PHASE (required — FactionDecisionPhase wiring pattern)
- TCK-20260619-E53Cb-SIEGE-MODEL (blocked on this)

## Related Docs
- `docs/engine/kernel.md` (6-phase loop, sub-phase insertion points)
- `docs/engine/authoritative_pipeline.md` (17-phase refinement sequence)
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md` (TickPhase frozen, sub-phase pattern)
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` (DiplomaticState.WAR transition rules)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`

## Related Code Areas
- `src/engine/military_conflict.py` (new)
- `src/engine/kernel.py` or `src/engine/world_dynamics.py` (wiring point)
- `src/engine/faction_decision.py` (reference for sub-phase pattern)
- `src/domains/world_emergence/phase.py` (reference for stateless phase pattern)

## Assumptions / Open Questions
- Exact wiring point (kernel.py vs world_dynamics.py vs cadence) to be determined at implementation time by reading the tick loop; follow E53Ab's precedent exactly.
- `owner_faction_id: Optional[int]` on `RegionState` vs `FactionState.faction_id: str` — the type mismatch (int vs str) must be investigated in this ticket and a resolution recorded before E53Cc touches `apply_plan.py`.

## Implementation Notes
- Phase must be stateless: no instance state, no caching.
- Follow `WorldEmergencePhase` pattern: `execute()` is a `@staticmethod` (or `@classmethod`) that reads `AuthoritativeState` and returns a `StateUpdate`.
- Do not import from `src/domains/campaigns/` — keep the engine layer clean of campaign-domain imports.
- Record the `owner_faction_id` int/str resolution decision in `implementation_notes` of the ticket before closing.

## Test Summary
```bash
pytest tests/unit/faction/test_military_conflict_phase.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
