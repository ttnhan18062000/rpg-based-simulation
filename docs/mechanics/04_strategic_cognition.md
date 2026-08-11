---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-08-11
---

# Chapter 4: Strategic Cognition

This chapter explains the "Mental Laws" of the simulation. Entities are not simple automatons; they possess a strategic layer that manages goals, remembers locations, and resists unnecessary interruptions.

---

## 1. Goal Hierarchy & Prioritization
Entities evaluate multiple "Concerns" and select the one with the highest calculated score as their active **Project**.

| Priority Tier | Concern Type | Drive |
| :--- | :--- | :--- |
| **Tier 1: Survival** | `danger`, `fleeing` | Avoidance of death or incapacitation. |
| **Tier 2: Biological** | `hunger`, `sleep`, `exhaustion` | Maintaining operational biological stats. |
| **Tier 3: Social** | `social`, `grudge`, `bond` | Protecting allies or seeking revenge. |
| **Tier 4: Economic** | `harvest`, `trade`, `craft` | Accumulating wealth and equipment. |

---

## 2. Interruption Resistance
To prevent "Goal Flickering" (rapidly switching between two similar goals), entities apply an **Interruption Margin**. For adventure-domain project routing specifically, this law only governs entities whose resolved `CognitionProfileDefinition.supports_adventure_routing` is `True` (`src/content/schema.py:100`) — see `docs/simulation/domains/adventure_contract.md` for the full eligibility gate. (System B's general goal-switching via `GoalRegistry` also uses `Switch_Allowed`/`Interruption_Margin`, independent of this eligibility gate.)

**Sole live tier-5 candidate (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE):** `AdventureGoalScorer` (`src/ai/goals/adventure_scorer.py`), registered unconditionally under `GoalKind.ADVENTURE_ROUTE` in `GoalRegistry`, is the sole adventure-decision mechanism — one candidate among the other `GoalKind` scorers in tier 5's `GoalRegistry.get_all_scores()` competition, evaluated every tick `StrategicIntelligenceSystem.evaluate_strategic_intent()` reaches for an entity (subject only to per-entity `SystemCadence` throttling, the same as every other `GoalKind`). It wraps the same opportunities → `AdventureRouteGenerator.generate()` → `AdventureDecisionService.decide()` sequence, unchanged, and its materialization branch (`src/systems/strategic_systems/intelligence.py`) uses the candidate's raw route score, not its normalized `GoalScore.utility`, when constructing the resulting `ProjectState` via `RouteToProjectMapper`. The formerly-separate `AdventureDecisionPhase` pipeline phase — which ran its own duplicate route-generation/scoring pass every tick, silently superseded by this tier-5 path's later-merged, last-writer-wins result whenever both ran — has been deleted; its eligibility helpers (`_resolve_cognition_profile_id`/`_supports_adventure_routing`) relocated byte-identical into this same module.

```python
# Switching Law
Switch_Allowed = New_Goal_Score > (Current_Goal_Score + Interruption_Margin)

# Where:
Interruption_Margin = Profile_Resistance * resistance_multiplier
```
*   **Profile Resistance**: A value (0.0 to 1.0) defined by the entity's personality or class.
*   **resistance_multiplier**: A profile-defined constant (not a hard-coded 30.0); value varies by entity profile.
*   **Generalized Bypass**: While a project's lock is active, only a `detour`-kind candidate is exempt from the added normalized floor/percentage gate below — it is not exempt from the base retention-priority comparison above (`candidate_project.score > effective_current_score` still applies to it unconditionally, like every candidate). Every other candidate kind, from either scoring system (System A/`AdventureRouteScorer`, declared ceiling `~2.9`, see §6.6; System B/`GoalRegistry`, ceiling `100.0`), must additionally clear a dual condition while the lock is active: its own score, normalized to its own system's ceiling, must exceed both (a) the current project's normalized effective score (`current.score/current_max + retention_margin/_GOAL_UTILITY_SCORE_MAX`), and (b) a fixed urgency floor of `0.8`. `current.score` is normalized to the current project's own system ceiling (`current_max`), same as always, but `retention_margin` is deliberately always normalized against the fixed universal baseline scale (`_GOAL_UTILITY_SCORE_MAX = 100.0`) rather than `current_max` — `retention_margin`'s own raw range (0-30, from `interruption_resistance × resistance_multiplier`) was calibrated against System B's 0-100 range from the start, and is not a coherent value against System A's much smaller `~2.9` scale, where dividing by `current_max` would let the margin term alone (e.g. `9.0/2.9 ≈ 3.1`) structurally exceed any real candidate percentage and make a locked System A project un-interruptible regardless of urgency (TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG). This generalizes the old "Danger score above 80" special case (which only ever applied to one concern kind on one 0-100 scale) to any kind on either scale.
*   **Threat-Resolved Early Release (STRAT-236)**: Before the dual-condition gate above is even entered, the lock itself (`lock_until_tick > current_tick`) is treated as already expired — the entire locked-branch block (detour exemption and dual-condition gate alike) is skipped, falling straight through to the same base retention-priority comparison (`candidate_project.score > effective_current_score`) that an unlocked or detour-kind candidate already uses — when the entity's HP ratio exceeds `0.8` **and** no alive hostile entity of a different faction is within radius `10.0` of the entity's position, evaluated via the module-level `_threat_resolved()` helper (`src/systems/strategic_systems/intelligence.py`). This check only runs when the caller supplies a real `AuthoritativeState` (`evaluate_project_switch()`'s `state` parameter, default `None`); with no `state`, the lock is evaluated exactly as if this condition did not exist. Originally `AdventureDecisionPhase`-only, this early-release condition was relocated and generalized to any caller with `state` in scope — including System B's `evaluate_strategic_intent()` — by `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION`. Purpose: prevents cascading 10-tick relocks from creating >50-tick dead windows after combat resolves (D06 F2 — 200-tick activation delay).

---

## 3. Strategic Memory: Leads & Blockers
Entities maintain a mental map of the world through two primary data structures.

### Leads (Knowledge)
A `Lead` is a stored piece of information about a resource or location.
*   **Subject**: What the lead is about (e.g., "Iron Ore").
*   **Detail**: Where it is located (e.g., `(45, 12)`).
*   **Certainty**: High, Medium, or Low. Certainty decays over time if the information is not refreshed.

### Blockers (Problems)
A `Blocker` is a reason why a goal cannot be achieved. The `BlockerKind` enum (`src/core/strategic.py`) defines the authoritative set of blocker kinds:

*   **`access`**: A path is blocked, a location is unreachable, or navigation is oscillating. Congestion (too many entities in an area) is also reported as `kind="access"` with `subject="congestion"`.
*   **`material`**: Missing items, resource node unavailable, out-of-stock, or liquidity exhausted.
*   **`inventory`**: No more physical space (slot or weight capacity exceeded).
*   **`capability`**: Action or navigation is blocked due to entity capability limits (e.g., entity cannot perform the required action type).
*   **`social`**: Goal blocked by social relationship constraints.
*   **`group`**: Goal blocked by group composition or group-level requirements.

---

## 4. The Project Lifecycle
Strategic goals are broken down into a multi-step hierarchy.

1.  **Directive**: High-level intent (e.g., "Improve Defense").
2.  **Project**: A specific actionable goal (e.g., "Craft Iron Breastplate").
3.  **Objective**: A granular, atomic step (e.g., "Travel to Forge", "Interact with Anvil").
4.  **Action**: The raw engine command sent to the simulation.

---

## 5. Perception & Salience
Entities do not see the entire world.
*   **Perception Radius**: **10.0 units** — all perception and neighbor-view calls use `radius=10.0` consistently (`src/engine/domain_logic.py`, `src/engine/domain/view.py`, `src/systems/strategic_systems/intelligence.py`). A 15.0-unit radius appears only in cooperation candidate search (`src/domains/cooperation/providers.py`) and is not a perception radius.
*   **Salience Filter**: Only entities or events within the perception radius are considered "Salient." Information outside this radius is either ignored or retrieved from Memory (Leads).
*   **Info Decay**: Strategic leads lose certainty after **50 ticks** without refresh (default `stale_threshold=50` in `BeliefCycleSystem.decay_stale_beliefs`, `src/systems/strategic_systems/belief.py:47`). Leads demote from APPROXIMATE → VAGUE → EXHAUSTED. PRECISE leads (direct observations) do not decay.

---

## 6. Adventure Route Scoring Constants

**Source:** `src/domains/adventure/scoring.py` — `AdventureRouteScorer.score()`

The adventure decision pipeline (enabled via `ENABLE_ADVENTURE_ROUTING`) scores every candidate route and selects the highest. The formula and all constants are documented here.

### 6.1 Scoring Formula

```
score = urgency + benefit + personality_bias + confidence_bonus − risk_penalty − blocker_penalty
score = max(0.0, score)   # clamped to non-negative; rounded to 4 decimal places
```

### 6.2 Formula Term Constants

| Term | Formula | Constants | Max value |
|---|---|---|---|
| `urgency` | `max(need.urgency for matched needs)` | Depends on active need pressures | ~2.0 |
| `benefit` | `route.expected_benefit × depletion_fraction` (GATHER_RESOURCE); `route.expected_benefit` (all others) | World-defined per opportunity; see §6.2.1 | — |
| `personality_bias` | `trait × weight` (family-matched; see §6.4) | **Weight varies by trait** (greed: 0.50, sociability: 0.40, others: 0.25) | 0.50 |
| `confidence_bonus` | `route.confidence × 0.15` | **Weight: 0.15** | 0.15 |
| `risk_penalty` | `route.expected_risk × risk_multiplier × 0.5` | **Risk weight: 0.5**; multiplier below | — |
| `blocker_penalty` | `2.0 if route.blockers else 0.0` | **Fixed: 2.0** (see §6.3) | 2.0 |

#### §6.2.1 Depletion Fraction (GATHER_RESOURCE only)

For `GATHER_RESOURCE` routes, the `benefit` term is scaled by a **depletion fraction** derived from the target resource node's charge state:

```
depletion_fraction = remaining_charges / max_charges
benefit = route.expected_benefit × depletion_fraction
```

| Charge state | `depletion_fraction` | Effect on benefit |
|---|---|---|
| Full (`remaining == max`) | 1.0 | No reduction |
| Half depleted | 0.5 | 50% reduction |
| Empty (`remaining == 0`) | 0.0 | Benefit zeroed |

**Guards:** Scaling is skipped (benefit used as-is) when:
- `resource_nodes` is not available (backward-compatible path)
- `route.target_node_id` is `None` (route not backed by a specific node)
- The target node is not found in `resource_nodes`
- `max_charges == 0` (division-by-zero guard)

**Source:** `src/domains/adventure/scoring.py` — `AdventureRouteScorer.score()` (TCK-20260619-E21C-SCORING-WIRE, 2026-06-20)

### 6.3 Risk Multiplier

```python
risk_multiplier = max(0.1, (1.0 + caution × 0.8) − bravery × 0.6)
```

| Parameter | Coefficient | Effect |
|---|---|---|
| `caution` (= 1.0 − bravery) | 0.8 | Higher caution → higher risk multiplier → more conservative |
| `bravery` | 0.6 | Higher bravery → lower risk multiplier → more risk-tolerant |
| Floor | 0.1 | Prevents multiplier going negative (very high bravery edge case) |

Range: 0.1 (pure bravery) to 1.8 (pure caution). Default personality (bravery=0, caution=1.0) → multiplier = 1.8.

**Related, real-time counterpart** (`TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY`):
this Risk Multiplier governs strategic (long-horizon) risk assessment. The tactical, real-time
panic/flee decision (`AppraisalSystem.evaluate_emotional_state`, `src/engine/cognition.py`) is a
separate function — until this ticket, it did not reference `bravery` at all, despite
`bravery`'s own dataclass comment declaring "Biases combat vs flee"
(`src/core/state.py:420`). It now subtracts `bravery * 0.3` from accumulated panic before the
`panic > 0.4` flee threshold check, giving personality a real effect on the immediate,
per-tick combat-vs-flee decision as well as the strategic one documented above.

**Where `bravery` itself comes from** (`TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION`):
`bravery` is a real, per-entity `DeterministicRNG` draw in `[0.0, 1.0)`
(`src/worldbuilding/compiler.py`, `get_bravery_bias()`). Until this ticket it was uncorrelated
with race/faction — a wolf and a citizen drew from the identical distribution. It is now biased
by the entity's real faction `alignment_bucket` (`data/content/social/factions.yaml`, via
`FactionSemanticsService.get_alignment_bucket`): `wild` +0.35, `invader` +0.25, `rival` +0.15,
`defender` +0.05, `neutral` +0.0, additive and clamped to `[0.0, 1.0]` — individual per-entity
variance is preserved within each faction, but the population mean now differs meaningfully by
faction (e.g. a real `wild_beast_pack` population averages bravery ≈0.89 vs. a real
`merchant_league` population's ≈0.49, measured on live compiled worlds).

Both the bias table and the values below are real, external, data-driven tuning data
(`data/content/social/personality_bias.yaml`, read by `WorldCompiler.compile()`), not hardcoded
in `compiler.py` — a designer can retune magnitudes without a code change.

**`ActionStyle` wiring** (`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`): the entity's own final
(bias-applied) bravery also sets its real `ActionStyle` (`src/core/enums.py`:
`BALANCED`/`AGGRESSIVE`/`EVASIVE`) at generation, via thresholds in the same data file
(`aggressive_at_or_above: 0.65`, `evasive_at_or_below: 0.35`). Until this ticket every entity kept
`ActionStyle`'s own class default (`BALANCED`) regardless of personality or race, leaving 2 real,
already-wired code hooks entirely dormant: kiting distance for `SKIRMISHER`-role entities
(`src/engine/tactical.py` — `AGGRESSIVE` kites less, `EVASIVE` kites more) and opportunity-attack
suppression on a deliberate `EVASIVE` retreat (`src/engine/movement.py`). Two further sub-branches
of `ActionStyle`'s own consumption in `tactical.py` (an `AGGRESSIVE` effective-range bonus and an
`EVASIVE` "reposition instead of attacking" stub) were traced and found to be genuinely dead code
independent of this fix — a local variable computed but never read by the function's own
downstream branches — disclosed, not fixed here (out of this ticket's own scope).

### 6.4 Personality Bias by Route Family

| RouteFamily | Trait | Weight |
|---|---|---|
| `RECOVER` | `caution` | 0.25 |
| `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD`, `TAKE_EASY_QUEST` | `greed` | **0.50** |
| `ASK_INFORMATION`, `SCOUT_LOCATION` | `curiosity` | 0.25 |
| `CRAFT_UPGRADE`, `GATHER_RESOURCE` | `industry` | 0.25 |
| `FORM_PARTY` | `sociability` | **0.40** |
| `QUEST_OPPORTUNITY` | `greed` | **0.50** |
| `BUY_UPGRADE`, `COMBAT_ENGAGE`, `DEFER_WITH_REASON` | (none) | 0.0 |

Only one family match applies per route. Maximum personality_bias = 0.50 (greed routes).

**Calibration history:** Weights were raised from a uniform 0.25 (E11C, 2026-06-28) after the
E11B 1k-tick personality audit showed greed and sociability had Δ<0.05 effect on route
selection. Bravery already exerts strong influence via risk_multiplier (multiplicative path)
and was not changed.

### 6.5 blocker_penalty = 2.0 — Justification

`blocker_penalty` is a **fixed constant**, not graduated by severity.

**Rationale (E12A, 2026-06-20):** In 100-tick measurements with `ENABLE_ADVENTURE_ROUTING=ON` (urban_political, seed=42), `blocker_frequency = 0.0` — no blocked routes were scored because resource nodes are absent in the test world. The constant cannot be empirically refined until world content provides non-DEFER route candidates.

**Design intent:** A route with _any_ blocker (missing item, inaccessible location) should be strongly deprioritized. The 2.0 magnitude exceeds the maximum personality_bias+confidence_bonus contribution (0.65 post-E11C), ensuring blocked routes are overridden by the highest-urgency unblocked routes.

**Revisit trigger:** If `blocker_frequency > 0.05` is observed in E12C regression tests, reconsider whether 2.0 is too blunt for minor blockers (e.g., gold deficit < 5).

### 6.7 QUEST_OPPORTUNITY — HERO Capability Matching

`QUEST_OPPORTUNITY` routes use a capability-match multiplier on `benefit` based on entity role and trait alignment.

**Source:** `src/domains/adventure/scoring.py` — `AdventureRouteScorer.score()` (TCK-20260619-E23D-HERO-MATCHING, 2026-06-20)

#### Role-based benefit multiplier

| Entity role | `capability_match` | `benefit` formula |
|---|---|---|
| `HERO` (full match) | 1.0 | `expected_benefit × 2.0` |
| `HERO` (partial match) | 0.5 | `expected_benefit × 1.5` |
| `HERO` (no match / no registry) | 0.0 | `expected_benefit × 1.0` |
| Non-HERO | N/A | `expected_benefit × 0.5` |

#### Capability match algorithm

```
entity_traits  = { token.split(":")[0].lower() for token in entity.identity.traits }
required_verbs = { token.split(":")[0].lower() for token in quest.objective_chain }
ratio          = len(entity_traits ∩ required_verbs) / len(required_verbs)

capability_match = 1.0  if ratio >= 1.0
                 = 0.5  if 0 < ratio < 1.0
                 = 0.0  otherwise (no match, missing registry entry, or null quest_id)
```

Traits are compared by verb prefix only (first token before `:`). Token format: `"verb:target:count"`.

**Guards (graceful fallback to 0.0):**
- `quest_registry` is `None`
- `route.quest_id` is `None`
- `route.quest_id` not found in `quest_registry`
- `objective_chain` is empty

### 6.6 Score Range Summary (Estimated, No Blockers)

| Component | Min | Max |
|---|---|---|
| urgency | 0.0 | ~2.0 |
| benefit | 0.0 | ~0.5 (typical opportunity) |
| personality_bias | 0.0 | 0.25 |
| confidence_bonus | 0.0 | 0.15 |
| risk_penalty | 0.0 | ~0.9 (max_risk=1.0 × 1.8 × 0.5) |
| **Total non-blocked** | 0.0 | ~2.9 |
| blocker_penalty | 0.0 | 2.0 (fixed) |
| **Total blocked** | clamped to 0 | ~0.9 |

This `~2.9` "Total non-blocked" ceiling is also the normalization anchor
(`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, `src/systems/strategic_systems/intelligence.py:29-31`) that
System A candidate scores are divided by when evaluated against §2's Generalized Bypass gate.

The same constant has a second consumer as of TCK-20260811-ADVENTURE-GOAL-SCORER: `AdventureGoalScorer`
(§2, "New tier-5 candidate") normalizes a raw route score onto the `GoalScore.utility` 0-100 scale via
`utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` for tier-5 goal
competition — a different purpose than the Generalized Bypass gate above, but the same anchor value.
Both readings must stay consistent if `_ADVENTURE_ROUTE_SCORE_MAX` is ever recalibrated. This
normalized `utility` is used only for tier-5 arbitration; the materialization branch that commits a
winning `ADVENTURE_ROUTE` candidate to a real `ProjectState` uses the raw route score instead, since
the resulting `ProjectState.kind` is a `ProjectKind` classified back onto this same 2.9-ceiling scale,
not the 100.0 one.

---

### 6.8 Class-Synergy Multipliers (SOC-229)

Applied in `AdventureRouteScorer.score()` block §8 when a `GroupRecord` context is passed. Read-only; no mutation.

| Condition | Route | Effect |
|---|---|---|
| WARRIOR + MAGE both in `group.roles` | `HUNT_WEAK_ENEMY` | `final_score × 1.15` |
| Entity is `EntityRole.HERO` | `QUEST_OPPORTUNITY` | `final_score × 1.10` |

**Source:** `src/domains/adventure/scoring.py` (TCK-20260619-E41C-REWARD-DIST, 2026-06-20)

---

### 6.9 Escort Route Scoring (SOC-230)

Applied in `AdventureRouteScorer.score()` block §9 when a group has `escort_target_id` set and the scored entity is **not** the escort target.

| Route family | Adjustment | Rationale |
|---|---|---|
| `PROTECT_TARGET` | `+3.0` (additive) | High-urgency — protecting the target overrides most other goals |
| `OWN_SURVIVAL` | `−1.0` (floored at 0.0) | Deprioritise self-preservation when escort duty is active |

The escort target entity itself receives no adjustment (it cannot protect itself via this route).

**New RouteFamily members:**
- `PROTECT_TARGET = "protect_target"` — guarding or covering the escort target.
- `OWN_SURVIVAL = "own_survival"` — self-preservation actions (retreat, heal, flee).

**Source:** `src/domains/adventure/schema.py` (RouteFamily), `src/domains/adventure/scoring.py` §9 (TCK-20260619-E41D-DEFECTION-ESCORT, 2026-06-21)

---

### 6.10 Faction Directive Urgency Scoring (E53Ac)

Applied in `AdventureRouteScorer.score()` block §2b when `faction_directives` is non-None.
`FactionDecisionPhase.execute()` runs every tick in the pipeline, producing a
`list[FactionDirective]`, but as of `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` this list is
**not** threaded into the live adventure-routing call path: `AdventureGoalScorer.score()`
(`src/ai/goals/adventure_scorer.py`, the sole live adventure-decision mechanism) calls
`AdventureDecisionService.decide()` with `faction_directives=None` unconditionally — there is no
`state.faction_directives` attribute for a `GoalScorer.score(entity, state)` call site to read,
unlike the deleted phase's own `apply()` signature, which received it as a pipeline-level
argument. This section's scoring table below remains accurate for when `faction_directives` is
supplied (e.g. via direct test calls to the scorer/service), but describes a condition that does
not occur in a live tick today — a disclosed simplification, not implemented parity.

| Entity role | Route family | Condition | Urgency delta |
|---|---|---|---|
| `GUARD` | `HUNT_WEAK_ENEMY` | Any `DEFEND_BORDER` directive in faction_directives | `+2.0` |
| `SHOPKEEPER` | `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD` | Any faction has `diplomatic_relations[*] == "allied"` | `+1.5` |
| `HERO` | `QUEST_OPPORTUNITY` | Any `COMMISSION_QUEST` directive in faction_directives | `+3.0` |

These are additive urgency boosts on top of the need-urgency baseline. Final scores above 1.0
are valid and expected when faction pressure compounds with active needs.

`HUNT_WEAK_ENEMY` serves as the patrol proxy for GUARD entities because no `PATROL` RouteFamily
exists. See `docs/guidelines/v2_intentional_divergences.md` for rationale.

**Parity reference:** `docs/parity_ledger/strategic_cognition.yaml` (FACTION-DIR-001)

**Source:** `src/domains/adventure/scoring.py` §2b, `src/engine/faction_decision.py`,
`src/engine/faction_constants.py` (TCK-20260619-E53Ac-DIRECTIVE-PROP, 2026-06-22)

