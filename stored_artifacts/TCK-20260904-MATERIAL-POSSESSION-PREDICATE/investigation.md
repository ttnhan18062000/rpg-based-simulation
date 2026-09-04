---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260904-MATERIAL-POSSESSION-PREDICATE
artifact_type: investigation
tags: [economy, progression, cognition]
---

# Investigation — TCK-20260904-MATERIAL-POSSESSION-PREDICATE

## Current Behavior

### `PossessionUnderstandingService` (`src/domains/progression/possession.py:18-117`)
Real, live, per-tick production code — Step 1 of the 6-step `ProgressionConversionPhase.execute()`
pipeline (`src/domains/progression/phase.py:54`, called for every active/alive entity every tick
this phase runs). `evaluate(entity, state) -> PossessionUnderstandingComponent` walks
`entity.inventory.items` and, for each `ItemStack`, assigns `keep_priority`/`sell_priority`/
`equip_priority`/`craft_priority`/`reason` via **hardcoded item-id checks**, not a real recipe
lookup:
- Line 53: `if item_id == "iron_ore" and "iron_sword" in known_recipes:`
- Line 60: `elif item_id == "wolf_fang" and "hunter_blade" in known_recipes:`
- Line 68: `is_weapon = item_id in ("iron_sword", "steel_sword", "rusted_sword")` (hardcoded weapon list)

These two hardcoded material/recipe pairs are a mock stand-in for a real "is this item a material
for a recipe I know" predicate — confirmed by the module docstring's own framing ("Evaluates
inventory items against known recipes ... Mock recipe lists for Phase 6 scenario needs", line 51).
No general lookup against `RecipeRegistry` exists anywhere in this file.

Output feeds `PossessionUnderstandingComponent` (`src/domains/progression/schema.py:43-49`),
consumed directly by `GrowthGapEvaluator.evaluate()` (`src/domains/progression/gaps.py:24`, called
at `phase.py:57`), which has **the identical mock-hardcoding defect**: its "Material Gap" check
(`gaps.py:67-86`) only ever checks `"iron_sword" in known_recipes` and `item_id == "iron_ore"` —
the same two literals, not a real per-recipe scan. `GrowthGapEvaluator`'s output flows on to
`RewardInterpretationService` → `ConversionOptionGenerator` → `ConversionDecisionService` →
`ConversionIntentResolver`, which produces a real, authoritative `StateUpdate`/`EntityUpdate`
applied every tick (`phase.py:73-90`) — this is a genuine, already-live production consumer chain,
not test-only scaffolding.

### The two `RecipeRegistry` classes (both directly re-verified against source)
1. **`src/core/recipes.py:15-48`** — hardcoded, 3 entries (`iron_sword`, `iron_shield`,
   `health_potion`). `Recipe` dataclass has `materials: Dict[str, int]`. `get_recipe(recipe_id) ->
   Optional[Recipe]` (returns `None` on miss, never raises) and `get_all()`. **This is the live
   crafting-execution path**: imported and read by
   `src/systems/economy_systems/crafting.py:4,24` (`CraftingSystem.craft()`, gate 1 of the 7-gate
   sequence the Mechanics Bible / `docs/mechanics/resource_conservation_contract.md` documents) and
   `src/town/blacksmith.py:5,28` (`BlacksmithService.craft_item()`). Both call sites read
   `recipe.materials` directly.
2. **`src/core/registries.py:129-148`** — catalog-bootstrapped, `RecipeDef` dataclass has
   `requires_items: Dict[str, int]` (different field name than `Recipe.materials`).
   `RecipeRegistry.bootstrap(data)` is called from `src/runtime/bootstrap.py:109,151` and from
   `src/core/registries.py:609/700-704` with **richer, place-tied content** —
   `"hunter_blade": RecipeDef("hunter_blade", {"iron_ore": 2, "beast_fang": 1, "moon_resin": 1}, ...)`
   at `registries.py:701` already includes exactly the `beast_fang`/`moon_resin` place-tied
   materials idea 49 wants to gate crafting on. `get(recipe_id)` **raises `KeyError`** on miss
   (`registries.py:139`), unlike `recipes.py`'s `None` return — a real behavioral asymmetry between
   the two classes, not just a naming collision. **CORRECTED below** (see "A second correction"
   subsection further down, added post architecture-review): this class has **two** production
   readers, not one — `action_intent.py:9,72-77`'s pre-flight `Requirement`-building use (as
   originally found here) **and** `action_intent.py:192-215`'s `REQUEST_CRAFT` execution branch,
   which **does** authoritatively commit a `ResourceTransferIntent`. The claim in this original
   paragraph that "it never authoritatively executes a craft" and that "the actual craft execution
   ... still routes to `CraftingSystem`/`BlacksmithService`" is **incorrect** — re-traced below;
   `CraftingSystem`/`BlacksmithService` in fact have zero production callers of their own. **This is a
   real, pre-existing, disclosed inconsistency** (registries.py's richer 25-entry catalog, per
   `docs/parity_ledger/town_resource.yaml:1805-1817`, is bootstrapped and used only for
   pre-validation, while the actual 3-recipe hardcoded `recipes.py` registry is what really executes
   and what `PossessionUnderstandingService`/`GrowthGapEvaluator` would need to read from) — out of
   scope to fix here (ticket's own Out of Scope explicitly forbids touching
   `registries.py::RecipeRegistry` or its consumers), but the predicate's own docstring/comment must
   name `src/core/recipes.py::RecipeRegistry` explicitly, per the ticket's Acceptance Criteria, to
   avoid a future implementer defaulting to the richer-looking `registries.py` one for material
   lookups and silently changing which recipes govern the predicate's yes/no answer.

