---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, schema]
last_verified: "2026-09-23"
---

# RPG Simulation Core Semantic Control Plane (external-AI draft — superseded)

**Provenance note (added 2026-09-23, moved here from `tmp/rpg-core-high-level-design-ext-ai.md`).**
This is the raw, unedited third draft an external AI produced for the Simulation Rule →
Implementation Mapping phase, preserved for provenance. It is not itself the epic. Two earlier
drafts it supersedes were reviewed against real repo state in `tmp/semantic-control-plane-review.md`
(8 open items found); this draft resolves all 8, verified point-by-point in that review's
addendum. **The actual epic, independently authored from this draft's design (not a copy), is
`docs/plans/simulation_semantic_control_plane/`** — read that first. This file is historical
source material only.

---

## Official Architecture Direction and Agent Operating Model

This document establishes the target direction for managing, implementing, maintaining, troubleshooting, validating, and evolving the **RPG simulation core**.

Its scope is deliberately limited to the simulation core.

It does not govern:

```text
UI
rendering
presentation
editor tooling
asset production
general application infrastructure
gameplay-lens UX
```

except where those systems directly provide evidence about simulation-core behavior.

---

# 1. Why this exists

The project now has substantial architectural knowledge:

```text
World Rule Catalog
Mechanism Registry
systems
domains
implementation code
scenario evidence
verification evidence
design/decision documents
```

Each is valuable.

The long-term risk is that maintaining correctness requires an agent to repeatedly rediscover:

```text
which document is authoritative
which logic is intended
which mechanism already exists
which domain owns a fact
whether observed behavior is a bug
whether missing behavior is actually required
whether code exists but is unwired
whether something is implemented but behaviorally ineffective
whether a result is semantically valid but merely surprising
```

The solution must not be:

```text
more summary documents
more manually-maintained matrices
one giant architecture document
one giant god registry
```

The target is:

> **One authoritative owner for each kind of fact, one connected semantic model across those facts, and one progressively-disclosed query surface for agents and humans.**

---

# 2. Fundamental architectural principle

Single Point of Truth means:

> **single ownership of a fact**

not:

> **single physical file containing every fact**

The project should behave like a normalized knowledge model.

Example:

```text
World Rule Catalog
owns semantic truth.

Mechanism Registry
owns mechanism identity, status, implementation binding,
functional dependencies, and verification metadata.

Source code
owns implementation truth.

Runtime/scenario evidence
owns observed-behavior truth.

Existing intentional-divergence mechanisms
own deliberate deviations where applicable.
```

Generated reports and dashboards own no architectural truth.

They are projections.

---

# 3. The five truth layers

Keep these concepts permanently distinct.

## 3.1 Semantic truth

Question:

> What is the simulated world supposed to mean?

Owned by:

```text
World Rule Catalog
```

Examples:

```text
claim ≠ control
knowledge ≠ world truth
ownership ≠ possession
magic ≠ causality exception
```

---

## 3.2 Realization truth

Question:

> What simulation mechanisms currently exist to realize those semantics?

Owned primarily by:

```text
Mechanism Registry
```

Examples:

```text
done
partial
gap
orphan
gated
skeleton
```

---

## 3.3 Implementation truth

Question:

> What code currently implements a mechanism?

Owned by:

```text
source code
```

with Mechanism Registry bindings indexing it.

---

## 3.4 Evidence truth

Question:

> What has actually been demonstrated?

Examples:

```text
code trace
scenario
corpus run
census
```

Keep:

```text
implemented
≠
runtime observed
```

and:

```text
executed
≠
behaviorally effective
```

---

## 3.5 Delivery / accepted-divergence truth

Question:

> Does the current product actually claim that this semantic must be realized now?

Do not introduce a new Conformance Profile system yet.

First reuse and reconcile existing concepts such as:

```text
intentional divergences
scope-deferred semantics
explicit current-product scope
```

Only introduce another conformance abstraction if real operational usage later proves those existing concepts insufficient.

---

# 4. World Rules remain normative

The World Rule Catalog is now the semantic constitution for the RPG simulation core.

It answers:

```text
what must be true
what may be true
what concepts are distinct
what causal relationships are valid
```

Repository implementation does not redefine Rules.

Mechanism Registry does not redefine Rules.

Existing code does not redefine Rules.

