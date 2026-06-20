---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53B-DIPLOMACY
phase: open
date: 2026-06-20
tags: [faction, diplomacy, diplomatic-state, treaty, alliance, epic, phase-5]
---

# TCK-20260619-E53B-DIPLOMACY

## Title
Epic 5.3B · Faction Diplomacy (child epic — M)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Implements the diplomatic state machine and diplomatic actions between factions.

**Requires:** TCK-20260619-E53A-FACTION-AGENT

## Scope

**DiplomaticState** enum:
```python
class DiplomaticState(str, Enum):
    NEUTRAL = "NEUTRAL"
    TENSE = "TENSE"
    HOSTILE = "HOSTILE"
    WAR = "WAR"
    ALLIED = "ALLIED"
    VASSAL = "VASSAL"
```

**Transition rules** (driven by `FactionDecisionPhase`):
- NEUTRAL→TENSE: `tension_level > 0.4`
- TENSE→HOSTILE: `tension_level > 0.7` OR resource conflict in shared territory
- HOSTILE→WAR: `FactionDecisionPhase` chooses war when `military_strength > opponent.military_strength * 1.2`
- WAR→NEUTRAL: `war_exhaustion` depletes `military_strength` below 0.3 (both sides)
- Any→ALLIED: via `AllianceProposal` acceptance

**Diplomatic actions** (as `FactionDirective` subtypes):
- `TreatyOffer(from_faction, to_faction, terms)`, `TradeAgreement`, `NonAggressionPact`, `AllianceProposal`, `Betrayal`

All diplomatic events → `NarrativeLedger`:
- `ALLIANCE_FORMED` (significance=0.8), `WAR_DECLARED` (significance=0.95), `PEACE_TREATY` (significance=0.75)

Scope child standard tickets at implementation time (suggest: (i) DiplomaticState enum + FactionState.diplomatic_relations migration, (ii) diplomatic action handlers, (iii) state machine transitions + governance integration, (iv) NarrativeLedger wiring).

## Acceptance Criteria
- `test_diplomatic_state_transitions_valid` passes
- `test_alliance_reduces_shared_territory_threat` passes
- `test_treaty_flows_through_narrative_ledger` passes

## Related Tickets
- TCK-20260619-E53-FACTION-DIPLOMACY (parent epic)
- TCK-20260619-E53A-FACTION-AGENT (required)
- TCK-20260619-E53C-WAR (blocked on this)

## Related Code Areas
- `src/engine/faction_decision.py` (FactionDecisionPhase — add diplomatic action generation)
- `src/domains/campaigns/state.py` (NarrativeLedger — wire diplomatic events)

## Test Summary
```bash
pytest tests/unit/faction/test_diplomacy.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
