---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD

Scope-only epic. Plan is the ticket file plus
`docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` — no code change in this epic
itself. When this epic is chosen for action:

1. Resolve the membership-index open question first (check `ClanState` membership prior art, per the
   plan doc's own pointer) and record the decision.
2. Cut child tickets for the 6 scope areas (schema migration; `WorldCompiler` wiring; Stage A pilot;
   Stage B pilot; remaining-19-world rollout; recalibration/triage), each independently
   plannable/implementable/testable.
3. Confirm with the concurrent M3 implementation session before any child ticket touches
   `src/worldbuilding/compiler.py` or `src/worldbuilding/schema.py`.
4. Each child ticket runs its own investigation/plan/test_plan staging artifacts per the standard
   workflow — this epic's staging artifacts do not substitute for those.
