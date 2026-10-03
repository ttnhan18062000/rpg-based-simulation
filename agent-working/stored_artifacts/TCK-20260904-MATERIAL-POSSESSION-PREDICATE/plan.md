---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260904-MATERIAL-POSSESSION-PREDICATE
artifact_type: plan
tags: [economy, progression, cognition]
---

# Implementation Plan — TCK-20260904-MATERIAL-POSSESSION-PREDICATE

## Summary

**Architecture decision (adopted, not left open): Route A — extend the existing
`PossessionUnderstandingService`/`GrowthGapEvaluator` production chain.** This plan does **not**
build a new `GoalKind`/`GoalScorer` for `AmbitionProfile`. `AmbitionProfile` remains untouched and
stays dead code after this ticket (see Anti-Drift Notes) — this is a deliberate, disclosed scope
decision, not an oversight, because the ticket's "wire to a real production consumer" requirement
is fully satisfied by extending the already-live, per-tick `ProgressionConversionPhase` chain
instead (`src/domains/progression/phase.py:54,57` — confirmed live, calls
`PossessionUnderstandingService.evaluate()` then `GrowthGapEvaluator.evaluate()` for every
active/alive entity every tick this phase runs; output flows into a genuine, applied `StateUpdate`
at `phase.py:73-95`). A new `GoalKind` would be a materially larger, unjustified lift per
`investigation.md`'s "GoalScorer wrapper pattern" analysis and would violate CLAUDE.md's
Strategic/Tactical Rule ("do not solve strategic problems by stacking more tactical goal
scoring").

**Second architecture decision, made in response to architecture-reviewer's NEEDS_CHANGES verdict
on the prior version of this plan — Option (a) adopted, not (b):** the predicate reads exclusively
through `src/core/recipes.py::RecipeRegistry`, exactly as the ticket's own Acceptance Criteria #2
and Related Code Areas explicitly and literally mandate ("The predicate's implementation and its
tests explicitly reference `src/core/recipes.py::RecipeRegistry` (not
`src/core/registries.py::RecipeRegistry`)"). Re-investigation (see `investigation.md`'s "The THIRD
recipe catalog" and its two correction subsections, added post-review) confirmed a third,
disjoint, `craft_*`-prefixed recipe namespace — `src/engine/blacksmith.py::BlacksmithSystem.RECIPES`
(14 entries) — governs the **only confirmed live production writer** of
`entity.identity.known_recipes` (`BlacksmithSystem.enforce()`, unconditionally wired at
`src/engine/pipeline.py:223`, wholesale-learns all 14 `craft_*` ids the first time an entity with
empty `known_recipes` stands on a blacksmith tile — `blacksmith.py:139-151`). None of those 14 ids
overlap with `recipes.py::RecipeRegistry`'s 3 (`iron_sword`, `iron_shield`, `health_potion`).
**Consequence, disclosed explicitly, not hidden:** this predicate will return `()` for every recipe
id in a `known_recipes` set that was populated the one confirmed-live way it actually gets
populated in production today — the predicate is correctly generalized, pure, and tested against
`recipes.py`'s real 3-entry catalog, but its practical hit-rate against organically-populated
`known_recipes` state is currently zero. This is accepted as a **pre-existing, disclosed,
separately-tracked limitation** — not a defect this ticket introduces, and not something switching
registries would actually fix (re-investigation also found `registries.py::RecipeRegistry`, the
*other* candidate, has the identical non-reachability problem against `craft_*`-populated
`known_recipes` — see investigation.md's three-way comparison table). Full evidence, the "why not
switch" reasoning, and a recommended (not built) follow-up ticket sketch are in Anti-Drift Notes
below.

The approach otherwise is unchanged from the prior plan: add exactly **one** new, small, pure,
side-effect-free predicate function — `recipe_materials(recipe_id) -> Tuple[str, ...]` — in a new
module, `src/domains/progression/material_predicate.py`, that reads exclusively through
`src/core/recipes.py::RecipeRegistry.get_recipe(recipe_id).materials` (confirmed live registry
*class* — though, per the re-investigation, not itself an invoked production execution path today;
see Anti-Drift Notes — `src/core/recipes.py:15-48`). Both `PossessionUnderstandingService.evaluate()`
(`src/domains/progression/possession.py:50-65`) and `GrowthGapEvaluator.evaluate()`
(`src/domains/progression/gaps.py:67-88`) are edited to build on this single function in place of
their current hardcoded two-literal mocks (`iron_ore`/`iron_sword`, `wolf_fang`/`hunter_blade` in
`possession.py`; `iron_sword`/`iron_ore` again in `gaps.py`), generalizing coverage to all three
real `recipes.py::RecipeRegistry` entries (`iron_sword`, `iron_shield`, `health_potion`) instead
of two hardcoded pairs. `src/core/registries.py::RecipeRegistry` and
`src/engine/blacksmith.py::BlacksmithSystem.RECIPES` are never read by the new predicate or by
either edited call site — this is a disclosed, intentional scope boundary matching the ticket's own
explicit AC, not an oversight (see Anti-Drift Notes).

## Steps

### Step 1 — Add the shared `recipe_materials()` predicate

**Files:** `src/domains/progression/material_predicate.py` (new)

**Change:** Create a new module with exactly one public function:

```python
from __future__ import annotations
from typing import Tuple

from src.core.recipes import RecipeRegistry


def recipe_materials(recipe_id: str) -> Tuple[str, ...]:
    """
    Returns the material item_ids required by `recipe_id`, read through
    RecipeRegistry.get_recipe(recipe_id).materials keys.

    Returns () -- not an exception -- if recipe_id is not registered
    (mirrors RecipeRegistry.get_recipe()'s own None-on-miss contract).
    """
    recipe = RecipeRegistry.get_recipe(recipe_id)
    return tuple(recipe.materials.keys()) if recipe is not None else ()
```

Module docstring (top of file, before the imports) must explicitly disambiguate **all three**
recipe-shaped things now confirmed to be in play (expanded from two, per architecture-reviewer's
finding that a third, disjoint namespace exists and must be named), per AC #2 and the ticket's
Related Code Areas listing:

```
src/domains/progression/material_predicate.py
───────────────────────────────────────────────────────────────────────────────
Shared material-possession predicate (TCK-20260904-MATERIAL-POSSESSION-PREDICATE, ideas 49/50).

Reads exclusively through src/core/recipes.py::RecipeRegistry -- the class the ticket's own
Acceptance Criteria explicitly names (src/core/recipes.py:15-48). 3 entries: iron_sword,
iron_shield, health_potion.

THREE other recipe-shaped things exist in this repo. Do NOT substitute any of them here:

1. src/core/registries.py::RecipeRegistry (registries.py:129-148) -- catalog-bootstrapped,
   up to 25 entries. Different dataclass field name (RecipeDef.requires_items vs. this
   module's Recipe.materials), different miss-behavior (.get() raises KeyError vs.
   recipes.py's get_recipe() returning None). Read by
   src/engine/intent/action_intent.py's REQUEST_CRAFT handling (both its pre-flight
   Requirement-building and its actual crafting-execution branch).

2. src/engine/blacksmith.py::BlacksmithSystem.RECIPES -- NOT a RecipeRegistry at all (a
   plain dict on BlacksmithSystem, no .get_recipe()/.get() classmethod), 14 entries, all
   craft_*-prefixed (craft_steel_sword, craft_battle_axe, ...). This is the class that
   actually, wholesale, populates entity.identity.known_recipes in live production today
   (src/engine/blacksmith.py:139-151, unconditionally wired every tick via
   src/engine/pipeline.py:223). Its 14 craft_* ids never overlap with this module's 3
   ids -- see TCK-20260904-MATERIAL-POSSESSION-PREDICATE's investigation.md "The THIRD
   recipe catalog" section for the full trace. This predicate does NOT read it: doing so
   would violate this ticket's own Acceptance Criteria #2, which requires the predicate
   to read recipes.py::RecipeRegistry specifically. The resulting namespace mismatch
   (this predicate returning () for craft_*-prefixed known_recipes members) is a
   disclosed, accepted, pre-existing limitation -- not something this ticket fixes.

Reading either of the other two here would silently change which recipes govern this
predicate's answer and is out of scope for this ticket (see
tickets/inprogress/TCK-20260904-MATERIAL-POSSESSION-PREDICATE.md's Out of Scope section).
```

This function's I/O contract was verified directly: `src/core/recipes.py:19-39` shows the three
live entries — `iron_sword` (`materials={"iron_ore": 5, "wood": 2}`), `iron_shield`
(`materials={"iron_ore": 8}`), `health_potion` (`materials={"herb": 3}`) — and `get_recipe()`
(`recipes.py:43-44`) returns `None` on a miss, never raises. `recipe_materials()` is
entity-decoupled by design (takes only a `recipe_id` string) so a later ticket (e.g.
`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) can call it directly without needing
`PossessionUnderstandingService` internals — this satisfies the ticket's downstream-reuse note
without building any part of that integration now.

**Do NOT touch:** `src/core/recipes.py`, `src/core/registries.py` (any class or function in
either file), `src/systems/economy_systems/crafting.py`, `src/town/blacksmith.py`,
`src/engine/blacksmith.py` (including `BlacksmithSystem.RECIPES` and `BlacksmithSystem.enforce()`),
`src/engine/intent/action_intent.py`, `src/world/providers/services.py`,
`src/world/providers/requirements.py`.

**Verify:**
- `test_recipe_materials_returns_materials_for_each_live_recipe` (normal flow — parametrized over
  all 3 real entries: `iron_sword` → contains `iron_ore`; `iron_shield` → contains `iron_ore`;
  `health_potion` → contains `herb`)
- `test_recipe_materials_unregistered_recipe_returns_empty_tuple_not_exception` (failure mode)
- `test_recipe_materials_docstring_disambiguates_all_three_registry_like_classes` (architecture
  guard — substring-asserts all three file paths, `src/core/recipes.py`, `src/core/registries.py`,
  and `src/engine/blacksmith.py`, appear in the module's `__doc__`; renamed/expanded from the prior
  plan's two-class version per this revision)
- New file: `tests/unit/domains/progression/test_material_possession_predicate.py`

### Step 2 — Wire `PossessionUnderstandingService.evaluate()` to the predicate

**Files:** `src/domains/progression/possession.py`

**Change:** Replace the two hardcoded literal checks at `possession.py:50-65` ("1. Check if
material for a known recipe" — the `if item_id == "iron_ore" and "iron_sword" in known_recipes:`
/ `elif item_id == "wolf_fang" and "hunter_blade" in known_recipes:` block) with:

```python
# 1. Check if material for a known recipe. See material_predicate.recipe_materials()
# docstring for why this reads src/core/recipes.py::RecipeRegistry, not
# src/core/registries.py::RecipeRegistry or src/engine/blacksmith.py::BlacksmithSystem.RECIPES.
matching_recipes = tuple(
    recipe_id for recipe_id in sorted(known_recipes)
    if item_id in recipe_materials(recipe_id)
)
is_recipe_material = bool(matching_recipes)
if is_recipe_material:
    known_uses.extend(matching_recipes)
    keep_priority = 0.95
    craft_priority = 0.8
    reason = f"Required for known {matching_recipes[0]} recipe."
```

Add `from src.domains.progression.material_predicate import recipe_materials` to the module's
import block. `sorted(known_recipes)` is required for determinism — `known_recipes` is a `set`
(confirmed by existing test usage, e.g. `test_phase6_possession_understanding_service.py:26`:
`identity=replace(entity.identity, known_recipes={"iron_sword"})`), and unordered set iteration
would make `matching_recipes[0]`/`reason` non-deterministic across runs, violating the engine's
determinism law (CLAUDE.md Hard Rules: "Do not break determinism"; `docs/mechanics/`'s
authoritative-pipeline determinism requirement).

**Disclosed behavior change:** the `wolf_fang`/`hunter_blade` hardcoded branch is retired, not
reproduced. `hunter_blade` does not exist in `recipes.py::RecipeRegistry`'s 3 live entries — it
only exists in `registries.py`'s catalog (`registries.py:701`), which this predicate must not
read (see Out of Scope). Confirmed via repo-wide grep that no test in `tests/` exercises
`wolf_fang`/`hunter_blade` through `possession.py` specifically — the only `wolf_fang`/
`hunter_blade` references in `tests/` target `action_intent.py`/`registries.py`-side behavior
(`tests/unit/strategic/test_intents.py`, `tests/architecture/test_no_new_hardcoded_gameplay_truth.py`,
etc.), which this ticket does not touch. This is an intended consequence of generalizing past a
documented mock (`possession.py`'s own docstring: "Mock recipe lists for Phase 6 scenario
needs"), not a regression.

**On organically-populated `known_recipes` (the review's core concern, addressed here explicitly):**
in live production, `known_recipes` is populated exclusively via `BlacksmithSystem.enforce()`'s
wholesale learning (`craft_*`-prefixed ids — see investigation.md). Since none of those ids match
`recipes.py::RecipeRegistry`'s 3 entries, `matching_recipes` will be empty for such entities today,
and this code path behaves identically to the pre-change hardcoded checks failing to match (i.e.
falls through to section "2. Check if a better compatible gear than equipped" below, exactly as it
does today for any item that isn't `iron_ore`). This is not a regression relative to current
behavior — the current hardcoded checks are equally unreachable against `craft_*`-populated
`known_recipes` (they test literal `"iron_sword"`/`"hunter_blade"` membership, neither of which is
a `craft_*` id either). The change is a strict generalization of the *set of recipe ids the mock
recognizes* (2 hardcoded literals → all of `recipes.py`'s 3 live entries), not a regression in
reachability against organic state, which was already zero for both the old and new code against
`BlacksmithSystem`-learned recipes.

**Do NOT touch:** section "2. Check if a better compatible gear than equipped"
(`possession.py:67-87`, unrelated weapon-upgrade logic) or section "3. Check for rare/unknown
items" (`possession.py:89-96`) — leave both exactly as-is.

**Verify:**
- All 3 existing tests in `tests/unit/domains/progression/test_phase6_possession_understanding_service.py`
  must keep passing unmodified in outcome.
- New: `test_material_possession_predicate_recognizes_known_recipe_material` — generalized normal
  flow using a recipe *other than* the original hardcoded `iron_ore`/`iron_sword` pair, e.g. an
  entity holding `herb` with `known_recipes={"health_potion"}` gets `keep_priority > 0.9`,
  `craft_priority > 0.7`, `"health_potion" in meaning.known_uses`.
- New: `test_material_possession_predicate_empty_inventory_returns_false_no_crash` — entity with
  `inventory.items == []` and `known_recipes={"iron_sword"}` evaluates to `comp.meanings == {}`,
  no exception.
- New: `test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match` —
  documents-as-test the disclosed limitation: an entity with `known_recipes={"craft_steel_sword"}`
  (a real `BlacksmithSystem.RECIPES` id) and `iron_ore` in inventory does **not** get
  `is_recipe_material` treatment via this path (asserts the honest current behavior rather than
  leaving it silently unverified) — this is a documentation/regression-pinning test, not a bug
  report; it exists so a future change to either namespace is forced to consciously update this
  test rather than silently drift.

### Step 3 — Wire `GrowthGapEvaluator.evaluate()`'s Material Gap check to the predicate

**Files:** `src/domains/progression/gaps.py`

**Change:** Replace the "2. Material Gap" section (`gaps.py:67-88` — currently
`if "iron_sword" in known_recipes:` followed by a hardcoded `item_id == "iron_ore"` scan) with:

```python
# 2. Material Gap. See material_predicate.recipe_materials() docstring for why this
# reads src/core/recipes.py::RecipeRegistry, not src/core/registries.py::RecipeRegistry
# or src/engine/blacksmith.py::BlacksmithSystem.RECIPES.
id_comp = getattr(entity, "identity", None)
known_recipes = getattr(id_comp, "known_recipes", set()) or set()
inventory_item_ids = {
    stack.item_id
    for stack in getattr(entity.inventory, "items", []) or []
    if stack.quantity > 0
}

missing_material_recipe = None
missing_material_id = None
for recipe_id in sorted(known_recipes):
    for material_id in recipe_materials(recipe_id):
        if material_id not in inventory_item_ids:
            missing_material_recipe = recipe_id
            missing_material_id = material_id
            break
    if missing_material_recipe:
        break

if missing_material_recipe:
    gaps.append(GrowthGap(
        key="material_gap",
        severity=0.5,
        confidence=0.8,
        reason=f"Missing {missing_material_id} to craft {missing_material_recipe} recipe.",
        candidate_resolution_tags=("gather_material", "buy_material")
    ))
```

Add `from src.domains.progression.material_predicate import recipe_materials` to `gaps.py`'s
import block. The existing `id_comp`/`known_recipes` variable declaration at the top of section 2
(`gaps.py:69-70`) is being replaced in place, not duplicated — the rest of the method (sections 1,
3, 4, and the dominant-gap sort at `gaps.py:113-118`) is unaffected and untouched.

**Other writers to `GrowthGap`/`gaps` list in this method (enumerated, per fact-verification
requirement):** this is a single-writer local list within one method call — `gaps: List[GrowthGap]
= []` is declared at `gaps.py:30` and only ever appended to within this same `evaluate()` call
(sections 1 "Weapon/Repair Gap" at lines 32-65, this section 2, section 3 "Gold Gap" at lines
90-100, section 4 "Level/AP Gap" at lines 102-111), then read once by the dominant-gap sort at the
end. No other module or concurrent call path writes into this list — `GrowthGapEvaluator.evaluate()`
is a pure `@staticmethod` called once per entity per tick from `phase.py:57`, with a fresh `gaps =
[]` per call, so there is no cross-entity or cross-tick aliasing risk. This step only changes how
section 2 populates that same list; sections 1/3/4 are untouched and still append independently.

**Same disclosed-limitation note as Step 2 applies here**: for entities whose `known_recipes` was
populated by `BlacksmithSystem.enforce()` (i.e. contains only `craft_*` ids), `recipe_materials()`
returns `()` for every member, so `missing_material_recipe` stays `None` and no `material_gap` is
raised via this path — identical reachability to the pre-change hardcoded `"iron_sword"`/
`"iron_ore"` literal check, which was equally unreachable against `craft_*` ids. Not a regression;
disclosed in Anti-Drift Notes below.

**Verify:**
- All 3 existing tests in `tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py`
  must keep passing unmodified — in particular `test_missing_recipe_material_creates_material_gap`
  (known_recipes `{"iron_sword"}`, empty inventory): under the new logic,
  `recipe_materials("iron_sword") == ("iron_ore", "wood")`, `"iron_ore"` is missing first, so the
  gap's `reason` text (`"Missing iron_ore to craft iron_sword recipe."`) is byte-identical to the
  original hardcoded output — confirmed by manual trace against `recipes.py:19-25`'s field order.
- New (production-consumer behavior-change test, required by AC #3's spirit — proves Route A's
  chosen consumer is real, not the AmbitionProfile route):
  `test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal` — entity with
  `known_recipes={"health_potion"}` and empty inventory produces a `material_gap` referencing
  `herb`/`health_potion`, proving the check now covers a recipe the old hardcoded literal
  (`iron_sword`/`iron_ore`) could never recognize.
- New: `test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap` — entity with
  `known_recipes={"craft_steel_sword"}` and empty inventory produces **no** `material_gap` via this
  path (documents the disclosed namespace-mismatch limitation as a pinned, intentional assertion,
  same rationale as Step 2's equivalent test).

### Step 4 — Full regression sweep (no code changes expected)

**Files:** none (verification-only step)

**Change:** Run the full scoped pytest command set from `test_plan.md`'s "Scoped Pytest Commands"
section:
```bash
pytest tests/unit/domains/progression/ -v
pytest tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py \
       tests/integration/domains/progression/test_phase6_progression_conversion_phase.py -v
pytest tests/unit/world/test_economy_contract.py -v
pytest tests/unit/core/test_registry_parity.py tests/unit/core/test_registry_cross_reference.py \
       tests/unit/core/test_hardcoded_regression_guard.py tests/unit/strategic/test_registries.py -v
pytest tests/perf/test_phase6_progression_conversion_budget.py -v
```
This confirms: (a) `RewardInterpretationService`/`ConversionOptionGenerator` (downstream consumers
of `PossessionUnderstandingComponent`/`GrowthGapReport`) see no shape regression; (b) all 7
`ProgressionConversionPhase` integration scenarios still produce fixed, reproducible outcomes
(determinism guard); (c) `CraftingSystem`/`BlacksmithService` (the `recipes.py::RecipeRegistry`
consumers, confirmed test-only/no production callers per investigation.md) are provably untouched;
(d) `registries.py::RecipeRegistry` and its consumers (`action_intent.py`, both its pre-flight and
its execution branch) show zero behavior change; (e) `BlacksmithSystem.enforce()`'s own crafting
and wholesale-learning logic (`src/engine/blacksmith.py`) shows zero behavior change — no test in
this sweep directly targets it, but Step 1's "Do NOT touch" list already forbids editing that file,
so this is a structural guarantee, not something the sweep itself needs to separately verify; (f)
the per-tick performance budget for `ProgressionConversionPhase` still holds with the predicate's
added lookups.

**Do NOT touch:** any file this sweep exercises — this step is verification-only. If any test in
this sweep fails, fix Steps 1-3's code (not the test) unless the test itself is proven wrong
against the ticket's own AC.

**Verify:** all commands above exit 0.

### Step 5 — Update `docs/simulation/domains/progression_contract.md`

**Files:** `docs/simulation/domains/progression_contract.md`

**Change:** Update "Step 1 — Possession Understanding" (currently lines 98-100: "Evaluates the
entity's current inventory and equipment state. Outputs a possession snapshot: what is equipped,
what is unequipped, what is sellable loot, what is damaged.") to add two sentences: one naming the
new `RecipeRegistry`-backed material lookup, and one disclosing the namespace-mismatch limitation,
e.g.: "Materials needed for the entity's known recipes are identified via a `RecipeRegistry`-backed
lookup (`src/core/recipes.py::RecipeRegistry`, per TCK-20260904-MATERIAL-POSSESSION-PREDICATE)
rather than a fixed item list. Note: `entity.identity.known_recipes` is populated in production
exclusively via `BlacksmithSystem.enforce()`'s `craft_*`-prefixed catalog
(`src/engine/blacksmith.py`), a namespace disjoint from `recipes.py::RecipeRegistry`'s catalog — this
lookup is therefore not yet reachable from organically-learned recipes; see
docs/parity_ledger/progression.yaml's corresponding entry (Step 6 below) for status." Also update
"Step 2 — Growth Gap Evaluation" (lines 102-104) to mention the material gap explicitly, since it
currently lists "missing weapon type, underleveled armor, missing key skill, unspent AP" but omits
the material gap entirely (a pre-existing doc gap, not introduced by this ticket, but directly
touched by Step 3's change) — add "missing recipe material" to that list.

**Do NOT touch:** any other section of this doc (Steps 3-6 of the pipeline, the "From world state"
table, etc.) — this ticket does not change those services.

**Verify:** manual doc review; no automated test binds to this doc's prose. Run
`make knowledge-index-update` after this edit per CLAUDE.md's "After Work" rule (docs under
`docs/` were modified).

### Step 6 — Add parity ledger entry for the new behavior

**Files:** `docs/parity_ledger/progression.yaml`

**Change:** No existing entry in this file covers `PossessionUnderstandingService` or
`GrowthGapEvaluator`'s material-gap check (confirmed by investigation.md's grep — zero hits for
`PossessionUnderstanding`/`GrowthGap`/`possession`). Per CLAUDE.md's Authoritative Mechanics Rule
("If no entry exists, add one"), add a new entry via `tools/parity_ledger_writer.py`'s
`write_entry()` (never hand-edit the YAML — this repo's own convention, see
`feedback_parity_updater_full_file_yaml_rewrite_risk` precedent). Confirmed existing ids in this
shard run `PROG-001`...`PROG-122` (highest currently present: `PROG-122` at
`docs/parity_ledger/progression.yaml:1467`) — **re-check the highest id immediately before writing**,
since this is one ticket in a larger concurrent batch and another ticket in the same batch may have
already claimed `PROG-123`. Entry shape (fields per `docs/parity_ledger/schema.json`, matching the
existing `PROG-*` entries' style), with the namespace-mismatch limitation explicitly recorded in
`divergence_note` (an intentional-limitation disclosure, not a claim of full parity):
```yaml
id: PROG-<next available>
text: "PossessionUnderstandingService and GrowthGapEvaluator identify recipe-material possession/gaps via a RecipeRegistry-backed predicate (recipe_materials()), not hardcoded item-id literals."
status: verified
priority: P2
v2_evidence: src/domains/progression/material_predicate.py
test_path: tests/unit/domains/progression/test_material_possession_predicate.py
divergence_note: "Predicate reads src/core/recipes.py::RecipeRegistry (3 entries) per this ticket's AC. entity.identity.known_recipes is populated in production only via src/engine/blacksmith.py::BlacksmithSystem.RECIPES's disjoint craft_*-prefixed 14-entry catalog, so this predicate does not yet fire against organically-learned recipes. Disclosed, pre-existing, tracked limitation -- not a defect of this entry's own scope. See TCK-20260904-MATERIAL-POSSESSION-PREDICATE investigation.md and the recommended follow-up ticket in that ticket's Completion Summary."
```

**Do NOT touch:** any other shard file (`combat_movement.yaml`, `strategic_cognition.yaml`, etc.)
— per the Risks section's conditional-resolution convention, `docs/parity_ledger/strategic_cognition.yaml`
and `docs/mechanics/04_strategic_cognition.md`'s "Live tier-5 candidates" paragraph are **not**
touched by this plan: the condition that would require them ("a new `GoalScorer`/`GoalKind` is
added") is not met, since Route A was adopted. State this explicitly in the ticket's Implementation
Notes when closing out.

**Verify:** `write_entry()`'s in-process index rebuild succeeds (per the tool's own docstring); then
run `python3 tools/parity_index.py build` as a second, visible Bash call per
`.claude/agents/parity-updater.md`'s convention so the retro-metric matcher sees it.

### Step 7 — Recommend (not build) a follow-up ticket for the namespace bridge

**Files:** none — this step is a recommendation to the orchestrating session, not an implementation
step. No code, doc, or ticket file is created by this plan.

**Change:** At ticket close, the implementer's Completion Summary should recommend filing a
follow-up ticket (sketch below) so the recommendation is durably recorded, matching this batch's
own established pattern for disclosed-but-out-of-scope gaps (`TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`,
filed to `tickets/todos/` as a standalone `OPEN`/`standard` ticket after being found during a
different ticket's investigation, not built by that ticket). Suggested sketch, for whoever files it:

- **Suggested ID:** `TCK-<date>-RECIPE-CATALOG-NAMESPACE-BRIDGE` (or similar; final naming is the
  filer's call)
- **Problem:** three disjoint recipe-shaped catalogs exist (`src/core/recipes.py::RecipeRegistry`,
  3 entries, zero production callers of its two consumer functions; `src/core/registries.py::RecipeRegistry`,
  up to 25 entries, genuinely live via `action_intent.py`'s `REQUEST_CRAFT` handling; `src/engine/blacksmith.py::BlacksmithSystem.RECIPES`,
  14 `craft_*`-prefixed entries, the *only* confirmed live wholesale writer of
  `entity.identity.known_recipes`). No production code path bridges the `craft_*` namespace to
  either `RecipeRegistry` class's ids, so any consumer reading `known_recipes` against either
  `RecipeRegistry` (including this ticket's new `recipe_materials()` predicate, and the pre-existing
  `recipe_known` `Requirement` check in `src/world/providers/requirements.py:196-197`) is
  structurally unreachable against organically-learned recipes today.
- **Scope sketch (for the filer to refine, not prescribed here):** either (i) unify the three
  catalogs into one, with a migration path for `known_recipes`'s existing `craft_*` values, or (ii)
  make `BlacksmithSystem.enforce()`'s wholesale-learning step id-compatible with whichever
  `RecipeRegistry` is chosen as canonical, or (iii) formally declare `recipes.py::RecipeRegistry`
  dead code (zero production callers, confirmed) and consolidate on `registries.py::RecipeRegistry`
  for both crafting-execution and recipe-possession-predicate purposes, updating this ticket's
  predicate accordingly in a follow-up. This plan does not choose among these — that decision needs
  its own investigation given how many call sites are involved (`CraftingSystem.craft()`,
  `BlacksmithService.craft_item()`, `action_intent.py`'s two `REQUEST_CRAFT`-adjacent branches,
  `ServiceOpportunityProvider.get_opportunities()`, `BlacksmithSystem.enforce()`, and now this
  ticket's `recipe_materials()`).
- **Priority:** P2 (disclosed, non-blocking; no corpus world currently depends on
  `recipe_materials()`'s answer being non-empty against `craft_*`-prefixed `known_recipes` — none of
  ideas 49/50/52's actual implementation exists yet, so nothing downstream is silently broken by
  this gap today).

**Do NOT touch:** do not create the follow-up ticket file as part of this ticket's implementation —
filing decisions and exact scoping belong to the orchestrating session, consistent with this
plan's role being to disclose and recommend, not to unilaterally expand scope by creating new
tickets mid-implementation.

**Verify:** N/A (recommendation only, not a code or file change this ticket makes).

## Scope Guards

- Do not modify `src/core/recipes.py` or `src/core/registries.py` (either `RecipeRegistry` class,
  or any of their existing consumers) — ticket's Out of Scope is explicit on this.
- Do not modify `src/engine/blacksmith.py` (`BlacksmithSystem.RECIPES` or `BlacksmithSystem.enforce()`)
  — newly confirmed as the live `known_recipes` writer, but touching it (e.g. to add
  `recipes.py`-style ids, or to make it call `recipe_materials()`) is a namespace-bridging change
  belonging to the recommended follow-up ticket (Step 7), not this one.
- Do not rename either `RecipeRegistry` class — only explicit selection of `recipes.py`'s class by
  the new predicate.
- Do not introduce a third confusably-named class (no new `*RecipeRegistry`, `*PossessionService`,
  or `*PossessionPredicate` name) — `material_predicate.py`'s one function, `recipe_materials()`,
  is deliberately named to avoid this.
- Do not implement `TCK-20260904-FACTION-EXPAND-DIRECTIVE` (EXPAND_TERRITORY directive) or any
  faction/country-level wrapper around `recipe_materials()` — that ticket's job, not this one.
  `recipe_materials()`'s plain, entity-decoupled signature is deliberately kept trivial to call
  from a future faction-level wrapper, but building that wrapper is out of scope here.
- Do not build a new `GoalKind`/`GoalScorer`/materialization branch for `AmbitionProfile` — Route A
  was adopted specifically to avoid this larger, unjustified lift (see Summary).
- Do not touch `MotivationModel.values`/`ValuePreferenceProfile` (`TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`'s
  separate, still-blocked dead field) — unrelated to `AmbitionProfile.ambition`, do not conflate.
- Do not modify `CraftingSystem.craft()`'s 7-gate sequence (`src/systems/economy_systems/crafting.py`)
  or `BlacksmithService.craft_item()` (`src/town/blacksmith.py`) — the predicate is read-only and
  additive; Step 4's regression sweep exists specifically to catch an accidental change here.
- Do not have `recipe_materials()` or either edited call site read
  `registries.py::RecipeRegistry`'s richer 25-entry catalog (including `beast_fang`/`moon_resin`)
  — even though it is genuinely richer content, it is explicitly out of scope per the ticket; this
  predicate answers strictly against `recipes.py`'s 3 live entries.
- Do not add exact-quantity gating (e.g. "needs 5 `iron_ore`, only have 3") to either call site —
  the original hardcoded checks only tested item *presence* (`stack.quantity > 0`), not the
  recipe's exact required count; `CraftingSystem.craft()` (untouched by this ticket) is the
  authoritative place exact-quantity gating already lives (per
  `docs/mechanics/resource_conservation_contract.md`'s 7-gate sequence). Reproducing quantity-exact
  gating here would be scope creep beyond generalizing the existing mock.
- Do not attempt to "fix" the `BlacksmithSystem.RECIPES`/`recipes.py` namespace mismatch by
  switching which registry the predicate reads, by adding a translation/alias layer between the
  two namespaces, or by patching `BlacksmithSystem.enforce()` to also learn `recipes.py`-style ids
  — any of these would be an unrequested, unscoped architecture change; the correct response is
  disclosure (this plan's Anti-Drift Notes) plus a recommended follow-up ticket (Step 7), not a
  silent in-ticket fix.
- Do not create the recommended follow-up ticket file (Step 7) as part of this ticket's own
  implementation — recommend it in the Completion Summary; filing is the orchestrating session's
  call.

## Dependency Map

- Step 1 has no dependencies — do first.
- Step 2 depends on Step 1 (`material_predicate.py` must exist to import from).
- Step 3 depends on Step 1 only — independent of Step 2 (different file, different call site); may
  be done in parallel with Step 2 once Step 1 lands.
- Step 4 depends on Steps 1-3 all being complete (it is a regression sweep over their combined
  effect).
- Step 5 depends on Steps 2-3 (doc text describes their final behavior, including the disclosed
  limitation).
- Step 6 depends on Step 1 (cites `material_predicate.py` as `v2_evidence`) and on the new test
  file from Step 1 existing (cited as `test_path`) — do last among the code/doc steps.
- Step 7 (recommendation only) has no code dependency but should be written into the ticket's
  Completion Summary after Steps 1-6 are done, so the recommendation reflects the final, as-built
  state.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A single, named material-possession predicate exists, reused/extended from `PossessionUnderstandingService`, with no duplicate parallel evaluator introduced. | Step 1 (creates `recipe_materials()`), Step 2 (wires it into `PossessionUnderstandingService.evaluate()`) | `test_recipe_materials_returns_materials_for_each_live_recipe`; all 3 existing `test_phase6_possession_understanding_service.py` tests passing unmodified |
| The predicate's implementation and its tests explicitly reference `src/core/recipes.py::RecipeRegistry` (not `src/core/registries.py::RecipeRegistry`), with a code comment or docstring disambiguating the two by file path. | Step 1 (module docstring, now disambiguating all three recipe-shaped classes — `recipes.py`, `registries.py`, and `blacksmith.py::BlacksmithSystem.RECIPES` — expanded scope per architecture-reviewer's finding), Step 2 and Step 3 (inline comments at each call site, also naming all three) | `test_recipe_materials_docstring_disambiguates_all_three_registry_like_classes` |
| If `AmbitionProfile` is the consumer, at least one real (non-test) production code path reads the populated field — verified by a test asserting production behavior changes based on the predicate's output. | **Not applicable — conditional not triggered.** Route A was adopted; `AmbitionProfile` is not the consumer. The ticket's real production-consumer requirement is instead satisfied via `GrowthGapEvaluator`'s already-live per-tick chain (Step 3) — genuinely live and unconditionally reachable code, though (per the disclosed limitation) not yet observably branching for `craft_*`-populated `known_recipes` in today's production state. | `test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal` (proves the real, non-`AmbitionProfile` production path changed behavior for the ids it does recognize) |
| Tests cover: entity possesses material X (positive), entity has no relevant inventory (edge), unknown/unregistered material (failure mode). | Step 1 (predicate-level failure mode), Step 2 (positive + edge + disclosed-limitation case at the possession-service level), Step 3 (positive + disclosed-limitation case at the growth-gap level) | `test_recipe_materials_returns_materials_for_each_live_recipe`, `test_recipe_materials_unregistered_recipe_returns_empty_tuple_not_exception`, `test_material_possession_predicate_recognizes_known_recipe_material`, `test_material_possession_predicate_empty_inventory_returns_false_no_crash`, `test_material_possession_predicate_craft_prefixed_known_recipes_do_not_match`, `test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal`, `test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap` |

## Anti-Drift Notes

- **The `BlacksmithSystem.RECIPES`/`recipes.py::RecipeRegistry` namespace mismatch is a disclosed,
  accepted, pre-existing limitation of this ticket's scope — not an oversight, and not something
  this plan silently works around.** Full evidence trail (all independently re-verified against
  source, not inferred):
  - `src/engine/pipeline.py:223` — `BlacksmithSystem.enforce()` runs unconditionally every tick,
    no feature flag.
  - `src/engine/blacksmith.py:139-151` — the **only** confirmed live production writer that
    wholesale-populates `known_recipes`, using the 14-entry `craft_*`-prefixed
    `BlacksmithSystem.RECIPES` catalog (`blacksmith.py:27-112`).
  - `src/core/recipes.py:15-48` — the 3-entry catalog this ticket's AC mandates the predicate read
    (`iron_sword`, `iron_shield`, `health_potion`). Zero overlap with the 14 `craft_*` ids.
  - Repo-wide grep of every `known_recipes`/`recipes_learned` writer (`investigation.md`'s "THIRD
    recipe catalog" section) found no other confirmed production writer that populates
    `known_recipes` with `recipes.py`-style (or `registries.py`-style) ids.
  - **Why this ticket does not switch registries to fix it (Option (a) over Option (b)):** the
    ticket's own body — not this investigation or plan — already explicitly and literally commits
    to `src/core/recipes.py::RecipeRegistry` in its Acceptance Criteria #2 and Out of Scope
    sections. Overriding that is not a decision available to planning. It also would not actually
    fix the underlying gap: re-investigation found `registries.py::RecipeRegistry` (the apparent
    alternative) has the **identical** non-reachability problem against `craft_*`-populated
    `known_recipes` — its own `recipe_known` `Requirement` check
    (`src/world/providers/requirements.py:196-197`) is equally unreachable today, since it too is
    never checked against `craft_*` ids. Switching to `BlacksmithSystem.RECIPES` directly is also
    not viable: it is not a `RecipeRegistry`-shaped class (no `.get_recipe()`/`.get()` classmethod,
    just a plain dict), importing an engine-pipeline module (`src/engine/blacksmith.py`) into
    `src/domains/progression/` would be a new, otherwise-absent layering direction, and it would
    directly contradict AC #2's literal text.
  - **Is there any real scenario where `recipes.py`-style ids end up in `known_recipes` some other
    way?** Re-investigated specifically for this: none found. The only other writer of
    `recipes_learned` (`src/engine/domain/core_actions.py:384`, a peer-to-peer "TEACH"/`TRAIN`
    action) sets it from a generic `skill_id` payload field checked only against `capability`-kind
    blockers; no production code path was found constructing a `"TRAIN"` action intent with
    `skill_id` set to any `recipes.py`- or `registries.py`-style recipe id. So: genuinely none
    exists today. Stated plainly, per the review's own request: **this ticket satisfies its "real
    production consumer" AC via a narrower, real, live, and correctly-implemented path
    (`GrowthGapEvaluator`/`PossessionUnderstandingService`, unconditionally reachable every tick)
    that is not yet observably reachable from `BlacksmithSystem`-learned recipes specifically.** A
    follow-up ticket to bridge the gap is recommended (Step 7's sketch), not built here.
  - Step 2 and Step 3 each add an explicit test (`..._craft_prefixed_known_recipes_do_not_match` /
    `..._produce_no_material_gap`) that pins this exact limitation as an intentional, asserted
    behavior — so a future change to either namespace must consciously update these tests, rather
    than the gap silently persisting unverified.
- **`AmbitionProfile` stays dead code after this ticket — deliberate, not an oversight.**
  `src/core/cognition.py:399-405` confirms it as a real, frozen dataclass with zero production
  reads (verified by investigation's repo-wide grep). This plan does not wire it, because Route A
  (the `GrowthGapEvaluator` chain) already satisfies the ticket's "real production consumer"
  requirement more cheaply and without the larger `GoalKind`/`GoalScorer` lift. State this
  explicitly in the ticket's Completion Summary when closing — do not let a future reader assume
  this ticket silently forgot `AmbitionProfile`.
- **`hunter_blade`/`wolf_fang` mock behavior is retired, not reproduced** (Step 2) — confirmed by
  repo-wide grep that no test in `tests/` depends on `possession.py`'s `wolf_fang`/`hunter_blade`
  branch specifically. This is intended: `hunter_blade` only exists in the out-of-scope
  `registries.py` catalog, not in the live `recipes.py::RecipeRegistry` this predicate reads.
- **Do not silently substitute `registries.py::RecipeRegistry`** because its 25-entry catalog looks
  richer/more "real" — it genuinely is richer (includes `beast_fang`/`moon_resin`, the exact
  materials idea 49 eventually wants), and (per the re-investigation) it is genuinely a live
  production execution path too (via `action_intent.py`'s `REQUEST_CRAFT` handling) — but reading
  it here would still silently change this predicate's answers away from the ticket's own explicit
  AC #2. This is the single highest-risk drift vector per investigation.md — the disambiguating
  docstring in Step 1 (now covering all three recipe-shaped classes) exists specifically to block
  it.
- **`recipes.py::RecipeRegistry`'s own "production consumer" status is weaker than originally
  characterized — disclosed for completeness, does not change this plan.** Re-investigation found
  `CraftingSystem.craft()` and `BlacksmithService.craft_item()`/`BlacksmithAction.craft()` (the two
  functions that import `recipes.py::RecipeRegistry`) have **zero** non-test callers anywhere in
  `src/`. This does not block this ticket — the AC's binding requirement is about which class the
  *predicate* reads through, not a claim that `recipes.py`'s existing consumers must themselves
  already be live — but it is material context for the follow-up ticket (Step 7) and must not be
  mischaracterized as "confirmed live crafting execution" in any doc this ticket touches (Step 5's
  doc edit and Step 6's parity entry both state this accurately).
- **Determinism**: `known_recipes` is a Python `set` — always iterate it via `sorted(known_recipes)`
  in both edited call sites (Steps 2 and 3), never raw set iteration, to keep
  `ProgressionConversionPhase`'s output reproducible across runs with identical seed/state.
- **`recipe_materials()`'s quantity-blind contract is intentional** — it answers "is this item ever
  a required material," not "do I have enough of it to craft right now." Exact-quantity gating
  belongs to `CraftingSystem.craft()` (untouched, out of scope), matching the original hardcoded
  checks' own presence-only semantics (`stack.quantity > 0`, not `>= recipe_required_count`).
- **`gaps.py`'s `gaps` list is single-writer per call** (see Step 3's writer enumeration) — the
  Material Gap section change does not introduce any new concurrent-write or ordering risk; the
  dominant-gap severity sort at `gaps.py:113-118` (untouched) still runs after all four sections
  append, unaffected by this change.
