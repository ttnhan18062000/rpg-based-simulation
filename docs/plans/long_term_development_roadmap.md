---
status: active
layer: architecture
authority: P1
audience: agent
tags: [roadmap, long-term, epics, planning, phases, simulation-quality, gameplay-loop, world-scale]
date: 2026-06-19
source: TCK-20260618-AUDIT-EPIC
---

# Engine Long-Term Development Roadmap

## Source

Synthesized from the 18-dimension audit programme (`TCK-20260618-AUDIT-EPIC`, 2026-06-19).
All scores, findings, and acceptance signals are grounded in observed simulation output and code reading — not design ambition.

See also:
- `docs/audits/audit_dimensions.md` — master audit index
- `docs/plans/engine_future_epics_roadmap.md` — gap analysis and candidate epic list (updated with audit findings)

---

## Scoring Rubric

All items scored on two axes (max 10 total). Score is consistent across all phases so items are directly comparable.

| Category | Axis A (1–5) | Axis B (1–5) | Score |
|---|---|---|---|
| **FIX** | Impact — how much damage this causes actively | Urgency — how much it blocks or compounds | A + B |
| **ADD** | Impact — behavioral/quality value when added | Unlock — how many other items this unblocks | A + B |
| **PLAN** | Impact — ceiling value for the engine | Interest — vision fit, novelty, leverage | A + B |

**Effort:** S < 1 week · M 1–4 weeks · L 1–3 months · XL 3–6 months

**Acceptance Signal:** the observable condition that proves an epic is done — not a checklist, but a behavioral or measurable fact.

---

## Phase Summary

| Phase | Goal | Horizon | Key Epics |
|---|---|---|---|
| **0 — Foundation Repair** | Make engine trustworthy | 2–3 weeks | CI, determinism, hunger satiation, entity initialization, doc repair |
| **1 — Sim Quality Foundation** | Make behavioral quality measurable | 6–10 weeks | Entity differentiation, balance baseline, content foundation |
| **2 — Depth Wave 1** | First living world | 10–14 weeks | Resource ecology, decision explanation, pressure-driven quests |
| **3 — Gameplay Loop** | Lab → product | 12–16 weeks | Scenario runtime, persistent campaign, macro-economy |
| **4 — Social & Cognition** | Entities feel like characters | 12–16 weeks | Party loop, active info-seeking, social memory |
| **5 — World Scale** | Simulation produces history | 14–18 weeks | Chronicle compiler, demographics, faction & diplomacy (XL) |
| **6 — Long Horizon** | Deliberate scheduling | 18+ months | Progression planner, culture drift, feature pack architecture |

**Critical path:** P0-2 (determinism) → P0-3 (hunger) → P0-4 (personality init) → Epic 1.1 → Epic 2.1 (resource ecology) → Epic 2.3 (quest gen) → Epic 3.2 (campaign runtime) → Epic 5.3 (faction & diplomacy).

Everything else can be parallelized around this spine.

---

## Phase 0 — Foundation Repair

**Goal:** Make the engine trustworthy before writing new code. These are pre-existing breaks that silently corrupt every experiment run on top of them. Nothing in Phase 1+ is reliable until these are done.

**Horizon:** 2–3 weeks. All S-effort items.

---

### P0-1 · CI Test Automation
**Score: 10 · Effort: S · Source: D18**
> **DONE (2026-06-25).** `.github/workflows/test.yml` added: 8 parallel domain jobs on every PR + slow-regression job (`--resource-budget large`) gated to PRs targeting `main`. `mypy` step included. See commits `146e5f31`–`63c290dd`.

**What:** A single `test.yml` GitHub Actions workflow that runs `make lane-all-fast` + `make gate-expansion` + `pytest tests/docs/` on every PR. `make lane-legacy-regression` on `main` push only (slow path).

**Scope:** ~30 lines of YAML. Wire to existing Makefile targets. No new test logic.

**Acceptance signal:** ✓ A PR that breaks an architecture guard is rejected by CI before review.

---

### P0-2 · Determinism Enforcement
**Score: 10 · Effort: S · Source: D10 F3**

**What:** Audit and replace all bare `random.` calls outside `rng.py` with `DeterministicRNG`-seeded calls. Add a static analysis step (grep or AST check) to CI that fails the build if any `import random` or `random.` appears in `src/` outside `rng.py`.

**Why now:** Bare `random.` is a P0 engine contract violation. Replay diverges without error — two runs with the same seed produce different outcomes. Any behavioral quality measurement made before this fix is potentially unreliable.

**Scope:** Replace existing bare calls; add CI lint rule. No new behavior.

**Acceptance signal:** Two 1000-tick runs with identical seeds produce identical event logs and final hash.

---

### P0-3 · Hunger Satiation Gap
**Score: 10 · Effort: S–M · Source: D06 F1**

**What:** Add a food-kind resource node to `sandbox_world` and `urban_political`. Verify that completing a hunger project reduces `need.hunger` durably and that hunger urgency stays below economic goal urgency for at least 300 ticks post-satisfaction.

**Why now:** Hunger permanently outscores every economic goal in every tested world. This is the single blocker preventing economic balance observation, crafting system validation, quest execution, and personality-driven route diversity. Without it, adding quests, crafting recipes, or personality traits has no observable effect — entities never leave hunger mode.

