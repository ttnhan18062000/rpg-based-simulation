---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING
artifact_type: plan
tags: [cognition, adventure, self-model]
---

# Implementation Plan — TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Summary

Make `confidence_bonus` in `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`)
reflect a real `CapabilityEstimateService.estimate()` value instead of the flat
`route.confidence × 0.15` constant, for the two route families that have an evidence-backed,
buildable capability key: `GATHER_RESOURCE` (key `gather.resource.<kind>`, resolved from
`resource_nodes[route.target_node_id].kind`, confirmed `src/core/state.py:911`) and
`CRAFT_UPGRADE` (key `craft.recipe.<recipe_id>`, resolved from `route.requirements`'s
`Requirement(kind="recipe_known", subject=recipe_id)` entry, confirmed
`src/world/providers/services.py:55`). This is implemented as a **direct, ad-hoc call** from
`AdventureRouteScorer.score()` into `CapabilityEstimateService.estimate()`
(`src/cognition/capability_estimate.py:85-91`) — confirmed a stateless `@staticmethod` taking
`(entity, state=None, context=None, tick=0)` with no dependency on `SelfModelUpdatePhase`'s dirty-check
machinery or on `entity.self_model.capabilities` being pre-populated. This plan does **not** wire
`SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:57-62`) to pass a real
`capability_context` into `run()` — that remains the unresolved, larger prerequisite (option (a) in
the ticket's own Scope section), explicitly not attempted here. After this plan lands,
`entity.self_model.capabilities.estimates` is still empty at every real tick — this plan only makes
`AdventureRouteScorer.score()` compute its own throwaway, local capability estimate for scoring
purposes, never written back to durable entity state.

Per AC2's own wording ("confidence_bonus reflects a real `CapabilityEstimate.estimate` value, not
always the generation-time confidence constant" — i.e. *sometimes* it should still be the flat
constant, for unmapped families), this is a **replacement of `confidence_bonus`'s input source for
the two mapped families**, not a new additive scoring term (unlike the sibling `memory_adjustment`
ticket's shape). The overall formula
(`score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment +
confidence_bonus - risk_penalty - blocker_penalty`, `scoring.py:47,252`) is unchanged; only how
`confidence_bonus` itself is computed changes, and only for the two mapped families. The `0.15`
weight is unchanged. No schema change is needed — `confidence_bonus: float = 0.0` already exists on
`AdventureRouteOption` (`src/domains/adventure/schema.py:69`) and is already written back via the
existing `dataclasses.replace(..., confidence_bonus=round(confidence_bonus, 4), ...)` call
(`scoring.py:297`); this plan only changes what value that local variable holds before that line
runs.

## Design Decisions

### 1. Family mapping scope: `GATHER_RESOURCE` + `CRAFT_UPGRADE` only

Confirmed via direct read of `src/domains/adventure/schema.py:36-73`: `AdventureRouteOption` has
**no `enemy_id` or `region_id` field at all** — its only identifying fields beyond `family` are
`target_node_id: Optional[int]` (used today for `GATHER_RESOURCE`'s depletion multiplier,
`scoring.py:150-155`) and `quest_id: Optional[str]` (used for `QUEST_OPPORTUNITY`). This is a
stronger reason than "dead code" alone: even if `HUNT_WEAK_ENEMY`/`SCOUT_LOCATION` were live-emitted
by `AdventureRouteGenerator.generate()` (confirmed they are not — zero `RouteFamily.HUNT_WEAK_ENEMY`
or `RouteFamily.SCOUT_LOCATION` emission sites in `generator.py:24-181`, matching
investigation.md), there is **no field on the route to extract a `combat.enemy_type.<id>` or
`travel.region.<id>` key from** — no enemy identity or region identity is ever attached to an
`AdventureRouteOption`. Building either mapping would require inventing a data source with zero
code evidence, which CLAUDE.md's Hard Rule ("Do not guess when uncertainty affects behavior or
architecture") and this epic's established discipline (ticket 7's plan review caught exactly this
class of unverified claim) both prohibit. `BUY_UPGRADE`, `RECOVER`, `ASK_INFORMATION`, `FORM_PARTY`,
`TAKE_EASY_QUEST`, `QUEST_OPPORTUNITY`, `SELL_LOOT_FOR_GOLD`, `TRAIN_SKILL`, `RETURN_TOWN`,
`DEFER_WITH_REASON`, `PROTECT_TARGET`, `OWN_SURVIVAL` likewise have no `CapabilityContext`-shaped
key source (`CapabilityContext`'s four domains are `combat_enemies`, `travel_regions`,
`gather_resources`, `craft_recipes` only — confirmed `src/cognition/capability_estimate.py:38-41`)
and are left on the flat term.

**`GATHER_RESOURCE` and `CRAFT_UPGRADE` are both live-generated** (confirmed: `generator.py:38-45`'s
`kind_map` maps opportunity kinds `"gather_resource"` → `GATHER_RESOURCE` and `"craft_item"` →
`CRAFT_UPGRADE`, both constructed at `generator.py:79-92` for every matching opportunity from
`ResourceOpportunityProvider.get_opportunities()` / `ServiceOpportunityProvider.get_opportunities()`)
and both carry a resolvable key source, confirmed by direct reads:
- `GATHER_RESOURCE`: `route.target_node_id` (set at `generator.py:90` from `int(opp.target_id)`) is
  the resource node's id; `resource_nodes[target_node_id].kind` (`src/core/state.py:911`) is the
  same string `ResourceRegistry.get()` keys on (`src/world/providers/resources.py:64-65`) — this is
  the exact same `resource_nodes`/`target_node_id` data path `score()` already uses for the
  depletion-fraction multiplier (`scoring.py:149-155`, `TCK-20260619-E21C-SCORING-WIRE`), so no new
  parameter is needed on `score()`'s signature.
