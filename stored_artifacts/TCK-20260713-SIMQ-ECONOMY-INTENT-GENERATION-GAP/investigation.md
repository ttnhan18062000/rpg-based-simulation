---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP
artifact_type: investigation
tags: [simulation-quality, cognition, stasis]
---

# Investigation — TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP

## Current Behavior

### Two independent, structurally divergent project/objective-generation systems exist

Both write to the same durable field (`entity.strategic.current_project_id` /
`current_objective_id`, `src/core/strategic.py:346-347`) every tick, but they build objectives
with **different `ObjectiveKind` vocabularies**, and only one vocabulary is understood by the
single production execution bridge.

**System A — Adventure/RouteFamily domain** (`src/domains/adventure/`), wired into the pipeline at
`src/engine/pipeline.py:237-247` (phase `"adventure_decision"`, runs early — Enhanced RPG Phase 3).
`RouteToProjectMapper._MAP` (`src/domains/adventure/mapper.py:31-47`) maps:
- `RouteFamily.CRAFT_UPGRADE → (ProjectKind.CRAFTING, ObjectiveKind.ACQUIRE_ITEM)` (mapper.py:34)
- `RouteFamily.GATHER_RESOURCE → (ProjectKind.HARVESTING, ObjectiveKind.REACH_RESOURCE)` (mapper.py:38)

Route candidates for these two families are only ever generated
(`src/domains/adventure/generator.py:38-45`, `kind_map`) from live `Opportunity` records of kind
`"craft_item"`/`"gather_resource"` supplied by `ResourceOpportunityProvider.get_opportunities`
(`src/world/providers/resources.py:25-99`) — confirmed this provider is real and does emit
`gather_resource` opportunities when `state.resource_nodes` has charge remaining and the entity's
region matches (resources.py:53-93); there is no equivalent opportunity provider observed for
`craft_item` in this scope (`AdventureRouteGenerator.generate` has no structural-default fallback
for `CRAFT_UPGRADE`, only for `RECOVER`/`ASK_INFORMATION`/`FORM_PARTY` — generator.py:93-163), so
craft candidates depend entirely on an external opportunity source not traced further here (open
question, see below).

**System B — GoalKind-based `fused_strategic_pass`** (`src/systems/strategic_systems/intelligence.py`),
wired into the pipeline at `src/engine/pipeline.py:330` (phase `"strategic_intelligence"`, runs
**later in the same tick** than `adventure_decision`). Goal scorers live in
`src/ai/goals/scorers.py`, registered in `src/ai/goals/__init__.py:9-17` against `GoalKind`
(`src/core/strategic.py:121-131`). **`GoalKind` has no CRAFTING or TRADE member at all** — only
`HARVESTING, FATIGUE, HUNGER, SOCIAL, TOWN_RETURN, COMBAT_ENGAGE, COMBAT_RETREAT, RECOVER,
RESOLVE_BLOCKER`. `HarvestScorer.score` (`src/ai/goals/scorers.py:6-34`) finds the nearest resource
node via `SpatialQueryService.nearest_resource_node` and returns `GoalScore(kind=GoalKind.HARVESTING,
utility=50.0/dist, target_id=str(node.id), target_pos=node.position)`. When this candidate wins
selection (`intelligence.py:1296-1301`, requires `utility >= 20.0`), the objective is built with a
**hardcoded** `kind="reach_location"` (`intelligence.py:1329`) regardless of `GoalKind` — this is
the critical divergence point from System A.

### The sole execution bridge only understands `ObjectiveKind.REACH_LOCATION`

`TacticalDecisionSystem.evaluate_entity_intent` (`src/engine/tactical.py:36-282`) is called for
**every** entity, every tick, via `CognitionDomain.execute_brain`
(`src/engine/domain/cognition.py:70`, itself called from the main per-entity brain loop). This is
the only place in production code that ever converts an active `entity.strategic.current_objective_id`
into a real `TaskUpdate`/`NavigationUpdate`/`InteractionUpdate`. Its "Pillar 5.1: Objective Pursuit"
branch (`tactical.py:205-282`) is gated by a single hardcoded literal:

```python
# src/engine/tactical.py:213
if obj and obj.kind == "reach_location" and obj.target:
```