**Scope:** World content authoring (food node + satiation mechanic if needed). Verify using 400-tick urban_political run.

**Acceptance signal:** In a 400-tick urban_political run, at least 10% of active ticks per entity produce non-hunger project kinds.

---

### P0-4 · Entity Initialization
**Score: 10 · Effort: S · Source: D05 F1, F2**

**What:** Two changes to `WorldCompiler.compile()`: (a) seed `PersonalityComponent` using `DeterministicRNG` per entity sub-seed so bravery/greed/industry/sociability vary across entities; (b) read class assignments from `data/content/spawn_tables.yaml` so entities are assigned non-NOVICE class_ids.

**Why now:** All entities are identical at spawn — same personality vector (0,0,0,0), same class (NOVICE). The scoring formula is correct, the OCEAN system is implemented, but zero variation enters the system. Prerequisite for every behavioral differentiation measurement in Phase 1+.

**Scope:** ~20 lines in WorldCompiler; spawn_tables.yaml content; seed derivation using existing DeterministicRNG.

**Acceptance signal:** Direct state inspection at tick 0 shows personality trait variance across entities; no two entities share the same (bravery, greed, industry, sociability) tuple when seeded differently.

---

### P0-5 · Stale Documentation Repair
**Score: 9 · Effort: S · Source: D17**

**What:** Fix `docs/engine/authoritative_pipeline.md` (update 17-phase table to current 30+ phases), fix `docs/engine/kernel.md` (remove stale first phase table), fix biological thresholds in `docs/mechanics/01_entity_anatomy.md` (hunger trigger 100→95, sleep debt 80→98). Update parity ledger entries.

**Why now:** These are the three most-referenced agent context documents. An agent implementing a new domain phase will use the wrong insertion point. Stale thresholds produce wrong test ACs.

**Scope:** Doc edits + parity ledger updates. No code changes.

**Acceptance signal:** `authoritative_pipeline.md` phase table matches what `pipeline.py` actually contains.

---

### P0-6 · Code Integrity Fixes
**Score: 8 · Effort: S · Source: D12 F1, D14, D10 F1**

**What:** Three targeted code fixes:
1. Add entity_id tiebreaker to sorts in `generator.py` and `selector.py` — eliminates non-determinism on score ties
2. Inject `MovementPlanCache` via pipeline constructor rather than constructing it in `core/state.py.__post_init__` — removes upward import through the most-imported file
3. Fix teardown mode contamination in `test_registry_bridge.py` — stops 15 false cognition test failures

**Scope:** Three surgical fixes, no architecture change.

**Acceptance signal:** Test suite passes with no teardown contamination failures; 1000-tick replay hashes are stable across sort-tie scenarios.

---

## Phase 1 — Simulation Quality Foundation

**Goal:** Make behavioral quality measurable and meaningful. Phase 0 makes the engine trustworthy; Phase 1 makes it *interesting*. After Phase 1, every entity has a distinct identity, the world has content to engage with, and the economic loop has at least one full turn.

**Horizon:** 6–10 weeks across three parallel streams.

---

### Epic 1.1 · Entity Identity & Behavioral Differentiation
**Score: 9 · Effort: M · Source: D05**

**Context:** All 20 entities across both tested seeds have identical personality vectors and NOVICE class. The scoring formula is architecturally correct but receives identical inputs for every entity. Observable behavioral variation is purely positional (proximity to buildings), not character-driven.

**Goal:** After this epic, two entities with different personality vectors in the same situation make observably different route choices at statistically significant rates across 400-tick runs.

**Scope:**
- Complete P0-4 (WorldCompiler seeding) if not done
- Add HERO role entities (2–3 per world) with distinct archetypes to `sandbox_world` and `urban_political`
- Extend `spawn_tables.yaml` to assign class_id distribution: HERO → [WARRIOR, MAGE, ROGUE]; CITIZEN → [WORKER, MERCHANT]; MONSTER → [BEAST, UNDEAD]
- Add per-entity personality snapshot to LIGHT observability mode (role, class, personality vector, active_project_kind at tick N)
- Build a 400-tick differentiation test harness: measures route-kind distribution variance across entities; fails if all entities produce identical project-kind histograms
- Calibrate personality bias weights in `scoring.py` so high-bravery entities measurably prefer risky routes

**Out of scope:** Multi-episode personality evolution (Phase 4). Campaign-level character arcs (Phase 3).

**Acceptance signal:** In a 400-tick sandbox_world run, entities in the top bravery quartile take combat_engage routes at ≥ 1.5× the rate of entities in the bottom quartile (recalibrated from an original ≥2× target — `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` found real 2× unreachable at any tested population/seed combination; a 24-seed, 16-hero/8-monster measurement converges on ~1.74×). Differentiation test harness passes in CI.

**Unlocks:** D04 balance tuning can complete blocked sections. Personality calibration in Epic 1.2. Party compatibility scoring in Phase 4.

---

### Epic 1.2 · Balance & Tuning Baseline
**Score: 8 · Effort: M · Source: D04**

**Context:** Economic/crafting balance is currently unmeasurable because hunger dominates (D06 F1). The `blocker_penalty = 2.0` fixed constant is near-binary — max non-blocked score is ~2.65, so a 2.0 penalty eliminates any blocked route regardless of urgency. After P0-3, a full balance measurement pass is needed.

