---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH8-M3-PROGRESSION
artifact_type: investigation
tags: [ph8, m3, progression]
---

# Investigation — PH8 M3: Progression and Leveling

## Goal
Implement the core growth mechanics: converting XP (Evolution Points) into Levels and updating derived attributes.

## Requirements
- **Level Curve**: Define XP requirements for each level.
- **Stat Growth**: Base attributes (HP, ATK, DEF) should increase upon leveling.
- **Authoritative Law**: Leveling should happen automatically when enough XP is accumulated (passive law) or via a specific `LevelUpUpdate`.
- **Milestones**: Special bonuses at specific levels (e.g. 5, 10, 20).

## Proposed Architecture

### 1. Progression Service (`src/progression/leveling.py`)
- `get_xp_required(level: int) -> int`.
- `calculate_stats(level: int, base_stats: Dict) -> Dict`.

### 2. State Update
- `IdentityUpdate` already has `evolution_level_set` and `evolution_points_delta`.
- We need a way to trigger stat recalculation.

### 3. Apply Path Logic
- `ApplyPath.apply_generation` already applies XP gains.
- We should add a check: if `evolution_points >= required_xp`, increment level and update `combat` stats.

## Questions
- Is growth linear or exponential?
  Exponential XP requirements are standard for RPGs.
- Do stats scale per level or in "bands"?
  Per-level scaling is simpler to implement deterministically.