Only when this is true does the branch resolve the target (as an `int` resource-node id or
building id, `tactical.py:216-237`) and, once within `dist <= 1.0` (line 241), emit a real
`ENTITY_ACT` task (`"INTERACT"` for nodes, `"EAT"`/`"REST"` for buildings by project kind,
`tactical.py:242-272`). **Every other `ObjectiveKind` value falls through all `if`/`elif` branches**
in the `if not hostiles:` block and the entity receives a bare idle `EntityUpdate(entity_id=entity.id)`
at `tactical.py:319` — no navigation, no task, no interaction. This includes:
- `ObjectiveKind.ACQUIRE_ITEM` (System A's `CRAFT_UPGRADE` objective) — never handled anywhere in
  `tactical.py`.
- `ObjectiveKind.REACH_RESOURCE` (System A's `GATHER_RESOURCE` objective) — never handled.
- `ObjectiveKind.BUY_ITEM`, `HARVEST_RESOURCE`, `REQUEST_CRAFT` — defined in the enum
  (`src/core/strategic.py:104-118`) but not referenced anywhere as a `ProjectState`/`ObjectiveState`
  producer in this codebase outside `ObjectiveIntentResolver` (see below) and its unit test.

### A second, more complete bridge exists but is never called in production

`ObjectiveIntentResolver.resolve()` (`src/domains/adventure/resolver.py:23-90`) correctly maps
**every** `ObjectiveKind` to an executable `ActionIntent`, including
`ACQUIRE_ITEM → "REQUEST_CRAFT"` (resolver.py:55-56), `REACH_RESOURCE → "MOVE_TO"` (resolver.py:67-69,
comment: "First reach, then harvest"), `HARVEST_RESOURCE → "HARVEST_RESOURCE"` (resolver.py:71-72),
`BUY_ITEM → "BUY_ITEM"` (resolver.py:52-53). These intents are consumable by
`ActionIntentAdapter.execute()` (`src/engine/intent/action_intent.py:48-202`), which has real
requirement gating (`recipe_known`, `has_gold`, `has_item` for `REQUEST_CRAFT` at lines 63-70;
`has_item`/`inventory_space` for `HARVEST_RESOURCE` at lines 71-77) and delegates to
`ActionRouter.execute_action`/`CraftingSystem`. **`ObjectiveIntentResolver` is never called anywhere
in the production pipeline** — grep across `src/` finds only its own definition, a comment
referencing it in `action_intent.py:139` ("Adventure/AGENCY-domain-originated intent
(ObjectiveIntentResolver)"), and one unit test
(`tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`). It is orphaned/dead
code — the intended bridge that was apparently never wired into `pipeline.py` or `tactical.py`.

### Crafting and trade have zero viable path, full stop

Because `GoalKind` has no CRAFTING or TRADE member (System B never generates a crafting/trade
project of any kind), and System A's `CRAFT_UPGRADE`/`SELL_LOOT_FOR_GOLD` objectives are silently
dropped by `tactical.py` (per above), **there is currently no code path by which any entity can
ever produce `item_crafted`, `trade_executed`, or `shop_transaction`**, regardless of world content
or merchant population. `CraftingSystem.craft()` (`src/systems/economy_systems/crafting.py:14-65`)
is a correctly-implemented, callable static method — confirmed per the ticket's Out of Scope framing
— but nothing in the strategic/tactical layer ever calls it.

### Harvesting has a working wire, but the picture is incomplete

System B's `HARVESTING` goal *is* structurally wired end-to-end: `HarvestScorer` → hardcoded
`reach_location` objective (matches `tactical.py:213`) → `tactical.py:242-251` fires `ENTITY_ACT`
`"INTERACT"` on arrival → `ActionRoutingPhase.route` (`src/engine/pipeline_phases/actions.py:34-223`)
→ `SimulationDomainLogic.execute_action`. `resource_harvested` is derived post-hoc by
`src/observability/event_extractor.py:326-333` from an **accepted intent result with
`source_kind == "NODE"`** on the entity — this completion path was not traced to its exact emission
site in this investigation (open question below), but the parity ledger (`TOWN-010`, `TOWN-104`,
`TOWN-114`, `TOWN-129` in `town_resource.yaml`) confirms the underlying harvest-completion mechanics
are independently verified and tested. Yet the ticket's corpus-wide grep found **zero**
`resource_harvested` events, ever, in any world. Two structural factors that could suppress this,
found but **not conclusively traced to root cause** in this pass:

1. **Merge ordering / competing writers.** `StrategicUpdate.merge` (`src/core/updates.py:530-566`)
   is last-write-wins for `current_project_id_set`/`current_objective_id_set` (`updates.py:549-550`:
   `other.current_project_id_set if other.current_project_id_set is not None else self.current_project_id_set`).
   Since `"strategic_intelligence"` (System B) runs after `"adventure_decision"` (System A) in the
   same tick (`pipeline.py:237` vs. `pipeline.py:330`), System B's selection should generally win the
   final committed value for a given tick — but System B only overwrites when it actually produces a
   `current_project_id_set` (i.e., `evaluate_project_switch` decides to switch). Whether HARVESTING
   reliably wins that switch decision against competing `GoalKind`s (HUNGER, FATIGUE, TOWN_RETURN,
   COMBAT_RETREAT, RECOVER, RESOLVE_BLOCKER, SOCIAL, COMBAT_ENGAGE) at typical entity states, and
   whether `SpatialQueryService.nearest_resource_node` reliably finds a node at all given each
   world's actual `resource_nodes` population, were **not traced to a definitive yes/no** in this
   pass.
2. **Utility gating.** `intelligence.py:1298`: `if g_score.utility < 20.0 ... continue`. HarvestScorer's
   utility is `50.0 / dist` — easily clears 20.0 at short range but degrades below threshold past
   dist=2.5, and is `0.0` outright when the entity is at inventory capacity (scorers.py:9-10) or no
   node is found (scorers.py:32-34, `SpatialQueryService.nearest_resource_node` returns falsy).

These are flagged as **open questions requiring further tracing during Plan/Implement**, not
resolved root causes — the ticket's AC only requires identifying *a* root cause with evidence and
producing one real event; the tactical.py `"reach_location"`-only gate (confirmed, reproducible,
file:line-cited) is sufficient to explain the CRAFTING/TRADE half of the gap outright and is a
strong contributing (if not sole) cause for the HARVESTING half.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §1 "Goal Hierarchy & Prioritization" explicitly lists
  **"Tier 4: Economic — `harvest`, `trade`, `craft` — Accumulating wealth and equipment"** as a
  first-class concern tier equal in documented standing to Survival/Biological/Social tiers.
- §4 "The Project Lifecycle" gives the canonical authoritative example this ticket's gap directly
  violates: *"2. Project: A specific actionable goal (e.g., 'Craft Iron Breastplate'). 3. Objective:
  A granular, atomic step (e.g., 'Travel to Forge', 'Interact with Anvil'). 4. Action: The raw engine
  command sent to the simulation."* Step 4 (Action) never happens for CRAFTING/HARVESTING(-via-
  System-A)/TRADE objectives — this is a direct violation of the documented Project→Objective→Action
  law, not merely a content gap.
- `docs/mechanics/03_economic_laws.md` §5 "Industry: Crafting & Conversion" (lines 112-122) governs
  the gather→craft→sell chain the fix must ultimately resolve through once wired — recipe
  materials, gold cost, atomic conservation. `CraftingSystem.craft()` already implements this
  correctly (recipe/knowledge/role/material/gold/capacity gates, `crafting.py:23-65`); this ticket's
  scope is the goal-generation/execution-routing layer above it, not the economic law itself.
- `docs/mechanics/03_economic_laws.md` §3 "Resource Harvesting" is the analogous authority for the
  harvesting half.

## Parity Ledger Overlap

| ID | File | Status | Priority | Relevance |
|---|---|---|---|---|
| `STRAT-189` | `strategic_cognition.yaml` | verified | P0 | Text: "Objective derivation can create executable objectives." `test_path: null`. This is the entry most directly contradicted by this investigation's finding for `ACQUIRE_ITEM`/`REACH_RESOURCE` objectives — they are derived but **not** executable (tactical.py never converts them to an action). Needs re-examination once the fix lands: either the entry's scope needs a `divergence_note` narrowing it to the objectives that *are* executable today, or its status needs revisiting. **P0 with `test_path: null` — currently has no passing test backing it, which is itself a gap per the Authoritative Mechanics Rule.** |
| `STRAT-078` | `strategic_cognition.yaml` | verified | P0 | Text: "`test_objective_resumption_aligns_with_tactical`: ... Verify that a resumed objective correctly drives goal selection." `test_path: null`. Directly adjacent to the strategic/tactical alignment gap found here — worth re-verifying once the fix lands. |
| `STRAT-188` | `strategic_cognition.yaml` | verified | P0 | Text: "Current objective has continuity priority." `test_path: null`. Not contradicted (continuity itself works — the objective persists correctly), but adjacent enough to check post-fix. |
| `TOWN-010`, `TOWN-104`, `TOWN-114`, `TOWN-129` | `town_resource.yaml` | verified | P0/P1 | Confirm the harvest-completion mechanics (channeled interaction, node depletion, yield-from-node-definition) are independently correct at the unit level — these are **not** the cause of the gap and should not be touched; they corroborate that the fix belongs at the strategic/tactical layer, not the economic layer. |
| `TOWN-017`, `TOWN-028`, `TOWN-172` | `town_resource.yaml` | verified | P0/P1 | Confirm blacksmith/crafting-resolution and the recipe catalog (≥25 entries, full gather→craft chain) are independently correct — same conclusion: not the cause, corroborating evidence the gap is upstream. |

**No existing parity ledger entry currently documents the tactical-execution gap itself
(`ObjectiveKind` values other than `REACH_LOCATION` being silently dropped, or `ObjectiveIntentResolver`
being orphaned).** A new entry should be added to `strategic_cognition.yaml` once the fix lands,
and `STRAT-189` should be updated with `v2_evidence`/`divergence_note` reflecting the corrected
behavior.

## Prior Work

- `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH/` — the ticket that discovered this
  gap. Its investigation independently confirmed `EconomyScorer` is purely event-driven and correct
  (Pattern 6 does not apply), and that `urban_political`'s 69-event "A" run is 100%
  `gold_sink_fired`, not real harvest/craft/trade — corroborated again here via direct inspection.
  That ticket's content-authoring work (3 worlds composed with `trading_company_hub`) remains valid
  and ready to exercise once this gap closes; nothing in this investigation invalidates it.
- `tickets/done/TCK-20260713-SIMQ-SCORE-CEILING-FIX.md` — its ECONOMY weight-derivation cited the
  same 69-event `urban_political` run as "genuinely rich activity." The weight *mechanism* is
  unaffected by this investigation's finding (weights were derived from real observed event
  *counts*, whatever their true composition); only the narrative characterization of what that data
  represented was inaccurate, as already flagged by ECONOMY-CONTENT-DEPTH.
- No prior ticket in `tickets/done/` or `stored_artifacts/` was found (via targeted grep for
  `ObjectiveIntentResolver`, `TacticalDecisionSystem`, `RouteToProjectMapper`, `GoalRegistry`, and
  `fused_strategic_pass`) that previously identified or attempted to close the two-parallel-systems
  divergence documented here. This appears to be a previously undiscovered structural gap, not a
  regression of prior work.

## Risks and Open Questions

1. **Blocking for Plan — which system should own CRAFTING/HARVESTING/TRADE going forward is not
   decided here.** Three shapes are possible: (a) extend `tactical.py`'s Pillar 5.1 branch to also
   handle `ACQUIRE_ITEM`/`REACH_RESOURCE`/`BUY_ITEM` inline (matches System B's existing pattern,
   smallest diff, but perpetuates two parallel objective vocabularies); (b) wire the already-built
   `ObjectiveIntentResolver`/`ActionIntentAdapter` bridge into `tactical.py` or `CognitionDomain`
   for objectives System B doesn't natively produce (reuses more-complete existing code, but two
   systems producing objectives with different kinds for overlapping concerns — e.g. both systems
   can produce a "harvesting" project — remains an architectural smell); (c) unify System A and
   System B into one goal-generation path (largest change, out of a `standard`-tier ticket's
   likely budget). **This must be decided in Plan, not assumed here.**
