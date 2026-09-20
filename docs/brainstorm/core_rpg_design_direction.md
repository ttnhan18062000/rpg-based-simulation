---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, world]
---

# Core RPG Design Direction

**The shared long-term direction for the simulation**, agreed between the project owner, the external design reviewer, and the local repository agent (2026-09-20).

## Status

This is the **compass**, not a specification. It is not a milestone plan, not an implementation instruction, and not permission to rewrite the repository.

It supersedes nothing in the codebase by itself. What it changes is the **question we ask of new work**: not "does this fit the current roadmap?" but "does this move the world toward the model below, and what does the repository already have that serves it?"

**This document is standalone and authoritative.** It is the single statement of the core RPG direction; nothing else needs to be read alongside it to understand what we are building.

| Document | Role |
|---|---|
| **This document** | The direction: what the world is, what rules govern it, what we are aiming at |
| [`../archive/the_unwritten_world.html`](../archive/the_unwritten_world.html) | **Deprecated and archived, 2026-09-20.** The original creative-direction page. Its 8 principles are not withdrawn — they are carried in full into §2 below. Kept only for its original wording and examples |
| [`2026-09-20-simulation-rule-and-taxonomy-review.md`](2026-09-20-simulation-rule-and-taxonomy-review.md) | The local agent's assessment of this direction against the real codebase |
| [`2026-09-19-core-rpg-lived-history-growth-brainstorm.md`](2026-09-19-core-rpg-lived-history-growth-brainstorm.md) | Evidence: 21 scenarios traced link-by-link through real code |
| `docs/plans/rpg_design_roadmap/` | What has actually been built (M1–M10) |

### What is settled, and what is still open

For anyone picking this up cold — including a reviewer with no repository access:

| | |
|---|---|
| **Settled** | The 8 principles (§2). The five agreed decisions (§6). The definition of realism and the legitimacy of RPG abstractions (§4). Hybrid progression (§5). The structural, rule and entity vocabularies, and the target domain map (§7). Power plurality without a conversion framework (§8). Depth measurement and the counterforce requirement (§9, §11). The runtime status vocabulary (§10). All decisions in §16 |
| **Still open** | The *soft failure* definition for quality scoring (§6/A2) — deliberately left to sharpen later. How today's scoring pillars are reconciled with "collapse is positive evidence". Everything about sequencing: what gets built, in what order, and when. No milestone, wave or ticket has been agreed, and none should be inferred from this document |
| **Deliberately absent** | Implementation design. This document says what the world is and what rules govern it, never how to build any of it |

**Relationship to the existing repository.** The repo is *evidence*, not a ceiling:

```
Current repository  →  evidence, reusable systems, constraints, lessons
Shared direction    →  target world model and design principles
Future work         →  incremental evolution toward that target
```

Where the repo already supports the direction, reuse it. Where it holds a useful mechanism under a different name, extend it rather than duplicating. Where it conflicts, **surface the conflict explicitly** — neither side automatically wins. Large changes still require evidence.

---

## 1. The one-line direction

> **Simulate not only what entities are, but what they can become.**

The loop we are building toward:

```
World State → Experience → Accumulation → Adaptation/Learning → Capability
→ Power → Conversion → Influence → World Reaction → Transformation → New World State
```

This is a **shared conceptual grammar, not a universal implementation**. A wolf, a merchant, a religion, a settlement and an artifact may all participate in comparable causal patterns while sharing no code and no common progression object.

---

## 2. The 8 founding principles

The founding creative direction, carried forward intact. Everything else in this document answers to these.

**1 — No one hands down the story; it has to be found.**
*The governing principle.* If you can point to a line of logic that says "and here is where the story happens", it is staged, not real. A story here is what is left over after independent entities, each acting on reasons that make sense only to them, happen to collide. The right test for a new mechanic is not "does this produce a satisfying story" but **does this create a new intersection other systems can stumble into**. Narrative satisfaction is a result, never a target.
*Failure looks like:* a mechanic that produces the same shape of consequence regardless of context, or a random event with no thread connecting it to what the world already knows about that entity or place.

**2 — Individuals carry their own trajectory, distinguishable from the aggregate.**
*Scale: one entity.* The world tracks populations because it must, but a name, a face and a specific history must never dissolve back into the average. Two entities from an identical template should visibly diverge because of what actually happened to each. The aggregate is not the enemy — a regional population count is a weather system — the failure is confusing the two. Part of owning a trajectory is that things are not merely done *to* you: joining, marrying, swearing allegiance should be something an entity could refuse, given who they are.
*Failure looks like:* a historied entity behaving exactly as the regional average would predict; or a commitment that simply happens to someone, with no point at which their own reasons could have refused.

