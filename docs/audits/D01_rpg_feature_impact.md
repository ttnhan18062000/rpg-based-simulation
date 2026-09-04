---
status: active
layer: simulation
authority: P1
audience: agent
tags: [audit, rpg-features, simulation-impact, feature-inventory]
---

# D01 — RPG Feature Impact

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | 0 — Feature Inventory |
| **State** | `done` |
| **Impact** | 5 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 10 |
| **Method** | code-read |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Which RPG-level features exist, which are partial, and
which are missing — and how much does each one actually matter to simulation behavior?
Scores are grounded in simulation dynamics, not design ambition.

**Related dimensions:** D03 (Behavioral Emergence Quality) — verifies whether the
`[E]` features actually produce the emergent behavior the scores predict.
D06 (Long-Run Simulation Health) — tests whether missing Tier-1/2 systems cause
the world to stagnate over long runs. D05 (Entity Differentiation) — verifies
personality/OCEAN scoring produces distinct arcs at scale.

---

## Rating Method

Five dimensions, each scored 1–5. Maximum possible: 25.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Trigger Rate** | One-time / rare events | Every 10–50 ticks or event-driven | Every tick, every entity |
| **Entity Reach** | Single entity or small group | Subset — parties, combatants, region | All entities, world-scale |
| **Cascade Width** | Self-contained, no downstream | Feeds 2–3 other systems | Feeds 5+ other systems |
| **Emergence Ceiling** | Binary on/off behavior | Creates local variation | Creates novel macro-patterns per run |
| **Absence Penalty** | Cosmetic gap, sim runs fine | Noticeable quality loss | Simulation invalid or stagnates |

**Composition Multiplier** (not a scored dimension): some features unlock or amplify
multiple other features when enabled. Noted separately where it applies.

**Status labels:** `[E]` Existing — implemented and verified in current src.
`[P]` Partial — partially implemented, gaps confirmed. `[M]` Missing — zero or near-zero code.

---

## Simulation Pipeline Context

The kernel executes this tick order for every simulation step:

```
Init → Scheduling (governance/eligibility) → Collection (domain decisions) →
Resolution (authoritative application) → Cleanup → Advancement → Persistence
```

The domain decision pipeline, which runs inside Collection, is approximately:

```
Perception (filter signals)
  → Memory (causal attribution, spatial, temporal urgency)
    → Motivation (drive urgency, doctrine bias)
      → Cognition / Self-Model (capability estimate, risk, knowledge routing)
        → Adventure Decision (route generation, scoring, selection)
          → Combat / Economy / Cooperation / Progression / World Emergence (execute)
```

Systems early in this chain have higher leverage because everything downstream is
conditioned on their output. Systems late in the chain feed signals back into early
systems on the next tick, creating feedback loops. The most dangerous simulation
failure mode is a **broken feedback loop** — the pipeline looks locally correct but
produces a dead world because upstream signals never vary.

---

## Tier 1 — Engine Foundations (Score 21–25)

Simulation breaks, stagnates, or produces meaningless output without these.

---

### Adventure Decision System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 5 | Every tick, every alive entity |
| Entity Reach | 5 | All entities |
| Cascade Width | 5 | Feeds combat, economy, cooperation, movement, quest execution |
| Emergence Ceiling | 4 | Personality-biased route diversity; risk/benefit/confidence variation creates behavioral divergence |
| Absence Penalty | 5 | Entities cannot act — simulation dies |
| **Total** | **24 / 25** | |

**Key dynamic:** The route selection decision is the central behavioral output of every
entity every tick. All downstream action (combat engagement, harvesting, trading, party
formation, quest execution) is a consequence of which route was selected here. Changes
to scoring weights, personality bias, or knowledge-gating produce the most visible
behavioral shifts in the simulation.

**Composition multiplier:** Any system that contributes a route score, a risk signal,
a confidence modifier, or a rejected-route reason increases the behavioral richness of
this system's output directly.

---

### Motivation & Goal System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 5 | Every tick, every entity |
| Entity Reach | 5 | All entities |
| Cascade Width | 5 | Drives adventure decision, combat posture, cooperation threshold, commitment abandonment |
| Emergence Ceiling | 4 | Competing urgencies create pressure waves — survival crowds out ambition, fear crowds out cooperation |
| Absence Penalty | 5 | Entities become aimless; route scoring has no urgency signal to optimize |
| **Total** | **24 / 25** | |

**Key dynamic:** Motivation urgency is the primary weight on route scoring. An entity
with high hunger urgency routes toward food. An entity with high threat urgency routes
toward safety. The interplay between competing drives — especially when multiple drives
hit high urgency simultaneously — produces the most interesting behavioral moments in the
simulation. Without this, all routes look equally attractive and behavior flattens.

---

### Cognition / Knowledge / Self-Model `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Updated on events and periodic belief staleness checks — not pure per-tick |
| Entity Reach | 5 | All entities maintain subjective knowledge state |
| Cascade Width | 5 | Feeds adventure decisions (confidence, risk estimate), cooperation (trust), combat posture, info-seeking |
| Emergence Ceiling | 5 | Imperfect information creates subjective divergence — two entities in the same region make different decisions because they know different things |
| Absence Penalty | 4 | Simulation runs but entities become effectively omniscient; decision divergence collapses |
| **Total** | **23 / 25** | |

