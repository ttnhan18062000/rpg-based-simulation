---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, world]
---

# Simulation Rule / World Law Design — Preparation

**A short, normative preparatory artifact answering one question: how will we design the actual
rules governing the world in the next phase?** It contains no rule catalog. It is the methodology
for writing one.

## Status

Companion to [`core_rpg_design_direction.md`](core_rpg_design_direction.md) (what the world is)
and [`simulation-rule-taxonomy-evaluation-direction.md`](simulation-rule-taxonomy-evaluation-direction.md)
(how its semantics get evaluated). This document sits between them and the actual work: it
defines the boundary, the test, the shape, the order, and the readiness bar for writing World
Laws — never the laws themselves.

| Document | Role |
|---|---|
| [`core_rpg_design_direction.md`](core_rpg_design_direction.md) | What the world is |
| [`simulation-rule-taxonomy-evaluation-direction.md`](simulation-rule-taxonomy-evaluation-direction.md) | How its semantics get evaluated |
| **This document** | How we will design the actual rules, next |

---

## 1. Current status of Simulation Rule design

Stated plainly, so the next phase doesn't start from a false premise:

> **We have largely designed the grammar for describing world laws. We have not yet
> systematically written the laws of the world.**

**Mature / mostly settled:**

```
Vision and world philosophy
Fundamental World Contract v0.1
Structural taxonomy (Domain → System → Mechanism → Rule → Parameter/Content)
Rule-type taxonomy
Entity/state vocabulary
Domain map
Link/loop vocabulary
Scale / cadence / authority axes
Evaluation-semantics direction
```

**Not yet designed systematically:**

```
Actual World Law Catalog
Domain-by-domain Rule Catalog
Cross-domain causal contracts
Detailed transformation laws
Detailed reach laws
Detailed pressure/counterforce relationships
Systematic Rule ↔ Mechanism mapping
```

The presence of domain names, a rule-type taxonomy, and a target map does **not** mean the actual
rules are complete, or even started. Every domain in the target map is a place a rule *could*
live — none of them yet has one written.

---

## 2. The rule-design boundary

The purpose of this boundary is to stop every implementation detail from becoming a "world rule."
Not every term below needs a new name if the existing taxonomy already has precise terminology —
the goal is the semantic separation, not the vocabulary.

| Level | What it is | Example |
|---|---|---|
| **World / Domain Law** | A semantic truth about how the simulated world works. | Knowledge requires a valid acquisition path. |
| **Rule** | A meaningful semantic constraint or transformation within a domain/mechanism. | An entity may act on a specific fact only if that fact is available through its own knowledge state. |
| **Mechanism** | A process that realizes one or more rules. | Rumor propagation; perception; teaching; report transmission. |
| **Derived State / Abstraction** | A representation calculated or materialized from other world state. | Scarcity ratio; threat classification; XP; reputation score. |
| **Parameter / Tuning** | A number governing strength, probability, duration, or threshold. | Rumor decay = 0.1; fire damage multiplier = 1.4. |
| **Content** | A specific authored instance. | Fireball spell; Iron Sword; Goblin species; Temple of X. |

### The test for "this deserves to be a Rule"

Before anything enters the future Rule Catalog:

1. Does this describe how the **world behaves**, rather than how code is organized?
2. Does violating it materially change simulation meaning?
3. Does it constrain possible state, action, transformation, or consequence?
4. Is it more than a tuning number?
5. Does it have at least one meaningful producer/consumer or causal consequence?
6. Does another rule already express the same semantic truth?
7. Is it universal, domain-scoped, mechanism-scoped, or merely content-specific?
8. **Would the world still conceptually work if its implementation changed completely?**

Question 8 is the sharpest test. If the honest answer is *"no, because this only exists due to
the current class/event implementation,"* it is not a world rule — it's an implementation detail
wearing a rule's name.

### The future Rule shape — conceptual only, not a schema

A future Rule entry will probably need to express some subset of: name/identity, domain,
system/mechanism context, rule type, meaning/semantic contract, scope, preconditions,
allowed/forbidden behaviour, inputs, outputs/consequences, state owner (where relevant), reach,
cross-domain links, persistence, transformation implications, counterforces/limits (where
relevant), failure semantics, validation intent, open questions.

**Not every rule uses every concept.** A content-scoped rule and a fundamental world law need
wildly different amounts of this list filled in. Proportional detail, never boilerplate.

### Ownership within a Rule: three distinct concepts, not one

**Corrected, 2026-09-21.** "State owner" in the field list above is easy to over-read as *"which
domain owns this rule,"* as if a rule needed exactly one owner the way a durable state field does.
It doesn't. **Canonical ownership applies to durable authoritative state, not necessarily to the
Rule itself** — the constitution's own canonical-state-ownership principle (§7) was always a
statement about *state*, and a Rule is not state; it can legitimately reference several owned
things at once. Three separate concepts, easily conflated, need to stay distinct:

