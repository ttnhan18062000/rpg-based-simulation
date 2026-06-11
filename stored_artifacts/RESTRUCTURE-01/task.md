---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [restructure]
---

- [x] Fix 1: Add `Inventory.is_effectively_full`, `weight_ratio`, `count_item` (36+ tests)
- [x] Fix 2: Add `TreasureChest.try_respawn`, `loot`, `is_available` (6 tests)
- [x] Fix 3: Update `WorkerPool` constructor call sites (43 tests)
- [x] Fix 4: Add missing `HomeStorage` methods and fix upgrade math (5+ tests)
- [x] Fix 5: Complete loot data and add `calamity` items (9 tests)
- [x] Fix 6: Fix `_DictShim` and `RACE_SKILLS` lookup (1 test)
- [x] Fix 7: Update `gold_ingot`, `iron_dagger` in `items.json`
- [x] Fix 8: Export `RACE_CLASS_MAP` and update `BREAKTHROUGHS` test
- [x] Fix 9: Align ranged mob gear tests with SPAWN_CONFIGS
- [x] Fix 10: Update deterministic replay hashes
- [x] Add missing E2E tests for data-driven registries
- [x] Phase 0: API & Architecture Audit (Document findings)
- [x] Phase 1: Game Data Refactoring (Move metadata out of routes)
- [x] Phase 2: Standardized Serialization (Entity to Schema mapping)
- [x] Phase 3: Route Cleanup (Decouple state routes from core logic)
- [x] Phase 4: EngineManager Decomposition (Extract WorldGenerator)
- [x] Phase 5: Audit Static vs. Dynamic Paths (Separate invariant state)