**Goal:** Establish quantitative baselines for all scoring constants with documented rationale. Create balance regression tests that fail if key ratios drift outside acceptable bands.

**Scope:**
- Requires P0-3 (hunger satiation) complete first
- Run D04 completion: 1000-tick urban_political runs measuring gold accumulation rate, harvesting frequency per entity-hour, quest completion rate, crafting conversion, combat attrition rate
- Audit `blocker_penalty = 2.0` — if max non-blocked score is ~2.65, a 2.0 penalty may be too severe; consider graduated penalty curve
- Audit hunger urgency threshold vs. benefit values: does completing a food-provision opportunity score above the next hunger project?
- Write balance regression tests: reference-run locked assertions on key ratios (e.g. `0.1 < harvesting_rate < 0.5` per entity per 100 ticks)
- Document all formula constants in `docs/mechanics/04_strategic_cognition.md` with justification

**Out of scope:** Faction-level supply/demand (Phase 5). Full economic macro-model (Epic 3.3).

**Acceptance signal:** D04 audit detail file promoted from `partial` to `done`. All formula constants have documented rationale. Balance regression tests run in CI.

**Unlocks:** Reliable baseline for every subsequent behavioral quality measurement. Pressure-Driven Quest Generation (Epic 2.3) calibrates against known baselines.

---

### Epic 1.3 · Content Foundation Layer
**Score: 9 · Effort: M · Source: D07**

**Context:** 430 catalog entries exist but critically skewed. Quest definitions: 4 (Gap Risk 15/15). Terrain/population module types: 0. Crafting recipes: 8 for 34 items. Without content depth, systems like quest generation, crafting loops, and world variety cannot produce meaningful runs.

**Goal:** Reach minimum viable content depth across all four critical gaps so world runs produce varied narrative output, not just combat and hunger loops.

**Scope:**

*Quest definitions (primary — Gap Risk 15/15):*
- Write 30+ quest definitions covering at least 8 world modules (only 3 have any currently)
- Quest categories: resource_fetch (10), investigation (5), escort (5), elimination (5), exploration (5), diplomatic (5+)
- Each quest needs: trigger_condition, objective_chain, reward, faction_association, expiry_ticks
- Extend at least 4 of the 6 conflict modules — conflict without quest objective produces pure combat loops

*Module types (secondary — Gap Risk 10/15):*
- Write 2 terrain modules: `mountain_pass` (traversal constraint, altitude pressure) and `river_crossing` (movement cost, resource source)
- Write 2 population modules: `nomadic_herd` (migration pressure, seasonal density) and `settled_quarter` (service density, faction alignment)

*Crafting recipes (tertiary — Gap Risk 10/15):*
- Expand from 8 to 25+ recipes; at least one recipe per item category; complete at least one gather→craft→upgrade chain (raw material → refined → item → improved item)

*Scenario coverage:*
- Add scenarios for `dungeon_crawl`, `urban_political`, `wilderness_survival` — all 8 existing scenarios are frontier-world variants

**Out of scope:** Dynamic/procedural quest generation (Epic 2.3). Faction quest chains (Phase 5). Authored faction storylines.

**Acceptance signal:** A 400-tick urban_political run produces at least one quest_started and quest_completed event. Crafting chain completes at least once in a 1000-tick run. All world compositions have at least 2 scenarios.

**Unlocks:** Pressure-Driven Quest Generation (Epic 2.3) has authored content to use as templates. Resource Ecology (Epic 2.1) has resources to actually deplete.

---

## Phase 2 — Simulation Depth Wave 1

**Goal:** First wave of major feature epics. All three are well-understood in scope, have direct audit evidence, and unlock critical downstream systems. This phase is where the simulation first starts to feel like a living world rather than a behavior loop.

**Horizon:** 10–14 weeks.

---

### Epic 2.1 · Resource Ecology Regeneration
**Score: 9 · Effort: M · D01 score: 22/25 (highest-leverage missing system)**

**Context:** Nodes are static or reset on scenario reload. `Cascade Width: 5` in D01 — enables economy pressure, quest demand, entity migration, faction territorial conflict, and world evolution in a single feature. Without it: economy never stresses, quests have no organic demand, world pressure is static, faction conflict has nothing to fight over.

**Goal:** Resource nodes deplete when harvested, regenerate at configurable rates, and create scarcity cycles that produce entity migration pressure, economic signal variation, and organic quest demand.

**Scope:**
- Add `ResourceNodeState` tracked durably in `AuthoritativeState`: current_charges, max_charges, regen_rate_per_tick, last_harvested_tick
- Wire `ResourceEcologyService` (already referenced) to apply depletion on harvest and regeneration on world tick
- Implement three regeneration models: `fixed_rate` (N charges/tick), `seasonal` (rate varies by world-age phase), `ecology_linked` (rate tied to biome health from `RegionalPressureModel`)
- Add `resource_depleted` and `resource_recovered` events to event taxonomy
- Wire depletion state into adventure decision scoring: entities near a depleted node score harvesting routes lower (reduce `expected_benefit` proportionally)
- Add resource availability to `WorldEmergencePhase` scarcity model so regional pressure increases when depletion exceeds threshold
- Update parity ledger `town_resource.yaml`

