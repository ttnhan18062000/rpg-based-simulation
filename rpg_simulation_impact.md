# RPG Engine — Simulation Impact Matrix

## Purpose

This document scores every high-level RPG feature of the engine — existing, partial, and
missing — by its actual impact on simulation behavior, not by design ambition or code
complexity. The goal is to give a prioritization tool grounded in simulation dynamics:
how often does this fire, how many other systems does it feed, does it create emergent
behavior, and how badly does the simulation degrade without it?

This is a companion to `docs/plans/engine_future_epics_roadmap.md` (the authoritative gap
analysis) and supersedes the feature priority columns in `feature_summary.md`.

---

## Scoring Methodology

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

**Status labels:** `[EXISTING]` — implemented and verified in current src.
`[PARTIAL]` — partially implemented, gaps confirmed. `[MISSING]` — zero or near-zero code.

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

### Adventure Decision System `[EXISTING]`

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

### Motivation & Goal System `[EXISTING]`

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

### Cognition / Knowledge / Self-Model `[EXISTING]`

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

### Resource Ecology Regeneration `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Periodic regional tick (not every entity tick, but world-scale regular) |
| Entity Reach | 4 | Indirectly affects all resource-seeking entities via supply availability |
| Cascade Width | 5 | Feeds: economy pressure, quest demand, entity migration, faction territorial conflict, world evolution trauma |
| Emergence Ceiling | 5 | Scarcity cycles → boom/bust → migration → territorial conflict → faction war → historical events; each run produces a different pressure history |
| Absence Penalty | 5 | Without it: economy never stresses, quests have no organic demand, world pressure is static, faction conflict has nothing to fight over, long-run simulation produces a flat dead world |
| **Total** | **22 / 25** | |

**Status:** Nodes are static or reset on scenario reload (confirmed in `known_limitations.md`
and roadmap investigation). This is the single highest-leverage missing system in the
engine by score.

**Key dynamic:** Resource regeneration is the **heartbeat of the simulation world**.
Without it, the economy satisfies all demand trivially — there is no scarcity to drive
migration, no depletion to generate quests, no territorial pressure to trigger faction
conflict. The entire emergent chain from individual needs → regional economics → macro
politics depends on resource nodes that can actually run out and recover at varying rates.
Scarcity creates the pressure gradient that makes every other system interesting.

**Composition multiplier:** Enabling this single system unblocks: Macro-Economy Health
Metrics, Pressure-Driven Quest Generation, Faction territorial conflict, and makes World
Emergence regional signals actually vary between runs.

---

### World Evolution System `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | World-scale events — periodic, slow; calamities are rare |
| Entity Reach | 5 | World-scale signals eventually reach all entities |
| Cascade Width | 5 | Feeds entity motivation (threat), migration pressure, resource availability, quest generation, faction conflict |
| Emergence Ceiling | 4 | Calamity + recovery cycles create distinct historical arcs per run |
| Absence Penalty | 3 | World is static between entity actions; entities react but the world doesn't evolve |
| **Total** | **19 / 25** | |

**Status:** Regional trauma and sovereignty are solid. Ecology systems exist
(`WorldEmergencePhase` evaluates `RegionalPressureModel`, `ScarcityModel`,
`ServiceStatePressureModel`). Missing: no complex regeneration, no long-run ecological
cycles, no demographic pressure.

---

## Tier 2 — High Leverage (Score 16–20)

These systems qualitatively enrich most runs. Missing one makes the simulation noticeably
shallower but it doesn't stop running.

---

### Economy / Resources / Crafting `[EXISTING]`

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

### Persistent Campaign Runtime `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Between episodes, not per-tick |
| Entity Reach | 5 | All entities carry cross-episode memory and consequence |
| Cascade Width | 5 | Feeds: social memory, faction history, progression planning, narrative legacy, entity motivation across runs |
| Emergence Ceiling | 5 | Consequences compound across episodes — a betrayed ally becomes a nemesis; a collapsed city leaves a ruin; a legendary fighter's death echoes forward |
| Absence Penalty | 4 | Each run is isolated and amnesiac; no compound history; real RPG continuity impossible |
| **Total** | **20 / 25** | |

