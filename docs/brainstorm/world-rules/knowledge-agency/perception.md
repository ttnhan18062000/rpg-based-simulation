---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Perception

**Purpose/scope.** Under what conditions a subject can obtain information about some part of
the world. Preserves the distinction `world fact ≠ perceived fact`: a world fact may exist even
when no subject observes it, and perception never automatically implies perfect or complete
knowledge.

**Status.** Batch 06 (Perception/Knowledge/Information/Agency), drafted 2026-09-22, revised the
same day per follow-up review (`tmp/world-rule-batch-6-followup-ext-ai.md`): PERC-01
generalized so its listed gating dimensions are possible constraints rather than a universal
mandatory joint requirement, and explicit-rule-permitted complete/perfect perception is no
longer implicitly prohibited. Candidates below originated as external-reviewer hypotheses
(`tmp/world-rule-batch-6-ext-ai.md`); each carries this session's disposition and repository
evidence. Structured per the normalized five-category methodology established in Batch 05's
admission-discipline pass — only genuinely new or domain-refined semantics receive a local Rule
ID.

---

## Domain Rules

## PERC-01 — Perception is bounded by declared constraints; it does not imply complete or perfect knowledge by default

> Perception is bounded by the declared constraints of the relevant subject, channel, target,
> and context. Capability (sense profile), channel, distance/reach, environmental interference,
> and attention/capacity limits are *possible* constraining dimensions a mechanism may declare —
> not a universal, mandatory joint requirement every perception-adjacent mechanism must impose.
> The core standing principle is narrower and more durable than any one implementation:
> perception does not imply complete or perfect knowledge **by default**. Where an explicit
> world rule declares a channel or condition that grants complete or perfect observation (a
> special sense, an unconditional reveal, a declared omniscient vantage), that is a legitimate,
> permitted exception — this Rule states a default, not a prohibition on ever perceiving
> completely.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — generalized from the original
draft's specific joint-gating list to the declared-constraints framing above.** The original
wording risked being read as requiring every perception mechanism to combine all four named
dimensions, and as implicitly prohibiting legitimate complete/perfect observation where a world
rule explicitly grants it. Neither was intended; the fix keeps the same repository evidence but
states the Rule at the level the Catalog actually needs: a default of partiality, declared
per-mechanism, not a mandatory formula shape. Passes the admission test: no earlier Rule states
that perception access defaults to bounded/partial — Batch 01's OWN-04/OWN-06 already establish
that a belief is not truth (see Inherited, below), but nothing before this batch states the
perception-boundedness default itself as a world-semantic constraint.

**Repository evidence: SUPPORTED for one legitimate, real instance of a declared-constraints
mechanism; MISSING for whether that instance actually runs in production today — a significant,
load-bearing distinction.** `PerceptionGate.can_perceive()` (`src/world/perception/gate.py`) is
this repository's own current declared-constraints mechanism — a real, deterministic, read-only
binary filter over 7 sense channels (`vision`, `hearing`, `smell`, `magic_sense`, `life_sense`,
`vibration`, `social_reading`), a detection threshold (score ≥ 0.2 on any channel), and a score
formula (`sense_strength × signal_strength × distance_factor × terrain_mod × (0.5 + alertness ×
0.5)`) — one legitimate way to declare the bound, not evidence that every future mechanism must
combine the same four dimensions. Only signals clearing this gate ever reach the downstream
salience/attention/budget pipeline (`AttentionFocusService` → `SignalSalienceEvaluator` →
`PerceptionFilterService`, which further partitions cleared signals into perceived /
recorded-ignored / silently-dropped under a hard budget of `max_perceived=10`,
`max_ignored_to_record=5`). **Checked directly: `PerceptionUpdatePhase` — the stage that runs
this downstream pipeline and writes `entity.cognition.subjective.perception` — has zero call
sites in `AuthoritativeApplyPipeline.refine()` and does not run in any production tick today**
(confirmed via `docs/simulation/domains/perception_contract.md`'s own explicit note, citing
`TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION`). Only `PerceptionGate` itself (the binary
channel/distance filter) is confirmed live; the richer salience/attention/budget layer this Rule
also describes is real, deterministic, and tested, but wired-dead in production (**INERT/OFF**,
not CONFLICTING — nothing actively violates the Rule here, the richer layer simply never runs).