**Out of scope:** Faction territorial claims over nodes (Phase 5). Quest generation triggered by depletion (Epic 2.3). Population migration from depletion (Epic 5.2).

**Acceptance signal:** In a 1000-tick run, at least one resource node reaches 0 charges and recovers at least once. Entity harvesting routes to depleted nodes score ≤ 0.5× routes to full nodes. Regional scarcity pressure rises in the window following depletion.

**Unlocks:** Macro-Economy Health Metrics (Epic 3.3). Pressure-Driven Quest Generation (Epic 2.3). Faction territorial conflict (Epic 5.3). World Evolution ecological cycles.

---

### Epic 2.2 · Decision Explanation Model
**Score: 7 · Effort: M · Source: D15**

**Context:** Goal scoring computed in `execute_brain()` every tick and discarded at tick boundary. `cognition_graph_snapshots.jsonl` artifacts exist per run but only in DEBUG/CERTIFICATION mode, no REST API, no tick index. Without this, every behavioral quality experiment requires manual JSONL parsing.

**Goal:** A developer can query "why did entity 7 choose harvesting over town_return at tick 342?" and receive a ranked score breakdown without reading log files.

**Scope:**
- Promote route trace data to a durable per-tick snapshot: store top-5 scored routes per entity per tick (route_kind, score breakdown: urgency/benefit/personality_bias/confidence_bonus/risk_penalty/blocker_penalty, selected=True/False)
- Write snapshots to `decision_trace.jsonl` in LIGHT observability mode
- Add tick-index sidecar (`decision_trace_index.json`) mapping tick → byte offset for O(1) lookup
- REST endpoints:
  - `GET /api/v1/observability/entities/{id}/decisions?tick={N}` — tick-N snapshot
  - `GET /api/v1/observability/entities/{id}/decisions/range?from={A}&to={B}` — time range
  - `GET /api/v1/observability/entities/{id}/decisions/summary` — project-kind distribution histogram

**Out of scope:** Interactive replay UI. Multi-entity comparison view. Goal score influence visualization.

**Acceptance signal:** `curl /api/v1/observability/entities/7/decisions?tick=342` returns a ranked list of scored routes with score component breakdown, without reading JSONL manually.

**Unlocks:** Every subsequent behavioral quality experiment. Balance & Tuning validation (Epic 1.2 follow-up). Phase 4 personality calibration loop.

---

### Epic 2.3 · Pressure-Driven Quest Generation
**Score: 9 · Effort: M · Source: D07 F1, D01**

**Context:** Quest definitions are the single highest-urgency content gap (Gap Risk 15/15). The `world_emergence` `OpportunityType` extension pattern is reusable as a trigger source — this is not starting from zero. Authored quest templates from Epic 1.3 provide the content substrate.

**Goal:** Entities receive dynamically generated quest objectives driven by real world pressure signals (resource depletion, faction tension, ecological events) rather than only static authored templates.

**Scope:**
- Design `QuestOpportunity` as a new `OpportunityType` in the world emergence layer: `QuestOpportunity(kind, trigger_condition, objective_chain, reward_spec, faction_source, expiry_ticks)`
- Implement `QuestOpportunityGenerator` triggered by: resource depletion events, faction tension thresholds, calamity aftermath signals, entity needs unsatisfied for N ticks
- Wire generated quests into adventure decision pipeline: a HERO entity with matching capabilities scores a quest opportunity above a generic harvesting route
- Implement 3 quest trigger families: `resource_crisis` (fetch/secure depleted resource), `threat_response` (eliminate/scout threat source), `diplomatic_errand` (deliver/negotiate between factions)
- Quest lifecycle state: `OFFERED → ACTIVE → PROGRESSED → COMPLETED / FAILED / EXPIRED`; tracked in `AuthoritativeState.quest_registry`
- Quest completion produces rewards (gold, XP, faction reputation delta) applied through authoritative mutation pipeline
- Authored quest templates (Epic 1.3) serve as static fallbacks when pressure signals are absent

**Out of scope:** Multi-quest chains/branching narratives (Phase 4). Faction-commissioned quests (Phase 5). Quest board/marketplace mechanic.

**Acceptance signal:** In a 400-tick urban_political run after a resource depletion event, at least one HERO entity starts a `resource_crisis` quest. At least one quest reaches COMPLETED state per 1000-tick run.

**Unlocks:** Persistent Campaign Runtime (Phase 3) has meaningful quest history to persist. Social Memory (Phase 4) has outcomes to remember. Faction Diplomacy (Phase 5) has quest rewards to create diplomatic leverage.

---

## Phase 3 — Gameplay Loop

**Goal:** Close the gap between "lab tooling" and "a product that runs an RPG simulation." The simulation currently produces interesting tick-by-tick events but has no persistent continuity, no win/loss state, and no way to experience a run as a story. This phase builds the product surface.

**Horizon:** 12–16 weeks.

---

### Epic 3.1 · Scenario Runtime Service
**Score: 7 · Effort: M · Source: roadmap D**

**Context:** Only `CampaignRunner` (analysis) and sweep/CI batch runs exist. Neither has objective state, pause/resume, or checkpoint. No interactive product-shaped execution loop.

**Goal:** A scenario can be started, paused, inspected, checkpointed, and resumed with objective tracking (win condition, loss condition, stall detection) — all via a stable service API.