**Key dynamic:** This is what makes agents *subjective* rather than omniscient. An entity
that doesn't know a mine exists can't route to it. An entity that overestimates its
combat capability charges enemies it should flee. Knowledge asymmetry between entities in
the same region produces emergent coordination and conflict patterns that cannot be
scripted. Currently partially limited: blockers are material-resource-only, leads are
coordinate-only — concepts/persons/rumors not yet modeled (see Active Info-Seeking).

---

### Resource Ecology Regeneration `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Periodic regional tick (not every entity tick, but world-scale regular) |
| Entity Reach | 4 | Indirectly affects all resource-seeking entities via supply availability |
| Cascade Width | 5 | Feeds: economy pressure, quest demand, entity migration, faction territorial conflict, world evolution trauma |
| Emergence Ceiling | 5 | Scarcity cycles → boom/bust → migration → territorial conflict → faction war → historical events; each run produces a different pressure history |
| Absence Penalty | 5 | Without it: economy never stresses, quests have no organic demand, world pressure is static, faction conflict has nothing to fight over, long-run simulation produces a flat dead world |
| **Total** | **22 / 25** | |

**Status (updated 2026-06-22):** Basic per-tick regeneration implemented by E21B
(`ResourceNodeRegenerationService` in `src/domains/economy/`), with seasonal multipliers
and scarcity tracking. This removes the fully-static node limitation. Remaining gaps:
density-dependent regeneration rates, complex multi-stage ecological cycles, and
long-run pressure gradients across linked regions are not yet modeled.

**Key dynamic:** Resource regeneration is the **heartbeat of the simulation world**.
Without it, the economy satisfies all demand trivially — there is no scarcity to drive
migration, no depletion to generate quests, no territorial pressure to trigger faction
conflict. The entire emergent chain from individual needs → regional economics → macro
politics depends on resource nodes that can actually run out and recover at varying rates.

**Composition multiplier:** Enabling this single system unblocks: Macro-Economy Health
Metrics, Pressure-Driven Quest Generation, Faction territorial conflict, and makes World
Emergence regional signals actually vary between runs.

---

### World Evolution System `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | World-scale events — periodic, slow; calamities are rare |
| Entity Reach | 5 | World-scale signals eventually reach all entities |
| Cascade Width | 5 | Feeds entity motivation (threat), migration pressure, resource availability, quest generation, faction conflict |
| Emergence Ceiling | 4 | Calamity + recovery cycles create distinct historical arcs per run |
| Absence Penalty | 3 | World is static between entity actions; entities react but the world doesn't evolve |
| **Total** | **19 / 25** | |

**Status (updated 2026-06-22):** Regional trauma and sovereignty are solid. Ecology systems
exist (`WorldEmergencePhase` evaluates `RegionalPressureModel`, `ScarcityModel`,
`ServiceStatePressureModel`). Basic resource regeneration added (E21B).
Demographic pressure added (E52A–E52D: `DemographicCycleService`, cohort birth/death/
migration). Remaining gaps: complex regeneration cycles and long-run ecological dynamics
(seasonal multi-region pressure propagation).

---

## Tier 2 — High Leverage (Score 16–20)

These systems qualitatively enrich most runs. Missing one makes the simulation noticeably
shallower but it doesn't stop running.

---

### Economy / Resources / Crafting `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Resource checks happen frequently — harvesting, trade, crafting route execution |
| Entity Reach | 5 | Most entities have resource needs |
| Cascade Width | 4 | Feeds motivation (have/need), adventure decisions (supply routes), progression (sell/craft), cooperation (party resource pooling) |
| Emergence Ceiling | 3 | Conservation laws correct, but no macro dynamics — currently no scarcity means no real pressure (dependent on Resource Ecology) |
| Absence Penalty | 4 | Entities cannot sustain themselves |
| **Total** | **20 / 25** | |

**Note:** Current emergence ceiling is 3 because static nodes prevent real economic
pressure. With Resource Ecology Regeneration, this ceiling rises to 4–5.

---

### Persistent Campaign Runtime `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Between episodes, not per-tick |
| Entity Reach | 5 | All entities carry cross-episode memory and consequence |
| Cascade Width | 5 | Feeds: social memory, faction history, progression planning, narrative legacy, entity motivation across runs |
| Emergence Ceiling | 5 | Consequences compound across episodes — a betrayed ally becomes a nemesis; a collapsed city leaves a ruin; a legendary fighter's death echoes forward |
| Absence Penalty | 4 | Each run is isolated and amnesiac; no compound history; real RPG continuity impossible |
| **Total** | **20 / 25** | |

**Status (updated 2026-06-22):** Implemented across E43A–E43E and E41B–E41D.
`CampaignState` (`src/domains/campaigns/state.py`) holds `narrative_ledger`,
`social_memories`, `faction_social_memories`, and `region_cultures`.
`CampaignOrchestrator._advance_state()` (`src/domains/campaigns/orchestrator.py`)
runs at every episode boundary, wiring entity carry-forward, social memory
decay/import, and narrative ledger harvesting. `CampaignRunner` remains an
analysis-only harness (separate from the runtime).

---

### Faction & Diplomacy System `[E]`

