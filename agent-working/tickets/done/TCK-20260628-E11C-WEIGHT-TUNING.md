---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E11C-WEIGHT-TUNING
phase: done
date: 2026-06-28
tags: [personality, ocean, calibration, adventure-scoring, p3]
---

# TCK-20260628-E11C-WEIGHT-TUNING

## Title
Increase greed/sociability personality weights in adventure scoring (E11C)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
E11B 1k-tick personality audit found that greed and sociability had Δ<0.05 effect on
route selection while bravery had STRONG Δ=-0.72. The root cause: uniform 0.25 weight
for all traits, while bravery operates multiplicatively through risk_multiplier. Raising
greed and sociability weights to produce statistically distinct behavioral differentiation.

## Scope
1. `src/domains/adventure/scoring.py` — greed weight 0.25 → 0.50 (GATHER_RESOURCE,
   SELL_LOOT_FOR_GOLD, TAKE_EASY_QUEST, QUEST_OPPORTUNITY); sociability 0.25 → 0.40
   (FORM_PARTY).
2. `docs/mechanics/04_strategic_cognition.md` §6.4 — updated weight table and calibration note.
3. `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227 and STRAT-228 updated.
4. Tests: 4 new E11C weight-calibration tests.

## Out of Scope
- Changing bravery's risk_multiplier path (already strong).
- Caution, curiosity, industry weights (no audit gap found for these).
- Re-implementing OCEAN trait system.

## Acceptance Criteria
- [x] greed weight on GATHER_RESOURCE = 0.50 (test: personality_bias == 0.50 at greed=1.0).
- [x] greed weight on QUEST_OPPORTUNITY = 0.50 (same test).
- [x] sociability weight on FORM_PARTY = 0.40 (test: personality_bias == 0.40 at sociability=1.0).
- [x] Greedy entity advantage gap ≥ 0.40 over neutral entity on gold routes.
- [x] All 48 existing adventure scoring tests pass.
- [x] STRAT-227 and STRAT-228 parity ledger entries updated.

## Related Tickets
- Parent: TCK-20260628-E-PERSONALITY-CALIBRATION
- Depends on: TCK-20260628-E11B-PERSONALITY-AUDIT (audit findings)
- Next: E11D-ABANDONMENT-RATE

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §6.4 (updated)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-227, STRAT-228 updated)

## Related Code Areas
- `src/domains/adventure/scoring.py` (weight constants in personality bias section)
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` (4 new E11C tests)

## Implementation Notes
- bravery exerts multiplicative effect via `risk_multiplier = max(0.1, (1+caution×0.8)-bravery×0.6)`.
  This naturally produces strong Δ without needing additive weight increase.
- Greed 0.25→0.50 means a greedy entity (greed=1.0) gets +0.50 on gold/quest routes vs +0.25 before.
- Sociability 0.25→0.40 means sociable entities (sociability=1.0) get +0.40 on FORM_PARTY.
- blocker_penalty=2.0 still dominates: 2.0 > max(personality_bias=0.50) + max(confidence=0.15) = 0.65.
- The docs/mechanics line "exceeds 0.40" updated to "exceeds 0.65".

## Test Summary
- 4 new E11C tests: weight assertion (greed=0.50 on gather/quest, sociability=0.40 on party),
  advantage gap ≥ 0.40.
- 11/11 route scoring tests pass; 48/48 adventure tests pass.

## Files Changed
- `src/domains/adventure/scoring.py` (greed weight × 2, sociability weight × 1.6)
- `docs/mechanics/04_strategic_cognition.md` §6.4 weight table + calibration note
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-227, STRAT-228)
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` (4 new tests)

## Completion Summary
greed and sociability personality weights raised to 0.50 and 0.40 respectively,
producing a greedy entity advantage gap of ≥ 0.40 on gold routes (was ≤ 0.25 before).
Parity ledger and mechanics doc updated in parity with source. All existing tests pass.