- `CRAFT_UPGRADE`: `route.requirements` (set at `generator.py:86` from `opp.requirements`) carries
  `Requirement(kind="recipe_known", subject=recipe_id)`, `Requirement(kind="has_gold",
  quantity=recipe.gold_cost)`, and one `Requirement(kind="has_item", subject=m_id, quantity=m_qty)`
  per required material — confirmed at `src/world/providers/services.py:53-59`, all three
  `Requirement` kinds unconditionally present on every `craft_item` opportunity `services.py`
  constructs. `Requirement` itself is `@dataclass(frozen=True, slots=True)` with fields `kind: str`,
  `subject: Optional[str] = None`, `quantity: int = 1` (`src/world/providers/requirements.py:9-12`).

### 2. Formula placement: REPLACE `confidence_bonus`'s source, not an additive term

AC2's literal text ("confidence_bonus reflects a real `CapabilityEstimate.estimate` value, not
always the generation-time confidence constant") only makes sense as a **conditional replacement**:
for mapped-and-resolvable routes, `confidence_bonus = capability_estimate × 0.15` instead of
`route.confidence × 0.15`; for every other route (unmapped family, or mapped family whose key
extraction fails), `confidence_bonus` stays exactly `route.confidence × 0.15`, unchanged from today
(`scoring.py:244`). This deliberately does **not** follow `memory_adjustment`'s additive-new-term
shape (`scoring.py:224-241`, `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`) — that ticket's AC1
asked for a new, independent signal to shift the score; this ticket's AC2 asks for the *existing*
`confidence_bonus` term to be sourced more richly for routes where a richer source exists. Adding a
second, parallel `capability_bonus` term alongside the flat one would double-count confidence for
mapped routes and contradicts AC2's "reflects... a real estimate value" (singular value, not two
stacked values). The `0.15` weight (`scoring.py:244`, `docs/mechanics/04_strategic_cognition.md`
§6.2 line 147, parity ledger STRAT-227) is unchanged — only the operand multiplied by `0.15`
changes, for the two mapped families.

### 3. Fallback behavior: silently fall back to the flat term, never raise

Mirrors the existing defensive style already used in this exact formula's other conditional blocks:
the depletion-fraction block guards with `if node_id is not None: ... if target_node is not None and
target_node.max_charges > 0: ...` (`scoring.py:150-154`) rather than raising on a missing node; the
`QUEST_OPPORTUNITY` capability-match block guards with `if opportunity is not None and
opportunity.objective_chain:` (`scoring.py:169`) rather than raising on a missing quest registry
entry. This plan follows the identical pattern: if `route.target_node_id` is `None`, or
`resource_nodes` is `None`/missing the node, or (Review round-1 fix) no `has_item` requirement
naming a required tool is found on the route (`GATHER_RESOURCE`), or no `Requirement(kind=
"recipe_known", ...)` is found in `route.requirements` (`CRAFT_UPGRADE`), the capability lookup is
skipped entirely and `confidence_bonus` keeps its `route.confidence × 0.15` value computed at the
top of the block — never partially computed, never `None`, never raised. The `required_tool` gate is
necessary, not optional: without it, `CapabilityEstimateService.estimate()`'s `has_tool` defaults to
`True` when no tool entry is supplied (`capability_estimate.py:179`), so an ungated call would
silently switch off the flat term for every resolvable `GATHER_RESOURCE` route regardless of whether
a tool requirement genuinely exists — confirmed to break `tests/unit/domains/adventure/
test_depletion_scoring.py`'s `_gather_route()` fixtures (no `requirements` set, `confidence=0.0`,
but `resource_nodes` IS provided), a real pre-existing regression test, not a hypothetical.

### 4. `recipe_data`/`resource_data` reconstruction: from `route.requirements` only, no registry read

