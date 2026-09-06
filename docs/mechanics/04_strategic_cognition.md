---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-09-03
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
| **Tier 4: Economic** | `harvest`, `trade`, `craft`, `occupation_change` | Accumulating wealth and equipment; `occupation_change` (`GoalKind.OCCUPATION_CHANGE`) is a `CITIZEN` entity taking an open, skill-matched civilian job (`SHOPKEEPER`/`WORKER`/`GUARD`) when idle. |

---

## 2. Interruption Resistance
To prevent "Goal Flickering" (rapidly switching between two similar goals), entities apply an **Interruption Margin**. For adventure-domain project routing specifically, this law only governs entities whose resolved `CognitionProfileDefinition.supports_adventure_routing` is `True` (`src/content/schema.py:100`) — see `docs/simulation/domains/adventure_contract.md` for the full eligibility gate. (System B's general goal-switching via `GoalRegistry` also uses `Switch_Allowed`/`Interruption_Margin`, independent of this eligibility gate.)

**Live tier-5 candidates (as of TCK-20260824-OCCUPATION-CHANGE-TRIGGER):** four `GoalKind` scorers are registered in `GoalRegistry` (`src/ai/goals/__init__.py`) and compete in tier 5's `GoalRegistry.get_all_scores()` pass, each evaluated every tick `StrategicIntelligenceSystem.evaluate_strategic_intent()` reaches for an entity (subject only to per-entity `SystemCadence` throttling): `AdventureGoalScorer` (`GoalKind.ADVENTURE_ROUTE`, `src/ai/goals/adventure_scorer.py`), `SocialContractGoalScorer` (`GoalKind.SOCIAL_CONTRACT`), `RegionStabilizationGoalScorer` (`GoalKind.REGION_STABILIZATION`, §2a below), and `OccupationChangeGoalScorer` (`GoalKind.OCCUPATION_CHANGE`, §Tier 4 Economic row above). `AdventureGoalScorer` wraps the same opportunities → `AdventureRouteGenerator.generate()` → `AdventureDecisionService.decide()` sequence, unchanged, and its materialization branch (`src/systems/strategic_systems/intelligence.py`) uses the candidate's raw route score, not its normalized `GoalScore.utility`, when constructing the resulting `ProjectState` via `RouteToProjectMapper` — the other three bespoke-materialization candidates follow the identical raw-score-not-utility rule via their own dedicated `elif` branches in the same function (never the generic branch). The formerly-separate `AdventureDecisionPhase` pipeline phase (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE) — which ran its own duplicate route-generation/scoring pass every tick, silently superseded by this tier-5 path's later-merged, last-writer-wins result whenever both ran — has been deleted; its eligibility helpers (`_resolve_cognition_profile_id`/`_supports_adventure_routing`) relocated byte-identical into this same module.

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

### Lead Contradiction Testing (E42D; TCK-20260824-LEAD-CONTRADICTION-WIRING)
Beyond time-based decay (§5), a lead can also be invalidated *immediately* when its claimed
destination is inconsistent with current world state. `LeadContradictionSystem.enforce()`
(`src/engine/pipeline_phases/lead_contradiction.py`) runs as the `lead_contradiction` phase of
`AuthoritativeApplyPipeline.refine()` (phase 32, between `strategic_intelligence` and
`near_death_hardening` — see `docs/engine/authoritative_pipeline.md`), scanning every alive
entity's non-`EXHAUSTED` leads in deterministic sorted order every tick.

Contradiction testing is per-`LeadKind`, via `_is_lead_contradicted()`:

| `LeadKind` | Contradiction test | Coverage mechanism |
| :--- | :--- | :--- |
| `location` / `resource` | Subject resolves to a resource node whose `remaining_charges <= 0`. | State-scanned in `_is_lead_contradicted()`. |
| `person` | Subject's entity id is absent from `state.entities`, or resolves to a non-`alive` entity. | State-scanned in `_is_lead_contradicted()`. |
| `object` | Subject does not match any ground item's or chest item's `item_id` (absence is the failure signal — opposite polarity from `location`/`resource`). | State-scanned in `_is_lead_contradicted()`. |
| `event` | Subject does not match any `local_scars` entry's `source_event_id`. | State-scanned in `_is_lead_contradicted()`. |
| `concept` | Not state-scanned — always returns "not contradicted" from this phase (explicit no-op, same shape as the pre-existing `information` kind). | Routed instead through `BeliefContradictionService.detect()` at the observation call site (`ObservationBeliefBridge.process_observation()`, `src/domains/information/bridge.py`, for `claim_failed_search`/`region_danger_seen` observation kinds) and `InformationBeliefPhase.apply()` (`src/domains/information/phase.py`), not the world-state scan above. |

On contradiction, the lead is marked `certainty=EXHAUSTED`, `test_outcome="FAILURE"`,
`failure_count += 1`. The originating `InformationProvider.reliability_score` is decremented by
`0.1`, floored at `0.1`. A new `UnknownFact(subject=lead.subject, reason="lead_contradicted",
priority=0.7)` is regenerated so the `InformationNeedDetector` fires a replanning
`INFORMATION_SEEKING` project next tick. A `belief_contradiction` `SimulationEvent` and a
`lead_contradiction_resolved` `SimulationEvent` are emitted for both kinds. All mutations are
typed `StrategicUpdate`/`EntityUpdate` records merged through the authoritative pipeline — no
direct state writes. See `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-230`) for parity
status.

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

### Cooperation Offer Retry Cooldown (TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING)
Unlike Committed Intentions' deliberately unbounded retry-forever pattern above, a cooperation
offer that expires unaccepted is throttled with a genuine bounded cooldown before the proposing
entity may propose again — this prevents the same entity from re-proposing a cooperation offer
to any target on the tick(s) immediately following a prior offer's expiry.

- **Key**: `"cooperation_offer_retry"`, a fixed, namespaced string entry in the same
  `IdentityComponent.cooldowns: Dict[str, int]` map used for skill cooldowns
  (`src/core/state.py`) — reused rather than adding a new `EntityState` field. It never collides
  with a real `skill_id`.
- **Scope**: per-entity blanket, not per-(entity, partner) pair — the cooldown blocks proposing to
  *any* target for its duration, not just the partner whose offer just expired.
- **Set point**: `ContractService.reap_expired_offers()` (`src/systems/social_systems/contracts.py`).
  When a reaped `OFFERED` contract has `kind == ContractKind.RECRUITMENT` (i.e. a cooperation
  offer, not a `LOAN` or other contract kind), the entity's `EntityUpdate.identity` is merged with
  `IdentityUpdate(cooldown_updates={"cooperation_offer_retry": current_tick + COOPERATION_OFFER_COOLDOWN_TICKS})`,
  alongside the existing `strategic.contracts_remove` write, in the same authoritative
  `StateUpdate` — going through the same authoritative apply path as skill cooldowns.
- **Constant**: `COOPERATION_OFFER_COOLDOWN_TICKS = 15` (module-level constant,
  `src/systems/social_systems/contracts.py`). Offer duration is 10 ticks, so a 15-tick post-expiry
  cooldown puts the next allowed proposal roughly 25 ticks after the failed attempt's creation.
