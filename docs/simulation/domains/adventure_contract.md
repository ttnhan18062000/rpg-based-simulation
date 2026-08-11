---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-08-11
---

# Adventure Domain Contract

**Source:** `src/domains/adventure/` (generator.py, scoring.py, service.py, resolver.py, mapper.py, schema.py) + `src/ai/goals/adventure_scorer.py` (`AdventureGoalScorer`, the tier-5 entry point)  
**Pipeline phase:** tier-5 goal candidate — `AdventureGoalScorer.score(entity, state)`, invoked via `GoalRegistry.get_all_scores()` inside `StrategicIntelligenceSystem.evaluate_strategic_intent()` (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE deleted the former dedicated `AdventureDecisionPhase` pipeline stage; see Engine Phase below)  
**Authoritative status:** Strategic routing domain — selects hero projects and objectives each tick. Does not execute combat or harvest actions directly.

---

## Purpose

The adventure domain implements **subjective route selection** for entities whose resolved `CognitionProfileDefinition.supports_adventure_routing` is `True` (see the Engine Phase eligibility table below) — "hero" is retained throughout this document, and in the code's own parameter naming (e.g. `_threat_resolved(hero, state)`), as the established shorthand for the routed entity, not a role gate. Each eligible tick, it generates candidate routes the hero could pursue, scores them through a personality-biased formula, selects the highest-scoring non-deferred route, and emits a `StateUpdate` carrying a `StrategicUpdate` that sets the hero's active project and objective. Downstream tactical systems read the project to determine immediate actions.

---

## Engine Phase

**Tier-5 goal candidate — `AdventureGoalScorer.score(entity, state)`**
(`src/ai/goals/adventure_scorer.py`; TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE)

`AdventureGoalScorer` is registered unconditionally in `GoalRegistry`
(`src/ai/goals/__init__.py`) and invoked via `GoalRegistry.get_all_scores()` inside
`StrategicIntelligenceSystem.evaluate_strategic_intent()`, which runs every tick through the
always-on `strategic_intelligence` pipeline phase (`src/engine/pipeline.py`), subject only to
per-entity `SystemCadence` throttling — the same cadence and 20.0 tier-5 utility floor every
other `GoalKind` scorer respects. Eligible entities:

| Criterion | Check |
|---|---|
| Cognition eligibility | Resolved `CognitionProfileDefinition.supports_adventure_routing = True`, resolved via (a) explicit `identity.properties["cognition_profile_id"]`, else (b) `identity.properties["role_id"]` → `RoleDefinition.default_cognition_profile`, else (c) legacy `EntityRole.HERO` → the `"hero"` role's own default |
| Alive | `entity.combat.alive = True` |
| Active | `entity.lifecycle.active = True` |
| Project lock | `tick >= active_project.lock_until_tick`, or the triggering threat has resolved (`_threat_resolved()`), or no active project — enforced inside `StrategicIntelligenceSystem.evaluate_project_switch()`'s shared locked-branch gate, not by a route-generation pre-filter |

These checks are unchanged from the prior, now-deleted phase-based mechanism
(TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE) — only their call site changed: eligibility
(cognition profile / alive / active) still gates whether `AdventureGoalScorer.score()` attempts
route generation at all, and the project-lock check now lives in the shared
`evaluate_project_switch()` arbiter every `GoalKind` candidate's commit already routes through,
rather than a route-generation pre-filter specific to adventure routing.

---

## What It Owns

- The hero's **active route selection**: which `RouteFamily` the hero pursues this tick
- The hero's **strategic project assignment**: `current_project_id` and `current_objective_id` written via `StrategicUpdate`
- **Debug trace properties** on the entity: `last_routing_tick`, `last_routing_family`, candidate count

The adventure domain does not own world state, inventory, combat state, or any other entity's strategic state.

---

## What It Reads

From the entity under evaluation:

| Field | Purpose |
|---|---|
| `entity.identity.personality` | Personality traits: `bravery`, `greed`, `industry`, `sociability` |
| `entity.identity.properties["curiosity"]` | Curiosity trait (derived from properties or intelligence) |
| `entity.identity.properties["caution"]` | Caution (derived: `1.0 - bravery`) |
| `entity.identity.properties["dominant_need"]` | Urgency source for needs-driven routing |
| `entity.strategic` | Current project state and `lock_until_tick` |
| `entity.inventory` | Items held (informs SELL_LOOT_FOR_GOLD and BUY_UPGRADE routes) |
| `entity.cognition` / self-model | Known weaknesses and self-assessed gaps |

From world state:

