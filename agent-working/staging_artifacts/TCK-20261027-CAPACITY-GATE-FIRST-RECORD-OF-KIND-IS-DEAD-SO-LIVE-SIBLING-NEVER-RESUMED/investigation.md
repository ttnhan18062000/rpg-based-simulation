---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
phase: open
date: 2026-10-28
tags: []
---

# investigation

Measured on d914bace7 (step A landed), frontier_living_world, audit mode, probe wrapper on `ScoreModifierSystem.apply_modifiers` (read-only; final state hash with the probe equals the plain run at both tick counts: s42 t531, s43 t326). Probe `target_probe.py` and results `t42.json`, `t43.json` under /mnt/data/scratch-rpg-implementer/n15trace/. Counts are over per-tick candidate evaluations where the best candidate has a same-kind stored project.

## The lookup today
`intelligence.py:1610` `existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)` takes the first same-kind project in dict order, any status. `:1612` resumes only when that one is SUSPENDED. `:1773` `not existing` skips the capacity gate whenever any record of the kind exists. A dead first record therefore blocks resume of a live sibling and skips the cap; `evaluate_project_switch` then adds an ACTIVE project and `CapacityEnforcementPhase` evicts the oldest SUSPENDED one.

## Counts (defect case = first same-kind record dead, a live one exists)
- s42 to t531: 149 entity-ticks (114 target-match, 35 differ = 23%); distinct (entity, candidate, newest-live record) 98 (66 match, 32 differ).
- s43 to t326: 43 entity-ticks (38 match, 5 differ = 12%); distinct 25 (20 match, 5 differ).
- Candidate kinds: combat_engage, resolve_blocker, guild, harvesting, recover, combat_retreat, hunger, fatigue.

## Per-kind target keys (ruling 1)
Over every same-kind record seen in both runs (first objective of each):
| kind | candidate sets | record objective carries |
|---|---|---|
| combat_engage | target_id and target_entity_id | target and target_entity_id |
| resolve_blocker | target_id only | target only |
| guild | target_id only | target only |
| harvesting | target_id only | target only |
| recover, combat_retreat, hunger, fatigue | target_id only | target only |
Same keys on both sides for every kind seen: no kind comes back to rpg-designer on this ground. Not seen in these seeds (not measured): ADVENTURE_ROUTE and committed-intention candidates, which are built through RouteToProjectMapper (:1610 area) and may carry other keys; the plan reads them before code.
Note on "both None is a match": hunger/fatigue targets are a building or town id, not None, so they match on equality like other target_id kinds. The ruling's rule is applied as written.

## Typed end reason (ruling 3)
`ProjectState` (src/core/strategic.py:323) has `status` (`ProjectStatus`: ACTIVE, SUSPENDED, COMPLETED, ABANDONED) and `failure_count`, no end-reason field. Existing endings (intelligence.py:1369, 1483, 1500; entity_target_objective.py:41-85) use `status` only. So a typed reason needs a new field.

## Open points for the plan
1. Where "newest live" is read: `created_tick`, ties by project id.
2. ACTIVE non-current can exist? Not seen as an extra state in the probe records (live = ACTIVE or SUSPENDED; the current project is ACTIVE). The plan states the order: current, then newest live with ACTIVE before SUSPENDED.