**Scope:**
- `ScenarioRuntimeService`: owns a running `Kernel` instance; exposes start/pause/resume/step/abort
- Objective state machine: `RUNNING → OBJECTIVE_MET / OBJECTIVE_FAILED / STALLED / ABORTED`; stall detector fires when no meaningful events for N ticks
- Win/loss conditions defined in scenario spec (`victory_conditions` array in scenario YAML)
- Checkpoint system: serialize `AuthoritativeState` + RNG state to named checkpoint file; restore from checkpoint on resume
- REST API:
  - `GET /api/v1/scenarios/{id}/status` — live objective state, tick count, alive entity count, key metrics
  - `POST /api/v1/scenarios/{id}/checkpoint` — write checkpoint
  - `POST /api/v1/scenarios/{id}/restore/{checkpoint}` — restore
- Replay mode: run from checkpoint with different seed to explore counterfactuals

**Out of scope:** Multi-scenario campaign orchestration (Epic 3.2). Scenario UI (client layer). Real-time streaming.

**Acceptance signal:** A scenario started via API reaches OBJECTIVE_MET or OBJECTIVE_FAILED, can be paused mid-run and resumed, and a checkpoint/restore cycle produces the same outcomes as an uninterrupted run.

---

### Epic 3.2 · Persistent Campaign Runtime
**Score: 9 · Effort: L · D01 score: 20/25**

**Context:** `CampaignRunner` is explicitly analysis-only — no multi-scenario continuity exists anywhere. Each run is amnesiac. D01 rates this as a Tier-2 gap (20/25). The existing `CampaignRunner` class should be renamed `SimulationAnalysisRunner` before this epic to eliminate the naming collision.

**Goal:** A campaign is a sequence of scenarios where entity state, world state, faction relationships, and narrative history persist across episode boundaries. Consequences compound.

**Scope:**
- `CampaignState` data model: `episode_history[]`, `persistent_entities{}`, `persistent_factions{}`, `world_timeline[]`, `narrative_ledger[]`
- `CampaignOrchestrator`: owns a sequence of `ScenarioSpec` + carries `CampaignState` forward; uses `ScenarioRuntimeService` (Epic 3.1) to run each episode
- Inter-episode state transfer: entity XP/equipment/reputation/injury persists; dead entities remain dead; faction tension/alliance state carries forward
- `NarrativeLedger`: structured record of significant campaign events (quest completions, entity deaths, faction shifts, calamities) by tick + episode; queryable by History Compiler (Phase 5)
- Campaign spec format: YAML defining episode sequence, world transition rules, carry-forward rules, campaign victory conditions
- Campaign checkpoint: serialize full `CampaignState` between episodes; resumable from any episode boundary
- `GET /api/v1/campaigns/{id}/history` — returns `NarrativeLedger` as structured event stream

**Out of scope:** Campaign UI. Player agency / interactive decision points. Cross-campaign storyline (Phase 6). Social memory within episodes (Phase 4 — feeds into this automatically via `NarrativeLedger`).

**Acceptance signal:** A 3-episode campaign where: (a) a HERO entity that reaches level 5 in episode 1 starts episode 2 at level 5; (b) a faction destroyed in episode 1 does not spawn in episode 2; (c) `NarrativeLedger` contains at least 10 cross-episode entries.

**Unlocks:** Social Memory as Campaign Consequence (Epic 4.3). History/Chronicle Compiler (Epic 5.1). Faction History (Epic 5.3). Progression Planner (Epic 6.1).

---

### Epic 3.3 · Macro-Economy Health Metrics
**Score: 7 · Effort: M · Source: roadmap C**

**Context:** Per-transaction conservation laws are solid. Dynamic pricing exists for calamity/survival pressure. No inflation detection, no gold-sink mechanism, no dead-economy signal. The "infinite shop, frozen economy" failure mode is documented but undetected.

**Goal:** The simulation can detect and report on economic health at the macro level and trigger corrective mechanisms when unhealthy patterns are detected.

**Scope:**
- `EconomyHealthMonitor`: runs as a governance phase step; samples gold distribution, transaction volume, price indices per region per tick-window
- Metrics tracked: Gini coefficient (gold inequality), transaction velocity (trades/tick/region), average price index per commodity, gold creation vs. destruction rate
- Alert conditions: `DEFLATION_RISK`, `INFLATION_SPIRAL` (price index growing >X%/100 ticks), `ECONOMIC_COLLAPSE` (region zero-transaction for 200 ticks), `GOLD_HOARDING` (Gini > 0.8)
- Alert events emitted to `simulation_events.jsonl`; health status in `metric_windows.jsonl`
- `GET /api/v1/economy/health` — current health state per region
- Gold sink mechanisms (triggered on INFLATION_SPIRAL): equipment degradation cost, service fees, tax events
- Reputation-based shop discounts (deferred feature from `known_limitations.md`)

**Out of scope:** Faction-level economic control (Epic 5.3). Player economy dashboard. Financial instruments.

**Acceptance signal:** A 2000-tick run produces at least one `ECONOMIC_ALERT` event. Gold sink mechanisms fire and demonstrably reduce gold accumulation rate in the following 200-tick window.

---

## Phase 4 — Social & Cognition Depth