| Concept | Question it answers |
|---|---|
| **Semantic Home** | Where is this rule catalogued, so it has one clear primary location and we never duplicate it elsewhere? |
| **State Ownership** | For each durable state concept the rule *references*, which domain/system is authoritative for it? |
| **Participating / Linked Domains** | Which other domains produce inputs to this rule, consume its outputs, constrain it, or react to its consequences? |

A rule scoped to one domain has all three concepts trivially aligned:

```
Rule:            Information requires a valid acquisition path.
Semantic home:   Perception / Knowledge / Information
State owner:     Knowledge domain owns the entity's knowledge claims.
Linked domains:  Agency, Politics, Religion, Social
```

A genuinely cross-domain rule may legitimately span **more than one** state owner — and that is
not a defect to resolve, it's the whole point of a cross-domain rule existing:

```
Rule:                Death can trigger succession.
Semantic home:       Family / Lineage / Succession
Input state owner:   Life/Body owns death state.
Output state owner:  Lineage owns succession state.
Semantic link:       Life → Lineage
```

For a rule like this, *"which single domain owns the whole rule"* is the wrong question. The
right three are: where does this rule belong in the catalog (its semantic home); who owns each
authoritative fact it touches (possibly more than one domain); and what cross-domain semantic
link does the rule itself define (the relationship those owners' facts stand in, to each other).

> **Every durable state concept referenced by a rule must have an unambiguous authoritative
> owner. Every rule should have a clear semantic home for cataloguing. But a cross-domain rule may
> legitimately span multiple state owners and participating domains — that is not an ambiguity
> to eliminate, it is what makes the rule cross-domain.**

This is a clarification, not a new blocker, and it doesn't change the entry-criteria checklist in
§4 — "canonical state ownership principle is accepted" already meant *state* ownership, correctly
understood; this section only makes explicit that a rule's own catalog location is a separate
question from the ownership of the facts it references.

---

## 3. Design method for the next phase

### 3.1 World-rule design order (design-area dependency order, not implementation sequencing)

**Terminology corrected, 2026-09-21.** This was previously called a "domain order." That's
imprecise: `Domain` is one specific level in the structural taxonomy (§2 above), and not every
entry below is a Domain — item 19 is explicitly the *cross-cutting* history/significance/
propagation layer (`core_rpg_design_direction.md` §7's own "Cross-cutting layers" table, not its
domain map), and item 15 deliberately merges two of that map's real domains (Politics/authority/
war and Law/crime/enforcement) into one design-sequencing step, because they need to be reasoned
about together even though they're catalogued separately. Calling this a **design-area** order,
never a domain order, keeps `Domain ≠ Scale ≠ Cross-cutting Layer` intact instead of blurring them
for convenience.

```
1. Substrate / foundational laws
2. Space & reach
3. Movement
4. Life / body / survival
5. Ecology / population
6. Perception / knowledge / information
7. Agency / decision
8. Capability / progression
9. Objects / ownership / material culture
10. Economy / resources
11. Combat / conflict
12. Social / relationships
13. Family / lineage
14. Organizations / institutions
15. Politics / authority / law
16. Places / settlements / territory
17. Culture / belief / religion
18. Magic / supernatural
19. Cross-domain history / significance / propagation
```

This orders *design dependency*, never build order or milestone scheduling — a later design area
in this list can reasonably reuse a semantic concept a foundational one already had to define
(e.g. ownership, before economy needs it), but nothing here says economy must be *built* before
combat.

Repository evidence mostly confirms this order rather than contradicting it, with one genuine
tension worth naming rather than smoothing over: the (Places, settlements & territory) domain
this session's evidence found **weakest** — its runtime immutability blocks the vision's own
headline scenario — sits at position 16, quite late, because *settlement standing, abandonment
and colonization* genuinely depend on population, economy and institutions existing first, per
this same dependency logic. But the specific missing **primitive** underneath that finding — a
place simply having a mutable kind at all, with no runtime update path today — is a Space &
environment concern, position 2, and does not need to wait for anything downstream. The lesson: a
domain's full design position in this order and its most urgent missing primitive can legitimately
sit at different points in the list. This order should not be read as "fix nothing about Places
until 15 other design areas are settled" — only as "Places' *full* semantic design depends on
domains that come first."

### 3.2 Foundations come first

The next phase should start by expanding the current Fundamental World Contract. Likely
foundational law families, not yet written in detail:

```
Identity          State ownership     Time              Causality
Authority         Space / topology    Reach             Capability
Cost              Information / truth Persistence       Transformation
Deterministic randomness              Resource / conservation semantics
Capacity / limits Provenance
```

### 3.3 Per-domain investigation order

For each future domain, the same order, every time:

```
A. What fundamental/domain laws apply here?
B. What state exists conceptually?
C. What can change that state?
D. What transformations are possible?
E. What reach constraints exist?
F. What pressures accumulate?
G. What thresholds matter?
H. What counterforces / limits exist?
I. What other domains consume its outputs?
J. What inputs does it depend on?
K. What histories can persist?
L. What semantic failures would make this domain incorrect?
```

