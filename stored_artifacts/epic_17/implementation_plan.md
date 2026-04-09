# Implementation Plan: Epic 17 — Phase 1 (Core Spine & Multi-Hero)

## 1. Objective
Establish the foundation for long-term narrative durability by replacing the single-hero model with a multi-generational, multi-hero ensemble.

## 2. Proposed Changes

### F1: Multi-Hero Spawning & Config
#### [MODIFY] [config.py](file:///d:/Projects/rpg-based-simulation/src/config.py)
- Add `hero_count: int = 4` (default).
- Add `death_tier_max: int = 4` (permadeath threshold).

#### [MODIFY] [engine_manager.py](file:///d:/Projects/rpg-based-simulation/src/engine_manager.py)
- Update `_build()` to loop spawn `hero_count` entities.
- Assign classes (Warrior, Ranger, Mage, Rogue) round-robin.

### F2: Hero Naming & Generation
#### [NEW] [hero_names.py](file:///d:/Projects/rpg-based-simulation/src/core/hero_names.py)
- Tables of first names and titles based on traits.
- Function `generate_hero_name(rng, traits: list[TraitType]) -> str`.

#### [MODIFY] [models.py](file:///d:/Projects/rpg-based-simulation/src/core/models.py)
- Add fields to `Entity`:
  - `display_name: str`
  - `death_count: int = 0`
  - `generation: int = 1`
  - `hero_familiarity: dict[int, float]`

### F3: Death Escalation & Replacement
#### [MODIFY] [world_loop.py](file:///d:/Projects/rpg-based-simulation/src/engine/world_loop.py)
- In `_process_death`:
  - Increment `death_count` for heroes.
  - Implement Tiered Drops:
    - 1 death: Bag items.
    - 2 deaths: Bag + accessory.
    - 3 deaths: Bag + accessory + armor.
    - 4 deaths: **Remove from world**.
- Add `_process_hero_replacement`:
  - If a hero is permadead, spawn a new Level 1 hero at town center after 50 ticks.
  - Increment generation: `new_gen = old_gen + 1`.

### F4: Hero Familiarity
#### [MODIFY] [world_loop.py](file:///d:/Projects/rpg-based-simulation/src/engine/world_loop.py)
- In cleanup phase, update proximity-based familiarity between hero pairs.
- Emit Alliance events at 0.5+ familiarity.

## 3. Verification Plan
### Automated Tests
- `tests/test_multi_hero.py`: Verify 4 heroes spawn at start with unique IDs.
- `tests/test_naming.py`: Verify names are generated and assigned.
- `tests/test_permadeath.py`: Kill a hero 4 times and verify replacement spawn with `generation=2`.

### Manual Verification
- Observe the frontend Sidebar to see 4 heroes with unique names.
- Verify that when a hero dies, the event log uses their specific name.
