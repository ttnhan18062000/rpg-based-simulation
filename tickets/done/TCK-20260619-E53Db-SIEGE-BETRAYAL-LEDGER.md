---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER
phase: done
date: 2026-06-23
tags: [faction, war, siege, betrayal, narrative-ledger, world-event, phase-5]
---

# TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER

## Title
Epic 5.3Db · NarrativeLedger Wiring for SIEGE_BEGINS and BETRAYAL Events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Wire two remaining faction event types into the NarrativeLedger pipeline. E53Bd covers WAR_DECLARED / ALLIANCE_FORMED / PEACE_TREATY; E53Cc covers TERRITORY_TRANSFERRED. Neither covers `SIEGE_BEGINS` (emitted when a siege starts) or `BETRAYAL` (emitted when `BetrayalDirective` executes). This ticket adds WorldEvent emission for both and extends `CampaignOrchestrator._advance_state()` to harvest them.

**Requires:** TCK-20260619-E53Cb-SIEGE-MODEL (SiegeState must exist so siege onset can be detected); TCK-20260619-E53Bc-STATE-MACHINE (BetrayalDirective is handled by DiplomaticActionHandler); TCK-20260619-E53Da-SIGNIFICANCE-NAMING (scorer must register siege_begins and betrayal before they pass CHRONICLE_THRESHOLD)

## Scope

### 1. `SIEGE_BEGINS` WorldEvent emission (`src/engine/military_conflict.py`)

In `MilitaryConflictPhase.execute()`, after a new `SiegeState` is committed to a region (i.e., this is the first tick the siege exists — detect via `prev_siege_state is None and new_siege_state is not None`):

Emit:
```python
WorldEvent(
    category=SIEGE_BEGINS,
    subject_id=region_id,
    payload={
        "attacker_faction_id": siege_state.attacker_faction_id,
        "defender_faction_id": siege_state.defender_faction_id,
        "tick": current_tick,
    }
)
```
Append to `AuthoritativeState.recent_world_events`.

Add constant `SIEGE_BEGINS = "SIEGE_BEGINS"` to `src/domains/world_emergence/schema.py` (or wherever `WorldEventCategory` constants are defined), following the same pattern as `FACTION_WAR_DECLARED` from E53Bd.

### 2. `BETRAYAL` WorldEvent emission (`src/domains/faction/diplomatic_action_handler.py` or equivalent)

In `DiplomaticActionHandler.handle(BetrayalDirective)`, after a BETRAYAL action successfully executes (causing an ALLIED→HOSTILE transition):

