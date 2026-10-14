---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261008-ENV-08-SETTLED-LAND-AND-THE-NEAR-WILD-CARRY-NO-STANDING-AMBIENT-HAZARD
artifact_type: test_plan
tags: []
---

# Test plan

SPC-S16 main and control arms; compile assertion; 24-world resolve; unit sweeps.

## Proof Plan

- level: unit + mechanic_scenario
- proof kind: behavioral
- oracle source: owner decision 30, rule ENV-08, Bible 05 Hazard Impacts
- expected effect: a town worker crosses the second town and the near forest at full HP and returns; the same walk into deep forest dies of HAZARD; no settled region carries a standing hazard
- selected commands: `pytest tests/mechanic_scenarios/test_near_wild_is_survivable_deep_wild_is_not.py`
