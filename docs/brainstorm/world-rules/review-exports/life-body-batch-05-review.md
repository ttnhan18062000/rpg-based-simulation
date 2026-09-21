---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 05 (Life / Body / Survival / Ecology)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

The second domain-facing (Milestone B) batch, and a high-priority one — individual living
entities are the primary narrative subjects of the simulation. Four rule families: Lifecycle,
Body/Condition, Survival Needs, Ecology/Population. Files live under `life-body/`, per the batch
instruction's own directory suggestion; no split or merge was found necessary beyond the four
families already suggested.

## Canonical files included

- `life-body/lifecycle.md` (LIFE-01–06)
- `life-body/body-condition.md` (BODY-01–07)
- `life-body/survival-needs.md` (SURV-01–04)
- `life-body/ecology-population.md` (ECOL-01–05)
- `scenarios/life-body-batch-05.md` (LB-S01–S16)

## Rule Inventory

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| LIFE-01 | Active Participation ≠ Permanent Termination | `combat.alive` and `is_permadeath_set` are separately tracked facts. | Accepted |
| LIFE-02 | Incapacitation/Defeat ≠ Necessarily Death | A real classification (KILL/DEFEAT/REBIRTH/PERMADEATH) determines fate, not one automatic outcome. | Accepted |
| LIFE-03 | Death Terminates Participation, Not Identity/History | Restates ID-05/HP-01 at this family's point of use. | Accepted, by reuse |
| LIFE-04 | Reproduction Establishes a New, Distinct Identity | Restates ID-04 for Lifecycle; defers family-meaning content. | Accepted |
| LIFE-05 | Biological Parentage ≠ Social/Familial Meaning | Explicit scope boundary — defers to Family/Lineage. | Accepted, scope boundary |
| LIFE-06 | Lifecycle Transitions Require a Valid Trigger | Restates TRANS-01 for lifecycle transitions. | Accepted |
| BODY-01 | HP Is a Materialized Abstraction, Not Complete Physical Truth | HP and richer wound detail coexist; HP claims no biological completeness. | Accepted |
| BODY-02 | Zero HP Triggers Classification, Not One Automatic Outcome | Reaching zero is a necessary trigger, never sufficient for a predetermined result. | Accepted |
| BODY-03 | HP Loss and Injury Are Related but Not Identical | Coupled at the one production site checked; independence unverified either way. | Accepted, PARTIAL evidence |
| BODY-04 | Body Condition Creates Real Capability Consequences | Never decorative numbers — wound penalties are read into real recalculation. | Accepted |
| BODY-05 | Recovery Requires a Valid, Declared Process | Confirmed gap: no HP-recovery process exists at all, declared or otherwise. | Accepted (mechanism MISSING) |
| BODY-06 | Persistent Injury May Outlast the Harmful Event | Legitimate, expected persistence, not a bug. | Accepted |
| BODY-07 | Life/Body Owns Bodily Consequence of Exposure, Given Protection | Resolves Batch 04's ENV-03 open question for bodily harm specifically. | Accepted |
| SURV-01 | Need ≠ Resource ≠ Cost ≠ Body Condition ≠ Pressure | Category distinction, confirmed by contrast. | Accepted |
| SURV-02 | Need Pressure Accumulates; Thresholds Produce Real Consequences | Richly evidenced across HP, capacity, and decision-priority consequences. | Accepted |
| SURV-03 | Only Causally-Consequential Needs Are Modeled | Scope discipline, matching COST-04. | Accepted |
| SURV-04 | Need-Adjacent State With No Consumer Is Inert | Confirmed: `last_meal_tick`/`last_sleep_tick`, contrasted against the live `well_rested_until`. | Accepted (one confirmed inert pair) |
| ECOL-01 | Individual and Aggregate Ecology Are Distinct Representations | Restates ID-07 for this domain. | Accepted |
| ECOL-02 | Aggregate Change Doesn't Automatically Mutate Individuals | The same ID-07 boundary, from its own direction. | Accepted |
| ECOL-03 | Aggregate Population Change Is Currently Statistical, Not Individual-Event-Driven | Confirmed gap: `process_demographics()` never reads real birth/death events. | Accepted (confirmed real gap) |
| ECOL-04 | Aggregate Pressure Feeds Back Into Individual Behavior | The working half of the causal loop — reused from CAUSE-02/LIMIT-05. | Accepted |
| ECOL-05 | Regional Adjacency Is Geometric, Consistent With LOC-02 | Reconfirmation, not a new finding. | Accepted, by reconfirmation |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| LB-S01 | Wounded but Alive | serious harm → remains alive → capability reduced | Lifecycle, Body/Condition | Conflict & combat | Covered |
| LB-S02 | Defeated but Not Dead | combat loss → incapacitated → survives | Lifecycle | Conflict & combat | Covered |
| LB-S03 | HP Zero Boundary | HP reaches zero → classification, not one automatic outcome | Body/Condition | Conflict & combat | Covered |
| LB-S04 | Injury Without Combat | starvation/environment → bodily harm, same owned state | Body/Condition, State Ownership | Space/Environment | Covered |
| LB-S05 | Hazard but Protected | hazard → immunity → no/reduced consequence | Body/Condition, Environment | Space/Environment | Covered |
| LB-S06 | Persistent Injury | harm ends → wound persists → capability stays impaired | Body/Condition | Capability & progression | Covered |
| LB-S07 | Recovery | injury → valid recovery process → impairment decreases | Body/Condition | Capability & progression | Revealed gap |
| LB-S08 | Survival Pressure | need shortage → pressure accumulates → body/capability consequence | Survival Needs | Agency/decision | Covered |
| LB-S09 | Need Exists but No Consequence (counter) | tracked field → no consumer | Survival Needs | Agency/decision | Revealed gap |
| LB-S10 | Birth Creates New Identity | reproduction → new living subject | Lifecycle, Identity | Family/lineage | Covered |
| LB-S11 | Parent ≠ Child Identity (counter) | provenance ≠ identity continuity | Lifecycle, Identity | Family/lineage | Covered |
| LB-S12 | Population Decline | deaths/migration → aggregate decreases | Ecology/Population | Politics/authority & war | Partial |
| LB-S13 | Aggregate Pressure Returns to Individuals | scarcity → individual decision/survival change | Ecology/Population, Causality | Agency/decision | Covered |
| LB-S14 | Population Change Does Not Rewrite Everyone (counter) | aggregate changes → unaffected individual unchanged | Ecology/Population, Identity | none | Covered |
| LB-S15 | Predator-Prey Pressure | predator abundance → prey pressure (schematic) | Ecology/Population | Ecology (future refinement) | Partial |
| LB-S16 | Death With Persistent History | death → cannot act → history/relationships persist | Lifecycle, Identity, Reach, History/Provenance | Family/lineage, Politics | Covered |