**3 — Different creatures should be different, not reskinned humans.**
*Scale: species and kind.* A goblin camp, a wolf's den and a dwarven city are three different answers to "how does this creature exist", not one settlement shape with three coats of paint. The distinction should reach into how a creature relates to its own life: a magical being manifests at full capability and has no childhood; a dragon's life is not a coming-of-age story with bigger numbers. Psychology should diverge the same way: a wolf pack's loyalty is territorial instinct, a goblin's is opportunistic, a human's can survive their guild losing.
*Failure looks like:* a bestiary where every entry is a human with different numbers — same drives, same social shape, same emotional register.

**4 — No single loyalty wins by default.**
*Scale: relationships and politics.* Someone can love a person their country is at war with. A guild can pull a member against their king. The world should let that tension sit unresolved rather than quietly picking a winner. The friction *is* the content. The interesting version is not the dramatic choice but the quiet one: most conflicting loyalties never erupt — they produce hesitation, a slightly worse decision, a private grudge, accumulating over a life. Design each loyalty to push on its own terms and let behaviour land where the pushes add up, even in a messy middle no single loyalty would have chosen.
*Failure looks like:* one layer of loyalty (usually political) silently overriding all others whenever they conflict.

**5 — Places remember what happened to them.**
*Scale: geography and history.* A ruin should be legible as a *specific* fallen city, a razed war-camp, a den something moved into after its owner died. Scars on the map are the world's memory of itself. Goblins camp beside an old battlefield, grow, raid a city, are destroyed; years later spiders have settled the abandoned structures and the place is remembered as a spider-infested ruin — today's world becoming tomorrow's archaeology, with no authored quest anywhere in it. Political geography deserves the same memory: a border that moved five times should leave a trace; a city that changed hands three times should feel unsettled generations later. And memory runs both ways — entities should remember places, carrying grief tied to an actual location with a history.
*Failure looks like:* a place fully described by "type plus a hazard number", indistinguishable from a freshly generated location with the same stats.

**6 — Nothing sits still forever.**
*Scale: pacing and pressure.* Left alone, a threat should worsen rather than wait to be convenient. A grudge should fester; an ambition should grow. A static world is a dead one. Population pressure in a crowded city should feed a nation's ambition to expand, which founds or contests places, which draws population, which builds pressure elsewhere. No layer's resting state is actually rest. Relationships deserve the same restlessness: an untested trust shouldn't stay perfectly trusted forever; an ally unseen for years isn't owed the same confidence as one seen yesterday.
*Failure looks like:* a system whose entire state is a number that only ever moves when something directly acts on it.

**7 — A world that feels lived-in without drowning in bookkeeping.**
*Scale: how much detail earns its keep.* This is the discipline that keeps the other seven from spiralling into simulating everything. Enough weight that a wound, a marriage or a death costs something real — without tracking the biology or logistics beneath it. Depth is chosen for what it produces, not for how realistic it sounds. The honest test: *if this were fully built, would anyone watching ever notice the difference?* A wound changing combat odds is noticed every time; a modelled digestive system never is.
*Failure looks like:* precise, invisible systems that are load-bearing for nothing — and worse, that create the appearance of richness never actually delivered. **Prefer one coarse signal an observer can feel over three precise ones nobody will ever see.**

**8 — The world has to tell on itself: legible from outside, not just correct underneath.**
*Cuts across every scale.* Emergence nobody can follow is indistinguishable from noise. A rise, a fall, a rivalry, a betrayal has to be recognisable as it happens, not merely true somewhere in internal state. Reputation and notoriety do this job one level down: they are how one entity's history becomes visible to others, rather than true only in a record the engine alone can read. For anything new, ask specifically: **how would this become visible — to a watching observer, or to another entity inside the world?** A place remembering something only pays off if that memory can surface in its name, its terrain, or a rumour a traveller carries.
*Failure looks like:* a correctly computed fact with no path to ever becoming visible to anyone, not even to the world's own history.

**Principles 7 and 8 are load-bearing for everything below.** This document sets a deliberately large target vocabulary (§8), which *increases* the risk of building precise, invisible things. Breadth in the map is not permission to build breadth in the world.

