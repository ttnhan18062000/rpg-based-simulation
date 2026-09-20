---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, content, world]
---

# Review: Simulation Rules, Taxonomy and System Model

Date: 2026-09-20. Checked against `origin/main` @ `74c11ceb7` plus the merge of #219/#221.

## What this is

The local-agent review requested by `simulation-rule-taxonomy-ext-ai.md` (§35–§36, sections A–Q), read together with `rpg-direction.md` (the agreed direction between the project owner, the external reviewer and this agent).

Following that instruction (§39), this document produces **no milestones, waves, tickets or migrations**. Where I name a change, it is a change to the *framework*, not a plan to build it.

**A process correction on my own prior output.** My earlier companion doc, `2026-09-19-core-rpg-lived-history-growth-brainstorm.md`, jumped straight to a wave/capability program. Per §39 that was premature. Its durable value is the **evidence**: 21 scenarios traced link by link through real code, with a status per link. This review cites that evidence and does not repeat it. The wave structure in it should be treated as illustrative, not as a proposed roadmap, until the three sides agree on the model below.

**Confidence convention.** Claims below are either verified in this session against code or docs (cited), or marked *(unverified)*.

---

## A. Overall assessment

The proposed world model is **coherent and, in its essentials, correct for this project**. It is also closer to what the repository already believes than the document assumes — in several places the repo has already learned a sharper version of the same lesson.

**Strongest ideas** (adopt with little change):

1. **Links and loops as first-class design objects** (§13–§14). This is the single most valuable idea in the framework, and it is independently confirmed by repository evidence: the 21 scenario traces show that most impossible stories fail on *missing connections*, not missing endpoints.
2. **Runtime status taxonomy** (§27). The repo has already paid for the absence of this. It maps almost exactly onto the mechanism registry's existing `state` vocabulary.
3. **Causal-Value First** (E2) — and the repo already has a metric for it (§J).
4. **Bounded ontology change** (D2) and **hybrid agency** (C2). Both match the architecture that exists.
5. **Hybrid progression** (§7) and **RPG abstractions are legitimate** (§6). These end a false dichotomy the earlier external suggestion created.
6. **Verb-first design** (§23), which can be made mechanical rather than rhetorical (§Q7).

**Weakest ideas** (change before adopting):

1. **The D0–D18 domain map is broader than the project's own discipline allows.** It is a *target vocabulary* presented at a size that invites Principle 7's failure ("precise, invisible, load-bearing for nothing"). It needs an explicit admission budget, not just an admission test.
2. **`SUBSYSTEM` is the weakest level** in the hierarchy. In the repo, what the doc calls a subsystem is sometimes a pipeline phase, sometimes a service, sometimes a scale tier. It carries no consistent meaning.
3. **The hierarchy encodes only containment.** The repo has already learned — and written down — that containment, execution order and functional dependency are three different axes that must never be conflated (`registries/mechanisms.yaml` header). The proposed model conflates the second and third inside `LINK`.
4. **The power taxonomy (§19) is a design vocabulary masquerading as a model.** The direction doc itself already resolves this correctly ("do not build a generic Power Conversion Framework… track the actual conversion mechanisms"). The review should keep the resolution and drop the ten-dimension list from the *model*.

**The framework's biggest omission:** it has no representation for **reach** (where and when a mechanism can fire) or for **authority** (who is allowed to mutate durable state). Both are load-bearing in this repo, and both have already produced real defects: mechanisms that are live but only at Campaign episode boundaries in a single corpus profile, and the architectural rule that decision logic may never mutate durable state.

---

## B. Fundamental principles review

