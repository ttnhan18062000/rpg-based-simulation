---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Bc-STATE-MACHINE
phase: open
date: 2026-06-22
tags: [faction, diplomacy, state-machine, transitions, governance, phase-5]
---

# TCK-20260619-E53Bc-STATE-MACHINE

## Title
Epic 5.3Bc · Diplomatic State Machine Transitions + FactionDecisionPhase Integration

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `DiplomaticStateMachine` in `src/domains/faction/diplomatic_state_machine.py` — a pure function module that reads `FactionState` pairs and tension levels, computes required `DiplomaticState` transitions, and returns `FactionUpdate` objects. Wire the state machine into `FactionDecisionPhase` (E53Ab) so it runs each tick at `TickPhase.INIT`, producing diplomatic `FactionUpdate` objects that flow through the authoritative apply path. Also wire `FactionDecisionPhase` to generate diplomatic action directives (`AllianceProposal`, war-intent `TreatyOffer`) based on faction state.

**Requires:** TCK-20260619-E53Bb-DIPLO-ACTIONS (action types + handler); TCK-20260619-E53Ab-DECISION-PHASE (FactionDecisionPhase must exist); TCK-20260619-E53Ad-TENSION-UPDATE (tension_level must be populated by awareness service)

## Scope

**DiplomaticStateMachine** (new file `src/domains/faction/diplomatic_state_machine.py`):
```python
def compute_transitions(
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    """
    For each ordered pair (a, b) of faction IDs, evaluate current
    DiplomaticState and tension/military thresholds and return
    FactionUpdate objects for any required transitions.
    Pairs are evaluated once (a < b lexicographically) to avoid duplicate updates.
    """
```

**Transition rules** (pure logic, no side effects):
| From | To | Condition |
|---|---|---|
| NEUTRAL | TENSE | `tension_level(a→b) > 0.4` |
| TENSE | HOSTILE | `tension_level(a→b) > 0.7` OR both factions share a territory region_id |
| HOSTILE | WAR | `military_strength(aggressor) > military_strength(defender) * 1.2` — aggressor is the faction with higher military_strength |
| WAR | NEUTRAL | both `military_strength(a) < 0.3` AND `military_strength(b) < 0.3` (exhaustion) |
| Any | ALLIED | only via `AllianceProposal` action (handled by DiplomaticActionHandler — NOT by state machine) |