Emit:
```python
WorldEvent(
    category=BETRAYAL,
    subject_id=f"{betrayer_faction_id}:{betrayed_faction_id}",
    payload={
        "betrayer_faction_id": betrayer_faction_id,
        "betrayed_faction_id": betrayed_faction_id,
        "tick": current_tick,
    }
)
```
Use alphabetically sorted faction IDs for `subject_id` (consistent with E53Bd's dual-faction dedup convention). Add constant `BETRAYAL = "BETRAYAL"` to the category constants.

**Important:** WorldEvent emission from the faction domain layer must not break the `src/engine/` ↔ `src/domains/campaigns/` boundary. If `DiplomaticActionHandler` lives in `src/domains/faction/`, it can append to `AuthoritativeState.recent_world_events` directly (same mechanism as `WorldEmergencePhase`). If it lives in `src/engine/`, follow the existing pattern. Verify exact file location from E53Bb's implementation before writing code.

### 3. `CampaignOrchestrator._advance_state()` harvesting (`src/domains/campaigns/orchestrator.py`)

Extend the existing world-event → NarrativeLedgerEntry conversion block to handle two new categories:

```python
"SIEGE_BEGINS" → NarrativeLedgerEntry(
    event_type="siege_begins",
    significance=0.80,
    subject_id=payload["defender_faction_id"],  # region_id from WorldEvent.subject_id
    tick=payload["tick"],
    payload={"attacker": payload["attacker_faction_id"], "defender": payload["defender_faction_id"]},
    entry_id=f"{episode}:{tick}:siege_begins:{world_event.subject_id}",
)

"BETRAYAL" → NarrativeLedgerEntry(
    event_type="betrayal",
    significance=0.85,
    subject_id=world_event.subject_id,  # "betrayerID:betrayedID"
    tick=payload["tick"],
    payload={"betrayer": payload["betrayer_faction_id"], "betrayed": payload["betrayed_faction_id"]},
    entry_id=f"{episode}:{tick}:betrayal:{world_event.subject_id}",
)
```

**Clarification on SIEGE_BEGINS subject_id:** The `NarrativeLedgerEntry.subject_id` for `siege_begins` should be the `region_id` (from `WorldEvent.subject_id`), not a faction ID, so that `ChronicleNamer.name_milestone()` can resolve it via `region_names`. Use `subject_id=world_event.subject_id`.

### 4. `NarrativeLedger.query()` — no changes needed

The query-by-event_type pattern works for the new lowercase event types.

## Out of Scope
- Significance scoring and naming template registration (E53Da)
- ChronicleCompiler integration test (E53Dc)
- Doc archive (E53Dd)
- WAR_DECLARED / ALLIANCE_FORMED / PEACE_TREATY / TERRITORY_TRANSFERRED (already covered by E53Bd and E53Cc)

## Acceptance Criteria
- `WorldEvent` with category `"SIEGE_BEGINS"` is present in `AuthoritativeState.recent_world_events` on the first tick a siege is established on a region
- `WorldEvent` with category `"BETRAYAL"` is present in `AuthoritativeState.recent_world_events` after `DiplomaticActionHandler` executes a `BetrayalDirective` on an ALLIED faction pair
- `CampaignOrchestrator._advance_state()` converts `"SIEGE_BEGINS"` into a `NarrativeLedgerEntry` with `event_type="siege_begins"`, `significance=0.80`, `subject_id=region_id`
- `CampaignOrchestrator._advance_state()` converts `"BETRAYAL"` into a `NarrativeLedgerEntry` with `event_type="betrayal"`, `significance=0.85`
- `NarrativeLedger.query(event_type="siege_begins")` returns the correct entry
- `NarrativeLedger.query(event_type="betrayal")` returns the correct entry
- `EventSignificanceScorer.is_chronicle_worthy()` returns True for both (requires E53Da to be done)
- No regressions in existing NarrativeLedger or CampaignOrchestrator tests

## Related Tickets
- TCK-20260619-E53D-HISTORY (parent epic)
- TCK-20260619-E53Cb-SIEGE-MODEL (required — SiegeState model must exist)
- TCK-20260619-E53Bc-STATE-MACHINE (required — BetrayalDirective handling)
- TCK-20260619-E53Da-SIGNIFICANCE-NAMING (required — registers siege_begins and betrayal in scorer before these entries can pass chronicle threshold)
- TCK-20260619-E53Dc-COMPILER-INTEGRATION (blocked on this)

## Related Docs
- `docs/simulation/domains/chronicle_contract.md` (NarrativeLedger pipeline)
- `docs/simulation/domains/cooperation_contract.md` (WorldEvent emission pattern)
- `staging_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` (BetrayalDirective context)
- `staging_artifacts/TCK-20260619-E53C-WAR/investigation.md` (SiegeState onset detection)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`

## Related Code Areas
- `src/domains/world_emergence/schema.py` (add SIEGE_BEGINS, BETRAYAL constants)
- `src/engine/military_conflict.py` (SIEGE_BEGINS emission on first siege tick)
- `src/domains/faction/diplomatic_action_handler.py` (BETRAYAL emission — verify exact path)
- `src/domains/campaigns/orchestrator.py` (_advance_state harvesting)
- `tests/unit/faction/test_siege_ledger.py` (new)
- `tests/unit/faction/test_betrayal_ledger.py` (new, or add to existing test_diplomacy.py)
- `tests/unit/campaigns/` (regression)

## Assumptions / Open Questions
- `DiplomaticActionHandler` file location must be verified from E53Bb's implementation; the exact path affects where WorldEvent is appended (direct state mutation vs return-value pattern).
- Siege onset detection: `MilitaryConflictPhase` must compare previous vs new `RegionState.siege_state` to identify first-tick onset. Check if `AuthoritativeState` provides a `prev_state` snapshot or if the phase must infer onset from the `StateUpdate` it is about to emit (emitting `SiegeState` for the first time = onset).
- If `BETRAYAL` category name conflicts with a legacy enum value, rename to `FACTION_BETRAYAL` and update E53Da templates accordingly.

## Implementation Notes
- `subject_id` for `SIEGE_BEGINS` in `NarrativeLedgerEntry` is the `region_id` (a string like `"border_region"`). The `ChronicleNamer` template `"The Siege of {region_name}"` uses `region_names` dict lookup. Keep payload carrying both faction IDs for downstream use.
- Dedup key format consistent with E53Bd: `"{episode}:{tick}:{event_type}:{subject_id}"`.
- `BETRAYAL` subject_id is `":".join(sorted([betrayer_id, betrayed_id]))` — alphabetical sort for consistent dedup regardless of which faction initiated.
- Do not add `NarrativeLedger` as a direct import to `src/engine/` — all wiring goes through the `WorldEvent` → `CampaignOrchestrator` pipeline.

## Test Summary
```bash
pytest tests/unit/faction/test_siege_ledger.py -x -v
pytest tests/unit/campaigns/ -x -v
pytest tests/unit/faction/test_diplomacy.py -x -v
```

## Files Changed
- `src/domains/world_emergence/schema.py` — added `SIEGE_BEGINS` and `BETRAYAL` to `WorldEventCategory`
- `src/engine/military_conflict.py` — emits `SIEGE_BEGINS` WorldEvent in siege initiation block (`if reg.siege_state is None:`)
- `src/domains/faction/diplomatic_state_machine.py` — added `betrayal_updates` optional param to `events_from_transitions()`; added `Optional` to typing imports; detects ALLIED→HOSTILE to emit `BETRAYAL` WorldEvent
- `src/domains/campaigns/orchestrator.py` — added `"SIEGE_BEGINS"` and `"BETRAYAL"` to `_SIGNIFICANCE_MAP`
- `tests/unit/faction/test_siege_ledger.py` — 6 new tests (new file)
- `tests/unit/faction/test_betrayal_ledger.py` — 8 new tests (new file)
- `docs/parity_ledger/social_narrative.yaml` — added SOC-FAC-007 through SOC-FAC-010

## Completion Summary
SIEGE_BEGINS and BETRAYAL are now full members of the NarrativeLedger pipeline. SIEGE_BEGINS is emitted on the first tick of a siege (subject=region_id for chronicle naming). BETRAYAL is detected by `events_from_transitions(betrayal_updates=[...])` via ALLIED→HOSTILE inspection of prior_factions. The orchestrator's `_SIGNIFICANCE_MAP` and generic `_extract_narrative_entries()` handle both without per-category custom code. 14 new tests, 236 total passing, zero regressions.