`CapabilityEstimateService.estimate()`'s crafting branch needs `recipe_data[recipe_id] =
{"requires_items": {...}, "gold_cost": N}` to avoid its own "unknown recipe" fallback
(`estimate=0.3, confidence=0.3`, `capability_estimate.py:210-219`); its gathering branch needs
`resource_data[resource_kind] = {"required_tool": tool_id}` to distinguish "has the tool" from
"doesn't" (`capability_estimate.py:176-190`) — without a `required_tool` entry, `has_tool` defaults
to `True` unconditionally (`capability_estimate.py:179-190`), which would make
`test_gather_resource_confidence_reflects_capability_estimate`'s required behavior ("entity with the
required tool present scores higher than an otherwise-identical entity missing it", `test_plan.md`
New Test 1) impossible to satisfy. Both dicts are reconstructed **purely from data already on the
route/passed-in params** — never from `RecipeRegistry`/`ResourceRegistry` (`src/core/registries.py`)
— preserving `scoring.py`'s existing "no registry reads" pattern (confirmed: `scoring.py` today
imports no registry module) and staying inside the entity/route-local information-opacity boundary:
- `CRAFT_UPGRADE`: `gold_cost` from the route's `has_gold` requirement's `quantity`;
  `requires_items` from each `has_item` requirement's `subject`→`quantity`. This is a faithful
  reconstruction of the exact same values `services.py:53-59` wrote into the requirement tuple in
  the first place — not an inference, a round-trip of real data.
- `GATHER_RESOURCE`: for `GATHER_RESOURCE` opportunities specifically, `resources.py:78-81`
  confirms **at most one** `has_item` requirement is ever added, and only when `res_def.
  required_tool` is set (`Requirement(kind="has_item", subject=res_def.required_tool,
  quantity=1)`) — unlike `CRAFT_UPGRADE`'s potentially-multiple `has_item` entries (one per
  material), `GATHER_RESOURCE`'s single possible `has_item` entry is unambiguously the required
  tool, not a material. This asymmetry is real (confirmed by comparing `resources.py:78-81` against
  `services.py:56-59`), not assumed.

### 5. `tick`/`state` parameters: pass `tick=0` (default), `state=None` (unused)

`CapabilityEstimateService.estimate()`'s `tick` parameter is only ever used to stamp
`last_updated_tick` on the returned `CapabilityEstimate` records (`capability_estimate.py:148,169,
200,217,251`) — confirmed by reading the full method body, `tick` never gates or scales any
`estimate`/`confidence` computation. Likewise `state` is accepted as a parameter
(`capability_estimate.py:88`) but **never referenced anywhere in the method body** — confirmed by
reading the full method. `score()` has no `tick`/`state`-derived value available in scope (its
signature has no `tick` parameter and no `state` argument, only `entity`/`route`/optional
`resource_nodes`/etc., `scoring.py:34-42`), so passing the defaults (`tick=0` implicit, `state=None`
default) is correct and introduces no new plumbing requirement — no change to `score()`'s own
signature.

### 6. Prerequisite disclosure (AC1): resolved via ad-hoc call, NOT via upstream wiring

Confirmed identically to investigation.md: `SelfModelUpdatePhase.apply()` (`self_model_phase.py:
57-62`) calls `SelfModelUpdatePhase.run(entity=entity, state=state, events=..., tick=state.tick)`
without `capability_context=`, so it defaults to `None` (`self_model_phase.py:84`), and Step 4 of
`run()` only calls `CapabilityEstimateService.estimate()` `if capability_context is not None`
(confirmed by reading `self_model_phase.py`'s Step-4 body pattern, matching investigation.md's
citation of lines 198-213) — otherwise capabilities stay unchanged from `old_bundle.capabilities`,
which defaults to `CapabilityEstimateComponent()` with `estimates={}` (`src/core/self_model.py:
152,230-232`). This plan's Step 1 does not touch `self_model_phase.py`, `builder.py`, or
`src/engine/pipeline.py` in any way. `entity.self_model.capabilities.estimates` remains empty in
production after this plan lands — the gap is bypassed for adventure scoring's own purposes, not
resolved upstream. This must be stated plainly in every doc update (Steps 3, 5, 6, 7, 8), not
glossed over as "capability estimation is now wired."

## Steps

### Step 1 — Capability-driven `confidence_bonus` in `AdventureRouteScorer.score()`
**Files:** `src/domains/adventure/scoring.py`

**Change:**
1. Add import: `from src.cognition.capability_estimate import CapabilityContext,
   CapabilityEstimateService` (new top-level import, alongside the existing `src.core.state`/
   `src.domains.adventure.schema` imports at `scoring.py:15-18`). No circular-import risk: `src/
   cognition/capability_estimate.py` imports only `src.core.self_model` (types) and, under
   `TYPE_CHECKING` only, `src.core.state` — it imports nothing from `src.domains.adventure` or any
   module that itself imports `scoring.py`.
2. Update the module docstring (`scoring.py:6-8`) from "Reads only subjective self-model and
   cognition/memory aspects — the entity's own beliefs, never omniscient world truth — to protect
   information opacity." to: "Reads only subjective self-model, cognition/memory, and (for
   `GATHER_RESOURCE`/`CRAFT_UPGRADE` routes with a resolvable capability key) entity-owned combat/
   stamina/inventory/equipment aspects via an ad-hoc `CapabilityEstimateService.estimate()` call —
   never omniscient world truth, and never `entity.self_model.capabilities` itself, which remains
   unpopulated in production (see `TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`) — to
   protect information opacity."
3. Add a short paragraph to the `score()` docstring (after the `Formula:` block, `scoring.py:44-52`):
   "For `GATHER_RESOURCE`/`CRAFT_UPGRADE` routes with a resolvable capability key, `confidence_bonus`
   is computed from `CapabilityEstimateService.estimate()` instead of `route.confidence`
   (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING); all other routes, and mapped routes whose
   key cannot be resolved, keep the flat `route.confidence × 0.15` term."
4. Replace the "── 5. Confidence Bonus ──" block (`scoring.py:243-244`, currently just
   `confidence_bonus = route.confidence * 0.15`) with:
   ```python
   # ── 5. Confidence Bonus (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) ──────
   # For GATHER_RESOURCE/CRAFT_UPGRADE routes with a resolvable capability key,
   # confidence_bonus is fed by an ad-hoc CapabilityEstimateService.estimate() call
   # (entity-owned combat/stamina/inventory/equipment only) instead of the flat
   # generation-time route.confidence constant. Replacement of the term's input
   # source, not a new additive term -- weight stays 0.15. Never touches
   # entity.self_model.capabilities (stays empty in production); this is a
   # scorer-local, throwaway read, never written back to durable entity state.
   confidence_bonus = route.confidence * 0.15
   capability_estimate_value = None

   if (
       route.family == RouteFamily.GATHER_RESOURCE
       and resource_nodes is not None
       and route.target_node_id is not None
   ):
       gather_node = resource_nodes.get(route.target_node_id)
       if gather_node is not None:
           resource_kind = gather_node.kind
           required_tool = None
           for req in route.requirements:
               if req.kind == "has_item" and req.subject:
                   required_tool = req.subject
                   break
           # Review round-1 fix: only take the capability-estimate path when a real tool
           # requirement exists. Without this gate, resource_data={} for tool-less resources
           # makes CapabilityEstimateService.estimate() default has_tool=True
           # (capability_estimate.py:179), always returning a non-None estimate and silently
           # switching off the flat term for every resolvable GATHER_RESOURCE route --
           # including the common case where no tool is required at all. There is nothing
           # capability-relevant to estimate when no tool requirement exists, so the flat
           # term is correctly kept in that case.
           if required_tool is not None:
               resource_data = {resource_kind: {"required_tool": required_tool}}
               cap_component = CapabilityEstimateService.estimate(
                   entity,
                   context=CapabilityContext(
                       gather_resources=(resource_kind,), resource_data=resource_data
                   ),
               )
               cap_estimate = cap_component.estimates.get(f"gather.resource.{resource_kind}")
               if cap_estimate is not None:
                   capability_estimate_value = cap_estimate.estimate

   elif route.family == RouteFamily.CRAFT_UPGRADE:
       recipe_id = None
       gold_cost = 0
       requires_items: Dict[str, int] = {}
       for req in route.requirements:
           if req.kind == "recipe_known" and req.subject:
               recipe_id = req.subject
           elif req.kind == "has_gold":
               gold_cost = req.quantity
           elif req.kind == "has_item" and req.subject:
               requires_items[req.subject] = req.quantity
       if recipe_id is not None:
           cap_component = CapabilityEstimateService.estimate(
               entity,
               context=CapabilityContext(
                   craft_recipes=(recipe_id,),
                   recipe_data={
                       recipe_id: {"requires_items": requires_items, "gold_cost": gold_cost}
                   },
               ),
           )
           cap_estimate = cap_component.estimates.get(f"craft.recipe.{recipe_id}")
           if cap_estimate is not None:
               capability_estimate_value = cap_estimate.estimate

   if capability_estimate_value is not None:
       confidence_bonus = capability_estimate_value * 0.15
   ```
   Note the `if ... elif ...` structure: a route is never simultaneously `GATHER_RESOURCE` and
   `CRAFT_UPGRADE` (mutually exclusive `RouteFamily` enum values), so this is not a priority
   ordering decision, just avoiding a redundant `route.family ==` re-check.
5. No change to the final-score formula (`scoring.py:252`) or the `dataclasses.replace(...)` call
   (`scoring.py:289-300`) — both already reference the `confidence_bonus` local variable by name and
   pick up whatever value this step computes, unchanged from today's structure.

**Other writers to `AdventureRouteOption.confidence_bonus`:** confirmed via the same grep basis as
the sibling ticket's Step 1 — `dataclasses.replace(route, ...)` at `scoring.py:289-300` is the
**only** site in the repo that sets `confidence_bonus` (the field defaults to `0.0` at every one of
`AdventureRouteOption`'s 7 construction call sites, 5 in `generator.py`, 2 in `services.py`/other
opportunity providers — none of them pass `confidence_bonus=`). No other code path reads or writes
this field concurrently; there is no race/collision to reason about.

**Other writers to `entity.self_model.capabilities`/`entity.self_model`:** the only writer anywhere
in the repo is `SelfModelUpdatePhase.apply()` (`self_model_phase.py:32-74`, via `EntityUpdate.
self_model_bundle_set`), which this step does not call, touch, or interact with — `score()` never
mutates `entity` (confirmed: `score()`'s only `dataclasses.replace` call targets the local `route`
parameter, never `entity`, matching the sibling ticket's identical finding). `CapabilityEstimateService.
estimate()` itself has zero writers to reason about beyond its own return value — it is a pure
function with no side effects (confirmed by reading its full body: every branch only populates a
local `estimates` dict and returns a new `CapabilityEstimateComponent`).

**Do NOT touch:** `get_trait` closure (`scoring.py:53-90`), needs/urgency block (`scoring.py:99-141`),
benefit/depletion/quest-capability blocks (`scoring.py:143-188`), risk_multiplier/risk_penalty
(`scoring.py:190-192`), personality_bias block (`scoring.py:194-211`), plan_advance_bonus
(`scoring.py:213-222`), memory_adjustment block (`scoring.py:224-241`), blocker_penalty
(`scoring.py:246-249`), final-score/class-synergy/escort blocks (`scoring.py:251-287`) — none of
these are affected by or need to reference the new capability-driven confidence source. Do not add a
`tick` or `state` parameter to `score()`'s signature (Design Decision 5). Do not modify `src/
cognition/capability_estimate.py` in any way — AC3 depends on that file being unchanged.

**Verify:** `tests/unit/domains/adventure/test_capability_confidence_scoring.py` (Step 2, all 7
tests), plus full existing `tests/unit/domains/adventure/` regression suite (`test_phase3_route_
scoring.py`, `test_depletion_scoring.py`, `test_memory_informed_scoring.py`, `test_scoring_plan_
bonus.py`, `test_hero_quest_scoring.py`) — none of these construct a `GATHER_RESOURCE` route with
both `resource_nodes` provided and a resolvable node, or a `CRAFT_UPGRADE` route with a
`recipe_known` requirement in a way that would change their existing assertions, but must be run to
confirm no regression (e.g. `test_depletion_scoring.py`'s routes are built via `_gather_route()`
with `confidence=0.0` and no `resource_nodes`-independent capability data — verify this stays a
no-op fallback to the flat term, since `resource_nodes` IS passed in those tests, so this is the one
existing test file whose fixtures actually exercise the new `GATHER_RESOURCE` branch's guard logic
and must be re-read carefully, not just assumed unaffected).

---

### Step 2 — Add new test file
**Files:** `tests/unit/domains/adventure/test_capability_confidence_scoring.py` (new file)

**Change:** Implement the 7 tests specified in `test_plan.md`'s "New Tests Required" (items 1-7;
item 8 is explicitly out of scope per Design Decision 1 — no `HUNT_WEAK_ENEMY`/`SCOUT_LOCATION`
test is added):

1. `test_gather_resource_confidence_reflects_capability_estimate` — build a `GATHER_RESOURCE` route
   with `target_node_id` resolving to a `ResourceNodeState(kind="iron_ore", ...)` (reuse the `_node`
   helper pattern from `test_depletion_scoring.py:38-47`) and `requirements=(Requirement(kind=
   "has_item", subject="pickaxe", quantity=1),)`. Assert an entity holding `"pickaxe"` in inventory
   scores a strictly higher `confidence_bonus` than an otherwise-identical entity without it, and
   that both differ from `route.confidence × 0.15` (proving the capability path fired, not the flat
   fallback).
2. `test_craft_upgrade_confidence_reflects_capability_estimate` — build a `CRAFT_UPGRADE` route with
   `requirements=(Requirement(kind="recipe_known", subject="iron_sword"), Requirement(kind=
   "has_gold", quantity=50), Requirement(kind="has_item", subject="iron_ingot", quantity=2))`. Assert
   an entity holding 50+ gold and 2+ `"iron_ingot"` scores a strictly higher `confidence_bonus` than
   an entity missing the gold/materials, and both differ from `route.confidence × 0.15`.
3. `test_capability_confidence_falls_back_to_flat_term_for_unmapped_families` — for `RECOVER`,
   `BUY_UPGRADE`, `ASK_INFORMATION`, and `FORM_PARTY` routes, `confidence_bonus` is exactly
   `round(route.confidence * 0.15, 4)` regardless of entity stats — confirms the change is scoped,
   not a wholesale replacement.
4. `test_capability_confidence_extraction_failure_falls_back_safely` — (a) `CRAFT_UPGRADE` route
   with `requirements=()` (no `recipe_known` entry), (b) `GATHER_RESOURCE` route with
   `target_node_id=None` and separately with a `target_node_id` not present in `resource_nodes`,
   and (c) (Review round-1 fix guard) `GATHER_RESOURCE` route with a resolvable
   `target_node_id`/`resource_nodes` entry but `requirements=()` (no tool requirement at all) —
   this last case is the exact scenario that caused the round-1 review's found regression against
   `test_depletion_scoring.py`'s `_gather_route()` fixtures; it must produce `confidence_bonus ==
   round(route.confidence * 0.15, 4)`, not a capability-estimate-derived value, since there is no
   tool requirement to estimate against. All four cases must not raise and must produce
   `confidence_bonus == round(route.confidence * 0.15, 4)` (Design Decision 3).
5. `test_capability_confidence_does_not_mutate_entity_self_model` — capture `entity.self_model`
   before calling `score()` on a `GATHER_RESOURCE` and a `CRAFT_UPGRADE` route (both with resolvable
   keys), assert `entity.self_model is` (identity check) the pre-call value after — proves the
   ad-hoc `CapabilityEstimateService.estimate()` call result is never written back to
   `entity.self_model.capabilities` (Design Decision 6 / CLAUDE.md durable-state rule).
6. `test_capability_confidence_reads_only_entity_owned_fields` — two entities with identical route/
   `resource_nodes` input but different `entity.inventory`/`entity.equipment` (tool present vs.
   absent) produce different `confidence_bonus`; changing an unrelated field the entity has no
   access to (e.g. constructing with a different `resource_nodes` dict containing an unrelated
   node the route doesn't reference) does not change the result — mirrors `test_phase3_route_
   scoring.py`'s `test_scoring_does_not_use_hidden_world_truth` guard pattern.
7. `test_capability_confidence_is_deterministic` — calling `score()` twice with identical inputs for
   both a `GATHER_RESOURCE` and a `CRAFT_UPGRADE` mapped route produces identical `confidence_bonus`/
   `score` both times.

Use the `V2EntityBuilder` pattern already established in `test_depletion_scoring.py:23-35` (`.
replace_combat(...)`, `.replace_biological(...)`, `.identity(...)`, `.replace_self_model(...)`) plus
`.replace_inventory(InventoryComponent(...))` / `.replace_equipment(EquipmentComponent(...))` (both
confirmed available on `V2EntityBuilder`, `src/core/builder.py:697,737`) to set up the tool/material/
gold fixtures each test needs. Import `Requirement` from `src.world.providers.requirements`.

**Do NOT touch:** any existing test file. This is a new file only.

**Verify:** `pytest tests/unit/domains/adventure/test_capability_confidence_scoring.py -v` — all 7
pass.

---

### Step 3 — Mechanics Bible update
**Files:** `docs/mechanics/04_strategic_cognition.md`

**Change:**
1. Add a new `### 6.12 Capability-Driven Confidence Bonus` subsection (next free number after the
   existing `6.11 Memory-Informed Advice Adjustment`, confirmed the file's headers run `6.1`-`6.11`
   with `6.12` as the next free slot), placed immediately after §6.11. Content: state the exact
   mechanism (`GATHER_RESOURCE`/`CRAFT_UPGRADE` routes with a resolvable capability key use
   `CapabilityEstimate.estimate × 0.15` instead of `route.confidence × 0.15`; all other routes, and
   mapped routes whose key cannot be resolved, keep the flat term), cite the two key-resolution
   sources (Design Decision 1), and include the same "Not yet live in `entity.self_model.
   capabilities`" disclosure style §6.11 already uses for `MemoryUpdatePhase`: *"This is a scorer-
   local, ad-hoc `CapabilityEstimateService.estimate()` call — `entity.self_model.capabilities.
   estimates` itself remains empty in every real tick, because `SelfModelUpdatePhase.apply()` never
   passes a `capability_context` to `run()` (confirmed `src/cognition/self_model_phase.py:57-62`).
   This term is fully live and observable via a real `generate() → score()` chain today (unlike
   `memory_adjustment`, §6.11) because both `GATHER_RESOURCE` and `CRAFT_UPGRADE` are live-generated
   route families."*
2. Update the §6.2 `Formula Term Constants` table's `confidence_bonus` row (`04_strategic_cognition.
   md:147`) from `| \`confidence_bonus\` | \`route.confidence × 0.15\` | **Weight: 0.15** | 0.15 |`
   to: `| \`confidence_bonus\` | \`route.confidence × 0.15\` (flat); for GATHER_RESOURCE/
   CRAFT_UPGRADE with a resolvable capability key: \`CapabilityEstimate.estimate × 0.15\` (see
   §6.12) | **Weight: 0.15** | 0.15 |`.