**Status:** Zero code for this concept. `CampaignRunner` in `src/domains/campaigns/` is
an **analysis tool** — it creates isolated `AuthoritativeState`, injects synthetic
`quest_completed` events every ~50 ticks for arc classification, wraps the Kernel, then
scorecard-evaluates the result. It shares no code surface with a real persistent campaign
runtime. The naming is a collision risk for future tickets.

**Key dynamic:** This is the durable consequence layer that makes individual run events
meaningful beyond the run. Without it, the simulation has no memory between sessions —
death, betrayal, rescue, and conquest leave no trace. All high-ceiling RPG emergence
(dynasty, legacy, nemesis, generational change) depends on state surviving episode
boundaries.

---

### Faction & Diplomacy System `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Low per-tick frequency; high-consequence periodic decisions (alliance proposals, war declarations, treaty breaks) |
| Entity Reach | 5 | Regional / world-scale — affects all entity choices through territorial pressure, affiliation, and war zones |
| Cascade Width | 5 | Feeds: quest generation, entity migration, combat motivation, economy disruption, world evolution, history chronicles |
| Emergence Ceiling | 5 | Highest ceiling in the engine — kingdom rise/fall, shifting alliances, conquest and collapse create world histories that are qualitatively unique per run |
| Absence Penalty | 3 | Simulation runs cleanly but is purely individual-scale; no macro-RPG structure above the regional level |
| **Total** | **20 / 25** | |

**Status:** Zero engine code. `src/content_semantics/faction.py` is catalog data only
(type labels, affiliation metadata). `docs/systems/grand_strategy.md` describes a legacy
system that does not exist in current `src/`. Fresh build required.

**Note:** Low trigger rate score reflects that individual faction tick-actions are
infrequent. The cascade width and emergence ceiling scores reflect that even infrequent
faction decisions reshape the entire world context that every other system responds to.

---

### Scenario Runtime Service `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Objective evaluation runs frequently; active scenario state shapes signals every tick |
| Entity Reach | 5 | Objective context reaches all entities through quest signals and world state |
| Cascade Width | 4 | Defines success/failure/stall context that shapes motivation, quest, adventure decision, and world evolution |
| Emergence Ceiling | 2 | Framework — it organizes emergence but doesn't itself create new behavioral patterns |
| Absence Penalty | 4 | Can only run open-ended lab experiments; no bounded scenario with objectives, outcomes, or resumable state |
| **Total** | **19 / 25** | |

**Status:** Zero code. Checkpoint infrastructure exists (`src/engine/checkpoint.py`) but
it is for determinism hashing only, not scenario save/resume.

---

### Spatial / Movement System `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Most ticks, most entities are in motion |
| Entity Reach | 5 | All entities need navigation |
| Cascade Width | 3 | Feeds adventure decisions (route feasibility), combat range, resource node access |
| Emergence Ceiling | 2 | Enables geography-sensitive behavior but limited intrinsic emergence |
| Absence Penalty | 4 | Entities cannot navigate — fundamental prerequisite |
| **Total** | **18 / 25** | |

---

### Information / Belief System `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Event-driven updates; periodic stale checks |
| Entity Reach | 4 | All entities hold belief state, but updates are sparse |
| Cascade Width | 4 | Feeds adventure decisions (confidence, risk estimate), cooperation (who to trust), motivation (known vs unknown threats) |
| Emergence Ceiling | 4 | Belief divergence makes two entities in the same region make opposite decisions; rumor propagation creates cascading misinformation |
| Absence Penalty | 3 | Entities become effectively omniscient; decision variance collapses but sim runs |
| **Total** | **18 / 25** | |

**Confirmed gaps:** Blockers are material-resource-only. Leads are coordinate-only.
No person/concept/rumor leads. No paid information economy.

---

### Perception / Attention System `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 5 | Every tick, every entity |
| Entity Reach | 5 | All entities filter signals |
| Cascade Width | 3 | Determines what downstream systems (motivation, cognition, adventure) even see |
| Emergence Ceiling | 2 | Salience budget creates prioritization but limited intrinsic emergence |
| Absence Penalty | 3 | Entities flood on all signals simultaneously — behavior quality and performance both degrade |
| **Total** | **18 / 25** | |

