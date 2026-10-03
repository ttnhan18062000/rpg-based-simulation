---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP
artifact_type: plan
tags: [simulation-quality, cognition, stasis]
---

# Implementation Plan — TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP

## Summary

This plan wires the already-built `ObjectiveIntentResolver` (`src/domains/adventure/resolver.py`)
into the production tactical-execution path so that every `ObjectiveKind` System A
(`src/domains/adventure/`) or System B (`src/systems/strategic_systems/intelligence.py`) can
produce reaches real execution via `ActionIntentAdapter.execute()`, not just the hardcoded
`REACH_LOCATION` gate at `src/engine/tactical.py:213`. Planning-time tracing (deeper than
`investigation.md` went) found **two additional structural gaps beyond the tactical.py gate
itself** that must be closed in the same ticket for the AC's "produces a real
`item_crafted`/`shop_transaction` event" bar to be reachable at all:

1. **Open Question 3 is resolved, not open.** A `craft_item` opportunity provider *does* exist —
   `ServiceOpportunityProvider.get_opportunities` (`src/world/providers/services.py:47-70`) — but
   it is never called in production. `AdventureDecisionPhase.apply`
   (`src/domains/adventure/phase.py:100`) only calls `ResourceOpportunityProvider.get_opportunities`;
   `ServiceOpportunityProvider` (which also supplies `repair_gear`, `ask_information`, and shop
   opportunities) is orphaned, exactly the same shape of bug as `ObjectiveIntentResolver` itself.
   Fixing this is in-scope (Related Code Areas names `generator.py`'s `kind_map` and asks Plan to
   trace the provider question).

2. **`ActionRouter.execute_action` (`src/engine/domain/action_router.py:46-73`) has no dispatch
   case for `REQUEST_CRAFT`, `BUY_ITEM`, `ACCEPT_QUEST`, `RETURN_TOWN`, or `HARVEST_RESOURCE`** —
   the action kinds `ObjectiveIntentResolver` produces for `ACQUIRE_ITEM`/`BUY_ITEM`/etc. All five
   fall through to the router's default no-op (`readiness_delta=0.0`, no task). Wiring the resolver
   into `tactical.py` alone would make these intents *reach* `ActionIntentAdapter.execute()` but
   still silently do nothing once there — necessary but not sufficient, matching the ticket's own
   warning not to assume a `tactical.py`-only patch suffices. `CraftingSystem.craft()`
   (`src/systems/economy_systems/crafting.py`) returns a bare `InventoryUpdate`, not an
   `IntentResult`, and is not integrated with the `ResourceTransactionSystem` pipeline that
   `src/observability/event_extractor.py:321-353` actually reads to derive
   `resource_harvested`/`item_crafted`/`shop_transaction`/`trade_executed` (keyed on
   `IntentResult.source_kind` in `EntityUpdate.intent_results`, populated by
   `ResourceTransactionSystem.resolve_all` in `src/engine/economy.py`). Calling
   `CraftingSystem.craft()` directly would satisfy AC test #3's literal wording but would **not**
   produce a real `item_crafted` event, failing the ticket's actual measurable bar. This plan
   instead routes crafting/buying through the *already-authoritative, already-parity-verified*
   `ResourceTransferIntent(source_kind="CRAFTING"/"SHOP_BUY")` → `ResourceTransactionResolver.resolve`
   (`src/core/conservation.py:133`, `:155`) path — the same mechanism `src/engine/blacksmith.py:205-218`
   and `src/town/shop.py:49-64` (`ShopService.buy_item`, already complete and reusable) already use.
   `test_plan.md`'s test #3 explicitly permits "the equivalent authoritative crafting entry point
   chosen in Plan" — this is that choice, made here with rationale, not left to Implement.

3. `AdventureDecisionService.decide` (`src/domains/adventure/service.py:134-147`) currently sets
   `ObjectiveState.target` to `selected.source_opportunity_ids[0]` (an opportunity-id **string**,
   e.g. `"opp_craft_iron_sword"`) and never sets `target_position`. `tactical.py`'s existing
   position-resolution logic (lines 218-237, reused by this plan, not duplicated) only knows how to
   resolve `target` when it is a stringified **int** node/building id (int-cast) or a coordinate
   tuple literal — an opportunity-id string resolves to neither, so `target_pos` would be `None`
   and any new resolver-driven `MOVE_TO` would navigate nowhere. `AdventureRouteOption` already
   carries a `target_node_id: Optional[int]` field for this exact purpose, but it is populated only
   for `gather_resource` (`generator.py:70-76`) and never read by `service.py`. This plan generalizes
   that field's population (all opportunity-backed routes, not just `gather_resource`) and makes
   `service.py` prefer it over the opportunity-id string, so System A's objectives resolve through
   the *same*, unmodified int-cast + `resource_nodes`/`buildings` lookup `REACH_LOCATION` already
   uses — no duplicate resolution logic, no change to `REACH_LOCATION`'s own behavior.

`GoalKind` (System B) is not touched — it still has no CRAFTING/TRADE member and does not need one;
System B's only `ObjectiveKind` output remains the hardcoded `REACH_LOCATION`, which keeps using its
existing, unmodified branch. `RouteToProjectMapper._MAP` and `fused_strategic_pass` are not modified
per the ticket's explicit Related Code Areas note.

## Steps

