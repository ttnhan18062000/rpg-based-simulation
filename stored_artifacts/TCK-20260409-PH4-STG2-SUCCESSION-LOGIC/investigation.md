# Investigation: Phase 4 Stage 2 — Succession Logic

## Existing Death Logic
- `HeroLifecycleSystem.process_hero_death` handles permadeath.
- It drops *all* items on the ground.
- It removes the entity and schedules a replacement with a generic `rep` dict.
- Replaced hero gets a new ID and is treated as a fresh spawn with generic gear.

## Succession Requirements
1. **Link to History**: Every death must be a `HistoricalEvent`.
2. **Household Persistence**: Heroes must remain part of their house across generations.
3. **Legacy Transfer**:
    - **Physical**: Some items (Heirlooms) should transfer to the Household, not drop on the ground.
    - **Abstract**: Motives (grudges, goals) should transfer to the successor.
4. **Successor Initialization**: The new hero must be "born" with awareness of their predecessor and household ties.

## Design Decisions
- **SuccessorRegistry**: Add a temporary registry in `WorldState` to hold `SuccessorRecord` objects until the replacement hero is spawned.
- **Heirloom Logic**: Items of `RARE` or higher rarity, or specific slots (Weapon/Armor), will be considered "Heirlooms" for the household.
- **Motive Fragments**: Specifically transfer `resentment` towards the killer as a high-priority motive.
