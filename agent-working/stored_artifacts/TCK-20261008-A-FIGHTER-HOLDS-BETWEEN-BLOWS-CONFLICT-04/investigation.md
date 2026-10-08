---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04
phase: open
date: 2026-10-08
tags: [combat]
---

# Investigation: TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04

_(see body below)_

## Findings
- Chokepoint `ENTITY_ACT` `HOLD` (src/engine/tactical.py, VANGUARD branch, HOLD_CHOKEPOINT) has no ActionRouter handler (src/engine/domain/action_router.py falls through to `_reported_no_op(UNSUPPORTED_ACTION)` at line 90), so it would end as UNSUPPORTED_ACTION every time. Count in the pinned runs (5 seeds x 3 worlds, both arms): 0 HOLD_CHOKEPOINT decisions, so it is unreachable in the corpus. Out of scope; routed to rpg-planner.
- Pinned report: see divergence 2.86. Probe: probes/oa_fix_ms.py (extended with flee, hold and low-HP counters).
- stale_ticks reset is at ATTACK/SKILL emission, not at landing.
