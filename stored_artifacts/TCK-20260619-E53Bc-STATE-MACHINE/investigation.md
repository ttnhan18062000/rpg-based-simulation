---
ticket_id: TCK-20260619-E53Bc-STATE-MACHINE
phase: investigate
date: 2026-06-22
---

# Investigation — TCK-20260619-E53Bc-STATE-MACHINE

## Architecture Decision

Ticket says "DiplomaticStateMachine must not import from src.engine". This means:
- `compute_transitions()` stays pure: DiplomaticState, FactionUpdate, FactionState only
- Alliance generation helper `compute_common_enemy_pairs()` also stays clean (no engine imports)
- AllianceProposal construction + DiplomaticActionHandler.handle() called in pipeline.py

`FactionDecisionPhase.execute()` return type is NOT changed — alliance generation is wired
in pipeline.py Phase 8d block directly, keeping existing anti-drift guard tests intact.

## Transition Rules

| From | To | Condition | Priority |
|---|---|---|---|
| WAR | NEUTRAL | both military_strength < 0.3 | 1st |
| HOSTILE | WAR | max(a.ms, b.ms) > min * 1.2 | 2nd |
| TENSE | HOSTILE | max(tension) > 0.7 OR shared territory | 3rd |
| NEUTRAL | TENSE | max(tension) > 0.4 | 4th |
| ALLIED / VASSAL | skip | terminal states | guard |

Tension proxy: max(a.tension_level, b.tension_level) for the pair.
Single-step per pair per call.

## Pipeline Wiring

New Phase 8d in pipeline.py after faction_awareness (8c):
```
compute_transitions(state.factions) → _diplo_updates
compute_common_enemy_pairs(state.factions) → (fid_a, fid_b, ps) tuples
→ AllianceProposal + DiplomaticActionHandler.handle() → more _diplo_updates
run_phase("diplomatic_transitions", ..., lambda u: StateUpdate(faction_updates=_diplo_updates))
```
