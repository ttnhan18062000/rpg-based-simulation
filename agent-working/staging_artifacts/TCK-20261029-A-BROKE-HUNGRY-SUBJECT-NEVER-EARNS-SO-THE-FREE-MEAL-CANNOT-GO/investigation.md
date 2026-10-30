---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
artifact_type: investigation
tags: []
---

# Investigation
- Root causes: (1) nothing emitted WORK (`building_arrival` always EAT); (2) `SHIFT_START` is read from the payload and nothing set it, so a shift could never pay; (3) a held WORK was never woken by a threat (`_is_woken`: an action holder is not interrupted).
- Building 20000 (urban_political) is a town_hall: functional, `maintenance_open`, wage treasury-backed, `_can_pay_shift` True at t0; the earn step names a building where WORK can succeed.
- Shift arithmetic: a person's hunger rate is 0.05 a tick, a 200-tick shift is +10; the shift pays only on its last tick; the starvation line (95) costs health slowly (`hp_loss_period`), so the line is a cost, not a veto (designer, decision 36).
- Found by the D73-shape probe: a restart livelock under a standing hostile (frontier s46, guard 9: 58 one-tick shifts, each woken by the same hostile); fixed by putting the threat test inside `shift_takeable`; mutation test reproduces it.
- The core EAT action still gives a free 40 relief on this stack whatever the law (`core_actions.eat_update`); the scenario tests switch it off through one named fixture (D73's removal).