**Scenarios:** [KA-S01](../scenarios/knowledge-agency-batch-06.md#ka-s01) (see it, know
something about it), [KA-S03](../scenarios/knowledge-agency-batch-06.md#ka-s03) (partial
observation), [KA-S18](../scenarios/knowledge-agency-batch-06.md#ka-s18) (complete observation
where declared — confirms this Rule does not prohibit legitimate perfect observation).

---

## Inherited / Applied Foundational Rules

### World fact existence and truth do not depend on any subject perceiving or believing it

> A world fact may be true, exist, and go on causing real consequences whether or not any
> subject ever perceives or believes it.

**Disposition: INHERITED — direct reuse of OWN-04 ("proposed change is distinct from committed
state"), OWN-06 ("historical reference does not imply present ownership... a belief being held
does not make it true"), and CAUSE-01 (a consequence requires a real causal path, independent of
any subject's cognition). No new claim is added by restating this at Perception's point of use
— the entire authoritative-apply-pipeline architecture already makes world-state commitment
independent of any entity's cognition by construction.**

**Repository evidence: SUPPORTED**, reused directly: the typed `Update`→`Patch`→
`AuthoritativeState` apply path never takes entity perception/cognition as an input to whether
a durable state change commits — a resource node depletes, a region takes calamity damage, or
an entity dies whether or not any other entity currently perceives that region.

**Scenarios:** [KA-S02](../scenarios/knowledge-agency-batch-06.md#ka-s02) (event happens
unobserved).

### Reach is asymmetric — perceiving does not imply being perceived

> Subject A having reach (including perceptual reach) to affect or observe subject B does not
> imply B has the reciprocal reach to observe A.

**Disposition: INHERITED — direct reuse of REACH-03 ("reach may be asymmetric"), which already
cites `PerceptionGate.can_perceive()`'s one-directional signature as its own evidence. This
batch reconfirms the same finding from Perception's own vantage point; no new claim.**

**Repository evidence: SUPPORTED, reconfirmed.** `PerceptionGate.can_perceive(source_entity,
target_signals, context)` computes a one-directional query with no reciprocal computation in
its signature or return value — exactly what REACH-03 already found.

**Scenarios:** none newly traced; reuses Batch 02's own TAR-S17 evidence directly.

---

## Scope / Deferred Boundaries

### Formal stealth/ambush content

> REACH-03's asymmetry finding (inherited above) establishes that one-directional perception is
> architecturally real, but formal domain-specific stealth/ambush mechanics — deliberate
> concealment, detection rolls, ambush-bonus content — are not designed here. REACH-03's own open
> question explicitly flagged this for "the future Perception/knowledge batch"; this batch
> confirms the asymmetry still holds but does not design concealment/detection content on top of
> it.

**Disposition: SCOPE BOUNDARY.** Not a Domain Rule: no new world-semantic claim, only a
deferral of concrete content design.

### Universal perception/detection formula

> This family does not generalize `PerceptionGate`'s specific score formula (sense
> strength × signal strength × distance × terrain × alertness) into a universal law — that
> formula is this repository's own current implementation choice for the sense-channel gate, not
> a claim that every future perception-adjacent mechanism must use the same formula shape. Per
> the 2026-09-22 follow-up revision, PERC-01 itself now states this generalization directly
> (declared constraints, not a mandatory joint formula) — this boundary remains to make explicit
> that the *specific* score formula above is still only this repository's own implementation
> choice, not a second universal law smuggled in under a different name.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

