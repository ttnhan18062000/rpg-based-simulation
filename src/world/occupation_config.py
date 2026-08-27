# src/world/occupation_config.py
from src.core.enums import EntityRole

# Target headcount per 100x100 area unit for each civilian occupation role (mirrors
# spawn_config.py's BASE_MONSTER_DENSITY exactly -- same area-normalization formula, applied
# per-region in occupation_change_scorer.py, not here).
BASE_OCCUPATION_DENSITY: dict[int, float] = {
    EntityRole.SHOPKEEPER: 0.5,
    EntityRole.WORKER: 1.0,
    EntityRole.GUARD: 0.5,
}
# Floor so every active region has at least one open slot per role, even a small region -- mirrors
# spawn.py's `target_count = max(2, target_count)` monster-density floor pattern (spawn.py:76),
# using 1 instead of 2 since civilian roles are intentionally sparser than monster density.
MIN_OCCUPATION_SLOTS = 1
