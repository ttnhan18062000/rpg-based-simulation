# PH8 M2: Quest Generation

Implement dynamic, deterministic quest generation for town buildings.

## Proposed Changes

### [Models] [NEW] [templates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/quests/templates.py)
- Define `QuestTemplate` dataclass and a registry of templates.

### [Generator] [NEW] [generator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/quests/generator.py)
- Implement `QuestGenerator` class with deterministic selection and scaling logic.

### [Town Services] [MODIFY] [guild.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/guild.py)
- Update `GuildAction` to use `QuestGenerator` for populating quest lists.

## Verification Plan

### Automated Tests
- `tests/quests/test_quest_generation.py`:
  - Verify deterministic output for same seed/level.
  - Verify reward scaling with level.
  - Verify variety of quest kinds across different building types.

#### Manual Verification
- CLI inspection of guild quest boards across different regions.