**Do NOT touch:** §6.1-§6.10's existing content, §6.11 (memory-informed adjustment, unrelated to
this change), the Risk Multiplier calibration history (§6.3), the Personality Bias table (§6.4).

**Verify:** No automated test for doc content; manual proofread that the new subsection and updated
table row match `scoring.py` exactly post-Step-1.

---

### Step 4 — Parity ledger update (STRAT-227)
**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** Extend the existing STRAT-227 entry (`strategic_cognition.yaml:2507-2540`) — same entry
the sibling memory ticket extended, since this is the same `AdventureRouteScorer.score()` formula
gaining a new conditional source for one existing term, not a new formula:
- `text`: append, after the existing `memory_adjustment` clause (line 2519): "; confidence_bonus for
  GATHER_RESOURCE/CRAFT_UPGRADE routes with a resolvable capability key (resource kind via
  resource_nodes[target_node_id].kind, or recipe id via route.requirements's recipe_known entry) is
  computed via an ad-hoc CapabilityEstimateService.estimate() call instead of route.confidence, same
  0.15 weight; all other routes, and mapped routes whose key cannot be resolved, keep route.
  confidence × 0.15; entity.self_model.capabilities itself remains unpopulated in production; all
  constants documented in docs/mechanics/04_strategic_cognition.md §6.12."
- `v2_evidence`: append: "confidence_bonus capability-driven source for GATHER_RESOURCE/
  CRAFT_UPGRADE, ad-hoc CapabilityEstimateService.estimate() call, SelfModelUpdatePhase.apply()
  still never passes capability_context (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING)."
- `test_path`: append `; tests/unit/domains/adventure/test_capability_confidence_scoring.py` to the
  existing string (`...test_memory_informed_scoring.py`).
- `status`: remains `verified`. `priority: P1`, `legacy_evidence: null`, `proof_type: parity`,
  `divergence_note: null` unchanged.

**Other writers to this file/entry:** same 3 other parity ledger files identified by the sibling
ticket's plan (`social_narrative.yaml:2442,2472`, `progression.yaml:1180`,
`infrastructure.yaml:4117`) reference `scoring.py` but cite unrelated sections (escort block, plan-
advance-bonus, route-scoring test evidence) — none require changes. No other entry covers
`confidence_bonus` or capability-estimate consumption.