## Coverage Summary

**Lifecycle**
- active-participation vs. permanent termination — LB-S01, LB-S02, LB-S03
- classification over automatic outcome — LB-S03
- death preserves identity/history — LB-S16
- reproduction creates new identity, provenance ≠ continuity — LB-S10, LB-S11

**Body/Condition**
- HP as abstraction, coexisting with richer detail — LB-S03
- capability consequences, never decorative — LB-S01, LB-S06
- recovery, confirmed absent — LB-S07
- producer-neutral ownership — LB-S04, LB-S05

**Survival Needs**
- category distinction — evidenced by contrast, no dedicated scenario
- accumulation → threshold → consequence — LB-S08
- inert adjacent state, confirmed — LB-S09

**Ecology/Population**
- individual/aggregate separation, both directions — LB-S12, LB-S14
- aggregate → individual feedback, working — LB-S13
- individual → aggregate feedback, confirmed gap — LB-S12
- schematic predation, honestly uncertain — LB-S15

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with every prior batch's own framing:

- LIFE-05's family-meaning boundary (surname, inheritance, dynastic legitimacy) stays fully
  with Family/Lineage — not designed here.
- BODY-05's confirmed absence of any HP recovery mechanism is deferred, but flagged as
  worth prioritizing given how foundational "can an injured entity ever get better" is for a
  lived-history-focused simulation.
- SURV-04's confirmed inert fields (`last_meal_tick`/`last_sleep_tick`) — whether to wire them
  to a real consumer is deferred to a future Agency/decision batch.
- ECOL-03's confirmed gap (population change not driven by individual events) is deferred, but
  is this batch's single most load-bearing finding — affects any future domain wanting named-
  entity history to visibly affect population counts.
- LB-S15's predator-prey uncertainty is deferred to a future Ecology-focused pass, recorded
  honestly as PARTIAL rather than resolved either way.