- **Check point**: `CooperationDecisionService.select()` (`src/domains/cooperation/services.py`).
  Near the top of the method: `on_offer_cooldown = state.tick < entity.identity.cooldowns.get("cooperation_offer_retry", 0)`.
  This is read-only — decision logic reads state, it does not mutate it (Core Boundaries rule).
  The "good partner exists" branch is gated with `if best_report and not on_offer_cooldown:`, so a
  cooldown-gated entity falls through unchanged to the existing `solo_score >= 0.5` /
  `DEFER_NO_PARTNER` fallback logic — the same fallback path already used when no suitable partner
  exists. `CooperationIntentBridge.map_decision()` is unchanged: while on cooldown it never
  receives a `REQUEST_HELP`/`HIRE_SUPPORT` decision, so no new contract is created.
- **Not a Committed-Intentions-style retry**: this is a genuinely different, bounded-cooldown
  mechanic. Committed Intentions' Retry-on-loss (above) is deliberately retry-forever with no
  cooldown; the cooperation-offer-retry cooldown here is a fixed 15-tick durable suppression
  window applied specifically to cooperation-offer proposal, not multi-step project arbitration.

### Cooperation Offer Pending-Duplicate Gate (TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST)
The retry cooldown above only throttles re-proposing *after* a prior offer has expired. It does
not stop the same entity from creating several simultaneous un-expired offers on consecutive
ticks *before* the first one ever expires — real corpus evidence
(`highland_traverse_seed42_200t`) showed an entity creating a new `RECRUITMENT` offer on every
single tick a decision persisted (up to 11-13 simultaneous pending offers) until the first one
finally expired and set the retry cooldown. This gate closes that gap by checking for an
already-pending offer at decision time, not just a post-expiry cooldown.

- **Check point**: `CooperationDecisionService.select()` (`src/domains/cooperation/services.py`).
  Immediately after the existing `on_offer_cooldown` read: `has_pending_recruitment_offer = any(c.kind
  == ContractKind.RECRUITMENT and c.status == ContractStatus.OFFERED and (c.expiry_tick <= 0 or
  c.expiry_tick > state.tick) for c in entity.strategic.contracts.values())` — read-only, scans the
  entity's own already-materialized `strategic.contracts` map (never mutates it).
- **Scope**: per-entity blanket, mirroring the retry cooldown's own scope — any pending
  `RECRUITMENT` offer blocks a new one regardless of target, not just a pending offer to the same
  candidate.
