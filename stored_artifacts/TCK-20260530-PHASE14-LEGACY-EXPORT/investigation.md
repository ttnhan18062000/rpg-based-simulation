# Investigation Notes - Phase 14 Legacy Export

## Current Hardcoded State
- Hardcoded definitions exist in `src/core/registries.py` (ItemRegistry, ResourceRegistry, EnemyRegistry, RecipeRegistry, ServiceRegistry, RegionRegistry).
- Combat profiles (`profiles/combat.yaml`) and Cognition profiles (`profiles/cognition.yaml`) currently do not exist in the active content catalog directory or are completely empty.
- We need to export all Phase 1 content to match the active schema definitions exactly.
