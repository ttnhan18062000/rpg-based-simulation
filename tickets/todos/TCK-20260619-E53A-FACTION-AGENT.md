---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53A-FACTION-AGENT
phase: open
date: 2026-06-20
tags: [faction, faction-state, faction-decision-phase, directive-propagation, epic, phase-5]
---

# TCK-20260619-E53A-FACTION-AGENT

## Title
Epic 5.3A · Faction as Agent (child epic — M)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Zero engine code exists for faction behavior. This child epic implements `FactionState` as a V2 typed durable model and `FactionDecisionPhase` at the governance layer. Build fresh against V2 architecture — do NOT port from `docs/systems/grand_strategy.md`.

**Blocks:** TCK-20260619-E53B-DIPLOMACY, TCK-20260619-E53C-WAR, TCK-20260619-E53D-HISTORY

## Scope

**FactionState** durable model (new in `src/core/state.py`):
```python
@dataclass(frozen=True, slots=True)
class FactionState:
    faction_id: str
    territory: Tuple[str, ...] = ()          # region_ids controlled
    resources: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict)
    active_doctrines: Tuple[str, ...] = ()
    military_strength: float = 1.0
    tension_level: float = 0.0
```

Add to `AuthoritativeState`:
```python
factions: Dict[str, FactionState] = field(default_factory=dict)
```

**FactionDecisionPhase** (new in `src/engine/faction_decision.py`):
- Registered in `GovernorPolicy` (check insertion pattern before implementing)
- Reads faction territory, resources, tension
- Produces `FactionDirective(faction_id, directive_kind, target_faction, priority)`

**Entity-level directive propagation**:
- GUARD near contested border: patrol route urgency +2.0
- MERCHANT near allied region: trade route urgency +1.5
- HERO: quest from faction commission: +3.0

**Faction awareness**: observe RESOURCE_DEPLETED events in territory → `tension_level += 0.1`.

Scope child standard tickets at implementation time (suggest: (i) FactionState model + AuthoritativeState field, (ii) FactionDecisionPhase + GovernorPolicy registration, (iii) directive propagation to entity scoring, (iv) faction awareness/tension update).

## Out of Scope
- Diplomatic actions (E53B)
- War/siege mechanics (E53C)
- grand_strategy.md porting

## Acceptance Criteria
- `test_faction_decision_phase_produces_directive` passes
- `test_faction_tension_increases_on_resource_depletion` passes
- `FactionState` persists and serializes in `AuthoritativeState`

## Related Tickets
- TCK-20260619-E53-FACTION-DIPLOMACY (parent epic)
- TCK-20260619-E53B-DIPLOMACY (blocked on this)

## Related Docs
- `docs/engine/governance_logic.md` (FactionDecisionPhase insertion point)
- `docs/mechanics/04_strategic_cognition.md` (update with faction directive scoring)
- `docs/systems/faction_contract.md` (new V2 contract — create after A complete)

## Related Code Areas
- `src/core/state.py` (add FactionState + AuthoritativeState.factions)
- `src/engine/policy.py:L10` (GovernorPolicy — faction phase insertion)
- `src/content_semantics/faction.py` (catalog data — faction IDs only)
- `src/domains/adventure/scoring.py` (add directive propagation)

## Test Summary
```bash
pytest tests/unit/faction/test_faction_state.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
