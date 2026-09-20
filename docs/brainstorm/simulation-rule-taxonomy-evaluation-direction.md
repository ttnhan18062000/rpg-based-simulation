---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, simulation-quality, content]
---

# Simulation Rule/Taxonomy Evaluation Direction

**A design companion to [`core_rpg_design_direction.md`](core_rpg_design_direction.md), narrowly
scoped to one question: how should the semantics of a Rule or Mechanism eventually be evaluated?**

## Status

This document is **implementation-independent**. It is not an implementation design for SimQ,
`HardLawMonitor`, observability, the mechanism registry, or any evaluator. It does not redesign
scorers, accumulators, events, registry schemas, or runtime hooks. It defines *what should be
true*, *what would count as a violation*, and *what kind of evidence should eventually be
possible* — never *which event type, which class, which threshold*.

**Authority.** Filed at P1 alongside the constitution, because it states real, binding design
principles rather than analysis or evidence — but it is a **companion**, not a replacement:
`core_rpg_design_direction.md` remains the single statement of what the world is; this document
only extends it into one dimension (evaluation) it deliberately left open (§15 of that document:
"the soft-failure definition… to be sharpened later").

| Document | Role |
|---|---|
| [`core_rpg_design_direction.md`](core_rpg_design_direction.md) | Defines what the world and its taxonomy *are* |
| **This document** | Defines *how the semantics of those rules should eventually be evaluated* |
| [`2026-09-20-simulation-rule-and-taxonomy-review.md`](2026-09-20-simulation-rule-and-taxonomy-review.md) | Repository-grounded reasoning and assessment behind both of the above |
| `tmp/simulation-quality-system-review.md` | Current-state evidence for §2 below (local review artifact, not part of the tracked design set) |

---

## 1. The core separation

```
WORLD DESIGN
Domain → System → Mechanism → Rule → Semantic Contract → Validation Intent / Claims
                              ↓
CROSS-CUTTING EVALUATION
How do we establish evidence that the declared semantics hold?
                              ↓
IMPLEMENTATION (illustrative only, not prescribed)
SimQ · HardLawMonitor · observability · scenario tests · property tests · replay ·
registry verification · other instrumentation not yet chosen
                              ↓
EVIDENCE
                              └──── feedback ────→ explicit design review (not silent redefinition)
```

> **Validation semantics belong to simulation design. Validation instrumentation belongs to
> implementation.**
>
> **Evaluation Semantics** defines what must hold, what constitutes a violation, and what must
> eventually be observable *in principle*. **Evaluation Implementation** defines how evidence for
> that is actually produced, collected, and assessed. Neither this document nor any future
> evaluator description should make Evaluation Semantics itself responsible for a concrete
> evidence structure or detector — that responsibility belongs one layer down, always.
>
> **The relationship is not strictly one-way.** Implementation and evaluation evidence must never
> *silently* redefine world semantics — an evaluator cannot quietly change what a rule means just
> because that's easier to measure. But evidence *may* expose a contradiction, an ambiguity, a
> missing concept, or an invalid assumption in the semantics above it — and when it does, that
> triggers an **explicit** Rule/Taxonomy revision through the normal design-authority process, not
> a silent one. The constitution is stable, but it is not unfalsifiable.

A Rule or Mechanism describes **what must be true**, never **how a particular evaluator will
detect it**.

```
Rule: an agent may only make a knowledge-dependent decision from information available to it.

Good validation intent (this stage):
  A decision must not depend on unavailable knowledge.
  A violation should eventually be detectable.

Too implementation-specific for this stage:
  Emit KNOWLEDGE_USED. Compare field X against cache Y. Deduct 10 SimQ points.
```

---

## 2. Evaluation-aware, not evaluation-driven

> **Architecture should eventually expose enough evidence to validate important semantic
> contracts, but world rules must not be shaped around what the current evaluator happens to
> measure easily.**

