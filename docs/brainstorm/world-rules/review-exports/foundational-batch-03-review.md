---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Foundational Batch 03 (Capability / Cost / Capacity / Resource / Transformation)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the fix
for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

Five foundational law families — Capability, Cost, Capacity/Limits, Resource/Conservation
Semantics, Transformation — following on Batch 01 (Identity, State Ownership, Causality) and
Batch 02 (Time, Authority, Reach). Not a per-domain batch; deliberately domain-agnostic. Drafted
per `tmp/world-rule-batch-3-ext-ai.md`, using the same canonical-file + Scenario Bank +
review-export workflow established in Batches 01/02. All five families were kept separate — no
merge was found necessary despite the instruction explicitly permitting one.

## Canonical files included

- `foundations/capability.md` (CAP-01–05)
- `foundations/cost.md` (COST-01–05)
- `foundations/capacity.md` (LIMIT-01–05)
- `foundations/resource.md` (RES-01–06)
- `foundations/transformation.md` (TRANS-01–05)
- `scenarios/foundational-batch-03.md` (CTR-S01–S16)

## Rule Inventory

One row per Rule — semantic territory only. Full preconditions, ownership analysis, repository
evidence, and rationale stay in the canonical files linked above.

### Capability (`foundations/capability.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| CAP-01 | Capability ≠ Authority | Being able to attempt and being authorized to cause are independent facts. | Accepted |
| CAP-02 | Capability ≠ Opportunity/Reach | Being able to act doesn't mean the present situation gives the chance to exercise it. | Accepted |
| CAP-03 | Capability ≠ Resource Availability | Knowing/being able to perform a technique doesn't mean its resource is available. | Accepted |
| CAP-04 | Capability Doesn't Guarantee Success | Eligibility to attempt ≠ assured outcome. | Accepted |
| CAP-05 | Capability May Depend on Several Independent Factors | Subject state, learned ability, equipment confirmed; body/form, environment, relationships, institutional support confirmed MISSING as gates. | Accepted |

### Cost (`foundations/cost.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| COST-01 | Cost Is Broader Than Currency | Resource, time, energy, health, durability, attention, opportunity, risk, social/political cost are all legitimate categories. | Accepted |
| COST-02 | Precondition, Cost, Consequence Are Three Distinct Things | Whether an action may occur, what it consumes, and what it produces downstream are not automatically the same. | Accepted |
| COST-03 | Cost Is Paid Only on Commitment | A rejected attempt never incurs its cost. | Accepted |
| COST-04 | Not Every Action Requires a Cost | Cost is opt-in per action type, never a universal requirement. | Accepted |
| COST-05 | Actor's Cost and Another Subject's Consequence Are Independently Tracked | Even from the same action, cost and consequence on different subjects are separate facts. | Accepted |

### Capacity / Limits (`foundations/capacity.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| LIMIT-01 | Capacity Is Domain-Specific, Not Universal | Several independent bounds, never one generic "Capacity" stat. | Accepted |
| LIMIT-02 | Capacity May Degrade Under Strain | A capacity bound can be a live function of current state, not a fixed ceiling. | Accepted |
| LIMIT-03 | Exceeding Capacity Requires Explicit Handling | Rejection, eviction, or degradation — never silent overflow. | Accepted |
| LIMIT-04 | Threshold-Crossing ≠ Automatic Cause | The accumulated condition, not the check, is the real cause; not promoted to its own family. | Accepted, disposition explicit |
| LIMIT-05 | Diminishing Returns/Saturation Must Be Explicit | Legitimate, but never assumed to apply just because a limit exists. | Accepted |

### Resource / Conservation Semantics (`foundations/resource.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| RES-01 | Resource ≠ State/Capability/Capacity/Derived Abstraction | A resource is a held, consumable/transferable/transformable quantity, not any of these neighbors. | Accepted |
| RES-02 | Creation/Destruction Requires a Declared Cause | Causal legitimacy, not real-world physics. | Accepted |
| RES-03 | Strict Conservation Is Domain-Specific | Not a universal law — each resource kind's strictness is its own declared choice. | Accepted |
| RES-04 | Resource Transactions Are Atomic | Fully occurs or fully doesn't; no partial transfer. | Accepted |
| RES-05 | Renewable Resources Regenerate Through a Declared Process | Reuses TIME-04 directly; regeneration is never unexplained reappearance. | Accepted |
| RES-06 | Resource Conversion Preserves a Provenance Link | The causal link to inputs is real, independent of the output's identity question (ID-03). | Accepted |