---

### Memory System (Causal / Spatial / Temporal) `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Updated every tick alongside memory domain |
| Entity Reach | 5 | All entities |
| Cascade Width | 3 | Feeds adventure decisions, cooperation scoring, motivation urgency via temporal deadlines |
| Emergence Ceiling | 3 | Causal attribution affects future decisions; spatial memory avoids wasted re-exploration |
| Absence Penalty | 3 | Entities forget everything — repeat failures, no improvement, but sim runs |
| **Total** | **18 / 25** | |

---

### Social / Cooperation / Reputation System `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Periodic + event-driven (help-need evaluation, betrayal detection, reputation updates) |
| Entity Reach | 4 | Entities in proximity or with prior relationship history |
| Cascade Width | 4 | Feeds adventure decisions (party vs solo), combat posture, progression (shared loot), commitment |
| Emergence Ceiling | 4 | Trust networks, betrayal chains, party dynamics, reputation propagation create social fabric |
| Absence Penalty | 3 | Entities become isolated agents; social RPG fabric disappears |
| **Total** | **18 / 25** | |

---

### Active Information-Seeking / Belief Economy `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Deliberate actions: asking guide, paying for rumor, contradicting bad intel |
| Entity Reach | 4 | Info-seeking entities + town NPCs as information sources |
| Cascade Width | 4 | Feeds adventure decisions, belief updates, cooperation (share intel), economy (paid info cost) |
| Emergence Ceiling | 4 | Info markets; rumor propagation; knowledge asymmetry between entities diverges decisions at scale |
| Absence Penalty | 3 | Entities are currently passive about information — they receive it but never seek it; subjective cognition is real but shallow |
| **Total** | **18 / 25** | |

**Confirmed gap:** Strategic blockers are material-only; leads are coordinate-only.
No paid-information routes, no person/concept leads, no contradiction-driven replanning.
This is what currently prevents entities from feeling truly subjective.

---

### Emotion / Mood System `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 4 | Event-driven updates, but events are frequent enough to keep mood active |
| Entity Reach | 5 | All entities |
| Cascade Width | 3 | Feeds adventure decision bias, cooperation threshold, habit bias |
| Emergence Ceiling | 3 | Mood creates short-term behavioral deviation from baseline personality |
| Absence Penalty | 2 | Entities feel mechanical; mood variation is lost but decisions still work |
| **Total** | **17 / 25** | |

---

### Narrative Consequence Layer `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Milestone events only (death, betrayal, rescue, conquest) |
| Entity Reach | 4 | Entities and regions involved in the milestone event |
| Cascade Width | 4 | Feeds motivation (grief, rage, legacy drive), social (nemesis formation), faction (aftermath), world evolution (regional scar) |
| Emergence Ceiling | 5 | Converts raw simulation events into named RPG moments — this is what makes the simulation feel like a story |
| Absence Penalty | 2 | Simulation runs correctly; just doesn't feel like an RPG |
| **Total** | **17 / 25** | |

**Note:** High emergence ceiling at low trigger rate — milestone events are rare but
their consequences should persist forever. Depends on Persistent Campaign Runtime to
have somewhere to write those consequences.

---

### Social Memory as Campaign Consequence `[MISSING — BLOCKED]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Between episodes, loaded at episode start |
| Entity Reach | 4 | Entities with prior cross-episode relationships |
| Cascade Width | 4 | Feeds cooperation (prior betrayal = no party), adventure decisions (avoid nemesis region), reputation, faction affiliation |
| Emergence Ceiling | 5 | Cross-episode grudges, debts, alliances, loyalties create multi-run behavioral through-lines |
| Absence Penalty | 3 | Each episode social state is cold-start; no compound trust history |
| **Total** | **17 / 25** | |

**Blocked by:** Persistent Campaign Runtime. There is no cross-episode state container
to write into yet.

---

### Macro-Economy Health Metrics `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Monitoring, periodic sampling |
| Entity Reach | 5 | World-scale health signal |
| Cascade Width | 3 | Feeds balancing signals, world health status, quest demand calibration |
| Emergence Ceiling | 2 | Measurement and detection, not generative of emergence |
| Absence Penalty | 4 | Economy can silently die — "infinite shop" and "gold inflation" failure modes are invisible without this; sim produces confident but wrong behavior |
| **Total** | **16 / 25** | |

