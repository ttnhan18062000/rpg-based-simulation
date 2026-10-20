---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION
tags: []
---

# investigation - TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION

## Finding
After step one (a49896e1c) V3 on frontier 42 was still red: merchant 37 starved at t4081 with the same record. Probe at ticks 2100-3650: project and objective empty at every sample, no hunger goal chosen. Cause: `_escalated_unless_threatened` drops the escalation while a present threat holds; raw hunger 100 is outscored by town_return (155-161), fatigue and combat_retreat (Lane C trace). Forced equivalent (merchant 37 hp 10/85, hunger 100, at (41,31), hunter 45 adjacent): with step one alone, hunger stays 100 after 200 ticks; with the hunger gate lifted at hunger >= 95 it takes proj_hunger and eats by tick 14.
