---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
artifact_type: test_plan
tags: []
---

# Test plan
- Unit (`tests/unit/engine/test_earn_shift.py`): shift_takeable (urban shape over the line but alive; hp not lasting; exact boundary projected hp 0; the line object is starvation's; far meal costs more), open step / ways_in_reach agree, the pull over the whole step, arrival action by building under both laws (inn that hires, town hall, ends the project when not alive at the meal, other purposes unchanged), a threat at the hiring inn gives no WORK and no strategic change, WORK again once gone, the wake: hunger does not wake a shift, a present threat wakes a held WORK only.
- Real kernel (`tests/integration/scenarios/test_a_broke_hungry_worker_earns_and_then_eats.py`): earns then buys a meal at the inn (paid service), hunger rising does not end a feasible shift, a threat ends a held shift with no wage, scripted-threat seam: no shift cut off after one tick (mutation reproduces 51 one-tick shifts).
## Proof Plan
- level: unit, real-kernel scenario, paired run, D73-shape probe
- proof kind: regression plus hash-identity on main
- oracle source: the parent commit's final hashes; the probe's per-person counts
- expected effect: no behaviour change on main (CLAMP, free meal on); under the D73 shape persons earn and eat, no starvation rise, no loop
- selected commands: `pytest tests/unit/engine/test_earn_shift.py tests/integration/scenarios/test_a_broke_hungry_worker_earns_and_then_eats.py`; `python -m tools.rpg_measure.paired --base b9287a3de --new <head>`