Unexpected simulation output does not redefine Rules.

If implementation convenience conflicts with a frozen Rule:

```text
implementation changes
```

unless an explicit semantic revision process changes the Rule.

---

# 5. Do not introduce a FORBIDDEN modality yet

The frozen Catalog currently operates with:

```text
REQUIRED
PERMITTED
```

Do not add `FORBIDDEN` merely because it is theoretically convenient.

A required invariant can already express prohibition:

```text
REQUIRED:
claim and control remain distinct

therefore:
silently collapsing them is invalid
```

Introduce a new modality only if real future usage proves REQUIRED/PERMITTED insufficient.

---

# 6. Mechanism Registry remains focused

Keep `registries/mechanisms.yaml` responsible for its existing concepts:

```text
mechanism identity
layer
systems
functional depends_on
state
implemented_by
verification
```

Do not turn it into the entire Semantic Control Plane.

Especially preserve the narrow semantics of:

```text
depends_on
```

It means:

> this mechanism cannot produce a meaningful result without the dependency existing/having run.

It does not mean:

```text
execution order
call direction
containment
causal propagation
information flow
state ownership
system membership
```

Do not overload it.

---

# 7. Rule ↔ Mechanism mapping

Introduce a sibling semantic mapping layer connecting frozen Rules to actual mechanisms.

This relationship is:

```text
many Rules ↔ many Mechanisms
```

Never assume:

```text
1 Rule = 1 Mechanism
```

or:

```text
1 Mechanism = 1 Rule
```

The mapping must answer:

> Which mechanisms participate in realizing this Rule?

and:

> Which Rules constrain or explain this mechanism?

Do not generate the Cartesian product:

```text
172 Rules × 93 mechanisms
```

Only record meaningful relationships.

Unmapped relationships remain:

```text
UNKNOWN
```

not automatically:

```text
MISSING
```

---

# 8. Mapping starts as baseline, not as a gated research project

Do not stop RPG-core work until the entire mapping exists.

Do not require an ROI proof before establishing it.

The initial state may legitimately be:

```text
Rules:       known
Mechanisms:  known
Mappings:    mostly UNKNOWN
Evidence:    existing partial baseline
```

That is already useful.

The control plane should improve through actual engineering work.

Normal tasks should enrich it incrementally.

---

# 9. First slice vs pilot

Use a small coherent domain such as:

```text
Territory / Control
```

as the **first operational slice**.

Its purpose is:

```text
establish the first real data shape
find obvious schema friction
exercise actual workflow
produce first management view
```

Its purpose is not:

```text
prove whether the entire Control Plane deserves to exist
```

After the first slice, continue incrementally.

Do not wait for a perfect evaluation methodology.

---

# 10. Semantic Control Plane logical model

Conceptually:

```text
                         RPG SIMULATION CORE

                              DOMAIN
                                │
                                ▼
                              RULE
                                │
                         semantic mapping
                                │
                                ▼
SYSTEM ─────────────────── MECHANISM
                                │
                                ▼
                         IMPLEMENTATION
                                │
                                ▼
                            EVIDENCE
                                │
                                ▼
                    MANAGEMENT / AGENT VIEWS
```

Additional cross-cutting facts include:

```text
state ownership
scenario coverage
causal chains
intentional divergence
known gaps/conflicts
runtime outcomes
```

Do not assume each needs its own physical registry.

Promote concepts to canonical structured data only when they have clear ownership and recurring operational value.

---

# 11. State ownership must remain queryable

Agents need to answer:

> Who owns this durable fact?

Examples:

```text
Body owns wounds
Knowledge owns individual belief
Social owns relational state
Property owns ownership facts
Territory owns claim/control relations
Place owns persistent place state
Magic owns an ongoing supernatural condition,
not every consequence caused by magic
```

Initially this may be derived/indexed from frozen Rules and mapping data.

Do not immediately create a large separate State Concept registry unless real use demonstrates that a first-class tier is necessary.

The capability must exist.

The storage abstraction may evolve.

---

# 12. Management Plane

The Semantic Control Plane must support not only architecture queries but project-state management.

Humans and agents should be able to understand:

```text
how deep a domain is designed
how much is implemented
how much is actually realized
how much is verified
how much composes end-to-end
what simulations actually produce
where known gaps/conflicts/unknowns remain
```

