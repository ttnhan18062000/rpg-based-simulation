---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261027-CRAFT-UNKNOWN-RECIPE-RAISES-KEYERROR
artifact_type: investigation
tags: [economy, bug]
---

# Investigation

- `RequirementEvaluator` has no recipe-exists kind (only `recipe_known`, added inside the `RecipeRegistry.contains` guard), so the refusal is a direct failed-trace return.
- The only reader of the `FAILED_REQUIREMENTS` prefix is `src/testing/route_family_classifier.py:27,68`, which counts the refusal as a failed route.
- No live producer of an unknown id is known, so world hashes are expected to be unchanged.
- The retired `CraftingSystem.craft()` returned `UNKNOWN_RECIPE` here; PROG-097 was graded divergent by #760.