**Note:** Absence penalty is high not because the sim breaks, but because it breaks
*silently*. Gold inflation, resource exhaustion, and dead-economy states accumulate
without any signal. This is a quality gate for the economy's feedback loop.

---

### Pressure-Driven Quest Generation `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Triggered by world pressure signals from WorldEmergence |
| Entity Reach | 4 | Quest availability broadcasts to entities in affected region |
| Cascade Width | 4 | Feeds motivation (quest urgency), adventure decisions (quest routes), cooperation (group quests), progression (quest rewards) |
| Emergence Ceiling | 4 | Quests generated from actual world state create a feedback loop — entity behavior responds to real pressure, not static templates |
| Absence Penalty | 3 | Current quests are 5 hardcoded `QuestKind` enum values with static templates; world pressure creates no new quest demand |
| **Total** | **16 / 25** | |

**Confirmed:** `QuestKind` is a static enum; templates are hardcoded; `CampaignRunner`
injects synthetic `quest_completed` events to help arc classification. World pressure
signals from `WorldEmergencePhase` currently have no path to quest generation.

**Reuse opportunity:** `OpportunityType` in world_emergence is the confirmed reusable
trigger source — this epic doesn't start from zero.

---

### Combat System `[EXISTING]`

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

### Progression / Rewards `[EXISTING]`

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

### Commitment / Reputation Labels `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Event-driven, low frequency |
| Entity Reach | 3 | Entity + affected relationship partners |
| Cascade Width | 3 | Feeds adventure decisions (social-route viability), cooperation (reputation gate), social standing |
| Emergence Ceiling | 3 | Reputation propagation affects future opportunities — a coward label closes cooperation doors |
| Absence Penalty | 2 | Social fabric thinner; abandonment has no consequence |
| **Total** | **13 / 25** | |

---

### History / Chronicle Compiler `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Background compression — not a per-tick behavior engine |
| Entity Reach | 5 | Compresses all entity and world events |
| Cascade Width | 2 | Output consumed by narrative reports; could feed culture drift and myth formation eventually |
| Emergence Ceiling | 3 | Creates narrative structure from emergent events but does not itself generate new behavior |
| Absence Penalty | 2 | Simulation runs fine; long runs produce unreadable raw event logs; thousand-year simulation is uninterpretable without this |
| **Total** | **13 / 25** | |

**Note:** Low score does not mean low importance for the long-horizon vision — it means
the impact is on interpretability and output quality rather than simulation behavior
itself. Required for thousand-year simulation to produce anything useful.

---

### Full Party Adventure Loop `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 3 | Party lifecycle events: formation, cohesion checks, reward splits, dissolution |
| Entity Reach | 3 | Party members (typically 2–6 entities) |
| Cascade Width | 3 | Feeds adventure decisions (party routes differ from solo), combat coordination, cooperation, social trust |
| Emergence Ceiling | 4 | Sustained parties develop shared history → party dynamics → long-form adventure arcs that solo entities cannot produce |
| Absence Penalty | 2 | Parties form but don't sustain; social RPG depth is limited |
| **Total** | **15 / 25** | |

**Confirmed gap:** Recruit, contract appraisal, grudge/betrayal hooks exist. No sustained
multi-tick party lifecycle, class-compatibility scoring, fair reward-split, or escort
behavior. Parties trigger but do not sustain.

---

### Decision Explanation Model `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 5 | Trace is generated every tick with every route decision — just not stored durably |
| Entity Reach | 5 | All entities |
| Cascade Width | 1 | Observability only — does not feed back into simulation behavior |
| Emergence Ceiling | 1 | Captures emergence; does not create it |
| Absence Penalty | 3 | Behavior is a black box for developers; debugging requires log archaeology; behavioral regressions are hard to trace |
| **Total** | **15 / 25** | |

**Note:** High development leverage despite low simulation-behavior score. Route trace is
already computed every tick — this is promotion of existing data to a queryable API, not
new logic. Small build, high debugging value.

---