The future implementation may need provenance, observability, replayability, or inspection
support. That requirement must never become *"the world rule exists this way because SimQ expects
this event shape."* If a semantic contract and an evaluator's convenience ever pull in different
directions, the semantic contract wins — the evaluator adapts, not the rule.

---

## 3. Current evaluation landscape

Several related but genuinely distinct capabilities already exist. Recorded here as **evidence
and reusable infrastructure**, never as a constraint on what evaluation must become:

- **Simulation Quality (SimQ)** — per-run, per-pillar activity/health scoring, event-driven, zero
  measured engine overhead, config-driven weights.
- **`HardLawMonitor`** — six cheap, dirty-set-scoped, per-tick invariant checks (non-negative HP/
  readiness/gold/stamina, finite position, no tile-occupancy collision), fail-fast in
  DEBUG/CERTIFICATION modes.
- **Corpus/scenario infrastructure** — a four-tier world corpus (Unit / End-to-end / Stress /
  Regression) already built for a different purpose (calibration), whose *shape* is reusable for
  scenario-level validation.
- **Mechanism registry verification / claims-as-tests direction** — a live, separate initiative
  already building a "claim → detector" pattern for mechanism-level assertions.
- **Observability infrastructure** — the event bus, envelopes, and persistence SimQ itself is
  built on.
- **Regression anchors** — a two-dimensional (letter-band + score-tolerance) statistical mechanism
  for detecting unintended scoring drift.
- **Activity/balance metrics** — the bulk of SimQ's ~77+ scoring rules, genuinely useful for
  tuning, not for correctness.

**The important finding, carried forward from the current-state review:** existing SimQ is
primarily a mature simulation-health / activity / balance monitoring system. It already contains
several real causal-quality checks — a declared war never followed by conflict, combat initiated
but never resolved, the same goal re-selected with no new reasoning, an entity's present capability
failing to reflect a documented past event — but **health/activity and causal correctness
currently sit mixed together in the same per-pillar score**, and roughly half of all committed
regression-anchor grades (45.3%, by direct count) currently mean "no event ever fired" rather than
any judgment about quality at all. `HardLawMonitor` already correctly and narrowly owns hard
invariants. None of this dictates what evaluation becomes below — it establishes what already
exists to build on, and where the real conceptual gap is.

---

## 4. Future evaluation semantics

Seven dimensions. None of them is a metric, a class, or a schema — each is a question a future
evaluator, whichever one is eventually chosen, should be able to answer.

### 4.1 Hard correctness

Does the simulation violate a fundamental invariant: impossible state, conservation failure,
invalid ownership, invalid position, a determinism failure where determinism is required. These
stay conceptually distinct from balance or from any particular world outcome — a hard failure is
never a matter of degree or taste.

### 4.2 Soft / causal correctness

> A soft failure is a decision, transition, derived result, or causal chain that is technically
> executable but violates a declared semantic contract of the simulation.

Examples: acting without required capability; using knowledge the entity cannot possess; violating
a declared precondition; violating authority (a proposer committing what only the authoritative
path may commit); a derived value that stops responding to its own declared driver; a required
causal follow-through that never occurs; a learning or adaptation rule that is simply ignored.

**A soft failure is never "the agent failed to choose the single expected action."** Autonomous
agents may have many valid choices. Evaluation tests **admissibility, preconditions, knowledge
scope, capability, authority, and causal consistency** — never scripted behaviour. An agent that
chooses differently from what a human observer expected has not failed anything; an agent that
chooses an action its own declared preconditions forbid has.

### 4.3 Observed reach

Does this rule or mechanism actually participate in real simulation — was it ever reached, how
often, for which entities, regions, modes, or scenarios?

**Evaluation supplies evidence. It does not classify.** The lifecycle status a mechanism carries —
`MISSING` / `STARVED` / `REACH-LIMITED` / `LIVE` — is conceptually owned by the mechanism
registry and its governance process, not by whatever evaluator happens to produce the reach
evidence. An evaluator that observes "this mechanism fired zero times in this run" has done its
job completely; deciding what that means for the mechanism's standing is a separate, governance-
level act.

