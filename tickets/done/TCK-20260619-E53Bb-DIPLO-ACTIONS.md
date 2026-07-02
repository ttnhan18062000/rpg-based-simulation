---
status: done
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Bb-DIPLO-ACTIONS
phase: done
date: 2026-06-22
tags: [faction, diplomacy, diplomatic-actions, faction-directive, phase-5]
---

# TCK-20260619-E53Bb-DIPLO-ACTIONS

## Title
Epic 5.3Bb · Diplomatic Action Types + Handler

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add diplomatic action dataclasses (`TreatyOffer`, `TradeAgreement`, `NonAggressionPact`, `AllianceProposal`, `Betrayal`) as `FactionDirective` subtypes in `src/engine/faction_decision.py`. Implement `DiplomaticActionHandler` in `src/domains/faction/diplomatic_actions.py` that processes each action type and returns `FactionUpdate` objects encoding the diplomatic relation changes.

**Requires:** TCK-20260619-E53Ba-DIPLO-STATE (DiplomaticState enum must exist); TCK-20260619-E53Ab-DECISION-PHASE (FactionDirective base class must exist)

## Scope

**Diplomatic action types** (in `src/engine/faction_decision.py`, as `FactionDirective` subtypes):
```python
@dataclass(frozen=True, slots=True)
class TreatyOffer(FactionDirective):
    from_faction: str
    to_faction: str
    terms: str            # e.g. "non_aggression" | "trade" | "alliance" | "vassal"
    accepted: bool = False

@dataclass(frozen=True, slots=True)
class TradeAgreement(FactionDirective):
    from_faction: str
    to_faction: str

@dataclass(frozen=True, slots=True)
class NonAggressionPact(FactionDirective):
    from_faction: str
    to_faction: str

@dataclass(frozen=True, slots=True)
class AllianceProposal(FactionDirective):
    from_faction: str
    to_faction: str
    proposer_strength: float   # for VASSAL determination

@dataclass(frozen=True, slots=True)
class Betrayal(FactionDirective):
    from_faction: str
    to_faction: str            # must currently be ALLIED
```

**DiplomaticActionHandler** (new file `src/domains/faction/diplomatic_actions.py`):
- `handle(action: FactionDirective, factions: Dict[str, FactionState]) -> List[FactionUpdate]`
- Pure function — no side effects, no durable mutation. Returns `FactionUpdate` list.
- Action semantics:
  - `TreatyOffer(accepted=True, terms="trade")` → sets both factions' relation toward each other to NEUTRAL (if TENSE) or leaves NEUTRAL/ALLIED unchanged; reduces tension_delta by -0.1
  - `TradeAgreement` → sets relation to NEUTRAL on both sides; reduces tension_delta -0.15
  - `NonAggressionPact` → sets relation to NEUTRAL on both sides; no tension change
  - `AllianceProposal` → sets both sides to ALLIED if `proposer_strength < target_strength * 2.0`, else sets target to VASSAL (proposer stays ALLIED with VASSAL as label for target)
  - `Betrayal` → sets BOTH sides' relation to HOSTILE immediately (from_faction→to_faction and to_faction→from_faction); tension_delta +0.3 for betrayed faction
- Handler must guard: `Betrayal` only valid when current relation is ALLIED; if not ALLIED, return empty list (no-op).

**Module registration**: add `src/domains/faction/__init__.py` if not present.

## Out of Scope
- State machine transition logic from tension levels (E53Bc)
- NarrativeLedger event emission (E53Bd)
- When/whether `FactionDecisionPhase` decides to issue these actions (E53Bc wires that)