- Transitions are one-step per tick (no skipping states in a single tick).
- VASSAL and ALLIED states are terminal until a `Betrayal` action (also not in state machine).
- Shared territory check: `bool(set(faction_a.territory) & set(faction_b.territory))`.
- `tension_level` used is from `FactionState.tension_level` (per-faction global; not per-pair — use the max of the two involved factions' tension as a proxy for the pair tension until E53Ad adds per-pair tension).

**FactionDecisionPhase integration** (in `src/engine/faction_decision.py`):
- After running `FactionAwarenessService` (E53Ad), call `DiplomaticStateMachine.compute_transitions(factions)`.
- Collect returned `FactionUpdate` objects and add to the tick's `StateUpdate.faction_updates`.
- Also generate `AllianceProposal` directives: if two factions are both HOSTILE toward a third (common enemy), propose an alliance between them via `AllianceProposal` directive processed by `DiplomaticActionHandler`.
- These directives are consumed within the same sub-phase (not queued for next tick).

**War exhaustion** — military_strength depletion:
- Out of scope for this ticket. Military_strength depletion from combat is an E53C concern. This ticket only reads `military_strength` for WAR→NEUTRAL detection; it does not write it.

## Out of Scope
- Military_strength mutation from combat (E53C)
- NarrativeLedger event emission for WAR_DECLARED / PEACE_TREATY (E53Bd — but this ticket must emit WorldEvents so E53Bd can harvest them)
- VASSAL/ALLIED terminal state management (E53Bb covers Betrayal exit)

## Acceptance Criteria
- `DiplomaticStateMachine.compute_transitions(factions)` returns an empty list when no thresholds are met
- NEUTRAL→TENSE transition fires for a pair when `tension_level > 0.4` on either faction
- TENSE→HOSTILE transition fires when `tension_level > 0.7`
- TENSE→HOSTILE fires when both factions share a territory region_id even at tension 0.5
- HOSTILE→WAR fires when aggressor `military_strength > defender * 1.2`
- WAR→NEUTRAL fires when both factions' `military_strength < 0.3`
- Transitions are single-step per call (NEUTRAL does not jump to HOSTILE in one call even if tension=0.9)
- `test_diplomatic_state_transitions_valid` passes (AC from parent epic)
- `test_alliance_reduces_shared_territory_threat` passes (AC from parent epic — ALLIED state suppresses TENSE→HOSTILE on shared territory)
- `FactionDecisionPhase` integration: after calling compute_transitions, returned `FactionUpdate` objects appear in `StateUpdate.faction_updates`

## Related Tickets
- TCK-20260619-E53B-DIPLOMACY (parent epic)
- TCK-20260619-E53Bb-DIPLO-ACTIONS (required — action types + handler for alliance generation)
- TCK-20260619-E53Ab-DECISION-PHASE (required — FactionDecisionPhase)
- TCK-20260619-E53Ad-TENSION-UPDATE (required — tension_level populated)
- TCK-20260619-E53Bd-LEDGER-WIRING (depends on this — harvests WorldEvents emitted here)
- TCK-20260619-E53C-WAR (depends on this — military_strength depletion integrates with WAR state)

## Related Docs
- `docs/engine/kernel.md` (6-phase deterministic loop — TickPhase.INIT is where FactionDecisionPhase runs)
- `docs/mechanics/04_strategic_cognition.md` (goal hierarchy, interruption logic)
- `staging_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/domains/faction/diplomatic_state_machine.py` (new)
- `src/engine/faction_decision.py` (wire state machine + alliance generation)
- `src/core/updates.py` (StateUpdate.faction_updates — already planned in E53Aa)
- `tests/unit/faction/test_diplomacy.py`

## Assumptions / Open Questions
- `tension_level` in E53Ba is a per-faction scalar, not per-pair. Using `max(a.tension_level, b.tension_level)` as the pair proxy is an acceptable simplification for this tier; per-pair tension can be added in a future ticket if needed.
- ALLIED and VASSAL states suppress tension-driven transitions — the machine must guard: if current state is ALLIED or VASSAL, skip threshold checks for that pair entirely.
- The "common enemy" heuristic for `AllianceProposal` generation: factions A and B both have relation HOSTILE or WAR toward faction C → generate one `AllianceProposal(from_faction=A, to_faction=B)` per common enemy. Limit to one proposal per pair per tick to avoid flooding.

## Implementation Notes
- Iterate faction pairs in deterministic lexicographic order (`sorted(factions.keys())`). For each pair (a, b), check the current state from `factions[a].diplomatic_relations.get(b_id, DiplomaticState.NEUTRAL)`.
- Single-step enforcement: apply at most one transition per pair per `compute_transitions` call. Return the first applicable transition found (in priority order: WAR→NEUTRAL > HOSTILE→WAR > TENSE→HOSTILE > NEUTRAL→TENSE).
- The returned `FactionUpdate` for a transition must set `diplomatic_relations_set` for BOTH factions (bidirectional — both sides of the pair get the update).
- `DiplomaticStateMachine` must not import from `src.engine` — keep in `src/domains/faction/` to avoid circular dependencies.

## Test Summary
```bash
pytest tests/unit/faction/test_diplomacy.py::test_diplomatic_state_transitions_valid -xvs
pytest tests/unit/faction/test_diplomacy.py::test_alliance_reduces_shared_territory_threat -xvs
pytest tests/unit/faction/test_diplomacy.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