**Do NOT touch:** any other entry in `strategic_cognition.yaml`, or any entry in the 3 files above.

**Verify:** After Step 2 passes, confirm the appended `test_path` file exists and its tests pass.

---

### Step 5 — `capability_and_knowledge_contract.md` staleness correction
**Files:** `docs/cognition/capability_and_knowledge_contract.md`

**Change:** Correct the "How adventure routing uses capability estimates" section (confirmed lines
75-77, present-tense claim: *"The adventure domain (`src/domains/adventure/`) reads capability
estimates to score route feasibility. A route with `estimate < threshold` for a required capability
generates a blocker (scored at −2.0 penalty). The exact threshold is configurable in the adventure
scoring config."*, confirmed false today by investigation — no such threshold/blocker mechanism
exists in `scoring.py`) to accurately state **both halves**:
> "As of `TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`, `AdventureRouteScorer.score()`
> (`src/domains/adventure/scoring.py`) calls `CapabilityEstimateService.estimate()` directly, ad hoc,
> for `GATHER_RESOURCE` and `CRAFT_UPGRADE` routes with a resolvable capability key — the resulting
> `CapabilityEstimate.estimate` value feeds `confidence_bonus` (replacing the flat `route.confidence
> × 0.15` term for those two families only), NOT a blocker-generation threshold mechanism. There is
> no `−2.0` capability-blocker penalty anywhere in `scoring.py` — that prior claim was aspirational
> and inaccurate. This call is scorer-local and ad hoc: it does not go through
> `SelfModelUpdatePhase`, and `entity.self_model.capabilities.estimates` remains empty in production
> (see 'Not yet live' note above), because `SelfModelUpdatePhase.apply()` never passes a
> `capability_context` to `run()`."

