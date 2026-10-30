---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT
artifact_type: investigation
tags: []
---

# Investigation: N14 door stall, chosen rests and threat wakes

## Cause (lane B, main de5a223ca, urban s46)
FATIGUE squatters hold the inn's 4 door tiles, chattering in 1-tick RESTs at the wake line 58.8 while the fatigue project completes only at REST_MIN_SLEEP_DEBT 20. 878 stalled approaches on main (3 worlds x s42-46 x 5000t), 130,995 ticks.

## Findings during the work
1. Held sleepers have no threat wake on main: `_is_woken` skips anyone holding a payload and `_is_need_woken` wakes a sleeper for hunger only. F1 lengthens sleeps from about 1 tick to hundreds, so the threat wake (2.154) is required.
2. Perception: radius 10, saliency cap 5, no sleep term. The longest attack reach in the content is 3. A shooter hidden behind five closer hostiles is the only miss; counted in the paired run.
3. F1 alone moves the hover from 59 to 20 (real Kernel, one hero): the rest ends at 19.9, but the project completes only on a strategic-cadence tick (every 10, staggered by id), by which time the awake debt (+0.05 a tick) is back at the floor and `rest_in_place_update` fires again. Fixed by the floor-end brain wake, folded into 2.153.
4. A real woken sleeper under threat chooses ATTACK, never REST (the REST-reissue STOP did not fire).
