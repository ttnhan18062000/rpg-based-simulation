---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED
phase: open
date: 2026-10-27
tags: [economy]
---

# TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED

## Title
Legacy `core/recipes.py::RecipeRegistry` is only reached through `town/blacksmith.py::BlacksmithAction`, which nothing in src/ constructs

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
A follow-up from TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS (U3). rpg-planner (u24) ruled on
2026-10-27, relayed, to keep the legacy RecipeRegistry with an allowlist reason for now, and to file
this ticket for the town module.

On origin/main 3b5fab1e9:
- The live `RecipeRegistry` is `src/core/registries.py`, which `action_intent.py` imports.
- The legacy `src/core/recipes.py::RecipeRegistry` has one src reader,
  `src/town/blacksmith.py::BlacksmithAction` (line 68).
- Nothing in `src/` or `tools/` constructs `BlacksmithAction`. Only
  `tests/unit/world/test_economy_contract.py` (lines 8, 76 and 88) uses it.
- `docs/audits/unreachable_code_inventory.csv:123` already lists it as unreachable.

## Scope
1. Confirm there are no callers, including string or `getattr` dispatch, the CLI and the lab.
2. Decide which of these to do, and record why:
   - (a) delete `BlacksmithAction` and the legacy `RecipeRegistry`, and repoint or delete the
     test_economy_contract cases;
   - (b) keep them, with the reason stated.
   The #760 precedent is delete. Check what those test cases assert that the live craft path
   (`tests/integration/economy/test_crafting_live_path.py`) does not already cover.
3. Remove the legacy RecipeRegistry's allowlist entry from the same-name guard if (a) is chosen.

## Out of Scope
- The live craft path and `src/core/registries.py`.
- Other `town/` actions (ShopAction, GuildAction, HomeAction).

## Acceptance Criteria
1. The caller sweep is recorded.
2. Either the code is deleted, with no live coverage lost and the guard allowlist updated, or it is
   kept with a stated reason.
3. A hash-neutral proof.

## Related Tickets
- TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
- TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF (#760 precedent)

## Related Docs
- docs/audits/unreachable_code_inventory.csv

## Related Stored Artifacts

## Related Code Areas
- src/core/recipes.py, src/town/blacksmith.py, tests/unit/world/test_economy_contract.py

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
