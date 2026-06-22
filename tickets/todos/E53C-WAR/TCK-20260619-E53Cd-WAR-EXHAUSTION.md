---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Cd-WAR-EXHAUSTION
phase: open
date: 2026-06-22
tags: [faction, war, exhaustion, peace-trigger, diplomatic-state-machine, phase-5]
---

# TCK-20260619-E53Cd-WAR-EXHAUSTION

## Title
Epic 5.3Cd · War Exhaustion + Peace Triggers

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement per-tick `military_strength` drain for factions at war and the peace trigger that fires when `military_strength < 0.3`, transitioning `DiplomaticState.WAR → NEUTRAL` via the existing `DiplomaticStateMachine`. Adds the `test_war_exhaustion_ends_conflict` acceptance test.

**Requires:** TCK-20260619-E53Cc-TERRITORY-TRANSFER (E53Cb's siege model and E53Bc's DiplomaticStateMachine must both be present)

## Scope

### War exhaustion drain in MilitaryConflictPhase (`src/engine/military_conflict.py`)

Each tick, for every faction whose `DiplomaticState` is `WAR` with at least one other faction:
- Emit `FactionUpdate(faction_id=..., military_strength_delta=-0.001)`
- Both attacker and defender drain simultaneously — incentivizes peace when both sides are exhausted

### Peace trigger

When `MilitaryConflictPhase` observes that a faction's `military_strength < 0.3` (after applying this tick's drain via state inspection — read current tick's `FactionState` before any delta, apply floor check):
1. Emit a transient `FactionDirective(kind="SEEK_PEACE", source_faction_id=..., target_faction_id=...)` for each WAR pair involving the exhausted faction
2. The `DiplomaticStateMachine` (already wired into `FactionDecisionPhase`) processes `SEEK_PEACE` directives and transitions `WAR → NEUTRAL` if both sides accept OR if either side's `military_strength < 0.3`
3. Emit `WorldEvent(category=WAR_ENDED_EXHAUSTION, subject_id=faction_id, payload={"faction_pair": [f1, f2], "tick": tick})` with significance=0.8
4. `WAR_ENDED_EXHAUSTION` flows to `NarrativeLedger` via existing `CampaignOrchestrator._advance_state()` pipeline

### DiplomaticStateMachine extension (`src/domains/faction/diplomatic_state_machine.py`)

The existing `WAR → NEUTRAL` transition rule (from E53Bc: fires when `military_strength < 0.3` on both sides) must be extended or confirmed to handle the `SEEK_PEACE` directive input:
- If directive `kind="SEEK_PEACE"` arrives AND `military_strength < 0.3` on the issuing faction → transition fires
- If `military_strength < 0.3` on BOTH factions → transition fires without explicit directive (autonomous)
- Update the state machine to emit `WorldEvent(PEACE_TREATY)` when WAR→NEUTRAL transition fires (if not already done in E53Bd)

### WorldEventCategory additions
- `WAR_ENDED_EXHAUSTION` — if not already present, add to `WorldEventCategory` in `src/domains/world_emergence/schema.py`

### NarrativeLedger significance constants
- `WAR_ENDED_EXHAUSTION`: significance = 0.8
- `PEACE_TREATY` (E53Bd): significance = 0.75 (confirm this is wired)

### Unit test: `test_war_exhaustion_ends_conflict`

Location: `tests/integration/scenarios/test_faction_campaign.py` (append to existing file) or `tests/unit/faction/test_war_exhaustion.py`

Test setup:
- 2-faction scenario (ALPHA, BETA) in `DiplomaticState.WAR`
- ALPHA.military_strength = 0.31 (one drain tick will push below 0.3)
- BETA.military_strength = 0.31 (same)
- Run 2 ticks

Assertions:
- After tick 1: both factions' `military_strength` = 0.309
- After tick 2: both factions' `military_strength` = 0.308; SEEK_PEACE directive emitted
- `DiplomaticStateMachine` transitions WAR → NEUTRAL for the ALPHA–BETA pair
- `AuthoritativeState.factions["ALPHA"].diplomatic_relations["BETA"]` == `DiplomaticState.NEUTRAL`
- `WAR_ENDED_EXHAUSTION` WorldEvent is present in `recent_world_events`
- No active siege remains (if a `SiegeState` was present, it is cleared when war ends)

