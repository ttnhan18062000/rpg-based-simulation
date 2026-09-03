---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
artifact_type: investigation
tags: [content]
---

# Investigation — TCK-20260902-PLACE-SCHEMA-MIGRATION

Full investigation is `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` (Target
Shape + Membership-index decision sections) — not duplicated here. Field-level schema:
`docs/brainstorm/rpg_expected_schemas.html#schema-66`.

Membership pattern precedent, verified directly against `src/core/state.py`:
`GroupRecord.member_ids`/`IdentityComponent.group_id` (`state.py:503`) and
`NavigationComponent.region_id` (`state.py:388`, "Cache region_id to avoid O(N) scans").