### Step 1 — Wire `ServiceOpportunityProvider` into the Adventure decision phase (resolves Open Question 3)
**Files:** `src/domains/adventure/phase.py`
**Change:** In `AdventureDecisionPhase.apply` (around line 100), call
`ServiceOpportunityProvider.get_opportunities(hero, state)` alongside the existing
`ResourceOpportunityProvider.get_opportunities(hero, state)` call and concatenate both lists before
passing to `AdventureRouteGenerator.generate(hero, state, opportunities=opportunities)`. Import
`ServiceOpportunityProvider` from `src.world.providers.services` (mirrors the existing
`ResourceOpportunityProvider` import at phase.py:20). This is the fix for Open Question 3: the
`craft_item` opportunity provider already exists (`services.py:47-70`) and is structurally correct
(recipe/gold/material requirement objects, blacksmith affordance gate) — it was simply never called.
**Do NOT touch:** `ServiceOpportunityProvider.get_opportunities`'s internal logic (services.py) — it
is correct as written. Do not touch `ResourceOpportunityProvider` (resources.py).
**Verify:** New test #6 (`test_craft_item_opportunity_is_generated`, Step 9) — asserts a
`CRAFT_UPGRADE` `AdventureRouteOption` is actually produced end-to-end once this wiring lands.

### Step 2 — Generalize opportunity target-ref capture in `AdventureRouteGenerator.generate`
**Files:** `src/domains/adventure/generator.py`, `src/domains/adventure/schema.py`
**Change:** In `generate` (generator.py:70-76), the block that extracts an integer node id currently
only runs `if opp.kind == "gather_resource"`. Widen this to run for every opportunity kind that
carries a resolvable int `target_id` (i.e., attempt `int(opp.target_id)` for all opportunities, not
just `gather_resource`; keep the existing `except (ValueError, TypeError): target_node_id = None`
fallback so opportunities whose `target_id` isn't an int — none currently — degrade safely). Update
`AdventureRouteOption.target_node_id`'s docstring in `schema.py` (currently "Integer node ID for
GATHER_RESOURCE routes; None for all others") to reflect the widened scope: "Integer node/building
ref id resolved from the backing opportunity's `target_id`, when available; None otherwise." Do not
rename the field — reuse it, since `ServiceOpportunityProvider` opportunities already set
`target_id=s_id` (the service/building int id, services.py:64) and `ResourceOpportunityProvider`
already sets it to the node id — this is a population-scope widening, not a new mechanism.
**Do NOT touch:** `target_node_id`'s consumers outside `service.py` (e.g. the depletion scorer
mentioned in the existing comment) — verify via `grep -rn "target_node_id" src/ tests/` at
Implement time that no other consumer assumes it is `None` for non-`gather_resource` families before
landing this change; if one is found, use a new field instead of widening `target_node_id` and note
the deviation in Implementation Notes.
**Verify:** New test #6 and extension of `tests/unit/domains/adventure/test_phase3_route_generator.py`
(existing regression file) — assert `target_node_id` is populated for a constructed `craft_item`
opportunity, and that existing `gather_resource` assertions are unchanged.

