---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260425-PH7-M2-GUILD
phase: done
date: 2026-04-25
tags: [ph7, m2, guild]
---

# TCK-20260425-PH7-M2-GUILD

## Title

Implementation of Guild Service and Quest Generation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the Guild service for strategic lead generation and world intelligence. Ensure entities can receive quests and world-knowledge authoritatively.

## Scope

- Implement \`GuildAction.visit(entity, state)\`.
- Implement \`QuestGenerator\` for creating strategic projects.
- Logic to generate leads based on world truth.
- Add contract tests for guild service.

## Out of Scope

- Quest resolution logic (deferred to future milestones).
- Guild reputation.

## Acceptance Criteria

- [x] Guild visit adds new leads to entity strategic state.
- [x] Guild visit can create quest offers (projects).
- [x] Leads are relevant to existing world nodes.
- [x] All tests in \`tests/town/test_guild_pipeline.py\` pass.

## Related Tickets

- TCK-20260425-PH7-M1-TOWN (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/town/guild.py [NEW]
- src/town/quests.py [NEW]
- src/core/strategic.py

## Implementation Notes

- \`GuildAction.visit\` scans \`resource_nodes\` to provide relevant intelligence.
- \`QuestGenerator\` creates \`ProjectState\` with \`ObjectiveState\` for strategic tracking.
- Leads use \`LeadCertainty.VAGUE\` for rumors.

## Test Summary

- \`tests/town/test_guild_pipeline.py\`:
  - \`test_guild_visit_leads\`: PASS
  - \`test_guild_visit_quests\`: PASS
  - \`test_guild_visit_determinism\`: PASS

## Files Changed

- src/town/guild.py [NEW]
- src/town/quests.py [NEW]
- src/core/state.py (Restored global_resources)

## Completion Summary

Phase 7 Milestone 2 is complete. The Guild now functions as a strategic hub, providing entities with world intelligence and concrete objectives, integrated into the authoritative engine.