### Personality → Long-Run Behavior Calibration `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | N/A | Calibration concern, not a runtime system |
| Entity Reach | 5 | All entities have OCEAN traits |
| Cascade Width | 2 | If calibrated correctly, personality weights adjust adventure decision scoring → all behavior |
| Emergence Ceiling | 4 | Correctly calibrated personality creates diverging life arcs — a greedy entity and a cautious entity in the same world should produce detectably different histories |
| Absence Penalty | 3 | Personality works in unit tests but may collapse into similar behavior at scale without calibration |
| **Total** | **14 / 25** | |

**Confirmed:** OCEAN traits, mood, grudges all implemented locally. No metric proves
they compound into distinct long-run life arcs vs. one-off route nudges.

---

### Demographic / Cohort Population Model `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Very slow — generational timescale |
| Entity Reach | 5 | All population |
| Cascade Width | 3 | Feeds economy labor supply, faction power balance, world evolution pressure |
| Emergence Ceiling | 4 | Population cycles, generational knowledge loss, baby boom after war, demographic collapse |
| Absence Penalty | 1 | Only matters in 100+ year simulations; below that threshold this system is irrelevant |
| **Total** | **14 / 25** | |

---

### Progression Planner `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Long-term planning — updated when build goals change, not per-tick |
| Entity Reach | 4 | All progressing entities |
| Cascade Width | 3 | Feeds adventure decisions (routes toward build goal), progression conversion (defer vs use reward), motivation |
| Emergence Ceiling | 3 | Entities pursue specialization paths → differentiated capability curves → different risk tolerances → different regional specializations |
| Absence Penalty | 2 | Progression is tick-local; no long-term character trajectory |
| **Total** | **13 / 25** | |

---

### Combat Ecology Extension (nemesis, multi-year rivalry) `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 2 | Only triggered when recurring antagonist relationship exists |
| Entity Reach | 2 | Specific entity pairs or small groups |
| Cascade Width | 3 | Feeds adventure decisions (avoid nemesis zone), cooperation (warn others), reputation, motivation |
| Emergence Ceiling | 4 | Nemesis relationships create narrative through-lines; retirement-from-fear creates behavioral arcs |
| Absence Penalty | 2 | Combat works; this adds RPG depth |
| **Total** | **13 / 25** | |

**Note:** Roadmap recommendation is to verify current grudge depth before building —
existing grudge/tactical-avoidance system may be deeper than assumed.

---

## Tier 4 — Specialty / Tooling (Score 6–10)

Valuable in specific run types or for simulation quality measurement, not primary
behavioral drivers.

---

### Behavior Scorecard `[EXISTING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Post-run analysis |
| Entity Reach | 5 | Analyzes all entities |
| Cascade Width | 1 | Analysis only — does not feed back into live sim |
| Emergence Ceiling | 1 | Measures emergence; does not create it |
| Absence Penalty | 2 | Lose quality gate; behavior quality undetectable by automated means |
| **Total** | **10 / 25** | |

**Note:** Low simulation-behavior score but high strategic value as a certification gate.
Should become a mandatory gate for every major gameplay change rather than an optional
analysis tool.

---

### Long-Horizon Regression Suite `[PARTIAL]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | CI / periodic |
| Entity Reach | 5 | Tests entire population |
| Cascade Width | 1 | Tooling |
| Emergence Ceiling | 1 | Measures behavior stability |
| Absence Penalty | 2 | Behavioral regressions go undetected across refactors |
| **Total** | **10 / 25** | |

---

### Capability / Support Registry `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Registry query at startup / tooling |
| Entity Reach | 1 | Tooling only |
| Cascade Width | 2 | Prerequisite for Feature Pack Architecture; surfaces known-unsupported paths |
| Emergence Ceiling | 1 | Infrastructure |
| Absence Penalty | 2 | Feature status is ambiguous across docs/tests/source; pluggable-pack work cannot safely start |
| **Total** | **7 / 25** | |

---

### Pluggable Feature Pack Architecture `[MISSING]`

