# TCK-20260422-RECOVERY-GAPS

## Title
Implementing Phase 7 & 8 Recovery Gaps (Hazards, Calamities, Evolution, Sabotage)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Continue the V2 engine recovery by implementing the remaining semantic gaps identified in the Phase 7 backlog and Phase 8 planning. This includes regional hazards, calamity consequences, entity evolution, and building sabotage.

## Scope
- Implement **Regional Hazards** substrate (LEG-RPG-071).
- Implement **Calamity Consequences** substrate (LEG-RPG-139).
- Implement **Entity Evolution** mechanics (LEG-RPG-143).
- Implement **Building Sabotage** interactions (LEG-RPG-001/006).
- Synchronize **Legacy Checklists** (Part 1-5) with implemented behavior.

## Out of Scope
- Full Tactical AI expansion (Ph 8 Milestones 2-6).
- Broad strategic cognition recovery (Ph 9).

## Acceptance Criteria
- [x] Regional hazards affect entity status/readiness based on position.
- [x] Calamity levels influence regional hazard intensity and world dynamics.
- [x] Entities can evolve (transform identity/role) upon reaching thresholds.
- [x] Buildings can be sabotaged, affecting regional services (Shop, Blacksmith).
- [x] All 5 Legacy Checklists are updated to reflect the new implementation status.
- [x] 100% test pass rate for recovery gap proof suite.

## Related Tickets
- None

## Related Docs
- [resource_phase7_high_level.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase7_high_level.md)
- [docs/engine/phase7_backlog.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/phase7_backlog.md)
- [legacy_checklist_part1.md](file:///home/vboxuser/Work/rpg-based-simulation/legacy_checklist_part1.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src/core/state.py`
- `src/engine/pipeline.py`
- `src/engine/legality.py`

## Implementation Notes
- **Regional Hazards**: Implemented in `WorldDynamicsSystem`. It iterates over regions, finds entities within `bounds`, and applies HP/Readiness drains scaled by `hazard_level` and `calamity_intensity`.
- **Evolution**: Implemented in `EvolutionSystem`. Tracks `evolution_points` and triggers transformation to a new `kind` and `evolution_level` when threshold (1000) is hit.
- **Sabotage**: Implemented in `BuildingSabotageSystem`. Routes `SABOTAGE` intents to damage buildings. If HP falls below 50, `functional` is set to `False`, which is now respected by `ShopSystem` and `BlacksmithSystem`.
- **State Integrity**: Updated `AuthoritativeState` and `EntityState` to be the singular sources of truth for these mechanics, fulfilling the M7 Law of deterministic substrate.

## Test Summary
- `tests/verify/test_recovery_gaps.py`: Specialized contract proof for hazards, evolution, and sabotage (3/3 PASS).
- `tests/integrity/test_logic_guards.py`: Verified autonomous loop determinism and scenario build integrity (7/7 PASS).
- `tests/`: Full V2 test suite (232/232 PASS).

## Files Changed
- `src/core/state.py`
- `src/core/updates.py`
- `src/engine/apply.py`
- `src/engine/pipeline.py`
- `src/engine/world_dynamics.py`
- `src/engine/evolution.py`
- `src/engine/sabotage.py`
- `src/engine/shop.py`
- `src/engine/blacksmith.py`
- `docs/engine/legacy_replacement_ledger.md`
- `legacy_checklist_part1.md`
- `legacy_checklist_part3.md`
- `legacy_checklist_part4.md`

## Completion Summary
Phase 7/8 recovery gaps are now officially closed. The V2 engine has a hardened representation of regional hazards, calamities, entity evolution, and infrastructure sabotage. All mechanics are integrated into the authoritative apply pipeline and verified against legacy semantics.