> **RESOLVED (2026-06-23):** TCK-20260619-E53-FACTION-DIPLOMACY — all 16 child tickets (E53Aa–E53Dd) fully implemented; `docs/systems/faction_contract.md` is authoritative.

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Low per-tick frequency; high-consequence periodic decisions (alliance proposals, war declarations, treaty breaks) |
| Entity Reach | 5 | Regional / world-scale — affects all entity choices through territorial pressure, affiliation, and war zones |
| Cascade Width | 5 | Feeds: quest generation, entity migration, combat motivation, economy disruption, world evolution, history chronicles |
| Emergence Ceiling | 5 | Highest ceiling in the engine — kingdom rise/fall, shifting alliances, conquest and collapse create world histories that are qualitatively unique per run |
| Absence Penalty | 3 | Simulation runs cleanly but is purely individual-scale; no macro-RPG structure above the regional level |
| **Total** | **20 / 25** | |

**Status (as of 2026-06-23 — IMPLEMENTED):** FactionState model, FactionDecisionPhase, DiplomaticStateMachine (5 transitions), MilitaryConflictPhase, SiegeState, territory transfer via authoritative pipeline, NarrativeLedger wiring for diplomatic/war events, and ChronicleCompiler faction integration are all implemented and tested. `docs/systems/faction_contract.md` is the authoritative reference. `docs/archive/grand_strategy_v1.md` archived.

---

### Scenario Runtime Service `[E]`

> **RESOLVED: TCK-20260619-E31-SCENARIO-RUNTIME (2026-06-20):** ScenarioRuntimeService implemented with objective FSM, pause/resume/checkpoint, and REST API.

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Objective evaluation runs frequently; active scenario state shapes signals every tick |
| Entity Reach | 5 | Objective context reaches all entities through quest signals and world state |
| Cascade Width | 4 | Defines success/failure/stall context that shapes motivation, quest, adventure decision, and world evolution |
| Emergence Ceiling | 2 | Framework — it organizes emergence but doesn't itself create new behavioral patterns |
| Absence Penalty | 4 | Can only run open-ended lab experiments; no bounded scenario with objectives, outcomes, or resumable state |
| **Total** | **19 / 25** | |

**Status (updated 2026-06-20):** Implemented by TCK-20260619-E31-SCENARIO-RUNTIME. `ScenarioRuntimeService` provides objective FSM, pause/resume/checkpoint, and REST API. Checkpoint infrastructure in `src/engine/checkpoint.py` extended beyond determinism hashing to support full scenario save/resume.

---

### Spatial / Movement System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Most ticks, most entities are in motion |
| Entity Reach | 5 | All entities need navigation |
| Cascade Width | 3 | Feeds adventure decisions (route feasibility), combat range, resource node access |
| Emergence Ceiling | 2 | Enables geography-sensitive behavior but limited intrinsic emergence |
| Absence Penalty | 4 | Entities cannot navigate — fundamental prerequisite |
| **Total** | **18 / 25** | |

---

### Information / Belief System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Event-driven updates; periodic stale checks |
| Entity Reach | 4 | All entities hold belief state, but updates are sparse |
| Cascade Width | 4 | Feeds adventure decisions (confidence, risk estimate), cooperation (who to trust), motivation (known vs unknown threats) |
| Emergence Ceiling | 4 | Belief divergence makes two entities in the same region make opposite decisions; rumor propagation creates cascading misinformation |
| Absence Penalty | 3 | Entities become effectively omniscient; decision variance collapses but sim runs |
| **Total** | **18 / 25** | |

**Status (updated 2026-06-22):** E42A–E42E closed all confirmed gaps. Blockers now
include non-material types (`UnknownFact` + `InformationNeedDetector`); leads include
`LeadKind.PERSON` and `LeadKind.CONCEPT`; `PaidInformationTransactionSystem` implements
the gold-cost info economy; `LeadContradictionSystem` handles contradiction-driven
replanning. `InformationProviderArchetype` (MERCHANT, GUILD_MASTER, ELDER) models
town NPCs as differentiated sources.

---

### Perception / Attention System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 5 | Every tick, every entity |
| Entity Reach | 5 | All entities filter signals |
| Cascade Width | 3 | Determines what downstream systems (motivation, cognition, adventure) even see |
| Emergence Ceiling | 2 | Salience budget creates prioritization but limited intrinsic emergence |
| Absence Penalty | 3 | Entities flood on all signals simultaneously — behavior quality and performance both degrade |
| **Total** | **18 / 25** | |

---

### Memory System (Causal / Spatial / Temporal) `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Updated every tick alongside memory domain |
| Entity Reach | 5 | All entities |
| Cascade Width | 3 | Feeds adventure decisions, cooperation scoring, motivation urgency via temporal deadlines |
| Emergence Ceiling | 3 | Causal attribution affects future decisions; spatial memory avoids wasted re-exploration |
| Absence Penalty | 3 | Entities forget everything — repeat failures, no improvement, but sim runs |
| **Total** | **18 / 25** | |

---

### Social / Cooperation / Reputation System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Periodic + event-driven (help-need evaluation, betrayal detection, reputation updates) |
| Entity Reach | 4 | Entities in proximity or with prior relationship history |
| Cascade Width | 4 | Feeds adventure decisions (party vs solo), combat posture, progression (shared loot), commitment |
| Emergence Ceiling | 4 | Trust networks, betrayal chains, party dynamics, reputation propagation create social fabric |
| Absence Penalty | 3 | Entities become isolated agents; social RPG fabric disappears |
| **Total** | **18 / 25** | |