Classified per the three-way distinction sharpened by the 2026-09-22 follow-up review: a
**CONFLICTING** finding is a live, active behavior that violates a target Rule's own semantic
boundary; an **INERT/OFF** finding is a real mechanism that simply does not run, violating
nothing because nothing runs; a **MISSING** finding is a permitted mechanism that was never
built at all. This distinction matters — the follow-up review explicitly required not
collapsing an active violation into the same bucket as a dormant or unbuilt one.

- **INERT/OFF — the salience/attention/budget layer never runs.** `PerceptionUpdatePhase` (the
  layer that actually produces `entity.cognition.subjective.perception`) has zero call sites in
  the production pipeline — see PERC-01 above. Only the upstream binary `PerceptionGate` is
  confirmed live. Nothing actively violates PERC-01 here; the richer layer is simply dormant.
- **CONFLICTING — the most load-bearing finding in this family, and one of the most significant
  in the whole Rule Catalog to date.** `ResourceOpportunityProvider.get_opportunities()`
  (`src/world/providers/resources.py`) and `HarvestScorer.score()` (`src/ai/goals/scorers.py`)
  are live, unconditional, actively-running decision paths that read raw/omniscient world state
  directly — `ResourceOpportunityProvider` reads `state.resource_nodes` directly, scoped only by
  the entity's current *region* (a coarse geographic proxy, not a perception/knowledge gate —
  every node in-region is surfaced at `confidence=1.0` regardless of whether `PerceptionGate`
  would ever have let that node's signal through), and `HarvestScorer.score()` calls
  `SpatialQueryService.nearest_resource_node(state, entity.navigation.position)` — the nearest
  node in the *entire* world state, with no perception or knowledge check at all. This is not
  an absent or dormant mechanism (INERT/OFF) — it is active behavior that directly contradicts
  PERC-01's own default (perception is bounded by declared constraints) for the specific
  decisions these two call sites drive. Classified CONFLICTING, not MISSING: the target
  semantics (subject-bounded perception/knowledge should gate what a decision can see) are
  coherent and already partly implemented elsewhere (`PerceptionGate` itself); these two call
  sites simply do not route through that implementation, producing a real, live architecture
  mismatch rather than an unbuilt feature. This directly answers the batch instruction's own
  required call-out ("whether agents currently access omniscient state") — yes, actively, for
  these two paths. See `knowledge-information.md`'s own Repository Findings for the parallel
  INERT/OFF finding on `entity.cognition.knowledge_model` having no decision consumer at all —
  a different kind of gap from this one, and deliberately not classified the same way.

**This finding does not invalidate the Rule Catalog.** PERC-01's own target semantics remain
coherent and internally consistent; what this finding shows is that the Catalog successfully
exposed a real, documented mismatch between that target and this repository's current
implementation — exactly the kind of result a Rule Catalog investigation is supposed to be able
to produce.

## Cross-domain links recorded here

- PERC-01 → Agency/decision (`agency-decision.md`'s AGENCY-03, opportunity generation is one of
  the confirmed omniscience-bypass sites), Knowledge/Information (`knowledge-information.md`,
  what a subject does with a perceived signal once it clears the gate)
- Inherited entries → State Ownership (OWN-04, OWN-06), Causality (CAUSE-01), Reach (REACH-03)

## Open questions carried forward

1. Whether `PerceptionUpdatePhase` should be wired into production (closing the dead-code gap)
   is an implementation/rollout decision, not a semantic one — this family states what
   perception *should* look like when live; whether or when to wire it is not decided here.
2. Whether `ResourceOpportunityProvider` and `HarvestScorer` (and any other omniscience-reading
   decision path not enumerated here) should be re-scoped to read through perception/knowledge
   instead of raw world state is a real, load-bearing design question for a future batch or
   ticket — flagged, not decided, since redesigning those call sites is an implementation
   change, not a Rule-Catalog decision.
3. Formal stealth/ambush content (concealment, detection rolls) remains deferred, per REACH-03's
   own carried-forward open question — still not designed here.
