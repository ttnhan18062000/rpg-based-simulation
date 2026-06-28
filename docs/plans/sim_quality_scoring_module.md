---
status: active
layer: simulation
authority: P1
audience: agent
tags: [simulation-quality, scoring, pillars, major-feature, architecture, design]
---

# Simulation Quality Scoring Module — Feature Design

**Ticket:** TCK-20260628-SIMQ-INVESTIGATION  
**Status:** Investigation complete. Implementation pending.  
**Related:** `docs/audits/D19_domain_phase_inventory.md`, `docs/audits/D01_rpg_feature_impact.md`,
`docs/engine/contracts/rpg_refinement_pillars.md`

---

## 1. Purpose

The engine can run a simulation and produce output, but today there is no automated way
to answer: *how good is this run?* Specifically:

- Is any subsystem producing degenerate output (zero harvesting, no quest activity, instant extinction)?
- Is the simulation in an infinite behavioral loop — the same small set of goals cycling endlessly?
- Is combat balanced across different world configurations?
- Are factions actually interacting, or are they all isolated?
- Which part of the simulation caused a bad run — was it cognition, ecology, progression, or narrative?

The audit dimensions (D01–D19) answer these questions manually, after one or more runs.
The `RunBehaviorScorecard` and `CampaignScorecard` answer a subset post-run, from
behavioral episode aggregates. The `hard_law_monitor` answers the correctness question,
not the quality question.

**This module answers the quality question automatically, per run, per subsystem, in
real time.**

---

## 2. What This Module Is Not

| System | What it does | Why this module doesn't overlap |
|---|---|---|
| `RunBehaviorScorecard` | Post-run behavioral diversity from episode aggregates | Episode-level, behavioral patterns only, not per-subsystem |
| `CampaignScorecard` | Semantic pass/fail verdict from arc types | Binary verdict, post-run, semantic only |
| `AnalyzerQualityReporter` | Analyzer rule accuracy (false positive rates) | About the analyzer, not the simulation |
| `hard_law_monitor` | Correctness: contract invariant violations | Correctness ≠ quality; a simulation can pass all laws and still score F on Economy |
| Audit dimensions D01–D19 | Manual static analysis, one-time findings | Human-authored, not automated per-run |

This module scores **simulation health** — whether systems are alive, balanced, and
producing emergent output. It does not score correctness, performance, or content.

---

## 3. Architectural Position

```
┌──────────────────────────────────────────────────────────────┐
│                     Simulation Loop                          │
│   Kernel → pipeline.py:refine() (PP-01…PP-37)               │
│           → world_dynamics.py:resolve_dynamics() (WD-01…15)  │
└───────────────────────────┬──────────────────────────────────┘
                            │ authoritative state transitions
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   Observability Layer                        │
│  EventBus (SimulationEvent) → BoundedObservabilityQueue      │
│  → simulation_events.jsonl  → replay chunks  → telemetry bridge  │
└───────────────────────────┬──────────────────────────────────┘
                            │ ObservabilityEventEnvelope stream
                            ▼ (subscriber, non-blocking)
┌──────────────────────────────────────────────────────────────┐
│             Simulation Quality Layer  [NEW]                  │
│                                                              │
│   QualityHub                                                 │
│   ├── Pillar scorers (10 × PillarScorer)                     │
│   ├── PillarAccumulators (running totals + window state)     │
│   ├── ScoreRecord writer → quality_scores.jsonl              │
│   └── QualityReport builder → quality_report.json           │
│                                                              │
│   Read-only query API (for future engine feedback)           │
│   GET /api/v1/quality/pillars                                │
│   GET /api/v1/quality/pillars/{id}/worst_events              │
│   GET /api/v1/quality/alerts                                 │
└───────────────────────────┬──────────────────────────────────┘
                            │ read-only quality signals (future)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              Analysis / Post-Run Layer                       │
│  RunBehaviorScorecard, CampaignScorecard, audit tooling      │
└──────────────────────────────────────────────────────────────┘
```

**Coupling rule:** The quality layer never imports from `src/engine/`, `src/domains/`, or
`src/systems/` directly. It subscribes to `ObservabilityEventEnvelope` — the same
boundary that the rest of the observability layer uses. Domain internals are invisible.

**Engine feedback rule:** The engine may query the quality layer through a read-only
interface, but must apply any consequences through the authoritative pipeline — never by
having a scorer write to simulation state.

---

## 4. Score Model

### 4.1 Score Records

Every meaningful event produces at most one `ScoreRecord`:

```python
@dataclass(frozen=True)
class ScoreRecord:
    tick: int
    event_id: str          # links back to the ObservabilityEventEnvelope
    pillar: PillarId
    delta: float           # positive = good, negative = bad
    reason: str            # human-readable, for traceability
    event_type: str        # original event_type for drill-down
    entity_id: int | None
    region_id: str | None
    tags: tuple[str, ...]  # e.g. ("stagnation", "loop_detected", "zero_harvest")
```

Score records are written to `data/runs/{run_id}/quality_scores.jsonl` using the same
directory pattern as replay chunks and events.

### 4.2 Pillar Accumulation

Each pillar maintains:
- `raw_score: float` — cumulative sum of all deltas
- `event_count: int` — number of scored events
- `negative_event_count: int` — number of events with negative delta
- `worst_events: list[ScoreRecord]` — top-N by abs(delta), negative only
- `window_buffer: deque[ScoreRecord]` — sliding window (last W ticks) for loop detection

### 4.3 Normalized Score

Pillar comparisons across run lengths use the normalized score:

```
normalized_score = raw_score / max(1, tick_count)
```

This makes a 100-tick run and a 1000-tick run comparable. The normalized score is what
drives health grades.

### 4.4 Health Grades

Each pillar receives a health grade at report time:

| Grade | Normalized Score | Meaning |
|---|---|---|
| **S** | > +2.0 | Exceptional — subsystem producing rich, diverse output above baseline |
| **A** | +0.5 to +2.0 | Healthy — subsystem functioning well |
| **B** | 0.0 to +0.5 | Adequate — subsystem active but limited |
| **C** | -0.5 to 0.0 | Concerning — subsystem underperforming; investigate |
| **D** | -1.0 to -0.5 | Degraded — subsystem producing significant bad signals |
| **F** | < -1.0 | Degenerate — subsystem is broken or absent in this run |

Initial thresholds are calibrated estimates. They will be tuned after the first batch of
baseline runs. Threshold values are constants in `pillars.py`, not hardcoded inline.

### 4.5 Overall Quality Score

```
overall_score = weighted_average(pillar_normalized_scores, pillar_weights)
```

Default weights are equal across all 10 pillars. Weights are configurable per scenario
profile (e.g., a combat-focused world can weight Combat higher).

### 4.6 Loop and Stagnation Detection

Each pillar accumulator maintains a sliding window of the last `W` ticks (default W=100).
If the same event_type appears in more than `L%` of window records with negative or zero
delta (default L=70%), a `LOOP_DETECTED` tag is appended to subsequent score records.

Loop detection is not a score penalty in itself — it is a diagnostic tag that causes the
pillar to emit a high-visibility alert in the quality report.

---

## 5. The 10 Pillars

Each pillar covers a distinct simulation subsystem. The table maps every pillar to its
source pipeline phases (from D19) and its D01 RPG feature tier anchors.

---

### Pillar 1 — Cognition

**Question answered:** Are entities genuinely reasoning from subjective knowledge, or
are they effectively omniscient robots with flat decision distributions?

**Pipeline phases:** PP-03 (self_model), PP-04 (information_belief), PP-30 (strategic_intelligence)