---

### Active Information-Seeking / Belief Economy `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Deliberate actions: asking guide, paying for rumor, contradicting bad intel |
| Entity Reach | 4 | Info-seeking entities + town NPCs as information sources |
| Cascade Width | 4 | Feeds adventure decisions, belief updates, cooperation (share intel), economy (paid info cost) |
| Emergence Ceiling | 4 | Info markets; rumor propagation; knowledge asymmetry between entities diverges decisions at scale |
| Absence Penalty | 3 | Entities are currently passive about information — they receive it but never seek it; subjective cognition is real but shallow |
| **Total** | **18 / 25** | |

**Status (updated 2026-06-22):** Implemented by E42A–E42E. `InformationNeedDetector`
generates seeking projects; `PaidInformationTransactionSystem` charges gold per
`LeadCertainty` tier; `LeadContradictionSystem` tracks contradicting leads and decays
certainty; `LeadKind` enum (LOCATION, OBJECT, EVENT, PERSON, CONCEPT) covers all lead
types; `LeadRoutingSystem` resolves the best provider per `InformationProviderArchetype`.
All prior confirmed gaps are closed.

---

### Emotion / Mood System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Event-driven updates, but events are frequent enough to keep mood active |
| Entity Reach | 5 | All entities |
| Cascade Width | 3 | Feeds adventure decision bias, cooperation threshold, habit bias |
| Emergence Ceiling | 3 | Mood creates short-term behavioral deviation from baseline personality |
| Absence Penalty | 2 | Entities feel mechanical; mood variation is lost but decisions still work |
| **Total** | **17 / 25** | |

---

### Narrative Consequence Layer `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Milestone events only (death, betrayal, rescue, conquest) |
| Entity Reach | 4 | Entities and regions involved in the milestone event |
| Cascade Width | 4 | Feeds motivation (grief, rage, legacy drive), social (nemesis formation), faction (aftermath), world evolution (regional scar) |
| Emergence Ceiling | 5 | Converts raw simulation events into named RPG moments — this is what makes the simulation feel like a story |
| Absence Penalty | 2 | Simulation runs correctly; just doesn't feel like an RPG |
| **Total** | **17 / 25** | |

**Status (updated 2026-06-22):** Partially implemented. `SocialMemoryRecord`
(E43A–E43E) carries grudge/friendship marks cross-episode, providing a consequence
through-line for social betrayal and alliance. `BetrayalDesertionEvent` (E41D) emits
the canonical betrayal consequence signal. `ChronicleCompiler` (E51A–E51E) names and
structures narrative events into ledger entries consumed by `CampaignOrchestrator`.
Remaining gap: real-time "grief/rage → motivation urgency" feedback loop and nemesis
formation from chronicle events are not yet modeled.

---

### Social Memory as Campaign Consequence `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Between episodes, loaded at episode start |
| Entity Reach | 4 | Entities with prior cross-episode relationships |
| Cascade Width | 4 | Feeds cooperation (prior betrayal = no party), adventure decisions (avoid nemesis region), reputation, faction affiliation |
| Emergence Ceiling | 5 | Cross-episode grudges, debts, alliances, loyalties create multi-run behavioral through-lines |
| Absence Penalty | 3 | Each episode social state is cold-start; no compound trust history |
| **Total** | **17 / 25** | |

**Status (updated 2026-06-22):** Implemented by E43A–E43E. `SocialMemoryRecord`
(typed, serializable) carries entity-pair trust marks across episodes. `SocialMemoryDecay`
applies half-life erosion. `SocialMemoryExporter` / `SocialMemoryImporter` are wired
into `CampaignOrchestrator._advance_state()`. `FactionSocialMemory` extends the
pattern to faction-pair relationships. The original blocker (Persistent Campaign Runtime)
was resolved by the same epic.

---

### Macro-Economy Health Metrics `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Monitoring, periodic sampling |
| Entity Reach | 5 | World-scale health signal |
| Cascade Width | 3 | Feeds balancing signals, world health status, quest demand calibration |
| Emergence Ceiling | 2 | Measurement and detection, not generative of emergence |
| Absence Penalty | 4 | Economy can silently die — "infinite shop" and "gold inflation" failure modes are invisible without this |
| **Total** | **16 / 25** | |

**Status (updated 2026-06-26):** Implemented. `GoldSinkSystem` (`src/engine/gold_sink.py`) tracks Gini index and gold drain; `economy_health_monitor` events in `src/observability/events.py`; REST endpoint `GET /economy/health` in `src/api/routes/economy.py`.

---

### Pressure-Driven Quest Generation `[E]`

> **RESOLVED (2026-06-20):** TCK-20260619-E23-QUEST-GENERATION — all 4 child tickets (E23A–E23D) fully implemented: `QuestOpportunityGenerator.from_resource_depleted()` / `from_threat_signal()` in `src/domains/world_emergence/services.py`; `quest_registry` in `AuthoritativeState`; reward distribution in `pipeline_phases/quest_opportunity_rewards.py`; `QUEST_OPPORTUNITY` RouteFamily wired in `AdventureRouteScorer`.

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Triggered by world pressure signals from WorldEmergence |
| Entity Reach | 4 | Quest availability broadcasts to entities in affected region |
| Cascade Width | 4 | Feeds motivation (quest urgency), adventure decisions (quest routes), cooperation (group quests), progression (quest rewards) |
| Emergence Ceiling | 4 | Quests generated from actual world state create a feedback loop — entity behavior responds to real pressure, not static templates |
| Absence Penalty | 3 | Current quests are 5 hardcoded `QuestKind` enum values with static templates; world pressure creates no new quest demand |
| **Total** | **16 / 25** | |

