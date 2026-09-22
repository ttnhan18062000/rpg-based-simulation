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

**Status.** Batch 06 (Perception/Knowledge/Information/Agency), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-6-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology established in Batch 05's admission-discipline pass — only genuinely new or
domain-refined semantics receive a local Rule ID.

---

## Domain Rules

## PERC-01 — Perception is a bounded, gated process; it never yields automatic or complete access to world fact

> A subject's access to a world signal is jointly gated by capability (sense profile), channel
> (vision, hearing, smell, magic sense, life sense, vibration, social reading), distance/reach,
> environmental interference, and attention/capacity limits. Passing a gate does not guarantee
> perception — a signal that clears the gate may still be dropped or recorded-but-ignored under
> capacity limits. A signal that never clears the gate does not exist for that subject at all,
> even though the underlying world fact is real. Perception is always partial by construction,
> never complete or automatic.

**Disposition: ACCEPT.** This is the central distinction the batch instruction required
("perception should not automatically imply perfect or complete knowledge"). Passes the
admission test: no earlier Rule states the mechanics of *how* a subject's access to world
signals is gated and bounded — Batch 01's OWN-04/OWN-06 already establish that a belief is not
truth (see Inherited, below), but nothing before this batch states the perception-gating
mechanism itself as a world-semantic constraint.

**Repository evidence: SUPPORTED for the gating mechanism's design; MISSING for whether it
actually runs in production today — a significant, load-bearing distinction.**
`PerceptionGate.can_perceive()` (`src/world/perception/gate.py`) is a real, deterministic,
read-only binary filter: 7 sense channels (`vision`, `hearing`, `smell`, `magic_sense`,
`life_sense`, `vibration`, `social_reading`), a detection threshold (score ≥ 0.2 on any
channel), and a score formula (`sense_strength × signal_strength × distance_factor ×
terrain_mod × (0.5 + alertness × 0.5)`) that only signals clearing this gate ever reach the
downstream salience/attention/budget pipeline (`AttentionFocusService` →
`SignalSalienceEvaluator` → `PerceptionFilterService`, which further partitions cleared signals
into perceived / recorded-ignored / silently-dropped under a hard budget of `max_perceived=10`,
`max_ignored_to_record=5`). **Checked directly: `PerceptionUpdatePhase` — the stage that runs
this downstream pipeline and writes `entity.cognition.subjective.perception` — has zero call
sites in `AuthoritativeApplyPipeline.refine()` and does not run in any production tick today**
(confirmed via `docs/simulation/domains/perception_contract.md`'s own explicit note, citing
`TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION`). Only `PerceptionGate` itself (the binary
channel/distance filter) is confirmed live; the richer salience/attention/budget layer this
Rule also describes is real, deterministic, and tested, but wired-dead in production.

**Scenarios:** [KA-S01](../scenarios/knowledge-agency-batch-06.md#ka-s01) (see it, know
something about it), [KA-S03](../scenarios/knowledge-agency-batch-06.md#ka-s03) (partial
observation).

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
> a claim that every future perception-adjacent mechanism must use the same formula shape.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **The most load-bearing finding in this family.** `PerceptionUpdatePhase` (the
  salience/attention/budget layer that actually produces `entity.cognition.subjective.
  perception`) has zero call sites in the production pipeline — see PERC-01 above. Only the
  upstream binary `PerceptionGate` is confirmed live.
- **Confirmed — decision-making systems currently read raw/omniscient world state rather than
  any perception-gated or knowledge-gated representation**, for at least two major decision
  paths: `ResourceOpportunityProvider.get_opportunities()` (`src/world/providers/resources.py`)
  reads `state.resource_nodes` directly, scoped only by the entity's current *region* (a coarse
  geographic proxy, not a perception/knowledge gate — every node in-region is surfaced at
  `confidence=1.0` regardless of whether `PerceptionGate` would ever have let that node's signal
  through), and `HarvestScorer.score()` (`src/ai/goals/scorers.py`) calls
  `SpatialQueryService.nearest_resource_node(state, entity.navigation.position)` — the nearest
  node in the *entire* world state, with no perception or knowledge check at all. This directly
  answers the batch instruction's own required call-out ("whether agents currently access
  omniscient state") — yes, for these two paths. See `knowledge-information.md`'s own Repository
  Findings for the parallel finding on `entity.cognition.knowledge_model` having no decision
  consumer at all.

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