---

## 3. Core before gameplay

> **Build the simulation core first. Gameplay is a way of interacting with that simulation.**

```
WORLD SIMULATION → AUTONOMOUS AGENTS → OBSERVATION/AUTHORITY/AUTOMATION
→ GAMEPLAY LENS → PLAYER EXPERIENCE
```

The same world might one day support a single-character RPG, party or guild management, kingdom management, indirect political play, god-like influence, or pure observer/chronicle mode. **We are not building those modes now.** We are only avoiding decisions that make them impossible.

> **Decided 2026-09-20 — there is no player, and none is planned.** The founding pitch stands: *a living world you observe.* The core stays player-agnostic by simply not having a player, and anything player-facing is a lens built over the simulation later. No core design decision should be justified by a hypothetical player's experience.

Consequences we accept:

- gameplay-layer code may later need adapting to protect a cleaner core;
- preserving existing gameplay code is **not** more important than the integrity of the long-term simulation.

The limit: **no universal-engine syndrome.** Do not add abstraction because a hypothetical future game might want it. Generalise only where real variation or shared semantics justify it.

---

## 4. What kind of realism

The target is **systemic fantasy realism**, not literal realism.

Fantasy may be impossible in reality. But once something exists in this world, the simulation treats it as a real part of that world's causality. If dragons exist, then habitat, food, territory, fear, knowledge, trade avoidance, hunting, lairs, wealth, death, remains and historical significance may all legitimately have to reason about dragons.

**Magic is not a bypass.** Magic means *additional rules inside* the simulation:

```
necromancy → corpse becomes an active entity → settlement reacts → religion reacts
→ population changes → regional fear changes
```

> **Decided 2026-09-20 — magic is its own domain, wired outward.** It owns its own sources, costs, rules and consequences rather than being scattered as modifiers inside other systems. But it is only real to the extent it connects: a spell that changes a damage number and nothing else has failed the principle. Magic must reach combat, interaction, body, ecology, places, belief and information — the same way any other domain earns its keep through links.

**RPG abstractions are legitimate world rules.** HP, XP, levels, skill ranks, mana, morale, reputation, rarity, threat level and status effects are all allowed. XP is a *materialized abstraction* of accumulated experience; HP of continued combat effectiveness. Do not reject a useful convention for being unrealistic.

What matters is knowing which is which: **direct simulation / materialized abstraction / fantasy convention / derived state / content**.

---

## 5. Hybrid progression

Traditional RPG progression and lived-history progression **coexist**:

```
combat → XP → level → attributes/capabilities          (legible, predictable)
survives dragon fire repeatedly → formative history
   → fire adaptation → reputation → changed behaviour   (unique, emergent)
```

Two level-20 warriors may therefore be radically different: one a famous, fire-scarred, politically connected dragon hunter; the other a wealthy duelist feared by criminals. Level gives readable progression; history gives individuality. **Neither replaces the other.**

Progression is also plural in *channel*: numeric, practice/mastery, history, capability, social, economic, political, knowledge, institutional, spatial, artifact, ontological. No system must implement every stage of the grammar, and no universal component is required.

---

## 6. The five agreed decisions

### A2 — Open instability

The world is **not guaranteed to return to equilibrium**. Growth processes should usually meet real counterforces, but those counterforces may lose. Outcomes may include recovery, a new equilibrium, regional collapse, institutional collapse, ecological regime change, economic breakdown, political fragmentation, or long-term transformation.

We are **not** designing around apocalypse. The rule is only:

> The simulation must permit systemic resistance to fail — there is no hidden guarantee that restores the original state.

**Boundary:** this applies to *stabilisers*, never to *invariants*. Atomic conservation, determinism and the per-tick hard-law checks must still always hold. "Instability" means the world may change irreversibly, not that its laws may break.

> **Decided 2026-09-20 — collapse is a success signal, not a quality failure.** Simulation-quality scoring exists to detect **logic failure**, not misfortune:
>
> - **Hard failure** — the world doing something impossible: duplicated movement, invalid or erroring actions, conservation breaches, non-determinism.
> - **Soft failure** — the world reasoning wrongly: decision chains that don't follow their own rules, goals selected against their own preconditions, causal chains that don't hold up. (Definition to be sharpened later.)
>
> A country destroyed, an economy broken, a region ruined, a population collapsed — these score as **positive** evidence that the world's causality works. A healthy world is one whose *logic* is sound, not one whose *fortunes* are good. Scoring must never quietly push the simulation back toward comfortable outcomes.

