---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: epic-17-multi-hero
artifact_type: plan
tags: [epic, multi, hero]
---

# Implementation Plan: Epic 17 Multi-Hero

## Step 1: Model & Config Upgrades
- Modify `src/config.py` to add `hero_count: int = 4`.
- Modify `src/core/models.py` `Entity` to explicitly accept nullable:
  - `display_name: str`
  - `death_count: int`
  - `generation: int`
  - `hero_familiarity: dict[int, float]`
- Integrate `display_name` seamlessly into the core `/api/world/state` response inside `src/api/schemas.py`.

## Step 2: The Multi-Hero Loop
- Update `src/engine/engine_manager.py` `_build` phase:
  - Instead of yielding 1 hardcoded Hero Class, loop over `range(hero_count)`.
  - Statically select `WARRIOR`, `MAGE`, `RANGER`, `ROGUE` in sequence utilizing modulo arithmetic `i % 4`.
  - Shift their `home_pos` across the town grid trivially `(+i, +i)` to avoid collision overlaps on tick 0.

## Step 3: Hero Lifecycle System
- Create `src/systems/hero_lifecycle_system.py`.
- Hook it via `SystemManager` into the system ticking sequence.
- **Naming Routine**: Inject `FirstName the Title` logic into `HeroLifecycleSystem.on_tick` where `role == EntityRole.HERO` and `display_name is None`. Include the generation hash inside the Name generation.
- **Familiarization Routine**: Run a N^2 radial check over all active heroes inside the system to increment `familiarity[other_id]`.
- **Mortality Routine**: Scan the graveyard tracker for dead heroes. Bump `death_count`. Apply the exponential drop mappings based on `death_count`. Set up `_pending_hero_replacements` queue for the Engine to spawn a refreshed Generation N+1 hero. 

## Step 4: UI Support
- No structural UI changes are heavily required natively due to flexible React mapping, but we must verify that inspecting multiple heroes doesn't crash the sidebar.
