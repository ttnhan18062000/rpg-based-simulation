---
status: authoritative
layer: mechanics
authority: P1
audience: agent
last_verified: 2026-08-11
tags: [adventure-routing, strategic-cognition, scoring, route-family, opportunity]
related_chapter: 04_strategic_cognition.md
---

# Adventure Routing Contract

Companion sub-contract to `04_strategic_cognition.md`. That chapter describes the goal hierarchy and strategic direction; this doc gives the exact route family taxonomy, scoring formula, blocker handling, candidate cap, and fallback guarantee needed to safely implement or modify routing logic.

---

## Purpose

Define the complete decision law for how entities select adventure routes each tick: what options are generated, how they are scored, how blockers affect scoring (not exclusion), and what guarantees exist on the output.

---

## RPG Meaning

An entity in the world has needs and opportunities. The routing system translates those into a ranked list of candidate routes — each representing a meaningful activity family (harvest, combat, trade, etc.). The entity commits to the highest-scoring viable route. The simulation is deterministic: given the same entity state and opportunities, the same route is selected.

---

## Inputs

| Field | Type | Description |
|---|---|---|
| `entity` | `Entity` | Full entity snapshot including inventory, identity, self_model, attributes |
| `opportunities` | `Sequence[Opportunity]` | Provided by `src/world/providers/resources.py` from `StrategicWorldIntegrationSystem` |
| `active_needs` | `Dict[str, float]` | From `entity.self_model.needs.active_needs` |

Each `Opportunity` has:
- `kind` — maps to `RouteFamily` via `kind_map`
- `confidence` — float 0–1, copied to `AdventureRouteOption.confidence`
- `estimated_reward` — divided by 100 to produce `expected_benefit`
- `estimated_risk` — copied to `expected_risk`
- `requirements` — list of requirement objects (kind, quantity, subject)
- `id`, `subject` — for tracing

---

## Core Rules

1. **Opportunity → RouteFamily mapping:** each opportunity `kind` is mapped via `kind_map` in `generator.py`:
   - `gather_resource` → `GATHER_RESOURCE`
   - `buy_item` → `BUY_UPGRADE`
   - `craft_item` → `CRAFT_UPGRADE`
   - `repair_gear` → `RECOVER`
   - `ask_information` → `ASK_INFORMATION`
   - `rest_inn` → `RECOVER`

2. **Blocker detection:** for each opportunity, requirements are inspected:
   - `req.kind == "has_gold"`: if `entity.inventory.gold < req.quantity` → blocker string `f"insufficient_gold:{shortfall}"`
   - `req.kind == "has_item"`: if item quantity in inventory < `req.quantity` → blocker string `f"missing_item:{req.subject}:{shortfall}"`
   - Blocked routes still appear in the candidate set and receive a `blocker_penalty = 2.0` in scoring

3. **Structural defaults (added after opportunity loop):**
   - `low_health` or `healing` need present → forced `RECOVER` route at confidence 0.9
   - `weak_weapon` or `equipment_improvement` need present, and no BUY_UPGRADE / CRAFT_UPGRADE already in opts → forced `ASK_INFORMATION` at confidence 0.8

4. **Candidate cap:** `opts[:25]` — hard maximum of 25 candidates before scoring to prevent evaluation blowup

5. **Fallback guarantee:** if `opts` is empty after all processing, one `DEFER_WITH_REASON` route is appended:
   - `score=0.01`, `confidence=1.0`, `expected_benefit=0.0`
   - This guarantees a non-empty candidate set and a valid decision outcome

6. **Selection:** after scoring, the caller (service layer) selects the highest-scoring candidate

---

## Route Family Taxonomy

All 13 families defined in `RouteFamily` (str enum in `src/domains/adventure/schema.py`):

| Family | Value | Meaning |
|---|---|---|
| `RECOVER` | `"recover"` | Rest, healing, equipment repair |
| `BUY_UPGRADE` | `"buy_upgrade"` | Purchase from shop |
| `CRAFT_UPGRADE` | `"craft_upgrade"` | Blacksmith crafting |
| `TRAIN_SKILL` | `"train_skill"` | Class hall training |
| `TAKE_EASY_QUEST` | `"take_easy_quest"` | Low-risk quest |
| `HUNT_WEAK_ENEMY` | `"hunt_weak_enemy"` | Combat for resources |
| `GATHER_RESOURCE` | `"gather_resource"` | Harvest resource node |
| `SELL_LOOT_FOR_GOLD` | `"sell_loot_for_gold"` | Sell to shop |
| `ASK_INFORMATION` | `"ask_information"` | Information gathering |
| `SCOUT_LOCATION` | `"scout_location"` | Exploration |
| `FORM_PARTY` | `"form_party"` | Social grouping |
| `RETURN_TOWN` | `"return_town"` | Travel back to settlement |
| `DEFER_WITH_REASON` | `"defer_with_reason"` | Fallback when no options |

---

## Formula / Decision Logic

### Scoring Formula

`AdventureRouteScorer.score()` computes:

```
score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
final_score = round(max(0.0, score), 4)
```

**Component breakdown:**

| Component | Formula |
|---|---|
| `urgency` | max urgency value of active needs matching the route's family (via `family_needs` lookup table) |
| `benefit` | `route.expected_benefit` directly |
| `personality_bias` | see personality bias table below (max +0.25) |
| `confidence_bonus` | `route.confidence * 0.15` (flat); for `GATHER_RESOURCE`/`CRAFT_UPGRADE` routes with a resolvable capability key, an ad-hoc `CapabilityEstimateService.estimate()` call replaces the source instead — see `docs/mechanics/04_strategic_cognition.md` §6.12 (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) |
| `risk_penalty` | `route.expected_risk * risk_multiplier * 0.5` |
| `blocker_penalty` | `2.0` if any blocker present, else `0.0` |

**Risk multiplier:**
```
risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)
```

### Personality Bias Table

Computed in an if/elif chain — only the first matching branch applies per route:

| Branch | Route Families | Bias |
|---|---|---|
| RECOVER | `RECOVER` | `caution * 0.25` |
| greed | `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD`, `TAKE_EASY_QUEST` | `greed * 0.25` |
| curiosity | `ASK_INFORMATION`, `SCOUT_LOCATION` | `curiosity * 0.25` |
| industry | `CRAFT_UPGRADE`, `GATHER_RESOURCE` | `industry * 0.25` |
| sociability | `FORM_PARTY` | `sociability * 0.25` |

**Known quirk — GATHER_RESOURCE:** This family appears in both the greed branch and the industry branch of the if/elif chain in `scoring.py`. Because `elif` is used, the greed branch fires first for `GATHER_RESOURCE` and the industry branch is never reached for it. This is a code-level artifact — `GATHER_RESOURCE` always receives `greed * 0.25` bias, never `industry * 0.25`. Documented here for correctness; not corrected in this documentation ticket.

### Trait Normalisation

`get_trait()` normalises raw trait values:
- If value > 1.0: divide by 100 (handles percentage-scale storage)
- `caution` is derived: `max(0.0, min(1.0, 1.0 - bravery))`
- `curiosity` is derived from `entity.identity.properties["curiosity"]` or `attributes.intelligence / 10.0` if stored value > 1.0

---

## Lifecycle

Adventure routing runs inside the kernel's **Scheduling** stage, as one tier-5 goal candidate
among others. Specifically: `StrategicWorldIntegrationSystem` emits opportunities →
`AdventureRouteGenerator.generate()` builds candidates → `AdventureRouteScorer.score()` scores
each → service layer selects top candidate → `ObjectiveIntentResolver.resolve()` maps to
`ActionIntent`.

**Sole live entry point (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE):** `AdventureGoalScorer.score(entity, state)`
(`src/ai/goals/adventure_scorer.py`), registered unconditionally under `GoalKind.ADVENTURE_ROUTE`
in `GoalRegistry`, invoked via `GoalRegistry.get_all_scores()` inside
`StrategicIntelligenceSystem.evaluate_strategic_intent()` — which itself runs every tick through
the always-on `strategic_intelligence` pipeline phase (`src/engine/pipeline.py`), subject only to
per-entity `SystemCadence` throttling (see `04_strategic_cognition.md` §2). The formerly-separate
`AdventureDecisionPhase` pipeline stage (`src/domains/adventure/phase.py`), which used to run its
own duplicate route-generation/scoring pass every tick ahead of the tier-5 competition, has been
deleted — `AdventureGoalScorer` was already winning tier-5 arbitration for every non-cadence-skipped
entity before the deletion (later-merged, last-writer-wins semantics), so this cutover removed
now-wasted duplicate compute rather than switching on a new live path for the first time. Do not
read this contract as describing two active routing paths — only one exists today.

---

## Mutation Rules

**What routing reads (read-only):**
- `entity.inventory.gold`, `entity.inventory.items`
- `entity.self_model.needs.active_needs`
- `entity.identity.properties` (traits, curiosity)
- `entity.combat.attributes` (for curiosity derivation)
- Opportunity sequence from world providers

**What routing does not mutate:** world state is not changed by routing evaluation. Only the resulting `ActionIntent` is forwarded to the execution pipeline which mutates state.

---

## Objective Intent Resolver

`ObjectiveIntentResolver.resolve()` maps `ObjectiveKind` → `ActionIntent.kind`:

| ObjectiveKind | ActionIntent kind |
|---|---|
| `REACH_SERVICE` | `MOVE_TO` |
| `BUY_ITEM` | `BUY_ITEM` |
| `ACQUIRE_ITEM` | `REQUEST_CRAFT` |
| `REACH_LOCATION` | `MOVE_TO` |
| `ACCEPT_QUEST` | `ACCEPT_QUEST` |
| `DEFEAT_ENEMY` | `ATTACK_TARGET` |
| `REACH_RESOURCE` | `MOVE_TO` |
| `HARVEST_RESOURCE` | `HARVEST_RESOURCE` |
| `ASK_INFORMATION` | `ASK_INFORMATION` |
| `RETURN_TOWN` | `RETURN_TOWN` |
| default | `MOVE_TO` |