The Management Plane is a generated projection.

It does not become another source of truth.

---

# 13. Never use one global completion percentage

Do not report:

```text
Territory: 63% complete
```

as the authoritative picture.

Keep independent axes.

At minimum:

```text
DESIGN
REALIZATION
IMPLEMENTATION
VERIFICATION
INTEGRATION
OBSERVED OUTCOME
```

A domain may legitimately be:

```text
Design           mature
Realization      partial
Implementation   substantial
Verification     weak
Integration      weak
Observed outcome sparse
```

That distinction is valuable.

---

# 14. Domain depth is causal depth, not Rule count

Do not use number of Rules as a depth metric.

For each major domain, evaluate causal coverage such as:

```text
STATE
Does the domain have coherent authoritative state?

CHANGE
Can that state change through declared mechanisms?

INPUT PRESSURE
Can other domains meaningfully affect it?

OUTPUT CONSEQUENCE
Can it affect other domains?

CONSUMPTION
Do real consumers use its state?

HISTORY
Can consequences persist / produce provenance?

INFORMATION
Can relevant actors learn about it through valid paths?

CROSS-DOMAIN
Do meaningful trajectories compose end-to-end?
```

Use categorical status rather than fake precision.

Example:

```text
SUPPORTED
PARTIAL
MISSING
CONFLICTING
UNKNOWN
NOT_APPLICABLE
```

---

# 15. Designed vs Realized vs Observed

Every important domain/system should eventually support these three views:

## DESIGNED

```text
What the target World Rules permit/require.
```

## REALIZED

```text
What mechanisms and implementation currently exist.
```

## OBSERVED

```text
What current scenarios/corpus/world runs actually produce.
```

Example:

```text
DESIGNED
An ordinary creature can become a named regional threat.

REALIZED
Ecology and progression exist;
named recognition propagation is incomplete.

OBSERVED
Current corpus has not produced a persistent named non-HERO threat.
```

Do not collapse these into one status.

---

# 16. Actual-result baseline

Begin recording actual simulation outcomes where useful.

Do not wait for perfect metrics.

Examples may include:

```text
how often entities gain capability
how often mechanisms fire
how often outputs are consumed
whether migration occurs
whether settlements grow or decline
whether non-HERO subjects become recognized
whether organizations react to named individuals
whether provenance affects future behavior
```

Early data may be sparse.

Sparse truthful data is better than no baseline.

Historical comparison becomes useful naturally over time.

---

# 17. Unknown is first-class

The Control Plane must never force certainty.

Use:

```text
UNKNOWN
```

when evidence is insufficient.

Especially:

```text
mechanism not in registry
≠
mechanism does not exist
```

because Mechanism Registry completeness is not currently exhaustive.

Likewise:

```text
no mapping recorded
≠
no semantic relationship exists
```

Unknown means investigate when operationally relevant.

---

# 18. Graphify and repository discovery

Do not replace existing repository-discovery tools unnecessarily.

Where available and healthy:

```text
graphify
```

remains an important source for:

```text
symbol location
call relationships
structural investigation
mechanism-edge corroboration
impact exploration
```

The future Context Compiler should wrap/orchestrate existing retrieval mechanisms rather than replace them blindly.

Semantic search may be another input when healthy.

Its temporary absence must not invalidate the architecture.

The Control Plane should degrade gracefully to:

```text
registry
graph/code search
targeted source inspection
scenario evidence
```

---

# 19. Context Compiler comes later

Do not build the full Context Compiler first.

First collect real query patterns.

Rollout order:

```text
canonical graph/data
→ mappings
→ management views
→ real agent usage
→ repeated query patterns
→ Context Compiler
```

Eventually it should provide task-shaped context such as:

```text
context implement <concept>
context debug <mechanism>
context impact <rule>
context explain <behavior>
```

but exact CLI/API design is deferred until actual usage shows what is needed.

---

# 20. Progressive disclosure

Agents should not read the whole architecture for ordinary work.

Provide three conceptual depths:

## Level 0 — Orientation

```text
semantic owner
key Rules
relevant mechanism
current status
critical invariant
```

## Level 1 — Working context

```text
relevant Rules
mechanisms
dependencies
state ownership
known gaps/conflicts
scenarios
verification
```

## Level 2 — Evidence

