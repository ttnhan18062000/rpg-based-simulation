---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP
artifact_type: plan
tags: [performance, combat]
---

# Plan

1. `RelationLookup` in `src/content_semantics/relation.py`: first-match indexes for perspective (by id, then by `chosen_faction`), has-perspective, faction relationship (source, target), species relation (source, target). Rebuilt when a table object or length changes.
2. `RelationProjectionService.project_relation` uses the lookup in place of its three scans.
3. `FactionSemanticsService.is_hostile_compat` reuses one projection service and the lookup in place of its three scans and the per-call service.
4. No label cache; no hostility-semantics change; no cooperation or threat files.
5. Host-gated verification (on planner's "host free"): bisect timing, before/after `combat_engagement`, 3-world hash, `--neutral`.
