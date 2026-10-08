---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT
artifact_type: test_plan
tags: []
---

# Test plan

Unit tests for steps, scorers and carried food; node and placement tests; LB-S17 two arms; 24-world identity proof; gates; 5000-tick pinned 5x3 (free meals on).

## Proof Plan

- level: unit + mechanic_scenario
- proof kind: behavioral and structural
- oracle source: owner decisions 27 and 29 (docs/world_rules/life-body/survival-needs.md SURV-06, SURV-07), Bible 03 section 3
- expected effect: a hungry subject with no inn within reach is pulled to the forage step; a carrying subject eats its own item; a wild food node is placed on tiles its region owns; LB-S17 two arms
- selected commands: `pytest tests/unit/ai tests/unit/engine tests/unit/worldbuilding/test_wild_food_node.py tests/mechanic_scenarios/test_forage_loop_wild_food.py`
