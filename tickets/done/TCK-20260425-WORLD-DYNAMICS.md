# TCK-20260425-WORLD-DYNAMICS

## Title

Implementation of Phase 11 World Dynamics: Influence, Conquest, Strongholds, and Macro Threats.

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement regional influence shifts, territory conquest/liberation lifecycle, stronghold spawning with debuffs, world maturity, calamities (world bosses), and faction raids.

## Scope

- Faction influence shifts based on hero/monster deaths.
- Territory conquest and liberation logic.
- Stronghold spawning and removal in regions.
- Aura of Despair debuff near strongholds.
- World maturity advancement.
- Periodic Faction Raids.
- Calamity (World Boss) spawning.

## Out of Scope

- Full faction AI (strategic NPC factions).
- Economic impact of conquest.

## Acceptance Criteria

- [x] Influence shifts on combat outcomes.
- [x] Regions change ownership at influence thresholds.
- [x] Strongholds spawn on conquest and are removed on liberation.
- [x] Aura of Despair reduces movement speed of nearby heroes.
- [x] Maturity increases over time.
- [x] Calamities spawn on maturity milestones.
- [x] Raids spawn on fixed intervals far from town.

## Related Tickets

- None

## Related Docs

- [resource_v2_e_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e_phases.md)
- [legacy_checklist.md](file:///home/vboxuser/Work/rpg-based-simulation/legacy_checklist.md)
- [parity_ledger.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/world/influence.py`
- `src/world/raid.py`
- `src/world/environment.py`
- `src/systems/generator.py`
- `src/engine/apply.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added `entities_add` and `entities_remove` to `StateUpdate`.
- Implemented authoritative entity management in `ApplyPath.apply_generation`.
- `FactionInfluenceService` handles conquest lifecycle.
- `RaidService` and `CalamityService` handle macro threats.

## Test Summary

- `tests/world/test_influence.py` (Influence and Conquest)
- `tests/world/test_stronghold.py` (Stronghold Lifecycle)
- `tests/world/test_aura.py` (Aura of Despair)
- `tests/world/test_calamity_raid.py` (Maturity, Calamity, Raids)

## Files Changed

- `src/core/updates.py`
- `src/engine/apply.py`
- `src/systems/generator.py`
- `src/world/influence.py`
- `src/world/raid.py`
- `src/world/environment.py`
- `src/core/enums.py`
- `src/core/state.py`

## Completion Summary

- Phase 11 is functionally complete and verified with 100% test pass rate.
- Authoritative entity spawning/removal is now a first-class citizen of the engine.
- World dynamics (conquest/threats) are deterministic and replay-ready.
