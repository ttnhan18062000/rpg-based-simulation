# Test Plan: Phase 7/8 Recovery Gaps

## 1. Focused Recovery Proofs
Create `tests/verify/test_recovery_gaps.py` to verify:
- **Hazard Drains**: Entities inside a hazard zone lose HP and Readiness each tick.
- **Calamity Scaling**: Hazard intensity increases with world calamity levels.
- **Evolution**: Entities transform from `goblin` to `goblin_warrior` upon hitting 1000 evolution points.
- **Sabotage**: Sabotaging a building reduces its HP and eventually sets `functional=False`.

## 2. Integrity & Regression
- **Autonomous Loop**: Run `tests/integrity/test_logic_guards.py` to ensure the 100-tick progression loop remains deterministic and successful.
- **Scenario Factory**: Verify that all scenarios in `scenarios.py` build correctly without `TypeError`.
- **Full Suite**: Execute `pytest tests` to confirm 0 regressions across the 232 established tests.

## 3. Parity Validation
- Cross-reference with `legacy_checklist_part3.md` and `part4.md` to ensure legacy behavior (e.g., milestone level-ups) is accurately represented in the V2 authoritative substrate.
