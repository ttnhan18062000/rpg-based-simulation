---
ticket_id: TCK-20260619-E53Bb-DIPLO-ACTIONS
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E53Bb-DIPLO-ACTIONS

## Tests (appended to tests/unit/faction/test_diplomacy.py)

1. `test_diplomatic_action_alliance_proposal` — both ALLIED; VASSAL case for strength >= 2x
2. `test_diplomatic_action_betrayal_valid` — both HOSTILE + tension +0.3 for betrayed
3. `test_diplomatic_action_betrayal_invalid_not_allied` — returns []
4. `test_diplomatic_action_trade_agreement` — both NEUTRAL + tension -0.15
5. `test_diplomatic_action_noop_when_noop` — TreatyOffer(accepted=False) → []
6. `test_diplomatic_action_non_aggression_pact` — both NEUTRAL, no tension change

## Run
```bash
pytest tests/unit/faction/test_diplomacy.py -x -v
```
