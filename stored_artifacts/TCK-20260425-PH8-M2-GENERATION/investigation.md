---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH8-M2-GENERATION
artifact_type: investigation
tags: [ph8, m2, generation]
---

# Investigation — PH8 M2: Quest Generation

## Goal
Implement a dynamic quest generator that produces quests based on level, region, and building type.

## Requirements
- **Templates**: Hunt, Explore, Gather, Liberate, Bounty.
- **Level Scaling**: Rewards and goal difficulty should scale with entity/region level.
- **Deterministic Seed**: Use the world seed/tick for deterministic generation.
- **Service Integration**: `QuestGenerator` should be used by `GuildAction` and other town services.

## Proposed Architecture

### 1. Quest Templates (`src/data/quest_templates.py`)
- Define base parameters for each quest kind.

### 2. Generator Service (`src/quests/generator.py`)
- `generate_quest(seed: int, level: int, region_id: str, building_id: int) -> QuestState`.

### 3. Reward Calculation
- `xp_reward = base_xp * level_factor`
- `gold_reward = base_gold * level_factor`

## Questions
- Should quest IDs be unique across the world or just per-building?
  Global unique IDs (e.g. `q_{building_id}_{tick}`) are safer.
- Do we need "Gather" quests if we don't have a harvesting loop yet?
  Milestone 3 of Phase 6 (Harvest) is complete, so we can support Gather.