### Transformation (`foundations/transformation.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| TRANS-01 | Transformation Requires a Valid Trigger | Not an arbitrary state update — a real trigger/precondition gates it. | Accepted |
| TRANS-02 | Transformation's Scope Is Whatever the Domain Rule Declares | Touching one listed effect category doesn't require touching all of them. | Accepted |
| TRANS-03 | Identity Preserved by Default — Deference to ID-03 | This family adds no new claim to Identity's own boundary. | Accepted, by explicit deference |
| TRANS-04 | The Accumulated Condition, Not the Check, Is the Cause | LIMIT-04 applied specifically to transformation triggers. | Accepted |
| TRANS-05 | Domain-Specific Transformations Out of Scope | Vampire/settlement/evolution content deferred to their own future domains. | Accepted, scope boundary |

## Scenario Inventory

One row per scenario, including the required counter and the meta-conclusion scenario. Full
traces stay in `scenarios/foundational-batch-03.md`.

| Scenario ID | Short name | Trajectory (initial → consequence) | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| CTR-S01 | Friendly Fire, Capable but Unauthorized | capable + in-range attack on ally → refused | Capability, Authority | Conflict & combat | Covered |
| CTR-S02 | A Leader Authorized, Not Personally Able | wounded/cooling-down leader retains full join-request authority | Capability, Authority | Organizations & institutions | Partial |
| CTR-S03 | Knows the Recipe, Lacks the Materials | recipe known → materials missing → craft blocked | Capability, Resource | Objects & material culture | Covered |
| CTR-S04 | Has Gold and Materials, Lacks the Skill | resources sufficient → recipe never learned → craft blocked | Capability, Resource | Objects & material culture | Partial |
| CTR-S05 | Stamina Spent, Wound Dealt, Outcome Not Guaranteed | attacker pays cost → attack may miss/resist → defender bears consequence if it lands | Cost, Capability | Conflict & combat | Covered |
| CTR-S06 | Several Domain-Specific Limits, Degraded by Strain | fatigue → multiple independent capacity bounds reduced together | Capacity | Agency/decision, Perception/knowledge | Covered |
| CTR-S07 | Capacity Exceeded | new lead would exceed max_leads → explicit rejection/eviction | Capacity | Agency/decision, Perception/knowledge | Covered |
| CTR-S08 | Resource, or Something Else Entirely? | gold vs. readiness vs. skill vs. scarcity ratio compared | Resource, State Ownership | none | Covered |
| CTR-S09 | Strict Gold, Generous Loot | gold conserved strictly ↔ loot generated by declared rule | Resource | Economy/resources | Covered |
| CTR-S10 | Threshold Crossed, Transformation Withheld (counter) | value crosses threshold → required context absent → no transformation | Capacity, Transformation | Capability/progression | Covered |
| CTR-S11 | The Node Regrows, Traceably | node depleted → declared regeneration rule → charges return | Resource, Time | Economy/resources | Covered |
| CTR-S12 | Ore Becomes a Sword, Traceably | ore + gold consumed → sword produced, provenance intact | Resource, Identity | Objects & material culture | Covered |
| CTR-S13 | An Ordinary Creature, Sufficiently Changed | accumulated XP → valid trigger → kind/attributes/equipment change, identity intact | Transformation, Capability, Cost, Resource, Identity | Capability/progression | Covered |
| CTR-S14 | Capable, but Out of Reach (cross-batch) | capable actor → LOS obstructed → no effect | Capability, Reach | Space & environment | Covered |
| CTR-S15 | Growth Meets Its Ceiling | accumulation continues → declared saturation floor prevents unconstrained scaling | Capacity | Ecology/population | Covered |
| CTR-S16 | Same Situation, Different Outcome? | same situation → several valid outcomes proposed → disposition traced | none (disposition probe) | Evaluation (explicitly excluded) | Moved out |