**Do NOT touch:** the "Craft"/"CapabilityEstimate record"/"Confidence decay" sections immediately
above/below (accurate, unrelated), or the "Knowledge Model" section starting after this one.

**Verify:** No automated test; manual proofread against `scoring.py` post-Step-1.

---

### Step 6 — `docs/cognition/README.md` staleness correction
**Files:** `docs/cognition/README.md`

**Change:** Correct the "Relationship to other subsystems" table's `src/domains/adventure/` row
(confirmed line 73: `| \`src/domains/adventure/\` | \`entity.self_model.capabilities\` → route
feasibility (can entity reach/fight?) |`) — this claims adventure reads the entity's own
`self_model.capabilities` field, which stays empty in production even after this ticket. Correct to:
`| \`src/domains/adventure/\` | Ad-hoc \`CapabilityEstimateService.estimate()\` call from
\`AdventureRouteScorer.score()\` (GATHER_RESOURCE/CRAFT_UPGRADE only) → \`confidence_bonus\`; NOT
via \`entity.self_model.capabilities\`, which remains empty in production (TCK-20260811-CAPABILITY-
CONFIDENCE-ADVENTURE-SCORING) |`.

**Do NOT touch:** any other row in the "Relationship to other subsystems" table (Motivation,
Perception, `intelligence.py`, `src/strategy/`, world-side providers) — all accurate and unrelated.

**Verify:** No automated test; manual proofread.

---

### Step 7 — `adventure_contract.md` update
**Files:** `docs/simulation/domains/adventure_contract.md`

