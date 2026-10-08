---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION
phase: done
date: 2026-10-08
tags: [combat]
---

# Investigation: TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION

Path reproduced in a constructed kernel case (orc VANGUARD in a one-tile wall gap, hostile 2 tiles away, range 1): on main the hold ends as UNSUPPORTED_ACTION at tick 8 (router fallthrough, `action_router.py` end of `execute_action`), movement mode HOLD keeps the tile (resolve_move mode multiplier 0.0), the brain re-decides at tick 18. A router no-op success with the task kept reports HOLD SUCCESS for 60 ticks and the brain never runs again (scheduler runs the brain only for an empty payload): rejected. Built: typed success + payload cleared on a HOLD success. 0 HOLD_CHOKEPOINT decisions in 30 pinned runs. Probe: probes/choke_probe.py.