## Acceptance Criteria
- All five diplomatic action dataclasses are frozen, slotted, and importable from `src.engine.faction_decision`
- `DiplomaticActionHandler.handle(AllianceProposal(...), factions)` returns two `FactionUpdate` objects setting both factions to ALLIED (or VASSAL for weaker faction when proposer strength ≥ 2x)
- `DiplomaticActionHandler.handle(Betrayal(...), factions)` where current relation is ALLIED returns two `FactionUpdate` objects setting HOSTILE on both sides; when relation is not ALLIED, returns empty list
- `DiplomaticActionHandler.handle(TradeAgreement(...), factions)` returns two `FactionUpdate` objects with NEUTRAL relation and correct tension_delta
- `test_diplomatic_action_alliance_proposal` passes
- `test_diplomatic_action_betrayal_valid` passes
- `test_diplomatic_action_betrayal_invalid_not_allied` passes
- `test_diplomatic_action_trade_agreement` passes
- `test_diplomatic_action_noop_when_noop` passes (TreatyOffer with accepted=False returns empty list)

## Related Tickets
- TCK-20260619-E53B-DIPLOMACY (parent epic)
- TCK-20260619-E53Ba-DIPLO-STATE (required — DiplomaticState enum)
- TCK-20260619-E53Ab-DECISION-PHASE (required — FactionDirective base class)
- TCK-20260619-E53Bc-STATE-MACHINE (depends on this)

## Related Docs
- `docs/engine/authoritative_mutation_pipeline_contract.md` (mutation via typed updates only)
- `staging_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/engine/faction_decision.py` (add diplomatic FactionDirective subtypes)
- `src/domains/faction/diplomatic_actions.py` (new — DiplomaticActionHandler)
- `src/domains/faction/__init__.py` (create if absent)
- `tests/unit/faction/test_diplomacy.py`

## Assumptions / Open Questions
- `FactionDirective` base class (from E53Ab) is a frozen dataclass or Protocol — implementation must be compatible with whatever E53Ab establishes. If it is a frozen dataclass, diplomatic subtypes inherit it; if Protocol, they implement it structurally.
- `TreatyOffer(accepted=False)` is a no-op in the handler (represents an outgoing offer not yet responded to) — the state machine (E53Bc) handles offer initiation; the handler only processes accepted outcomes.
- VASSAL relationship is asymmetric: `from_faction` relation toward `to_faction` = ALLIED (dominant), `to_faction` relation toward `from_faction` = VASSAL (subordinate).

## Implementation Notes
- `DiplomaticActionHandler` must be a pure function module — no class state, no constructor. Use a module-level `handle()` dispatcher or a simple dict-of-callables per action type.
- All returned `FactionUpdate` objects must set only the fields relevant to the action — rely on `FactionUpdate.is_noop()` semantics for unset fields.
- Tests should construct minimal `FactionState` objects (only `faction_id`, `diplomatic_relations`, `tension_level`) without needing full `AuthoritativeState`.

## Test Summary
```bash
pytest tests/unit/faction/test_diplomacy.py::test_diplomatic_action_alliance_proposal -xvs
pytest tests/unit/faction/test_diplomacy.py::test_diplomatic_action_betrayal_valid -xvs
pytest tests/unit/faction/test_diplomacy.py -x -v
```

## Files Changed
- `src/engine/faction_decision.py` — added TreatyOffer, TradeAgreement, NonAggressionPact, AllianceProposal, Betrayal (frozen slotted FactionDirective subtypes)
- `src/domains/faction/__init__.py` — new (module registration)
- `src/domains/faction/diplomatic_actions.py` — new (DiplomaticActionHandler.handle() pure dispatcher)
- `tests/unit/faction/test_diplomacy.py` — 7 new E53Bb tests
- `docs/parity_ledger/faction.yaml` — added FAC-005

## Completion Summary
Five diplomatic action dataclasses added as frozen/slotted FactionDirective subtypes (all new fields carry defaults to satisfy Python slots inheritance ordering). DiplomaticActionHandler in src/domains/faction/diplomatic_actions.py dispatches by type to pure handlers returning FactionUpdate lists. All 15 test_diplomacy.py tests pass.