### 4.4 Causal connectivity

Do declared links between mechanisms actually complete?

**Correlation between two mechanisms' activity is not evidence of causal connectivity.** It may be
useful telemetry — worth having, worth watching — but it never establishes that one caused the
other. The evidence connectivity actually needs is:

```
declared causal/semantic link
  + producer consequence (the link's stated cause actually occurred)
  + consumer reaction (the link's stated effect actually followed)
  + a causal/provenance relation between them where one is needed
```

Some important multi-step chains will only ever be checkable at the scenario level (§6), because
no single-event signal can establish that a chain of several links held end to end within one run.

### 4.5 Persistent / historical consequence

Can something that happened previously alter later state, capability, knowledge, behaviour,
relationships, institutions, places, or world reaction?

```
entity survives repeated fire exposure → qualifying history exists
  → adaptation develops → future behaviour/capability changes
```

**Simply recording a historical event is not enough.** The historical state must have a possible
downstream consumer wherever a rule claims one exists. A chronicle entry that is written and never
read by anything satisfies §4.4's producer half and fails its consumer half — recording history and
history mattering are two different claims, and only the second one is what "persistent
consequence" means.

### 4.6 Emergent capacity

Can valid interacting rules create meaningful trajectories that were not directly authored?

Do not reward randomness itself, and do not reward a dramatic outcome merely for being dramatic.
The property that matters is:

```
unplanned trajectory + valid causal chain
```

A wolf becoming a legend through an unbroken chain of real causes is emergent capacity. A wolf
becoming a legend because a die roll said so, with no causal chain behind it, is not — however
dramatic either looks from the outside.

### 4.7 Health / activity

Combat volume, economic activity, population size, market activity, stability, faction
concentration, progression rate. These remain genuinely useful diagnostics and tuning signals.

> **Health/activity is not equivalent to simulation correctness.**

They answer "is this world lively and balanced," which is a real and useful question — just a
different one from every question in §4.1–§4.6.

---

## 5. Outcome neutrality

> **Simulation quality evaluates causal validity, not whether the resulting world is comfortable,
> prosperous, balanced, peaceful, violent, stable, or collapsed.**

```
valid collapse       ≠ quality failure
valid stability      ≠ quality failure
collapse itself      ≠ quality bonus
dramatic emergence   ≠ quality bonus by itself
```

Precisely stated, **collapse carries no polarity of its own, in either direction.** All polarity
comes from whether the *process* that produced the outcome was itself causally valid:

```
rules behaved correctly     → quality evidence
rules contradicted themselves → failure evidence
```

A peaceful world and a ruined world may both be high-quality simulation outcomes; a peaceful world
and a ruined world may both be low-quality ones, if either was produced by a rule contradicting
itself along the way. The outcome tells you nothing on its own — only the causal chain behind it
does. This is a sharper statement than "collapse should score positive when causally valid" — that
phrasing still treats collapse as an axis with a preferred value. It has none.

---

## 6. What belongs beside a Rule or Mechanism

Not a metadata schema — a list of the kinds of things that will eventually need stating, in
whatever form the taxonomy work settles on:

| Concept | What it captures |
|---|---|
| **Semantic Contract** | What the rule means. |
| **Preconditions** | When it is allowed to apply. |
| **Allowed / Forbidden Outcomes** | Where meaningful — not every rule has these. |
| **State Ownership** | Which system owns the authoritative truth (the direction doc's own canonical-state-ownership rule, restated in evaluation terms). |
| **Inputs / Outputs** | Semantic, never implementation-specific. |
| **Reach** | Where the rule can logically apply. |
| **Consumers / Links** | What can consume its consequences. |
| **Validation Intent** | What must eventually be possible to verify. |
| **Failure Semantics** | What would demonstrate the rule violated its own declared meaning. |

### Validation Claims

An implementation-independent statement of what is expected to be provable later, not yet a test:

```
An item cannot have two authoritative owners.
An entity cannot perform an action without required capability.
Information must not propagate beyond a valid information path.
A learned adaptation must have qualifying causal history.
A place declared abandoned must remain historically identifiable unless explicitly destroyed
  by world rules.
A declared semantic link must have a possible consumer.
```

A Validation Claim states *what we expect to be provable later* — it commits to nothing about how.

---

## 7. Proportional validation effort

Not every rule needs the same weight of validation. Avoid turning the taxonomy into a validation
bureaucracy.

**Strong candidates for a mandatory claim:** hard invariants; authoritative state transitions;
cross-domain links; important derived rules; mechanisms whose failure can silently corrupt the
world; mechanisms claiming persistent consequence; mechanisms involved in a canonical systemic
scenario (§9).

**Lighter requirements are appropriate for:** simple content; tuning parameters; purely cosmetic
presentation; obvious local calculations already covered by a stronger enclosing contract.

> **Validation depth should scale with causal importance, blast radius, and invisibility of
> failure.**

A rule whose failure would be silent, wide-reaching, and hard to detect earns a claim. A rule
whose failure would be loud, narrow, and obvious to anyone watching does not need one just to have
one.

---

## 8. Black-box before white-box

Prefer implementation-independent behavioural claims wherever one is possible.

```
Black-box (preferred at this stage):
  When sustained scarcity exists, valid migration pressure can eventually change.

White-box (implementation-specific, not this stage):
  ScarcitySystem emitted X, then MigrationSystem consumed event Y through handler Z.
```

White-box validation has real, legitimate uses — just later, and for narrower purposes: debugging,
authority boundaries, performance-sensitive contracts, exact invariants, implementation-level
regression detection. At the Rule/Taxonomy stage, the black-box claim is always the one that
belongs here; the white-box detector is an implementation decision for whoever builds the
evaluator.

---

## 9. Relationship to canonical scenarios

Canonical scenarios (already traced as evidence in
[`2026-09-19-core-rpg-lived-history-growth-brainstorm.md`](2026-09-19-core-rpg-lived-history-growth-brainstorm.md))
are the natural home for validating a *chain* of links at once, where no single-event signal can:

```
ordinary wolf → historically significant threat
wealth → capability → institutional influence
settlement → abandonment → successor occupation → remembered place
belief → following → institution
artifact → provenance → relic → world reaction
```

Their purpose is never to enforce one exact story. They test whether the expected **causal
possibilities and links exist** — multiple valid outcomes must remain possible for any of them.
A scenario "fails" only if the causal chain it names turns out to be impossible to complete at
all, never because one particular run happened to end differently from another.

---

## 10. Relationship to SimQ, and to registry/governance

**SimQ is one existing evaluation capability that may later implement part of this philosophy —
not the definition of the philosophy itself.** This document's semantics must never depend on
SimQ's current scoring format, and not every Validation Claim needs to become a score. Possible
future representations for a claim's evidence include, without any one being required:

```
pass/fail invariant · coverage/reach evidence · scenario result · causal trace ·
diagnostic metric · confidence/evidence record · quality dimension
```

A single numeric score is not required anywhere in this model.

**Evaluation and governance are two different acts, not two names for one act.** §4.3 already
draws this line for reach specifically; it holds generally. An evaluator's job ends at producing
evidence — *this fired, this many times, in these conditions* — or a verdict on one bounded claim —
*this specific precondition held, or it didn't*. Deciding what a pattern of evidence means for a
mechanism's standing, priority, or disposition (build it further, wire it, retire it, leave it as
designed-not-built) is a governance act, and belongs to whichever process already owns that
decision — today, the mechanism registry. Evaluation never adjudicates; it only ever produces the
evidence adjudication needs.

---

## 11. What this document does not do

It does not redefine SimQ's implementation, mandate any one instrumentation choice, create a
metadata schema, or produce tickets or milestones. It does not decide *when* any of this gets
built. It exists so that, whenever evaluation implementation work does begin, it starts from an
agreed statement of what correctness means — rather than inheriting whatever an existing scorer
happened to already measure.