| Field | Purpose |
|---|---|
| `state.world_signals` / `exposed_world_signals` | Opportunities visible to the hero |
| Active opportunities | Candidate source for route generation |
| Known resource nodes | Candidate source for GATHER_RESOURCE routes |
| Region exploration targets | Candidate source for SCOUT_LOCATION routes |

---

## Route Generation — AdventureRouteGenerator

`AdventureRouteGenerator.generate(hero, state)` builds candidate `AdventureRouteOption` objects.

**Hard cap:** 25 candidate routes maximum per tick per hero.

**Candidate sources:**

| Source | Route families sourced |
|---|---|
| Active opportunities | TAKE_EASY_QUEST, HUNT_WEAK_ENEMY, FORM_PARTY, ASK_INFORMATION |
| Known resource nodes | GATHER_RESOURCE, SELL_LOOT_FOR_GOLD |
| Region exploration targets | SCOUT_LOCATION |
| Standing availability | RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, TRAIN_SKILL, RETURN_TOWN |

**Full `RouteFamily` enum (13 values):**

| Value | Meaning |
|---|---|
| `RECOVER` | Rest or heal at a safe location |
| `BUY_UPGRADE` | Purchase equipment at a vendor |
| `CRAFT_UPGRADE` | Craft a gear improvement |
| `TRAIN_SKILL` | Spend XP or AP on a skill |
| `TAKE_EASY_QUEST` | Accept a low-risk quest |
| `HUNT_WEAK_ENEMY` | Seek a beatable enemy for XP/loot |
| `GATHER_RESOURCE` | Collect a resource node |
| `SELL_LOOT_FOR_GOLD` | Convert inventory loot to gold |
| `ASK_INFORMATION` | Seek intel from an NPC or faction |
| `SCOUT_LOCATION` | Explore an unknown region |
| `FORM_PARTY` | Recruit or join a cooperative group |
| `RETURN_TOWN` | Return to a town hub |
| `DEFER_WITH_REASON` | No viable route — strategic deferral |

Each candidate carries: `family`, `score`, `confidence`, `expected_benefit`, `expected_risk`, `requirements`, `blockers`, `source_opportunity_ids`, `reason`.

---

## Scoring — AdventureRouteScorer / AdventureDecisionService

**Formula:**

```
score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
```

| Term | Source |
|---|---|
| `urgency` | Maximum urgency across entity's active needs matching the route family |
| `benefit` | `route.expected_benefit` (0.0–1.0) |
| `personality_bias` | Per-family trait contribution (see table below) |
| `confidence_bonus` | Derived from `route.confidence` |
| `risk_penalty` | `expected_risk × risk_multiplier × 0.5`; risk_multiplier = `max(0.1, (1.0 + caution×0.8) - bravery×0.6)` |
| `blocker_penalty` | `2.0` flat if `route.blockers` is non-empty |

**Personality bias by route family:**

| Route family | Trait applied | Contribution |
|---|---|---|
| RECOVER / RETURN_TOWN | `caution` | `caution × 0.25` |
| GATHER_RESOURCE / SELL_LOOT_FOR_GOLD | `greed` | `greed × 0.25` |
| SCOUT_LOCATION / ASK_INFORMATION | `curiosity` | `curiosity × 0.25` |
| CRAFT_UPGRADE / TRAIN_SKILL | `industry` | `industry × 0.25` |
| FORM_PARTY | `sociability` | `sociability × 0.25` |

Note: `caution` is a derived trait (`1.0 - bravery`); `curiosity` is read from `entity.identity.properties`.

**Known quirk:** In `scoring.py`, blocked routes receive a flat `-2.0` blocker penalty rather than being excluded. A heavily-favoured route with active blockers will still appear in the candidate list with a depressed score. The highest-scoring *non-blocked* route is selected; `DEFER_WITH_REASON` is returned only if all candidates are blocked or the scored list is empty.

**Greed/industry elif ordering issue:** In one scoring branch the `greed` condition is listed before the `industry` condition using an `elif` chain. For certain family values that match both intents, the `industry` branch may be unreachable. This is a documented known behaviour — not yet corrected.

#### Calibration Note (E11D, 2026-06-19 — corrected TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION)