| Dimension | Score | Reason |
|---|---|---|
| Trigger Rate | 1 | Load-time / configuration |
| Entity Reach | 5 | If built, would shape all entity-facing RPG systems |
| Cascade Width | 5 | Meta-architecture — enables swapping race/combat/economy/time-scale models |
| Emergence Ceiling | 1 | Enables emergence from swappable systems but is not itself emergent |
| Absence Penalty | 1 | Zero code; the current engine is not extensible at this level yet |
| **Total** | **13 / 25 in principle — 0 in practice** | |

**Note:** Scored at current state, not at theoretical completion. Score of 13/25 only
applies once Persistent Campaign Runtime, Scenario Runtime, and Capability Registry
exist. At current zero-code state, the absence penalty is effectively 0 because nothing
depends on it yet. Build the anchor epics first.

---

## Infrastructure Tier (not RPG features — scored separately)

These are not RPG features but the simulation depends on them unconditionally.

| System | Status | Notes |
|---|---|---|
| Simulation Kernel (tick loop, phases, determinism) | `[EXISTING]` | `infrastructure.yaml` 100% verified, zero open divergences |
| Authoritative Mutation Pipeline (17-phase apply path) | `[EXISTING]` | Mature; single-mutation-point law enforced |
| Observability (live status, events, WebSocket, anomalies) | `[EXISTING]` | Strong coverage confirmed by tests |
| Replay & Determinism | `[EXISTING]` | Seed-stable, canonical state hashing in `src/engine/checkpoint.py` |
| Granular Phase Permissions (INFRA-155/156) | `[PARTIAL]` | Only 2 unchecked items remain; narrower gap than "Phase Guard" framing implies |
| Unified Read Model Service | `[MISSING]` | APIs fragmented; no single presenter layer |
| Performance / Resource Budgeting | `[EXISTING]` | Budget tests pass; hardware class contracts verified |

---

## Master Summary Table

Sorted by score descending. `[E]` = Existing, `[P]` = Partial, `[M]` = Missing.

| Rank | Feature | Status | Score | Tier |
|---|---|---|---|---|
| 1 | Adventure Decision System | `[E]` | 24 | Foundation |
| 2 | Motivation & Goal System | `[E]` | 24 | Foundation |
| 3 | Cognition / Knowledge / Self-Model | `[E]` | 23 | Foundation |
| **4** | **Resource Ecology Regeneration** | **`[M]`** | **22** | **Foundation GAP** |
| 5 | World Evolution System | `[P]` | 19 | Foundation/High |
| 6 | Economy / Resources / Crafting | `[E]` | 20 | High |
| 7 | Persistent Campaign Runtime | `[M]` | 20 | High GAP |
| 8 | Faction & Diplomacy System | `[M]` | 20 | High GAP |
| 9 | Scenario Runtime Service | `[M]` | 19 | High GAP |
| 10 | Spatial / Movement System | `[E]` | 18 | High |
| 11 | Information / Belief System | `[P]` | 18 | High |
| 12 | Perception / Attention System | `[E]` | 18 | High |
| 13 | Memory System | `[E]` | 18 | High |
| 14 | Social / Cooperation / Reputation | `[E]` | 18 | High |
| 15 | Active Information-Seeking | `[P]` | 18 | High GAP |
| 16 | Combat System | `[E]` | 17 | High |
| 17 | Emotion / Mood System | `[E]` | 17 | High |
| 18 | Narrative Consequence Layer | `[M]` | 17 | High GAP |
| 19 | Social Memory as Campaign Consequence | `[M]` | 17 | High GAP (blocked) |
| 20 | Macro-Economy Health Metrics | `[M]` | 16 | High GAP |
| 21 | Pressure-Driven Quest Generation | `[M]` | 16 | High GAP |
| 22 | Full Party Adventure Loop | `[P]` | 15 | Depth |
| 23 | Decision Explanation Model | `[P]` | 15 | Depth (tooling) |
| 24 | Personality Long-Run Calibration | `[P]` | 14 | Depth |
| 25 | Demographic / Cohort Population Model | `[M]` | 14 | Depth (long-horizon) |
| 26 | Progression / Rewards | `[E]` | 13 | Depth |
| 27 | Commitment / Reputation Labels | `[E]` | 13 | Depth |
| 28 | History / Chronicle Compiler | `[M]` | 13 | Depth |
| 29 | Combat Ecology Extension | `[P]` | 13 | Depth |
| 30 | Progression Planner | `[M]` | 13 | Depth |
| 31 | Behavior Scorecard | `[E]` | 10 | Tooling |
| 32 | Long-Horizon Regression Suite | `[P]` | 10 | Tooling |
| 33 | Capability / Support Registry | `[M]` | 7 | Infra prerequisite |
| 34 | Pluggable Feature Pack Architecture | `[M]` | 0→13 | Big bet (deferred) |