```text
full rationale
source symbols
runtime traces
decision history
scenario details
```

Expand context only as evidence requires.

---

# 21. Official agent workflow for RPG-core tasks

From now on, any meaningful RPG simulation-core task should follow this general process.

The agent may adapt details to the task.

It must preserve the semantic stages.

```text
REQUEST / OBSERVATION
        ↓
RESOLVE ARCHITECTURAL CONTEXT
        ↓
CLASSIFY TASK
        ↓
TRACE RELEVANT CAUSAL CHAIN
        ↓
IDENTIFY FIRST UNPROVEN / FAILED EDGE
        ↓
CHANGE OR INVESTIGATE
        ↓
VERIFY AT THE REQUIRED EVIDENCE LEVEL
        ↓
CHECK WORLD-RULE CONFORMANCE
        ↓
UPDATE ONLY THE CANONICAL FACTS THAT CHANGED
        ↓
REFRESH GENERATED MANAGEMENT VIEWS
```

---

# 22. Resolve context before modifying core logic

Before substantive changes, determine as much as relevant:

```text
affected domain
affected World Rules
existing mechanism(s)
system membership
canonical state ownership
implementation symbols
upstream producers
downstream consumers
verification evidence
known intentional divergence
known repository gap/conflict
relevant scenario
```

Do not require every item for every trivial task.

Use proportional context.

---

# 23. Task classification

Reuse the existing Mechanism Registry change taxonomy as authoritative where applicable:

```text
INTRODUCE
EXTEND
WIRE
TUNE
SPLIT
MERGE
RETIRE
INTERPOSE
```

Add workflow/investigation modes without pretending they are registry change kinds:

```text
DEBUG_EXECUTION
DEBUG_BEHAVIOR
DEBUG_SEMANTICS
DISCOVERY
REFACTOR
CAUSAL_CHAIN_DEBUG
```

Local agent may refine this workflow vocabulary if required.

Do not invent a competing mechanism-change taxonomy.

---

# 24. Implementing genuinely new core behavior

When asked to add a feature:

do not immediately introduce a new mechanism.

First determine:

```text
Does an existing Rule already govern it?

Does an existing mechanism already own this capability?

Is the missing work:
EXTEND?
WIRE?
INTERPOSE?
or genuinely INTRODUCE?
```

If introducing:

define at minimum:

```text
semantic purpose
independent success/failure boundary
inputs/preconditions
canonical state affected
outputs
upstream dependencies
downstream consumers
failure semantics
relevant World Rules
verification path
```

Then update the Mechanism Registry and semantic mapping appropriately.

---

# 25. Wiring existing logic

If implementation already exists but does not participate in runtime:

classify it as wiring/reachability work, not “new feature implementation”.

Trace:

```text
producer
→ activation
→ mechanism
→ committed state
→ consumer
```

Do not mark wiring successful merely because a function is now callable.

Verify the causal chain actually carries meaningful state.

---

# 26. Core troubleshooting ladder

When debugging RPG simulation behavior, use this ladder unless evidence clearly points elsewhere:

```text
1. EXISTENCE
Does the mechanism/code exist?

2. REACHABILITY
Can runtime reach it?

3. ACTIVATION
Do actual generated worlds satisfy its trigger/preconditions?

4. EFFECT
Does it commit meaningful state?

5. CONSUMPTION
Does anything read/use that state?

6. BEHAVIOR
Does observed behavior match what the mechanism claims?

7. SEMANTICS
Does that behavior conform to World Rules?

8. DISTRIBUTION
Does it occur with appropriate frequency/magnitude?

9. SYSTEMIC EXPERIENCE
Does the composed behavior create the intended systemic consequence?
```

Always attempt to identify the:

> **first failed causal edge**

rather than patching the final visible symptom.

---

# 27. Execution correctness ≠ behavioral correctness ≠ semantic correctness

These are separate.

## Execution correctness

```text
Did it run?
```

## Behavioral correctness

```text
Did it do what the mechanism says it does?
```

## Semantic correctness

```text
Is that behavior valid under the target world model?
```

## Balance / systemic quality

```text
Does it happen with desirable frequency, magnitude, and consequence?
```

A mechanism may pass the first three and still require tuning.

It may pass runtime verification and still violate a World Rule.

---

# 28. Debugging “does it run?”

