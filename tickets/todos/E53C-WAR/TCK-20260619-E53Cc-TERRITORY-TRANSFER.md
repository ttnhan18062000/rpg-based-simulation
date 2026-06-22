---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Cc-TERRITORY-TRANSFER
phase: open
date: 2026-06-22
tags: [faction, war, siege, territory-transfer, authoritative-pipeline, integration-test, phase-5]
---

# TCK-20260619-E53Cc-TERRITORY-TRANSFER

## Title
Epic 5.3Cc · Territory Transfer via Authoritative Pipeline + Integration Test

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement the `siege_progress ≥ 1.0` trigger that transfers `RegionState.owner_faction_id` to the attacker faction via `WorldUpdate.owner_faction_id_set`, clears the siege state, and emits a `TERRITORY_TRANSFERRED` `WorldEvent`. Author the integration test `test_war_declared_and_territory_transferred`.

**Requires:** TCK-20260619-E53Cb-SIEGE-MODEL

## Scope

### Territory transfer in MilitaryConflictPhase (`src/engine/military_conflict.py`)

When `RegionState.siege_state` is not `None` and `siege_state.siege_progress >= 1.0`:
1. Emit `WorldUpdate(region_id=..., owner_faction_id_set=<attacker_int_id>, siege_state_clear=True, service_availability_delta=+1.0)` — restores service_availability to 1.0 post-conquest (clamped to 1.0 by apply-path)
2. Disband the `FACTION_SQUAD` `GroupRecord` for both factions in that region (emit `StateUpdate` removing the group)
3. Emit `WorldEvent(category=TERRITORY_TRANSFERRED, subject_id=region_id, payload={"attacker": attacker_faction_id, "defender": defender_faction_id, "tick": current_tick})` into `AuthoritativeState.recent_world_events`
4. `TERRITORY_TRANSFERRED` event flows to `NarrativeLedger` via existing `CampaignOrchestrator._advance_state()` pipeline (significance=0.85)

### FactionState territory list update
- Emit `FactionUpdate` that: removes `region_id` from `defender.territory`, adds `region_id` to `attacker.territory`
- `FactionUpdate.territory_add: List[str]` and `FactionUpdate.territory_remove: List[str]` fields must be added to `src/core/updates.py` if not already present from E53Aa

### NarrativeLedger significance constants
- `TERRITORY_TRANSFERRED`: significance = 0.85
- `SIEGE_STARTED` (optional, low-priority): significance = 0.5

### Integration test: `test_war_declared_and_territory_transferred`

New file: `tests/integration/scenarios/test_faction_campaign.py`

Test setup:
- 3-faction scenario (ALPHA, BETA, GAMMA)
- ALPHA and BETA in `DiplomaticState.WAR`
- BETA owns region "border_region"
- Run simulation for enough ticks that `siege_progress` accumulates to ≥ 1.0 (20 ticks at `+0.05/tick` with no defender reinforcement = 1.0)

Assertions:
- `AuthoritativeState.regions["border_region"].owner_faction_id` equals ALPHA's faction int id after siege completes
- `AuthoritativeState.regions["border_region"].siege_state` is `None` after transfer
- `AuthoritativeState.factions["ALPHA"].territory` contains `"border_region"`
- `AuthoritativeState.factions["BETA"].territory` does NOT contain `"border_region"`
- At least one `TERRITORY_TRANSFERRED` event in `recent_world_events` or `NarrativeLedger`
- Marked `@pytest.mark.slow`

## Out of Scope
- War exhaustion / peace trigger (E53Cd)
- Chronicle naming of the war (E53D)
- Multi-wave sieges (a second siege on the same region after transfer)

## Acceptance Criteria
- `test_war_declared_and_territory_transferred` passes (3-faction scenario, siege completes, region ownership transfers)
- `TERRITORY_TRANSFERRED` `WorldEvent` is emitted with correct `attacker`, `defender`, and `region_id` payload
- `RegionState.siege_state` is `None` after transfer
- `RegionState.service_availability` is restored to 1.0 after transfer
- `FactionState.territory` lists are updated for both attacker and defender
- `NarrativeLedger` contains a `TERRITORY_TRANSFERRED` entry with significance 0.85

## Related Tickets
- TCK-20260619-E53C-WAR (parent epic)
- TCK-20260619-E53Cb-SIEGE-MODEL (required)
- TCK-20260619-E53Cd-WAR-EXHAUSTION (blocked on this)
- TCK-20260619-E53D-HISTORY (blocked on this for full `TERRITORY_TRANSFERRED` chronicle names)

## Related Docs
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md` (Decision 4: WorldUpdate.owner_faction_id_set; no new RegionSovereigntyUpdate type)
- `docs/engine/authoritative_mutation_pipeline_contract.md` (mutation rules and apply-path law)
- `docs/mechanics/regional_sovereignty.md` (update for faction ownership transfer)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` (NarrativeLedger wiring via WorldEvent pipeline)

## Related Code Areas
- `src/engine/military_conflict.py` (territory transfer trigger)
- `src/engine/apply_plan.py:L119` (existing `owner_faction_id_set` handling)
- `src/core/updates.py` (FactionUpdate.territory_add/remove if not yet added)
- `src/domains/campaigns/orchestrator.py` (NarrativeLedger harvesting)
- `tests/integration/scenarios/test_faction_campaign.py` (new)

## Assumptions / Open Questions
- `FactionUpdate.territory_add/remove` may already be added by E53Aa. If not, add them in this ticket.
- The 3-faction scenario fixture must be self-contained (no dependency on a specific world YAML); author it programmatically using `V2EntityBuilder` and `AuthoritativeState` constructors.
- `TERRITORY_TRANSFERRED` must be added to `WorldEventCategory` in `src/domains/world_emergence/schema.py` if not present.

## Implementation Notes
- The `service_availability_delta=+1.0` in the transfer `WorldUpdate` is intentional: combined with the clamping to 1.0 in apply_plan.py, this resets availability regardless of how low it fell during the siege.
- Do not try to "resume" a siege on a region that was just transferred; the clear flag removes `siege_state`, so the next tick `MilitaryConflictPhase` sees no active siege for that region pair.
- Parity ledger: add `WAR-TERR-001` entry in `docs/parity_ledger/substrate.yaml` (or a new `faction_war.yaml`) with status=`verified` once the integration test passes.

## Test Summary
```bash
pytest tests/integration/scenarios/test_faction_campaign.py::test_war_declared_and_territory_transferred -x -v -m slow
pytest tests/unit/faction/test_territory_transfer.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
