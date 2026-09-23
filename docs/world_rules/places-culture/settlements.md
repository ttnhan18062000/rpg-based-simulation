---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Settlements

**Purpose/scope.** What makes a settlement more than a Place containing population, how
settlement growth/decline gains real causal meaning, and how settlement transformation relates
to identity. Does not decide Place-level identity (see `places.md`) or territorial control
(see `territory-control.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 11A (Places/Settlements/Territory), first draft, per
`tmp/world-rule-batch-11-ext-ai.md`.

---

## Domain Rules

## SETT-01 — A settlement is a Place carrying a declared settlement-level social/material function and persistent state, normally associated with a resident population but not reducible to population alone; it is distinct from a bare population cohort, an organization, a territory, or a government, and its own status (active, temporarily depopulated, abandoned, ruined-former, resettled) may change independently of the underlying Place's own identity, which by default persists throughout (PLACE-03)

> A settlement is not a fifth kind of subject alongside Place, Organization, Territory, and
> Population — it is a **Place** (`places.md`'s own PLACE-01) carrying a declared
> settlement-level social/material function and its own persistent state, normally associated
> with a resident population but never reducible to that population alone: an active
> settlement, a temporarily depopulated settlement, an abandoned settlement, a ruined former
> settlement, and a resettled site are all distinguishable settlement-status values a domain
> may model over the same, or a different, underlying Place. A settlement is never identical
> to its current population cohort (the settlement persists through resident turnover, exactly
> as an Organization persists through member turnover, Batch 10's ORG-01), to any organization
> operating within it, to the territory it sits in, or to whichever government or institution
> governs it. A settlement may, but need not, additionally have built environment, resource
> access, services, institutions, economic activity, defenses, or political relationships — no
> domain is required to model all of them for every settlement. The default relationship
> between these three facts is: **a settlement's own status may end or become dormant while
> the underlying Place's own identity persists** (PLACE-03's own default-continuity outcome,
> reused directly) — population reaching zero ends or dormant-izes the settlement's own active
> function, never the Place's own identity, by that same default. Whether a later resettlement
> *reactivates the same settlement identity* or *establishes a new one* is not resolved by one
> universal answer — that remains a further, domain-declared question, exactly as PLACE-03
> itself leaves the *declared-exception* half of Place-identity continuity open for content to
> decide.

**Disposition: ACCEPT — REQUIRED for the distinctness and for the default relationship
between settlement status, Place identity, and population presence; which optional facts any
given settlement has, and whether any specific resettlement reactivates or replaces
settlement identity, remain PERMITTED, domain-specific content; corrected 2026-09-22 per a
second external follow-up review.** The prior wording ("a settlement is a Place hosting a
resident population") was too reductive, defining settlement almost entirely in terms of
population presence — the follow-up correctly identified that a settlement is better
understood as a Place carrying its own declared social/material function and state, which may
persist (dormant) through zero population, rather than a concept that exists only while
population is present. This revision also directly answers the batch instruction's own request
to establish the *default* relationship between Place identity, settlement lifecycle/status,
and population presence — rather than leaving all three as independently unresolved
questions, as the immediately preceding follow-up round had left them. Passes the admission
test: no earlier Rule states this specific settlement-vs-five-adjacent-concepts distinction,
nor the specific default relating settlement status to Place-identity continuity — it directly
parallels Batch 10's ORG-02 (membership ≠ six adjacent concepts) and reuses this batch's own
corrected PLACE-03 default, but requires new content specific to what makes a *settlement*
(as opposed to a bare Place or a bare population) its own coherent, statused concept.

**Repository evidence: SUPPORTED, by construction, for the ordinary-turnover case; MISSING
for any settlement-status field distinct from raw population presence.** `PlaceState`'s own
`CITY` kind already *is* this repository's settlement concept for continuous habitation — no
separate `SettlementState` class exists, and `PlaceKind.CITY`'s own fields (`scale`,
`building_ids`, `entity_ids`) are exactly the "Place carrying settlement content" shape this
Rule describes. Checked directly: no field represents settlement *status* (active/dormant/
abandoned/resettled) independently of `entity_ids`' own raw population count — a settlement's
own "status" is not separately tracked, only inferable from population presence, which is a
narrower realization than this Rule's own revised target (status as its own fact, only
*normally* correlated with population). No resettlement-after-total-abandonment mechanism
exists anywhere in this repository (PT-S05's own confirmed MISSING finding, extended below)
for the harder identity-reactivation-vs-replacement question to be checked against at all.

**Scenarios:** [PT-S03](../scenarios/places-territory-batch-11a.md#pt-s03) (village becomes
town, extended), [PT-S05](../scenarios/places-territory-batch-11a.md#pt-s05) (abandoned and
resettled, extended — depopulated settlement), [PT-S11](../scenarios/places-territory-batch-11a.md#pt-s11)
(migration changes settlement).

---

## SETT-02 — Settlement growth or decline requires a real, declared causal path connecting population/resource/safety/hazard conditions to settlement-state change; a settlement tier, level, or scale value, where materialized, must carry declared consequences and must never be a bare incrementing counter

> A settlement growing (more population, activity, infrastructure) or declining (contraction,
> abandonment) is never an unstated default direction — it results from a real, declared causal
> path (resources, safety, and opportunity driving migration/reproduction; war, famine, hazard,
> or isolation driving death/migration/decline). Where a settlement's own scale, tier, or level
> is materialized as a tracked value, that value must carry real, declared world consequences —
> a value that simply increments with no consumer is not semantic depth.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is the settlement-specific
instance of the already-established "no default X, only declared causal paths" pattern
(Batch 09's SOC-03, Batch 07's PROG-05, Batch 10's own reclassified open-instability entry),
combined with the batch instruction's own explicit warning against `town.level += 1` without
meaningful consequences — genuinely new content is the specific causal factors this Rule names
for settlement growth/decline (resources/safety/opportunity vs. war/famine/hazard/isolation),
which no earlier Rule states.

**Repository evidence: MISSING, for any growth/decline causal mechanism; UNKNOWN, whether
`PlaceState.scale` is ever mutated after world-compile time.** No mechanism was found that
grows or shrinks a settlement's own `scale`, `building_ids`, or `entity_ids` from population,
resource, or hazard conditions during simulation — `scale` appears to be set once, at
world-compile time, rather than causally evolving. This was not exhaustively traced against
every world-assembly/regeneration code path this batch, so it is recorded as UNKNOWN rather
than a confirmed MISSING, pending a future, more targeted investigation.

**Scenarios:** [PT-S12](../scenarios/places-territory-batch-11a.md#pt-s12) (settlement growth
without a level), [PT-S13](../scenarios/places-territory-batch-11a.md#pt-s13) (settlement
level with no consumer, counter).

---

## SETT-03 — Settlement transformation (hamlet → village → town, town → city, city → ruin, camp → permanent settlement) does not follow one universal linear progression; each transformation may independently change identity, capability, institutions, resource demand, social opportunity, and world reaction, and a domain must declare which

> Settlement transformation is not assumed to follow a single progression tree (hamlet →
> village → town → city, and no other path). Each transformation case independently determines
> which of the following change and which persist: the settlement's own identity (continuing
> the same Place, per PLACE-03), its capability, its institutions, its resource demand, its
> social opportunity, and how the wider world reacts to it.

**Disposition: ACCEPT — REQUIRED for the "no universal tree, declare per case" requirement.**
Passes the admission test: this is SETT-01/PLACE-03's own settlement-specific deepening,
required by the batch instruction's own explicit request not to force one linear progression —
new content beyond PLACE-03 in that it names the *specific* facts (capability, institutions,
resource demand, social opportunity, world reaction) a settlement transformation must decide
about, beyond the bare identity-continuity question PLACE-03 already covers.

**Repository evidence: MISSING.** No settlement-transformation mechanism (hamlet→village→town
or the reverse) beyond the single CITY→RUIN case already covered by PLACE-03's own evidence
was found — confirmed via the same investigation.

**Scenarios:** [PT-S03](../scenarios/places-territory-batch-11a.md#pt-s03),
[PT-S04](../scenarios/places-territory-batch-11a.md#pt-s04).

---

## Inherited / Applied Foundational Rules

### A settlement's own collective/aggregate population state is distinct from any single resident's own individual state

> A settlement's own population-level facts (total count, cohort composition, aggregate
> activity) are distinct from, and never automatically derived into or from, any single
> resident's own individual state.

**Disposition: INHERITED — direct reuse of Batch 05's ECOL-01/ECOL-02 (individual and
aggregate representations are distinct), applied to settlement population specifically. No
new claim beyond instantiating an already-settled boundary for this kind of collective
subject.**

**Repository evidence: SUPPORTED.** `RegionState.population_cohorts` (age-bracket-keyed
demographic data, E52A) is a real, aggregate-scale fact structurally separate from any
individual `EntityState` — confirmed distinct by construction, consistent with this Rule.

**Scenarios:** none newly traced; confirmed by direct inspection of the field's own shape.

---

## Scope / Deferred Boundaries

### Concrete settlement-tier/service/institution catalog

> This family states that settlements may optionally have services, institutions, economic
> activity, and defenses (SETT-01) but does not design the concrete catalog of specific tiers,
> service kinds, or institution types — deferred, per this family's own scope.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **SUPPORTED — this repository already collapses Settlement into a Place kind, exactly as
  this Rule permits.** No separate `SettlementState` exists; `PlaceKind.CITY` fills the role.
  See SETT-01 above.
- **MISSING/UNKNOWN — no confirmed causal settlement growth/decline mechanism.** See SETT-02
  above; the `scale` field's own mutability was not exhaustively traced.
- **Confirmed MISSING — no migration mechanism of any kind exists anywhere in this repository**
  (confirmed via direct, broad search for migration-related terms across `src/systems/` and
  `src/engine/`) — the settlement-growth causal chain this family's own SETT-02 requires (and
  the batch instruction's own §28 investigation) has no realized input mechanism to trace.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** settlement growth/decline requires a real causal path from population/
  resource/safety/hazard conditions (SETT-02).
  **Current realization:** no such mechanism exists; `scale` appears static post-world-
  compile.
  **Gap/mismatch:** the entire causal chain, including its migration input (see below), is
  unrealized.
  **Possible implementation direction:** a scheduled settlement-state-update process (paralleling
  `TownResolutionSystem`'s own tax/maintenance pass, Batch 10 evidence) reading regional
  population/resource/hazard state and producing a declared `scale`/service delta.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** individual and aggregate population movement (migration) connects
  pressure/opportunity to settlement, economic, and cultural consequence.
  **Current realization:** no migration mechanism of any kind exists.
  **Possible implementation direction:** a population-flow process reading regional
  push/pull factors (hazard, resource depletion, opportunity) and producing declared
  population-cohort deltas.
  **Implementation decision:** DEFERRED.

## Cross-domain links recorded here

- SETT-01 → Places (`places.md`'s PLACE-01), Organizations (Batch 10's ORG-01/02 — the same
  persistence-through-turnover and multi-way-distinctness patterns)
- SETT-02 → Social Relations (SOC-03, Batch 09), Capability/Progression (PROG-05, Batch 07),
  Organizations (Batch 10's reclassified open-instability entry) — the same declared-causal-
  path family
- SETT-03 → Places (`places.md`'s PLACE-03)
- Inherited population-aggregate entry → Ecology/Population (ECOL-01/02, Batch 05)

## Open questions carried forward

1. **Is settlement growth/decline authoritative state or a derived relation over
   population/resource/hazard facts already tracked elsewhere?** Not decided here.
2. Whether `PlaceState.scale` is ever mutated during simulation (as opposed to only at
   world-compile time) was not exhaustively confirmed this batch — a repository-realization
   fact for future investigation, not a Rule Catalog decision.
3. **Partially resolved by a second 2026-09-22 follow-up.** The *default* relationship
   between Place identity, settlement status, and population presence is now stated
   (SETT-01, revised): settlement status may end/become dormant while Place identity
   persists by default (PLACE-03). What remains genuinely open, and is not decided here: in
   the total-abandonment-then-unrelated-resettlement case specifically, does the later
   resettlement *reactivate* the same settlement identity, or *establish a new one*? SETT-01
   explicitly declines to give one universal answer to that narrower question, and no
   repository mechanism exists to test either answer against (PT-S05's own confirmed MISSING
   finding, extended).