- **Boundary semantics**: `c.expiry_tick > state.tick` (strict, not `>=`) intentionally matches
  `ContractService.reap_expired_offers()`'s own reap condition (`0 < contract.expiry_tick <=
  current_tick`) — a contract at its exact expiry tick is treated as already-expired by both, so
  this gate never disagrees with the reaper about when an offer stops counting as pending.
- **Gate site**: the same "good partner exists" branch the retry cooldown gates:
  `if best_report and not on_offer_cooldown and not has_pending_recruitment_offer:`. While gated,
  execution falls through unchanged to the existing `solo_score >= 0.5` / `DEFER_NO_PARTNER`
  fallback — identical fallback behavior to the retry-cooldown case.
- **Verified**: real A/B corpus trial (`tools/evaluate_simq.py --scenario
  highland_traverse_seed42_200t`, deterministic seed 42) confirmed the fix. Pre-fix, every one of 8
  offer-creating entities showed a consecutive per-tick creation burst (84 total burst instances,
  e.g. entity 7 created 11 offers on ticks 19-29 with no gaps); post-fix, zero burst instances
  across all entities and every offer is spaced by a full 10-tick offer lifetime or more. SOCIAL
  pillar `normalized_score` improved from 5.636 to 6.020 (grade stayed `S`, anchor unchanged).

---

### Role-Model Watching & Imitation Fidelity (TCK-20260831-ROLE-MODEL-IMITATION)
Entities periodically watch nearby entities and, from among them, admire one as a role model —
minimal durable state answering "who does this entity look up to," feeding a scaling hook for
future imitation-driven behavior.

- **State**: `CognitionModel.role_model` (`RoleModelBundle`, `src/core/cognition.py`) — 4 scalar
  fields: `admired_entity_id` (the currently-admired entity, or `None`), `admired_since_tick` (when
  the current choice started), `last_reconsidered_tick` (the last tick the choice was
  re-evaluated, even if unchanged), and `imitation_fidelity` (a `0.0`–`1.0` multiplier, default
  `0.5`). A single *current* role model at a time — no history log.
- **Cadence**: `RoleModelSelectionPhase` re-evaluates each entity's choice on the existing
  `SystemCadence.social_memory` tier (10 ticks), staggered per-entity via `should_run(tick,
  entity_id, cadence)` — no new `SystemCadence` field was added.
- **Selection rule**: proximity via `SpatialQueryService.nearby_entities(state, position,
  radius=10.0)` (the same radius used elsewhere for perception, §5) combined with
  `identity.evolution_level` — the nearest-by-radius neighbor with the strictly highest
  `evolution_level` above the watcher's own becomes the admired entity. Deterministic tie-break:
  candidates are iterated in `sorted(entity_id)` order, so ties resolve to the lowest id. Every
  cadence tick recomputes fresh — there is no "keep current unless a strictly-better candidate
  exists" carve-out, so a previously-admired entity that leaves the world or radius, or is
  overtaken by a better candidate, is implicitly replaced (or cleared to `None`) on the next
  reconsideration.
- **Imitation fidelity**: `RoleModelImitationService.compute_imitation_fidelity()`
  (`src/strategy/role_model_imitation.py`) reads `entity.identity.properties["species_id"]` →
  `SpeciesDefinition.intelligence_tier` (landed by `TCK-20260831-SPECIES-INTELLIGENCE-TIER`) and maps
  `"high"` → `1.0`, `"low"` (or an unresolved species/tier) → `0.5`. Deliberately kept as a separate
  service rather than folded into `CapacityService.derive_profile` — see the Anti-Drift Notes in
  `staging_artifacts`/`stored_artifacts/TCK-20260831-ROLE-MODEL-IMITATION/plan.md` for the fork
  rationale; `CognitionProfile`'s existing 11 fields are untouched.
- **Rollout**: gated off by default behind `ENABLE_ROLE_MODEL_IMITATION`
  (`src/domains/optimization/feature_flags.py`), per the DEV-002 default-OFF policy for brand-new
  mechanics with no corpus profile or SHADOW-validation history yet.
- **Scope note**: `imitation_fidelity` is the minimal real hook point for intelligence-tier-scaled
  behavior — this ticket does not build any actual behavior-copying/imitation-learning mechanism on
  top of it.

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
with species/faction — a wolf and a citizen drew from the identical distribution. It is now biased
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
`ActionStyle`'s own class default (`BALANCED`) regardless of personality or species, leaving 2 real,
already-wired code hooks entirely dormant: kiting distance for `SKIRMISHER`-role entities
(`src/engine/tactical.py` — `AGGRESSIVE` kites less, `EVASIVE` kites more) and opportunity-attack
suppression on a deliberate `EVASIVE` retreat (`src/engine/movement.py`). Two further sub-branches
of `ActionStyle`'s own consumption in `tactical.py` (an `AGGRESSIVE` effective-range bonus and an
`EVASIVE` "reposition instead of attacking" stub) were traced and found to be genuinely dead code
independent of this fix — a local variable computed but never read by the function's own
downstream branches — disclosed, not fixed here (out of this ticket's own scope).

**Live habit-biased re-derivation** (`TCK-20260831-HABIT-BIAS-WIRING`): both of the above dormant-
but-wired consumers can now optionally re-derive `ActionStyle` at decision-time from
*habit-biased* bravery instead of only the frozen construction-time value, gated behind
`ENABLE_HABIT_BIAS_ACTION_STYLE` (default OFF — bit-identical to the construction-time value
above while off). When the flag is ON, **both** `TacticalDecisionSystem.evaluate_entity_intent()`
(`src/engine/tactical.py`, feeding the SKIRMISHER kiting-distance branch) **and**
`MovementSystem.resolve_move()` (`src/engine/movement.py`, feeding the EVASIVE opportunity-attack
suppression check) independently call `HabitBiasService.apply_habit_bias(entity.cognition.memory.habit,
["combat_engagement"], entity.identity.personality.bravery)`, clamp the result to `[0.0, 1.0]`,
and re-run it through the same `get_action_style_for_bravery()` thresholds documented above. Both
sites were wired together in the same change deliberately — wiring only one would create a
flag-ON inconsistency between the two real `ActionStyle` consumers named above, which otherwise
read the identical frozen construction-time field.

The `combat_engagement` habit pattern that feeds this re-derivation is written by a new
`HabitBiasUpdatePhase` (`src/domains/emotion/habit_phase.py`), placed in the authoritative
mutation pipeline strictly after `memory_update` and before `self_model`, which calls
`HabitBiasService.record_outcome(habit, "combat_engagement", success=False)` for every
`combat_loss`-kind trigger event on the entity's tick. **No win/victory `WorldEventCategory`
exists yet**, so `record_outcome` can currently only ever be invoked with `success=False` — the
`combat_engagement` pattern is therefore a **one-way monotonic decay from its 0.5 neutral baseline
toward the 0.0 floor** as an entity accumulates combat losses, with no code path that can
currently raise it back up. This is not a bug; it is the accurate current behavior and must be
revisited if a win/victory trigger is ever added. See
`docs/simulation/domains/emotion_contract.md` for the full `HabitBiasService` contract and event
wiring table.

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

### 6.13 Personal Dependents Route Bias (SOC-262)

Applied in `AdventureRouteScorer.score()` block §9b, immediately after §9's escort scoring, when
the scored entity's own durable state (`entity.lifecycle.dependent_entity_ids`) is non-empty.
Unlike §6.10's `faction_directives` parameter, this term reads directly off the `entity` argument
that is unconditionally passed at every real call site — it is live-wired by construction and
cannot silently go dead the way §6.10's mechanic has.

| Route family | Adjustment | Rationale |
|---|---|---|
| `HUNT_WEAK_ENEMY` | `−2.0` (floored at 0.0) | An entity responsible for a dependent avoids unnecessary combat risk |
| `RECOVER` | `+1.0` | Recovering favors an entity that needs to remain able to care for its dependent |
| `RETURN_TOWN` | `+1.0` | Returning to town favors an entity with a dependent to attend to |

Both adjustments are flat, additive, and independently `round()`-and-floored at 0.0, matching §6.9's
own shape. The bias fires on mere **presence** of at least one id in `dependent_entity_ids` — not on
whether that id refers to a currently-alive entity — because `AdventureRouteScorer.score()` has no
world-state parameter to check liveness against (see §6.10's own precedent for why a new parameter
is deliberately not added here). This is a disclosed simplification, not an oversight.

**Durable field and write path:** `LifecycleComponent.dependent_entity_ids: list[int]`
(`src/core/state.py`), written only via `LifecycleUpdate.dependent_entity_ids_add` applied through
`LifecyclePatch.apply()` (`src/engine/patches.py`) — never a direct mutation. See
`docs/mechanics/05_world_evolution.md`'s "Personal Dependents (Non-Parental)" subsection for the
full write-path description.

**Deferred follow-up — not implemented by this mechanic:** birth-triggered parental dependent
auto-registration (a newborn automatically becoming a parent's dependent via
`parent_a_entity_id`/`parent_b_entity_id`) is explicitly **not** built here. It is deferred to
`TCK-20260902-EPIC-RPG-M3-REPRODUCTION`, pending that epic's birth-record schema maturing further.
As of this ticket, `dependent_entity_ids` is populated only via `V2EntityBuilder.lifecycle(
dependent_entity_ids=...)` or `V2EntityBuilder.replace_lifecycle()`, for tests/demo construction —
no production trigger establishes a dependent relationship automatically.

**Source:** `src/domains/adventure/scoring.py` §9b, `src/domains/adventure/schema.py`
(`AdventureRouteOption.dependent_bias`), `src/core/state.py` (`LifecycleComponent.
dependent_entity_ids`), `src/core/updates.py` (`LifecycleUpdate.dependent_entity_ids_add`),
`src/engine/patches.py` (`LifecyclePatch.apply()`) (TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS,
2026-09-02)

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

### 7.3 Role-Affinity Adjustment (TCK-20260824-RELATIONSHIP-ROLE-FIELD)

`SocialBond` gains an additive `role: RelationshipRole` field (`NEUTRAL` default / `FRIEND` /
`RIVAL`), settable only through the authoritative `SocialBondUpdate.role_set` →
`RelationshipService.process_update()` path (`src/systems/social_systems/relationships.py`). When
`PartyCompositionScorer.score(entities, actor=acting_entity)` is called with `actor` supplied, this
role tag contributes a second additive term alongside §7.2's trust/bonds term:

score = clamp(base_score + TRUST_BONUS_WEIGHT(0.15) × score_trust_bonds(actor, entities) + ROLE_AFFINITY_WEIGHT(0.10) × score_role_affinity(actor, entities), 0.0, 1.0)

`score_role_affinity` is the mean, across the candidate pool, of each candidate's directed
`RelationshipRole` value as seen from `actor`'s own `SocialComponent`: `FRIEND` → `+1.0`, `RIVAL` →
`−1.0`, `NEUTRAL` or no bond → `0.0`. Range −1.0 to 1.0; `0.0` for an unknown/never-met candidate or
when `actor` is omitted. `RelationshipRole.RIVAL` is fully independent of `nemesis_ids`/
`grudge_history`-driven nemesis promotion (§Social Systems Contract, "Nemesis promotion") — it never
reads or writes either field.

This term is purely additive: §7.1's `ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT` base-score weights
and §7.2's `TRUST_BONUS_WEIGHT` term stay bit-identical. Omitting `actor` reproduces §7.1's base score
exactly, same as before this change.

**Source:** `src/systems/social_systems/party_composition.py`, `src/core/models/social.py`,
`src/systems/social_systems/relationships.py` (SOC-247, TCK-20260824-RELATIONSHIP-ROLE-FIELD,
2026-08-27)

---

## 8. Marriage Proposal Law (idea 33, SOC-261)

Marriage is a propose/accept relationship contract following the same `ContractKind`/
`SocialAppraisalSystem` pattern §Social Systems Contract already documents for `TEACH` and
`TEAM_UP` -- it is not a scoring function and does not add a new tier-5 project kind.

**Gate.** `ContractKind.MARRIAGE` routes through `SocialAppraisalSystem.appraise_contract()`'s
shared trust prelude exactly like every other contract kind, with no marriage-specific
threshold: hard-cancel to `CANCELLED`/`TOTAL_DISTRUST` when `trust_score < 0.2` or
`bond.sentiment < -0.8`; hard-cancel to `CANCELLED`/`BETRAYAL_HISTORY` when
`betrayal_count > 0 and trust_score < 0.4`. Once the prelude passes, `_appraise_marriage()`
always accepts (`ACCEPTED`, `ReasonCode.MARRIAGE_ACCEPTED`) -- the prelude alone is the entire
gate, with no additional utility/risk model and no `eligibility_gate` field.

**Direction.** `CoreActions.execute_propose_marriage()` (`src/engine/domain/core_actions.py`)
builds a transient (non-persisted) `ContractState(kind=ContractKind.MARRIAGE, source_id=proposer,
target_id=target, status=OFFERED)` and calls `appraise_contract(target, temp_contract, context)`
-- **the target appraises the proposer**, the same direction `execute_recruit`/`execute_team_up`/
`execute_trade`/`execute_train` already use.

**Durable record.** On `ACCEPTED`, a `MarriageState` record (`src/core/strategic.py`) is written
via `StrategicUpdate.marriages_add_or_update` on **both** parties' `EntityUpdate`, through the
same authoritative `Patch.apply()` merge path `StrategicComponent.contracts` already uses:

```python
@dataclass(frozen=True, slots=True)
class MarriageState:
    id: str
    proposer_entity_id: int
    target_entity_id: int
    status: MarriageStatus  # PROPOSED | ACCEPTED | REJECTED
    married_tick: Optional[int] = None
