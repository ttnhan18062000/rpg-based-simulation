---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE
artifact_type: investigation
tags: [content, economy]
---

# Investigation — TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE

## Context scan
`mcp__knowledge-search__search_docs` and `graphify query` run first, per CLAUDE.md's mandatory
Context Scan. Confirmed `docs/mechanics/resource_conservation_contract.md`'s "Crafting Atomicity"
section already documents `CraftingSystem`'s 7-gate check starting with "Recipe known in
RecipeRegistry" — a third, separate crafting path (`src/systems/economy_systems/crafting.py`) not
directly relevant to this ticket's 3-registry bridge (its own `RecipeRegistry` reference resolves
to `src/core/recipes.py`'s legacy registry per the sibling ticket's own citation, and `CraftingSystem`
itself was already confirmed to have zero production callers).

## Fresh verification beyond the ticket's own citations (not re-litigating what was already
## twice-verified, but confirming what this ticket's own fix must actually change)

**`registries.py::RecipeRegistry`'s live reachability, re-confirmed with a new trace**: the
sibling ticket already established `action_intent.py`'s `REQUEST_CRAFT` branch reads it. Traced
one level further: `src/domains/adventure/resolver.py:56` converts `ObjectiveKind.ACQUIRE_ITEM`
into `kind = "REQUEST_CRAFT"` — a real strategic-cognition dispatch site, not a test/certification
scenario. This is the genuine AI-driven trigger for the live crafting path.

