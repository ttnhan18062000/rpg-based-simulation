---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D03-BEHAVIOR
phase: open
date: 2026-06-18
tags: [audit, behavioral-emergence, simulation-quality, stasis, rejections, quests, economy]
---

# TCK-20260618-AUDIT-D03-BEHAVIOR

## Title
D03 — Behavioral Emergence Quality Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Run the simulation and observe whether entities behave like RPG characters or enter
a repetitive loop. Establish a behavioral quality baseline for all run-sim audits.

## Scope
- Run 200-tick simulation under two seeds (42 and 137)
- Observe event distribution, goal variety, movement, resource use, quest activity
- Score behavioral emergence gaps

## Out of Scope
- Fixing behavioral regressions
- Content additions

## Acceptance Criteria
- docs/audits/D03_behavioral_emergence.md written with scoring rubric
- audit_dimensions.md D03 row updated to done
- Working log and monitoring entries written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)
- TCK-20260618-AUDIT-D07-CONTENT (F1: 4 quest definitions — confirmed zero quest activity)
- TCK-20260618-AUDIT-D10-TESTS (F2: ItemStack.position — may be causing final_integrity budget overruns)

## Implementation Notes
Pre-condition bug: sandbox_world template used quest_definitions (wrong key) instead of quests.
Fixed in data/worlds/sandbox_world/world.yaml before running.

Run results:
- Seed 42: 8 events total; all in ticks 3-7; 94+100=194 rejections; 15.3 alive avg
- Seed 137: 9 events total; all in ticks 3-20; 426+500=926 rejections; 15.43 alive avg
- Both: zero quests, zero resource transactions, zero gold, behavioral stasis after tick 20

## Files Changed
- data/worlds/sandbox_world/world.yaml (bug fix: quest_definitions → quests)
- docs/audits/D03_behavioral_emergence.md (create)
- docs/audits/audit_dimensions.md (update)

## Completion Summary
D03 audit complete. Behavioral stasis confirmed across both seeds (42, 137). All 4 findings scored with Emergence Gap rubric. docs/audits/D03_behavioral_emergence.md written. audit_dimensions.md updated. Pre-condition bug (world.yaml quest_definitions→quests) fixed as part of investigation. staging_artifacts migrated to stored_artifacts.
