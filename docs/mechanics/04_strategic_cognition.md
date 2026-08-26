---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-08-26
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
*   **Generalized Bypass**: While a project's lock is active, only a `detour`-kind candidate is exempt from the added normalized floor/percentage gate below — it is not exempt from the base retention-priority comparison above (`candidate_project.score > effective_current_score` still applies to it unconditionally, like every candidate). Every other candidate kind, from either scoring system (System A/`AdventureRouteScorer`, declared ceiling `~2.9`, see §6.6; System B/`GoalRegistry`, ceiling `100.0`), must additionally clear a dual condition while the lock is active: its own score, normalized to its own system's ceiling, must exceed both (a) the current project's normalized effective score (`current.score/current_max + retention_margin/_GOAL_UTILITY_SCORE_MAX`), and (b) a fixed urgency floor of `0.8`. `current.score` is normalized to the current project's own system ceiling (`current_max`), same as always, but `retention_margin` is deliberately always normalized against the fixed universal baseline scale (`_GOAL_UTILITY_SCORE_MAX = 100.0`) rather than `current_max` — `retention_margin`'s own raw range (0-30, from `interruption_resistance × resistance_multiplier`) was calibrated against System B's 0-100 range from the start, and is not a coherent value against System A's much smaller `~2.9` scale, where dividing by `current_max` would let the margin term alone (e.g. `9.0/2.9 ≈ 3.1`) structurally exceed any real candidate percentage and make a locked System A project un-interruptible regardless of urgency (TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG). This generalizes the old "Danger score above 80" special case (which only ever applied to one concern kind on one 0-100 scale) to any kind on either scale. As of `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`, `SocialContractGoalScorer`-materialized projects also land on System A's `~2.9` ceiling once materialized (any real `ProjectKind`-typed candidate does, by `_score_scale_max()`'s `isinstance` check) — "System A" here means "any `ProjectKind`-typed candidate," not specifically adventure.
*   **Threat-Resolved Early Release (STRAT-236)**: Before the dual-condition gate above is even entered, the lock itself (`lock_until_tick > current_tick`) is treated as already expired — the entire locked-branch block (detour exemption and dual-condition gate alike) is skipped, falling straight through to the same base retention-priority comparison (`candidate_project.score > effective_current_score`) that an unlocked or detour-kind candidate already uses — when the entity's HP ratio exceeds `0.8` **and** no alive hostile entity of a different faction is within radius `10.0` of the entity's position, evaluated via the module-level `_threat_resolved()` helper (`src/systems/strategic_systems/intelligence.py`). This check only runs when the caller supplies a real `AuthoritativeState` (`evaluate_project_switch()`'s `state` parameter, default `None`); with no `state`, the lock is evaluated exactly as if this condition did not exist. Originally `AdventureDecisionPhase`-only, this early-release condition was relocated and generalized to any caller with `state` in scope — including System B's `evaluate_strategic_intent()` — by `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION`. Purpose: prevents cascading 10-tick relocks from creating >50-tick dead windows after combat resolves (D06 F2 — 200-tick activation delay).

---

## 2a. Regional Danger and Stabilization Projects (LEG-RPG-116)

When an entity's current region's `hazard_level` exceeds `0.7`, `EventInterpreter.
compute_danger_urgency()` (`src/systems/world_systems/events.py`) computes
`urgency = min(1.0, (hazard_level - 0.7) / 0.3)` (0.0 at the threshold, 1.0 at `hazard_level >= 1.0`)
and `interpret_regional_danger()` generates a `danger`-kind `ConcernState` from it every tick this
method is called (today: only from its own direct unit tests -- see the Reachability note below).

As of `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`, `RegionStabilizationGoalScorer`
(`src/ai/goals/region_stabilization_scorer.py`), registered under `GoalKind.REGION_STABILIZATION`,
is the live production path for this mechanic: it resolves the entity's current region via
`LegalityServiceV2.get_region_for_position()`, calls the same `compute_danger_urgency()` helper, and
-- if the region is dangerous -- emits a tier-5 `GoalScore` candidate. Its raw score is
`urgency * 2.9` (calibrated to System A's `~2.9` ceiling, §6.6), carried in `GoalScore.metadata
["raw_score"]`; its `target_pos` is the region's own centroid (`(bounds[0]+bounds[2])/2,
(bounds[1]+bounds[3])/2`), since a region id is not itself a resolvable tactical target. A winning
candidate materializes into a `ProjectState(kind=ProjectKind.STABILIZE, ...)` through
`evaluate_project_switch()`, exactly like every other tier-5 candidate -- not an unconditional
override.

**Reachability note**: `interpret_regional_danger()` itself has no production caller, before or
after this migration -- it exists only for its own concern-generation unit tests. Unlike
`AdventureGoalScorer`/`SocialContractGoalScorer` (which wrapped already-live decision paths),
`RegionStabilizationGoalScorer` re-implements the hazard-threshold/urgency decision to read
`state.regions` directly (via the shared `compute_danger_urgency()` helper), which means
**registering this scorer makes LEG-RPG-116 live-reachable in production for the first time** --
not merely a bypass-closure on an already-live mechanic. See
`docs/parity_ledger/strategic_cognition.yaml` (`STRAT-255`) for the full disclosure.

**Pre-migration behavior (historical, no longer current)**: prior to this ticket,
`interpret_regional_danger()` additionally computed `should_pivot = urgency >
profile.interruption_resistance` and, if true, unconditionally suspended the entity's current
project and set `current_project_id` directly -- with no comparison against the current project's
own strength or lock state. This direct-write bypass has been removed; `should_pivot`'s
urgency-vs-resistance formula is not preserved anywhere post-migration -- `profile.
interruption_resistance` still governs pivoting, but only through the single, unified
`retention_margin` mechanism (§2) every other tier-5 candidate already goes through.

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

### Grief Urgency & Nemesis Relations: Two Injection Paths (TCK-20260824-GRIEF-NEMESIS-REACHABILITY)

Grief-urgency `ConcernState`s and nemesis-relation `BlockerState`s (E43F/E43G) are injected via
two structurally different paths, distinguished by whether a live `Kernel`/`ApplyPath` exists at
injection time.

**Path 1 — Episode boundary (pre-existing, both mechanisms).** At the start of each campaign
episode, `CampaignOrchestrator._build_initial_state()` calls `GriefUrgencyImporter.apply()` /
`NemesisRelationImporter.apply()` (`src/domains/campaigns/grief_urgency.py:65-79`,
`:124-133`) for every `GriefUrgencyModifier`/`NemesisRelation` carried forward in
`CampaignState.grief_urgencies`/`.nemesis_relations`. Both `apply()` methods return a **new**
`EntityState` with the concern/blocker merged directly into `entity.strategic.concerns`/
`.blockers` — a direct-return mutation shape, not a `StrategicUpdate`. This is only
architecturally safe because it runs before any `Kernel` instance (and therefore any
`ApplyPath`) exists for the episode; there is no live tick to bypass. `CampaignState.grief_
urgencies`/`.nemesis_relations` are themselves populated at the *previous* episode's teardown by
`CampaignOrchestrator._advance_grief_urgencies()`/`_advance_nemesis_relations()`
(`src/domains/campaigns/orchestrator.py:214-221`), which detect new grief from `entity_death`
narrative entries and scan cumulative social-memory interaction history for repeated antagonism,
respectively.

**Path 2 — Mid-episode, tick-time (new, grief only).** A live ally death detected *during* a
running episode now injects the same `grief_ally_{dead_ally_id}` `SOCIAL_THREAT` concern within
the same episode, through the authoritative pipeline rather than a direct `EntityState` return:

1. `EventExtractor.detect_grief_triggers()` (`src/observability/event_extractor.py:1665-1706`)
   is called from `Kernel._phase_observability()` (`src/engine/kernel.py:1009`), immediately
   after that phase's own `EventExtractor.extract()` call. It re-walks the same
   `lifecycle.active: True→False` transition condition used for death detection and returns
   `(griever_id, dead_ally_id, urgency)` triples for every currently-alive entity whose
   `entity.social.trust_history` toward the newly-dead entity meets `ALLY_TRUST_THRESHOLD`
   (`0.30`, `src/core/social_constants.py` — re-exported by `grief_urgency.py` for its own
   callers). `urgency = round(min(1.0, trust * 0.8), 6)` — the identical
   formula `CampaignOrchestrator._advance_grief_urgencies()` uses, so the two paths cannot
   diverge in value.
2. Because Observability runs *after* that tick's own `ApplyPath` pass in the 7-phase kernel loop
   (`docs/engine/kernel.md`), the resulting mutation cannot land in the same tick that detected
   the death. `Kernel._phase_observability()` records a `GriefUrgencyTriggeredEvent` immediately
   (`kernel.py:1008-1012`) and queues each triple onto `Kernel._pending_grief_triggers`
   (`kernel.py:1013`).
3. On the *next* tick's `_phase_resolution()`, `Kernel._drain_pending_grief_triggers()`
   (`kernel.py:692-730`) converts each queued triple into a `StrategicUpdate` via
   `GriefUrgencyImporter.build_strategic_update()` (`grief_urgency.py:81-91`) — built from the
   same `_build_grief_concern()` helper (`grief_urgency.py:45-63`) Path 1's `apply()` uses, so
   the concern id/shape cannot drift between the two paths. The `StrategicUpdate` is merged into
   that tick's `entity_updates` (`EntityUpdate.merge()`, preserving any decision system's own
   update for the same entity) and committed through the normal `AuthoritativeApplyPipeline.
   refine()` / `ApplyPath` route (`kernel.py:635`, `:659-664`) — the same authoritative route
   `src/engine/tactical.py` already uses for its own `StrategicUpdate`s. This is the durable-state
   rule this mechanism now satisfies for any mid-tick caller, which the Path 1 direct-`EntityState`
   -return shape could not.
4. **Last-tick edge case:** a death on an episode's *final* tick has no subsequent tick to drain
   into. `Kernel.drain_pending_triggers_at_teardown()` (`kernel.py:732-754`) is a one-shot
   resolution+apply flush against the current (final) state — reusing
   `_drain_pending_grief_triggers()` and the same `AuthoritativeApplyPipeline.refine()` +
   `ApplyPath.apply_generation()` commit route, but running none of the other 6 kernel phases and
   not advancing `tick`/`world_time`. `ScenarioRuntimeService.flush_pending_grief_triggers()`
   (`src/engine/scenario_runtime.py:264`) invokes it, and `CampaignOrchestrator.run_episode()`
   (`src/domains/campaigns/orchestrator.py:178`) calls that before reading `svc.final_state` —
   guaranteeing the same-episode injection guarantee holds even on the terminal tick.

**Nemesis relations do not (yet) have a mid-episode path.** `NemesisRelationImporter.
build_strategic_update()` (`grief_urgency.py:135-150`) exists for architectural symmetry with
`GriefUrgencyImporter`'s pair, but is not wired to any live call site: nemesis-relation formation
requires `NEMESIS_EPISODE_COUNT >= 2` (`grief_urgency.py:28`) distinct *episodes* of antagonism
history — a cross-episode aggregate that cannot be evaluated from a single live episode's data —
so there is no natural mid-episode trigger condition for it, unlike grief (a single death event).

**Reachability.** `CampaignOrchestrator.run_episode()` — the entry point both paths above
ultimately run under — is now reachable from a real production entry point for the first time:
`tools/calibrate_simq.py`'s new `campaign_life_arc` SimQ profile drives a new
`_run_campaign_engine()` branch (`tools/calibrate_simq.py:364-415`) that constructs a
`CampaignOrchestrator` and calls `run_episode()` in a loop, previously reachable only from tests.
Both `grief_urgency_triggered` and `nemesis_relation_formed` `SimulationEvent`s
(`event_category="social"`) are scored by the SOCIAL SimQ pillar
(`src/simulation_quality/scorers/social.py`).

---

## 4. The Project Lifecycle
Strategic goals are broken down into a multi-step hierarchy.

1.  **Directive**: High-level intent (e.g., "Improve Defense").
2.  **Project**: A specific actionable goal (e.g., "Craft Iron Breastplate").
3.  **Objective**: A granular, atomic step (e.g., "Travel to Forge", "Interact with Anvil").
4.  **Action**: The raw engine command sent to the simulation.

### Committed Intentions (Multi-Step Planning)
`CommittedIntention` (`src/core/strategic.py`) is a durable, frozen record letting an entity
commit to a short, ordered sequence of future intentions (e.g. train -> craft -> quest) instead
of re-deciding the single next action every eligible tick. `StrategicComponent.committed_intentions`
holds the sequence as a `Tuple[CommittedIntention, ...]`, capped at
`CognitionProfile.max_committed_intentions` (default **3**) and enforced by
`CapacityEnforcementPhase` using an order-preserving trim (`score_func=lambda ci: -ci.sequence_index`)
that drops the furthest-future, lowest-priority entries first, never the front of the sequence.

**Materialization.** Each eligible tick, `evaluate_strategic_intent()`
(`src/systems/strategic_systems/intelligence.py`) checks `committed_intentions[0]`: if its
`status == "pending"` and its `goal_kind` is one of the 10 generic `GoalKind` values (the
pre-epic set with live registered scorers — `ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`/
`REGION_STABILIZATION` are excluded, MVP scope), it is synthesized as an ordinary tier-5
`GoalScore` candidate (`utility=50.0`, a fixed mid-scale value) and appended to the same
candidate list `GoalRegistry`'s live scorers populate — before routine/role-utility biasing, so
it is boosted identically to a live candidate. It then competes through the completely
**unmodified** `evaluate_project_switch()` arbiter (STRAT-185/186/187 lock/margin logic
applies exactly as it does to every other tier-5 candidate). Because the 10 eligible kinds
always resolve to a real `GoalKind` instance (not `ProjectKind`), a committed intention's
materialized `ProjectState.score` equals `best_candidate.utility` directly (the 100-ceiling
scale) — this is scale-consistent by construction, unlike the three special branches, which
must use `metadata["raw_score"]` to avoid the 2.9-ceiling `ProjectKind` scale.

**Retry-on-loss.** When the synthesized candidate loses arbitration (a different candidate
wins, or `evaluate_project_switch()` itself blocks the switch), no code touches
`committed_intentions` — the entry is left exactly as it was (`sequence_index` unchanged,
`status="pending"`) and is re-synthesized and re-offered on the next eligible tick. This is a
structural consequence of the win-transition bookkeeping firing only `if switch_up:`, not a
retry counter or timer.

**Win transition.** When the synthesized candidate wins, the head entry is written back via
`StrategicUpdate.committed_intentions_add_or_update` with `status="active"` — the sole place a
`CommittedIntention` is ever mutated, going through the same authoritative
`StrategicPatch.apply()` merge path (keyed by `intention_id`, re-sorted by `sequence_index`) as
every other `StrategicComponent` collection.

**Scope note (as of this ticket).** No production write path constructs a `CommittedIntention`
yet — this mechanism is consume-side only. A future ticket owns: (a) a write path (a candidate
producer is `ProgressionPlan.goal_queue`, see
`docs/simulation/domains/progression_planner_contract.md`, auto-seeding `committed_intentions`
— explicitly deferred, not decided here), (b) mid-sequence-skip/abandonment semantics (advancing
past `committed_intentions[0]` when its status is not `"pending"` is out of scope — only the
head is ever read), and (c) a bounded retry count for a permanently-unresolvable `target_hint`
(currently: a `None` `target_hint` never clears the arbiter's own target-floor check, so it
retries forever, harmlessly, since nothing in this ticket's scope can ever produce one in
production).

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
score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment + confidence_bonus − risk_penalty − blocker_penalty
score = max(0.0, score)   # clamped to non-negative; rounded to 4 decimal places
```

### 6.2 Formula Term Constants

| Term | Formula | Constants | Max value |
|---|---|---|---|
| `urgency` | `max(need.urgency for matched needs)` | Depends on active need pressures | ~2.0 |
| `benefit` | `route.expected_benefit × depletion_fraction` (GATHER_RESOURCE); `route.expected_benefit` (all others) | World-defined per opportunity; see §6.2.1 | — |
| `personality_bias` | `trait × weight` (family-matched; see §6.4) | **Weight varies by trait** (greed: 0.50, sociability: 0.40, others: 0.25) | 0.50 |
| `plan_advance_bonus` | `1.5 if route.family matches head BuildGoal.target_route_family and that goal is pending/in_progress, else 0.0` | **Fixed: 1.5**, capped at 3.0 | 3.0 |
| `memory_adjustment` | `±1.0 when a matching CausalMemoryEntry.future_advice is present` (see §6.11) | **Fixed: ±1.0** | 1.0 |
| `confidence_bonus` | `route.confidence × 0.15` (flat); for GATHER_RESOURCE/CRAFT_UPGRADE with a resolvable capability key: `CapabilityEstimate.estimate × 0.15` (see §6.12) | **Weight: 0.15** | 0.15 |
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
| urgency | 0.0 | ~2.0 (only when faction_directives is live-supplied; see the per-need-key ceiling table below for the live tier-5-competition path) |
| benefit | 0.0 | ~0.5 (typical opportunity) |
| personality_bias | 0.0 | 0.50 (greed/GATHER_RESOURCE-family, QUEST_OPPORTUNITY); 0.40 (sociability/FORM_PARTY); 0.25 (caution/RECOVER, curiosity/ASK_INFORMATION-family, industry/CRAFT_UPGRADE) — not a flat 0.25; see §6.4 |
| confidence_bonus | 0.0 | 0.15 |
| risk_penalty | 0.0 | ~0.9 (max_risk=1.0 × 1.8 × 0.5) |
| **Total non-blocked** | 0.0 | ~2.9 (faction-directive-inclusive theoretical estimate — see live-ceiling correction below) |
| blocker_penalty | 0.0 | 2.0 (fixed) |
| **Total blocked** | clamped to 0 | ~0.9 |

This `~2.9` "Total non-blocked" ceiling is also the normalization anchor
(`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, `src/systems/strategic_systems/intelligence.py:29-31`) that
System A candidate scores are divided by when evaluated against §2's Generalized Bypass gate.

**Live tier-5-competition ceiling is lower, and now uses its own dedicated denominator
(`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`).** The `~2.9` figure above
assumes `faction_directives` is live (§6.10's urgency boosts), which — per §6.10's own
disclosure — is never true on the live `AdventureGoalScorer.score()` call path (`faction_directives=
None` unconditionally). `AdventureGoalScorer.score()`'s `utility` computation was originally
reusing `_ADVENTURE_ROUTE_SCORE_MAX=2.9` for its own tier-5-competition normalization even though
its own real, live-reachable `raw_score` ceiling never approaches it — this silently compressed
`AdventureGoalScorer.utility` into a narrow low band (empirically measured: max `raw_score=0.7439`
across a 6-run_key corpus spanning `simq_routing_test`/`hero_guild_routing` × seeds {42,123,456}
`_500t`, i.e. `utility ≈ 25.6` at the observed maximum), which `COMBAT_ENGAGE`
(floor `utility=40.0`) and `ResolveBlockerScorer` (flat `utility=80.0`) structurally dominated on
effectively every tier-5-competitive tick. The fix: `AdventureGoalScorer.score()`
(`src/ai/goals/adventure_scorer.py`) now normalizes against its own dedicated
`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4` module-level constant — decoupled from
`_ADVENTURE_ROUTE_SCORE_MAX`, which stays exactly `2.9` and continues to serve only the
Generalized Bypass gate above. `2.4` is `max(empirical raw_score corpus maximum = 0.7439,
theoretical safety floor = 2.4)` rounded up to 1 decimal place — the theoretical floor, derived
below, governs. A `min(100.0, utility)` runtime clamp guards against any future change to
opportunity-generation/need-interpretation logic silently pushing `utility` above the implicit
0-100 `GoalScore.utility` contract.

**Per-need-key urgency-tier ceiling (the real, live-reachable basis for the `2.4` theoretical
floor above).** `AdventureRouteScorer.score()`'s `urgency` term is the max urgency among whichever
`InterpretedNeed` keys a `RouteFamily` maps to (`family_needs` dict,
`src/domains/adventure/scoring.py:116-132`). Each need key's own maximum reachable urgency tier is
fixed by `src/cognition/need_interpretation.py`'s own branching — not every need key can reach
`_URGENCY_CRITICAL`:

| Need key | Max urgency tier reachable | Source |
|---|---|---|
| `healing` | `_URGENCY_CRITICAL` (0.95), when `health < 0.20` | `need_interpretation.py:70-77` |
| `food` | `_URGENCY_CRITICAL` (0.95), when `hunger > 85.0` | `need_interpretation.py:80-90` |
| `rest` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:92-101` |
| `stamina_recovery` | `_URGENCY_MEDIUM` (0.50) flat | `need_interpretation.py:103-112` |
| `equipment_repair` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:114-123` |
| `equipment_improvement` | `_URGENCY_MEDIUM` (0.50) only — never HIGH/CRITICAL | `need_interpretation.py:125-137` |
| `inventory_space` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:139-148` |
| `gold` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:150-159` |
| `information` | `_URGENCY_LOW` (0.25) flat | `need_interpretation.py:161-169` |
| `social` | never populated anywhere in the codebase — urgency term contributes `0.0` | full-repo grep, zero hits |

Of the live-reachable `RouteFamily` values (`AdventureRouteGenerator.generate()` only ever
produces `GATHER_RESOURCE`, `BUY_UPGRADE`, `CRAFT_UPGRADE`, `RECOVER`, `ASK_INFORMATION`,
`FORM_PARTY`), `RECOVER` is the dominant family at a `2.35` ceiling, rounding up to the `2.4`
theoretical floor used above — not `CRAFT_UPGRADE`, whose matched need key
(`equipment_improvement`) is hardcoded to `_URGENCY_MEDIUM` and can never reach HIGH/CRITICAL.
`RouteFamily.RECOVER` itself maps to **two** distinct opportunity kinds sharing the same
urgency-lookup key set (`generator.py:38-45`'s `kind_map`): `repair_gear` (fixed
`estimated_reward=80.0`, capping `expected_benefit=0.8`) and `rest_inn`
(`estimated_reward=sleep_debt`, a per-entity state value reaching `expected_benefit=1.0` at
`sleep_debt=100`). Because the urgency term is keyed by `route.family`, not by which opportunity
kind backs the candidate, a `rest_inn`-backed RECOVER candidate can still inherit an
independently-critical `healing` urgency (a low-health, sleep-deprived entity is a realistic
combined state). RECOVER's corrected ceiling: `urgency(0.95, healing CRITICAL) +
benefit(1.0, rest_inn at sleep_debt=100) + personality_bias(0.25, caution) +
confidence_bonus(0.15, rest_inn's confidence=1.0 fixed) − risk_penalty(0) = 2.35`.

The same constant has a second consumer as of TCK-20260811-ADVENTURE-GOAL-SCORER: `AdventureGoalScorer`
(§2, "New tier-5 candidate") normalized a raw route score onto the `GoalScore.utility` 0-100 scale via
`utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` for tier-5 goal
competition — a different purpose than the Generalized Bypass gate above, but originally the same
anchor value. As of `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`, this consumer no
longer reads `_ADVENTURE_ROUTE_SCORE_MAX` at all — it uses its own dedicated
`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` (see the live-ceiling correction above). `SocialContract
GoalScorer`/`RegionStabilizationGoalScorer` (the third/fourth consumers below) still read
`_ADVENTURE_ROUTE_SCORE_MAX = 2.9` directly, unaffected by this decoupling. This
normalized `utility` is used only for tier-5 arbitration; the materialization branch that commits a
winning `ADVENTURE_ROUTE` candidate to a real `ProjectState` uses the raw route score instead, since
the resulting `ProjectState.kind` is a `ProjectKind` classified back onto the `_ADVENTURE_ROUTE_SCORE_
MAX`-anchored 2.9-ceiling scale, not the 100.0 one.

The same constant has a third consumer as of TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER:
`SocialContractGoalScorer` (`src/ai/goals/social_contract_scorer.py`) normalizes its own raw contract
score (`clamp(trust*1.0 + urgency*1.0 + value*0.9 - risk_weight*0.3, 0.0, 2.9)`, independently
calibrated to the same 0-2.9 ceiling) onto the same `GoalScore.utility` 0-100 scale via the same
`utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` formula. This constant
is therefore now shared by two structurally unrelated raw-score domains (adventure routing, social
contracts) purely because `_score_scale_max()` classifies by Python enum class (`isinstance(kind,
ProjectKind)`), not by provenance — a deliberate, disclosed design choice (not an oversight), recorded
in `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-254`). As with `ADVENTURE_ROUTE`, the
materialization branch for a winning `SOCIAL_CONTRACT` candidate (`intelligence.py`'s
`elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:` branch) commits `ProjectState.score` from
`metadata["raw_score"]`, never from `best_candidate.utility`.

The same constant has a fourth consumer as of `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`:
`RegionStabilizationGoalScorer` normalizes `urgency * _ADVENTURE_ROUTE_SCORE_MAX` (itself
recalibrated from the pre-migration `interpret_regional_danger()`'s `urgency * 100`, which was only
valid while `kind="stabilize"` was a bare string outside `_score_scale_max()`'s `ProjectKind`
classification -- see §2a's Reachability note) onto the same `GoalScore.utility` 0-100 scale via the
same `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` formula. This
constant is therefore now shared by three structurally unrelated raw-score domains (adventure
routing, social contracts, regional stabilization), purely because `_score_scale_max()` classifies
by Python enum class (`isinstance(kind, ProjectKind)`), not by provenance — recorded in
`docs/parity_ledger/strategic_cognition.yaml` (`STRAT-255`).

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

**Downstream effect on §6.6's normalization ceiling
(`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`):** `faction_directives=None`'s
effect here is not merely a call-signature simplification — it is the specific reason §6.6's old
`~2.9` "Total non-blocked" figure over-estimated the tier-5-competition-reachable ceiling for
`AdventureGoalScorer.score()`. The `~2.0` urgency-term estimate `~2.9` was built from is only
reachable via this section's faction-directive urgency boosts; the needs-based baseline alone (see
§6.6's per-need-key ceiling table) never exceeds `0.95`. This is now corrected by §6.6's dedicated
`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4` denominator, calibrated to the real,
faction-directive-excluded live path this section describes.

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

---

### 6.11 Memory-Informed Advice Adjustment

Applied in `AdventureRouteScorer.score()` block §4c. Reads `entity.cognition.memory.causal.entries`
(a `Tuple[CausalMemoryEntry, ...]`, populated by `CausalAttributionService.attribute()`) and applies
a fixed ±1.0 adjustment for exactly 2 of the 10 real, reachable `future_advice` values a
`CausalMemoryEntry` can carry across the memory system's 4 supported `event_kind`s.

| `event_kind` | `future_advice` value | Mapped `RouteFamily` | Direction | Magnitude |
|---|---|---|---|---|
| `combat_loss` (fallback branch — fires only when none of `hp_pct < 0.3` / `stamina < 20` / `weapon_dur < 0.2` triggered) | `avoid_enemy` | `HUNT_WEAK_ENEMY` | Suppress | `−1.0` |
| `party_abandoned` (unconditional) | `boost_party_trust` | `FORM_PARTY` | Promote | `+1.0` |

The read is boolean-gated per matching advice string via `any(...)` over the full entries tuple, not
accumulated per matching entry — a full 30-entry causal-memory buffer with many matching entries
still produces exactly one ±1.0 adjustment per mapped family, never a growing stack.

**Magnitude rationale:** ±1.0 sits below `blocker_penalty` (2.0, §6.5) so a blocked route is never
rescued by a favorable memory adjustment, and above `confidence_bonus` (max 0.15, §6.2) and
`personality_bias` (max 0.50, §6.4) so the effect is unambiguously measurable, comparable in order
of magnitude to `plan_advance_bonus` (flat 1.5, §6.2). This constant remains **undertuned** — as of
`TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING`, `MemoryUpdatePhase` is wired into the pipeline (see
"Pipeline wiring status" below) but the gating `ENABLE_MEMORY_UPDATE` flag defaults to OFF, so no
live-run measurement has occurred yet — the same honest disclosure pattern §6.5 already uses for
`blocker_penalty`. Symmetric magnitude (not asymmetric suppress-vs-promote weighting) is chosen
because there is no empirical basis yet to justify asymmetry.

**Deliberately left unmapped in this pass:** `heal_first` / `rest_often` / `repair_weapon`
(`combat_loss`, non-fallback branches), `seek_trusted_guide` / `verify_intel` (`failed_search`),
`acquire_mats` / `train_blacksmith` (`failed_craft`), `realign_directive` (`party_abandoned`) — all
real, reachable advice strings, deferred to a future ticket with product/design input on the
correct `RouteFamily` target, not guessed at here.

**Pipeline wiring status:** This term is real, reachable code in `AdventureRouteScorer.score()`.
As of `TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING`, `MemoryUpdatePhase` (`src/domains/memory/phase.py`),
the only code that populates `entity.cognition.memory.causal.entries`, is now registered as the
`memory_update` phase in `AuthoritativeApplyPipeline.refine()` (between `actor_validity` and
`self_model`; see `docs/engine/authoritative_pipeline.md`), wired to a real `WorldEventCategory.COMBAT_LOSS`
trigger producer built in `ActionRoutingPhase.route()` (fires when a defender survives an `ATTACK`
and takes damage). This call site is gated by the `ENABLE_MEMORY_UPDATE` feature flag, which
**defaults to OFF** — so the term is wired but not yet enabled by default, not "always active in
production." Until a rollout decision turns the flag on for a corpus/production profile, this term
is exercised live only in tests that explicitly enable `ENABLE_MEMORY_UPDATE` (plus the existing
unit tests using manually-constructed `CausalMemoryEntry` fixtures).

**Dead-code caveat:** `AdventureRouteGenerator.generate()` never emits a `HUNT_WEAK_ENEMY` candidate
(confirmed zero emission sites) — the `avoid_enemy` suppression is provably correct at the
`AdventureRouteScorer.score()` unit level but has zero observable effect via a live
`generate()` → `score()` call chain today.

**Source:** `src/domains/adventure/scoring.py` §4c, `src/domains/adventure/schema.py`
(`memory_adjustment` field), `src/core/cognition.py` (`CausalMemoryEntry`), `src/domains/memory/
attribution.py` (`CausalAttributionService.attribute()`) (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING,
2026-08-11)

### 6.12 Capability-Driven Confidence Bonus

Applied in `AdventureRouteScorer.score()` block §5. For `GATHER_RESOURCE` and `CRAFT_UPGRADE` routes
with a resolvable capability key, `confidence_bonus` uses `CapabilityEstimate.estimate × 0.15` instead
of the flat `route.confidence × 0.15` term. All other routes, and mapped routes whose key cannot be
resolved, keep the flat term unchanged. The `0.15` weight itself does not change — only the operand
multiplied by it.

| Route family | Capability key | Key resolution source |
|---|---|---|
| `GATHER_RESOURCE` | `gather.resource.<kind>` | `resource_nodes[route.target_node_id].kind`, only when `route.requirements` carries a `has_item` entry naming a required tool |
| `CRAFT_UPGRADE` | `craft.recipe.<recipe_id>` | `route.requirements`'s `Requirement(kind="recipe_known", subject=recipe_id)` entry |

**Fallback (never raises):** the capability lookup is skipped entirely — keeping `confidence_bonus`
at `route.confidence × 0.15` — when: `resource_nodes` is `None`, `route.target_node_id` is `None`, the
target node is missing from `resource_nodes`, no `has_item` requirement naming a tool exists on a
`GATHER_RESOURCE` route, or no `recipe_known` requirement exists on a `CRAFT_UPGRADE` route. The
tool-requirement guard is necessary: `CapabilityEstimateService.estimate()`'s `has_tool` defaults to
`True` when no tool data is supplied, so an ungated call would silently switch off the flat term for
every resolvable `GATHER_RESOURCE` route, including the common case where no tool is required at all.

This is a scorer-local, ad-hoc `CapabilityEstimateService.estimate()` call — `entity.self_model.
capabilities.estimates` itself remains empty in every real tick, because `SelfModelUpdatePhase.
apply()` never passes a `capability_context` to `run()` (confirmed `src/cognition/
self_model_phase.py:57-62`). This term is fully live and observable via a real `generate() →
score()` chain today (unlike `memory_adjustment`, §6.11) because both `GATHER_RESOURCE` and
`CRAFT_UPGRADE` are live-generated route families.

**Source:** `src/domains/adventure/scoring.py` §5, `src/cognition/capability_estimate.py`
(`CapabilityEstimateService.estimate()`, unchanged) (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING,
2026-08-11)

---

## 7. Party Composition & Formation Scoring

### 7.1 PartyCompositionScorer.score() — Role Diversity & OCEAN Compatibility

`src/systems/social_systems/party_composition.py`. Pre-existing behavior (TCK-20260628-E41F-PARTY-SCORER,
first documented here as of TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY — was previously undocumented
in the Mechanics Bible):

score = ROLE_DIVERSITY_WEIGHT(0.6) × score_role_diversity(entities) + OCEAN_COMPAT_WEIGHT(0.4) × score_ocean_compatibility(entities)

- `score_role_diversity`: fraction of the 4 `PartyRole` values (TANK/HEALER/DPS/SUPPORT) represented
  in the candidate pool (0.0–1.0).
- `score_ocean_compatibility`: normalized bravery + sociability variance across the pool (0.0–1.0);
  `0.5` neutral for a single-candidate pool.

### 7.2 Trust/Bonds-Aware Adjustment (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY)

When `PartyCompositionScorer.score(entities, actor=acting_entity)` is called with `actor` supplied:

score = clamp(base_score + TRUST_BONUS_WEIGHT(0.15) × score_trust_bonds(actor, entities), 0.0, 1.0)

`score_trust_bonds` is the mean, across the candidate pool, of each candidate's directed trust value
as seen from `actor`'s own `SocialComponent`: `SocialBond.sentiment` if a bond exists toward that
candidate, else `trust_history.get(candidate.id, 0.0)` — bond takes priority (same rule as
`SocialAppraisalSystem.appraise_contract()`, §Social Systems Contract). Range −1.0 to 1.0; `0.0` for
an unknown/never-met candidate. Omitting `actor` reproduces §7.1's base score exactly.

`AdventureRouteGenerator.generate()`'s FORM_PARTY branch (`src/domains/adventure/generator.py`) uses
this to compute both `expected_benefit` (via `PartyCompositionScorer.score(candidates[:8],
actor=entity)`) and, separately, `confidence`:

confidence = clamp(sociability + 0.3 + TRUST_BONUS_WEIGHT(0.15) × score_trust_bonds(entity, candidates), 0.0, 1.0)

This is entirely generation-time (`AdventureRouteGenerator`), not scoring-time — `scoring.py`'s
`AdventureRouteScorer.score()` and its `FORM_PARTY | sociability | 0.40` `personality_bias` term
(§6.4) are **unmodified** by this section; the trust/bonds term never reaches `scoring.py`.

**Source:** `src/systems/social_systems/party_composition.py`, `src/domains/adventure/generator.py`
(TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY, 2026-08-11)