**`BlacksmithSystem.enforce()`'s own crafting-EXECUTION branch (not just its recipe list) is ALSO
dead in practice, confirmed by direct trace** — a finding beyond what either prior ticket
established: that branch (`src/engine/blacksmith.py:154-246`) only runs when
`entity.identity.craft_target` is non-empty. Grepped every real assignment of `craft_target=`
across `src/`: the only non-clearing assignment is `src/certification/scenarios.py:480` (a
synthetic certification scenario builder, not live AI), and `src/systems/strategic_systems/
intelligence.py`'s two references both *clear* it (`craft_target=""`). No real strategic/goal
system ever sets it to a real value. Consequence: changing what ids the wholesale-learn step
populates into `known_recipes` (this ticket's actual fix) cannot regress
`BlacksmithSystem.enforce()`'s own crafting-execution behavior, because that behavior is already
unreachable today regardless of `known_recipes`' content — confirmed, not assumed.

**Real content-parity check between the 14 and 25-entry catalogs (the ticket's own explicit
demand: "do not default to the smallest textual diff without evaluating gameplay/balance
impact")**: fetched both real catalogs directly.
- `registries.py::RecipeRegistry` (`catalog.recipes`, 25 raw entries, confirmed the real live source
  bootstrapped via `CatalogToRecipeRegistryAdapter(catalog_repo).adapt()`): e.g.
  `craft_iron_sword -> {iron_sword} materials {iron_ore:2, wood:1}`, `craft_hunter_blade`,
  `craft_small_potion`, etc. — all output items and materials are real, populated `CatalogRepository`
  entries. **Correction found during test-fixing (not affecting the decision below):** the
  bootstrapped registry actually holds ~46 keys, not 25 — `CatalogToRecipeRegistryAdapter.adapt()`
  (`src/core/registries.py:282-317`) registers a `craft_`-stripped legacy alias id for every recipe
  whose `rec_id` starts with `craft_`, alongside the original id, both pointing at the same
  `RecipeDef` (e.g. `craft_iron_sword` and `iron_sword` both resolve). The 25 is the raw
  `catalog.recipes` count; the live, queryable `RecipeRegistry.all()` surface is larger.
- `BlacksmithSystem.RECIPES` (14 entries, `craft_steel_sword`/`craft_battle_axe`/etc.): **13 of 14
  output items (`battle_axe`, `enchanted_blade`, `iron_plate`, `enchanted_robe`, `ring_of_power`,
  `evasion_amulet`, `wolf_cloak`, `fang_necklace`, `desert_bow`, `bone_shield`, `spectral_blade`,
  `mountain_plate`, `herbal_remedy`) do not exist in `catalog.items` at all** — confirmed via direct
  check (`item_id in catalog.items` — False for all 13; only `steel_sword` exists as a real item,
  and no `registries.py` recipe produces it either). **11 of its 15 distinct required materials
  (`bone_shard`, `dark_moss`, `ectoplasm`, `enchanted_dust`, `fiber`, `glowing_mushroom`, `leather`,
  `raw_gem`, `steel_bar`, `stone_block`, `wolf_fang`) do not exist in `catalog.materials` or
  `catalog.items` either** — confirmed via direct check, and via a repo-wide grep confirming they
  appear nowhere else in `data/content/` or `src/` (only in `blacksmith.py` itself and
  `material_predicate.py`'s own docstring, which cites them as the disclosed-limitation example).

  **Zero id, output-item, or output-item overlap exists between the two 14/25-entry sets** — this
  confirms the ticket's own "not simply the same data under different names" caution, but the
  direction of the finding settles the decision rather than complicating it: `BlacksmithSystem.
  RECIPES`'s 14 entries reference content that was **never actually authored** anywhere in this
  repo's real catalog. There is no real, functional content to "preserve" by keeping them as the
  `known_recipes` population source — they name items that could never be crafted meaningfully
  even if `craft_target` reachability were separately fixed (no real `ItemRegistry`/stat entry for
  the outputs, no real way to organically acquire the missing materials).

## Decision (see plan.md for the full recorded architecture decision)

**Option (a)** — migrate the wholesale-learn step's population source from `BlacksmithSystem.
RECIPES`'s private 14 ids to `registries.py::RecipeRegistry`'s real 25 ids — confirmed as the
right choice by the content-parity check above, not merely the smallest diff.

**Option (b)** (extend `registries.py` to include `BlacksmithSystem.RECIPES`'s 14 entries as
first-class catalog entries) is **rejected**: it would require inventing 13 new items and ~11 new
materials into the real catalog from nothing, since they don't exist today — directly conflicting
with this ticket's own Out of Scope ("resolve them by choosing one as canonical... not by
inventing new balance values"). Option (b) is not a smaller-scope alternative here; it is a
strictly larger, forbidden one.

## The bridge has two real ends, not one
`recipe_materials()` (`material_predicate.py`) itself reads a **fourth**, separate registry:
`src/core/recipes.py::RecipeRegistry` (legacy, 3 entries — `iron_sword`/`iron_shield`/
`health_potion`), per `TCK-20260904-MATERIAL-POSSESSION-PREDICATE`'s own explicit Acceptance
Criteria #2 at the time. That ticket's own docstring already disclosed this exact gap as a
"disclosed, accepted, pre-existing limitation" for a future ticket (this one) to close. Migrating
only the population side (`BlacksmithSystem`) without also redirecting the consumption side
(`recipe_materials()`) would leave the predicate reading a registry (`recipes.py`, 3 ids) that
overlaps with neither `BlacksmithSystem`'s old ids nor `registries.py`'s new ones — still fully
inert. Both ends must point at the same real registry (`registries.py::RecipeRegistry`) for the
bridge to actually close.

`RecipeDef` (`registries.py`) uses field name `requires_items` (not `materials`) and
`.get()`/`.contains()` (not `.get_recipe()` returning `None`-on-miss) — `recipe_materials()`'s
adaptation must account for both differences, not just swap the import.

## `src/core/recipes.py::RecipeRegistry`'s fate (ticket's own open question)
Confirmed zero real callers remain anywhere once `recipe_materials()` is redirected (its own
`get_recipe()` becomes fully unreferenced in `src/`). **Decision: leave it in place, undeleted.**
Removing a now-dead class is a separate, low-priority cleanup — this ticket's own scope is the
namespace bridge, not a dead-code sweep, and CLAUDE.md's own architecture discipline favors a
narrow, well-evidenced fix over incidental cleanup. Flagged in Completion Summary as a real,
disclosed follow-up opportunity, not silently left unstated.

## `BlacksmithSystem.RECIPES`'s own crafting-execution branch (lines 154-246 of blacksmith.py)
Stays completely untouched — it's a separate, deeper reachability gap (fixing `craft_target`
never being set by real AI) explicitly out of this ticket's scope (the Scope section is about the
namespace bridge and `recipe_materials()`'s reachability, not `BlacksmithSystem`'s own internal
crafting-execution mechanism). Flagged as a related, disclosed, out-of-scope finding, not silently
dropped.

## Real simulation verification plan
AC requires "a real simulation run (not a synthetic fixture) demonstrates an entity's
organically-learned `known_recipes` producing a non-empty result." Plan: construct a real `Kernel`
+ `AuthoritativeState` with one entity positioned on a real `blacksmith`-kind building tile and a
real recipe material in inventory (e.g. `iron_ore`, needed by `craft_iron_sword`), advance one real
tick, confirm (a) `BlacksmithSystem.enforce()`'s wholesale-learn branch populates
`entity.identity.known_recipes` with real `registries.py` ids, and (b)
`PossessionUnderstandingService.evaluate()` against that same post-tick entity produces a non-empty
`known_uses`/`craft_priority > 0` for `iron_ore` — mirrors
`test_information_intent_execution_fires_through_kernel_tick_once`'s existing "real kernel tick,
not hand-constructed" precedent in `tests/simulation_quality/test_grade_regression.py`.