### The THIRD recipe catalog: `BlacksmithSystem.RECIPES` — the actual live `known_recipes` populator (re-investigation finding, added post architecture-review NEEDS_CHANGES)

**This is the load-bearing finding this section exists to document.** A prior version of this
investigation traced only the two `RecipeRegistry`-named classes and concluded `recipes.py` was
"the live crafting-execution path" because it is imported by `CraftingSystem.craft()` and
`BlacksmithService.craft_item()`. That conclusion never traced **how `entity.identity.known_recipes`
itself actually gets populated** in the live authoritative pipeline — a gap the architecture-reviewer
caught. Re-traced directly, verbatim from source:

- `src/engine/pipeline.py:223`: `update = run_phase("blacksmith", update, lambda u:
  BlacksmithSystem.enforce(state, u))` — **no feature-flag gate**; this runs unconditionally every
  tick as Phase 2 of `AuthoritativeApplyPipeline`.
- `src/engine/blacksmith.py:13-18`: `V2Recipe` dataclass — `recipe_id: str`, `output_item: str`,
  `gold_cost: int`, `materials: Dict[str, int]`. **Same field name and shape as
  `recipes.py::Recipe.materials`** — a predicate reading `.materials` works identically against
  either dataclass; this is not a structural obstacle, only a catalog-membership one.
- `src/engine/blacksmith.py:27-112`: `BlacksmithSystem.RECIPES` — 14 entries, **all `craft_*`-prefixed**
  (`craft_steel_sword`, `craft_battle_axe`, `craft_enchanted_blade`, `craft_iron_plate`,
  `craft_enchanted_robe`, `craft_ring_of_power`, `craft_evasion_amulet`, `craft_wolf_cloak`,
  `craft_fang_necklace`, `craft_desert_bow`, `craft_bone_shield`, `craft_spectral_blade`,
  `craft_mountain_plate`, `craft_herbal_remedy`). **Zero overlap** with `recipes.py::RecipeRegistry`'s
  3 entries (`iron_sword`, `iron_shield`, `health_potion`).
- `src/engine/blacksmith.py:139-151`: when an entity with **empty** `known_recipes` occupies a
  `blacksmith` building tile, it **wholesale-learns** `all_recipes =
  list(BlacksmithSystem.RECIPES.keys())` — the 14 `craft_*` ids — via
  `IdentityUpdate(recipes_learned=all_recipes)`, which flows through `src/engine/patches.py:191,210,240`
  (`rec |= set(u_id.recipes_learned)`) into the authoritative `known_recipes` set.