## Coverage Summary

What this batch actually stress-tests — coverage shape, not scenario count.

**Capability**
- capability vs. authority (both directions) — CTR-S01, CTR-S02
- capability vs. resource (both directions) — CTR-S03, CTR-S04
- capability vs. reach — CTR-S14
- capability vs. guaranteed success — CTR-S05
- multi-factor dependency, confirmed and unconfirmed factors — CTR-S03, CTR-S04

**Cost**
- broader-than-currency categories — CTR-S05
- precondition/cost/consequence triple — CTR-S05
- cost charged only on commitment — CTR-S05
- actor-cost vs. other-subject-consequence — CTR-S05

**Capacity**
- domain-specific plural bounds — CTR-S06
- degradation under strain — CTR-S06
- exceeding capacity, explicit handling — CTR-S07
- threshold-crossing causal discipline — CTR-S10
- saturation/diminishing returns — CTR-S15

**Resource**
- resource vs. neighboring concepts — CTR-S08
- declared creation/destruction, strict vs. non-strict — CTR-S09
- atomicity — CTR-S09
- renewable regeneration provenance — CTR-S11
- conversion provenance — CTR-S12

**Transformation**
- valid trigger requirement — CTR-S13
- scope-is-whatever-is-declared — CTR-S13
- identity deference (no new claim) — CTR-S13
- threshold-is-not-the-cause — CTR-S10

**Disposition-only**
- deterministic randomness moved out — CTR-S16

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with Batches 01/02's own framing:

- CAP-05's body/form and environment capability gates are confirmed MISSING — deferred to
  Capability & progression and Space/environment respectively.
- CAP-05's relationships/institutional-support capability gate is not decided — deferred to
  Groups/organizations & institutions if that domain ever needs it.
- COST-01's attention and social/political-consequence cost categories are named but not yet
  repository-evidenced as *cost* specifically — deferred to Agency/decision and Politics/
  authority & war respectively.
- CTR-S04's learned-recipe capability gate (separate from resource sufficiency) was not
  independently re-verified — deferred to Objects & material culture or Capability &
  progression, whichever formalizes crafting content first.
- LIMIT-05's saturation/diminishing-returns concrete content stays with Ecology/population.
- RES-01–06's actual resource catalog (what specific things are resources, their kinds) stays
  with Economy/resources and Objects & material culture.
- TRANS-01–05's actual transformation content (vampire, settlement lifecycle, species
  evolution) stays with Magic/supernatural, Places/settlements & territory, and Capability &
  progression respectively — explicitly not designed here, per the batch instruction.

## Cross-domain findings

- Capability ↔ Authority: CAP-01 and AUTH-01 are the same boundary stated from each family's own
  side — CTR-S01/S02 and Batch 02's TAR-S06/S07 are the same evidence reused, not
  re-discovered.
- Capability ↔ Reach: CAP-02 and REACH-01 are likewise the same boundary from two sides —
  CTR-S14 is the explicit cross-batch check the instruction required.
- Capacity ↔ Transformation ↔ Causality: LIMIT-04/TRANS-04 both restate CAUSE-01's real-
  causal-path requirement for the threshold-crossing case specifically, and CTR-S10/CTR-S13 both
  rely on the same `EvolutionSystem.evaluate()` mechanism to answer two different families'
  questions — a small piece of evidence Capacity and Transformation are correctly kept separate.
- Resource ↔ Time: RES-05 reuses TIME-04 directly rather than re-deriving recurrence semantics
  for Resource specifically.
- Resource ↔ State Ownership: RES-01 reuses OWN-03's derived-view finding directly (the
  readiness-vs-scarcity-ratio contrast) as one of its four category distinctions.
- Resource ↔ Identity: RES-06 is deliberately framed to avoid reopening ID-03's crafting
  exception — provenance (causal) and identity (continuity) are kept as separate concerns even
  though both apply to the same crafting scenario.