```

`MarriageState.status` is its own three-value `MarriageStatus` enum, distinct from
`ContractStatus` (which has no `REJECTED` member) -- the transient offer's own `ContractState.status`
still resolves through the ordinary `ContractStatus` values; only the durable record uses
`MarriageStatus`. `StrategicComponent.marriages: Dict[str, MarriageState]` is keyed by a synthetic
record id (mirroring `contracts`), not by spouse entity id, so both parties can independently hold
records without collision.

**Out of scope (deliberate).** No bigamy/duplicate-marriage precondition is enforced -- nothing
prevents an entity from accumulating multiple `marriages` entries; this is a documented, deliberate
scope boundary, not an oversight, deferred to a future ticket. No fantasy-year aging or
lifecycle-duration threshold is introduced -- `married_tick` is a plain tick timestamp with no
derived-duration/expiry logic, blocked on the unmigrated `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`.
No household/family/dependents state is added to `MarriageState` -- that belongs to a separate
ticket (idea 31, Personal Dependents). `ContractService.get_project_mapping()` returns `None` for
`MARRIAGE` by construction, so a marriage proposal never materializes a tier-5 strategic project.

**Source:** `src/core/strategic.py` (`ContractKind.MARRIAGE`, `MarriageStatus`, `MarriageState`,
`StrategicComponent.marriages`); `src/core/updates.py` (`StrategicUpdate.marriages_add_or_update`/
`marriages_remove`); `src/engine/patches.py` (`Patch.apply()` merge); `src/core/enums.py`
(`ReasonCode.MARRIAGE_ACCEPTED`/`MARRIAGE_DECLINED`); `src/systems/social_systems/appraisal.py`
(`SocialAppraisalSystem._appraise_marriage()`, `appraise_contract()`'s `MARRIAGE` dispatch branch);
`src/engine/domain/core_actions.py` (`CoreActions.execute_propose_marriage()`);
`src/engine/domain/action_router.py` (`"PROPOSE_MARRIAGE"` branch) (TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT,
2026-09-02)

---

## 9. Coming of Age Archetype-Choice Roll (idea 34, STRAT-267)

A genuinely weighted (not fixed-priority) occupation-selection roll fires once when a citizen
child reaches adulthood, filling the same `role_set` slot `OccupationChangeGoalScorer`
(`src/ai/goals/occupation_change_scorer.py`, §Strategic Systems, `STRAT-259`) later reads for
adult occupation changes -- deliberately not that scorer's own fixed-priority-first-fit pattern,
since applying it here would collapse every same-tick, same-region child onto the identical
occupation.

**Gate.** Fires inside `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/
lifecycle.py`), immediately beside the existing `life_stage_set`/ELDER-branch trigger, when all
three hold simultaneously on the pre-tick frozen entity: `entity.identity.life_stage ==
LifeStage.CHILD`, the age-derived `target_stage == LifeStage.ADULT` (the same CHILD->ADULT
transition idea 20 already drives), and `entity.identity.role == EntityRole.CITIZEN`. The role
gate is not optional bookkeeping: without it this branch would also fire for a MONSTER-role
CHILD produced by the flag-gated Natural-Creature reproduction path
(`spawn_natural_creature_offspring()`, `src/systems/world_systems/generator.py`), which is
parentless but still carries a real nonzero `birth_tick` -- the no-birth-record exclusion below
does not catch it, so the role gate is the only thing preventing an incoherent
`MONSTER_HORDE`-faction entity from being handed a citizen occupation.

A second gate, `is_excluded_no_birth_record()`, additionally excludes any entity for which
`lifecycle.birth_tick == 0 AND lifecycle.parent_a_entity_id is None AND
lifecycle.parent_b_entity_id is None` all hold at once (a compound check, not `birth_tick == 0`
alone -- `HumanoidReproductionService.process_reproduction()` has no explicit `tick > 0` guard,
so a real Humanoid-path child can be born at tick 0 with non-`None` parent ids; the compound form
correctly treats that case as "has a birth record"). Forward-compatibility caveat: this is not
provably safe against a hypothetical future reproduction path with neither an accumulation gate
nor tracked parent ids -- no such path exists in the live codebase today.

**Direction.** `choose_archetype(entity, state)` (`src/ai/coming_of_age.py`) draws one role from
`{SHOPKEEPER, WORKER, GUARD}` via `DeterministicRNG(state.seed).weighted_choice(Domain.STRATEGIC,
state.tick, entity.id, roles, weights)` -- a genuine seeded weighted-random draw, never Python's
unseeded `random` module and never a deterministic argmax (an argmax over shared regional-need
terms would reproduce `OccupationChangeGoalScorer`'s exact zero-variance convergence bug through
a different mechanism). The weight vector comes from the pure function `compute_role_weights()`:

```
weight(role) = max(WEIGHT_FLOOR,
    BASE_WEIGHT
    + PERSONALITY_COEFF * personality_term(role, entity.identity.personality)
    + PARENTAL_COEFF    * parental_term(role, entity, state)
    + regional_coeff    * regional_need_term(role, entity, state)
)
```

- `personality_term`: `SHOPKEEPER -> greed`, `WORKER -> industry`, `GUARD -> bravery` (mirrors
  `PersonalityService.get_goal_modifiers()`'s own trait-to-domain mappings, `src/ai/
  personality.py`).
- `parental_term`: count of the entity's resolvable, active parents (via `state.entities.get()`,
  skipping a `None` id, a removed/dead parent, or `lifecycle.active is False`) currently holding
  that role -- 0, 1, or 2. A parentless or fully-inactive-parent entity yields a flat 0.0 for
  every role, never a crash and never a fallback toward a specific occupation.
- `regional_need_term`: `max(0.0, target_count(role) - live_count(role))`, read-only reuse of
  `OccupationChangeGoalScorer`'s own region-lookup and per-role headcount tally as an input
  signal (`BASE_OCCUPATION_DENSITY`/`MIN_OCCUPATION_SLOTS`, `src/world/occupation_config.py`) --
  not a duplicate of that scorer's own selection behavior. `region is None` yields 0.0 for every
  role.
- `WEIGHT_FLOOR = 0.05` guarantees every role keeps strictly nonzero draw probability regardless
  of how skewed the other three terms get -- the structural guard behind the convergence property
  below.

**Durable record.** The roll produces exactly one `IdentityUpdate(role_set=<role>)`, merged via
`replace()` onto the same `EntityUpdate.identity` that already carries `life_stage_set` for this
tick's CHILD->ADULT transition -- committed only through the authoritative apply pipeline
(`ApplyPath.apply_generation`/`IdentityPatch.apply()`), never a direct-mutation shortcut. The
origin-stage check (`entity.identity.life_stage == LifeStage.CHILD`, read from the pre-tick
frozen entity) is what guarantees the roll fires exactly once: once the durable `life_stage_set`
write lands, the entity's next frozen snapshot has `life_stage == ADULT`, so the branch's origin
check no longer matches on subsequent ticks.

**Convergence-risk metamorphic guard (permanent property, not just a test artifact).** Holding
`personality_coeff`/`parental_coeff` fixed, increasing `regional_coeff` must strictly increase
the entropy of the resulting weight distribution -- it must never collapse variance toward a
single dominant role. This is the direct correction for the convergence bug class
`OccupationChangeGoalScorer`'s fixed-priority-first-fit selection demonstrates: any same-region
batch of children sharing a regional-need term would otherwise deterministically converge on one
role. `WEIGHT_FLOOR` plus the genuine `weighted_choice` draw (rather than argmax) are what keep
this property true empirically for any same-tick, same-region batch, verified by
`tests/unit/strategic/test_coming_of_age_archetype_choice.py`.

**Out of scope (deliberate).** No `GoalKind`/`GoalScorer` registration -- Coming of Age stays a
direct `LifecycleSystem` write, never a goal-hierarchy candidate evaluated by
`StrategicIntelligenceSystem.evaluate_strategic_intent()`. No change to
`OccupationChangeGoalScorer`'s own fixed-priority selection logic, `_CANDIDATE_ROLES` tuple, or
`BASE_OCCUPATION_DENSITY`/`MIN_OCCUPATION_SLOTS` -- those are read-only reuse targets. No
long-run corpus-tier population-pressure convergence property (idea 38) -- the metamorphic guard
here is a bounded single-tick synthetic batch, not a long-run corpus claim.

**Source:** `src/ai/coming_of_age.py` (`compute_role_weights`, `is_excluded_no_birth_record`,
`choose_archetype`); `src/systems/lifecycle_systems/lifecycle.py`
(`LifecycleSystem.resolve_lifecycle()`'s Coming of Age sibling branch, beside the ELDER branch);
`src/platform/rng.py` (`DeterministicRNG.weighted_choice`); `src/core/enums.py`
(`Domain.STRATEGIC`); `src/core/updates.py` (`IdentityUpdate.role_set`)
(TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE, 2026-09-02)

---

## 10. Clan Lifecycle Law (idea 40/M4, SOC-264)

`ClanState` is wired into the authoritative mutation pipeline for the first time. Clan joining
follows the same propose/accept `ContractKind`/`SocialAppraisalSystem` pattern §8 Marriage
Proposal Law already documents; leaving and succession are unconditional service-level lifecycle
transitions, never scoring functions and never a new tier-5 project kind.

**Gate.** `ContractKind.CLAN` routes through `SocialAppraisalSystem.appraise_contract()`'s shared
trust prelude exactly like every other contract kind, with no Clan-specific threshold: hard-cancel
to `CANCELLED`/`TOTAL_DISTRUST` when `trust_score < 0.2` or `bond.sentiment < -0.8`; hard-cancel to
`CANCELLED`/`BETRAYAL_HISTORY` when `betrayal_count > 0 and trust_score < 0.4`. Once the prelude
passes, `_appraise_clan()` always accepts (`ACCEPTED`, `ReasonCode.CLAN_JOIN_ACCEPTED`) -- the
prelude alone is the entire gate, with no additional utility/risk model and no `tension_level`
interaction of any kind.

**Direction.** `CoreActions.execute_join_clan()` (`src/engine/domain/core_actions.py`) builds a
transient (non-persisted) `ContractState(kind=ContractKind.CLAN, source_id=joiner,
target_id=clan.leader_entity_id, status=OFFERED)` and calls
`appraise_contract(leader, temp_contract, context)` -- **the Clan's leader appraises the joining
entity**, the same "target appraises source" direction `execute_propose_marriage` already uses.
Leaving (`execute_leave_clan()`) has no appraisal gate at all -- it is unconditional.

**Durable record.** Unlike Marriage's per-entity `EntityUpdate.strategic` record, joining and
leaving write a `ClanUpdate` into `StateUpdate.clan_updates` (registry-keyed by `clan_id`,
mirroring `FactionUpdate`/`StateUpdate.faction_updates`). Because `ActionRouter.execute_action` is
contractually locked to `Dict[int, EntityUpdate]`, `execute_join_clan`/`execute_leave_clan` cannot
themselves emit a `ClanUpdate` -- they only decide ACCEPTED/CANCELLED and signal the outcome via
the ordinary `task.payload_set` annotation every action already relies on
(`ActionRoutingPhase.route()`). A second, dedicated pipeline phase, `ClanLifecyclePhase`
(`src/engine/pipeline_phases/clan_lifecycle.py`, run immediately after the existing `groups`
phase), reads that SUCCESS/FAILURE outcome and performs the actual `ClanUpdate` write. This
two-phase split -- action handler decides, phase commits -- is a deliberate design, not
incidental.

**Succession.** `ClanLifecycleService.process_succession()` (`src/systems/social_systems/
clan_lifecycle.py`) promotes the highest-sociability surviving member to `leader_entity_id`
immediately whenever the leader is dead/inactive/`None`, with **no 0.2 sociability-margin gate**
-- explicitly contrasted with Group's `PartyLifecycleService.check_leadership()` (SOC-228), which
only re-elects a *living* leader's replacement when the challenger's sociability exceeds the
current leader's by >= 0.2. Clan succession promotes on death alone; there is no "current"
sociability to beat once the leader is gone. Leader liveness uses the same same-tick-effective-
state pattern `GroupSystem.update_groups()`'s `is_alive`/`is_active` helpers use (reading the
current tick's `StateUpdate.entity_updates` before falling back to the frozen start-of-tick
`EntityState`), re-implemented locally in `ClanLifecycleService` rather than imported from
`groups.py`, to avoid coupling Clan lifecycle to Group lifecycle. Tiebreak: lowest entity id,
the same numeric convention `PartyLifecycleService.check_leadership()` uses (reused as a rule, not
via shared code).

**Dissolution.** `ClanLifecycleService.process_dissolution()` sets `dissolved_tick` only when
`member_entity_ids` **and** `asset_ids` are **both** empty simultaneously -- either alone does not
dissolve the Clan. This is a deliberate divergence from Group's `GroupSystem.update_groups()`,
which dissolves unconditionally the moment its leader dies/deactivates (SOC-176/SOC-189); Group's
dissolution path is untouched by this ticket and does not apply to Clan. `process_dissolution`
reads the start-of-tick `state.clans` snapshot, so a Clan whose last member leaves this same tick
dissolves on the *following* tick's pass -- the same one-tick lag `FactionAwarenessService`
already documents ("one-tick lag is inherent (state frozen)"), not a new pattern.

`ClanState.asset_ids: Tuple[int, ...] = ()` is the field this dissolution check reads for the
asset/institutional-footprint half of the gate. **It is currently always empty in every real run
-- no producer or consumer of this field exists anywhere in the codebase.** Nothing in this
ticket's scope grants, spends, or otherwise populates `asset_ids`; it is populated only by direct
`ClanState(...)` construction in tests. Because of this, the "zero assets" half of the AND-gate is
**inert** in practice today: `asset_ids` is always `()`, so `process_dissolution` currently
reduces to a members-only check for every Clan a real simulation run can produce. This is not a
bug and not silently load-bearing -- it is the intentional minimum schema slot the AC requires,
with the real asset-granting mechanic explicitly deferred to a future ticket (see Out of scope
below). A future reader must not mistake `asset_ids` for a currently dual-gated, load-bearing
condition; today it is dead weight the gate carries for forward compatibility only.

**Out of scope (deliberate).** Idea 68 (Inter-Clan Relations) -- `ClanState.tension_level` is
read/written by nothing in this ticket, and no diplomacy/alliance/war-adjacent field or logic is
added. No asset-granting/consuming mechanic -- `asset_ids` is read-only in this ticket's
dissolution check (see above); a future ticket owns whatever mechanic actually grants or spends
Clan assets. No Clan founding/creation logic -- Clans are pre-existing; tests construct
`ClanState` directly for fixtures, the same way `FactionState` tests do. No personal
inheritance/heir assignment -- Clan leadership succession (`leader_entity_id`) is unrelated
durable state from `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s heir field; the two "succession"
concepts must not be conflated.