- §13's transformation boundary (human→vampire, species evolution, magical corruption) stays
  with Capability/Progression and Magic/supernatural, per the batch instruction's own
  explicit deferral — not touched here beyond LIFE-06's general trigger-validity restatement.

## Cross-domain findings

- Lifecycle ↔ Identity/History-Provenance: LIFE-01/02/03 and LB-S02/S16 are, in large part,
  reconfirmations of ID-05/HP-01/REACH-04 from Lifecycle's own vantage point — the pattern
  every domain-facing batch so far has found (foundational Rules predict most of a domain's
  own shape).
- Body/Condition ↔ Space/Environment/Movement: BODY-07 is this batch's own resolution of one
  of Batch 04's explicitly-carried-forward open questions (ENV-03's "which domain owns
  exposure's consequence") — resolved for bodily harm specifically, not for every possible
  exposure-consequence type.
- Body/Condition ↔ State Ownership: LB-S04 confirms Life/Body's bodily-harm ownership is
  genuinely producer-neutral — both Combat and Environment/starvation write through the same
  owned path, matching OWN-02's own participation-≠-ownership discipline from a new angle.
- Survival Needs ↔ Capacity: SURV-02 reuses LIMIT-02 directly (capacity degrading under
  strain) rather than re-deriving the same finding for Needs specifically.
- Ecology/Population ↔ Causality: ECOL-03's confirmed gap is exactly a CAUSE-01 violation risk
  waiting to happen — if a future domain ever *claims* population reflects individual history
  without checking, that claim would fail CAUSE-01's real-causal-path requirement; this batch
  flags the gap now so that claim is never made without first closing it.
- Ecology/Population ↔ Location/Topology: ECOL-05 reconfirms LOC-02's geometric-adjacency
  finding independently, via a second, unrelated subsystem (`find_adjacent_regions()`) —
  strengthening rather than revising Batch 04's own finding.

**Explicit call-out — semantic meaning of HP:** HP is a materialized abstraction representing
survivability/accumulated harm (BODY-01), not a complete physical description; richer detail
(`WoundState`/`ScarState`) coexists specifically where it adds capability consequences a bare
scalar couldn't.

**Explicit call-out — death/lifecycle boundary:** `combat.alive=False` (incapacitation, from
any producer) and `is_permadeath_set=True` (true, final death) are two separately-tracked
facts (LIFE-01); reaching zero HP triggers a real classification (KILL/DEFEAT/REBIRTH/
PERMADEATH), never a single hardcoded transition (BODY-02).

**Explicit call-out — which body states have real consumers:** `WoundState`/`ScarState`
penalties (BODY-04, live), `hunger`/`sleep_debt`/`rest_pressure` (SURV-02, live, richly so) —
vs. `last_meal_tick`/`last_sleep_tick` (SURV-04, confirmed inert).

**Explicit call-out — individual ↔ aggregate ecology causal links:** aggregate → individual is
real and evidenced (ECOL-04, scarcity/migration/saturation); individual → aggregate is
confirmed MISSING for population counts specifically (ECOL-03) — the loop this family's own
purpose statement describes is currently only half-built.

**Explicit call-out — causally inert survival/body state:** `last_meal_tick`/`last_sleep_tick`
(SURV-04) are the confirmed inert pair; no inert *body-condition* field was found (`WoundState`/
`ScarState` are fully live) — the inert-state pattern this batch found lives in Survival Needs,
not Body/Condition.

**Explicit call-out — Combat vs. Life state ownership:** Combat produces the *event* (an
attack, a starvation tick); Life/Body's own `combat.hp`/`CombatUpdate` path is what actually
commits the result, regardless of producer (LB-S04) — Combat is a producer among several, not
the owner, consistent with the correction Batch 04's own follow-up already applied to
Environment (ENV-03).

**Explicit call-out — how much biological detail was deliberately NOT modeled:** No detailed
wound-location/organ-system simulation (BODY-01's own abstraction stance); no temperature/
shelter *need* distinct from Environment's own exposure mechanism (Survival Needs' own open
question); no predator-prey-specific aggregate formula beyond general density/scarcity
pressure (LB-S15, PARTIAL); no transformation content (human→vampire, species evolution) — all
deliberately deferred, per the batch instruction's own "avoid invisible realism" discipline.

## Open questions

1. BODY-03's HP-loss/injury coupling was only confirmed at one production site — whether a
   future mechanism should produce one without the other is not decided.
