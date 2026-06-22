---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Bd-LEDGER-WIRING
phase: open
date: 2026-06-22
tags: [faction, diplomacy, narrative-ledger, world-event, campaign, phase-5]
---

# TCK-20260619-E53Bd-LEDGER-WIRING

## Title
Epic 5.3Bd · NarrativeLedger Wiring for Diplomatic Events

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Wire diplomatic state transitions into the `NarrativeLedger` pipeline. When `DiplomaticStateMachine` or `DiplomaticActionHandler` detects ALLIANCE_FORMED, WAR_DECLARED, or PEACE_TREATY transitions, emit typed `WorldEvent` objects into `AuthoritativeState.recent_world_events`. Update `CampaignOrchestrator._advance_state()` to harvest these event types and create `NarrativeLedgerEntry` records with the correct significance values (ALLIANCE_FORMED=0.8, WAR_DECLARED=0.95, PEACE_TREATY=0.75).

**Requires:** TCK-20260619-E53Bc-STATE-MACHINE (state machine must emit WorldEvents); TCK-20260619-E32D-NARRATIVE-LEDGER (NarrativeLedger must exist — already DONE)

## Scope

**WorldEvent emission** (in `src/engine/faction_decision.py`, called from `FactionDecisionPhase`):
- After `DiplomaticStateMachine.compute_transitions()` produces a transition to WAR: emit `WorldEvent(category="FACTION_WAR_DECLARED", payload={"from_faction": ..., "to_faction": ..., "tick": tick})`
- After `DiplomaticActionHandler.handle(AllianceProposal(...))` returns ALLIED updates: emit `WorldEvent(category="FACTION_ALLIANCE_FORMED", payload={"faction_a": ..., "faction_b": ..., "tick": tick})`
- After WAR→NEUTRAL transition: emit `WorldEvent(category="FACTION_PEACE_TREATY", payload={"faction_a": ..., "faction_b": ..., "tick": tick})`
- All three `WorldEvent` objects are appended to `AuthoritativeState.recent_world_events` (same as existing calamity/ecology events).

**WorldEvent category constants**: add three constants to `src/domains/world_emergence/schema.py` (or wherever `WorldEventCategory` is defined):
```python
FACTION_WAR_DECLARED = "FACTION_WAR_DECLARED"
FACTION_ALLIANCE_FORMED = "FACTION_ALLIANCE_FORMED"
FACTION_PEACE_TREATY = "FACTION_PEACE_TREATY"
```

**CampaignOrchestrator harvesting** (in `src/domains/campaigns/orchestrator.py`, method `_advance_state()`):
- Extend the existing world-event → NarrativeLedgerEntry conversion block to handle:
  - `"FACTION_WAR_DECLARED"` → `NarrativeLedgerEntry(event_type="war_declared", significance=0.95, subject_id=f"{payload['from_faction']}:{payload['to_faction']}", ...)`
  - `"FACTION_ALLIANCE_FORMED"` → `NarrativeLedgerEntry(event_type="alliance_formed", significance=0.8, subject_id=f"{payload['faction_a']}:{payload['faction_b']}", ...)`
  - `"FACTION_PEACE_TREATY"` → `NarrativeLedgerEntry(event_type="peace_treaty", significance=0.75, subject_id=f"{payload['faction_a']}:{payload['faction_b']}", ...)`
- `entry_id` format: `"{episode}:{tick}:{event_type}:{subject_id}"` — consistent with existing ledger dedup key format.

**NarrativeLedger.query()** — no changes needed; the new event types are plain strings and the existing query-by-event_type pattern works immediately.

## Out of Scope
- Chronicle Compiler naming of wars/alliances (E53D — depends on this ticket)
- Changing `NarrativeLedger` or `NarrativeLedgerEntry` model structure
- Altering `CampaignState` serialization

## Acceptance Criteria
- `WorldEvent` with category `"FACTION_WAR_DECLARED"` is present in `AuthoritativeState.recent_world_events` after `FactionDecisionPhase` produces a HOSTILE→WAR transition
- `CampaignOrchestrator._advance_state()` converts `FACTION_WAR_DECLARED` into a `NarrativeLedgerEntry` with `event_type="war_declared"` and `significance=0.95`
- `CampaignOrchestrator._advance_state()` converts `FACTION_ALLIANCE_FORMED` into a `NarrativeLedgerEntry` with `event_type="alliance_formed"` and `significance=0.8`
- `CampaignOrchestrator._advance_state()` converts `FACTION_PEACE_TREATY` into a `NarrativeLedgerEntry` with `event_type="peace_treaty"` and `significance=0.75`
- `NarrativeLedger.query(event_type="war_declared")` returns the correct entry after the above
- `test_treaty_flows_through_narrative_ledger` passes (AC from parent epic)
- No regressions in existing `NarrativeLedger` or `CampaignOrchestrator` tests

## Related Tickets
- TCK-20260619-E53B-DIPLOMACY (parent epic)
- TCK-20260619-E53Bc-STATE-MACHINE (required — state machine emits WorldEvents)
- TCK-20260619-E53D-HISTORY (depends on this — Chronicle Compiler consumes ledger entries)

## Related Docs
- `docs/simulation/domains/cooperation_contract.md` (pattern for domain event emission)
- `staging_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E32D-NARRATIVE-LEDGER/` (if exists)
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/domains/world_emergence/schema.py` (add FACTION_* WorldEvent category constants)
- `src/engine/faction_decision.py` (emit WorldEvent on transitions)
- `src/domains/campaigns/orchestrator.py` (_advance_state — harvest diplomatic WorldEvents)
- `src/domains/campaigns/state.py` (NarrativeLedgerEntry — read-only reference; no changes)
- `tests/unit/faction/test_diplomacy.py`
- `tests/unit/campaigns/` (existing orchestrator tests — regression check)

## Assumptions / Open Questions
- `AuthoritativeState.recent_world_events` already exists and is cleared each tick by the apply path (confirmed by existing world_emergence/calamity usage). No structural change needed.
- `WorldEvent` in `src/domains/world_emergence/schema.py` already has a `category` field and `payload: dict` — verify field names match before implementing.
- The `CampaignOrchestrator` harvesting block may use a dict dispatch or if/elif chain; follow whichever pattern already exists in `_advance_state()`.
- Duplicate suppression: `entry_id` dedup key prevents double-recording if `_advance_state()` is called multiple times for the same tick (edge case in replay scenarios).

## Implementation Notes
- Do not add `NarrativeLedger` as a direct import to `src/engine/` — all wiring goes through the `WorldEvent` → `CampaignOrchestrator` pipeline to respect the `src/engine/` ↔ `src/domains/campaigns/` boundary.
- `subject_id` for dual-faction events uses `"factionA:factionB"` with alphabetically sorted faction IDs (`":".join(sorted([a, b]))`) to ensure consistent dedup keys regardless of which faction is listed first.
- If `WorldEventCategory` is an enum rather than plain string constants, add the three new members to that enum and use the enum values in both emission and harvesting.

## Test Summary
```bash
pytest tests/unit/faction/test_diplomacy.py::test_treaty_flows_through_narrative_ledger -xvs
pytest tests/unit/campaigns/ -x -v
pytest tests/unit/faction/test_diplomacy.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