**Change:**
1. "What It Reads" table (confirmed lines 63-74): add a new row directly after the existing
   `entity.cognition.memory.causal.entries` row (line 74): `| Ad-hoc \`CapabilityEstimateService.
   estimate()\` call (GATHER_RESOURCE/CRAFT_UPGRADE only; entity.combat/stamina/inventory/equipment)
   | Feeds \`confidence_bonus\` for the two mapped families — see \`docs/mechanics/
   04_strategic_cognition.md\` §6.12; NOT via \`entity.self_model.capabilities\`, which stays empty
   in production |`.
2. The "Scoring — AdventureRouteScorer / AdventureDecisionService" formula table's `confidence_bonus`
   row (confirmed line 138: `| \`confidence_bonus\` | Derived from \`route.confidence\` |`) — update
   to: `| \`confidence_bonus\` | \`route.confidence × 0.15\` (flat); for GATHER_RESOURCE/
   CRAFT_UPGRADE with a resolvable capability key: \`CapabilityEstimate.estimate × 0.15\` — see
   \`docs/mechanics/04_strategic_cognition.md\` §6.12 |`.

**Do NOT touch:** the "Full `RouteFamily` enum (13 values)" table's pre-existing 13-vs-16 drift
(confirmed pre-existing per investigation.md, unrelated to this ticket), the "Candidate sources"
table's `SCOUT_LOCATION`/"Region exploration targets" pre-existing dead-route inaccuracy (also
pre-existing, out of scope to fix generation-side claims here), or any other section.

**Verify:** No automated test; manual proofread.

---

### Step 8 — Architecture design doc update
**Files:** `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`

**Change:** Update the "Capability-estimate-driven confidence" bullet (confirmed lines 430-432,
currently an open Future Extension Pattern: *"`src/cognition/`'s `CapabilityEstimateService` already
computes real 'can I fight/craft/travel' estimates that adventure's own `confidence_bonus` term
doesn't read — wiring this in closes an inert loop between two subsystems that already exist."*) to
reflect the scoped, closed version:
> "**Capability-estimate-driven confidence** (closed, scoped,
> `TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`): `AdventureRouteScorer.score()` now calls
> `CapabilityEstimateService.estimate()` directly, ad hoc, for `GATHER_RESOURCE` (via
> `resource_nodes[target_node_id].kind`) and `CRAFT_UPGRADE` (via `route.requirements`'s
> `recipe_known` entry) — the only two route families with an evidence-backed capability-key source
> (`AdventureRouteOption` has no `enemy_id`/`region_id` field, so 'can I fight/travel' remain
> unbuildable without inventing a data source). This bypasses, not fixes, the upstream gap:
> `SelfModelUpdatePhase.apply()` still never passes a `capability_context` to `run()`, so `entity.
> self_model.capabilities.estimates` remains empty in every real tick — see `capability_and_
> knowledge_contract.md`."

**Do NOT touch:** the "Memory-informed candidates" bullet immediately above (already closed by the
sibling ticket) or the "Relationship-aware `FORM_PARTY`"/"Multi-step planning" bullets below
(separate, already-ticketed or explicitly-deferred concerns) — or any other section of this design
doc.

**Verify:** No automated test; manual proofread.

## Scope Guards

- **Do not modify `src/cognition/self_model_phase.py`, `SelfModelUpdatePhase.apply()`/`run()`,
  `src/core/builder.py`, or `src/engine/pipeline.py`.** Option (a) — populating a real
  `CapabilityContext` upstream of `SelfModelUpdatePhase.apply()` — is a materially larger,
  cross-subsystem change (deciding what every `ENABLE_SELF_MODEL_COGNITION`-gated entity needs
  estimated every tick, not just adventure-eligible heroes) that this ticket's own Scope section
  frames as one of two options, not a commitment. This plan implements option (b) only.
- **Do not modify `src/cognition/capability_estimate.py` in any way.** AC3 requires its existing
  unit tests (`tests/unit/cognition/test_phase2_capability_estimate_service.py`) to pass unchanged;
  this plan's Step 1 only adds a new *caller* of `CapabilityEstimateService.estimate()` from
  `scoring.py`, never touches the service's own implementation.
- **Do not claim `entity.self_model.capabilities`/`entity.self_model.capabilities.estimates` is
  populated in production anywhere** — in code comments, doc updates, or the ticket's own
  Completion Summary. It remains empty at every real tick after this plan lands; only
  `AdventureRouteScorer.score()`'s own local, throwaway read changes.
- **Do not map `HUNT_WEAK_ENEMY`, `SCOUT_LOCATION`, or any other `RouteFamily`** beyond
  `GATHER_RESOURCE`/`CRAFT_UPGRADE` — `AdventureRouteOption` has no `enemy_id`/`region_id` field to
  build a `combat.enemy_type.*`/`travel.region.*` key from (Design Decision 1); this is not merely a
  "dead code, low priority" judgment call but a genuine data-availability gap.
- **Do not add a `RecipeRegistry`/`ResourceRegistry` (or any other registry) read inside
  `scoring.py`.** `recipe_data`/`resource_data` are reconstructed entirely from `route.requirements`
  and the already-passed-in `resource_nodes` parameter (Design Decision 4) — `scoring.py` imports no
  registry module today and this plan does not introduce one.
- **Do not touch `AdventureGoalScorer`, `AdventureDecisionService.decide()`, or
  `RouteToProjectMapper`.** `entity`/`resource_nodes` already flow to `AdventureRouteScorer.score()`
  unchanged; no new parameter or plumbing is needed.
- **Do not mutate `entity.self_model`, `entity.cognition`, or any other durable entity field from
  `score()`.** `CapabilityEstimateService.estimate()`'s result is used only as a local scoring
  input for this call, never written back via `dataclasses.replace`/`EntityUpdate`.