2. BODY-05's confirmed absence of any HP recovery mechanism — the most load-bearing MISSING
   finding in Body/Condition. Not designed here; flagged as worth prioritizing.
3. SURV-04's confirmed inert fields — wire to a consumer or leave forward-declared? Not
   decided.
4. ECOL-03's confirmed gap — the most load-bearing finding in this whole batch. Deferred to
   whichever future batch first needs population counts to reflect real named-entity events.
5. LB-S15's predator-prey uncertainty — deferred to a future Ecology-focused pass.
6. Whether `DEFEAT` (non-lethal, non-rebirth-eligible) is a live, reachable outcome for any
   currently-classified entity kind, or a vestigial label, was not resolved (LIFE-02's own open
   question).

## Repository evidence

No CONFLICTING or UNKNOWN findings. Two confirmed MISSING mechanisms with real weight: BODY-05
(no HP recovery anywhere) and ECOL-03 (population change disconnected from individual events).
One confirmed inert pair: `last_meal_tick`/`last_sleep_tick` (SURV-04). One PARTIAL finding
recorded honestly rather than resolved either way: BODY-03's HP-loss/injury coupling, confirmed
at one site, not verified for independence.

Key evidence, all confirmed by direct code inspection: `src/engine/combat.py`
(`CombatResolutionSystem`, `new_hp <= 0`, `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`,
`is_lethal`), `src/core/updates.py` (`LifecycleUpdate.is_permadeath_set`, no `active_set`
field), `src/engine/apply.py` (passive hunger/sleep_debt accumulation, starvation
`total_passive_dmg`), `src/cognition/need_interpretation.py` (`InterpretedNeed(key="healing",
...)` with no fulfillment path), `src/strategy/cognition_capacity.py` (fatigue-driven capacity
degradation, reused), `src/systems/world_systems/routine.py`, `src/systems/
strategic_systems/intelligence.py`, `work_queue.py` (hunger-driven decision-priority
consequences), `src/core/state.py` (`BiologicalComponent`'s full field list), `src/engine/
evolution.py` (`well_rested_until` consumption, confirming the contrast against inert
timestamps), `src/domains/demographics/cohort.py` (`PopulationCohort`, `process_demographics`'s
statistical birth/death formula, `find_adjacent_regions`'s geometric adjacency,
`compute_regional_scarcity`, `compute_population_density`), `src/content_semantics/role.py`
(`ecological_predator` role classification).

## Owner-attention decisions

- Whether BODY-05's HP-recovery gap should be prioritized ahead of its "natural" place in the
  design order, given how foundational recovery feels for any entity expected to have a real
  lived history rather than a one-way trajectory toward permadeath.
- Whether ECOL-03's individual↔aggregate population link should be prioritized, given how many
  future domains (Politics/authority & war's own war-casualty content, most plausibly) would
  want population counts to reflect real named-entity events.
- Whether `last_meal_tick`/`last_sleep_tick` should be wired to a consumer now or left
  forward-declared.

## Starter-candidate disposition summary

22 rules drafted across four families (6 Lifecycle, 7 Body/Condition, 4 Survival Needs, 5
Ecology/Population) — all 22 accepted, 0 rejected, 0 split, 0 merged. The batch instruction's
own suggested file grouping was kept as-is — no split or merge was found necessary beyond the
four families already proposed. No rule was rejected as an implementation concern; the
batch's own explicit non-goals (detailed wound-location simulation, transformation content,
universal need catalogs, detailed food-web ecology) were respected throughout rather than
quietly designed anyway.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/life-body-batch-05-report.md` (local review report, not part of this catalog).

---

> **BATCH 05 (LIFE / BODY / SURVIVAL / ECOLOGY) READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist: four rule-family files (22 rules), one scenario file (16
scenarios covering all sixteen required probes), this review export with all nine required
sections plus every explicitly-required call-out, and a local disposition report. No
contradiction was found against any prior batch or within this one — this batch's own
genuinely new material is concentrated in two significant confirmed gaps (BODY-05's absent
recovery mechanism; ECOL-03's disconnected individual/aggregate population link) and one
confirmed inert field pair, rather than in tension with anything already accepted. Per the
batch instruction's stop condition: all twelve checklist items are satisfied. Do not begin
Batch 06 (Perception / Knowledge / Information / Agency) until this batch receives high-level
review.