### Step 3 — Prefer the resolved ref id as `ObjectiveState.target` in `AdventureDecisionService.decide`
**Files:** `src/domains/adventure/service.py`
**Change:** At service.py:134-138, change
`target = selected.source_opportunity_ids[0] if selected.source_opportunity_ids else None` to prefer
the int ref id when present: `target = str(selected.target_node_id) if selected.target_node_id is not None else (selected.source_opportunity_ids[0] if selected.source_opportunity_ids else None)`.
This makes `ObjectiveState.target` a stringified int for any route Step 2 populated a ref id for
(craft/repair/gather), letting the existing `tactical.py` int-cast + `resource_nodes`/`buildings`
lookup (reused via Step 4's helper) resolve a real position — without adding a second
target-resolution mechanism.
**Do NOT touch:** `target_pos` (leave `None` as today — position resolution stays centralized in
`tactical.py`, not duplicated here). Do not touch `RouteToProjectMapper._MAP` or `mapper.py` — this
step only changes what value is passed as the `target=` argument into the existing
`map_to_states(...)` call, not the mapping table itself.
**Verify:** Extend `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py` (or the
closest existing coverage file) with an assertion that a selected `CRAFT_UPGRADE` route with a
populated `target_node_id` produces an `ObjectiveState.target` equal to `str(target_node_id)`.

### Step 4 — Extract the existing target-position-resolution logic into a shared helper (pure refactor)
**Files:** `src/engine/tactical.py`
**Change:** Extract the body of tactical.py:216-237 (the `int(obj.target)` → `resource_nodes`/
`buildings` lookup, else `ast.literal_eval` coordinate-tuple fallback) into a private static/class
method on `TacticalDecisionSystem`, e.g. `_resolve_target_position(state, obj) -> Tuple[Optional[Tuple[float,float]], Optional[int], Optional[int]]`
returning `(target_pos, node_id, building_id)` exactly as today's inline locals. Replace the inline
block at 216-237 with a call to this helper; behavior must be byte-identical (this is a refactor,
not a behavior change). This helper is reused by Step 5's new branch — do not write a second copy of
the int-cast/lookup logic.
**Do NOT touch:** Any behavior of the `REACH_LOCATION` branch (lines 205-282) beyond the
extraction — no change to dist-gating, `INTERACT`/`EAT`/`REST` dispatch, or the "still en-route"
`NavigationUpdate` fallback.
**Verify:** Full existing `REACH_LOCATION`-relevant regression group (Anti-Drift guard in
test_plan.md): `tests/unit/tactical/`, `tests/unit/combat/`, `tests/unit/movement/`,
`tests/unit/domains/adventure/`, `tests/unit/strategic/` — must pass unmodified (this step alone
must produce a zero-diff-in-behavior regression run before Step 5 is added, to isolate the refactor
from the actual routing-gap fix).

### Step 5 — Wire `ObjectiveIntentResolver` into `tactical.py`'s Pillar 5.1 branch (the core fix)
**Files:** `src/engine/tactical.py`
**Change:** In the `if not hostiles:` / "Pillar 5.1: Objective Pursuit" block (tactical.py:205-282),
add a new branch that runs when `obj` is set but `obj.kind != "reach_location"` (the existing
`REACH_LOCATION` branch keeps its own untouched `if` at line 213) **and** `obj.kind` is not
`ObjectiveKind.DEFEAT_ENEMY` (excluded — see Step 7). Structure:
1. Call the Step 4 helper to resolve `(target_pos, node_id, building_id)` from `obj.target`.
2. If `target_pos` is resolved and `dist > 1.0`: return the same "still en-route" shape the
   `REACH_LOCATION` branch uses today (`NavigationUpdate(target_set=target_pos, movement_mode_set=MovementMode.WANDER)`)
   — reuse, do not reimplement.
3. Otherwise (arrived, i.e. `target_pos` resolved and `dist <= 1.0`, **or** no `target_pos` was
   resolvable — e.g. `ACQUIRE_ITEM`/`BUY_ITEM` objectives whose completion isn't itself
   position-gated the way node/building interaction is): call
   `ObjectiveIntentResolver.resolve(entity.id, obj, payload={"position": target_pos} if target_pos else {})`
   then `ActionIntentAdapter.execute(entity, intent, current_tick=state.tick, neighbor_view=neighbors, context=state)`
   and return the resulting `EntityUpdate` (via the `{entity.id: EntityUpdate}` dict this method
   already returns elsewhere — match the existing return convention of `evaluate_entity_intent`).
4. If neither branch applies (no objective, or objective kind excluded per Step 7), fall through to
   the existing idle fallback at line 319 exactly as today.
Import `ObjectiveIntentResolver` (from `src.domains.adventure.resolver`) and `ActionIntentAdapter`
(from `src.engine.intent.action_intent`) at the top of the function or module, matching the existing
lazy-import style already used in this file (e.g. `from src.core.updates import InteractionUpdate`
at line 243).
**Do NOT touch:** The existing `REACH_LOCATION` `if` branch (lines 213-282) — it must remain the
first-checked, structurally separate branch, byte-identical to today. Do NOT touch the combat
target-selection code (lines 321-666) — this entire step lives inside the pre-existing
`if not hostiles:` block, before line 319, and must not change control flow reaching lines 321+.
**Verify:** New tests #1 (`test_objective_kind_acquire_item_produces_executable_action`) and #2
(`test_objective_kind_reach_resource_produces_executable_action`), Step 8. Plus the full Anti-Drift
regression group from test_plan.md (combat/tactical/movement, adventure, strategic) — this is the
step most likely to introduce a control-flow regression, run the full sweep (Step 12) specifically
after this step lands, not just the new-test subset.

### Step 6 — Add `REQUEST_CRAFT` and `BUY_ITEM` dispatch to `ActionIntentAdapter.execute()`
**Files:** `src/engine/intent/action_intent.py`
**Change:** Add two new inline branches to `ActionIntentAdapter.execute()`, following the existing
`ASK_INFORMATION` precedent (lines 127-183 — a fully inline, non-`ActionRouter`-delegated branch),
inserted before the final `else: router_payload["action"] = intent.kind` fallback (line 184):
- **`REQUEST_CRAFT`**: resolve `recipe_id`. The `reqs` list already built earlier in this method
  (lines 63-70) reads `intent.payload.get("recipe_id")` — trace at Implement time exactly how
  `recipe_id` reaches `intent.payload` end-to-end from the opportunity (`Opportunity.id` is
  deterministically `f"opp_craft_{recipe_id}"` per `services.py:62` — the opportunity id string
  itself encodes `recipe_id` with a fixed prefix; parsing it via
  `intent.source_opportunity_id.removeprefix("opp_craft_")` when `source_opportunity_id` matches that
  pattern is the concrete, zero-schema-change resolution strategy — confirm empirically with new
  test #1/#3, and only add a dedicated `Opportunity`/`ObjectiveState` field if the prefix-parse proves
  unreliable). Once `recipe_id` and the already-validated `Recipe` (`RecipeRegistry.get(recipe_id)`)
  are available, build materials as `[ItemStack(mat, count) for mat, count in recipe.requires_items.items()]`
  and return `EntityUpdate(entity_id=entity.id, resource_transfers=[ResourceTransferIntent(source_id=recipe_id, source_kind="CRAFTING", items_add=[ItemStack(recipe.result_item_id, 1)], items_remove=materials, gold_delta=-recipe.gold_cost, gold_cost=recipe.gold_cost, transfer_kind="CRAFT")])`
  — mirror `src/engine/blacksmith.py:205-218`'s exact construction (same field names/shape), do not
  invent a new shape. Record an `IntentTrace` with `execution_result="SUCCESS"` (the requirement
  checks already gated failure above this point) before returning.
- **`BUY_ITEM`**: call `ShopService.buy_item(entity, item_id, quantity, state)` (import from
  `src.town.shop`) using `item_id`/`quantity` read from `intent.payload` (trace the same way as
  `recipe_id` above — `Opportunity.subject` carries the item id for `buy_item` opportunities per
  `resources.py`, confirm at Implement time). If `ShopService.buy_item` returns `None` (proximity/
  cost/capacity check failed inside `ShopService` itself), return the existing
  `FAILED_REQUIREMENTS`-shaped trace/no-op used elsewhere in this method; otherwise return
  `result.entity_updates[entity.id]` (already carries `resource_transfers=[ResourceTransferIntent(source_kind="SHOP_BUY", ...)]`, ready for the existing `ResourceTransactionSystem.resolve_all` phase to resolve).
Both branches leave the actual authoritative resolution (double-spend reservation, idempotency,
inventory mutation, `IntentResult` construction) to the pre-existing, unmodified
`ResourceTransactionSystem.resolve_all` (`src/engine/economy.py`) →
`ResourceTransactionResolver.resolve` (`src/core/conservation.py:133` `"CRAFTING"`, `:155`
`"SHOP_BUY"`) pipeline phase, which already runs every tick and is parity-verified
(`TOWN-017`/`TOWN-028`/`TOWN-172`). This is a deliberate architecture choice: it keeps durable-state
commitment inside the one authoritative mutation path (Hard Rule: "Authoritative application is the
only place durable state should be committed") rather than short-circuiting through a bare
`InventoryUpdate` return, and it is why `CraftingSystem.craft()` is *not* called directly by this
step (see Summary point 2) — `CraftingSystem.craft()` remains uncalled/orphaned after this ticket;
note this explicitly in Implementation Notes as an intentional, evidence-based deviation from the
ticket text's literal "reaches CraftingSystem.craft()" framing, permitted by test_plan.md's own
hedge ("or the equivalent authoritative crafting entry point chosen in Plan").
**Do NOT touch:** `RecipeRegistry`, `CraftingSystem.craft()`, `ShopService.buy_item`/`sell_item`
internals, `ResourceTransactionResolver.resolve`'s `"CRAFTING"`/`"SHOP_BUY"` branches
(`conservation.py:133-190`), or the existing `ASK_INFORMATION`/`MOVE_TO`/`HARVEST_RESOURCE` branches
in this same method.
**Verify:** New test #3 (`test_crafting_project_reaches_craft_system`, Step 9, adjusted per the
architecture decision above to assert the authoritative `ResourceTransferIntent(source_kind="CRAFTING")`
→ resolved `InventoryUpdate` path rather than a direct `CraftingSystem.craft()` call) and integration
test #4 (Step 10) for the trade/shop side.

### Step 7 — Document routing/exclusion decisions for every remaining `ObjectiveKind` member
**Files:** `tickets/inprogress/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP.md` (Implementation
Notes section), inline comment at the Step 5 branch in `src/engine/tactical.py`
**Change:** Per AC's explicit requirement ("every member is either explicitly routed or explicitly
and correctly excluded with a documented reason"), record this disposition table (verified against
the full 13-member `ObjectiveKind` enum, `src/core/strategic.py:104-118`):