**Goal:** Make entities feel like characters rather than agents. Phase 3 gives the engine continuity; Phase 4 gives entities memory, relationships, and deliberate social behavior. This is the phase that makes emergent stories *about* something.

**Horizon:** 12–16 weeks.

---

### Epic 4.1 · Full Party Adventure Loop
**Score: 8 · Effort: M · Source: roadmap B**

**Context:** Recruit, contract appraisal, grudge/betrayal hooks exist. No sustained multi-tick party lifecycle, class-compatibility scoring, fair reward-split, or escort behavior. Social cohesion currently triggers parties but doesn't sustain them.

**Goal:** Two or more HERO entities can form a party, sustain it across multiple quest objectives, share rewards fairly, and dissolve it due to completion or interpersonal conflict — producing a coherent "adventuring party" narrative arc.

**Scope:**
- `PartyState` durable model: members, formation_tick, shared_inventory, commitment_contracts[], grievance_log[]
- Party formation: requires mutual compatibility score above threshold (class, personality, prior grievance history)
- Sustained leadership: `PartyLeaderElection` each N ticks based on Charisma-equivalent trait; leadership changes produce morale events
- Reward distribution: `FairShareProtocol` computes each member's share based on contribution metrics
- Defection mechanics: high-grievance members may defect mid-quest (`betrayal_desertion` event); carries reputation penalty
- Escort behavior: one member designated `ESCORT_TARGET`; others score protecting-target routes above own survival routes
- Party dissolution: graceful (quest_completed + reward_distributed) or conflict (grievance_threshold_breached)
- Class synergy bonuses: WARRIOR + MAGE scores better on combat routes than two WARRIORs

**Out of scope:** Player-controlled party composition. Multi-party faction wars (Phase 5). Cross-episode party legacy (Campaign Runtime carries this automatically).

**Acceptance signal:** In a 600-tick urban_political run with HERO entities, at least one party forms, completes a quest together, distributes rewards, and either dissolves gracefully or produces a betrayal event. Party history appears in `NarrativeLedger`.

---

### Epic 4.2 · Active Information-Seeking / Belief Economy
**Score: 8 · Effort: M · Source: D01, roadmap B**

**Context:** Passive leads and belief/trust/strategic-blocker system exist. Blockers are material-resource-only; leads are coordinate-only — no person/concept leads. Entities are effectively omniscient-by-passive-injection. No deliberate "ask guide/merchant," no paid information, no contradiction-driven replanning.

**Goal:** Entities actively seek information they know they lack. An entity that needs a rare material can ask a merchant, pay for the lead, receive coordinates, and discover that its current belief was wrong when it arrives to find the node depleted.

**Scope:**
- `InformationNeed` as a first-class belief state: entity recognizes a gap (missing lead for resource X) and generates an `information_seeking` project kind
- `InformationProviders`: MERCHANT, GUILD_MASTER, ELDER archetypes can answer queries about resource locations, faction tensions, entity whereabouts; each has `reliability_score` and `knowledge_age`
- Paid information transactions: entity pays gold/reputation for a lead; provider receives gold/reputation; lead has quality (exact/approximate/rumored)
- Lead contradiction: entity arrives, finds lead wrong (node depleted, entity dead, faction hostile), generates `belief_contradiction` event; provider reputation decreases; revised seeking project starts
- Extend existing lead system to support `PERSON_LEAD` and `CONCEPT_LEAD` types (not just coordinate leads)
- Knowledge staleness decay: leads age, confidence degrades each tick; entity scores information_seeking routes higher as stale leads accumulate

**Out of scope:** Deliberate deception/misinformation propagation (future). Collective rumor networks (Phase 6, culture drift). Player information queries.

**Acceptance signal:** In a 600-tick run, at least one HERO entity transitions through: `information_need_identified → information_seeking_project → information_transaction → lead_received → route_scored_with_lead → belief_contradiction (if lead was stale) → information_seeking_retry`.

---

### Epic 4.3 · Social Memory as Campaign Consequence
**Score: 8 · Effort: M · Source: roadmap B — requires Epic 3.2**

**Context:** Reputation and commitment solid within one run. Nothing persists betrayal/rescue/cooperation history across episodes. Requires `CampaignState.NarrativeLedger` (Epic 3.2) as the storage layer.

**Goal:** An entity's social history shapes its reputation and relationship scores in subsequent episodes. A legendary hero of episode 2 receives deference in episode 4. A known traitor faces hostility.

**Scope:**
- `SocialMemoryRecord` as a durable cross-episode model: entity_id, interaction_history[], reputation_events[], relationship_scores{entity_id: float}
- Cross-episode reputation transfer: at episode end, `SocialMemoryExporter` serializes entity reputation delta into `CampaignState`; at episode start, `SocialMemoryImporter` applies legacy reputation
- Relationship decay: old scores decay toward neutral over episodes; betrayals decay slower than cooperations (grudge half-life > friendship half-life)
- Faction memory: faction reputation tracks separately; a faction that was wronged maintains collective hostility even if key members died
- Social consequence events: `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED`

**Out of scope:** Procedural relationship narrative generation. Player-facing relationship screen. Cross-campaign (beyond one campaign) social memory.

**Acceptance signal:** In a 2-episode campaign, an entity that completes a quest for Faction A in episode 1 receives a faction reputation bonus in episode 2 that measurably increases its starting score with Faction A's affiliated NPCs.

