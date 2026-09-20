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

| Document | Role |
|---|---|
| **This document** | The agreed direction: what the world is, what rules govern it, what we are aiming at |
| [`the_unwritten_world.html`](the_unwritten_world.html) | The original 8 creative principles. **Still in force** — fully preserved here (§2), never replaced |
| [`2026-09-20-simulation-rule-and-taxonomy-review.md`](2026-09-20-simulation-rule-and-taxonomy-review.md) | The local agent's assessment of this direction against the real codebase, with proposed amendments |
| [`2026-09-19-core-rpg-lived-history-growth-brainstorm.md`](2026-09-19-core-rpg-lived-history-growth-brainstorm.md) | Evidence: 21 scenarios traced link-by-link through real code |
| `docs/plans/rpg_design_roadmap/` | What has actually been built (M1–M10) |

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

## 2. The 8 founding principles (unchanged, still governing)

Everything below answers to these. They are restated here in one line each; the full text with examples and failure modes stays in [`the_unwritten_world.html`](the_unwritten_world.html).

| # | Principle | Where it appears below |
|---|---|---|
| 1 | No one hands down the story — it has to be found | §3 causality, §9 quests, §10 authored content |
| 2 | Individuals carry their own trajectory, distinguishable from the aggregate | §5 hybrid progression, §6 significance |
| 3 | Different creatures should be different, not reskinned humans | §4 hybrid agency, §6 bounded ontology |
| 4 | No single loyalty wins by default | §3 agency, §7 power is plural |
| 5 | Places remember what happened to them | §3 identity/persistence, §8 domains |
| 6 | Nothing sits still forever | §6 open instability, §7 loops |
| 7 | A world that feels lived-in without drowning in bookkeeping | §6 causal-value-first, §11 admission test |
| 8 | The world has to tell on itself — legible from outside | §3 information, §6 world reaction |

**Nothing in this document weakens Principle 7 or Principle 8.** The direction below is broader in scope, which makes those two *more* load-bearing, not less: a bigger target vocabulary increases the risk of building precise, invisible things nobody can see.

---

## 3. Core before gameplay

> **Build the simulation core first. Gameplay is a way of interacting with that simulation.**

```
WORLD SIMULATION → AUTONOMOUS AGENTS → OBSERVATION/AUTHORITY/AUTOMATION
→ GAMEPLAY LENS → PLAYER EXPERIENCE
```

The same world might one day support a single-character RPG, party or guild management, kingdom management, indirect political play, god-like influence, or pure observer/chronicle mode. **We are not building those modes now.** We are only avoiding decisions that make them impossible.

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

**Boundary (from the repository):** this applies to *stabilisers*, never to *invariants*. Atomic conservation, determinism and the per-tick hard-law checks must still always hold. "Instability" means the world may change irreversibly, not that its laws may break.

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
DOMAIN → SYSTEM → SUBSYSTEM → MECHANISM → RULE → PARAMETER / CONTENT
```

with **LINK** and **LOOP** operating across the whole hierarchy, and treated as equally important.

- **Mechanism** is the practical unit: testable, ownable, replaceable, and the level at which this project already tracks reality.
- **Parameters are not features.** **Content volume is not system depth.**

### Rule types

Fundamental world law · domain law · materialized abstraction · systemic convention · derived rule · threshold rule · pressure rule · transformation rule · counterforce rule · content rule · exception rule.

### Entity and state types

First-class simulated entity · aggregate entity · resource · condition · relationship · event · knowledge claim.

An aggregate (a population cohort, a regional economy, a culture, an ecosystem) is a legitimate abstraction — a weather system, not a failure. It may be promoted to finer detail when causal value requires it.

### Links are first-class

The clearest lesson from this repository: **systems can exist and still produce no histories, because they are not connected.** Link types worth tracking explicitly:

```
State Feed · Trigger · Conversion · Recognition · Information · Authority
Constraint · Spatial Propagation · Historical Provenance · Reaction · Transformation · Feedback
```

> A system with many internal mechanics and almost no external links is complicated, not deep.

### Loops

Positive (wealth → opportunity → wealth), negative (wealth → visibility → taxation/theft/rivalry), and transformative (environment → adaptation → behaviour → environment).

The goal is **not** to eliminate positive feedback — it is one of the main sources of historically significant entities. Counterforces should come from other world systems wherever practical, and, per A2, they are allowed to fail.

---

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

---

## 10. Knowing what we actually have

"Implemented" is not enough. A mechanism can exist in code with no producer, no consumer, no caller, unreachable thresholds or a disabled flag. The project should always be able to say, per mechanism:

```
MISSING · DESIGNED · EXPERIMENTAL · OFF · DORMANT · STARVED · LIVE · DEPRECATED · REPLACED
```

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

## 15. Open amendments (proposed, not yet agreed)

The local agent's review of this direction against the real codebase proposes several changes to the vocabulary above — including splitting `LINK` into dependency/flow/semantic edges, adding scale, cadence and authority axes, adding invariant/reach/budget rule types, adding intent/affordance/obligation/project entity kinds, adding a `REACH-LIMITED` status, reclassifying history and systemic-pressure as cross-cutting rather than domains, and adding five domains the map omits (movement, content authoring, law/crime, observation, evaluation).

They are **not folded into this document** until the three sides agree. See [`2026-09-20-simulation-rule-and-taxonomy-review.md`](2026-09-20-simulation-rule-and-taxonomy-review.md) §P for the full list and the reasoning, and §O for the conflicts this direction has with current practice.