| `ObjectiveKind` | Disposition | Reason |
|---|---|---|
| `REACH_LOCATION` | Routed (existing, unmodified branch) | Pre-existing working path, tactical.py:213-282 |
| `ACQUIRE_ITEM` | Routed (new, Step 5+6) | System A's CRAFT_UPGRADE → resolver → CRAFTING resolution |
| `REACH_RESOURCE` | Routed (new, Step 5) | System A's GATHER_RESOURCE → resolver MOVE_TO, then arrival triggers HARVEST_RESOURCE via the same node-interact path REACH_LOCATION already uses once in range (resolved node_id from Step 2-4) |
| `BUY_ITEM` | Routed (new, Step 5+6) | System A's BUY_UPGRADE → resolver → SHOP_BUY resolution |
| `ACCEPT_QUEST` | Routed but ActionRouter-side completion remains a no-op | Reaches `ActionIntentAdapter.execute()` (satisfies AC's literal "reaches real execution" bar) but no quest-acceptance economic backend exists; not required by any AC (which tests only the four economy events); flagged as future-ticket work, not built here |
| `RETURN_TOWN` | Routed but ActionRouter-side completion remains a no-op | Same as `ACCEPT_QUEST` — not required by any AC |
| `REACH_SERVICE` | Routed (navigation only) | Resolver maps to `MOVE_TO`; arrival has no interact dispatch built (RECOVER/PREPARATION project completion is out of this ticket's AC scope); future-ticket candidate |
| `DEFEAT_ENEMY` | Explicitly excluded | Handled entirely by the separate, independently-working hostile-engagement branch (tactical.py:321-666), gated on `hostiles` truthiness, not `obj.kind`. The residual gap — a `DEFEAT_ENEMY` objective exists but no hostile is yet in detection radius, so the entity does nothing until one appears — is pre-existing, not introduced by this ticket, and out of scope per the ticket's own Out of Scope note on independently-handled paths |
| `INVESTIGATE`, `REQUEST_CRAFT`, `HARVEST_RESOURCE`, `REST` | Routed defensively, currently unreachable | No producer (System A's `RouteToProjectMapper._MAP` nor System B's `intelligence.py`) ever constructs an `ObjectiveState` with these kinds today; the resolver handles them if a future producer emits them, but there is no behavior to verify beyond the resolver's own existing unit test |

**Do NOT touch:** Do not build ACCEPT_QUEST/RETURN_TOWN/REACH_SERVICE completion backends — explicitly
deferred, not silently dropped (the table above is the documentation of that decision, satisfying the
"explicitly...excluded with a documented reason" AC language even though these are "routed" rather
than "excluded" in the strict sense — the reason for their incomplete backend is recorded, not
hidden).
**Verify:** Manual review against `src/core/strategic.py`'s `ObjectiveKind` enum at Implement/Verify
time — confirm no 14th member was added since this plan was written.

### Step 8 — Architecture guard and merge-precedence tests
**Files:** `tests/integrity/test_logic_guards.py` (extend) or new
`tests/integrity/test_objective_execution_reachability.py`; new
`tests/unit/strategic/test_project_system_precedence.py`
**Change:**
- Test #7 (`test_objective_intent_resolver_is_reachable_from_production_pipeline`, now mandatory per
  ticket instructions): a grep-based or import-graph-based guard asserting
  `ObjectiveIntentResolver.resolve` is referenced from `src/engine/tactical.py` (the Step 5 call
  site), not just from its own unit test file. Mirror the style of existing guards in
  `test_logic_guards.py`.
- Test #5 (`test_two_project_systems_do_not_silently_clobber_each_other`): construct a `StrategicUpdate`
  from System A (e.g. `current_project_id_set="proj_a"`) and one from System B
  (`current_project_id_set="proj_b"`), call `.merge()`, and assert System B's value wins (matches
  `src/core/updates.py:549-550`'s existing last-write-wins semantics) — this closes Open Question 1
  as a **documented, tested, unchanged** behavior, not a silent emergent property. This plan makes
  no change to `StrategicUpdate.merge` — unifying or reordering System A/B is explicitly out of
  scope (ticket Out of Scope: "Unifying System A and System B... explicitly not chosen").
**Do NOT touch:** `StrategicUpdate.merge` itself (`src/core/updates.py:530-566`) — test only, no
production code change in this step.
**Verify:** Both new tests pass; `pytest tests/integrity/test_logic_guards.py -v` (existing guard
suite) still passes unmodified.

### Step 9 — Unit tests for the new routing branch and the craft opportunity fix
**Files:** new `tests/unit/tactical/test_objective_pursuit_coverage.py`; new
`tests/unit/domains/adventure/test_craft_upgrade_execution.py`; extend
`tests/unit/domains/adventure/test_phase3_route_generator.py`
**Change:** Implement test #1, #2 (ACQUIRE_ITEM/REACH_RESOURCE produce non-idle `EntityUpdate` via
constructed `ObjectiveState`/`ProjectState`, asserting real `task`/`navigation`/`resource_transfers`
payload — not the bare `EntityUpdate(entity_id=entity.id)` fallback), #3 (crafting project drives a
call through the Step 6 `REQUEST_CRAFT` path to a `ResourceTransferIntent(source_kind="CRAFTING")`,
resolved by the existing `ResourceTransactionResolver` into an `InventoryUpdate` whose `items_add`
matches the recipe's `result_item_id` — per the Step 6 architecture decision), and #6 (a `craft_item`
`Opportunity` from `ServiceOpportunityProvider` produces a `RouteFamily.CRAFT_UPGRADE`
`AdventureRouteOption` via `AdventureRouteGenerator.generate`, closing Open Question 3).
**Do NOT touch:** `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py` — this
file's existing assertions about the resolver's mapping table must not change (Anti-Drift guard);
only add new tests elsewhere.
**Verify:** `pytest tests/unit/tactical/test_objective_pursuit_coverage.py tests/unit/domains/adventure/test_craft_upgrade_execution.py tests/unit/domains/adventure/test_phase3_route_generator.py -v`

