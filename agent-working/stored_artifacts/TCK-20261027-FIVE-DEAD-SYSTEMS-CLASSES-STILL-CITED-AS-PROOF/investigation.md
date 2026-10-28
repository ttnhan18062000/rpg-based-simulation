---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF
artifact_type: investigation
tags: [world, engine]
---

# Investigation (written at close)

Reachability per class (import by class name, string registration, `importlib`, phase table):

| Class | Live caller found | Live path that carries the behavior |
|---|---|---|
| `LootSystem` | none outside its shim and tests | `InteractionSystem.enforce` (loot progress, completion, movement interrupt) |
| `TownServiceSystem` | none | `InteractionSystem.enforce` and the building service path; `visited_guild_tick` and kind-based routing existed only in the dead class |
| `CraftingSystem` | none (`craft()` has zero callers) | `ActionIntentAdapter.execute` (REQUEST_CRAFT), `ResourceTransactionResolver` CRAFTING branch |
| `QuestSystem` | none | quest reward conservation in `test_transaction_completion.py` |
| `GuildIntelSystem` | none | none for intel; `GuildAction.visit` via `GuildVisitPhase` grants up to two VAGUE `iron_vein` leads (flag default ON) |

Finding: live REQUEST_CRAFT with a recipe id absent from `RecipeRegistry` raises `KeyError` (`action_intent.py`, `RecipeRegistry.get`) where the retired class returned `UNKNOWN_RECIPE`. No live producer of such an id was observed (not measured). PROG-097 is `divergent`; the fix is deferred.

After #757 deleted `chests.py`, `HarvestSystem` also has no `src/` caller (`resource_harvesting` is `orphan`); the `interaction_channeling` call sites were re-traced to `CoreActions.execute_interact` and `InteractionPhase`.