- **Do not touch the `memory_adjustment` block (`scoring.py:224-241`), `plan_advance_bonus`
  (`scoring.py:213-222`), or any other scoring term** — this plan changes only how `confidence_bonus`
  (`scoring.py:243+`) is computed.
- **Do not change the `0.15` confidence-bonus weight, or add a new additive term to the final-score
  formula.** Design Decision 2 explicitly rejects the additive shape for this ticket.
- **Do not fix the pre-existing 13-vs-16 `RouteFamily` doc/code drift, the `SCOUT_LOCATION`
  "Candidate sources" table inaccuracy, or resync `adventure_contract.md`'s entire formula table**
  beyond the two rows Step 7 specifies — all pre-existing gaps unrelated to this ticket's scope.

## Dependency Map

- Step 1 (scoring logic) must land before Step 2 (tests exercise the new logic) and before Step 4
  (parity ledger cites the implemented constants and test file).
- Step 2 must land before Step 4 (parity ledger's `test_path` must reference an existing, passing
  test file).
- Steps 3, 5, 6, 7, 8 (doc updates) are independent of each other and can land in any order, but all
  should land after Step 1 is finalized (they describe the exact implemented mechanism) and ideally
  in the same session per CLAUDE.md's Parity rule.
- All steps are otherwise independent — no step requires a different step to be redone if it
  changes.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: "The capability_context-never-populated prerequisite gap is explicitly disclosed and resolved as part of this ticket's own scope (not silently assumed already wired)" | Step 1 (ad-hoc call bypasses the gap without touching the upstream pipeline wiring, Design Decision 6); Steps 3, 5, 6, 8 (explicit doc disclosure that `entity.self_model.capabilities` stays empty in production) | `tests/unit/cognition/test_phase2_self_model_phase.py` continuing to show `capability_context` defaulting to `None` at the `apply()`/production level unchanged (no test modification, confirms no upstream wiring was added) |
| AC2: "For a route whose family maps to a capability key, confidence_bonus reflects a real CapabilityEstimate.estimate value, not always the generation-time confidence constant" | Step 1 (GATHER_RESOURCE/CRAFT_UPGRADE branches, Design Decisions 1-4) | Step 2 tests 1, 2 (`test_gather_resource_confidence_reflects_capability_estimate`, `test_craft_upgrade_confidence_reflects_capability_estimate`) prove the estimate-driven value differs from the flat constant; test 3 (`test_capability_confidence_falls_back_to_flat_term_for_unmapped_families`) proves unmapped families keep the flat constant, satisfying "not always" |
| AC3: "Existing isolated CapabilityEstimateService unit tests continue to pass unchanged" | Step 1 makes zero edits to `src/cognition/capability_estimate.py` (only adds a new caller in `scoring.py`) | `tests/unit/cognition/test_phase2_capability_estimate_service.py` (4 test classes: `TestCapabilityCombat`, `TestCapabilityTravel`, `TestCapabilityCraft`, `TestCapabilityGeneral`) run unchanged; confirm via diff review at Verify time that this file is untouched |

## Anti-Drift Notes

- **`CapabilityEstimateService.estimate()`'s `tick`/`state` parameters are both unused in the
  method's actual computation** (Design Decision 5) — passing `tick=0`/`state=None` implicitly is
  correct and requires no new plumbing on `score()`'s own signature. Do not add a `tick` parameter
  to `score()` "just in case" — there is no code path that needs it.
- **`GATHER_RESOURCE`'s `has_item` requirement is unambiguously the required tool** (at most one
  such requirement per route, confirmed `resources.py:78-81`) — **`CRAFT_UPGRADE`'s `has_item`
  requirements are materials, potentially several** (confirmed `services.py:56-59`). Do not reuse
  the same extraction loop/variable semantics between the two branches — they parse structurally
  different (if same-shaped) `Requirement` tuples for different purposes.
- **`route.family` cannot be both `GATHER_RESOURCE` and `CRAFT_UPGRADE` simultaneously** (mutually
  exclusive enum) — the `if`/`elif` structure in Step 1 is not a priority ordering decision.
- **Do not let the `CRAFT_UPGRADE` branch's "unknown recipe" edge case (a real recipe with both
  `gold_cost == 0` and no required materials) get "fixed"** — this is `CapabilityEstimateService`'s
  own pre-existing behavior (`capability_estimate.py:210-219`, `if not requires_items and not
  gold_cost:`), inherited unchanged, not a bug this ticket introduces or should patch.
- **`entity.self_model.capabilities.estimates` remains empty in production after this plan lands.**
  Every doc update (Steps 3, 5, 6, 7, 8) must state this plainly — the ticket's own Request Summary
  language ("Deepen adventure's internal reasoning by making route confidence reflect
  capability-estimate-driven data") is only half-true after this ticket: the *scoring-side* wiring
  becomes real and live-observable (unlike the sibling memory ticket's still-dormant term), but
  `entity.self_model.capabilities` itself is still never populated by the pipeline.
- **This term IS live-observable via a real `generate() → score()` chain today**, unlike
  `memory_adjustment` — both `GATHER_RESOURCE` and `CRAFT_UPGRADE` are live-generated route families
  (confirmed `generator.py:38-45,79-92`), so this is a stronger, more immediately measurable change
  than the sibling ticket's dead-code-family caveat. State this distinction accurately in doc
  updates — do not undersell it by copy-pasting the memory ticket's "not yet live" framing verbatim
  where it does not apply.

## Unresolved Questions

None blocking. All ambiguities flagged in investigation.md (option (a) vs (b), the 2-family mapping
scope, the fallback behavior, the `recipe_data`/`resource_data` reconstruction question) have been
explicitly decided above with code-grounded rationale. If Review disagrees with the replacement-vs-
additive formula placement (Design Decision 2) or the 2-family scope (Design Decision 1), that is a
design disagreement to raise at Review, not a gap in this plan.