**D01 anchors:** Cognition / Knowledge / Self-Model (23/25), Motivation & Goal System (24/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Belief updated from event (entity changes known state) | +2 | Knowledge asymmetry is working |
| Entity makes different decision than same-region peer (divergence event) | +5 | Subjective divergence confirmed |
| Lead certainty increased (knowledge got sharper) | +1 | Information quality improving |
| Lead certainty decayed to zero without replacement | −3 | Knowledge rotting; entity becoming blind |
| Entity makes decision with zero knowledge (default fallback path) | −2 | Cognition not feeding adventure routing |
| Strategic intelligence re-scoring fires and changes goal | +3 | Re-evaluation working |
| Same goal re-selected for Nth consecutive tick (no re-scoring fired) | −2 per N>5 | Goal lock without cognition update |

**Loop/stagnation signal:** Same lead re-evaluated with decreasing certainty every tick
without any entity action to refresh it.

**Traceability:** A low Cognition score → find worst_events tagged `knowledge_decay` or
`zero_knowledge_decision` → look up event_id in simulation_events.jsonl → identify which entity and
which tick → cross-reference with cognition_graph_snapshots.jsonl.

---

### Pillar 2 — Agency & Action

**Question answered:** Are entities taking purposeful, varied actions — or cycling
through the same DEFER loop indefinitely?

**Pipeline phases:** PP-12 (adventure_decision), PP-13 (action_routing), PP-14 (position_swaps),
PP-15 (movement_routing), PP-30 (strategic_intelligence)

**D01 anchors:** Adventure Decision System (24/25), Motivation & Goal System (24/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Entity executes a meaningful action (not DEFER) | +1 | Entity is participating in the simulation |
| Entity executes a NEW route family (not seen in last W ticks) | +3 | Behavioral variety confirmed |
| Entity successfully moves toward a goal location | +1 | Navigation working |
| Entity receives DEFER_WITH_REASON (idle tick) | −1 | One idle tick is fine; patterns are not |
| Entity receives DEFER for Nth consecutive tick (N>5) | −3 per additional tick | Stasis detected |
| Rejection cascade: >100 rejections in one tick (population-level) | −5 | Pipeline overloaded with futile re-evaluations |
| Entity abandons and immediately restarts the same project | −2 | Goal cycling — commitment instability |
| Entity completes a commitment and transitions to next goal | +4 | Decision continuity working |
| Route family distribution entropy (H) per 100-tick window | +H×2 | More variety = higher score |

**Loop/stagnation signal:** Rolling rejection cascade rate >500/tick for more than 50
consecutive ticks. Tagged `rejection_cascade_sustained`.

**Traceability:** Low Agency score → find `rejection_cascade_sustained` or `stasis_n`
tags → entity_id + tick range → look up `adventure_decision` events for that entity →
trace which route opportunities were rejected and why.

---

### Pillar 3 — Combat

**Question answered:** Is combat balanced — engaging without causing instant extinction,
occurring at a rate appropriate to the world, and producing meaningful tactical variety?

**Pipeline phases:** PP-16 (combat_engagement), PP-31 (near_death_hardening), PP-33 (lifecycle),
PP-11 (military_conflict — faction-level)

**D01 anchors:** Combat System (17/25), Spatial / Movement (18/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Combat engagement initiated | +2 | World is dangerous enough to produce conflict |
| Combat resolved (winner determined, loser retreats or dies) | +3 | Resolution pipeline working |
| Near-death hardening fires and entity survives | +2 | Survival tension working |
| Entity dies in combat (attrition event) | −1 | Each death is a net loss to the world |
| First death occurs before tick 10 | −10 | Too fast; world is lethally unbalanced |
| Attrition exceeds 50% of population by tick 100 | −20 | Extinction spiral |
| Attrition exceeds 90% of population by tick 200 | −50 | Degenerate world — combat is the only system |
| Zero combat events in a world that has hostile faction or spawn config | −15 | Combat pipeline inactive |
| Combat resolution without a winner (infinite loop outcome) | −8 | Resolution pipeline broken |
| Tactical modifier diversity: each combat uses different active modifiers | +1 per unique modifier used | Tactical richness |
| Hard law violation in combat pipeline | −30 | Correctness and quality both fail |

**Loop/stagnation signal:** Combat events without any lifecycle events (combat_damage
emitted but no entity death or retreat ever fires) for >50 consecutive combat events.

**Traceability:** Low Combat score → `extinction_spiral` or `zero_combat_active_world`
tags → world config + tick range → cross-reference attrition_rate with entity lifecycle
events → check spawn config in world.yaml for expected combat pressure.

---

### Pillar 4 — Faction & Military

**Question answered:** Are factions interacting — diplomatically and militarily — in a
balanced, dynamic way? Is any faction dominating without resistance?

**Pipeline phases:** PP-08 (faction_decision direct-call), PP-09 (faction_awareness),
PP-10 (diplomatic_transitions), PP-11 (military_conflict), PP-23 (world_emergence)

**D01 anchors:** Faction & Diplomacy System (20/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Diplomatic state transition fires (neutral→hostile, hostile→war, etc.) | +5 | Diplomacy is alive |
| Alliance proposal generated (common-enemy pair detected) | +4 | Coalition dynamics working |
| Alliance accepted | +6 | Diplomatic cooperation confirmed |
| Military conflict resolved (faction battle outcome) | +3 | Military pipeline working |
| Territory ownership transition (conquest or liberation) | +6 | Macro-political change occurring |
| Resource seizure event (faction acquires contested resource) | +2 | Economic-military coupling working |
| Faction tension delta > threshold (tension escalating or de-escalating) | +2 | Awareness pipeline active |
| Zero diplomatic transitions in a world with 2+ factions over 200 ticks | −20 | Factions exist but never interact |
| Single faction controls >80% of territory by tick 500 | −15 | Monopoly — no balance |
| Single faction controls 100% of territory | −40 | Degenerate — world is conquered |
| War declared but no military conflict events follow | −10 | Military pipeline broken |
| Faction declared dead (all members dead) within 50 ticks | −8 | Faction extinction too fast |
| All factions remain at NEUTRAL for entire run | −25 | Diplomatic machine is idle |

**Loop/stagnation signal:** Faction tension oscillates repeatedly between the same two
values without ever crossing a transition threshold — tagged `tension_oscillation_loop`.

**Traceability:** Low Faction score → `all_factions_neutral` or `monopoly_control` →
look up faction state at tick range → cross-reference diplomatic_transitions log for
missing transitions → check faction_decision events for why directives stayed passive.

---

### Pillar 5 — Economy

**Question answered:** Is the resource loop alive — entities harvesting, crafting,
trading, accumulating and spending gold? Is the conservation law holding? Is resource
ecology creating actual scarcity and recovery cycles?

**Pipeline phases:** PP-07 (blacksmith), PP-24 (quest_rewards), PP-25 (shop),
PP-26 (paid_information), PP-27 (resource_transactions), PP-21 (gold_sink),
PP-20 (town_resolution), WD-05 (node cooldown), WD-10 (resource ecology)

**D01 anchors:** Economy / Resources / Crafting (20/25), Resource Ecology Regeneration (22/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Resource harvested (entity gains items from node) | +3 | Core loop step 1 working |
| Item crafted (blacksmith/entity produces output) | +4 | Core loop step 2 working |
| Trade / buy / sell event | +3 | Core loop step 3 working |
| Gold changes hands (non-zero net gold delta on any entity) | +1 | Economy has monetary flow |
| Quest reward dispensed (XP + item) | +3 | Economy and narrative coupling |
| Resource node depleted (charges → 0) | +1 | Scarcity is real (good signal) |
| Resource node regenerated after depletion | +2 | Ecology cycle complete |
| Conservation law verification passes (transfer balanced) | +1 per tick | Law is holding |
| Gold sink fires on inflation pressure | +2 | Anti-inflation mechanism working |
| Paid information transaction | +2 | Knowledge economy active |
| Zero harvesting events after tick 100 | −20 | Resource loop not running |
| Zero crafting events after tick 200 | −15 | Production loop silent |
| Zero trade events after tick 300 | −15 | Commerce loop dead |
| All resource nodes permanently depleted (zero regeneration after depletion) | −25 | Ecology broken |
| Conservation law violation | −50 | Hard correctness failure — also triggers hard_law_monitor |
| Gold accumulation without any spending (per entity, flat gold > 500 ticks) | −5 | Inflation risk building |
| Zero gold flow across entire population for 100 ticks | −10 | Monetary system paralyzed |

**Loop/stagnation signal:** Same resource node repeatedly depleted and not regenerating
over more than 3 ecology cadence intervals — tagged `ecology_regeneration_failure`.

**Traceability:** Low Economy score → `zero_harvesting` or `ecology_regeneration_failure`
→ identify affected regions and nodes → check world.yaml resource node config and
ecology cadence → verify `ENABLE_ADVENTURE_ROUTING` flag and entity region_id assignment.

---

### Pillar 6 — Progression

**Question answered:** Are entities growing — gaining XP, leveling up, unlocking skills,
expressing traits, and evolving their playstyle over time? Or are they locked at level 1
for the entire run?

**Pipeline phases:** PP-24 (quest_rewards), PP-28 (evolution), PP-29 (progression_conversion),
PP-31 (near_death_hardening), PP-33 (lifecycle)

**D01 anchors:** Character Progression / Advancement (19/25), Combat System (17/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| XP granted to entity (any source: quest, combat, crafting) | +1 per 10 XP | Growth signal |
| Level-up event fires | +8 | Milestone achieved |
| Skill unlocked | +5 | Character becoming more specialized |
| Trait expressed (personality trait actively modified a decision) | +2 | Genetic determinism working |
| Pillar trait unlocked (level 50/75/100 milestone) | +15 | Exceptional progression milestone |
| Progression conversion fires and produces permanent update | +4 | Soft-skill evolution working |
| Near-death survival (hardening fires) | +3 | Survival experience creates character |
| Entity at max level produces level-up event | −1 | Capped entity; not a failure but no growth |
| Entity alive for 200+ ticks with zero XP gain | −10 | Progression frozen |
| Entity reaches level 5+ with zero skill unlocks | −5 | Skill system not engaging |
| All entities still at level 1 after tick 300 | −30 | Progression system is silent |
| XP gain rate drops to zero after initial burst (post-tick 50 plateau) | −8 | Feedback loop broken |
| Trait expression rate = 0 for entire run | −10 | Personality is not affecting behavior |

**Loop/stagnation signal:** Entity XP delta = 0 for 100 consecutive ticks while entity
is alive and active. Tagged `progression_plateau`.

**Traceability:** Low Progression score → `all_level_1_tick_300` or `progression_plateau`
→ entity IDs + tick range → check quest_rewards events for zero XP grants → verify
evolution thresholds and XP accumulation in entity state snapshots.

---

### Pillar 7 — Social

**Question answered:** Are entities building social structures — cooperating, forming
groups, honoring and breaking contracts, shifting reputation, creating the social fabric
that makes RPG worlds feel alive?

**Pipeline phases:** PP-05 (cooperation), PP-34 (groups), PP-35 (active_contracts),
PP-36 (expired_offers), PP-18 (interaction_enforcement — trade/talk)

**D01 anchors:** Social Contracts / Reputation (16/25), Cooperation System (15/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Cooperation event (joint task formed, help offer accepted) | +4 | Social fabric forming |
| Group join event | +2 | Party / faction membership growing |
| Contract milestone completed | +3 | Social commitments honored |
| Contract completed (all milestones done) | +6 | Full social contract lifecycle |
| Reputation delta > 0.5 on any entity (meaningful shift) | +2 | Reputation system active |
| Social memory created (entity remembers significant interaction) | +2 | Relationship depth forming |
| Group expulsion event | +1 | Enforcement working (good — groups have standards) |
| Contract offer accepted | +2 | Negotiation working |
| Contract expired without acceptance (dangling offer) | −1 | Offer made with no uptake |
| Contract lapsed (missed milestone, obligor failed) | −3 | Social commitment broken |
| Zero cooperation events in world with multiple entity classes after tick 100 | −15 | Cooperation system dormant |
| Zero group membership changes in 300 ticks | −8 | Social structure static |
| All entities with reputation = 0 at tick 200 | −10 | Reputation not accumulating |
| Reputation perfectly flat for entire run | −12 | Reputation system producing no signal |
| Entity with zero social interactions for entire run (isolated) | −2 per entity | Social isolation |

**Loop/stagnation signal:** Contract offers emitted but never accepted and then
immediately expiring — tagged `contract_offer_dead_loop`.

**Traceability:** Low Social score → `cooperation_dormant` or `reputation_flat` →
check cooperation phase flag (`ENABLE_SOCIAL_COOPERATION`) → verify entity proximity
and compatibility conditions → check contract offer/acceptance timeline.

---

### Pillar 8 — Information & Belief

**Question answered:** Are entities using imperfect information to make divergent
decisions? Is the knowledge economy (paid information, lead tracking, belief propagation)
producing subjective differences in behavior — or are all entities effectively omniscient?

**Pipeline phases:** PP-04 (information_belief), PP-26 (paid_information), PP-30 (strategic_intelligence)

**D01 anchors:** Information / Belief System (18/25), Cognition / Knowledge / Self-Model (23/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Belief update assimilated (entity changes internal state based on new info) | +2 | Belief system active |
| Lead certainty increased from information event | +2 | Intelligence quality improving |
| Entity pays for information (paid transaction) | +3 | Knowledge economy functioning |
| Paid information changes entity's goal within next 5 ticks | +5 | Information has behavioral impact |
| Lead contradiction resolved (entity replanned from conflicting intel) | +4 | Information creates decision complexity |
| Two entities in same region diverge on route choice due to belief difference | +6 | Subjective divergence confirmed |
| Lead certainty decay to zero on an active lead (knowledge rotted) | −2 | Knowledge rotting without refresh |
| Information response received but not assimilated (belief unchanged) | −1 | Belief pipeline not consuming events |
| Zero paid information transactions in a world with `InformationProviderArchetype` NPCs after tick 200 | −10 | Knowledge economy dormant |
| Zero belief updates population-wide for 100 ticks | −15 | Belief system not receiving events |
| All entities sharing identical lead certainty distributions at tick 200 | −20 | No subjective divergence — omniscience collapse |
| Entity buys same information repeatedly (loop — no memory of prior purchase) | −5 | Social memory not preventing waste |

**Loop/stagnation signal:** Entity purchases the same lead tip more than 3 times across
100 ticks with no certainty improvement — tagged `paid_info_memory_failure`.

**Traceability:** Low Information & Belief score → `omniscience_collapse` or
`knowledge_economy_dormant` → check `ENABLE_BELIEF_ASSIMILATION` flag → verify
InformationProviderArchetype NPCs are present in world → check entity belief state
snapshots for stale lead certainty.

---

### Pillar 9 — World Dynamics

**Question answered:** Is the world itself alive — ecology regenerating, calamities
striking, boss entities spawning, regions transforming, demographics shifting? Or is
the world a static backdrop that entities move through without consequence?

**Pipeline phases:** PP-20 (town_resolution), PP-22 (world_dynamics dispatch),
WD-01 (hazard drain), WD-02 (trauma), WD-03 (ownership/calamity), WD-04 (transformation),
WD-05 (node cooldown), WD-06 (chest cooldown), WD-07 (corpse decay),
WD-08 (calamity), WD-09 (spawn), WD-10 (resource ecology), WD-11 (threat evolution),
WD-12 (boss spawn), WD-13 (raid), WD-14 (camp), WD-15 (demographics)

**D01 anchors:** Resource Ecology Regeneration (22/25), World Evolution System (19/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Calamity spawned | +8 | Major world event — high-impact dynamics |
| Boss entity spawned | +6 | Threat escalation working |
| Raid party spawned | +4 | Regional threat producing response |
| Region transformation fires (PLAINS → CORRUPTED, etc.) | +6 | World evolution producing visible change |
| Regional trauma escalating (trauma_delta > 0 from combat deaths) | +2 | World-entity interaction feedback |
| Region ownership transition | +5 | World politics shifted |
| Resource ecology cycle complete (depleted → regenerated) | +3 | Ecology working |
| Monster spawn cadence fires and populates region | +2 | World repopulating |
| Demographic birth event (new cohort member) | +2 | Population dynamics active |
| Demographic mortality event (cohort member dies of age/pressure) | +1 | Natural lifecycle working |
| Camp constructed | +1 | Persistent world structure forming |
| Hazard drain damages entity (hazardous region is dangerous) | +1 | Hazard system working |
| Zero calamity events in a run of 500+ ticks | −8 | Calamity conditions never triggered |
| Zero spawn cadence fires (no monster repopulation) | −10 | World depopulating without recovery |
| Zero region transformations in run of 1000+ ticks | −6 | World is static — no evolution |
| All resource nodes permanently depleted with zero ecology fires | −20 | Ecology system broken |
| Regional trauma monotonically increasing with no hazard-level effect | −5 | Trauma→hazard feedback broken |
| Zero demographic events in a world with demographic config | −8 | Demographics system dormant |
| Boss spawn cadence never fires despite threat threshold exceeded | −6 | Boss spawn pipeline blocked |
| World trauma everywhere = 0 despite significant combat activity | −8 | Trauma accumulation broken |

**Loop/stagnation signal:** Trauma accumulates to the threshold but never produces a
hazard_level increment — repeatedly — tagged `trauma_hazard_feedback_broken`.

**Traceability:** Low World Dynamics score → `ecology_broken` or `world_static` →
check world.yaml cadence settings for ecology/spawn/calamity → verify hazard_level
thresholds → cross-reference WD-08/09/10 firing logs.

---

### Pillar 10 — Narrative

**Question answered:** Is there a story happening? Are quests starting and completing,
chronicle entries accumulating, world events giving each run a unique history, and
scenario objectives progressing toward resolution?

**Pipeline phases:** PP-08 (faction_decision → narrative triggers), PP-23 (world_emergence),
PP-24 (quest_rewards), PP-33 (lifecycle — death is a narrative event)

**D01 anchors:** Narrative Consequence Layer (10/25 — partial), Persistent Campaign Runtime (20/25),
Faction & Diplomacy System (20/25)

**What to score:**

| Signal | Delta | Rationale |
|---|---|---|
| Quest started (entity accepts objective) | +5 | Narrative mission active |
| Quest completed | +10 | Full story arc resolved |
| Quest failed (entity unable to complete, timed out) | −2 | Failure is narrative, but too many failures degrades story |
| Chronicle entry created (NarrativeLedger receives milestone) | +4 | World history forming |
| World emergence event fires (threshold-triggered narrative trigger) | +6 | Emergent story happening |
| Narrative milestone: first faction war declaration | +8 | World-history event |
| Narrative milestone: first boss kill | +8 | Heroic achievement recorded |
| Narrative milestone: first region sovereignty transfer | +6 | Political history |
| Scenario objective progressed | +4 | Story framework advancing |
| Scenario objective completed | +15 | Scenario resolved |
| Scenario stalled (no progress for N ticks) | −10 | Story framework blocked |
| Zero quest starts after tick 200 (world has quest config) | −20 | Quest system dormant |
| Zero chronicle entries after tick 300 | −15 | World producing no history |
| Zero world emergence events in 500 ticks | −10 | Emergence thresholds never crossed |
| Same quest repeatedly failed without any entity ever completing it | −6 | Quest is unsolvable in current world |
| Entity death with no chronicle entry (heroes dying without record) | −1 per hero death | Significant event unrecorded |

**Loop/stagnation signal:** Quest started, then failed, then re-started by same entity,
then failed again — more than 3 cycles on same quest — tagged `quest_retry_loop`.

**Traceability:** Low Narrative score → `quest_system_dormant` or `quest_retry_loop` →
check quest definitions in world.yaml (D07 found only 4 quest definitions total) →
verify quest reward pipeline PP-24 is receiving completed objectives → check world
module quest coverage.

---

## 6. Pillar Coverage Matrix

Each row is a usage scenario. Each column is a pillar. An ● means that pillar is the
primary scorer for this scenario; a ◎ means secondary relevance.

| Usage Scenario | Cog | Agency | Combat | Faction | Economy | Progress | Social | Info | World | Narrative |
|---|---|---|---|---|---|---|---|---|---|---|
| Simulation in infinite loop | ◎ | ● | | | | | | | | |
| Entities all doing same thing | ● | ◎ | | | | | | | | |
| Combat is balanced | | | ● | ◎ | | | | | ◎ | |
| Entity class dominates in combat | | | ● | | | ◎ | | | | |
| Faction politically dominant | | | | ● | | | | | | |
| Factions isolated, no interaction | | | | ● | | | ◎ | | | |
| Economic loop alive | | | | | ● | | | | ◎ | |
| Resource ecology in balance | | | | | ● | | | | ● | |
| Gold inflation building | | | | | ● | | | | | |
| Entities growing / leveling up | | | | | | ● | | | | |
| Progression plateauing | | ◎ | | | | ● | | | | |
| Entities cooperating | | ◎ | | | | | ● | | | |
| Contracts completing | | | | | | | ● | | | |
| Reputation shifting | | | | | | | ● | | | |
| Information asymmetry working | ◎ | | | | | | | ● | | |
| Knowledge economy active | | | | | ◎ | | | ● | | |
| World alive (calamities, spawns) | | | | | | | | | ● | |
| Ecology regenerating | | | | | ◎ | | | | ● | |
| Quests completing | | ◎ | | | | | | | | ● |
| World producing history | | | | ◎ | | | | | ◎ | ● |
| Entities as distinct archetypes | ● | | | | | ◎ | | | | |
| Scenario progressing | | ◎ | | | | | | | | ● |

---

## 7. Module Structure

```
src/simulation_quality/
├── __init__.py
├── pillars.py              # PillarId enum, pillar metadata, grade thresholds, weights
├── score_record.py         # ScoreRecord dataclass (frozen, typed)
├── pillar_accumulator.py   # PillarAccumulator — thread-safe running totals + window
├── quality_hub.py          # QualityHub — subscriber, router, accumulator orchestrator
├── quality_report.py       # QualityReport builder — pillar summaries, grades, worst events
├── persistence.py          # quality_scores.jsonl writer (same pattern as replay chunks)
├── scorers/
│   ├── base.py             # PillarScorer abstract base: score(event, context) -> ScoreRecord | None
│   ├── cognition.py        # CognitionScorer
│   ├── agency.py           # AgencyScorer
│   ├── combat.py           # CombatScorer
│   ├── faction.py          # FactionScorer
│   ├── economy.py          # EconomyScorer
│   ├── progression.py      # ProgressionScorer
│   ├── social.py           # SocialScorer
│   ├── information.py      # InformationBeliefScorer
│   ├── world_dynamics.py   # WorldDynamicsScorer
│   └── narrative.py        # NarrativeScorer
└── api/
    └── routes.py           # REST endpoints for live and post-run quality reports
```

**Not inside `src/observability/`** — the quality layer consumes from observability but
is architecturally distinct (meta-evaluation, not event recording).

**Not inside `src/domains/`** — cross-domain by design; no domain affiliation.

---

## 8. Data Flow

```
1. Simulation emits SimulationEvent via EventBus (existing)
2. ObservabilityEventEnvelope written to BoundedObservabilityQueue (existing)
3. QualityHub.on_event(envelope) called from queue drain callback (new subscriber)
4. QualityHub routes to matching PillarScorer(s) based on event_type + event_category
5. PillarScorer.score(envelope, context) → ScoreRecord | None
6. QualityHub feeds ScoreRecord to PillarAccumulator for the matched pillar
7. PillarAccumulator updates raw_score, window_buffer, worst_events
8. Persistence writes ScoreRecord to quality_scores.jsonl (async, non-blocking)
9. On demand (API call or run end): QualityReport.build() reads all accumulators → report
```

**Error handling:** Steps 4–8 are wrapped in try/except. Any scorer exception is caught,
logged as WARNING, and discarded. The simulation is never aware of the failure.

**Thread safety:** `PillarAccumulator` uses a lock for `raw_score` updates. `worst_events`
list is replaced atomically. The window buffer is a `deque` with `maxlen=W`.

---

## 9. Traceability Path

The "troubleshoot a bad pillar" workflow:

```
1. QualityReport.pillars["economy"].grade == "F"
     ↓
2. QualityReport.pillars["economy"].worst_events[:5]
   → ScoreRecord(tick=200, event_id="abc123", delta=-20.0, tags=["zero_harvest"])
     ↓
3. Cross-reference event_id "abc123" in data/runs/{run_id}/simulation_events.jsonl
   → Full SimulationEvent with entity_id, region_id, tick context
     ↓
4. Cross-reference entity_id at tick 200 in cognition_graph_snapshots.jsonl
   → Why was this entity not pursuing a harvest route?
     ↓
5. Check world.yaml resource_nodes for the entity's region
   → Confirm node exists, has charges, entity region_id is assigned
```

This path requires no new infrastructure beyond `quality_scores.jsonl`.
All cross-reference targets already exist: `simulation_events.jsonl`, `cognition_graph_snapshots.jsonl`,
`world.yaml`.

---

## 10. API Surface

### Live query (during run)

```
GET /api/v1/quality/pillars
→ { pillar_id: string, raw_score: float, normalized_score: float, grade: string,
    event_count: int, tick_count: int }[]

GET /api/v1/quality/pillars/{pillar_id}
→ full pillar state + top-5 worst events

GET /api/v1/quality/alerts
→ all pillars currently graded D or F, with tags and worst event summaries

GET /api/v1/quality/report
→ full QualityReport: overall score, all pillar grades, loop detection flags
```

### Post-run artifact

```
data/runs/{run_id}/quality_scores.jsonl   — all ScoreRecord entries
data/runs/{run_id}/quality_report.json    — final QualityReport snapshot
```

---

## 11. Future Engine Feedback Path

This module is designed so that quality signals can be consumed by the engine without
violating the architecture contract. The path is:

```
QualityHub.get_pillar_score(PillarId.AGENCY) → float    [read-only]
QualityHub.get_pillar_grade(PillarId.COGNITION) → Grade  [read-only]
```

Engine systems that want to use quality signals (e.g., "low Agency score → increase
entity motivation urgency cap") must:

1. Read the signal from `QualityHub` in the Decision phase (read-only, no mutation)
2. Emit a typed `MindUpdate` or `MotivationUpdate` through the authoritative pipeline
3. The pipeline applies the change to live state

This preserves `architecture_reference.md §1.1`: decision-making is read-only, state
mutation is authoritative. Quality signals are inputs to decisions, not direct mutations.

**What is specifically NOT done:**
- Scorers do not write to any domain state
- `QualityHub` does not call any pipeline phase
- Grade thresholds do not modify feature flags or world config

---

## 12. Non-Goals for MVP

- Score constant calibration (initial values are estimates; calibration follows first
  baseline run batch)
- Per-entity quality profiles (pillar scores are run-level, not per-entity in MVP)
- Historical run comparison (cross-run scoring requires baseline storage — future)
- Real-time alert pushing to clients (REST polling is sufficient for MVP)
- ML-based anomaly detection (deterministic rules only in MVP)

---

## 13. Implementation Sequencing (for child ticket)

| Phase | Deliverable | Prerequisite |
|---|---|---|
| 1 | `pillars.py`, `score_record.py` — typed model only | None |
| 2 | `pillar_accumulator.py` — accumulator + window logic | Phase 1 |
| 3 | `scorers/base.py` + `scorers/agency.py` + `scorers/combat.py` (highest signal value) | Phase 2 |
| 4 | Remaining 8 scorers | Phase 3 |
| 5 | `quality_hub.py` — subscriber wiring, routing, error handling | Phase 4 |
| 6 | `persistence.py` — quality_scores.jsonl writer | Phase 5 |
| 7 | `quality_report.py` — report builder + grade computation | Phase 5 |
| 8 | `api/routes.py` — REST endpoints | Phase 7 |
| 9 | Tests: unit (scorers), integration (hub + event bus), regression (grade stability) | Phase 8 |
| 10 | Calibration run: baseline quality_report.json on canonical worlds | Phase 9 |