- `src/engine/blacksmith.py:154-246`: **also a live crafting-execution path**, independent of
  `CraftingSystem`/`BlacksmithService`. If `entity.identity.craft_target` names a
  `BlacksmithSystem.RECIPES` id, it gates on `craft_target not in entity.identity.known_recipes`
  (line 173, the actual live "does this entity know a recipe" check — not `recipes.py`'s), checks
  gold (line 178), scans `recipe.materials.items()` against live inventory (lines 188-193, the actual
  live "does this entity possess the material" check), and on success builds a real
  `ResourceTransferIntent` (lines 205-218) that is queued into `EntityUpdate.resource_transfers` —
  a genuine, authoritative, applied durable change, via the exact same conservation-resolver
  mechanism `docs/mechanics/resource_conservation_contract.md`'s crafting-atomicity gates describe.

**Full grep of every writer of `known_recipes`/`recipes_learned` repo-wide** (`grep -rn
"recipes_learned\|known_recipes" src/`) confirms `src/engine/blacksmith.py:145` is the **only**
confirmed-live, unconditionally-wired production writer that populates `known_recipes` in bulk. One
other theoretical writer exists — `src/engine/domain/core_actions.py:384`
(`CoreActions.execute_train()`, dispatched from `action_router.py:58-59` on a `"TRAIN"` action,
itself a peer-to-peer "TEACH" contract mechanic) sets `IdentityUpdate(recipes_learned=[skill_id])`
where `skill_id` comes from `payload.get("skill_id")` and is checked only against `capability`-kind
blockers (`core_actions.py:373-375`). No repo-wide occurrence of a production code path constructing
a `"TRAIN"` action intent with `skill_id` set to any `recipes.py`/`registries.py`-style recipe id was
found (the only confirmed `capability`-blocker producer, `src/engine/pipeline_phases/actions.py:158`,
sets `subject=reason_value` from a navigation-failure reason code, unrelated to crafting). This path
is not a confirmed recipe-namespace writer either way — noted for completeness, not relied upon.

**Consequence, stated plainly:** for any entity whose `known_recipes` was populated through the real,
live, unconditionally-wired `BlacksmithSystem.enforce()` pipeline — which is the *only* confirmed
production wholesale-learning path today — a predicate that answers `recipe_materials(recipe_id)` by
reading `recipes.py::RecipeRegistry` will return `()` for every member of that entity's
`known_recipes`, because none of the 14 `craft_*` ids exist in `recipes.py`'s 3-entry catalog. See
"Risks and Open Questions" below for how this ticket's plan discloses and handles this.

### A necessary correction: `recipes.py::RecipeRegistry`'s other two claimed "production consumers"
have **zero production callers**, repo-wide

Re-verified by grepping every call site of `CraftingSystem.craft(`, `BlacksmithService.craft_item(`,
and `BlacksmithAction.craft(` across `src/` **and** `tests/`:
- `CraftingSystem.craft()` (`src/systems/economy_systems/crafting.py:14`): the only two call sites in
  the entire repo are `tests/unit/quest/test_progression_lifecycle.py:75,90`. A comment at
  `src/engine/intent/action_intent.py:196-198` confirms this is intentional: "do not call
  `CraftingSystem.craft()` directly, it bypasses that authoritative path."
- `BlacksmithService.craft_item()` (`src/town/blacksmith.py:12`): its only caller is
  `BlacksmithAction.craft()` (`blacksmith.py:71`, itself explicitly docstringed "Action wrapper for
  economy tests"), whose only callers are `tests/unit/world/test_economy_contract.py:76,88`.

So `recipes.py::RecipeRegistry` is, strictly, **not invoked by any live production code path today at
all** — a stronger and more precise finding than this investigation's earlier draft, which
characterized it as "the live crafting-execution path" on the basis of being *imported* by
production-looking function signatures. Being imported by a function that itself has zero production
callers does not make a registry "live." This does not change the ticket's own binding requirement
(the ticket's AC #2 and Related Code Areas text explicitly and literally name
`src/core/recipes.py::RecipeRegistry` as the class the predicate must read through — a decision
already made in the ticket body itself, not something investigation/planning inferred), but it
sharpens exactly what is and is not true about that requirement's premise.

### A second correction: `registries.py::RecipeRegistry` **is** read by a genuine live production
execution path (contrary to the earlier "pre-flight-only" characterization)

Traced the full chain: `ObjectiveIntentResolver.resolve()` (`src/domains/adventure/resolver.py:52-53`)
maps `ObjectiveKind.ACQUIRE_ITEM` to `ActionIntent(kind="REQUEST_CRAFT", ...)`. This reaches
`ActionIntentAdapter.execute()`'s `REQUEST_CRAFT` branch at `src/engine/intent/action_intent.py:192-215`,
which does `recipe = RecipeRegistry.get(recipe_id)` (imported at `action_intent.py:9` — this file
imports `from src.core.registries import RecipeRegistry`, the catalog-bootstrapped class, **not**
`recipes.py`'s) and `materials = [... for mat, count in recipe.requires_items.items()]`, then builds
and returns a real `ResourceTransferIntent` in `EntityUpdate.resource_transfers` — this **is** a
durable, authoritative commit, not merely a pre-flight `Requirement` object as the earlier draft
claimed. The `recipe_id` values this branch receives originate from
`ServiceOpportunityProvider.get_opportunities()` (`src/world/providers/services.py:61-70`), which
iterates `RecipeRegistry.all()` (same `registries.py` class) and emits
`Opportunity(id=f"opp_craft_{recipe_id}", ..., requirements=(Requirement(kind="recipe_known",
subject=recipe_id), ...))` — i.e. this path **does** check `entity.identity.known_recipes` as a
pre-flight eligibility gate (`src/world/providers/requirements.py:196-197`), using
`registries.py`-style recipe ids (e.g. `"iron_sword"`, `"hunter_blade"`, `"small_potion"` in the
QUARANTINED fallback catalog at `registries.py:697-702`, or the richer catalog-bootstrapped set in
normal `CATALOG` mode).

This means the true live picture has **three**, not two, disjoint-or-partially-overlapping recipe
systems, each with a different practical reachability profile — not one "live" and one "dead" class:

| Class | Entries | Confirmed live production execution? | Confirmed live production reader of `known_recipes`? |
|---|---|---|---|
| `src/core/recipes.py::RecipeRegistry` | 3 (`iron_sword`, `iron_shield`, `health_potion`) | **No** — zero non-test callers of either consumer | No (only the mock literals in `possession.py`/`gaps.py` this ticket is fixing) |
| `src/core/registries.py::RecipeRegistry` | up to 25 (catalog) / 3 (fallback) | **Yes** — `action_intent.py`'s `REQUEST_CRAFT` branch | Yes — `recipe_known` Requirement check, but only ever matched against whatever is actually in `known_recipes` (see below) |
| `src/engine/blacksmith.py::BlacksmithSystem.RECIPES` | 14 (`craft_*`) | **Yes** — `enforce()`'s craft-target branch | **Yes — and the only confirmed writer of `known_recipes`** |

Because `BlacksmithSystem.enforce()` is the only confirmed production writer of `known_recipes`, and
it writes exclusively `craft_*` ids, the `registries.py` path's own `recipe_known` Requirement check
(against non-`craft_*` ids like `"iron_sword"`/`"hunter_blade"`) is **itself** in the same practical
situation as `recipes.py`'s — reachable code, correct logic, but not currently exercised by any
organically-populated `known_recipes` set either. This is a genuinely repo-wide, pre-existing
namespace fragmentation across all three catalogs, not a defect specific to `recipes.py` or to this
ticket's chosen registry. See "Risks and Open Questions" for how this changes (and does not change)
the plan.

### `AmbitionProfile` (`src/core/cognition.py:399-405`)
Confirmed real, frozen dataclass:
```python
class AmbitionProfile:
    """Future strategic objectives goals."""
    strategic_value_targets: Tuple[str, ...] = ()
```
`MotivationModel.ambition: AmbitionProfile = field(default_factory=AmbitionProfile)`
(`cognition.py:423`). A full-repo grep of `strategic_value_targets` and `AmbitionProfile` finds
**zero production reads or non-default production constructions anywhere in `src/`** — the only
two hits for `strategic_value_targets` are the field declaration itself and its own
`to_canonical_dict()` serializer (`cognition.py:402,405`). This is a genuinely distinct dead field
from the one `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK` documented (`ValuePreferenceProfile.
material_ambition`, a field that ticket explicitly deferred and never created) — `AmbitionProfile`
already exists in `src/`, unlike `material_ambition`, but shares the exact same dead-on-arrival
*pattern*: populated-but-never-read.

### The `GoalScorer` wrapper pattern (established, low-risk, well-precedented)
`src/ai/goals/base.py` defines `GoalScorer` (Protocol, one `score(entity, state) -> GoalScore`
method) and `GoalRegistry` (class-level dict, `register(kind, scorer)`,
`get_all_scores(entity, state)` — deterministic, sorted-key iteration). Four scorers already follow
this pattern end-to-end in production: `AdventureGoalScorer`, `SocialContractGoalScorer`,
`RegionStabilizationGoalScorer`, `OccupationChangeGoalScorer` — all registered in
`src/ai/goals/__init__.py:14-27`, all documented in `docs/mechanics/04_strategic_cognition.md`
§1/§2/§2a. Adding a brand-new `GoalKind` consumer is **not small**: per
`OccupationChangeGoalScorer`'s own precedent (`TCK-20260824-OCCUPATION-CHANGE-TRIGGER`), a full new
`GoalKind` requires a new enum member (`src/core/strategic.py`, with an explicit tie-break-order
comment), the scorer class, `GoalRegistry` registration, **and** a dedicated materialization
`elif` branch in `StrategicIntelligenceSystem.evaluate_strategic_intent()`
(`src/systems/strategic_systems/intelligence.py`), plus (if it should actually commit a durable
change) `ObjectiveKind`/`ProjectKind` entries and resolver/intent-adapter branches. That is a
materially larger lift than this ticket's own scope (a shared predicate + one production wiring
point), and risks scope creep into idea 51/52's territory (explicitly Out of Scope here).

### `OccupationChangeGoalScorer` (`src/ai/goals/occupation_change_scorer.py`) — reviewed for pattern only
Confirmed real and live (`GoalKind.OCCUPATION_CHANGE`, registered `__init__.py:27`) but is a
**structurally unrelated** goal (civilian occupation slot-filling by region headcount/aptitude, not
material possession) — not a natural host for this predicate's output, only useful here as the
canonical "how a new small GoalScorer gets wired" reference implementation.

## Mechanics / Engine Constraints
- `docs/mechanics/03_economic_laws.md` §5 "Industry: Crafting & Conversion" (lines 120-127) states
  crafting requirements as "Recipe Materials: the exact item counts specified" — the predicate must
  answer against the *live* recipe materials (`recipes.py::RecipeRegistry.Recipe.materials`), not
  invent a parallel notion of "material requirement."
- `docs/mechanics/resource_conservation_contract.md` "Crafting Atomicity" documents
  `CraftingSystem`'s 7 sequential gates, gate 1 being "Recipe known in `RecipeRegistry`" — this is
  the authoritative crafting-atomicity law the predicate must not bypass or duplicate; the predicate
  is a *read-only* possession/consumption query, not a new crafting gate.
- `docs/simulation/domains/progression_contract.md` §"The 6-Step Pipeline", Step 1 (lines 98-100)
  documents `PossessionUnderstandingService.evaluate()`'s current (hardcoded-mock) behavior — this
  is the doc that goes stale the moment the predicate generalizes the hardcoded item-id checks into
  a real `RecipeRegistry`-backed lookup.
- `docs/mechanics/04_strategic_cognition.md` §1 "Goal Hierarchy & Prioritization" and its "Live
  tier-5 candidates" paragraph (lines 15-30) is the authoritative, actively-maintained list of every
  registered `GoalScorer` — any new `GoalKind`/`GoalScorer` this ticket adds must be reflected here,
  matching the exact citation style already used for `OccupationChangeGoalScorer`.
- CLAUDE.md Strategic/Tactical Rule: "Do not solve strategic problems by stacking more tactical
  goal scoring." A brand-new `GoalKind`/materialization branch for a still-narrow "does entity have
  material X" signal risks exactly this — the Anti-Drift Hazards section below flags this
  explicitly.

## Docs Requiring Update

- `docs/simulation/domains/progression_contract.md`: Step 1's description (lines 98-100) states
  `PossessionUnderstandingService.evaluate()` only evaluates "current inventory and equipment
  state" via a possession snapshot — if the predicate generalizes the hardcoded `iron_ore`/
  `wolf_fang` checks into a real `RecipeRegistry`-backed material-possession/consumption predicate
  (per this ticket's own Scope), this description must be updated to describe the new,
  RecipeRegistry-driven behavior, not the old two-literal mock.
- `docs/parity_ledger/progression.yaml`: no existing entry for `PossessionUnderstandingService` or
  `GrowthGapEvaluator`'s material-gap check exists in this file (confirmed via grep — zero hits for
  `PossessionUnderstanding`/`GrowthGap`/`possession` in `docs/parity_ledger/progression.yaml`). Per
  the Authoritative Mechanics Rule ("If no entry exists, add one"), this ticket's behavior change to
  `possession.py` (and possibly `gaps.py`) requires a new entry here.
- `docs/mechanics/04_strategic_cognition.md` (§1 Goal Hierarchy table + "Live tier-5 candidates"
  paragraph, lines ~15-30): **only if** the implementer chooses the new-`GoalScorer`/`GoalKind`
  route for AmbitionProfile's production read site (see Risks below) — a new scorer must be added
  to this table/paragraph exactly like `OccupationChangeGoalScorer` was. **Resolved during
  implementation, condition not met** should be added to this bullet's own text if the implementer
  instead wires the predicate/AmbitionProfile through the existing
  `GrowthGapEvaluator`/`ConversionOptionGenerator` pipeline (no new `GoalKind`), per
  `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`'s resolution convention.
- `docs/parity_ledger/strategic_cognition.yaml`: **only if** the new-`GoalScorer` route above is
  taken (a new `GoalKind` registration is exactly the kind of behavior change every prior
  `*-GOAL-SCORER` ticket recorded here, e.g. `STRAT-254`/`STRAT-255` for the social-contract/
  region-stabilization scorers). **Resolved during implementation, condition not met** — Route A
  (extending the existing `PossessionUnderstandingService`/`GrowthGapEvaluator` chain) was adopted
  instead of a new `GoalScorer`/`GoalKind`, so no `strategic_cognition.yaml` entry was required and
  this file was correctly left untouched, matching the sibling `04_strategic_cognition.md` bullet's
  own resolution above.

The `docs/mechanics/03_economic_laws.md` §5 crafting section (path:
`docs/mechanics/03_economic_laws.md`) is not required to change for this ticket: it states
crafting requirements in general terms (recipe materials, gold cost, station) and does not name
either `RecipeRegistry` class or `PossessionUnderstandingService`; this ticket does not change
crafting's gold/material/atomicity behavior, only adds a read-only possession predicate, so this
section's text remains accurate as written.

The `docs/mechanics/resource_conservation_contract.md` "Crafting Atomicity" section (path:
`docs/mechanics/resource_conservation_contract.md`) is not required to change either: the 7-gate
sequence it documents is `CraftingSystem.craft()`'s real behavior, unchanged by this ticket (the
predicate is a separate, read-only query, not a new or modified crafting gate).

## Parity Ledger Overlap
- `docs/parity_ledger/town_resource.yaml`, entries around lines 1805-1817 (`Crafting recipe catalog
  has >= 25 entries...`, `v2_evidence: data/content/world/recipes.yaml`, `test_path:
  tests/unit/content/test_recipe_catalog_expansion.py::test_gather_craft_chain_iron_to_steel`) —
  this entry documents the `registries.py`-side catalog (25 entries) that this ticket must
  explicitly *not* read through. Confirmed the entry's own text does not claim this catalog is the
  live crafting path, so no correction is needed there, but a future reader could conflate the two
  — worth a cross-reference note if the implementer touches this file at all (not required by this
  ticket's own scope).
- `docs/parity_ledger/town_resource.yaml:195,318-319` (`Blacksmith visits resolve recipe/
  crafting/material-gating behavior`, `test_visit_blacksmith_crafting_resolution`) — regression
  surface for the live `recipes.py`-backed crafting path; not owned by this ticket but must not
  regress (`tests/unit/world/test_economy_contract.py::test_blacksmith_crafting` is the closer,
  more direct unit-level equivalent — see Test Plan).
- No P0 entries were found touching `PossessionUnderstandingService`, `GrowthGapEvaluator`, or
  `AmbitionProfile` in any parity ledger file (grepped `docs/parity_ledger/*.yaml` for
  `PossessionUnderstanding`/`AmbitionProfile` — zero hits). No P0 test_path obligation applies.

## Prior Work
- `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK` (`stored_artifacts/`, done) — the prior, adjacent
  dead-on-arrival finding this ticket's Assumptions section cites. Confirmed it is about a
  *different* field (`ValuePreferenceProfile.material_ambition`, never created) than
  `AmbitionProfile.strategic_value_targets` (which does exist in `src/`, just unread) — same defect
  pattern, different concrete field. Its own Target Design Sketch is explicitly deferred/blocked on
  a separate `MotivationModel.values` foundation ticket that still does not exist; that blocker does
  **not** apply to `AmbitionProfile.ambition`, a structurally separate `MotivationModel` sub-field
  with no such dependency.
- `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` (done) — the canonical, fully-worked reference for what
  a complete new `GoalKind`/`GoalScorer` wiring costs (enum member, scorer, registration,
  materialization branch, resolver/intent-adapter changes). Directly informs the Risks section's
  recommendation against a new `GoalKind` unless genuinely warranted.
- `TCK-20260811-ADVENTURE-GOAL-SCORER`, `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`,
  `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER` (all done) — the `GoalScorer`-wrapper pattern
  precedents; `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
  "Future Extension Patterns" section documents the pattern's intended generalization and both
  landed follow-ons.
- `TCK-20260619-E13C-RECIPES` (done) — populated the 25-entry `data/content/world/recipes.yaml`
  catalog that bootstraps `registries.py::RecipeRegistry` (not the live path); relevant only as
  context for why that class looks more "real"/content-rich than the live one.
- No stored artifact anywhere references `PossessionUnderstandingService`, `AmbitionProfile`, or a
  prior "material possession predicate" attempt — this is confirmed new ground, not a re-do.

## Risks and Open Questions
- **Resolved (not left open): the predicate must still read `recipes.py::RecipeRegistry`, per the
  ticket's own explicit, already-fixed AC text — the newly-discovered `BlacksmithSystem.RECIPES`
  namespace mismatch is accepted as a disclosed, pre-existing, separately-tracked limitation, not a
  reason to switch registries.** The ticket body (not this investigation) already names
  `src/core/recipes.py::RecipeRegistry` explicitly in both its Request Summary and Acceptance
  Criteria #2 ("The predicate's implementation and its tests explicitly reference
  `src/core/recipes.py::RecipeRegistry` (not `src/core/registries.py::RecipeRegistry`)") and its Out
  of Scope ("Rewriting or renaming either existing `RecipeRegistry` class — only explicit selection
  of which one the new predicate uses"). That selection was made by the ticket author before this
  investigation began; planning/investigation is not positioned to unilaterally override it — doing
  so would also not resolve the underlying fragmentation, since (per the corrected finding above)
  `registries.py::RecipeRegistry` has the exact same practical non-reachability problem against
  organically-populated `known_recipes` today (both non-`craft_*` catalogs are equally unreachable
  from `BlacksmithSystem`-learned recipes). Switching to `BlacksmithSystem.RECIPES` itself is also
  not a clean fix: it is not a `RecipeRegistry`-shaped class at all (no `RecipeRegistry.get_recipe()`/
  `.get()` classmethod, just a plain dict on `BlacksmithSystem`), reading it here would require the
  predicate to import from `src/engine/blacksmith.py` (an engine-pipeline module) into
  `src/domains/progression/`, a layering direction not otherwise present in this domain, and it would
  directly contradict the ticket's own AC #2, which requires the predicate's tests to assert
  *against* `registries.py::RecipeRegistry`-style substitution, not perform the equivalent
  substitution with a third class instead. The correct resolution is: implement exactly as the
  ticket specifies (predicate reads `recipes.py::RecipeRegistry`), disclose the namespace-mismatch
  limitation explicitly in `plan.md`'s Anti-Drift Notes with full evidence, and recommend (not build)
  a follow-up ticket to bridge the gap. See `plan.md`'s Anti-Drift Notes for the full disclosure and
  the recommended follow-up ticket sketch.
- **Open question (blocks a specific implementation choice, not the ticket itself): which
  production consumer should the predicate wire to?** Two real, verified candidates, with a
  recommendation:
  1. **Recommended — extend the existing `PossessionUnderstandingService`/`GrowthGapEvaluator`
     production chain directly.** Both are already real, live, per-tick consumers
     (`ProgressionConversionPhase`, applied every tick via a genuine `StateUpdate`). Their current
     "material gap"/"recipe material" logic is hardcoded to two literal item ids
     (`iron_ore`/`iron_sword`, `wolf_fang`/`hunter_blade` in `possession.py`; `iron_ore`/
     `iron_sword` again in `gaps.py`) — replacing those hardcoded checks with the shared predicate
     querying `recipes.py::RecipeRegistry.get_recipe()` generically satisfies AC's "real production
     consumer" requirement with no new `GoalKind`/materialization machinery, and does not require
     touching `AmbitionProfile` at all (the AC's AmbitionProfile-wiring clause is explicitly
     conditional — "if it feeds AmbitionProfile").
  2. **Alternative — route through `AmbitionProfile.strategic_value_targets`.** Populate it (e.g.
     from `possession.py` or a new small step) with material ids the entity currently lacks but
     ambitiously wants (matching the class's own docstring, "Future strategic objectives goals"),
     then wire a real read site. The cheapest real read site is **not** a new `GoalScorer` — that
     is the materially larger lift documented above under "Mechanics / Engine Constraints" — but
     reading it inside the existing `GrowthGapEvaluator.evaluate()` (already per-entity, per-tick,
     already reads `entity.identity`/possession state) to bias `severity`/`candidate_resolution_
     tags` for the gaps it already generates. This still counts as a genuine "AmbitionProfile ...
     production behavior changes based on the predicate's output" per the AC, without a new
     `GoalKind`.
  This choice determines which docs bullets above are conditional (see "Resolved during
  implementation, condition not met" markers) — the planner must pick one and both `plan.md` and
  the eventual `investigation.md` state should stay consistent with whichever is chosen. This is a
  design decision, not something this investigation should collapse to a guess (Uncertainty Rule).
- **Confirmed real inconsistency, not a blocker but worth disclosing again to the implementer**:
  `registries.py::RecipeRegistry` is bootstrapped from a genuinely richer, place-tied 25-entry
  catalog (including exactly the `beast_fang`/`moon_resin` materials idea 49 wants) but is read only
  for pre-flight `Requirement` validation in `action_intent.py`, never for actual execution. If a
  future idea-49 ticket extends `recipes.py` (the live 3-entry registry) with place-tied materials,
  it will need to duplicate content that already exists in `registries.py`'s catalog rather than
  being able to reuse it directly — a real content-duplication cost the atlas doc doesn't currently
  surface. Flagged here since this ticket's own predicate is the first piece of new code to read
  `recipes.py::RecipeRegistry` for a non-crafting-execution purpose.
- `recipes.py::RecipeRegistry.get_recipe()` returns `None` on a miss;
  `registries.py::RecipeRegistry.get()` raises `KeyError`. Since the ticket mandates the `recipes.py`
  class specifically, the predicate's "failure mode" (unregistered material) is a `None`-return
  case, not an exception — test_plan below is written against this confirmed behavior.
- Idea 52 (`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) operates at Faction/Country scale, not
  per-entity — confirmed via `docs/brainstorm/rpg_feature_atlas.html` idea 51/52 text
  (`FactionDecisionPhase.execute()`, faction-level `military_strength`/`tension_level` gates). The
  predicate this ticket produces is entity-scoped (`entity, material_id, state -> bool/float`); for
  idea 52 to reuse it later, that ticket will need its own faction-level wrapper (e.g. iterate
  member entities) — this ticket does not need to build that wrapper (Out of Scope confirms), but
  the predicate's signature should stay a plain, entity-scoped, side-effect-free function/staticmethod
  so such a wrapper is trivial later, not something requiring a redesign.

## Anti-Drift Hazards
- Do not let "wire to a real production consumer" balloon into implementing idea 49 (extending
  `recipes.py` with new place-tied recipes) or idea 50 (the material-gated evolution branch in
  `src/engine/evolution.py::EvolutionSystem.evaluate()`) — both are confirmed real, live extension
  points (re-verified: `EvolutionSystem.evaluate()` is purely XP-driven today, no material check
  anywhere in it), but actually building either feature is out of this ticket's scope; the ticket
  only needs the shared predicate wired to *a* real consumer, not the full idea-49/50 feature.
- Do not silently substitute `registries.py::RecipeRegistry` for `recipes.py::RecipeRegistry`
  because the former's content looks richer/more "real" (it is genuinely richer — 25 bootstrapped
  entries vs. 3 hardcoded — but it is not the live crafting-execution path, and the ticket's Out of
  Scope explicitly forbids touching it or its consumers).