### B2 — All first-class entities are eligible for significance

Any first-class simulated entity may **in principle** become historically significant: people, creatures, groups, organizations, factions, religions, settlements, places, artifacts, major supernatural phenomena.

Eligibility is not destiny. Significance should stay **rare**, through competition, thresholds, mortality, scarcity, failure, counterforces and history — and through an explicit observability budget, so that "significant" keeps meaning something.

Different categories may have very different simulation fidelity.

### C2 — Hybrid agency

Not every entity is modelled as a person.

```
Person      → needs, drives, goals, knowledge, risk, fear, relationships, planning, refusal
Faction     → expand, defend, tax, negotiate, mobilize
Settlement  → attract population, invest, consume, decline
Institution → recruit, spread, preserve doctrine, oppose rivals
```

A city does not need a fake human personality to participate in world progression.

### D2 — Bounded ontology change

History may cause qualitative transformation:

```
wolf → adapted predator → corrupted predator
camp → settlement → abandoned settlement → ruin → occupied ruin
following → organization → institution
ordinary weapon → heirloom → relic
human → cursed human → transformed being
```

But **ontology matters**. The rule is *not* "everything can become everything". Rare exceptions exist only where world rules explicitly support them.

### E2 — Causal-value first

Depth is valuable when it creates new decisions, interactions, capabilities, history, propagation, transformations or systemic consequences — **not** because more variables feel more realistic.

> A coarse property used by six systems beats twenty precise variables nothing consumes.

---

## 7. How the world is structured

### Fundamental world contract

| Aspect | Rule |
|---|---|
| **Identity** | First-class entities keep persistent identity; transformation does not erase historical continuity |
| **Time** | Processes take time; not everything runs every tick |
| **Causality** | Durable change should have a traceable cause: event → consequence → new state |
| **Space & reach** | Effects are not automatically global. Information, disease, trade, danger, authority and influence all have reach |
| **Capability** | Entities act only within real capability and context; agentic action also needs knowledge, intent and opportunity |
| **Cost** | Powerful actions normally touch time, resources, risk, attention, social capital or opportunity cost. Consequence-free capability should be deliberate |
| **Information ≠ truth** | The world has true state; agents have perception, memory, reports, rumor and belief, which may be wrong |
| **Persistence** | Causally valuable state survives; raw history may be retained, compressed, summarized or derived into traits and counters |
| **Transformation** | Qualitative change is allowed within bounded ontology |
| **Instability** | The world may leave equilibrium |

### Structural vocabulary

```
DOMAIN → SYSTEM → MECHANISM → RULE → PARAMETER / CONTENT
```

`SUBSYSTEM` remains available as informal prose grouping, but carries no metadata meaning — in this repo it variously denotes a pipeline phase, a service or a scale tier.

- **Mechanism** is the practical unit: testable, ownable, replaceable, and the level at which this project already tracks reality.
- **Parameters are not features.** **Content volume is not system depth.**

**Three axes cut across the hierarchy** (adopted 2026-09-20), because containment alone cannot describe a mechanism:

| Axis | Values | Why |
|---|---|---|
| **Scale** | entity · group · region · faction · world | Already carried by the mechanism registry (as its `layer` field). Note the word collision: registry "layer" = this axis, not a stack level |
| **Cadence / phase** | per-tick · per-cadence · phase-scoped · episode-boundary | When a mechanism can fire. Primary cost control, and the difference between "done" and "done but almost never runs" |
| **Authority** | proposes · applies · commits | Decision logic reads state and emits typed updates; only the authoritative path commits. A description ignoring this mis-places the mechanism |

### Rule types

Fundamental world law · domain law · **invariant (hard law)** · materialized abstraction · systemic convention · derived rule · **reach rule** · **budget/capacity rule** · threshold rule · pressure rule · transformation rule · counterforce rule · content rule · exception rule.

- **Invariant** is distinct from fundamental world law: invariants are *enforced* (atomic conservation, determinism, per-tick hard-law checks) and are exempt from A2's "resistance may fail".
- **Reach rule** governs how far an effect, an item of information or an authority extends.
- **Budget/capacity rule** governs bounding: capped lists, pruning, top-K, cadence gating. These decide which stories are possible, so they are design rules, not implementation details.
- **Derived rule**: derived state is computed at read time and never persisted.