**Source:** `src/core/state.py` (`ClanState.asset_ids`, `AuthoritativeState.clans`);
`src/core/updates.py` (`ClanUpdate`, `StateUpdate.clan_updates`); `src/engine/apply.py`
(clan-merge block); `src/core/strategic.py` (`ContractKind.CLAN`); `src/core/enums.py`
(`ReasonCode.CLAN_JOIN_ACCEPTED`/`CLAN_JOIN_DECLINED`); `src/systems/social_systems/appraisal.py`
(`SocialAppraisalSystem._appraise_clan()`, `appraise_contract()`'s `CLAN` dispatch branch);
`src/systems/social_systems/clan_lifecycle.py` (`ClanLifecycleService`);
`src/engine/pipeline_phases/clan_lifecycle.py` (`ClanLifecyclePhase`);
`src/engine/domain/core_actions.py` (`execute_join_clan`/`execute_leave_clan`);
`src/engine/domain/action_router.py` (`"JOIN_CLAN"`/`"LEAVE_CLAN"` branches); `src/engine/
pipeline.py` (`clan_lifecycle` phase, run after `groups`); `src/observability/events.py`
(`ClanMemberLeftEvent`, `ClanSuccessionEvent`) (TCK-20260903-CLAN-LIFECYCLE-SUCCESSION, SOC-264,
2026-09-03)

### 10a. Clan Reputation & Guilt-by-Association Law (idea 54/M5, SOC-268)

`ClanState` gains a second scalar, `clan_reputation: float = 1.0` (clamped `[0.0, 2.0]`) --
the Clan's own aggregate standing, structurally distinct from any individual member's
`SocialComponent.public_reputation`/`regional_reputation` (idea 53/idea 60, SOC-267/SOC-266).
`clan_reputation` is never derived by summing/averaging member reputations; it accrues and
decays only through the explicit misconduct deltas below. `ClanState.tension_level` (idea 68,
still out of scope) is untouched by this law.

**Write path.** The sole legal mutation point is `apply.py`'s existing clan-merge block
(`src/engine/apply.py:379-396`, the same block SOC-264 established), extended with one more
additive-delta line: `new_reputation = max(0.0, min(2.0, existing.clan_reputation +
cu.clan_reputation_delta))`, mirroring `FactionState.tension_level`'s clamp pattern at the
adjacent block. The only field carrying a delta into that block is the new
`ClanUpdate.clan_reputation_delta: float = 0.0` (`src/core/updates.py`), folded into
`ClanUpdate.is_noop()`'s existing check. Two producers exist:

- **Party defection (live).** `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py:163-170`)
  calls the new `ClanLifecycleService.find_clan_id_for_entity(state, m_id)` reverse lookup
  immediately after `PartyLifecycleService.check_defection()` returns a non-`None` entity
  update, and if the defector belongs to a Clan, appends
  `ClanUpdate(clan_id=clan_id, clan_reputation_delta=CLAN_REPUTATION_MISCONDUCT_DELTA)` to
  `new_clan_updates`. This is the only live-pipeline trigger for `clan_reputation` today.
  Runs as pipeline phase `"groups"` (`src/engine/pipeline.py:402`).
