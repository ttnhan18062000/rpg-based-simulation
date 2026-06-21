---
status: done
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53B-DIPLOMACY
phase: done
date: 2026-06-20
tags: [faction, diplomacy, diplomatic-state, treaty, alliance, epic, phase-5]
---

# TCK-20260619-E53B-DIPLOMACY

## Title
Epic 5.3B · Faction Diplomacy (child epic — M)

## Status
EPIC_SCOPED

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

## Out of Scope
- Territorial conflict and war mechanics (E53C)
- Chronicle Compiler naming of wars/alliances (E53D)
- Player faction control

## Acceptance Criteria
- `test_diplomatic_state_transitions_valid` passes
- `test_alliance_reduces_shared_territory_threat` passes
- `test_treaty_flows_through_narrative_ledger` passes

## Related Tickets
- TCK-20260619-E53-FACTION-DIPLOMACY (parent epic)
- TCK-20260619-E53A-FACTION-AGENT (required)
- TCK-20260619-E53C-WAR (blocked on this)
- **TCK-20260619-E53Ba-DIPLO-STATE** (child — DiplomaticState enum + FactionState migration)
- **TCK-20260619-E53Bb-DIPLO-ACTIONS** (child — diplomatic action types + handler)
- **TCK-20260619-E53Bc-STATE-MACHINE** (child — state machine transitions + FactionDecisionPhase integration)
- **TCK-20260619-E53Bd-LEDGER-WIRING** (child — NarrativeLedger wiring for diplomatic events)

## Related Docs
- `docs/plans/long_term_development_roadmap.md` (Epic 5.3 Phase B)
- `docs/systems/grand_strategy.md` (legacy context only — do NOT port)
- `staging_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` → `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`

## Related Code Areas
- `src/core/enums.py` (DiplomaticState — E53Ba)
- `src/core/state.py` (FactionState.diplomatic_relations — E53Ba)
- `src/core/updates.py` (FactionUpdate.diplomatic_relations_set — E53Ba)
- `src/engine/faction_decision.py` (diplomatic FactionDirective subtypes + state machine wiring — E53Bb/E53Bc)
- `src/domains/faction/diplomatic_actions.py` (DiplomaticActionHandler — E53Bb)
- `src/domains/faction/diplomatic_state_machine.py` (DiplomaticStateMachine — E53Bc)
- `src/domains/world_emergence/schema.py` (FACTION_* WorldEvent categories — E53Bd)
- `src/domains/campaigns/orchestrator.py` (NarrativeLedger harvesting — E53Bd)

## Assumptions / Open Questions
- Child tickets must be implemented in strict dependency order: E53Ba → E53Bb → E53Bc → E53Bd.
- E53Ba cannot start until E53Aa (FactionState model) is complete.
- The `FactionDecisionPhase` (E53Ab) must exist before E53Bc can wire into it.
- The `FactionAwarenessService` (E53Ad) must populate `tension_level` before E53Bc transition thresholds are meaningful.

## Implementation Notes
- All four child tickets add to `tests/unit/faction/test_diplomacy.py` (single cohesive test module).
- `DiplomaticStateMachine` lives in `src/domains/faction/` — not in `src/engine/` — to avoid circular imports.
- Diplomatic events flow through `WorldEvent` → `CampaignOrchestrator` pipeline, not via direct `NarrativeLedger` injection from engine code.

## Test Summary
```bash
pytest tests/unit/faction/test_diplomacy.py -x -v
pytest tests/unit/campaigns/ -x -v
```

## Files Changed
- `tickets/todos/TCK-20260619-E53Ba-DIPLO-STATE.md` (created)
- `tickets/todos/TCK-20260619-E53Bb-DIPLO-ACTIONS.md` (created)
- `tickets/todos/TCK-20260619-E53Bc-STATE-MACHINE.md` (created)
- `tickets/todos/TCK-20260619-E53Bd-LEDGER-WIRING.md` (created)
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` (created)

## Completion Summary
Epic scoped into 4 child standard tickets: E53Ba (DiplomaticState enum + FactionState.diplomatic_relations migration), E53Bb (diplomatic action FactionDirective subtypes + DiplomaticActionHandler), E53Bc (DiplomaticStateMachine + FactionDecisionPhase integration), E53Bd (WorldEvent emission + CampaignOrchestrator NarrativeLedger harvesting). Key decisions: DiplomaticState placed in src/core/enums.py; state machine is pure function in src/domains/faction/ to avoid circular imports; NarrativeLedger wiring goes through existing WorldEvent pipeline, not direct engine→campaign injection; all four tickets share tests/unit/faction/test_diplomacy.py. Linear dependency order enforced: Ba→Bb→Bc→Bd; each blocked by E53Aa (FactionState) and E53Ab (FactionDecisionPhase).