### Entity and state types

First-class simulated entity · aggregate entity · resource · condition · relationship · event · knowledge claim · **intent (typed proposed change)** · **affordance/opportunity** · **obligation/directive** · **project**.

The last four were added 2026-09-20 because the repository already treats them as first-class: typed updates and transfer intents; leads, opportunities and world signals; contracts, directives and bounties; multi-step goals with progress.

An aggregate (a population cohort, a regional economy, a culture, an ecosystem) is a legitimate abstraction — a weather system, not a failure. It may be promoted to finer detail when causal value requires it.

### Links are first-class

The clearest lesson from this repository: **systems can exist and still produce no histories, because they are not connected.** `LINK` and `LOOP` operate across the whole hierarchy and matter as much as the levels themselves.

Links come in three kinds, which must never be conflated — containment, execution order and functional dependency are three different things:

| Link kind | Meaning |
|---|---|
| **Dependency** | "cannot produce a meaningful result without X" |
| **Flow** | "X's output is Y's input" — where dormancy defects live |
| **Semantic link** | The design-level edges: conversion · recognition · reaction · transformation · historical provenance · information · authority · constraint · spatial propagation · state feed · trigger · feedback |

> A system with many internal mechanics and almost no external links is complicated, not deep.

### Loops

Positive (wealth → opportunity → wealth), negative (wealth → visibility → taxation/theft/rivalry), and transformative (environment → adaptation → behaviour → environment).

The goal is **not** to eliminate positive feedback — it is one of the main sources of historically significant entities. Counterforces should come from other world systems wherever practical, and, per A2, they are allowed to fail.

---

### The target domain map

This is the **target taxonomy for the whole simulation**, deliberately drawn complete rather than trimmed to what exists today. Most of it is far from current implementation. That is intentional: a clean map is what lets us plan RPG features against a long roadmap instead of one feature at a time.

**Reading rule:** presence on this map is *not* a commitment to build. Every entry still has to pass the admission test (§11) and Principle 7. The map says where a thing would belong if it existed, not that it should.

**Foundations**

| Domain | Scope |
|---|---|
| **Substrate** | Entity identity, state transition, time, scheduling and cadence, spatial topology, event flow, persistence, history storage, deterministic randomness |
| **Space & environment** | Regions, places, adjacency, routes, terrain, biome, hazards, environmental degradation and recovery, biome transformation |
| **Movement & navigation** | Pathing, spatial indexing, traversal cost, readiness, pursuit, blocking, transport |

**The living world**

| Domain | Scope |
|---|---|
| **Ecology & population** | Species populations, predator/prey, food availability, habitats, migration, reproduction, competition, succession, extinction |
| **Life, body & survival** | Vitality, needs, injury, impairment, disease, poison, healing, aging, lifecycle, death, remains, physical form |
| **Perception, knowledge & information** | Perception, awareness, memory, belief, rumour, communication, reports, secrets, last-known state, teaching, research, discovery, distortion, information networks. *Truth ≠ knowledge* |
| **Agency, motivation & decision** | Needs, drives, personality, disposition, values, goals, intent, risk and opportunity evaluation, fear, morale, planning, task and action selection, habits, obedience, refusal |

**Capability and conflict**

| Domain | Scope |
|---|---|
| **Capability & progression** | Attributes, XP, levels, skill mastery, traits, adaptations, abilities, training, learning, capability unlocks, thresholds |
| **Conflict & combat** | Hostility, threat recognition, engagement, targeting, positioning, attack, defence, damage, armour, resistance, injury, morale, retreat, surrender, death, loot, combat history |
| **Objects & material culture** | Item identity, inventory, equipment, materials, quality, durability, repair, crafting, maker identity, ownership, provenance, heirlooms, relics |
| **Resources, production & economy** | Extraction, production, labour, employment, consumption, supply, demand, scarcity, markets, pricing, trade, transport, currency, wealth, property, taxation, tribute |

**Society**

