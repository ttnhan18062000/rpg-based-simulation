---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND
artifact_type: plan
tags: [world]
---

# Plan — TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND

1. Add `yield_item: Optional[str]` to `ResolvedResourceProfile` (`src/worldassembly/models.py`).
2. Fill it in `WorldResolver` from the catalog resource definition (`runtime_kind or resource_type`).
3. In `WorldCompiler` step 4 use `profile.yield_item`, else `ResourceRegistry`, else the declared string.
4. Regression tests: `tests/unit/worldbuilding/test_compiled_node_yields_item.py` (context path, no-context path,
   unknown kind, every corpus world yields a registered item).
5. Re-run the probe before/after; record both, with conditions.
6. Out of scope: renaming the module-authoring field (schema change); SimQ anchor re-baseline (own ticket).
