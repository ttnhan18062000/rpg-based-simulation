---
ticket: TCK-20260609-SCENARIO-MODIFIER-APPLY
phase: test_plan
---

# Test Plan

All unit tests in `tests/unit/scenarios/test_scenario_modifier_apply.py`.

| # | Test | Validates |
|---|------|-----------|
| 1-8 | One test per supported modifier type | Correct field in ScenarioSetupContext |
| 9 | Multiple territorial_intrusion | Accumulates claims list |
| 10 | Empty modifier list | All fields empty/None |
| 11 | Unsupported type raises UnsupportedModifierError | Fail-explicit |
| 12 | Unsupported type in mixed list | Raises, not partial |
| 13 | Same modifiers → same context | Determinism |
| 14 | Context is frozen | Immutability |
| 15 | No catalog/repo imports | Boundary check |
