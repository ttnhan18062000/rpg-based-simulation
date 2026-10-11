---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02
artifact_type: test_plan
tags: [economy, resource]
---

# test_plan — TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02

## Tests
tests/unit/world/test_work_shift_pays_a_wage_from_the_inns_purse.py, tests/unit/resource/test_conservation_rejection_paths.py

## Acceptance map
- [ ] A shift pays exactly once per shift id even under double execution (tests/unit/world/test_work_shift_pays_a_wage_from_the_inns_purse.py).
- [ ] Wage rejection cases covered; conservation holds.
- [ ] Pinned paired measurement reported to rpg-planner (also the batch-2 closing measurement).

## Gates
mypy, ratchet, import-linter (17 kept), mechanism completeness pin, scoped unit sweeps, CI matrix sweep.
