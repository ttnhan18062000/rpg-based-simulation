---
ticket_id: TCK-20260619-E12B-BLOCKER-RECAL
phase: investigation
date: 2026-06-20
---

# Investigation: blocker_penalty Recalibration

## E12A Measurement Result

- blocker_frequency = 0.0 (zero blocked routes in 100-tick run)
- All routes: 30 × DEFER_WITH_REASON — no real routes evaluated
- Threshold: < 5% → KEEP 2.0

## Scoring Formula Constants (from scoring.py)

See docs/mechanics/04_strategic_cognition.md §6 for the full table.

Key constants:
- blocker_penalty = 2.0 (fixed)
- personality_bias weight = 0.25
- confidence_bonus weight = 0.15
- risk weight = 0.5 × risk_multiplier
- risk_multiplier = max(0.1, (1.0 + caution×0.8) - bravery×0.6)

## STRAT-227 Placement

New entry; no existing STRAT-* entry covers adventure route scoring constants.
Last entry was STRAT-226 (bravery/caution risk multiplier, added by E11D).
