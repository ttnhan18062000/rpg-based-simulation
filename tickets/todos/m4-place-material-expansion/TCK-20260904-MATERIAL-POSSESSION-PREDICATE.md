---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-MATERIAL-POSSESSION-PREDICATE
phase: open
date: 2026-09-04
tags: [economy, progression, cognition]
---

# TCK-20260904-MATERIAL-POSSESSION-PREDICATE

## Title
Shared material-possession predicate for ambition and expansion (ideas 49+50)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Ideas 49 (Ambition) + 50 (Expansion), consolidated per the epic doc's own scope text: both gate on "does this entity possess/consume material X" — worth one shared predicate, not a ticket merge. Reuses/extends the existing `PossessionUnderstandingService` (`src/domains/progression/possession.py`) rather than duplicating it, and must name explicitly which of the two colliding `RecipeRegistry` classes (`src/core/recipes.py`, legacy/live vs `src/core/registries.py`, catalog-only) the predicate reads through.

## Scope
- Add a shared material-possession/consumption predicate (single function or small service), reusing/extending `PossessionUnderstandingService.evaluate()` rather than building a parallel evaluator.
- Explicitly name and use `src/core/recipes.py::RecipeRegistry` as the live crafting-path registry the predicate reads through (confirmed the one imported by `src/systems/economy_systems/crafting.py` and `src/town/blacksmith.py`) — `src/core/registries.py::RecipeRegistry` (catalog-bootstrapped, not the live crafting path) must not be silently substituted, and any new naming introduced by this ticket must avoid adding a third confusable `RecipeRegistry`-like name.
- Wire the predicate to at least one real production consumer (not test-only) — if it feeds `AmbitionProfile` (`src/core/cognition.py`, currently zero production consumers per `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`), this ticket must also wire `AmbitionProfile` itself into at least one real production read site, not just add another populated-but-unread field.
- Cover normal flow (entity possesses/consumes material X), edge cases (entity has zero inventory, material not in any known recipe), and failure modes (RecipeRegistry lookup miss) with tests.

## Out of Scope
- National EXPAND_TERRITORY directive implementation itself — that's `TCK-20260904-FACTION-EXPAND-DIRECTIVE` (a separate ticket); this ticket only produces the shared predicate idea 52 will consume.
- Any change to `src/core/registries.py::RecipeRegistry` or its catalog-bootstrap consumers — out of scope, named only to disambiguate.
- Rewriting or renaming either existing `RecipeRegistry` class — only explicit selection of which one the new predicate uses.

## Acceptance Criteria
- A single, named material-possession predicate exists, reused/extended from `PossessionUnderstandingService`, with no duplicate parallel evaluator introduced.
- The predicate's implementation and its tests explicitly reference `src/core/recipes.py::RecipeRegistry` (not `src/core/registries.py::RecipeRegistry`), with a code comment or docstring disambiguating the two by file path.
- If `AmbitionProfile` is the consumer, at least one real (non-test) production code path reads the populated field — verified by a test asserting production behavior changes based on the predicate's output, not just that the field gets set.
- Tests cover: entity possesses material X (positive), entity has no relevant inventory (edge), unknown/unregistered material (failure mode).

## Related Tickets
- TCK-20260904-FACTION-EXPAND-DIRECTIVE
- TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html (ideas 49, 50)
- docs/mechanics/03_economic_laws.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/progression/possession.py (PossessionUnderstandingService)
- src/core/recipes.py (RecipeRegistry — live crafting path)
- src/core/registries.py (RecipeRegistry — catalog-bootstrapped, NOT the live path)
- src/systems/economy_systems/crafting.py
- src/town/blacksmith.py
- src/core/cognition.py (AmbitionProfile)
- tests/unit/domains/progression/test_phase6_possession_understanding_service.py

## Assumptions / Open Questions
- Two unrelated classes are both named `RecipeRegistry` (`src/core/recipes.py`, live; `src/core/registries.py`, catalog-only, not live) — this ticket must name which one it reads through and avoid a third confusable name.
- `AmbitionProfile` (`src/core/cognition.py`) currently has zero production consumers (confirmed: only defined, `strategic_value_targets: Tuple[str, ...] = ()`) — if this predicate feeds it, the ticket must wire at least one real consumer per `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`'s prior finding on this exact dead-on-arrival pattern.
- Recommended sequencing (soft): idea 52's population-pressure-driven expansion (`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) is meant to be informed by material possession per idea 52's card — recommend landing this predicate before/alongside that ticket, though not a hard blocker.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