---

## Key Findings

### Finding 1: One missing Tier-1 system — Resource Ecology Regeneration

The only missing system in Tier 1 (Foundation) is Resource Ecology Regeneration, scored
22/25. Its absence penalty of 5 reflects a specific failure mode: the simulation appears
locally correct (entities harvest, trade, craft, and progress) but the world never
generates real pressure. No scarcity means no migration, no faction territorial tension,
no organic quest demand. The engine's motivation → adventure-decision pipeline receives
stable, flat signals instead of dynamic pressure gradients. Long runs produce a living
simulation but not a *living world*.

This is the single highest-leverage missing piece to implement first.

### Finding 2: Three missing Tier-2 systems are the product gap

Persistent Campaign Runtime, Faction & Diplomacy, and Scenario Runtime Service are all
missing and score 19–20. Together they represent the gap between "lab tooling that
analyses simulation behavior" and "a product that runs an RPG simulation." None of the
high-ceiling social/narrative/historical emergence features (Social Memory, Narrative
Consequence, History Compiler) can be built until Persistent Campaign Runtime exists —
there is no cross-episode state container to write consequences into.

### Finding 3: Cascade structure determines priority more than score alone

Resource Ecology Regeneration (rank 4) unlocks Macro-Economy Health Metrics (rank 20)
and Pressure-Driven Quest Generation (rank 21) simultaneously. Persistent Campaign
Runtime (rank 7) unblocks Social Memory as Campaign Consequence (rank 19) and Narrative
Consequence Layer (rank 18). A system's rank in this table should be read alongside which
systems it unblocks, not in isolation.

### Finding 4: Several high-scoring existing systems are depth-limited by missing dependents

Economy/Resources (rank 6, score 20) has an emergence ceiling of 3 instead of 5 because
Resource Ecology Regeneration does not exist. Information/Belief (rank 11, score 18) has
an emergence ceiling of 4 but is partially capped because Active Info-Seeking is missing.
The foundation systems are good — they are waiting for the pressure systems that make
them interesting.

### Finding 5: The CampaignRunner naming is an active risk

`src/domains/campaigns/runner.py` is an analysis harness, not a persistent campaign
runtime. Future tickets that assume they can build cross-episode state on top of it will
discover the mismatch late. It should be renamed to `AnalysisCampaignRunner` or similar
before the Persistent Campaign Runtime epic begins.

---

## Implications for Sequencing

| Priority | Action | Reason |
|---|---|---|
| Immediate | P0 parity hotfixes (`COMB-006`, `COMB-133/134`, `STRAT-164/177`, `SOC-134`) | Pre-existing debt under Authoritative Mechanics Rule; independent of all epics |
| Immediate | Refresh `known_limitations.md` | Stale since 2026-04-21; actively misleads investigation agents |
| Immediate | Rename `CampaignRunner` → `AnalysisCampaignRunner` | Prevents naming collision with real campaign runtime epic |
| Epic 1 | Resource Ecology Regeneration (S–M) | Highest missing score; unblocks economy, quests, faction conflict simultaneously; lowest build cost of the anchors |
| Epic 2 | Scenario Runtime Service (M) | Defines the product-shaped execution loop; required before meaningful scenario-scoped testing |
| Epic 3 | Persistent Campaign Runtime (L) | Unblocks Social Memory, Narrative Consequence, and gives Faction System a consequence container |
| Decide | Faction & Diplomacy System (XL) | Highest ceiling in the engine; largest build; worth a deliberate scoping decision, not backing into it |
| Defer | Pluggable Feature Pack Architecture (XL) | Score is 0 at current state; prerequisites are Scenario Runtime + Capability Registry + at least one anchor epic |