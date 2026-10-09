---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02
phase: done
date: 2026-10-08
tags: [combat]
---

# Investigation: TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02

## Findings
- The "capacity degradation" SURV-02 cites is cognitive only (`strategy/cognition_capacity.py` fatigue_multiplier: hunger or sleep debt above 70 gives x0.5 of project/lead/concern limits). It cannot carry recovery or fighting; it stays as the hungry stage.
- Existing physical hooks reused: the `combat.py` EXHAUSTION attack factor pattern, the stamina regeneration and the readiness regeneration in `apply.py`. There is no passive HP regeneration.
- Pinned 5x3 at 10000 ticks: see divergence 2.94 and probes/d36/ (main arm `main`, feature arm `d36`).
- cProfile (1500 ticks, frontier_living_world seed 42): hp_loss 0.061 s, recovery_scale 0.020 s of 12.0 s in `_compute_entity_changes`.
- Finding: sleep debt >= 98 costs 1 HP per tick, same shape; for the designer.
