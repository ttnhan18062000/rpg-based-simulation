---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED
phase: done
date: 2026-10-27
tags: [economy]
---

# TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED

## Title
Legacy `core/recipes.py::RecipeRegistry` is only reached through `town/blacksmith.py::BlacksmithAction`, which nothing in src/ constructs

## Status
DONE

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
Decision (a): delete both files (#760 precedent). Plan by rpg-planner-ubuntu, ruling by rpg-planner (u24), relayed via lead-planner-u24 and lead-planner, word for word in `rpg_planner_plan_and_ruling_2026-10-28.md` (stored artifacts); owner's go on #715 6473373689 and 6473439661. Rulings are not owner approvals. Caller sweep, the assertion-by-assertion coverage map of `test_blacksmith_crafting`, the AC3 static proof and the inventory precedent are in `investigation.md`.
- AC3's run was replaced by a static proof under rpg-planner's 2026-10-28 ruling, because /data is under 10 GB and no run is allowed. The AC text is not edited.
- Completeness pins moved (this is the deletion's substance, not an edit made to pass a test). Before -> after, main a6a01f808 -> this branch: scope_files 345 -> 343, unbound_files 248 -> 246, candidates 68 -> 67; wired 19, WIDER_EXCLUSIONS 18, WIDER_PENDING 1 unchanged. The candidate that left is `src/town/blacksmith.py::BlacksmithService` (name ends in "Service"); `RecipeRegistry` never counted ("Registry" is not a wider suffix). `tools/mechanism_registry/mechanism_registry_completeness_check.py` is untouched.
- Ruling on the pins, word for word in substance, via lead-planner-u24 and lead-planner from agent-working-planner-u24 and rpg-planner (relayed by rpg-planner-ubuntu): (1) `route` on main puts tests/unit/tools/test_mechanism_registry_completeness_check.py in rpg's domain (tests/**; agent-working's glob is tests/{tools,docs}/**), so this is NOT a cross-domain edit, no agent-working agreement is needed, and the PR body must not call it cross-domain. (2) agent-working-planner-u24 confirmed the starting pins on a6a01f808 (345 / 248 / 68, wired 19, EXCLUSIONS 18, PENDING 1) and that the moves fit. (3) rpg-planner: its no-move expectation was wrong; the pin moves are the deletion's real substance and its plan OK stands.
- The inventory CSV/JSON are untouched; rows 123 and 182 are recorded as deleted in prose in `unreachable_code_inventory.md`, following the BiologicalSystem precedent.

## Test Summary
Scoped: tests/unit/world, tests/unit/domains/progression, tests/unit/core, tests/integration/economy, tests/integration/domains/progression 832 passed; completeness file + paths-guard 25 passed; lint-imports 17 kept; code-health 0 new / 0 worse; mechanism-registry changed-code advisory 0 drift.

## Files Changed
src/core/recipes.py and src/town/blacksmith.py (deleted); tests/unit/world/test_economy_contract.py; tests/integration/economy/test_crafting_live_path.py; tests/unit/core/test_same_name_class_guard.py; tests/unit/tools/test_mechanism_registry_completeness_check.py (3 pins); docs/mechanics/resource_conservation_contract.md; docs/parity_ledger/progression.yaml (PROG-123); docs/audits/unreachable_code_inventory.md.

## Completion Summary
Both uncalled legacy files deleted with no live coverage lost; Bible and PROG-123 text updated; completeness pins moved with their reasons recorded.