| Domain | Scope |
|---|---|
| **Social relations & identity** | Relationships, trust, sentiment, friendship, rivalry, grudges, fear, romance, marriage, kinship, patronage, mentorship, status, reputation, notability, titles, epithets |
| **Family, lineage & succession** | Parentage, inheritance, heirs, dynasties, inherited property, inherited reputation, inherited conflict, teaching lineage, succession |
| **Groups, organizations & institutions** | Parties, companies, clans, guilds, religious and military organizations, membership, leadership, roles, hierarchy, treasury, recruitment, founding, growth, succession, schism, dissolution |
| **Politics, authority & war** | Authority, offices, titles, legitimacy, policy, diplomacy, alliances, faction relations, war, mobilization, conquest, borders, rebellion, secession, polity founding and collapse |
| **Law, crime & enforcement** | Ownership legality, crime, detection, witnesses, justice, punishment, enforcement bodies, outlawry |
| **Places, settlements & territory** | Place identity, residence, home, occupancy, control, infrastructure, services, traffic, founding, growth, standing/tiers, abandonment, ruin, colonization, territory, borders, place history and naming |
| **Culture, belief & religion** | Culture, norms, traditions, cultural drift, belief, faith, worship, conversion, religious authority and institutions, ritual, heresy, schism, sacred places, relics, myths |
| **Magic & the supernatural** | Magical sources, energy, spells, rituals, enchantments, curses, blessings, exposure, corruption, mutation, summoning, transformation, spirits, undead, divinity, magical artifacts, magical ecology |

**Cross-cutting layers.** These are not domains — they are connective tissue that every domain feeds and reads. Modelling them as domains would hide the fact that their whole value is the connection.

| Layer | Scope |
|---|---|
| **History, significance & world reaction** | Events, formative experiences, causal memory, biography, chronicle, historical fact, notability, naming, legend, myth and distortion, rumour, targeted response, bounties, hunts, pilgrimage, commemoration |
| **Systemic pressure & propagation** | Scarcity propagation, contagion (disease, fire, corruption), migration pressure, economic shock, political instability, ecological imbalance, calamity, recovery, counterforces, regime change, collapse |
| **Observation & legibility** | Read models, presenters, chronicles, telemetry, inspection surfaces — how Principle 8 is actually delivered |
| **Content authoring & world assembly** | Catalogs, world modules, compilation, content resolution, registries — where authored identity enters the world |
| **Evaluation** | Simulation-quality scoring, corpus tiers, baselines — how we know the world still works (§10) |

**Mapping to today's scoring vocabulary.** Simulation-quality scoring currently uses 10 pillars, and corpora and baselines are keyed to them. Any use of the map above should state its mapping rather than silently replacing them: COMBAT → conflict; ECONOMY → resources/economy; SOCIAL → social relations; COGNITION → perception/knowledge; AGENCY & ACTION → agency/decision; PROGRESSION → capability/progression; NARRATIVE → history layer; INFORMATION & BELIEF → perception/knowledge plus culture/belief; FACTION & MILITARY → politics/war; WORLD DYNAMICS → ecology, space/environment and the pressure layer.

## 8. Power is plural

Do not reduce influence to one generic Power score. Useful **design dimensions**: physical, economic, social, political, informational, knowledge, territorial, technological, institutional, spiritual/magical.

These are a vocabulary, not a required set of stats. What matters is **conversion**:

```
wealth → hired soldiers → physical force
victory → reputation → followers → political leverage
knowledge → technique → production advantage → wealth
territory → resources → revenue → military capability
```

> **Do not build a generic Power Conversion Framework.** Track the actual conversion mechanisms instead.

---

## 9. Design order and discipline

### World rules before RPG mechanics

Do not start from "what skill tree / boss / quest should exist?". Start from:

> What exists? What can happen? What persists? What can change? What can be perceived? What can act? What can accumulate? What can propagate? What can convert? What can transform? What resists growth? What can become historically important?

Then decide what is directly simulated versus represented by an RPG abstraction. Only then ask how gameplay exposes it.

### Verb-first

If a verb should exist (`teach`, `steal`, `hire`, `claim`, `abandon`, `betray`, `worship`…), the world needs enough state to make it meaningful — and no more. `steal` implies ownership, transfer, detection, knowledge, legality and consequence. This keeps us from adding state no entity can ever interact with.

### Quests prefer world-native causes

```
settlement fears a creature → bounty exists → the RPG layer presents a quest
```

rather than a quest existing and the world inventing a reason. The core may model requests, contracts, bounties, obligations, rumors, opportunities, goals and orders; "quest" can be a presentation of those. Authored quests remain allowed.

### Authored content and emergence

Author species, cultures, gods, spells, materials, historical seeds, ancient cities, world laws, artifacts, catastrophes and special entities freely.

> **Authored content provides identity. Simulation provides consequences.**