| Principle | Verdict | Notes |
|---|---|---|
| Core before gameplay | **Agree** | Already true in fact: there is no player. The "observation" layer also already exists as API presenters and read models, plus the Chronicle. Reuse them as the gameplay lens rather than inventing one. |
| Systemic fantasy realism | **Agree, currently untested** | The repo has almost no supernatural mechanics to test it on: no mana, no spells *(verified: no `mana` field in `src/core/state.py`, no spell module)*. Magic exists only as hazard kinds (`ARCANE_CORRUPTION`), calamity spawns and belief. This principle's first real test will be whatever magic becomes. |
| A2 Open Instability | **Agree with an important modification** | Distinguish **stabilisers** (may fail: trauma decay, war exhaustion, migration) from **invariants** (must never fail: atomic conservation, determinism, the `HardLawMonitor` per-tick checks). "The simulation must permit systemic resistance to fail" must not be read as licence to weaken invariants. Also: SimQ's scoring assumes a healthy world, so a legitimately collapsing world will currently read as a bad run. |
| B2 Significance eligibility | **Agree, with a budget constraint** | Eligibility must be paired with a hard observability budget (e.g. top-K notables per region). Otherwise Principle 7 breaks and so does per-tick cost. |
| C2 Hybrid agency | **Strongly agree** | Already the architecture: rich per-entity cognition (needs, beliefs, goals, risk) versus coarse faction directives (`DEFEND_BORDER`, `TRADE_ROUTE`, `COMMISSION_QUEST`, `EXPAND_TERRITORY`). Do not unify these. |
| D2 Bounded ontology change | **Agree** | The repo already has a live example that proves the bound is the easy part and the *meaning* is the hard part: `EvolutionSystem` changes an entity's `kind` at levels 10/25/50, and nothing reads the new kind. |
| E2 Causal-Value First | **Agree** | Operationalise it with the existing D01 rating dimensions rather than a new metric (§J). |
| RPG abstractions allowed | **Agree** | Add one requirement: each abstraction should be *labelled* as such in the registry, so nobody later mistakes XP for a simulated quantity. |
| Hybrid progression | **Agree, blocked** | Not visible until the combat gate is addressed: the decision-driven attack path fires 0–2 times per 1000–2000 ticks, and most combat that does happen uses a legacy hostility source that disagrees with the authored catalog on 34–97% of pairs. |
| Bottom-up world design | **Agree with modification** | The order in §8 ("what exists → what can happen → …") is right for a greenfield world. For *this* repo the dominant failure is not a missing rule but a missing link, so the alignment pass should be **link-first**: ask what cannot currently happen and why, before asking what fundamentally exists. |

---

## C. Taxonomy review

### C1. The levels

| Level | Verdict |
|---|---|
| DOMAIN | Keep. But see §F: the repo already has a 10-name de facto domain vocabulary (the SimQ pillars). |
| SYSTEM | Keep. Maps to real services/registries. |
| SUBSYSTEM | **Demote to informal.** No consistent repo meaning; it is variously a phase, a service, or a scale tier. Allow it as prose grouping, don't put it in metadata. |
| MECHANISM | Keep. This is the repo's proven unit: 93 entries in `registries/mechanisms.yaml`, each independently verifiable. |
| RULE | Keep. |
| PARAMETER / CONTENT | Keep, and keep the warning that content volume ≠ depth. The repo has a textbook case: the live crafting registry has **3 recipes** while a richer authored item catalog sits disconnected (idea 49). |

### C2. Three axes the hierarchy is missing

The registry header already records the repo's hard-won distinction — containment, execution order and functional dependency are three different things, and `depends_on` is deliberately sparse (~25 of 75 rows at the time) because most wiring-map arrows encode execution order, not dependency. The proposed model keeps only containment, and puts everything else in one `LINK` bag. Recommend making these explicit:

1. **SCALE** — entity / group / region / faction / world. The registry already carries this as `layer` *(verified: entity 50, world 19, faction 11, region 9, group 4)*. Note the terminology collision: the direction doc uses "layer" for stack level. Rename one of them; I suggest **scale** for this axis.
2. **PHASE / CADENCE** — when a mechanism runs. This repo is unusually explicit here (a 7-phase kernel, a 39-phase authoritative pipeline, per-system `SystemCadence`), and cadence is a primary cost control. A taxonomy without it cannot express "live but only every 200 ticks" or "only at an episode boundary".
3. **AUTHORITY** — who may propose versus who may commit. The architecture rule is that decision logic reads state and emits typed updates, and only the authoritative apply path commits them. Any mechanism description that ignores this axis will mis-describe where a mechanism "lives".

### C3. Split `LINK` into three

`LINK` currently mixes three relationships with different lifetimes and different failure modes:

- **DEPENDENCY** — "cannot produce a meaningful result without X" (the registry's `depends_on`).
- **FLOW** — "X's output is Y's input" (the actual wiring; this is where the repo's dormancy bugs live, e.g. cross-region scarcity propagation computed and then discarded).
- **SEMANTIC LINK** — conversion, recognition, reaction, transformation, provenance (the design-level edges the framework cares about most).

The doc's own link categories (State Feed, Trigger, Conversion, Recognition, Information, Authority, Constraint, Spatial Propagation, Historical Provenance, Reaction, Transformation, Feedback) are good, and mostly belong to the third group.

**Should LINK be formally represented?** Yes, but as an **extension of the existing mechanism registry**, not a new artifact (§Q1). The repo already has the machinery: a validator, a completeness check, a graphify cross-check, and rendered views.

---

## D. Rule taxonomy review

Keep the eleven proposed categories. Suggested changes:

| Change | Why |
|---|---|
| **Add: INVARIANT (hard law)** | Distinct from "Fundamental World Law", which is descriptive. Invariants are *enforced*: atomic conservation, determinism, the per-tick `HardLawMonitor` checks. A2's "resistance may fail" must never be read as applying to these. |
| **Add: REACH rule** | Makes §17.4 first-class: how far an effect, an item of information, or an authority extends. The repo's real defects here (global pricing, guild-only rumors, omniscient-ish perception) are all reach defects. |
| **Add: BUDGET / CAPACITY rule** | The repo's most common real constraint: bounded lists, pruning by salience, top-K, cadence gating, scan policy. These are design rules, not implementation details, because they decide what stories are possible. |
| **Clarify: DERIVED rule** | The repo already has a strict discipline here: derived signals are computed at read time and never persisted (scarcity ratio, threat classification). Fold that rule into the category definition. |
| **Merge candidate: SYSTEMIC CONVENTION into MATERIALIZED ABSTRACTION** | The distinction ("combat grants experience" vs "XP") is a distinction between a *rule* and the *quantity it manipulates*, which the RULE/PARAMETER levels already express. Keep one name unless a real case separates them. |

---

## E. Entity/state taxonomy review

The seven proposed kinds are sound. Four repo-first-class concepts do not fit cleanly and should be added:

| Missing kind | Repo evidence | Why it matters |
|---|---|---|
| **INTENT / typed update** | `StateUpdate`, `EntityUpdate`, `ResourceTransferIntent`, the `*Update`/`*Patch` family | A proposed-but-not-yet-committed change is a real object here, and it is the backbone of the authority axis. |
| **AFFORDANCE / OPPORTUNITY** | leads, `QuestOpportunity`, `WorldSignal`, perceived opportunities | The world advertises possibilities; agents consume them. This is neither an event nor a relationship. |
| **OBLIGATION / DIRECTIVE** | `ContractState` (10 kinds), `DirectiveState`, dying wish, bounty | §22's "world-native quest causes" are all obligations. Naming the category makes that design direction concrete (§Q10). |
| **PROJECT** | `QuestState` extends `ProjectState` | A multi-step goal with progress is distinct from an event and from an obligation. |

Two notes on the existing kinds:

- **First-class entity** maps to `EntityState`, `FactionState`, `ClanState`, `GroupRecord`, `RegionState`, `CampState`, `PlaceState`, `BuildingState`. **`PlaceState` is the exception that proves the model matters**: it is first-class in schema but has **no runtime update path** *(verified: no `PlaceUpdate` in `src/core/updates.py`)*, so a Place cannot change kind, be abandoned, or be founded during play.
- **Aggregate** maps to population cohorts, regional pressure, culture. The vision already endorses this split ("a regional population count is a weather system"). Keep the rule that an aggregate may be promoted to first-class only when a named consumer needs per-individual identity.

---

## F. Domain map review (D0–D18)

First, the repo already has a **de facto 10-domain vocabulary**: the SimQ pillars — COMBAT, ECONOMY, SOCIAL, COGNITION, PROGRESSION, NARRATIVE, INFORMATION & BELIEF, FACTION & MILITARY, WORLD DYNAMICS, AGENCY & ACTION. Any new domain map should state its mapping to these, because scoring, corpus tests and grade anchors are all keyed to them.

| Domain | Verdict | Repo state (summary) |
|---|---|---|
| D0 Substrate | **Necessary foundation; deeper than the doc assumes** | Kernel, authoritative pipeline, determinism, persistence, history, dirty sets, cadence. The strongest area in the project. Part of it is technical architecture, not design taxonomy: split "Rule/Mechanism Configuration" and "Deterministic Randomness" out as governance. |
| D1 Space & environment | **Necessary** | Regions, places, adjacency, hazard kinds, biome shifts on trauma. Missing: propagation/spread of any condition. Weather: agree it is optional. |
| D2 Ecology & population | **Important long-term** | Respawn, cohorts, migration, camps/nests exist. Predator/prey as a real loop is missing; several growth paths are flag-gated OFF. |
| D3 Life & body | **Necessary** | Hunger/sleep, aging, wounds and scars, death, corpses, heirs. Disease missing. |
| D4 Perception & information | **Necessary; deeper than the doc assumes** | Beliefs, leads, knowledge model with freshness, causal/spatial memory, chronicle fidelity drift. Gap is reach: rumors originate only from guild intel; no entity-to-entity gossip. |
| D5 Agency & decision | **Necessary; do not re-derive** | The repo has a mature cognition/strategy/domain-decision split with its own contracts. The doc's D5 list is essentially a re-description of it. Highest duplication risk in the whole map. |
| D6 Capability & progression | **Important; currently thin** | XP/levels/skills only; personality frozen; breakthroughs static. |
| D7 Conflict & combat | **Necessary** | Functional, but see the hostility-source divergence and the starved decision path. |
| D8 Items & material culture | **Important** | Inventory, equipment, durability, crafting (3 recipes), heirlooms. Provenance built but OFF. |
| D9 Resources & economy | **Necessary; shallow** | Conservation is solid; pricing is global; no labor market, no supply chains. The open question "what can wealth actually do?" is exactly right and currently answers "almost nothing". |
| D10 Social relations | **Necessary** | Rich: trust, bonds, contracts, reputation (two systems), parties, clans. Several edges dormant. |
| D11 Family & lineage | **Keep separate — stronger than the doc assumes** | Parentage, genetics, heirs, inherited feuds, dying wishes, succession. This is the best live substrate for emergent history in the project. |
| D12 Groups & institutions | **Important** | Groups and clans with a real lifecycle (succession, dissolution). Companies/mercenaries missing. |
| D13 Politics, law, war | **Important; largely unreachable** | Diplomacy, sentiment, territory, war exhaustion exist; conquest and HOSTILE/WAR are not reached in practice; no offices, titles, crime or enforcement. |
| D14 Places & settlements | **Necessary — and the weakest layer; recommend top priority** | Place is immutable at runtime; camps only compiled; no tiers, abandonment, colonisation, place history or naming. Breaks the vision's own headline example (a goblin camp becoming a spider ruin). |
| D15 Culture, belief, religion | **Important** | Culture drift, belief institutions, fidelity drift — all real, all reach-limited to Campaign episode boundaries. |
| D16 Magic & supernatural | **Important long-term; essentially greenfield** | No mana, no spells. Decide first whether magic is *a domain* or *a rule-injection into existing domains* (§Q9) — this choice is bigger than any spell list. |
| D17 History & significance | **Not a domain — connective tissue.** The doc's own hunch is right | Chronicle, fame, fidelity, belief all exist as derivations over other domains' events. Model it as a cross-cutting **recognition layer**. |
| D18 Pressure & collapse | **Not a system — a design category** | Agree with the doc. The repo has exactly one instance (cross-region scarcity propagation), and its output is discarded before reaching a consumer. |

**Domains missing from D0–D18** (all real in this repo):

| Proposed domain | Why |
|---|---|
| **Movement & navigation** | Pathing, spatial indexing, readiness costs, pursuit. Heavy, load-bearing, and the origin of real defects. It is not a sub-note of D1. |
| **Content authoring & world assembly** | Catalogs, world modules, the compiler, registries, content resolution. This is where "authored content defines possibility" (§31) actually lives, and it has its own failure modes (compiled-artifact staleness). |
| **Law, crime & enforcement** | Listed inside D13, but it needs its own identity: the repo has a legality table and a reputation penalty for `THEFT`, and no theft action and no enforcement. |
| **Observation & legibility** | Presenters, read models, the Chronicle, telemetry. Principle 8 has no home in the domain map otherwise. |
| **Evaluation & simulation quality** | SimQ pillars, corpus tiers, grade anchors. A governance domain, but it constrains design (see §K). |

---

## G. Missing mechanisms

The mechanism-level gaps are enumerated as link types L1–L17 in the companion evidence doc and are not repeated here. In short, the highest-leverage missing mechanisms are: individual lived history; recognition/naming of individuals; entity-to-entity gossip; place mutability, founding and succession; leverage (wealth buying capability); crime and enforcement; persistent companies; condition spread; species-specific drives; teaching lineage.

---

## H. Repository mapping

The inventory §20 asks for **already exists**: `registries/mechanisms.yaml`, 93 mechanisms, each with `layer` (scale), `depends_on`, `state`, and a `verified` block recording instrument, verdict, date and evidence.

Current distribution *(verified, this session)*:

| `state` | Count |
|---|---|
| done | 53 |
| partial | 12 |
| gap | 11 |
| gated | 8 |
| orphan | 7 |
| skeleton | 2 |

Recommendation: **extend this, do not replace it.** Mapping to the proposed status taxonomy: `done`→LIVE, `partial`→partial/STARVED, `gap`→MISSING, `gated`→OFF, `orphan`→DORMANT, `skeleton`→DESIGNED. Two statuses have no registry equivalent and should be added: **STARVED** (the registry currently records this only in free-text `verified.note`, e.g. `tactical_decision`'s verdict `contradicted`) and **REACH-LIMITED** (§Q5).

---

## I. Connectivity review

**Existing strong chains** (real, live, multi-hop):

- death → succession → heirloom transfer → inherited feud → dying wish → chronicle;
- resource depletion → scarcity → migration / quest weighting / opportunity reward scaling;
- deaths → regional trauma → hazard level → passive drain → biome transformation;
- contract outcome → bond sentiment → bond role → party composition → future cooperation;
- calamity intensity → displacement → home region retained.

**Isolated or one-hop systems:** economy (in-only), places (terminal), magic (absent), crime (absent), progression (feeds stats, little else).

**Five missing links that would unlock the most histories** (detail in the companion doc): individual lived history; recognition and naming; gossip; place mutability; wealth→capability.

---

## J. Depth map

Recommend **adopting the repo's existing D01 rating dimensions** rather than the eight proposed in §25. They already exist, are already scored across ~36 features, and cover the same ground more cheaply: **Trigger Rate, Entity Reach, Cascade Width, Emergence Ceiling, Absence Penalty**. `Cascade Width` ("feeds 5+ other systems") *is* connectivity, which the doc rightly calls the most important property.

Qualitative map (my assessment, using the doc's four depth levels):

| System | Depth | Connectivity | Notes |
|---|---|---|---|
| Substrate/kernel | Deep | High | Determinism, phases, dirty sets |
| Agency/cognition | Systemic→Deep | High | Mature; duplication risk |
| Social/relationships | Systemic | Medium | Dormant edges |
| Lineage/death | Systemic | High | Best emergent substrate |
| Combat | Functional | Medium | Wrong hostility source; starved decisions |
| Information/belief | Functional→Systemic | Medium | Reach-limited |
| History/chronicle | Systemic | Medium | Campaign-only reach |
| World dynamics/ecology | Functional | Medium | Several loops OFF |
| Economy | Functional | Low | Nothing to buy |
| Progression | Primitive→Functional | Low | Generic, starved |
| Factions/politics | Functional | Low-Medium | Unreachable thresholds |
| Items | Functional | Low | Provenance OFF |
| Places | **Primitive** | **Low** | Immutable at runtime |
| Magic | Missing | — | No mana/spells |
| Crime/law | Missing | — | Legality table only |

---

## K. Architecture and boundary concerns

1. **Canonical state hashing and corpus recalibration.** Every durable field participates in canonical serialisation. Adding state changes `state_hash`, which forces corpus baseline recalibration — the Region/Place rebuild needed a two-stage pilot and a `state_hash`-based recalibration procedure. Any "add history to every entity" idea pays this cost.
2. **Save/persistence size.** History that is per-entity and unbounded is the main new cost risk. Bounded lists plus compression into counters is the existing pattern (causal memory capacity, salience pruning).
3. **Per-tick budget.** Candidate budgets, scan policy, dirty-set scoping and per-system cadence already exist. New per-tick mechanisms (notability, gossip) must declare a cadence, not run every tick.
4. **Concurrency.** Bit-identical parity is officially ratified for sequential execution only. New cross-entity mechanisms (gossip, targeted response) touch multiple entities per step and need care.
5. **Event volume and observability backpressure.** More world reaction means more events; the recorder has explicit backpressure modes.
6. **SimQ grade anchors versus Open Instability.** Scoring assumes a functioning world. A world that legitimately collapses (A2) will score badly, and mechanic changes already cause grade-anchor staleness. The framework needs a way to say "unstable by design" without it reading as "broken".
7. **Reach split (tick vs episode).** Several finished mechanics only derive at Campaign episode boundaries, and exactly one corpus profile enables Campaign mode. Any design that depends on them inherits that narrow reach.
8. **Content pipeline staleness.** Compiled world artifacts don't pick up catalog changes until recompiled.

---

## L. Over-simulation risks

Highest risk first, with the cheaper alternative:

| Risk | Cheaper alternative |
|---|---|
| Weather, climate, atmospheric detail | Region condition tags with real consumers (the existing `hazard_kind` pattern) |
| A psychology model (values, morals, ambitions as separate profiles) | Two or three disposition axes that existing scorers already read. Note the repo already has orphaned `MotivationModel`/`ValuePreferenceProfile`/`AmbitionProfile` — evidence this risk is real, not theoretical |
| Ten power dimensions as state | Named conversion mechanisms only (the direction doc's own resolution) |
| Unbounded history | Bounded formative records + compression into counters |
| Disease modelled before places can change | One generic spread primitive, first instance chosen by need |
| Magic as a spell catalogue | Magic as rule-injection (§Q9) |
| Relationship-type explosion | The existing dimension set (trust, familiarity, fear, grudge, salience) plus roles |
| Per-entity economic simulation (labor, debt, credit) | Coarse regional pressure that real consumers read |

---

## M. Under-simulation risks

Each of these is already real in the repo, not hypothetical:

| Risk | Current instance |
|---|---|
| Wealth with nothing to buy | Gold accumulates; `PROTECTION` contracts have no live producer |
| Relationships that don't change behaviour | `SocialBond.role` was permanently NEUTRAL until 2026-09-07; nemesis promotion still has no caller |
| History nobody remembers | `LegendFact` shipped with no live consumer; belief institutions were terminal until wired |
| Places that cannot change | `PlaceState` has no update path |
| Politics disconnected from individuals | The faction importance signal was cut for lack of a real signal |
| Magic as damage numbers | No magic system at all yet |
| Ecology that can't affect civilisation | No predator/prey loop; growth paths flag-gated OFF |
| Progression that never happens | 0–2 decision-driven attacks per 1000–2000 ticks |

---

## N. Existing principles that should survive

**Preserve unchanged:**

- The **Durable State Rule** (typed model, stable location, lifecycle, inspection, tests) — it is the reason this codebase can be reasoned about at all.
- **Authoritative apply path / no direct mutation**, and **decision logic reads, never commits**.
- **Determinism**, including seeded randomness and sorted iteration.
- **Presenters over raw domain models** at the API boundary.
- **The disclosed-dormancy culture** — the habit of writing "this exists but has no caller" instead of quietly shipping. It is the reason this review could be grounded at all.
- **Verification by corpus instrumentation** rather than by unit test alone (the registry's `verified` blocks).
- **The Mechanics Bible + parity ledger** as the doc/code parity mechanism.
- **The 8 principles of The Unwritten World**, especially 7 (bookkeeping) and 8 (legibility). The new direction adds scope; it should not dilute these two.
- **One fact, one home** for documentation.

**Should become narrower, not disappear:**

- **Feature flags** — governance and migration only, never a way to ship core mechanisms half-wired (the repo has several flag-gated growth loops that have rotted).
- **SimQ** — balance measurement, not feature verification (a specific mechanic needs a focused scenario).

---

## O. Conflicts between the new direction and current practice

| # | Conflict | Likely reason | Trade-off (not resolved here) |
|---|---|---|---|
| 1 | D0–D18 breadth vs Principle 7 ("without drowning in bookkeeping") | Intentional philosophical difference | Breadth gives a target vocabulary; it also invites building state nobody consumes. Needs an admission *budget*, not just a test |
| 2 | A2 Open Instability vs SimQ grade anchors and health scoring | Previous product assumption | Either SimQ learns to distinguish designed instability from breakage, or collapse scenarios are excluded from scored corpora |
| 3 | Replaceable/optional mechanisms (§10, §22) vs "core mechanisms ship unflagged" | Temporary roadmap decision, backed by real rot | Optionality helps experiments; flags have repeatedly produced dormant branches here |
| 4 | "The core is allowed to outgrow current gameplay" vs the in-flight HUD/live-map programs | Scheduling | If the core's state model changes, presenter/HUD work may need rework; sequencing decision, not a philosophical one |
| 5 | Progression-forward framing vs D01's own ranking of Progression as Tier 3 | Evidence vs ambition | The audit measured current impact; the direction describes intended impact. Both can be true — but the measurement should not be quietly discarded |
| 6 | Unbounded emergent history vs canonical hashing, save size and corpus baselines | Technical constraint | Every new durable field has a recalibration cost |
| 7 | "Shared grammar, no universal component" vs the desire for cross-entity comparability | Terminological | Solve in *metadata* (registry fields), never in a shared base class |

---

## P. Suggested changes to the framework

1. **Rename the scale axis.** The registry's `layer` (entity/group/region/faction/world) is a *scale*; the direction doc's "layer" is a stack level. Pick distinct words.
2. **Demote SUBSYSTEM** to informal prose grouping.
3. **Add three axes**: SCALE, PHASE/CADENCE, AUTHORITY (§C2).
4. **Split LINK** into DEPENDENCY, FLOW and SEMANTIC LINK (§C3).
5. **Add rule types**: INVARIANT (hard law), REACH, BUDGET/CAPACITY (§D).
6. **Add entity kinds**: INTENT, AFFORDANCE/OPPORTUNITY, OBLIGATION/DIRECTIVE, PROJECT (§E).
7. **Add runtime status REACH-LIMITED**, and promote STARVED from free text to a real status (§H).
8. **Reclassify D17 as a cross-cutting recognition layer** and D18 as a design category, not domains.
9. **Add five domains**: movement/navigation, content authoring & world assembly, law/crime/enforcement, observation & legibility, evaluation/SimQ (§F).
10. **Adopt D01's five rating dimensions** instead of the eight proposed depth dimensions (§J).
11. **Require a named counterforce** for any mechanism classified as growth-producing (§Q2).
12. **State the mapping to the 10 SimQ pillars** wherever a new domain map is used, since scoring and corpora are keyed to them.
13. **Drop the ten power dimensions from the model**, keep them as design vocabulary, and track real conversion mechanisms instead — as the direction doc itself already concludes.

---

## Q. My own design ideas

### Strong recommendations

1. **Extend the mechanism registry into a link registry rather than creating a new artifact.** Add per-mechanism `produces` / `consumes` / `converts` edges alongside the existing `depends_on`, and add a **dangling-link check** to the existing validator: a mechanism that produces an output nothing consumes is a dormancy defect, detectable mechanically. This directly automates the failure mode that produced most of this project's dormant systems, and it reuses tooling that already exists (validator, completeness check, graphify cross-check, rendered views).
2. **Counterforce pairing as a registry invariant.** Any mechanism tagged as growth-producing must name a counterforce mechanism id (or an explicit, reviewed `none` with a reason). This turns A2's "counterforces may fail" into something checkable, while keeping failure legal.
3. **Promote Place to a mutable first-class entity.** This is the highest-leverage single structural change in the repository: it is the weakest layer (§F/D14), it blocks the vision's own headline example, and it is additive rather than a rewrite. Without it, no scenario involving ruins, founding, abandonment, colonisation or settlement growth is reachable.
4. **Treat recognition as an explicit cross-cutting layer** (notability + naming + gossip + targeted response), rather than as features inside separate systems. B2 ("all first-class entities are eligible for significance") is not achievable by any single domain: it needs one shared recognition substrate that each domain feeds and reads, with per-domain *meaning* (dread, renown, reverence, infamy).
5. **Make REACH a first-class metadata field** on every mechanism: per-tick / per-cadence / episode-boundary / campaign-only, and spatial scope (self, adjacent, region, faction, world). The repo's most misleading status today is "done" on something that only fires at an episode boundary in one corpus profile.
6. **Promote the scenario stress tests into an executable constitution.** Author one corpus world per canonical scenario (the "Ash Fang" world being the first), and treat "can this story still happen?" as a regression test at the corpus tier. The corpus tier taxonomy and long-run observation dimension already exist to hold them.
7. **Make verb-first mechanical.** Maintain the verb inventory (§23) as a real list, and check it against the action/legality registry. Any verb with no action, or any action no agent ever selects, is a finding. This converts a rhetorical exercise into a repeatable audit — and it would immediately surface `steal` (a legality entry and a reputation weight with no action).

### Speculative ideas

8. **A history compaction contract.** Define tiers explicitly — raw event → bounded formative record → derived counter → chronicle entry — with a stated retention rule per tier. This bounds the biggest cost risk in the whole direction and makes "history matters" affordable.
9. **Magic as rule-injection, not a subsystem.** Rather than a spell engine, let magical content instantiate *existing* rules with unusual parameters: fire magic uses the fire/hazard rules; necromancy is a spawn rule keyed to corpses and mass-death regions; corruption is a hazard kind plus adaptation. This satisfies "magic is additional rules inside the simulation" and avoids a parallel magic simulation. Decide this before any spell list.
10. **Obligations as a unifying primitive.** Quests, bounties, contracts, dying wishes, faction directives and patronage are the same shape: an obligation with an origin, a subject, terms, a deadline and a consequence. Unifying them would make §22's "world-native quest causes" nearly free, and would let obligations be inherited, sold, broken and remembered.
11. **A conversion ledger instead of power stats.** Record actual conversion events (wealth→protection, victory→renown, renown→followers) as first-class history. This gives §19 real content — you can ask "how did this entity's power actually move between domains?" — without inventing ten scores.
12. **Aggregate promotion as an explicit lifecycle.** Define how an aggregate (a cohort, a regional economy) can promote into first-class entities when it becomes causally important, and demote back. This is how Songs-of-Syx-style scale and named-individual depth coexist without either a hard cap or a uniform cost.

---

## Scenario stress tests (§37)

Twenty-one scenarios are already traced link by link in the companion evidence doc, including the five this document asks for. Summary verdicts:

| Scenario | Verdict |
|---|---|
| Ordinary creature → regional threat | Not reachable. Breaks at: no memory of exposure or survival, no adaptation, no naming, no way to refer to a specific entity |
| Poor individual → economic/institutional power | Not reachable. Wealth accumulates with nothing to buy; no individual→institution path |
| **Cult as an evolving entity** (not just its founder) | Not reachable *as an entity*. `BeliefInstitution` exists but is a **derived read-model** over chronicle history, not an actor with resources, doctrine or decisions. Making the cult itself first-class (treasury, membership, doctrine drift, schism) is a distinct requirement from the founder's story — the framework is right to insist on the distinction |
| **Settlement as an evolving entity** | Not reachable. Requires Place mutability (§Q3) plus tiers; the demographic and pressure inputs already exist |
| Artifact → relic | Partly reachable. Inheritance is live; item history is built but OFF and has no consumer |

The general pattern holds: **endpoints exist, links do not**.

---

## Recommended next step

Per the direction doc §29, the natural next artifact is the **repository-to-target alignment pass** (its sections A–I), not a milestone plan. Much of it is drafted here (§F, §H, §I, §J, §K, §O). What is missing and worth doing deliberately:

1. agree the **model changes** in §P first, since the alignment pass's vocabulary depends on them;
2. then produce the **current system map** using repo terminology, keyed to the mechanism registry rather than hand-written;
3. only then discuss priorities.

## References

- `rpg-direction.md`, `simulation-rule-taxonomy-ext-ai.md` (the inputs; repo root, untracked)
- [`the_unwritten_world.html`](the_unwritten_world.html) — the 8 principles
- [`2026-09-19-core-rpg-lived-history-growth-brainstorm.md`](2026-09-19-core-rpg-lived-history-growth-brainstorm.md) — the 21 scenario traces and link types (evidence; its wave structure is superseded by §39's "no roadmap yet")
- `registries/mechanisms.yaml` — 93 mechanisms, `layer`/`depends_on`/`state`/`verified`
- `docs/audits/D01_rpg_feature_impact.md` — the five rating dimensions
- `docs/simulation_quality/quality_scoring_contract.md` — the 10 pillars; `corpus_tier_taxonomy.md` — tiers
- `docs/engine/kernel.md`, `authoritative_pipeline.md`, `performance_contract.md`
- `docs/mechanics/05_world_evolution.md`, `07_social_political_dynamics.md`
- `src/core/state.py`, `src/core/updates.py`, `src/engine/evolution.py`, `src/observability/hard_law_monitor.py`