Trace:

```text
registered?
implementation exists?
caller/producer exists?
caller itself reachable?
feature gate?
required world data seeded?
trigger happens?
mechanism invoked?
```

Static inspection cannot prove runtime activation.

Use runtime evidence where the claim requires runtime evidence.

---

# 29. Debugging “does it do anything?”

Trace beyond invocation:

```text
meaningful input
→ result
→ committed authoritative state
→ state survives update lifecycle
→ downstream consumer
```

Detect:

```text
write-only mechanisms
dead state
unused outputs
immediately overwritten results
empty-input execution
```

Execution alone is insufficient.

---

# 30. Debugging “does it behave correctly?”

Compare observed behavior against:

```text
mechanism intent
```

not yet against the entire World Rule Catalog.

A mechanism may be implemented and reachable but contradict its own stated capability.

Verification evidence should capture this separately from build state.

---

# 31. Debugging “is this behavior actually allowed?”

This is semantic debugging.

Compare:

```text
observed mechanism behavior
```

against:

```text
frozen World Rules
```

Example:

```text
NPC learns an event it had no valid information path to know.
```

All code may execute successfully.

The result is still semantically conflicting.

Find the earliest invalid causal edge.

Do not merely patch the final reaction.

---

# 32. Tuning and balance

Only tune after establishing that:

```text
mechanism executes
mechanism produces intended behavior
behavior is semantically valid
```

Do not use tuning to mask:

```text
missing wiring
dead consumers
invalid semantics
incorrect state ownership
```

Example:

```text
NPCs almost never learn skills
```

must first determine:

```text
learning never triggers?
no opportunity producer?
writes unused?
or learning probability genuinely too low?
```

Only the last case is straightforward tuning.

---

# 33. Refactoring

A refactor should ideally preserve:

```text
World Rules
mechanism identity
semantic mapping
observed behavior
```

while implementation bindings change.

Update:

```text
implemented_by
source references
verification where necessary
```

Do not rewrite architectural documentation simply because symbols moved.

---

# 34. Strange emergent outcome

When simulation produces an unexpected result:

ask:

```text
Is the causal chain valid?
Does any REQUIRED Rule fail?
```

If the chain is valid and Rules permit it:

```text
NOT A BUG
```

even if the narrative outcome is unusual.

Examples:

```text
powerful ruler loses territory
famous subject becomes forgotten
city collapses
law is ignored
weak actor defeats stronger actor
```

The simulation judges causal validity, not narrative desirability.

---

# 35. Why did X happen?

Treat causal explanation as a first-class debug workflow.

For an actor decision, trace relevant inputs such as:

```text
knowledge/belief
motivation
relationship
capability
opportunity
authority
constraints
reach
```

Always distinguish:

```text
world truth
```

from:

```text
what the acting subject knew/believed.
```

---

# 36. Why did X not happen?

Trace the expected chain until the first missing transition.

Example:

```text
member killed             ✓
witness exists            ✓
faction learns             ✗
standing changes           ?
retaliation generated      ?
decision selects action    ?
execution possible         ?
```

Report the first causal breakpoint.

Do not diagnose solely from the missing final action.

---

# 37. Cross-domain debugging

Some failures occur even when every local mechanism works.

Example:

```text
economy
→ wealth
→ equipment
→ capability
→ combat
```

A change may break composition between two mechanisms rather than either mechanism locally.

Use:

```text
CAUSAL_CHAIN_DEBUG
```

Trace:

```text
producer
→ authoritative state
→ propagation
→ consumer
→ downstream consequence
```

Integration scenarios exist specifically for this class of failure.

---

# 38. Discovery of unregistered code

Because the registry is not exhaustive:

```text
unregistered code
≠ invalid code
```

Investigate:

```text
Is this implementation detail?

Does an existing mechanism already represent it?

Can it independently succeed/fail?

Is it a genuine missing registry mechanism?

Is it dead code?

Is evidence insufficient?
```

Then classify.

Never invent registry entries simply because a class looks important.

---

# 39. Mechanism identity remains strict

A mechanism is the smallest unit that is:

```text
intended as a capability
and
able to independently succeed/fail
```

Use existing:

```text
SPLIT
MERGE
```

semantics accordingly.

Do not split based on source-file structure.

Do not merge based on naming similarity.