- Transformation ↔ Identity: TRANS-03 is pure deference, adding no new claim — recorded as
  "Accepted, by explicit deference" rather than as an independent finding.

**Where a foundational concept could be confused with a later domain concept (explicit
call-out, per the batch instruction):**
- Capability (foundational: bare eligibility) vs. Capability & progression (later domain: skill
  trees, XP, mastery curves) — the family name overlap is real and intentional; CAP-01–05 states
  only the eligibility boundary, never a specific skill system.
- Capacity/Limits (foundational: bounded concurrent commitment in general) vs. any future
  domain's own "capacity" word (e.g., settlement population capacity, inventory capacity,
  military capacity) — LIMIT-01's own headline finding (no universal Capacity stat) is the
  guardrail against this confusion; each later domain's "capacity" is its own bound, not an
  instance of one shared stat.
- Resource (foundational: a held, consumable/transferable quantity in general) vs. Resources,
  production & economy (later domain: markets, pricing, trade) — RES-01–06 states only what
  qualifies as a resource and its conservation discipline; market mechanics are entirely
  deferred.
- Cost (foundational: what is paid for an action, in general) vs. any later domain's own use of
  "cost" (a spell's mana cost, a diplomatic cost, a social cost) — COST-01's "broader than
  currency" framing is the guardrail; a later domain's specific cost content is not
  pre-designed here.

## Open questions

1. Is CTR-S02's incapacitated-leader-authority behavior intentional or an unexamined gap? Same
   open judgment call as Batch 02's TAR-S07 — not re-resolved here.
2. Does the crafting system gate on a learned-recipe capability check separate from resource
   sufficiency (CTR-S04)? Not independently re-verified this batch.
3. CAP-05's body/form, environment, relationships, and institutional-support capability gates —
   should any of these become real gates in a future domain, and if so, which one investigates
   first?
4. COST-01's attention and social/political-consequence categories — real cost categories, or
   will they turn out to be consequences of something else once a domain actually models them?

## Repository evidence

No CONFLICTING or UNKNOWN findings this batch. Two PARTIAL findings (CTR-S02, reusing Batch 02's
already-recorded open judgment call; CTR-S04, a genuinely new PARTIAL — the learned-recipe gate
wasn't independently re-verified). Several confirmed MISSING findings (CAP-05's body/form,
environment, relationships, institutional-support capability gates) are recorded honestly as
absent mechanisms, not assumed to exist.

Key evidence, all confirmed by direct code inspection: `src/engine/legality.py`
(`FRIENDLY_FIRE_ILLEGAL`, `LOS_OBSTRUCTED`, reused from Batch 02), `src/engine/rpg_depth.py`
(`StaminaService.can_use_skill/drain_attack/drain_move/drain_harvest/drain_skill`),
`src/engine/domain/skill_actions.py` (attacker cost / defender consequence as two separate
`EntityUpdate`s), `docs/mechanics/resource_conservation_contract.md` (the four-gate atomicity
sequence), `docs/engine/governance_logic.md` (RPG-AUTH-003, the gold conservation law),
`src/content/schema.py` (`loot_table`, declared non-strict creation), `src/strategy/
cognition_capacity.py` (`CapacityService.derive_profile()`, five independent bounds,
fatigue-driven degradation), `src/engine/pipeline_phases/capacity_enforcement.py` and
`src/systems/strategic_systems/detour.py` (explicit capacity-exceeded handling), `src/world/
ecology.py` (`DENSITY_FLOOR`, explicit saturation), `src/engine/evolution.py`
(`EvolutionSystem.evaluate()`, reused from Batches 01/02 for the threshold-vs-cause and
valid-trigger findings), `src/engine/kernel.py` (`state.seed`, the deterministic-randomness
disposition's own evidence), `src/core/inventory.py` (`can_equip_item`'s slot-requirement
check).

**Which candidate rules were rejected as implementation detail (explicit call-out, per the batch
instruction):** none this batch. Unlike Batch 02's follow-up pass, no candidate rule required
walking back an implementation-specific claim after the fact — the starter hypotheses were
already framed at the semantic level throughout, and repository evidence was checked against
that framing rather than against an implementation detail that needed removing.

**Whether deterministic randomness belongs in the Rule Catalog (explicit call-out):** No.
Disposed of via CTR-S16: every "random" outcome in this repository is a deterministic function
of a stored `state.seed`; the residual world-semantic question (can a stochastic-flavored
decision be a legitimate cause?) is already fully covered by CAUSE-01/CAUSE-03; reproducibility/
replay belongs to Evaluation/implementation per the established boundary
(`simulation-rule-world-law-design-preparation.md` §3.8). No Rule family, and no individual
Rule, was created for it.

**Any rule that would accidentally impose real-world physics on the fantasy setting (explicit
call-out):** None. RES-02/RES-03 were drafted specifically to avoid this — the gold-vs-loot
contrast (CTR-S09) exists precisely to confirm strict conservation is a domain choice, not a
universal law the Catalog imposes on every resource. No rule in this batch requires any resource
to obey physical conservation it wasn't already declared to obey.

## Owner-attention decisions

- Whether to formally resolve CTR-S02/TAR-S07's incapacitated-leader-authority open judgment
  call now (across both batches) rather than continuing to carry it forward unresolved.
- Whether CAP-05's confirmed-missing capability gates (body/form, environment) should be
  prioritized in whichever future domain reaches them first, given how foundational "does form
  affect what you can do" feels for a lived-history-focused simulation.
- Whether the five families (Capability, Cost, Capacity, Resource, Transformation) should stay
  as five separate canonical files long-term, or whether a future consolidation pass (once
  domain content exists) might reveal a cleaner grouping — no merge was found necessary this
  batch, but the question was investigated at the "candidate families" level, not at the
  "having built more on top of them" level.

## Starter-candidate disposition summary

All five starter family groupings (Capability, Cost, Capacity/Limits, Resource/Conservation,
Transformation) were kept separate — investigated for a forced merge per the batch instruction's
own explicit invitation, and rejected: no two families were found semantically inseparable.
Within them, 26 Rules were drafted (5 Capability, 5 Cost, 5 Capacity, 6 Resource, 5
Transformation) — all 26 accepted, 0 rejected, 0 split, 0 merged. Two additional investigations
were explicitly *not* promoted to their own Rule family, per the batch instruction's own
invitation to make that call: **Threshold semantics** (folded into Capacity as LIMIT-04, cross-
linked from Cost/Resource/Transformation rather than duplicated) and **Deterministic randomness**
(moved out of the Catalog entirely, per CTR-S16's disposition). No rule was rejected as an
implementation concern this batch — the engine-tick-ordering/scheduler-execution-order exclusion
established in Batches 01/02 was carried forward unchanged, not re-litigated.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/world-rule-foundational-batch-03-report.md` (local review report, not part of this catalog).

---

> **FOUNDATIONAL BATCH 03 READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist: five rule-family files (26 rules total), one scenario file (16
scenarios covering all 12 required probes plus the explicit cross-batch checks), this review
export with all nine required sections (Rule Inventory, Scenario Inventory, Coverage Summary,
Deferred Semantics, Cross-domain findings, Open questions, Repository evidence, Owner-attention
decisions, Candidate disposition) plus every explicitly-required call-out, and a local
disposition report. No contradiction was found against Batches 01/02 or within this batch. Per
the batch instruction's stop condition: all ten checklist items are satisfied (capability
eligibility clear; authority/reach/resource/precondition boundaries distinct; cost vs.
consequence clear; capacity semantics exist without a universal stat; resource creation/
depletion/conversion has causal semantics; transformation semantics integrate with Identity;
thresholds have explicit meaning, folded into Capacity; deterministic-randomness disposition is
explicit — moved out; normal and counter-scenarios traced; deferred domain questions explicit).
Do not begin domain-facing Milestone B batches yet. Per the batch instruction: proceed next to
the planned Milestone A History/Provenance completion pass before declaring the foundational
milestone complete.