**Implementation:** `QuestOpportunityGenerator` produces typed `QuestOpportunity` records from
`RESOURCE_DEPLETED` and threat-signal world events. The generator is wired into
`WorldEmergencePhase` step 5b. `QuestOpportunityStatus` lifecycle and `quest_registry`
in `AuthoritativeState` handle offer/accept/expire/complete transitions. Reward delivery
uses the authoritative `ResourceTransferIntent` path with `WorldEvent` emission.

---

### Combat System `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | When entities engage; not every tick for every entity |
| Entity Reach | 3 | Combatants and immediately affected entities |
| Cascade Width | 4 | Feeds progression (XP, loot), reputation (grudges, public labels), economy (equipment damage, loot pool), world emergence (deaths change regional density) |
| Emergence Ceiling | 3 | Tactical variation is rich; long-run ecology is thin without combat ecology extension |
| Absence Penalty | 4 | Core RPG system — cannot fight means major gameplay gap |
| **Total** | **17 / 25** | |

---

## Tier 3 — Meaningful Depth (Score 11–15)

These add important dimensions. The simulation is viable without them but shallower.

---

### Progression / Rewards `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Low frequency — level-up, reward conversion after combat or quest |
| Entity Reach | 2 | Per-entity events, one at a time |
| Cascade Width | 3 | Feeds motivation (growth drive), adventure decisions (training routes), combat capability (equipment delta) |
| Emergence Ceiling | 3 | Character growth creates diverging capability curves over time; specialization paths emerge from reward choices |
| Absence Penalty | 3 | Entities don't grow; simulation stagnates on long runs |
| **Total** | **13 / 25** | |

**Gap confirmed:** Progression is tick-local only. No multi-episode skill/equipment/build
goals (see Progression Planner below).

---

### Commitment / Reputation Labels `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Event-driven, low frequency |
| Entity Reach | 3 | Entity + affected relationship partners |
| Cascade Width | 3 | Feeds adventure decisions (social-route viability), cooperation (reputation gate), social standing |
| Emergence Ceiling | 3 | Reputation propagation affects future opportunities — a coward label closes cooperation doors |
| Absence Penalty | 2 | Social fabric thinner; abandonment has no consequence |
| **Total** | **13 / 25** | |

---

### History / Chronicle Compiler `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Background compression — not a per-tick behavior engine |
| Entity Reach | 5 | Compresses all entity and world events |
| Cascade Width | 2 | Output consumed by narrative reports; could feed culture drift and myth formation eventually |
| Emergence Ceiling | 3 | Creates narrative structure from emergent events but does not itself generate new behavior |
| Absence Penalty | 2 | Simulation runs fine; long runs produce unreadable raw event logs; thousand-year simulation is uninterpretable without this |
| **Total** | **13 / 25** | |

**Status (updated 2026-06-22):** Implemented by E51A–E51E. `EventSignificanceScorer`
scores raw events (threshold 0.5 for chronicle inclusion); `ChronicleGrouper` bins events
into incidents/episodes/eras; `ChronicleNamer` generates RPG-flavored names from templates
(`naming.py`); `ChronicleRenderer` formats for API output; `ChronicleCompiler` orchestrates
the pipeline. `NarrativeLedger` in `CampaignState` persists the output across episodes.
REST endpoint at `GET /chronicle/{world_id}` exposes the full chronicle.

---

### Full Party Adventure Loop `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Party lifecycle events: formation, cohesion checks, reward splits, dissolution |
| Entity Reach | 3 | Party members (typically 2–6 entities) |
| Cascade Width | 3 | Feeds adventure decisions (party routes differ from solo), combat coordination, cooperation, social trust |
| Emergence Ceiling | 4 | Sustained parties develop shared history → party dynamics → long-form adventure arcs that solo entities cannot produce |
| Absence Penalty | 2 | Parties form but don't sustain; social RPG depth is limited |
| **Total** | **15 / 25** | |

**Status (updated 2026-06-22):** Partially complete. E41B added `PartyLifecycleService`
with leadership election (`LeadershipChangedEvent`). E41C added `FairShareProtocol` and
`build_reward_transfer_intents` for equitable loot distribution. E41D added
`check_defection`, `PROTECT_TARGET` and `OWN_SURVIVAL` `RouteFamily` entries, and
`BetrayalDesertionEvent` for escort + defection scenarios. Remaining gap: class-compatibility
scoring (party composition optimization) is not yet implemented.

---

### Decision Explanation Model `[E]`

> **RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN (2026-06-20):** Decision trace promoted to first-class durable object; REST API at /api/v1/observability/cognition/{entity_id}/tick/{n} implemented; tick index and LIGHT-mode capture added.

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 5 | Trace is generated every tick with every route decision — just not stored durably |
| Entity Reach | 5 | All entities |
| Cascade Width | 1 | Observability only — does not feed back into simulation behavior |
| Emergence Ceiling | 1 | Captures emergence; does not create it |
| Absence Penalty | 3 | Behavior is a black box for developers; debugging requires log archaeology |
| **Total** | **15 / 25** | |

