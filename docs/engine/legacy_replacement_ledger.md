# Legacy Replacement Ledger

## Purpose

Tracks every V1 system, pattern, or data contract that has been replaced by a V2
equivalent. This is the authoritative record that replacement is complete and the
old path is no longer reachable in production.

## Replacement Ledger

| Legacy ID | Legacy Location | V2 Replacement | Status | Verified By |
|---|---|---|---|---|
| V1 entity state dict | `src/legacy/entity.py` | `EntityState` dataclass | Replaced | SUB-005 |
| `_apply_tick()` direct mutation | `src/legacy/engine.py` | `AuthoritativeApplyPipeline.refine()` | Replaced | AUTH-005 |
| Hardcoded faction list | `src/legacy/factions.py` | `CatalogRepository` + `FactionSemanticsService` | Replaced | WORLD-CAT-004 |
| V1 reward calculator | `src/legacy/rewards.py` | `CombatRewardSystem` + `RewardClassification` | Replaced | PROG-102 |
| Inline RNG calls (`random.randint`) | Various | `DeterministicRNG` | Replaced | SUB-021 |
| Legacy quest dict | `src/legacy/quests.py` | `QuestOpportunity` + `QuestUpdate` | Replaced | AUTH-007 |