An ancient cursed sword may be authored; who owns it, who dies for it, where it travels, who worships it and whether it becomes politically important should preferably emerge.

### Depth, breadth and connectivity are different things

- **Breadth**: how much content or how many mechanisms exist.
- **Depth**: how rich the internal causal behaviour is.
- **Connectivity**: how strongly it interacts with other systems.

Hundreds of identical crafting recipes are breadth without depth. `ownership` is low breadth with enormous connectivity. **For this project, connectivity is one of the strongest indicators of value.**

Maturity ladder: **primitive → functional → systemic → deep**. A system need not become deep for completeness; depth should follow causal value.

**How we measure it.** Use the five dimensions the project's own feature audit already applies, rather than inventing a parallel set: **trigger rate** (how often it fires), **entity reach** (how much of the world it touches), **cascade width** (how many other systems consume it — this is connectivity), **emergence ceiling** (local variation versus novel macro-patterns), and **absence penalty** (what breaks without it). Cascade width is the dimension to watch first.

---

## 10. Knowing what we actually have

"Implemented" is not enough. A mechanism can exist in code with no producer, no consumer, no caller, unreachable thresholds or a disabled flag. The project should always be able to say, per mechanism:

```
MISSING · DESIGNED · EXPERIMENTAL · OFF · DORMANT · STARVED · REACH-LIMITED · LIVE · DEPRECATED · REPLACED
```

- **STARVED** — a live path whose conditions almost never occur in real simulation.
- **REACH-LIMITED** (added 2026-09-20) — live and reached, but only inside a narrow slice of reality: one execution mode, one corpus profile, or only at episode boundaries. Several finished mechanics in this project are in exactly this state, and calling them "live" has repeatedly overstated what the world can actually do.

and, at the system level: how many domains, systems, mechanisms, cross-system links and feedback loops exist.

Mechanism metadata worth carrying eventually: id, domain, system, purpose, rule type, scope, inputs, outputs, state owner, consumers, cross-system links, persistence, observability, optionality, replacement boundary, counterforce, depth, runtime status, validation scenario.

**Optionality is a governance tool, not a design pillar.** Mechanisms may be core, default, optional, experimental, replaceable or content-scoped — but fundamental invariants must not casually depend on a feature flag, and a replaceable mechanism should preserve a semantic contract (one implementation may use `kill → XP`, another `participation → mastery`; both satisfy "combat experience can produce progression").

---

## 11. The rule admission test

Before adding significant new state or a new mechanism:

1. What concept does this represent?
2. Is it a world rule, abstraction, fantasy convention, derived state or content?
3. Who can perceive or interact with it?
4. Which system consumes its output?
5. What future decision or state can it change?
6. What does it connect to?
7. Should this be simulated, or would an RPG abstraction represent it better?
8. Does it need numeric precision, or would coarse categories give the same causal value?
9. If it produces growth, what counterforce exists?
10. If it is optional, what happens when it is absent?
11. Can it produce meaningful history?
12. Does it duplicate an existing mechanism under different terminology?

> State with no interaction, no consumer, no behavioural effect and no historical consequence should be treated with suspicion.

**One hard requirement:** any mechanism that produces growth or accumulation must **name its counterforce** — another world process that pushes back — or record an explicit, reviewed reason why none exists. Per A2 the counterforce may lose; what is not allowed is growth with nothing on the other side of it.

---

## 12. What this direction does *not* say

It does **not** mean: simulate every real-world detail · remove XP, levels, HP, quests or classes · make every entity use one progression system · make every entity legendary · finish all domains before any gameplay · make every feature emergent · rewrite the repository · preserve every current system forever · build a generic engine for every imaginable game.

The target is narrower:

> **Build an unusually coherent and deeply connected systemic fantasy world, then build RPG experiences on top of it.**

---

## 13. The final shared principles

1. **World before gameplay** — the simulation stands on its own.
2. **Fictional rules are real rules** — fantasy is causally real inside the world.
3. **Causal value over microscopic fidelity.**
4. **Abstraction is legitimate.**
5. **History matters** — what happened to an entity can change what it becomes.
6. **Progression should create capabilities, not only numbers.**
7. **All first-class entities are eligible for significance** — possible, never guaranteed.
8. **Shared grammar, domain-specific meaning.**
9. **Power is plural and convertible.**
10. **World reaction is part of progression** — significance is other systems reacting to you.
11. **Transformation is bounded.**
12. **Agency is hybrid.**
13. **Counterforces are systemic but not guaranteed.**
14. **Connectivity is a first-class design goal.**
15. **Coarse first, deepen through causal need.**
16. **Systems and links must be legible to designers.**
17. **Optionality must be deliberate.**
18. **The core may outgrow current gameplay.**