2. **Not resolved: why does `resource_harvested` never fire even via System B's working wire?**
   The investigation identified two plausible contributing factors (merge-ordering/competing-writer
   interaction between System A and System B, and utility-threshold competition against other
   `GoalKind`s) but did not trace either to a definitive yes/no with a live run. **Implement must
   verify this empirically** (e.g., instrument or trace one `urban_political`/`trading_company_hub`
   run) rather than assume the `tactical.py:213` fix alone is sufficient to produce a real
   `resource_harvested` event — it is necessary but its sufficiency is unconfirmed.
3. **`ResourceOpportunityProvider` supplies `"gather_resource"` opportunities but no equivalent
   `"craft_item"` opportunity source was located in this pass** (`AdventureRouteGenerator.generate`
   has a `kind_map` entry for `"craft_item"` at generator.py:41, but no provider emitting that kind
   was traced). If confirmed absent, CRAFT_UPGRADE route candidates may never even be *generated*
   as `AdventureRouteOption`s (a System-A-side gap layered on top of the tactical.py execution gap) —
   this needs a follow-up trace in Plan/Implement before deciding the fix shape for crafting
   specifically.
4. Whether this affects only ECONOMY-family goals or is a broader symptom of a wider
   goal-generation/execution-routing issue (the ticket's own open question) is **partially
   answered**: `ObjectiveKind.ASK_INFORMATION`, `BUY_ITEM`, `ACCEPT_QUEST`, `DEFEAT_ENEMY`,
   `RETURN_TOWN` also fall through `tactical.py`'s `"reach_location"`-only gate when produced by
   System A — but combat (`DEFEAT_ENEMY`/hostile engagement) is handled by an entirely separate,
   independently-working branch of `tactical.py` (lines 321-666, target selection/attack), and
   `ASK_INFORMATION`/`ACCEPT_QUEST` may have their own separate resolution paths not traced in this
   ECONOMY-scoped investigation. **Do not assume the fix generalizes to those without separately
   verifying each.**

## Anti-Drift Hazards

- **Do not touch `src/simulation_quality/scorers/economy.py`** — explicit ticket Out of Scope,
  reconfirmed correct here (listens for the right 11 event types, no durable-state read).
- **Do not touch `src/economy/health_monitor.py`'s `INFLATION_SPIRAL_GINI_THRESHOLD`** — explicit
  ticket Out of Scope, unrelated mechanism.
- **Do not author new world content** (merchant population, `trading_company_hub` parameters) —
  explicit ticket Out of Scope; `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` already did this and it
  is not the cause.
- **Do not "fix" this by lowering `HarvestScorer`'s utility threshold competitors' priorities, or by
  hand-tuning `GoalKind` scorer weights** to make HARVESTING win more often — that would mask the
  structural execution-routing gap rather than close it, and would not create a path for
  CRAFTING/TRADE at all (no `GoalKind` exists for either).
- **Do not silently delete or bypass `ObjectiveIntentResolver`** on the theory that it's unused dead
  code — it is the more architecturally complete of the two bridges (handles all `ObjectiveKind`s
  with proper requirement gating) and is a strong candidate for the actual fix path; removing it
  would foreclose the lowest-risk implementation option before Plan has decided.
- **Do not conflate System A and System B silently** by, e.g., changing `RouteToProjectMapper` to
  emit `ObjectiveKind.REACH_LOCATION` instead of `ACQUIRE_ITEM`/`REACH_RESOURCE` as a quick patch.
  This would make `tactical.py:213` fire, but would collapse semantically distinct objective
  intents (craft vs. reach-a-location) into a shared kind, likely breaking the node/building
  disambiguation logic at `tactical.py:216-237` (which assumes the target is always a location,
  node, or building id — not an item/recipe id) and any other consumer that relies on
  `ObjectiveKind` being semantically accurate (e.g. `STRAT-189`-adjacent tests, observability/
  cognition event mapping in `src/observability/cognition/event_mapper.py`).
- **Full regression sweep must include `tests/unit/domains/adventure/`,
  `tests/integration/domains/adventure/`, and `tests/unit/strategic/`** — both System A and System
  B have substantial existing test coverage that a routing-layer change could silently break; do not
  scope the regression run to strategy/economy tests only.
- **Do not assume the fix only needs to touch `tactical.py`.** Per Open Question 2, the merge-order
  interaction between System A and System B, and per Open Question 3, the possible missing
  `craft_item` opportunity provider, may both need addressing for the AC's "at least one real
  calibration run produces a real event" bar to be met — a `tactical.py`-only patch may pass CRAFTING
  registration but still fail to produce a live event in a real run.