- Do not introduce a third confusably-named class (e.g. another `*RecipeRegistry`,
  `*PossessionService`, or `*PossessionPredicate` that could be mistaken for either existing
  registry or `PossessionUnderstandingService` itself) — the ticket's own AC requires avoiding this.
- Do not build a brand-new `GoalKind`/`GoalScorer`/materialization-branch chain for `AmbitionProfile`
  unless the recommended lighter-weight route (extending `GrowthGapEvaluator`) is genuinely
  insufficient — see Risks above; this is the CLAUDE.md Strategic/Tactical Rule's "don't solve
  strategic problems by stacking more tactical goal scoring" made concrete for this ticket.
- Do not touch `MotivationModel.values`/`ValuePreferenceProfile` (the *other*, still-blocked
  dead-on-arrival field from `TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`) — that ticket's blocker
  is unrelated and still unresolved; conflating the two "ambition"-flavored fields would be a scope
  error.
- `CraftingSystem.craft()`'s 7-gate sequence and `BlacksmithService.craft_item()` must not be
  modified by this ticket — the predicate is read-only and additive; regression tests in the Test
  Plan below exist specifically to catch an accidental change to either.
- **Do not treat the `BlacksmithSystem.RECIPES`/`known_recipes` namespace mismatch (see "The THIRD
  recipe catalog" finding above) as something this ticket must fix.** The predicate correctly and
  generically reads `recipes.py::RecipeRegistry` per the ticket's own explicit AC; the fact that
  `BlacksmithSystem.enforce()` (the only confirmed live wholesale writer of `known_recipes`) never
  writes `recipes.py`-style ids is a pre-existing architecture fragmentation across three separate
  recipe catalogs, not a defect this ticket introduces or is scoped to close. Do not silently expand
  scope to read `BlacksmithSystem.RECIPES` instead — see "Risks and Open Questions" for why that
  would also violate the ticket's own AC #2 and would not actually fix the fragmentation (
  `registries.py`'s catalog has the identical non-reachability problem). Disclose it; do not patch
  around it.
