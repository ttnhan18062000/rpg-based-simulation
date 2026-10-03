---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53A-FACTION-AGENT
phase: done
date: 2026-06-20
tags: [faction, faction-state, faction-decision-phase, directive-propagation, epic, phase-5]
---

# TCK-20260619-E53A-FACTION-AGENT

## Title
Epic 5.3A · Faction as Agent (child epic — M)

## Status
EPIC_SCOPED

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
- Runs as a sub-phase within existing TickPhase (FROZEN — no new TickPhase entries)
- Reads faction territory, resources, tension
- Produces `FactionDirective(faction_id, directive_kind, target_faction, priority)`

**Entity-level directive propagation**:
- GUARD near contested border: patrol route urgency +2.0
- MERCHANT near allied region: trade route urgency +1.5
- HERO: quest from faction commission: +3.0

**Faction awareness**: observe RESOURCE_DEPLETED events in territory → `tension_level += 0.1`.

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
- TCK-20260619-E53Aa-FACTION-STATE (child — FactionState model + AuthoritativeState field + FactionUpdate)
- TCK-20260619-E53Ab-DECISION-PHASE (child — FactionDecisionPhase + FactionDirective; depends on E53Aa)
- TCK-20260619-E53Ac-DIRECTIVE-PROP (child — directive propagation to entity scoring + faction_contract.md; depends on E53Aa, E53Ab)
- TCK-20260619-E53Ad-TENSION-UPDATE (child — faction awareness / tension update from RESOURCE_DEPLETED events; depends on E53Aa; concurrent with E53Ac)

## Related Docs
- `docs/engine/governance_logic.md` (FactionDecisionPhase insertion point)
- `docs/mechanics/04_strategic_cognition.md` (update with faction directive scoring — E53Ac)
- `docs/systems/faction_contract.md` (new V2 contract — create in E53Ac)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/core/state.py` (add FactionState + AuthoritativeState.factions)
- `src/core/updates.py` (add FactionUpdate, extend StateUpdate)
- `src/engine/faction_decision.py` (new — FactionDirective, FactionDecisionPhase, FactionAwarenessService)
- `src/engine/apply_plan.py` (apply FactionUpdate with tension cap)
- `src/domains/adventure/scoring.py` (add directive propagation)
- `tests/unit/faction/` (new test directory)

## Assumptions / Open Questions
- `TickPhase` enum is FROZEN — FactionDecisionPhase wires as a sub-phase call within an existing phase, NOT a new TickPhase value.
- `FactionDirective` objects are transient per-tick (not persisted in AuthoritativeState).
- String faction IDs (catalog-registered) used in FactionState; existing `Faction(IntEnum)` on entities is a separate numeric tag.

## Implementation Notes
Epic is scoped into 4 sequential/concurrent child tickets:
1. **E53Aa** — FactionState model, AuthoritativeState field, FactionUpdate typed mutation record, apply path
2. **E53Ab** — FactionDecisionPhase, FactionDirective, engine wiring (depends on E53Aa)
3. **E53Ac** — Directive propagation to AdventureRouteScorer, faction_contract.md creation (depends on E53Aa + E53Ab)
4. **E53Ad** — FactionAwarenessService for tension update from RESOURCE_DEPLETED events (depends on E53Aa; concurrent with E53Ac)

## Test Summary
```bash
pytest tests/unit/faction/ -x -v
```

## Files Changed
_Epic scoping only — no code changes._

## Completion Summary
Scoped into 4 child standard tickets: TCK-20260619-E53Aa-FACTION-STATE, TCK-20260619-E53Ab-DECISION-PHASE, TCK-20260619-E53Ac-DIRECTIVE-PROP, TCK-20260619-E53Ad-TENSION-UPDATE. Investigation artifacts stored in stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/.