## Out of Scope
- Chronicle naming of the concluded war (E53D)
- Reparations / post-war treaty terms
- Re-escalation logic (WAR again after NEUTRAL) — handled by existing DiplomaticStateMachine tension thresholds from E53Bc

## Acceptance Criteria
- `FactionState.military_strength` drains by 0.001 per tick for every faction in a WAR state
- When `military_strength < 0.3`, a `SEEK_PEACE` directive is produced and the state machine fires WAR→NEUTRAL
- `test_war_exhaustion_ends_conflict` passes (unit or integration, deterministic)
- `WAR_ENDED_EXHAUSTION` WorldEvent is emitted with correct payload
- `NarrativeLedger` contains a `WAR_ENDED_EXHAUSTION` or `PEACE_TREATY` entry after conflict resolution
- Active `SiegeState` on any contested region is cleared when the associated WAR pair returns to NEUTRAL

## Related Tickets
- TCK-20260619-E53C-WAR (parent epic)
- TCK-20260619-E53Cc-TERRITORY-TRANSFER (required)
- TCK-20260619-E53Bc-STATE-MACHINE (required — DiplomaticStateMachine WAR→NEUTRAL transition)
- TCK-20260619-E53D-HISTORY (blocked on this — chronicle can now name ended wars)

## Related Docs
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md` (Decision 6: war exhaustion via FactionUpdate.military_strength_delta; SEEK_PEACE directive delegates to DiplomaticStateMachine)
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` (Decision 6: WAR→NEUTRAL transition rule when military_strength < 0.3)
- `docs/mechanics/04_strategic_cognition.md` (goal hierarchy — peace incentive)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`

## Related Code Areas
- `src/engine/military_conflict.py` (add exhaustion drain + SEEK_PEACE directive emission)
- `src/domains/faction/diplomatic_state_machine.py` (extend/confirm SEEK_PEACE handling)
- `src/domains/world_emergence/schema.py` (WAR_ENDED_EXHAUSTION category)
- `src/domains/campaigns/orchestrator.py` (NarrativeLedger harvest for WAR_ENDED_EXHAUSTION)
- `tests/integration/scenarios/test_faction_campaign.py` (append test_war_exhaustion_ends_conflict)

## Assumptions / Open Questions
- E53Bc's `DiplomaticStateMachine` implements `WAR → NEUTRAL` when `military_strength < 0.3` on both sides. If E53Bc only implemented the autonomous check and not the `SEEK_PEACE` directive path, this ticket must extend it.
- If only ONE faction falls below 0.3, does peace trigger? Per roadmap: "both sides incentivized to end long wars." Interpretation: either side below 0.3 can propose SEEK_PEACE; both sides below 0.3 causes autonomous transition. Document the chosen rule in this ticket's Implementation Notes.
- Siege state cleanup on WAR→NEUTRAL: when the `DiplomaticStateMachine` fires WAR→NEUTRAL, it should emit a `WorldUpdate` to clear `siege_state` on any region where the pair was fighting. This may need to be handled in `MilitaryConflictPhase` by detecting the transition, not inside the state machine (to keep domain separation clean).

## Implementation Notes
- `military_strength_delta` is applied via the existing `FactionUpdate` apply-path established in E53Aa. Do not mutate `FactionState.military_strength` directly.
- The drain is unconditional — a faction at war drains even if no active siege exists in their territory. This is the "war exhaustion" concept: sustained war readiness is costly regardless of active combat.
- Parity ledger: add `WAR-EXHAUST-001` in the faction war parity file with status=`verified` once both acceptance tests pass.

## Test Summary
```bash
pytest tests/integration/scenarios/test_faction_campaign.py::test_war_exhaustion_ends_conflict -x -v
pytest tests/unit/faction/test_war_exhaustion.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
