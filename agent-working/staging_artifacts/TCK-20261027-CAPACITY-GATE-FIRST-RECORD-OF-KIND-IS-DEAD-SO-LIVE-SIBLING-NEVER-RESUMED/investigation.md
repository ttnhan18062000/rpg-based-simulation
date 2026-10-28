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

## What the old path did for the current project at the same kind and target (planner ask a)
Old `evaluate_strategic_intent`: `existing` = first same-kind project in dict order. For an ACTIVE `existing` there was no resume (:1612 resumed only SUSPENDED). A new candidate `proj_<kind>_<tick>` was built (score = live utility, fresh lock), the capacity gate was skipped (`not existing`), and `evaluate_project_switch` ran on it:
- lock active and threat not resolved: the candidate had to beat the current's normalised score plus margin and clear the urgency floor, else `None` (no update);
- otherwise `candidate.score > current.score + retention_margin`: the current project was SUSPENDED and the same-kind, same-target candidate was added and made current (a duplicate of the same kind and target, the old one suspended); else `None`.
So the old outcome was a no-op or a same-target duplicate with the old record suspended. The new path always continues (no update beyond boredom and leads). The paired run counts these as its own counter ("continue"), with the old-path duplicate events counted on the base arm by the probe.

## Edge cases from rpg-designer (via planner)
- ACTIVE record at the matching target that is NOT current: reachable. `current_project_id` is cleared without ending the project in `tactical.py:136`, `building_arrival.py:22`, `guild_visit.py:88` and `intelligence.py:575/858` (`current_project_id_set=""`). Old path: fell through to the duplicate. New path: the record is made current (`current_project_id_set`, `current_objective_id_set`), nothing created (ruling 2). Counted as its own counter in the paired run.
- SUSPENDED record where `resume_project` returns None: `resume_project` returns None only when the record is absent or not SUSPENDED in `entity.strategic.projects`; the lookup returns a SUSPENDED record from that same map, so it cannot happen for a looked-up record. A guard remains: the tick ends with no project created and boredom and lead deltas carried. Pinned by a test that forces None.