---

# 40. Evidence strength must match the claim

Examples:

```text
"The symbol exists"
→ source inspection

"The call path exists"
→ structural/call analysis

"The mechanism fires in generated worlds"
→ runtime evidence

"The mechanism changes later behavior"
→ end-to-end scenario/corpus evidence

"The behavior conforms to World Rules"
→ semantic comparison

"The mechanic is balanced"
→ population/distribution evidence
```

Never use a weaker instrument to establish a stronger claim.

---

# 41. Agent completion output

Do not create a new permanent document for every task.

For meaningful RPG-core work, summarize in:

```text
existing ticket completion notes
existing implementation notes
or ephemeral agent output
```

using a compact structure where useful:

```text
Task classification
Affected Rules
Affected mechanisms
Affected state ownership

Finding
First causal breakpoint

Change performed

Registry impact
Rule impact
Mapping impact

Verification performed
Remaining uncertainty
```

Do not create orphan architectural artifacts.

---

# 42. Architecture maintenance follows the changed fact

Only update canonical facts that actually changed.

Examples:

```text
implementation symbol moved
→ implementation binding

mechanism becomes wired
→ registry state / verification

new semantic participation discovered
→ Rule↔Mechanism mapping

new runtime evidence
→ evidence/verification

Rule changes
→ Rule authority + impact mapping

parameter tuning
→ config/tuning evidence,
not World Rule rewrite
```

Generated views update automatically.

---

# 43. Drift detection is mandatory architecture direction

Rule-level realization/mapping facts will become stale unless mechanically challenged.

Do not rely on agents remembering to synchronize them.

As mapping becomes structured, add report-only drift detection first.

At minimum detect cases such as:

```text
implementation bound to mapped mechanism changed
mechanism removed/renamed
Rule removed/renamed
mapped mechanism state materially changed
verification contradicted prior realization claim
```

The detector does not need to automatically determine new semantic truth.

It should surface:

```text
mapping/review required
```

This mirrors the existing Mechanism Registry philosophy.

---

# 44. Management views must be generated

Do not manually maintain:

```text
domain progress pages
rule coverage tables
mechanism health summaries
implementation matrices
verification dashboards
integration summaries
```

if they can be derived.

Generated views should expose both:

```text
known facts
and
UNKNOWN coverage
```

so partial mapping is visible rather than silently omitted.

---

# 45. Minimum domain management view

For each significant RPG-core domain, expose something equivalent to:

```text
Domain

Semantic design:
- Rules
- frozen/open status
- unresolved semantic questions

Realization:
- mapped Rules
- supported
- partial
- conflicting
- missing
- unknown

Mechanisms:
- relevant mechanisms
- state distribution

Verification:
- code-confirmed
- runtime-observed
- contradicted
- unverified

Integration:
- key scenarios
- passing/partial/failing/unknown causal trajectories

Observed outcomes:
- useful current runtime/corpus facts

Known structural issues:
- important conflicts/gaps

Recent movement:
- optional historical trend where evidence exists
```

Exact representation is an implementation decision.

---

# 46. Do not hide UNKNOWN from denominators

A management view must make visible:

```text
mapped
unmapped
verified
unverified
```

Avoid misleading percentages calculated only from pre-filtered known subsets.

If percentages are shown, always preserve the underlying counts and baseline.

---

# 47. Runtime baseline evolves with use

Do not attempt to define every RPG simulation metric now.

Start with actual evidence already available.

When work touches a domain, add observations that genuinely help answer:

```text
Does it execute?
Does it matter?
How frequently?
What downstream consequences appear?
```

Over time this naturally becomes the simulation baseline.

Do not invent metrics merely to make dashboards look complete.

---

# 48. Normal development should enrich the Control Plane

The Control Plane must not become a separate documentation project.

Example task:

```text
"Faction retaliation is not happening."
```

Agent investigates and discovers:

```text
combat/death exists
witnessing works
information never reaches faction state
```

That work should naturally produce:

```text
better Rule↔Mechanism mapping
better causal-chain knowledge
new verification evidence
updated mechanism state if appropriate
better domain management coverage
```

Normal engineering work improves future architecture context.

That is the intended maintenance model.

---

# 49. Deletion is first-class

Before deleting/retiring RPG-core logic, query impact:

```text
Rules
mechanisms
dependencies
systems
scenarios
verification
downstream consumers
```

Deletion should reveal newly uncovered semantic obligations.

Do not rely on later regressions to discover them.

---

# 50. Semantic changes are exceptional after freeze

If implementation work discovers that desired behavior contradicts a frozen Rule:

do not silently implement around the Rule.

Use:

```text
semantic-change proposal
→ impact analysis
→ explicit decision
→ Rule revision
→ affected mapping/scenario update
```

Frozen means controlled change, not impossible change.

---

# 51. Baseline rollout

Proceed incrementally.

## Stage A — establish minimal structured control-plane model

Reuse existing canonical sources.

Add only the minimum structured data required to represent:

```text
Rule ↔ Mechanism participation
coverage/realization classification
evidence reference
unknown state
domain aggregation
```

Do not design the final ontology up front.

---

## Stage B — establish first operational slice

Use a small but semantically demanding domain such as:

```text
Territory / Control
```

Map its Rules to real mechanisms/code/evidence.

Generate the first domain management view.

Exercise actual implement/debug/impact workflows against it.

Fix obvious modeling friction.

This is baseline establishment, not an ROI gate.

---

## Stage C — ingest existing known findings

Reuse existing Rule Catalog review evidence where reliable.

Do not manually rediscover everything.

However:

```text
old prose classification
```

must not automatically become:

```text
current structured truth
```

without sufficient evidence/reference.

Preserve uncertainty.

---

## Stage D — incremental expansion through real work

When tickets touch a domain/mechanism:

```text
resolve missing mappings
validate existing mappings
add evidence
improve domain view
```

This becomes the normal maintenance path.

Targeted broader sweeps may be run where useful.

---

## Stage E — management baseline

Generate cross-domain views covering:

```text
design
realization
implementation
verification
integration
observed outcome
unknowns
```

Do not wait for complete mapping.

Partial baseline is valid.

---

## Stage F — Context Compiler

Only after repeated agent workflows reveal stable query patterns:

design the task-shaped Context Compiler.

It should orchestrate existing architecture data and repo-discovery tools.

Do not prematurely build a second search engine.

---

# 52. Success is operational, not theoretical

Do not block rollout waiting for a formal proof that the Control Plane is “good enough.”

Judge it through accumulated use.

Signs it is working include:

```text
agents rediscover less architecture repeatedly

duplicate mechanisms are noticed earlier

WIRE vs INTRODUCE becomes easier to distinguish

bugs are localized to earlier causal breakpoints

semantic conflicts are distinguishable from runtime failures

tuning is less often used to mask wiring defects

domain coverage becomes visible

verification gaps become visible

unexpected emergent behavior is easier to explain

architecture changes leave traceable impact
```

Collect this evidence naturally.

Do not create a meta-evaluation project unless later needed.

---

# 53. Explicit non-goals

Do not:

```text
map the entire 172 × 93 cross-product

stop normal engineering until mapping is complete

create a God Registry

duplicate Mechanism Registry facts

rewrite frozen Rules as implementation documentation

turn systems into semantic owners

overload depends_on

create a new document for every task

treat generated views as canonical truth

invent metrics merely for completeness

force unknown facts into guessed classifications

build the Context Compiler before real usage exists

expand this Control Plane beyond RPG simulation core
```

---

# 54. Target steady-state workflow

Eventually normal RPG-core work should feel like:

```text
task arrives
↓
agent resolves semantic + mechanism context
↓
agent determines intended causal chain
↓
agent locates first uncertain/failed edge
↓
agent changes the smallest correct layer
↓
agent verifies at appropriate evidence level
↓
agent checks Rule conformance
↓
canonical architecture/evidence facts update
↓
management views regenerate
↓
future agent receives better context
```

The Control Plane should become stronger because the project is being worked on.

It should not require a parallel documentation process to stay alive.

---

# 55. Governing principles

> **Debug causal chains, not symptoms.**

> **One owner per architectural fact.**

> **Designed, implemented, verified, and observed are different states.**

> **UNKNOWN is valid data.**

> **Use the minimum context required for the current task.**

> **Normal engineering work should enrich architectural knowledge.**

> **Record reality first; improve measurement through actual use.**

> **The Semantic Control Plane exists to make a deep RPG simulation easier to change, not harder to document.**