**Note:** High development leverage despite low simulation-behavior score. Route trace is
already computed every tick — this is promotion of existing data to a queryable API,
not new logic.

---

### Personality → Long-Run Behavior Calibration `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | N/A | Calibration concern, not a runtime system |
| Entity Reach | 5 | All entities have OCEAN traits |
| Cascade Width | 2 | If calibrated correctly, personality weights adjust adventure decision scoring → all behavior |
| Emergence Ceiling | 4 | Correctly calibrated personality creates diverging life arcs |
| Absence Penalty | 3 | Personality works in unit tests but may collapse into similar behavior at scale without calibration |
| **Total** | **14 / 25** | |

**Confirmed:** OCEAN traits, mood, grudges all implemented locally. No metric proves
they compound into distinct long-run life arcs vs. one-off route nudges.

---

### Demographic / Cohort Population Model `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Very slow — generational timescale |
| Entity Reach | 5 | All population |
| Cascade Width | 3 | Feeds economy labor supply, faction power balance, world evolution pressure |
| Emergence Ceiling | 4 | Population cycles, generational knowledge loss, baby boom after war, demographic collapse |
| Absence Penalty | 1 | Only matters in 100+ year simulations |
| **Total** | **14 / 25** | |

**Status (updated 2026-06-22):** Implemented by E52A–E52D. `PopulationCohort` typed
dataclass (age_band, count, mortality_rate, birth_rate, migration_pressure); cadence-gated
`DemographicCycleService` in world_dynamics tick pipeline; `PopulationMigrationService`
moves cohorts across regions; age-band advancement advances cohorts each cycle. Density
signal (`DensitySignal`) feeds into `RegionalPressureModel`. `CohortModel` carries forward
in `CampaignState` via E52B migration artifacts.

---

### Progression Planner `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Long-term planning — updated when build goals change, not per-tick |
| Entity Reach | 4 | All progressing entities |
| Cascade Width | 3 | Feeds adventure decisions (routes toward build goal), progression conversion (defer vs use reward), motivation |
| Emergence Ceiling | 3 | Entities pursue specialization paths → differentiated capability curves |
| Absence Penalty | 2 | Progression is tick-local; no long-term character trajectory |
| **Total** | **13 / 25** | |

**Status (updated 2026-06-26):** Implemented. `ProgressionPlan`, `BuildGoal`, `MilestoneCheck`, `RevisionTrigger` frozen dataclasses in `src/domains/campaigns/progression_plan.py` with `ProgressionPlanExporter` / `ProgressionPlanImporter` for cross-episode persistence.

---

### Combat Ecology Extension `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Only triggered when recurring antagonist relationship exists |
| Entity Reach | 2 | Specific entity pairs or small groups |
| Cascade Width | 3 | Feeds adventure decisions (avoid nemesis zone), cooperation (warn others), reputation, motivation |
| Emergence Ceiling | 4 | Nemesis relationships create narrative through-lines |
| Absence Penalty | 2 | Combat works; this adds RPG depth |
| **Total** | **13 / 25** | |

**Note:** Roadmap recommendation is to verify current grudge depth before building.

---

## Tier 4 — Specialty / Tooling (Score 6–10)

---

### Behavior Scorecard `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Post-run analysis |
| Entity Reach | 5 | Analyzes all entities |
| Cascade Width | 1 | Analysis only |
| Emergence Ceiling | 1 | Measures emergence; does not create it |
| Absence Penalty | 2 | Lose quality gate; behavior quality undetectable by automated means |
| **Total** | **10 / 25** | |

---

### Long-Horizon Regression Suite `[P]`

> **Ticket:** TCK-20260627-P3A-DEFERRED-EPICS

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | CI / periodic |
| Entity Reach | 5 | Tests entire population |
| Cascade Width | 1 | Tooling |
| Emergence Ceiling | 1 | Measures behavior stability |
| Absence Penalty | 2 | Behavioral regressions go undetected across refactors |
| **Total** | **10 / 25** | |

---

### Capability / Support Registry `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Registry query at startup / tooling |
| Entity Reach | 1 | Tooling only |
| Cascade Width | 2 | Prerequisite for Feature Pack Architecture |
| Emergence Ceiling | 1 | Infrastructure |
| Absence Penalty | 2 | Feature status is ambiguous; pluggable-pack work cannot safely start |
| **Total** | **7 / 25** | |

**Status (updated 2026-06-26):** Implemented. `CapabilityRegistry` in `src/engine/capability.py` with `is_supported()`, `get_status()`, `all_capabilities()`, `capabilities_by_status()`.

---

### Pluggable Feature Pack Architecture `[E]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Load-time / configuration |
| Entity Reach | 5 | If built, would shape all entity-facing RPG systems |
| Cascade Width | 5 | Meta-architecture — enables swapping species/combat/economy/time-scale models |
| Emergence Ceiling | 1 | Enables emergence from swappable systems but is not itself emergent |
| Absence Penalty | 1 | Zero code; nothing depends on it yet |
| **Total** | **13 / 25** | |

