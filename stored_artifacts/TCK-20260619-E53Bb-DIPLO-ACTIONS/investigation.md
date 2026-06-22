---
ticket_id: TCK-20260619-E53Bb-DIPLO-ACTIONS
phase: investigate
date: 2026-06-22
---

# Investigation — TCK-20260619-E53Bb-DIPLO-ACTIONS

## What Exists

- `FactionDirective`: frozen dataclass (slots=True) in `src/engine/faction_decision.py`
  - Fields: `faction_id: str`, `directive_kind: str`, `target_faction=None`, `target_region=None`, `priority=1.0`, `created_tick=0`
- `DiplomaticState` enum: in `src/core/enums.py` (added by E53Ba)
- `FactionUpdate`: in `src/core/updates.py`, `diplomatic_relations_set: Dict[str, DiplomaticState]`
- `src/domains/faction/` — DOES NOT EXIST; must create with `__init__.py`

## Inheritance Design

`FactionDirective` is `@dataclass(frozen=True, slots=True)`. Subclasses with NEW fields can
use `@dataclass(frozen=True, slots=True)` and give all new fields defaults (`""`, `False`, `1.0`).
Python 3.13 handles slots inheritance correctly when subclass only adds new fields (no re-declaration
of parent slots). This avoids the "non-default follows default" ordering problem.

Key: subclass fields all have defaults so they come after parent fields in `__init__`.
Callers always pass new fields as keyword args anyway.

## Action Semantics (from ticket)

| Action | Relation set | Tension delta |
|---|---|---|
| `TreatyOffer(accepted=False)` | no-op | — |
| `TreatyOffer(accepted=True, terms="trade")` | both NEUTRAL | -0.1 |
| `TradeAgreement` | both NEUTRAL | -0.15 |
| `NonAggressionPact` | both NEUTRAL | 0 |
| `AllianceProposal(proposer_strength < target*2)` | both ALLIED | 0 |
| `AllianceProposal(proposer_strength >= target*2)` | from→ALLIED(to), to→VASSAL(from) | 0 |
| `Betrayal` (was ALLIED) | both HOSTILE | to +0.3 |
| `Betrayal` (not ALLIED) | no-op | — |

## Guard: Betrayal
- Only valid when current relation is ALLIED; check `factions[from].diplomatic_relations.get(to) == DiplomaticState.ALLIED`
- Return [] if not ALLIED