- **Contract betrayal (pure-function only, not live-wired).**
  `ContractService.compute_betrayal_clan_reputation_update(betrayer_id, state, tick)`
  (`src/systems/social_systems/contracts.py:263-291`) performs the same reverse lookup and
  returns a `ClanUpdate` with the same delta. It is deliberately kept separate from
  `resolve_contract_outcome()` because that method's `Tuple[StrategicUpdate,
  List[SocialUpdate]]` return shape is unpacked by every existing caller/test and must not
  change. **Disclosed gap, not fixed by this ticket:** `process_active_contracts()`
  (`src/systems/social_systems/contracts.py:294-300`, the only production caller of
  `resolve_contract_outcome()`, wired as pipeline phase `"active_contracts"`,
  `src/engine/pipeline.py:407`) always calls it with `success=True` and never passes
  `betrayal=True`/`betrayer_id` -- this pre-existing condition means
  `compute_betrayal_clan_reputation_update()` is reachable only from direct unit tests
  today, not from any live simulation run. A future ticket owns wiring a real
  betrayal-detection trigger into `process_active_contracts()`.

**Shared constant.** `CLAN_REPUTATION_MISCONDUCT_DELTA: float = -0.25`
(`src/systems/social_systems/clan_lifecycle.py`) is used by both producers -- no source
doc distinguishes the relative severity of defection vs. betrayal at the clan level, so one
constant covers both rather than two arbitrarily-differentiated magnitudes.

**Reverse lookup.** `ClanLifecycleService.find_clan_id_for_entity(state, entity_id) ->
Optional[str]` (`src/systems/social_systems/clan_lifecycle.py:40-51`) is a plain O(n_clans)
scan over `sorted(state.clans.items())`, returning the first Clan whose
`member_entity_ids` contains `entity_id`. No entity->clan index exists in durable state; a
scan was chosen over adding an index because no evidence in this repo's fixtures shows
Clan counts large enough to warrant one (2-6 clans in existing scenarios, the same order as
Faction counts). Sorted iteration is mandatory here, consistent with `to_canonical_dict()`
and the apply.py clan-merge block's own sorting convention.

**Read path -- stranger-judgment blend.** `SocialAppraisalSystem.appraise_contract()`'s
no-`SocialBond` ("stranger") branch (`src/systems/social_systems/appraisal.py:51-70`) gains
one additive term:

```
clan_id = ClanLifecycleService.find_clan_id_for_entity(state, source_id)
clan_trust = (state.clans[clan_id].clan_reputation / 2.0) if clan_id else 0.5