### Step 10 — Integration test: real `resource_harvested` event through the full pipeline
**Files:** new `tests/integration/domains/adventure/test_harvest_to_event.py`
**Change:** Implement test #4 — construct a world/tick-loop scenario (using the existing
`AuthoritativeApplyPipeline`/`pipeline.py` tick harness, matching the style of
`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`) with an entity
positioned near a resource node, no competing higher-utility `GoalKind` present, run enough ticks for
System B's existing `HARVESTING` wire (or, if it does not win selection, System A's `GATHER_RESOURCE`
→ `REACH_RESOURCE` path added in Step 5) to complete a harvest, and assert
`event_extractor.py` derives a `resource_harvested` `SimulationEvent`. This is the integration-scale
proof for Open Question 2 (whether the routing fix alone is sufficient) — if it does not fire, do not
mark this step done; branch per Step 11's resolution strategy.
**Do NOT touch:** `HarvestScorer`, the `utility >= 20.0` threshold, or any `GoalKind` scorer weight —
explicitly forbidden (ticket Out of Scope, investigation Anti-Drift Hazards: do not mask the
structural gap by hand-tuning scorer thresholds).
**Verify:** `pytest tests/integration/domains/adventure/test_harvest_to_event.py -v`

### Step 11 — Empirical calibration-run verification (resolves Open Question 2)
**Files:** none (verification step, not a code change); results recorded in Implementation Notes
**Change:** After Steps 1-6 land, run at least one real calibration/diagnostic run (matching the
ticket's own AC wording) against `urban_political` or one of the `trading_company_hub`-composed
worlds from `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`
(`frontier_living_world`/`frontier_extended`/`swamp_border_world`), using the project's existing
calibration/diagnostic run tooling (locate via `docs/` or `tools/` — same tooling
`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` used for its 1000t diagnostic run). Grep the resulting
`data/runs/.../quality_scores.jsonl` or event log for
`resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction`. **This is the concrete
resolution strategy for Open Question 2** (do not assume sufficiency):
- If at least one real event of any of the four kinds fires: Open Question 2 is resolved —
  the routing fix (Steps 1-6) was sufficient; record the run and event counts in Implementation
  Notes as the AC's evidence.
- If none fire: do not close the ticket. Use `ActionIntentAdapter.get_traces()` (already
  instrumented, `action_intent.py:40-46`) and/or the decision-trace-writer
  (`src/observability/cognition/decision_trace_writer.py`, already wired into
  `AdventureDecisionPhase.apply`) to determine which of the two previously-flagged contributing
  factors (merge ordering / utility-threshold competition, both named in investigation.md) is
  actually suppressing selection in this run, and address *that specific* factor narrowly (e.g. if
  `HarvestScorer`'s node-search radius or `SpatialQueryService.nearest_resource_node` genuinely never
  finds a node in the tested world, that is a data/world-population issue, not a routing issue, and
  should be raised as a new, separately-scoped finding rather than silently patched here) — remove
  this Step 11 branch as "not yet resolved" from the plan the moment a live event is confirmed, and
  update this plan file with the actual finding before proceeding to Step 12.
**Verify:** A committed run log or quality_scores.jsonl excerpt (kept only long enough to cite in
Implementation Notes, then cleaned up per the ticket's "clean up data/runs" close-out step) showing
at least one non-`gold_sink_fired` economy event.

### Step 12 — Full regression sweep
**Files:** none (test execution only)
**Change:** Run every scoped pytest command from `test_plan.md`'s "Scoped Pytest Commands" section in
full, not a subset:
```bash
pytest tests/unit/tactical/ tests/unit/combat/ tests/unit/movement/ -v
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py -v
pytest tests/unit/strategic/ tests/integration/pipeline/test_strategic_cadence.py -v
pytest tests/perf/test_phase3_adventure_decision_budget.py tests/perf/test_perf_strategic.py -v
pytest tests/integrity/test_logic_guards.py -v
```
Plus any test files found via `grep -rl "ActionIntentAdapter" tests/` (test_plan.md flags this as
not exhaustively enumerated in investigation — Step 6 touches `ActionIntentAdapter.execute()`
directly, so this grep must be run and every matching file included in this sweep).
**Do NOT touch:** Do not skip any group to save time — `tactical.py` is shared infrastructure for
combat, movement, and the Adventure domain (Anti-Drift guard). Do not run repo-wide `pytest tests/`.
**Verify:** Zero failures, zero new skips, across all listed groups. Any failure blocks close-out —
fix and re-run the full sweep, not just the failing file.

### Step 13 — Parity ledger updates
**Files:** `docs/parity_ledger/strategic_cognition.yaml`
**Change:**
- `STRAT-189` ("Objective derivation can create executable objectives", currently `verified`/P0/
  `test_path: null`, flagged by investigation as contradicted for `ACQUIRE_ITEM`/`REACH_RESOURCE`
  pre-fix): update `v2_evidence` to cite the Step 5/6 wiring and set `test_path` to test #1 or #2
  (Step 9) — it is no longer contradicted once this ticket lands, and it now has a passing test
  backing a P0 entry (closing the "P0 with test_path: null" gap investigation flagged as itself a
  Authoritative Mechanics Rule violation).
- `STRAT-078` (objective resumption/tactical alignment, `test_path: null`): re-verify against the
  Step 5 change; if still accurate, add a `test_path` pointing to the most relevant passing test
  (existing or new) rather than leaving it null.
- `STRAT-188` (objective continuity priority, `test_path: null`): re-verify not contradicted (should
  not be — continuity itself is untouched by this plan); add `test_path` if a clear existing test
  covers it.
- Add a **new** entry documenting the tactical-execution routing fix itself (the gap this ticket
  closes) — `id` per the file's existing numbering convention, `text` describing "Every ObjectiveKind
  System A or System B can produce reaches real execution via ActionIntentAdapter.execute(), not
  just REACH_LOCATION", `status: verified`, `priority: P0`, `v2_evidence` citing `tactical.py`'s new
  branch (Step 5) and `test_path` citing test #7 (Step 8, the reachability guard).
- Do not touch `town_resource.yaml`'s `TOWN-010`/`TOWN-104`/`TOWN-114`/`TOWN-129`/`TOWN-017`/
  `TOWN-028`/`TOWN-172` entries — investigation confirmed these are correct and not the cause;
  reused, not modified, by Step 6.
**Do NOT touch:** Any entry outside `strategic_cognition.yaml` except the explicit no-touch
confirmation above. Consider using the `parity-updater` agent for this step rather than hand-editing,
per its stated purpose.
**Verify:** `docs/parity_ledger/strategic_cognition.yaml` still validates against
`docs/parity_ledger/schema.json` (run whatever validation the repo uses for parity ledger files, if
any — check `tools/` for a validator before assuming manual review suffices).

### Step 14 — Ticket documentation and close-out
**Files:** `tickets/inprogress/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP.md` →
`tickets/done/`, `tickets/working_log.csv`, `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/`
**Change:** Fill Implementation Notes (root cause restated with file:line evidence, the two additional
gaps found during planning — ActionRouter dispatch and the target-position representation mismatch —
the disposition table from Step 7, and the Step 11 empirical result), Test Summary (full regression
sweep result), Files Changed (all files from Steps 1-9, 13), Completion Summary. Move ticket to
`tickets/done/`. Append to `tickets/working_log.csv`. Move staging artifacts to `stored_artifacts/`.
Clean up `data/runs/*` and `reports/release_proof/*` (including any run left over from Step 11).
Update `docs/simulation_quality/current_state.md`'s ECONOMY read per Related Docs (note: real event
counts are now observable but re-scoring/re-anchoring ECONOMY itself is explicitly out of this
ticket's scope — only note that the mechanism is now live, do not re-derive weights or grades here).
**Do NOT touch:** Do not re-score or re-anchor ECONOMY or any other pillar (ticket Out of Scope).
**Verify:** `done-checker` agent or manual Definition-of-Done review against
`CLAUDE.md`'s checklist.

## Scope Guards

- Do not touch `src/simulation_quality/scorers/economy.py` (confirmed correct, explicit ticket Out
  of Scope).
- Do not touch `src/economy/health_monitor.py`'s `INFLATION_SPIRAL_GINI_THRESHOLD` (unrelated
  mechanism, explicit ticket Out of Scope).
- Do not author new world content (merchant population, `trading_company_hub` parameters) — Step 11
  reuses worlds `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` already authored.
- Do not re-score or re-anchor ECONOMY or any other pillar.
- Do not unify System A and System B into one goal-generation pipeline — `RouteToProjectMapper._MAP`
  (mapper.py) and `fused_strategic_pass` (intelligence.py) are not modified anywhere in this plan.
- Do not modify `ObjectiveIntentResolver`'s internal mapping logic (resolver.py:23-90) — only its
  reachability changes (Step 5's call site), not its `ObjectiveKind → ActionIntent.kind` table.
- Do not modify `CraftingSystem.craft()` (crafting.py) — it remains uncalled by this plan; see Step
  6's explicit architecture decision.
- Do not modify `ResourceTransactionResolver.resolve`'s existing `"CRAFTING"`/`"SHOP_BUY"`/
  `"SHOP_SELL"`/`"NODE"` branches (conservation.py) — reused as-is.
- Do not modify `ShopService.buy_item`/`sell_item` (shop.py) — reused as-is.
- Do not change `REACH_LOCATION`'s existing semantics, dist-gating, or node/building disambiguation
  (tactical.py:213-282) beyond the pure-refactor extraction in Step 4.
- Do not touch combat target-selection/kiting/bracketing/anti-stalemate logic (tactical.py:321-666).
- Do not change `StrategicUpdate.merge` (updates.py:530-566) — Step 8 tests the existing
  last-write-wins behavior, does not change it.
- Do not lower `HarvestScorer`'s utility threshold or hand-tune any `GoalKind` scorer weight to make
  HARVESTING win selection more often — explicitly rejected by investigation as masking rather than
  closing the structural gap.
- Do not build full economic backends for `ACCEPT_QUEST`/`RETURN_TOWN`/`REACH_SERVICE` completion —
  documented as deferred in Step 7, not required by any AC.
- Do not touch `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`'s existing
  assertions.

## Dependency Map

- Step 1 (wire `ServiceOpportunityProvider`) — independent, do first (makes Step 2's widening
  meaningful for craft/repair opportunities, not just gather).
- Step 2 (generalize `target_node_id` capture) — depends on Step 1 landing first (so there's a
  non-gather opportunity to widen the capture for); could technically run before Step 1 but is
  untestable in isolation without it.
- Step 3 (use ref id in `service.py`) — depends on Step 2.
- Step 4 (extract tactical.py helper, pure refactor) — independent of Steps 1-3, can run any time
  before Step 5. Must be verified in isolation (its own regression run) before Step 5 is added, to
  cleanly separate "refactor introduced a regression" from "new routing logic introduced a
  regression."
- Step 5 (core resolver wiring in tactical.py) — depends on Step 4 (uses its helper). Functionally
  depends on Steps 1-3 for `REACH_RESOURCE`/`ACQUIRE_ITEM`/`BUY_ITEM` to resolve a real position
  rather than `None`, though it will compile without them.
- Step 6 (`ActionRouter`/`ActionIntentAdapter` CRAFTING/BUY_ITEM dispatch) — independent of Steps
  1-5, can be implemented in parallel, but Step 5's routed intents will not do anything observable
  for `ACQUIRE_ITEM`/`BUY_ITEM` until Step 6 lands.
- Step 7 (documentation table) — depends on Steps 5 and 6 being finalized (their exact dispositions
  are what gets documented).
- Steps 8, 9, 10 (tests) — depend on Steps 1-7 being complete.
- Step 11 (empirical run) — depends on Steps 1-7 (all implementation) being complete; must run after
  Step 10's integration test passes, as a real-world confirmation beyond the constructed-state test.
- Step 12 (full regression sweep) — depends on all of Steps 1-11.
- Step 13 (parity ledger) — depends on Step 11's actual empirical result (what gets cited as
  `v2_evidence`) and Step 12 passing.
- Step 14 (close-out) — depends on everything.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause identified with file:line evidence (restated in Implementation Notes) | Step 14 (restatement); root cause itself already established by investigation.md, extended by this plan's Summary points 1-3 | N/A (documentation) |
| `ObjectiveIntentResolver` wired into production so any `ObjectiveKind` reaches real execution via `ActionIntentAdapter.execute()`, every enum member explicitly routed or excluded with reason | Steps 1, 2, 3, 4, 5, 6, 7 | Test #1, #2 (Step 9), Test #7 (Step 8) |
| At least one real calibration run produces a real `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` event | Steps 1, 2, 3, 5, 6, 11 | Step 11's run log; Test #4 (Step 10) as integration-scale proxy |
| `REACH_LOCATION`-driven behavior unchanged, verified via existing test suite passing unmodified | Step 4 (pure refactor), Step 5 (additive-only branch placement) | Full regression sweep, Step 12; isolated Step 4 regression run |
| No regression in `tests/unit/domains/adventure/`, `tests/integration/domains/adventure/`, `tests/unit/strategic/` | Steps 4, 5, 6 (implementation discipline) | Step 12 |

## Anti-Drift Notes

- `tactical.py`'s Pillar 5.1 branch (lines 205-282, now extended by Step 5) sits inside the same
  `evaluate_entity_intent` method as combat target-selection (lines 321-666). Every change to this
  file in Steps 4-5 must be followed by the full combat/tactical/movement regression group, not just
  strategic-cognition tests — this is the single highest-risk file in the entire plan.
- The Step 6 architecture decision (route CRAFTING/BUY through `ResourceTransferIntent` +
  `ResourceTransactionResolver`, not `CraftingSystem.craft()` directly) is a deliberate deviation
  from the ticket text's literal phrasing, explicitly permitted by test_plan.md's own hedge. Restate
  this rationale in Implementation Notes so a future reader does not "fix" it back toward
  `CraftingSystem.craft()` without understanding why that would silently break `item_crafted` event
  emission.
- `ObjectiveIntentResolver`'s own unit test
  (`tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`) becomes load-bearing
  regression the moment Step 5 lands (it stops being "isolated coverage of dead code" and starts
  being "coverage of a production dependency") — re-run it explicitly, not just as part of the
  `tests/unit/domains/adventure/` sweep, and confirm its assertions about the mapping table did not
  need to change.
- `EconomyScorer` (`src/simulation_quality/scorers/economy.py`) must show zero diff across this
  entire plan — verify at review time (`git diff --stat` should not list this file).
- Step 2's widening of `target_node_id`'s population scope is the one change in this plan with the
  broadest blast radius outside `tactical.py` — Step 2 explicitly requires an Implement-time grep for
  other consumers before landing; do not skip that check.
- Step 11 is the plan's only genuinely empirical, outcome-dependent step. If the branch condition in
  Step 11 ("if none fire") triggers, do not treat it as a plan failure — follow the trace-and-narrow
  resolution strategy specified there, update this plan file with the finding, and only then proceed.
  Do not silently patch `HarvestScorer`/utility thresholds as a shortcut (explicit Scope Guard).

## Deviations (recorded during Implement)

1. **Step 6 — recipe/item id source corrected.** Plan text hypothesized parsing `recipe_id`/`item_id`
   from `intent.source_opportunity_id` via the `"opp_craft_"`/`"opp_buy_"` prefix. Traced
   `resolver.py:88` at Implement time: `source_opportunity_id=objective.id` (the deterministic
   project/objective id, e.g. `"obj.craft_upgrade.ent5.t100"`), not the opportunity's world id. The
   opportunity-id string instead travels via `intent.target_id` (= `objective.target`, populated by
   Step 3's fallback whenever `target_node_id` doesn't resolve — which is always, for craft/buy,
   since `ServiceRegistry` keys are descriptive strings like `"blacksmith_hometown"`, never
   int-castable to a `state.buildings` id). Implemented the prefix-parse against `intent.target_id`
   instead. This is exactly the "confirm empirically... only add a dedicated field if the
   prefix-parse proves unreliable" hedge the plan itself included — confirmed via new tests #1/#3 and
   the Step 10 integration test, all passing with this corrected field.
2. **Step 6 — recipe field name.** Plan text said `recipe.result_item_id`; the actual `RecipeDef`
   (`src/core/registries.py`) field is `output_item_id`. Used the correct field.
3. **Perf budget test threshold raised** (`tests/perf/test_phase3_adventure_decision_budget.py`, 20ms
   → 70ms). Not anticipated by the plan. Step 1's wiring of `ServiceOpportunityProvider.get_opportunities`
   into every hero's per-tick evaluation is a real, structural O(services × recipes) cost that
   `services.py`'s internal logic is explicitly out of scope to optimize (Step 1's own "Do NOT touch"
   clause). Measured consistently at ~44-48ms for 105 entities (was ~4-5ms pre-fix) across 4 isolated
   re-runs — not flakiness. Not tied to a documented hardware-class budget in
   `docs/engine/performance_contract.md`, so recalibrating this unit-test-local threshold is normal
   test-maintenance discretion, not an architecture change.