---

## 14. The ultimate target

Not "a game with many systems", but a world where we can say precisely:

> Combat is deep, but its political consequences are still shallow. Economy works, but wealth cannot yet become institutional power. Relationships are rich, but information propagation is too omniscient. Magic has many spells, but barely affects ecology. Places contain infrastructure but accumulate no history. Knowledge is modelled but cannot become leverage. Faction politics are broad, but individual history rarely propagates upward. Ecology exists, but predators cannot become historical actors.

At that point the roadmap stops being driven by *"what feature sounds interesting next?"* and starts being driven by:

> **Which part of the world model is currently shallow, isolated, missing a critical causal link, or preventing meaningful histories from emerging?**

---

## 15. Amendments

The local agent's review of this direction against the real codebase proposed 13 changes ([`2026-09-20-simulation-rule-and-taxonomy-review.md`](2026-09-20-simulation-rule-and-taxonomy-review.md) §P). **All 13 were adopted on 2026-09-20**, in two passes — the vocabulary first, then the taxonomy and measurement changes once the owner decided to build the clean model ahead of implementation.

### Adopted 2026-09-20 — vocabulary

Folded into §7 and §10 above:

1. `SUBSYSTEM` demoted to informal grouping.
2. Scale, cadence/phase and authority added as cross-cutting axes; the "layer" word collision called out.
3. `LINK` split into dependency / flow / semantic link.
4. Rule types added: invariant (hard law), reach, budget/capacity; derived-state discipline stated.
5. Entity kinds added: intent, affordance/opportunity, obligation/directive, project.
6. Runtime status `REACH-LIMITED` added; `STARVED` defined.

### Adopted 2026-09-20 — taxonomy and measurement

Owner decision: build the clean taxonomy even where it is far from current implementation.

7. The full **target domain map** (§7), including movement/navigation, law/crime/enforcement, and content authoring & world assembly as domains.
8. **History/significance, systemic pressure, observation/legibility and evaluation reclassified** as cross-cutting layers rather than domains.
9. **Magic kept as its own domain**, required to wire outward (§4).
10. The project's **five existing rating dimensions** adopted for depth measurement (§9).
11. A **named counterforce required** for any growth-producing mechanism (§11).
12. The **mapping to the 10 scoring pillars** stated wherever the map is used (§7).

### Resolved conflicts

- **Open instability versus quality scoring — resolved 2026-09-20.** Scoring detects logic failure (hard and soft), not misfortune. Destruction of countries, economies, lands and populations scores as positive evidence. See §6/A2.
- **Optionality versus "core ships unflagged" — resolved 2026-09-20.** Standing practice wins: flags are for experiments, migration and rollback only. Core mechanisms ship unflagged, and "replaceable" is a design property (a preserved semantic contract), not a runtime switch.

---

## 16. Decisions log

| Date | Decision | Notes |
|---|---|---|
| 2026-09-20 | **No player, and none planned.** The world stays observed | §3 |
| 2026-09-20 | **Combat: hybrid.** Keep ambient/incidental combat, and give entities a small number of genuine reasons to fight (predation, named threats, defending territory) rather than making all combat decisional | Answers the design question `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` left open. Direction only — no implementation scoping yet |
| 2026-09-20 | **Places come first** among structural gaps: a place must be able to be founded, change kind, be abandoned, be colonised and remember its history | The weakest layer today, and largely independent of the combat gate |
| 2026-09-20 | **Vocabulary amendments adopted** | §15 |
| 2026-09-20 | **This document is standalone**; the original creative-direction page is deprecated and archived, its 8 principles carried here in full | §2 |
| 2026-09-20 | **Quality scoring detects logic failure, not misfortune.** Collapse is positive evidence | §6/A2 |
| 2026-09-20 | **Optionality: standing practice wins.** Core ships unflagged; flags are for experiments, migration and rollback | §15 |
| 2026-09-20 | **Magic is its own domain**, required to wire outward into combat, interaction, body, ecology, places, belief and information | §4, §7 |
| 2026-09-20 | **Build the clean target taxonomy in full**, even far ahead of implementation, so RPG features can be planned against a long roadmap | §7 |
