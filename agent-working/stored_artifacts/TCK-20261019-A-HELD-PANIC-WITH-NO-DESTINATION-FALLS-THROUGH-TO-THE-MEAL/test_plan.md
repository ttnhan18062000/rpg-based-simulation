---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL
tags: []
---

# test_plan - TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL

## Test plan
tests/unit/tactical/test_held_panic_falls_through.py: (1) merchant 37, hp 10, unclaimed tile (41,31), eats (fails on main, passes now); (2) hp 10 inside hometown with an adjacent hunter still PANIC_RETREAT to a real destination; (3) synthetic region-less state with a strong adjacent monster keeps PANIC_RETREAT hold and does not ATTACK. Plus tests/unit/tactical and tests/unit/engine tactical suites, lint-imports, mypy_gate.