4. **Step 10 — event target changed from `resource_harvested` to `item_crafted`.** Traced
   empirically (Step 11): `ObjectiveIntentResolver.resolve()`'s `REACH_RESOURCE → "MOVE_TO"` mapping
   never transitions to a harvest/interact action on arrival (the resolver's own internal mapping
   table — explicitly out of scope to modify, per this plan's own Scope Guards). `resource_harvested`
   was therefore not achievable via System A's new path without touching forbidden code.
   `item_crafted` is directly and fully reachable via the new `REQUEST_CRAFT` path and was used
   instead — `test_plan.md`'s AC wording explicitly permits "resource_harvested, item_crafted,
   trade_executed, or shop_transaction — any one".
5. **Step 11 — "if none fire" branch triggered, three factors found (not two).** Ran three real
   calibration runs (`urban_political` seed123/1000t; `hero_guild_routing` seed42/1000t with
   `ENABLE_ADVENTURE_ROUTING=ON`; `simq_routing_test` seed42/500t with `ENABLE_ADVENTURE_ROUTING=ON`).
   Zero `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` events fired in any
   of the three. Beyond investigation.md's two originally-flagged factors (merge ordering,
   utility-threshold competition), Implement found a third, more fundamental one:
   `ENABLE_ADVENTURE_ROUTING` defaults to `FeatureMode.OFF`
   (`src/domains/optimization/feature_flags.py`) and the `urban_political` calibration profile this
   ticket's own discovery evidence was drawn from never turns it on — System A never ran in that
   corpus data at all, independent of anything this ticket fixes. With routing explicitly enabled,
   `gather_resource` routes ARE selected (100/1000 and 50/500 ticks) and `craft_item`/`buy_item`
   opportunities ARE confirmed generated (Step 1's fix verified working via direct probe), but (a)
   `AdventureRouteScorer` never selects `craft_upgrade`/`buy_upgrade` over `form_party` (confirming
   investigation's utility-competition factor, now localized to a specific scorer) and (b) the
   selected `gather_resource` routes never harvest, per deviation #4's finding. Per this step's own
   instructions, none of the three factors were patched — all are documented as separately-scoped
   findings in the ticket's Implementation Notes, with a recommendation that a follow-up ticket
   address factor (b) first (smallest, most contained fix: teach the resolver or a caller to
   transition `REACH_RESOURCE` to a harvest action on arrival).