Default kind before any match: `"DEFER"`.

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| All opportunities blocked (no gold, no items) | All candidates remain with blocker_penalty=2.0; highest scoring blocked route wins unless DEFER_WITH_REASON scores higher |
| No opportunities provided | Structural defaults may still add RECOVER/ASK_INFORMATION; if all empty, DEFER_WITH_REASON fallback fires |
| More than 25 opportunities generated | `opts[:25]` hard cap — opportunities beyond position 25 are discarded before scoring |
| Entity with no active needs | `urgency=0.0` for all routes; `benefit` and `personality_bias` alone drive scoring |
| `GATHER_RESOURCE` with both greed and industry traits | greed branch applies (elif chain; industry branch never reached for this family) |

---

## Examples

### Entity with 80% health harvesting iron

```
Opportunity: kind=gather_resource, confidence=0.85, estimated_reward=200, estimated_risk=0.1
Route generated: GATHER_RESOURCE, expected_benefit=2.0 (200/100), expected_risk=0.1

Scoring:
  urgency = 0.3 (harvest_need active)
  benefit = 2.0
  personality_bias = greed * 0.25 = 0.7 * 0.25 = 0.175  (greed branch fires, industry skipped)
  confidence_bonus = 0.85 * 0.15 = 0.1275  (flat term: no tool requirement on this route, so the
    TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING capability-estimate source, §6.12, does
    not apply here -- see the confidence_bonus row above for when it does)
  risk_penalty = 0.1 * risk_multiplier * 0.5 = 0.1 * 0.82 * 0.5 = 0.041
  blocker_penalty = 0.0
  score = 0.3 + 2.0 + 0.175 + 0.1275 - 0.041 - 0.0 = 2.5615
```

### Blocked buy_upgrade (insufficient gold)

```
Opportunity: kind=buy_item, requirements=[{kind:"has_gold", quantity:100}]
Entity gold: 30 → shortfall=70 → blocker="insufficient_gold:70"

Scoring blocker_penalty = 2.0
score = urgency + benefit + bias + confidence_bonus - risk_penalty - 2.0
(very unlikely to win unless all other options score < 0.0)
```

---

## Source Areas

| Module | Role |
|---|---|
| `src/domains/adventure/generator.py` | `AdventureRouteGenerator.generate()` — opportunity → route option |
| `src/domains/adventure/scoring.py` | `AdventureRouteScorer.score()` — scoring formula and trait normalisation |
| `src/domains/adventure/resolver.py` | `ObjectiveIntentResolver.resolve()` — ObjectiveKind → ActionIntent |
| `src/domains/adventure/schema.py` | `RouteFamily`, `AdventureRouteOption`, `AdventureDecisionResult` |
| `src/world/providers/resources.py` | Opportunity emission from StrategicWorldIntegrationSystem |

---

## Regression Tests

| Test / Group | Verified Law |
|---|---|
| `tests_v2/test_adventure_routing.py` | Route generation, scoring formula, fallback guarantee |
| `tests_v2/test_route_scoring.py` | Personality bias, risk multiplier, blocker penalty |
| `tests_v2/test_objective_resolver.py` | ObjectiveKind → ActionIntent mapping |
| COMB-093 `test_ai_boredom_diversification` | Boredom modifier interacts with routing scores |
| COMB-096–COMB-098 motive modifier tests | Motive modifiers bias route family selection |

---

## Extension Rules

To add a new RouteFamily (source-level change, modifies src/):
1. Add the enum value to `RouteFamily` in `src/domains/adventure/schema.py`
2. Add a `kind_map` entry in `AdventureRouteGenerator.generate()` if driven by opportunities
3. Add a `family_needs` entry in `AdventureRouteScorer` if need urgency should apply
4. Add a personality bias branch in the if/elif chain in `score()` (append to avoid disrupting existing elif order)
5. Add objective resolution mapping in `ObjectiveIntentResolver.resolve()` if needed
6. Update this doc and `04_strategic_cognition.md` if the new family represents a meaningful strategic direction
7. Add regression tests covering: family appears in candidate set, scores correctly with and without blockers, fallback still fires if only family is blocked

### Feature Pack Extension Path (E63 — no src/ modification required)

When adding a RouteFamily via a **feature pack**, do NOT follow steps 1–7 above.
Instead, use the `FeatureRegistry` pattern defined in
`docs/architecture/feature_pack_architecture.md`:

1. Declare the new family in a `FeaturePackManifest` YAML (`content/packs/{name}/manifest.yaml`)
2. Implement generator + scorer classes in a Python module outside `src/`
3. Register via `extension_points[].domain = adventure_routing` in the manifest
4. `FeaturePackLoader` bootstraps the registry from existing `RouteFamily` enum values,
   then registers pack-contributed entries at scenario init — no source edit needed

The source-level enum extension path remains valid for first-party core additions.
The feature pack path is for opt-in / add-on / community extensions.
