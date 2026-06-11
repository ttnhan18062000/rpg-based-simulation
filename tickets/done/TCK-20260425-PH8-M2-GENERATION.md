---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260425-PH8-M2-GENERATION
phase: done
date: 2026-04-25
tags: [ph8, m2, generation]
---

# TCK-20260425-PH8-M2-GENERATION

## Title
Implement Deterministic, Scaled Quest Generation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement a dynamic quest generator that produces deterministic, level-scaled quests for town buildings.

## Scope
- Define `QuestTemplate` and initial templates (HUNT, GATHER, EXPLORE).
- Implement `QuestGenerator` with scaling laws for goals and rewards.
- Integrate `QuestGenerator` into `GuildAction`.
- Remove legacy dummy quest logic.

## Out of Scope
- Dynamic world event triggers (Phase 12).
- Complex multi-stage quests (Phase 15).

## Acceptance Criteria
- Same seed/level/building produces identical quests.
- Goals and rewards scale strictly with entity level.
- Guild correctly populates project list with generated quests.

## Related Tickets
- `TCK-20260425-PH8-M1-QUESTS`

## Related Docs
- `resource_v2_e_phases.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260425-PH8-M2-GENERATION/`

## Related Code Areas
- `src/quests/templates.py`
- `src/quests/generator.py`
- `src/town/guild.py`
- `tests/quests/test_quest_generation.py`

## Implementation Notes
- Goal scaling: `base_goal * (1 + level * 0.2)`
- Reward scaling: `base_reward * (1 + level * 0.5)`
- `QuestGenerator` uses `random.Random(seed + building_id)` for stability.

## Test Summary
- `test_quest_generation_determinism`: PASS
- `test_quest_level_scaling`: PASS
- `test_guild_visit_integration`: PASS

## Files Changed
- `src/quests/templates.py` [NEW]
- `src/quests/generator.py` [NEW]
- `src/town/guild.py` [MODIFY]
- `src/town/quests.py` [DELETE]
- `tests/quests/test_quest_generation.py` [NEW]

## Completion Summary
- Implemented a robust, data-driven quest generation system.
- Verified that quests are correctly context-aware and level-appropriate.