The bravery coefficient (`0.6`) and caution coefficient (`0.8`) shown above still describe
`AdventureRouteScorer`'s own risk-multiplier term correctly, but the combat_engage-rate ratio
this note originally cited as evidence of their effect was mis-attributed: `RouteFamily.
HUNT_WEAK_ENEMY` (System A's only combat-tagged route) is confirmed dead code in
`src/domains/adventure/generator.py` (zero call sites), so `AdventureRouteScorer` can never
route a hero into combat at all today. The original 4.92× baseline almost certainly measured
`ProjectKind.COMBAT` via that now-dead route, not `GoalKind.COMBAT_ENGAGE`.

The real, live combat-engagement mechanism is System B (`GoalRegistry` / `CombatEngageScorer`,
`src/ai/goals/scorers.py`): `utility = 40 + bravery×40 + stamina_ratio×20` when a hostile is
visible. Re-measured baseline (`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`):
SEEDS=1..24, TICKS=400, 16 heroes/8 monsters → **~1.74× mean combat_engage rate ratio**
between bottom and top bravery quartiles, averaged per-seed (recalibrated acceptance
criterion: ≥1.5×, down from the stale ≥2× reading of the original 4.92× number).

- At bravery=0.0 (caution=1.0): `risk_multiplier = 1.8` (maximum risk aversion) — still an
  accurate description of `AdventureRouteScorer`'s own non-combat routing behavior.
- At bravery=1.0 (caution=0.0): `risk_multiplier = 0.4` (minimum risk aversion, floor preserved)
- The `max(0.1, …)` floor ensures survival-tier dominance is never zeroed out.

Parity ledger entry: STRAT-226 (`docs/parity_ledger/strategic_cognition.yaml`).

---

## Decisions Made

1. Selects the `AdventureRouteOption` with the highest score from the candidate list.
2. If all routes are blocked or no candidates exist, returns `DEFER_WITH_REASON` — no project update is emitted.
3. Maps the selected route via `RouteToProjectMapper` → `StrategicUpdate` (project + objective).
4. `ObjectiveIntentResolver` translates the objective into a downstream `ActionIntent` consumed by tactical phases.

---

## What It May Mutate (Via Intent Only)

All mutations are emitted as a `StateUpdate` — never applied directly inside this domain.

| Update type | Fields written |
|---|---|
| `StrategicUpdate` | `projects_add_or_update`, `current_project_id_set`, `current_objective_id_set` |
| `EntityUpdate.property_updates` | `last_routing_tick`, `last_routing_family`, `candidate_count`, `selected score` (debug trace) |

No direct writes to `AuthoritativeState` occur inside `AdventureGoalScorer.score()`.

---

## What It Must NOT Mutate

- World state of any kind (regions, ecology, resources)
- Entity inventory or gold
- Other entities' strategic or combat state
- Combat state (`alive`, HP, durability)
- Level, derived stats, or skill levels (those belong to `src/progression/`)

---

## Domain Interactions

| Domain / System | Relationship |
|---|---|
| **Motivation** | `MotivationBiasService.compute_bias_multiplier()` is called during route scoring; personality trait values and doctrine tags modulate the `personality_bias` term |
| **Perception** | World signals and `exposed_world_signals` — the set of opportunities visible to the hero — are read from perception domain outputs |
| **Cooperation** | Project locks originating from cooperative commitments (`lock_until_tick`) are respected; a hero in a cooperative lock is skipped entirely |
| **World emergence** | Active opportunities (sourced by `world_emergence`) are the primary dynamic input to route generation |
| **Strategy system** | The emitted `StrategicUpdate` (project + objective) is consumed by later tactical stages that decide immediate actions |

---

## Test Protection

Primary test targets:

```
grep -r "AdventureGoalScorer\|AdventureRouteGenerator\|AdventureRouteScorer\|RouteToProjectMapper\|RouteFamily" tests/
```

Tests must cover:

| Scenario | Required |
|---|---|
| All routes blocked → DEFER_WITH_REASON returned, no StateUpdate emitted | Yes |
| Hero with unexpired lock_until_tick → skipped, no update | Yes |
| Personality bias correctly modulates score per family | Yes |
| blocker_penalty of 2.0 applied to blocked routes | Yes |
| Greed/industry elif ordering (regression) | Recommended |
| Hard cap: >25 candidates truncated before scoring | Yes |

---

## Extension Rules

To add a new `RouteFamily`:

1. Add the value to the `RouteFamily` enum in `src/domains/adventure/schema.py`.
2. Implement a candidate source in `AdventureRouteGenerator.generate()` — define what world conditions produce this route.
3. Add a personality bias branch in `AdventureRouteScorer.score()` — which trait and contribution coefficient apply.
4. Add a mapping case in `RouteToProjectMapper` — define the `ProjectState` and initial `ObjectiveState` produced.
5. Add tests: candidate generation, score calculation, project mapping, deferred fallback.

Do not add route families that require direct mutation of world or inventory state inside the scoring or generation path. All effects belong in downstream tactical resolution phases.