---

## Phase 5 — World-Scale Systems

**Goal:** The simulation starts producing history, not just events. Phases 1–4 make entities rich and worlds dynamic; Phase 5 gives the world memory, demographic structure, and macro-political conflict. Runs feel like they happened in a real place with a real past.

**Horizon:** 14–18 weeks.

---

### Epic 5.1 · History / Chronicle Compiler
**Score: 8 · Effort: L · Source: roadmap A**

**Context:** Zero code; only scattered event logs. No event→episode→milestone→era compression. Required for long-horizon simulation and for making completed runs legible as history. Uses `NarrativeLedger` from Epic 3.2 as input.

**Goal:** A completed campaign produces a structured chronicle: events compressed into episodes, episodes into milestones, milestones into eras. The chronicle is queryable and readable as history.

**Scope:**
- `ChronicleCompiler`: post-run pipeline reading `NarrativeLedger` and `simulation_events.jsonl`; groups events into named episodes by significance threshold
- Event significance scoring: severity + entity_reach + cascade_downstream_count; only events above threshold appear
- Chronicle hierarchy: `Event → Incident (3–10 events) → Episode (5–20 incidents) → Era (campaign phase)`
- Named entities and events: significant NPCs, factions, locations acquire chronicle names ("The Fall of Iron Gate", "The Betrayal of Aldric")
- `Chronicle.md` output: human-readable narrative summary of a completed run, 1–5 pages
- REST:
  - `GET /api/v1/chronicle/{campaign_id}` — structured chronicle JSON
  - `GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary` — narrative text for an era

**Out of scope:** Generated prose narrative (language model integration). Player-facing history book UI. Cross-campaign historical comparison.

**Acceptance signal:** A completed 3-episode campaign produces a `Chronicle.md` that a reader with no prior context can understand as a coherent historical summary in under 5 minutes. At least 3 named milestones appear.

---

### Epic 5.2 · Demographic / Cohort Population Model
**Score: 6 · Effort: M · Source: roadmap A**

**Context:** `SpawnService` and `ResourceEcologyService` are density/spawn-rate driven. No age-structured birth/death/migration cohorts. Current model can't show population aging or generational change. Needed for any long-horizon (century+) simulation.

**Goal:** Regions have population cohorts with age structure, birth/death rates, and migration pressure. A depleted region sees population emigrate; a thriving region sees growth. Generational change happens over long runs.

**Scope:**
- `PopulationCohort` durable model per region: cohorts by age_bracket (young/adult/elder), birth_rate, mortality_rate, migration_threshold
- Birth/death cycle: each N ticks, apply rates; produce spawn events for new young entities when cohort exceeds threshold
- Migration pressure: when regional resource scarcity exceeds threshold (Epic 2.1), migration_pressure rises; cohorts above threshold emigrate to adjacent regions
- Age advancement: entities carry `age_ticks`; at threshold intervals, advance age bracket; elders have higher mortality, lower combat effectiveness, higher knowledge/reputation
- Population density signals: wire cohort density into `RegionalPressureModel` as demand signal
- Population module types from Epic 1.3 (`nomadic_herd`, `settled_quarter`) now have demographic models

**Out of scope:** Genetic trait inheritance. Cultural transmission between generations (Phase 6). Player population management.

**Acceptance signal:** In a 2000-tick run, at least one region's cohort composition changes measurably (emigration from scarcity or immigration from abundance). An elder entity exists that started as young in episode 1.

---

### Epic 5.3 · Faction & Diplomacy System (fresh build)
**Score: 10 · Effort: XL · Source: roadmap A**

**Context:** This is the single largest missing system (XL). Zero engine code exists — `src/content_semantics/faction.py` is catalog data, not behavior. `grand_strategy.md` is cited only to establish scope, not as a design or porting source. Build fresh against V2 architecture (domain ownership, authoritative mutation pipeline, typed durable state).

**Goal:** Factions are active agents in the simulation with territorial ambitions, diplomatic relationships, and the ability to wage war, form alliances, conduct sieges, and negotiate. The macro-political layer is as rich as the individual entity layer.

**Scope — four phases, implement in sequence:**

*Phase A — Faction as Agent:*
- `FactionState` durable model: territory[], resources[], diplomatic_relations{faction_id: TensionLevel}, active_doctrines[], military_strength
- `FactionDecisionPhase`: runs at governance layer; produces faction-level directives (expand territory, seek alliance, respond to threat, commission quests)
- Faction directives propagate to entity scoring: a GUARD entity near a contested border scores patrol routes higher; a MERCHANT near an allied region scores trade routes higher
- Faction awareness: factions observe world events (resource depletion, calamity, entity deaths) and update tension levels accordingly

*Phase B — Diplomacy:*
- Diplomatic actions: treaty offer, trade agreement, non-aggression pact, alliance, betrayal
- Diplomatic states: NEUTRAL, TENSE, HOSTILE, WAR, ALLIED, VASSAL
- Diplomatic events flow through `NarrativeLedger` for Chronicle Compiler
- Alliance logic: allied factions share territory defense; trade agreements reduce mutual tension

*Phase C — Territorial Conflict & War:*
- War declaration triggers `MilitaryConflictPhase`: faction commits entity squads to contested regions
- Siege mechanics: besieging faction depletes target region's service availability over N ticks; defender responds with reinforcement
- Territory transfer: after siege victory, region changes faction ownership; sovereignty entries update
- War exhaustion: military_strength depletes; both sides incentivized to end long wars