trust_score = (
    (public_trust * 0.7)
    + (history_trust * 0.3)
    + (clan_trust - 0.5) * CLAN_INFLUENCE_WEIGHT
)
```

`CLAN_INFLUENCE_WEIGHT = 0.2` (`src/systems/social_systems/appraisal.py`) bounds the clan
term to at most +/-0.1 (a full `clan_trust` swing from its floor 0.0 to its ceiling 1.0
times 0.2). This is a strictly additive delta, not a re-weighting of the two existing
terms: when the source has no Clan (`clan_id is None`), `clan_trust` defaults to `0.5`, the
delta term evaluates to exactly `0.0`, and the formula reduces byte-for-byte to the
pre-existing pinned formula (`public_trust * 0.7 + history_trust * 0.3`) that
**SOC-134** (P0, `docs/parity_ledger/social_narrative.yaml`) certifies. SOC-134's `status`
and `test_path` are unchanged by this law -- only its `v2_evidence` text was extended to
describe the new formula shape, since the no-clan case it tests remains bit-identical.
The `if bond:` branch (private-history judgment) is untouched and deliberately stays
clan-blind: a member with direct history is judged on that history, never diluted by their
counterpart's clan standing. `_appraise_clan()` (the `ContractKind.CLAN` join-offer
appraisal) is a separate code path and is not affected by this blend.

**Guard.** `tests/architecture/test_social_write_paths.py`'s existing scan for
`public_reputation=`/`regional_reputation=` writes outside its allowlist provides defense
in depth; `tests/architecture/test_clan_reputation_write_paths.py` additionally asserts (a)
`ClanState.clan_reputation` is written only by `apply.py`'s clan-merge block, and (b) no
`SocialComponent.public_reputation`/`regional_reputation` write occurs anywhere in the
clan-reputation code paths above.

**Out of scope (deliberate).** No `PublicReputationProfile`/`ReputationUpdateService`
wiring (confirmed dead code, zero call sites). No entity->clan index structure. No live
betrayal-detection trigger in `process_active_contracts()` (see above). No change to
`_appraise_clan()`'s CLAN-join gate.

**Source:** `src/core/state.py` (`ClanState.clan_reputation`); `src/core/updates.py`
(`ClanUpdate.clan_reputation_delta`); `src/engine/apply.py` (clan-merge block's reputation
clamp); `src/systems/social_systems/clan_lifecycle.py`
(`ClanLifecycleService.find_clan_id_for_entity`, `CLAN_REPUTATION_MISCONDUCT_DELTA`);
`src/engine/pipeline_phases/groups.py` (`GroupPhase.resolve()`'s defection hook);
`src/systems/social_systems/contracts.py`
(`ContractService.compute_betrayal_clan_reputation_update`);
`src/systems/social_systems/appraisal.py` (`appraise_contract()`'s stranger-judgment blend,
`CLAN_INFLUENCE_WEIGHT`) (TCK-20260904-CLAN-REPUTATION-ASSOCIATION, SOC-268, 2026-09-04)

## 11. Information Hub Knowledge Accumulation & Propagation Law (idea 41, M4)

`InformationProviderState` gains a real knowledge-accumulation mechanism, and a second,
independent mechanism propagates "critical" `WorldEvent`s City-to-City and City-to-Country using
`FactionState`'s existing `territory`/`diplomatic_relations` topology. Both are gated behind one
new flag, `ENABLE_INFORMATION_HUB_ACCUMULATION` (default OFF, DEV-002).

**Apply-path fix (prerequisite).** `ApplyPath.apply_generation`'s `AuthoritativeState(...)`
constructor call never carried `information_providers` forward -- unlike the adjacent
`factions=new_factions`/`clans=new_clans` pattern, no `information_providers=` keyword was passed
at all. Because `AuthoritativeState.information_providers` defaults to an empty dict, this silently
reset the durable provider registry to `{}` on every single tick apply, discarding both
`prior_state.information_providers` and any `StateUpdate.information_providers_update` regardless
of writer. This broke the already-shipped `STRAT-230` `LeadContradictionSystem` reliability
decrement too -- that mechanism's own `enforce()` logic was always correct, but its output never
survived a tick boundary in any real run; it was only ever observed by tests calling `enforce()`
directly. `src/engine/apply.py` now carries `information_providers` forward via the same
carry-forward-and-merge pattern as `factions`/`clans`. This is a wiring fix, not a change to
`LeadContradictionSystem`'s own decrement logic, `_RELIABILITY_PENALTY`, or `_RELIABILITY_FLOOR`.

**Accumulation.** `InformationProviderState` gains `knowledge_accumulated: int = 0` -- a
monotonically non-decreasing counter, distinct from `reliability_score` (trustworthiness) and
`knowledge_age` (freshness). `InformationAccumulationService.record_quest_reported_back()`
(`src/domains/information/accumulation.py`) is decision-only: given a provider, it returns a
replacement with `knowledge_accumulated + 1` and `knowledge_age` reset to `0`. The trigger is
hooked into `QuestResolutionSystem.enforce()`'s existing `is_newly_completed` branch
(`src/engine/quests.py`), directly beside the pre-existing ESCORT-kind reputation side effect --
when `ENABLE_INFORMATION_HUB_ACCUMULATION` is `"ON"` and the completed quest's
`QuestState.source_entity_id` resolves to a registered provider, that provider's counter
increments via `StateUpdate.information_providers_update`. Gated on `is_newly_completed` only (not
`is_retry_pending`), so a reward-delivery retry across ticks cannot double-increment.

`QuestState.source_entity_id` is an existing field this mechanism *reads*, not one this ticket
*populates* -- `GuildAction.visit()` (`src/town/guild.py`) never sets it (`source_entity_id=None`
on the Guild path), so the accumulation trigger is structurally inert in every real corpus run
today even with the flag ON. It is proven correct via direct unit-level construction of a
`QuestState`+`InformationProviderState` pair driven through the full `apply_generation` path, not
via corpus reachability. Building the Guild-to-provider attribution/seeding pipeline that would
make this live is explicitly out of this ticket's scope (a disclosed gap, not a silent narrowing).

**Propagation.** `InformationPropagationService` (`src/engine/faction_decision.py`, beside
`FactionAwarenessService`) reads `state.recent_world_events` -- the same bounded, one-tick-lagged
window `FactionAwarenessService.compute_tension_updates()` reads -- and, for every event with
`severity >= 0.8` (`_CRITICAL_SEVERITY_THRESHOLD`, this ticket's own reasoned "critical" anchor,
chosen over the disjoint `SimulationEvent.severity` vocabulary because propagation walks
`WorldEvent`s specifically) whose `region_id` sits inside a faction's `territory`:

- **City-to-City:** emits a new `WorldEvent(category=CRITICAL_INFORMATION_PROPAGATED)` at every
  *other* region in that same faction's `territory`.
- **City-to-Country:** emits the same event at every region in another faction's `territory`, but
  **only** when `diplomatic_relations.get(other_id, DiplomaticState.NEUTRAL) == ALLIED`. NEUTRAL is
  deliberately excluded -- `diplomatic_relations.get(...)` defaults an *absent* relation entry to
  `NEUTRAL`, so an unrelated faction with no explicit relation to the source would incorrectly
  receive the propagation if NEUTRAL were also a propagate-gate.

`InformationPropagationService` never mutates `FactionState` -- it emits only new `WorldEvent`s via
`StateUpdate.world_events_add` (an append-only list field with multiple existing same-tick
writers), never a `FactionUpdate`. No new `FactionState` field was added; an architecture-guard
test (`tests/architecture/test_information_hub_accumulation_guards.py`) pins `FactionState`'s field
set to prove this. The phase runs in `AuthoritativeApplyPipeline.refine()` immediately after
`faction_awareness`, gated by `ENABLE_INFORMATION_HUB_ACCUMULATION` via the standard
`run_phase(..., feature_flag=...)` form.

**Guide-to-Guide / hub-to-hub exchange (AC #5) -- scoped out entirely.** No
`Conversation`/entity-dialogue class exists anywhere in `src/`, and this ticket does not introduce
one, nor a state-level stand-in for one. An architecture-guard test enforces the zero-count
directly. Any future direct-exchange-between-providers mechanic is unbuilt and unscoped by this
ticket.

**Source:** `src/engine/apply.py` (`information_providers` carry-forward-and-merge block);
`src/domains/information/providers.py` (`InformationProviderState.knowledge_accumulated`);
`src/domains/information/accumulation.py` (`InformationAccumulationService`); `src/engine/
quests.py` (`QuestResolutionSystem.enforce()`'s accumulation branch); `src/domains/world_emergence/
schema.py` (`WorldEventCategory.CRITICAL_INFORMATION_PROPAGATED`); `src/engine/faction_decision.py`
(`InformationPropagationService`); `src/engine/pipeline.py` (`information_propagation` phase, run
after `faction_awareness`); `src/domains/optimization/feature_flags.py`
(`ENABLE_INFORMATION_HUB_ACCUMULATION`) (TCK-20260903-INFORMATION-HUB-ACCUMULATION, idea 41,
2026-09-03)

## 12. On-Death Lineage Dispatch: Inherited Feuds & Dying Wishes (ideas 55+58, M5)

Design ideas 55 (Feuds Outlive the Feuders) and 58 (A Dying Wish) both fire at the identical
trigger moment -- death, once `heir_entity_id` resolves -- so they are implemented as one dispatch
point with two thin handlers inside `LifecycleSystem.resolve_lifecycle` (`src/systems/
lifecycle_systems/lifecycle.py`), called once heir resolution completes and before the existing
heirloom-transfer block.

**Dispatch point.** `resolve_lifecycle` already resolves `heir_entity_id` deterministically (either
the deceased's manually-set heir, or the default heir selected by `_select_default_heir`) before
transferring heirlooms. `_transfer_inherited_feud()` and `_seed_dying_wish()` are called back to
back, right after heir resolution, both writing into the same `EntityUpdate` accumulated for the
heir -- there is exactly one call site, not two independently-hooked triggers.

**Idea 55 -- Inherited Feud.** `_transfer_inherited_feud()` reads the deceased's active
Campaign-mode Nemesis blockers (`entity.strategic.blockers["nemesis_*"]`, populated only by
`NemesisRelationImporter` from `CampaignState.nemesis_relations` -- see Section 3's "Grief Urgency
& Nemesis Relations" for that importer). For each, it transfers a weakened copy to the heir via a
typed `StrategicUpdate.blockers_add_or_update`: `severity * INHERITED_NEMESIS_SEVERITY_MULTIPLIER`
(0.5), with a distinct `inherited_nemesis_{antagonist}` id so it never silently overwrites a heir's
own, independently-formed nemesis blocker against the same antagonist. This is explicitly scoped to
the Campaign-mode blocker representation only -- it does not touch the always-live legacy
`SocialComponent.nemesis_ids`/`grudge_history` mechanism (tracked separately by
`TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`). Most default single-episode Kernel runs never populate
the Campaign-mode signal, so this handler is frequently a no-op -- a disclosed scope limit, not a
bug.

**Idea 58 -- A Dying Wish.** `_seed_dying_wish()` seeds a new `NamedIntentionBundle`
(`src/core/cognition.py`) onto the heir's `MotivationModel.named_intention`, source-attributed to
the deceased (`source_entity_id`), with a deterministic `text` (names the same antagonist as an
inherited feud when one exists, otherwise a generic remembrance wish -- no narrative-generation
subsystem is introduced) and `status="PENDING"`. Deliberately named distinctly from
`CommittedIntention` (`src/core/strategic.py`, Section 4's self-generated multi-step-planning
model) to avoid a naming collision. Honorable, ignorable, or rejectable: nothing in this codebase
reads `NamedIntentionBundle.status` to force an action, so seeding this bundle never
auto-executes anything.

**Same-tick cognition-write safety.** `EntityUpdate.cognition_bundle_set` is a whole-object-replace
field (`CognitionPatch.apply()`), not a per-field merge -- so `_seed_dying_wish()` follows this
codebase's established read-through-then-replace convention (mirrors `src/strategy/
role_model_phase.py`, `src/domains/emotion/habit_phase.py`, `src/engine/quests.py`'s reputation
write): it reads whatever `cognition_bundle_set` an earlier same-tick phase already staged on the
heir's `EntityUpdate` (falling back to `heir.cognition` if none), and replaces only the
`motivation.named_intention` sub-field on top of that base, before writing back. A same-tick
collision with another `cognition_bundle_set` writer therefore never silently clobbers either
write.

**Source:** `src/systems/lifecycle_systems/lifecycle.py`
(`LifecycleSystem._transfer_inherited_feud`, `LifecycleSystem._seed_dying_wish`,
`INHERITED_NEMESIS_SEVERITY_MULTIPLIER`); `src/core/cognition.py` (`NamedIntentionBundle`,
`MotivationModel.named_intention`) (TCK-20260904-LINEAGE-DEATH-DISPATCH, ideas 55+58, M5,
2026-09-04)