**Status (updated 2026-06-26):** Implemented. `FeatureRegistry` (generic, enum-backed) in `src/domains/feature_packs/registry.py` with `register()`, `lookup()`, `list_all()`. Full feature pack system present: `balance_spec.py`, `profile.py`, `manifest.py`, `loader.py`. Anchor prerequisites (Persistent Campaign Runtime, Scenario Runtime, Capability Registry) all now `[E]`.

---

## Infrastructure Tier

Not RPG features — scored separately. Listed for completeness.

| System | Status | Notes |
|---|---|---|
| Simulation Kernel (tick loop, phases, determinism) | `[E]` | `infrastructure.yaml` 100% verified |
| Authoritative Mutation Pipeline | `[E]` | Mature; single-mutation-point law enforced |
| Observability (events, WebSocket, anomalies) | `[E]` | Strong coverage |
| Replay & Determinism | `[E]` | Canonical state hashing in `src/engine/checkpoint.py` |
| Granular Phase Permissions (INFRA-155/156) | `[E]` | Implemented in `src/engine/phase_domain_permissions.py` — full `PHASE_READ_DOMAINS`/`PHASE_WRITE_DOMAINS` tables (updated 2026-06-26) |
| Unified Read Model Service | `[E]` | Implemented in `src/api/presenters/` — 6 dedicated presenter files (updated 2026-06-26) |
| Performance / Resource Budgeting | `[E]` | Budget tests pass; hardware class contracts verified |

---

## Master Summary Table

| Rank | Feature | Status | Score | Tier |
|---|---|---|---|---|
| 1 | Adventure Decision System | `[E]` | 24 | Foundation |
| 2 | Motivation & Goal System | `[E]` | 24 | Foundation |
| 3 | Cognition / Knowledge / Self-Model | `[E]` | 23 | Foundation |
| **4** | **Resource Ecology Regeneration** | **`[P]`** | **22** | **Foundation (partial)** |
| 5 | World Evolution System | `[P]` | 19 | Foundation/High |
| 6 | Economy / Resources / Crafting | `[E]` | 20 | High |
| 7 | Persistent Campaign Runtime | `[E]` | 20 | High |
| 8 | Faction & Diplomacy System | `[E]` | 20 | High |
| 9 | Scenario Runtime Service | `[E]` | 19 | High |
| 10 | Spatial / Movement System | `[E]` | 18 | High |
| 11 | Information / Belief System | `[E]` | 18 | High |
| 12 | Perception / Attention System | `[E]` | 18 | High |
| 13 | Memory System | `[E]` | 18 | High |
| 14 | Social / Cooperation / Reputation | `[E]` | 18 | High |
| 15 | Active Information-Seeking | `[E]` | 18 | High |
| 16 | Combat System | `[E]` | 17 | High |
| 17 | Emotion / Mood System | `[E]` | 17 | High |
| 18 | Narrative Consequence Layer | `[P]` | 17 | High (partial) |
| 19 | Social Memory as Campaign Consequence | `[E]` | 17 | High |
| 20 | Macro-Economy Health Metrics | `[E]` | 16 | High |
| 21 | Pressure-Driven Quest Generation | `[E]` | 16 | High |
| 22 | Full Party Adventure Loop | `[P]` | 15 | Depth |
| 23 | Decision Explanation Model | `[E]` | 15 | Depth (tooling) |
| 24 | Personality Long-Run Calibration | `[P]` | 14 | Depth |
| 25 | Demographic / Cohort Population Model | `[E]` | 14 | Depth |
| 26 | Progression / Rewards | `[E]` | 13 | Depth |
| 27 | Commitment / Reputation Labels | `[E]` | 13 | Depth |
| 28 | History / Chronicle Compiler | `[E]` | 13 | Depth |
| 29 | Combat Ecology Extension | `[P]` | 13 | Depth |
| 30 | Progression Planner | `[E]` | 13 | Depth |
| 31 | Behavior Scorecard | `[E]` | 10 | Tooling |
| 32 | Long-Horizon Regression Suite | `[P]` | 10 | Tooling |
| 33 | Capability / Support Registry | `[E]` | 7 | Infra prerequisite |
| 34 | Pluggable Feature Pack Architecture | `[E]` | 13 | Architecture |

---

## Key Findings

### Finding 1: Resource Ecology Regeneration is now partial — complex cycles remain
Previously the only missing Tier-1 system (score 22/25). E21B implemented basic per-tick
regeneration with seasonal multipliers, resolving the fully-static node limitation.
Remaining gap: density-dependent rates, multi-stage ecological cycles, and cross-region
pressure propagation. Economy pressure is now possible but long-run ecological dynamics
are still thin.

### Finding 2: No missing Tier-1 or Tier-2 systems remain (updated 2026-06-27)
Both previously-missing Tier-2 systems are now DONE: Faction & Diplomacy (E53Aa–E53Dd, 2026-06-23) and Pressure-Driven Quest Generation (E23A–E23D, 2026-06-20). Scenario Runtime Service, Persistent Campaign Runtime, Social Memory, Chronicle Compiler, Demographic Model, Progression Planner, Capability Registry, and Feature Pack Architecture are all DONE. The remaining gaps are all `[P]` (partial) systems: Resource Ecology Regeneration, World Evolution, Narrative Consequence Layer, Full Party Adventure Loop, Personality Long-Run Calibration, and Combat Ecology Extension.