*Phase D — History Integration:*
- All faction-level events (wars, treaties, territorial gains) flow to `NarrativeLedger`
- Chronicle Compiler names wars and alliances ("The Thornwood War of Year 3", "The Grand Alliance")

**Out of scope:** Player faction control. Real-time strategy layer. Culture/ideology generation (Phase 6). Cross-campaign faction legacy (can be enabled by Epic 4.3 extension).

**Acceptance signal:** In a 3-episode campaign with at least 3 factions, at least one war is declared, fought over 2+ episodes, and resolved with territory transfer. Chronicle Compiler names the war.

**Unlocks:** Culture/Myth Drift (Phase 6). Cross-faction quest chains. Demographic migration driven by political pressure.

---

## Phase 6 — Long Horizon (18+ Months, Deliberate Scheduling)

Scope and sequencing should be re-evaluated after Phase 5 is complete. These epics are speculative at planning time.

---

### Epic 6.1 · Progression Planner
**Score: 6 · Effort: M · Requires: Epic 3.2**

**Goal:** Entities with multi-episode awareness form build plans — sequences of skill acquisitions, equipment upgrades, class specializations — spanning episodes rather than being tick-local. A HERO that wants to become a legendary swordsmith starts planning in episode 1 for episode 3.

**Scope:** Multi-episode goal queue integrated with `SocialMemoryRecord`. Plan persistence in `CampaignState`. Plan revision when circumstances change (mentor died, item unavailable).

**Acceptance signal:** A HERO entity that identifies a target equipment tier in episode 1 pursues a coherent upgrade chain across 3 episodes, revising the plan when an intermediate goal is blocked.

---

### Epic 6.2 · Culture / Myth Drift
**Score: 6 · Effort: M · Requires: Epics 5.1 + 5.3**

**Goal:** Over long campaigns, regional cultures develop distinct values, taboos, and myths based on their history. A region with a history of calamity develops fatalistic cultural values. A region with a legendary hero develops a hero-cult. Cultural values influence entity behavior through the doctrine system.

**Scope:** `CultureState` per region updated by Chronicle Compiler based on accumulated narrative events. Culture values feed into entity motivation profiles when they enter a region.

**Acceptance signal:** In a 5-episode campaign, two regions with different narrative histories produce measurably different entity behavioral distributions in episode 5.

---

### Epic 6.3 · Pluggable Feature Pack Architecture
**Score: 8 · Effort: XL · Decision gate required**

**Context:** Zero code beyond the vision doc. The adventure-routing and world-emergence domains already use a clean `enum → generator → scorer → mapper → tests` extension pattern — proven twice at small scale.

**Goal:** A feature pack is a self-describing YAML manifest + code module that can be plugged into the engine without modifying core files. New quest types, combat mechanics, entity behaviors, and world events are authored as packs.

**Decision gate:** Do not start this epic until the existing extension points have been used to add at least 3 independent features. The pattern must be proven at small scale before it is generalized.

**Scope:** `FeaturePackManifest`, `RuntimeProfile`, `CompatibilityResolver`, `BalanceExperimentSpec`. Generalize from existing `adventure_routing_contract.md` and `world_emergence_contract.md` patterns.

**Acceptance signal:** A new quest type is added to the engine via a feature pack manifest without modifying any file in `src/engine/` or `src/domains/`.

---

## Dependency Map

```
Phase 0 (all)
  └─► Phase 1 (all three epics can run in parallel)
        ├─► Epic 2.1 (Resource Ecology) — requires Epic 1.3 (content)
        ├─► Epic 2.2 (Decision Explanation) — no content dependency
        └─► Epic 2.3 (Quest Generation) — requires 2.1 + 1.3
              └─► Epic 3.1 (Scenario Runtime)
                    └─► Epic 3.2 (Campaign Runtime)
                          ├─► Epic 3.3 (Macro-Economy)
                          ├─► Epic 4.1 (Party Loop)
                          ├─► Epic 4.2 (Info-Seeking)
                          └─► Epic 4.3 (Social Memory) ──► Epic 5.1 (Chronicle)
                                                              └─► Epic 5.2 (Demographics)
                                                              └─► Epic 5.3 (Faction & Diplomacy)
                                                                    └─► Epic 6.2 (Culture Drift)
                                                                    └─► Epic 6.3 (Feature Packs) [gated]
```

---

## Top 5 Highest-ROI Actions (Score 10, Effort S)

Do these first. Each delivers disproportionate value for minimal effort.

| # | Action | Score | Why |
|---|---|---|---|
| P0-1 | Add `test.yml` CI workflow | 10 | Every merge currently unvalidated; ~30 lines of YAML |
| P0-2 | Fix bare `random.` calls | 10 | P0 engine contract; silent replay divergence |
| P0-3 | Add food resource node | 10 | Unblocks hunger satiation → unlocks entire economic layer |
| P0-4 | Seed `PersonalityComponent` | 10 | ~20 lines in WorldCompiler; unlocks all personality differentiation |
| P0-5 | Fix `authoritative_pipeline.md` | 9 | Most-referenced agent doc currently gives wrong phase insertion points |
