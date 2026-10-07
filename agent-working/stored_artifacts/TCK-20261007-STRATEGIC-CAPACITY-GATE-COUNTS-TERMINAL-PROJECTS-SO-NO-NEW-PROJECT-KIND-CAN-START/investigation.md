---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START
artifact_type: investigation
tags: [strategy, cognition, bug]
---

# Investigation

See `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` for the full chain. For this ticket:
- Gate: `intelligence.py` (`at_capacity = len(strat.projects) >= strat.profile.max_active_projects`, then `if at_capacity and not existing: return`). `strat.projects` holds every project ever started; the only trimmer was `detour.py` (`len > max`, strictly greater than the gate's `>=`) and `CapacityEnforcementPhase` (lowest `score` first over all stored projects).
- Measured at the winning evaluation (crowded_frontier, seed 42): entity 3, tick 417, nprojects 3, max_active 3, statuses harvesting COMPLETED, resolve_blocker ABANDONED x2; entity 32, tick 448, nprojects 3, max_active 3, three resolve_blocker ABANDONED, no current project; `evaluate_project_switch` was never called for a fatigue or hunger candidate.
- Other readers of the same count: `scorers.py` (`GuildNeedScorer`), `town/guild.py` (`GuildAction.visit`); `raid.py` uses `max_active_projects=0` as the "no capacity" signal (preserved).
- Before and after (cc3f00a11 vs fix, seed 42, 1500 ticks, audit_mode): see divergence 2.77. Probes (scratchpad, not committed): `measure_cap.py`, `funnel3.py`, `counterfactual.py`.
