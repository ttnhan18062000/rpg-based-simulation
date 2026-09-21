---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Ecology / Population

**Purpose/scope.** How many living subjects collectively create population/ecological
pressures, and how those pressures feed back into individual trajectories — kept explicitly
distinct from individual simulation. The governing causal loop is: individual actions/lifecycle
→ aggregate pressure/state → changed world conditions → new individual opportunities/
constraints. This family avoids universal detailed population biology, per the batch
instruction's own scope discipline.

**Status.** Batch 05 (Life/Body/Survival/Ecology), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-5-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

---

## ECOL-01 — Individual simulation and aggregate ecology/population state are distinct representations

> A named, individually-simulated subject and an aggregate population statistic are two
> different kinds of state, never collapsed into one. This restates ID-07 for this domain
> specifically.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED**, reused directly from Batch 01's ID-07 finding:
`PopulationCohort` (keyed by age bracket, tracking a `count`) and named `EntityState` records
are architecturally separate — a regional population count is explicitly "a weather system,"
never a stand-in for any individual's own trajectory.

**Scenarios:** [LB-S14](../scenarios/life-body-batch-05.md#lb-s14) (population change does not
rewrite everyone, counter).

---

## ECOL-02 — Aggregate population change does not automatically mutate every individual

> A population statistic changing (a regional cohort count rising or falling) does not, by
> itself, cause any change to a specific individual's own state. An aggregate effect reaching a
> specific individual requires a real, separate causal path.

**Disposition: ACCEPT.** The same ID-07 boundary as ECOL-01, stated from its own explicit
direction per the batch instruction's own worked example ("regional wolf population declines
≠ every wolf becomes weaker").

**Repository evidence: SUPPORTED, architecturally.** `DemographicCycleService.
process_demographics()` writes only `WorldUpdate(population_cohorts_set=...)` — it never
constructs or touches any `EntityUpdate` for a named entity. There is no code path by which a
cohort-count change directly edits a specific individual's own fields.

**Scenarios:** [LB-S14](../scenarios/life-body-batch-05.md#lb-s14).

---

## ECOL-03 — Aggregate population change currently evolves independently of actual individual births/deaths

> The causal loop this family's own purpose statement describes (individual actions/lifecycle
> → aggregate pressure) requires that aggregate change actually trace back to real individual
> events. This batch's own investigation found that this repository's current aggregate model
> does not yet do this — it is a confirmed, honestly-recorded gap, not assumed to already work.

**Disposition: ACCEPT the rule; REJECT the assumption that current behavior already satisfies
it.** The rule states what *should* be true (individual → aggregate is a real causal
direction); the repository evidence shows it currently isn't, for population counts
specifically.

**Repository evidence: MISSING, confirmed directly — a significant, load-bearing finding.**
`DemographicCycleService.process_demographics()` computes `births = cohort.count *
cohort.birth_rate` and `deaths = cohort.count * cohort.mortality_rate` — a purely statistical
function of the cohort's own existing count and declared rates. It does not read, count, or
react to any actual named-entity birth (`V2EntityBuilder.birth_record()`) or death
(`is_permadeath_set`) event anywhere. The aggregate population model and the individual
lifecycle model currently run as two disconnected systems for this specific link — matching
the batch instruction's own explicit flag ("individual deaths not affecting populations").

**Scenarios:** [LB-S12](../scenarios/life-body-batch-05.md#lb-s12) (population decline —
scored against this finding, not assumed to pass).

---

## ECOL-04 — Aggregate pressure may feed back into individual decision/behavior through a real causal path

> The other half of this family's causal loop — aggregate pressure → changed conditions → new
> individual opportunities/constraints — is a real, evidenced direction, distinct from ECOL-03's
> confirmed gap in the opposite direction.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, reusing evidence Batch 01/03/04 already gathered for
adjacent purposes.** `compute_regional_scarcity()` and `_check_migration()`
(`src/domains/demographics/cohort.py`) feed real scarcity/migration-decision inputs back to
individual entities — the same evidence base Batch 01's CAUSE-02 already confirmed for the
drought→scarcity→migration chain. `compute_population_density()`'s `DENSITY_FLOOR` saturation
(reused from Batch 03/04) is a further real aggregate-condition-affects-individual-outcome
path (regeneration rate, which individuals experience through resource availability).

**Scenarios:** [LB-S13](../scenarios/life-body-batch-05.md#lb-s13) (aggregate pressure returns
to individuals).

---

## ECOL-05 — Regional adjacency for ecological/migration purposes is geometric, consistent with Location/Topology's own finding

> Adjacency used for migration and ecological pressure calculations is determined the same way
> Location/Topology's own LOC-02 already found: by shared geometric boundary, not by a declared
> non-geometric connection. This is not a new finding — it is a second, independent
> confirmation of the same gap from a different subsystem.

**Disposition: ACCEPT, by reconfirmation rather than new claim.**

**Repository evidence: SUPPORTED as a reconfirmation.** `find_adjacent_regions()`
(`src/domains/demographics/cohort.py`) computes adjacency purely from `RegionState.bounds`
sharing an edge (`docs/mechanics/06_worldbuilding_foundation.md`'s own declared adjacency
definition) — the same geometric-only pattern LOC-02 already found in
`SpatialQueryService.get_region_at()`. This strengthens LOC-02's own finding; it does not
require revising it.

**Scenarios:** none newly traced; reuses Batch 04's own LOC-02 evidence and finding directly.

---

## Cross-domain links recorded here

- ECOL-01, ECOL-02 → Identity (ID-07, directly reused)
- ECOL-03 → Causality (CAUSE-01 — the missing causal link is exactly a CAUSE-01 gap, applied
  to population specifically), Family/lineage & succession, Politics/authority & war (any
  future domain wanting population counts to reflect actual named-entity events depends on
  this gap being closed)
- ECOL-04 → Causality (CAUSE-02, directly reused), Resource (RES-01, scarcity), Capacity
  (LIMIT-05, saturation, directly reused)
- ECOL-05 → Location/Topology (LOC-02, reconfirmation, not a new link)

## Open questions carried forward

1. **The most load-bearing finding in this family.** ECOL-03's confirmed gap (aggregate
   population change is statistical, not individual-event-driven) affects any future domain
   that wants population counts to reflect actual named-entity history (e.g., a named hero's
   death visibly denting a region's population, or a mass-reproduction event visibly growing
   one). Not designed here — flagged for whichever future batch (most plausibly a later
   Ecology/population-focused pass, or Politics/authority & war for war-driven population
   effects) first needs this link to be real.
2. Whether predator-prey pressure specifically (as opposed to general scarcity/density
   pressure) needs its own dedicated mechanism was not confirmed either way this batch — an
   individual-level `ecological_predator` role classification exists
   (`src/content_semantics/role.py`), but no aggregate predator-count-affects-prey-pressure
   formula was found. Recorded as PARTIAL, not claimed as either present or absent with
   confidence.