The governing question throughout is *"what must be true for this part of the world to behave
coherently?"* — never *"what classes or features should this domain have?"* Then, once A–L are
answered, identify candidate mechanisms.

**Corrected, 2026-09-21 — this is not an absolute prohibition on naming a mechanism early.** The
actual discipline is: **semantics first, mechanism decomposition second.** Do not derive world
semantics from a desired mechanism decomposition — but existing or provisional mechanism names may
be referenced throughout A–L as repository evidence; only their *boundaries and structure* wait
for the semantics to be understood first. Concretely:
```
Bad:  We already have ReputationSystem → therefore the world rule must follow
      ReputationSystem's current behaviour.
Good: What does recognition/reputation mean in the world? → define the semantic rules
      → inspect ReputationSystem as evidence → determine whether it already satisfies,
      partially satisfies, or conflicts with those rules.
```
The repository stays evidence, existing mechanisms, constraints, lessons, and counterexamples
(§3.7) — never the authority defining the target semantics.

### 3.4 Cross-domain rules are first-class, not afterthoughts

Some of the most important rules exist **between** domains, and the next phase must not produce
isolated per-domain documents that bury them:

```
injury            Combat → Life/Body
scarcity          Economy → Agency / Migration
ownership         Objects → Economy / Law / Social
knowledge         Information → Agency / Politics / Religion
history           Experience → Progression / Reputation / World Reaction
place abandonment Population / Politics → Place → Ecology / History
```

The future Rule Catalog must make these links visible as semantic relationships, never bury them
as implementation dependencies discovered by accident later.

### 3.5 Avoid universal-rule overreach

> Shared conceptual grammar does not imply shared implementation or identical rules.

Wolf progression, merchant progression, city progression, religious-institution progression, and
artifact progression may obey comparable causal ideas — state → experience → adaptation →
transformation — while requiring completely different laws and mechanisms. **Do not invent a
`UniversalProgressionRule` or a universal state model merely to make the taxonomy look symmetrical.**
Symmetry in the *grammar* is the goal; symmetry in the *implementation* is not, and forcing it
would violate the direction's own Principle 3 (different creatures, not reskins).

### 3.6 Abstraction principle

> **Abstract semantics early; abstract implementation late.**
> **A stable foundation should make change cheap, not pre-design every possible future change.**

At this phase, abstraction clarifies meaning, ownership, boundaries, links, contracts, and
replaceability expectations — never generic frameworks built ahead of real evidence of variation.

### 3.7 Relationship to the existing repository

The repository is used as evidence, existing mechanisms, known constraints, lessons, and
counterexamples — never as the ceiling of the target world model. For each domain, the actual
Rule Catalog work (not this preparation pass) will eventually distinguish, per rule: the target
semantic rule, current repository support, any mismatch or missing mechanism, and any existing
implementation that already satisfies it. **This preparation document only establishes that
method — it does not begin the mapping.**

### 3.8 Relationship to evaluation

```
Rule/Law Design       → defines semantics
Evaluation Direction  → defines what must hold, what constitutes violation,
                         and what should eventually be observable
Implementation        → later determines how evidence is collected
```

No implementation-specific evaluation requirement belongs in Rule/Law design, and none is added
here. See `simulation-rule-taxonomy-evaluation-direction.md` for the full evaluation model,
including the corrected outcome-neutrality principle it and the constitution both now state:
world outcomes carry no quality polarity of their own; only causal validity does.

---

## 4. Entry criteria for beginning the World Rule Catalog

```
[x] Fundamental vs domain vs mechanism-level rule distinction is clear         (§2 above)
[x] Rule vs mechanism vs parameter/content distinction is clear               (§2 above)
[x] Cross-domain link representation is conceptually clear                    (§3.4 above)
[x] Canonical state ownership principle is accepted                          (core_rpg_design_direction.md §7)
[x] Evaluation semantics boundary is accepted                                (simulation-rule-taxonomy-evaluation-direction.md)
[x] Future Rule entry shape is understood without becoming a rigid schema     (§2 above)
[x] Design order is agreed                                                   (§3.1, §3.3 above)
[x] Repository evidence is understood as input, not authority over the target model (§3.7 above)
[x] No major P1 contradiction remains                                        (see the wording corrections applied 2026-09-21)
```

All nine criteria are satisfied.

> **READY TO BEGIN WORLD RULE CATALOG DESIGN.**

This does not mean every question about the world's rules is answered — it means the *methodology*
for answering them is settled well enough that the next phase can begin writing rules without
another conceptual cleanup round first.

---

## 5. What this document does not do

It does not write the Fundamental Law catalog, enumerate any rules, design detailed domain
mechanics, create implementation classes or interfaces, map every existing mechanism against the
target model, create tickets or milestones, design persistence schemas, redesign SimQ, define
event formats, or set numerical parameters. All of that belongs to the phase this document exists
to make possible — none of it to this one.
