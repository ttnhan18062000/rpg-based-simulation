---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY

## Normal flow
- `test_bravery_dampens_panic_and_raises_flee_threshold`
  (`tests/unit/strategic/test_cognition_immediate_fixes.py`): at HP=15%, a zero-bravery entity's
  panic stays at 0.5 (matching the pre-existing `test_near_death_panic_progression` baseline
  exactly — confirms no regression for the default/floor case) and flees; a bravery=1.0 entity's
  panic drops to 0.2 and does not flee.

## Edge cases
- Zero-bravery entities are provably unaffected (the fix is purely subtractive from a `0.0` floor)
  — covered by the same test and by the pre-existing `test_near_death_panic_progression` continuing
  to pass unmodified.

## Failure modes / regression-prone paths
- Existing `test_near_death_panic_progression` (4 HP tiers, all default bravery=0.0) re-run
  unmodified to confirm the fix introduces no regression for the un-braved case.

## Not re-verified against real corpus data (disclosed, not assumed)
This fix changes *which* entities flee at a given HP/context state, not *how often* combat
resolves or *how many* kills occur — it doesn't touch the combat-legality/readiness mechanics
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` (this same session) already
re-verified with real corpus probes. A full corpus re-run to observe flee-rate distribution shifts
was judged disproportionate for this specific, narrow, unit-testable behavioral tweak.

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/strategic/test_cognition_immediate_fixes.py \
  tests/unit/social/test_appraisal_logic.py tests/unit/combat/test_engagement_behavior.py \
  tests/unit/strategic/ tests/unit/combat/ tests/unit/social/ -q -m "not slow"
```