### Finding 3: Cascade unlocks — all core Tier-2 systems are now implemented (updated 2026-06-27)
Resource Ecology Regeneration (partial) still limits the depth of ecological feedback cycles. Macro-Economy Health Metrics is DONE (GoldSinkSystem + REST endpoint). Faction & Diplomacy (E53A–D) is DONE, unlocking faction-flavoured quest generation, combat motivation, and history chronicle faction events. Pressure-Driven Quest Generation (E23A–D) is DONE — `QuestOpportunityGenerator` produces quests from `RESOURCE_DEPLETED` and threat-signal world events, completing the world-state → quest → entity behavior feedback loop. The remaining cascade gaps are in the `[P]` partial systems.

### Finding 4: Active Info-Seeking gap is closed; remaining depth gaps are in ecology and narrative
Economy/Resources (score 20) still has emergence ceiling 3 because complex ecological
cycles aren't modeled yet. Information/Belief (score 18) gap is now closed — Active
Info-Seeking (E42A–E) is fully implemented. Faction & Diplomacy (E53A–D) and
Pressure-Driven Quest Generation (E23A–D) are both fully implemented (2026-06-23 / 2026-06-20).
No `[M]` items remain across all 34 assessed systems.

### Finding 5: CampaignRunner / CampaignOrchestrator split is now established
`CampaignRunner` remains the analysis harness (`src/domains/campaigns/runner.py`);
`CampaignOrchestrator` is the authoritative persistent runtime
(`src/domains/campaigns/orchestrator.py`). The naming risk flagged here is resolved —
the two classes serve distinct roles in the same package.

---

## Recommended Follow-Up Tickets

| Priority | Action | Reason |
|---|---|---|
| Immediate | P0 parity hotfixes (`COMB-006`, `COMB-133/134`, `STRAT-164/177`, `SOC-134`) | Pre-existing debt; independent of all epics |
| Immediate | Refresh `known_limitations.md` | Stale since 2026-04-21; misleads investigation agents |
| ~~Immediate~~ | ~~Rename `CampaignRunner` → `AnalysisCampaignRunner`~~ | **RESOLVED** — `CampaignOrchestrator` is now the persistent runtime; `CampaignRunner` retains the analysis role. Both names are now unambiguous. |
| Epic 1 | Resource Ecology Regeneration — complete complex cycles (M) | Basic regen done (E21B); density-dependent cycles + cross-region propagation still missing |
| ~~Epic 2~~ | ~~Faction & Diplomacy System (XL)~~ | **IMPLEMENTED** — TCK-20260619-E53-FACTION-DIPLOMACY + all 16 child tickets (E53Aa–E53Dd) completed 2026-06-23; see `docs/systems/faction_contract.md` |
| ~~Epic 3~~ | ~~Scenario Runtime Service (M)~~ | **IMPLEMENTED** — TCK-20260619-E31-SCENARIO-RUNTIME (2026-06-20) |
| ~~Epic 4~~ | ~~Pressure-Driven Quest Generation (M)~~ | **IMPLEMENTED** — TCK-20260619-E23-QUEST-GENERATION + all 4 child tickets (E23A–E23D) completed 2026-06-20; `QuestOpportunityGenerator` wired in `WorldEmergencePhase` |
| Done | Persistent Campaign Runtime | **IMPLEMENTED** — E43A–E43E + E41B–E41D |
| Done | Social Memory as Campaign Consequence | **IMPLEMENTED** — E43A–E43E |
| Done | History / Chronicle Compiler | **IMPLEMENTED** — E51A–E51E |
| Done | Demographic / Cohort Population Model | **IMPLEMENTED** — E52A–E52D |
| Done | Active Information-Seeking / Belief Economy | **IMPLEMENTED** — E42A–E42E |
| Done | Progression Planner | **IMPLEMENTED** — `src/domains/campaigns/progression_plan.py` (updated 2026-06-26) |
| Done | Macro-Economy Health Metrics | **IMPLEMENTED** — `GoldSinkSystem` + `GET /economy/health` (updated 2026-06-26) |
| Done | Capability / Support Registry | **IMPLEMENTED** — `src/engine/capability.py` (updated 2026-06-26) |
| Done | Pluggable Feature Pack Architecture | **IMPLEMENTED** — `src/domains/feature_packs/` (updated 2026-06-26) |
| Scoped | Culture / Myth Drift | E62A–D in `tickets/todos/E62-CULTURE-DRIFT/` |

---

## Related Dimensions

- **D03 (Behavioral Emergence Quality)** — verifies whether `[E]` features produce
  the emergent behavior their scores predict; directly validates the Tier 1 and Tier 2 ratings here
- **D05 (Entity Differentiation)** — verifies personality/OCEAN scoring produces
  observably distinct long-run arcs at scale; tests the emergence ceiling claims
- **D06 (Long-Run Simulation Health)** — tests whether missing Tier-1/2 systems
  (Resource Ecology, Campaign Runtime) cause the world to stagnate past 1000 ticks
- **D09 (System Wiring)** — confirmed all `[E]` features here are live-wired;
  also revealed 20+ domain-phase systems absent from D01's feature inventory
- **D10 (Test Coverage)** — `[P]` features scored highest on Absence Penalty
  are the regression-risk targets
