---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-IMMEDIATE-BUGS
artifact_type: test_plan
tags: [cog, immediate, bugs]
---

# Test Plan: Cognition Immediate Bugs

## Automated Tests
- Run `pytest tests/unit/strategic/` to verify no regressions in other strategic features.
- Create a new unit test suite `tests/unit/strategic/test_cognition_immediate_fixes.py` verifying:
  - Panic progression scaling (`hp_percent < 0.1` vs `< 0.2` vs `< 0.4` is monotonic and reaches expected values).
  - `TownScorer` goal score maps successfully to an active `town_return` project with a target ID of `town_center`.
