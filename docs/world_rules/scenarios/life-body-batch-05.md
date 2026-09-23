---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Scenario Bank: Life / Body / Survival / Ecology (Batch 05)

**Purpose/scope.** Sixteen scenarios used to pressure-test the Lifecycle, Body/Condition,
Survival Needs, and Ecology/Population rule families in `life-body/lifecycle.md`,
`life-body/body-condition.md`, `life-body/survival-needs.md`, and
`life-body/ecology-population.md`, per `tmp/world-rule-batch-5-ext-ai.md`. Covers all sixteen
required probes (wounded but alive, defeated but not dead, HP zero boundary, injury without
combat, hazard but protected, persistent injury, recovery, survival pressure, need exists but
no consequence, birth creates new identity, parent ≠ child identity, population decline,
aggregate pressure returns to individuals, population change does not rewrite everyone,
predator-prey pressure, death with persistent history).

Scoring uses the same vocabulary as prior batches: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current
repository behavior, not the ideal design.

---

## LB-S01 — Wounded but alive

An entity receives serious harm in combat, remains alive, and its capability is reduced —
later behavior is genuinely constrained by the wound.

- **Rules invoked:** LIFE-02 (defeat ≠ death), BODY-04 (body condition creates real
  capability consequences).
- **Result: covered.** `combat.alive` stays `True` at any `hp > 0`; `WoundState`/`ScarState`'s
  penalties are read directly into combat-stat recalculation — the wound is real and
  consequential without ending the entity's active participation.

## LB-S02 — Defeated but not dead

A combat loss incapacitates a subject, but it survives — no accidental `defeat = death`
assumption anywhere.

- **Rules invoked:** LIFE-01 (active participation ≠ permanent termination), LIFE-02.
- **Result: covered.** `CombatResolutionSystem`'s `REBIRTH` outcome (`generation_delta=1`,
  `generation < 4`) and the `DEFEAT` outcome (Hero-role, `is_lethal=False`) both confirm a
  defeated subject can continue existing — `is_permadeath_set` is the only truly final marker,
  and it is not set in either case.

## LB-S03 — HP zero boundary

HP reaches zero. What semantic transition is actually implied?

- **Rules invoked:** BODY-01 (HP is a materialized abstraction), BODY-02 (zero HP triggers
  classification, not one automatic outcome).
- **Result: covered — the answer was determined, not assumed in advance.** Reaching
  `new_hp <= 0` triggers `CombatRewardClassificationService.classify_defeated_target()`, which
  resolves to one of `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH` depending on role and generation —
  zero HP is a necessary trigger for a real classification process, never a sufficient cause of
  any single predetermined result.

## LB-S04 — Injury without combat

Environment or an accident (not Combat) produces bodily harm, through the same Life/Body-owned
state.

- **Rules invoked:** BODY-07 (Life/Body owns bodily consequence, producer-neutral).
- **Result: covered.** Starvation (`src/engine/apply.py`'s `total_passive_dmg`) and
  environmental hazard (`EnvironmentService.calculate_hazard_drain()`, committed via
  `WorldDynamicsSystem`) both write to the same `combat.hp`/`CombatUpdate` structure Combat
  itself uses — confirming Life/Body's bodily-harm ownership is genuinely producer-neutral, not
  an artifact of Combat being the only thing that ever calls it.

## LB-S05 — Hazard but protected

A hazardous environment is entered, but the entity has valid protection/resistance — no or
reduced bodily consequence results.

- **Rules invoked:** BODY-07, ENV-02 (reused directly from Batch 04).
- **Result: covered — reuses Batch 04's own SPC-S13 evidence.**
  `get_hazard_immunities(faction_id)` returning a match zeroes the drain before it ever reaches
  Life/Body's own update path — confirming the "subject-specific protection" step this family's
  own BODY-07 depends on.

## LB-S06 — Persistent injury

Harm ends; the resulting wound persists; capability remains impaired later, independent of the
originating event still being active.

- **Rules invoked:** BODY-04, BODY-06 (persistence).
- **Result: covered.** `WoundState`/`ScarState` are durable records, independent of whether the
  originating combat encounter continues — reused directly from Batch 01's own evidence.

## LB-S07 — Recovery

An injury undergoes a valid recovery process; impairment decreases. No spontaneous healing
without declared semantics.

- **Rules invoked:** BODY-05.
- **Result: revealed missing rule — a stronger finding than the probe anticipated.** The probe
  asks for evidence that recovery requires a *declared* process; this batch found something
  more basic missing: no HP-recovery process, declared or otherwise, exists anywhere in the
  engine. `src/cognition/need_interpretation.py` shows entities can perceive a "healing" need
  and form goals around it, but nothing fulfills that need. This is recorded as the confirmed
  absence BODY-05 already names, not a violation of the "no spontaneous healing" standard
  (there is no healing at all to be spontaneous or otherwise).

## LB-S08 — Survival pressure

A need/resource shortage accumulates pressure that produces a real body/capability
consequence.

- **Rules invoked:** SURV-02.
- **Result: covered.** `hunger`/`sleep_debt` crossing declared thresholds produces HP damage,
  capacity degradation, and decision-priority changes — three independently-confirmed
  consequence types from the same accumulating pressure.

## LB-S09 — Need exists but no consequence (counter)

A tracked need-adjacent field exists that nothing ever consumes or reacts to.

- **Rules invoked:** SURV-04.
- **Result: revealed gap — the probe's literal target (hunger itself) turned out to be live,
  not inert; investigation found the real counter-example one level over.** `hunger` and
  `sleep_debt` are both heavily consumed (SURV-02) — they are not the inert case this
  counter-scenario is looking for. `last_meal_tick`/`last_sleep_tick`, however, are written on
  every meal/sleep action and read nowhere — confirmed directly, and confirmed as a genuine
  contrast against `well_rested_until` (a similarly-shaped field that *is* read by
  `EvolutionSystem`).

## LB-S10 — Birth creates new identity

Existing living subject(s) undergo a valid reproduction process; a new living subject results.

- **Rules invoked:** LIFE-04, ID-04 (reused directly).
- **Result: covered.** `V2EntityBuilder.birth_record()` constructs a genuinely new `entity_id`
  — reused directly from Batch 01's own ID-04 evidence.

## LB-S11 — Parent ≠ child identity (counter)

Provenance/lineage from reproduction does not imply identity continuity between parent and
child.

- **Rules invoked:** LIFE-04.
- **Result: covered.** `parent_a_entity_id`/`parent_b_entity_id` are recorded as provenance
  fields on the *new* entity's own record — they are never used to imply the child shares, or
  continues, either parent's own `entity_id`.

## LB-S12 — Population decline

Many individual deaths and/or migration events lead to an aggregate population decrease.

- **Rules invoked:** ECOL-03.
- **Result: partially covered — the statistical half holds, the individual-linked half does
  not.** `DemographicCycleService.process_demographics()` genuinely can decrease a cohort's
  count over time (`deaths = cohort.count * cohort.mortality_rate`), so aggregate decline as a
  phenomenon is real. But this decline is never actually driven by counting real named-entity
  deaths or migrations — the two systems are disconnected, exactly as ECOL-03 confirms. This
  scenario is scored against that confirmed gap, not assumed to pass because *some* kind of
  decline mechanism exists.

## LB-S13 — Aggregate pressure returns to individuals

Population pressure creates resource scarcity, which changes individual movement/decision/
survival prospects.

- **Rules invoked:** ECOL-04.
- **Result: covered — reuses Batch 01's CAUSE-02 evidence directly.**
  `compute_regional_scarcity()`/`_check_migration()` feed real scarcity/migration inputs back
  to individual decision-making, and `compute_population_density()`'s `DENSITY_FLOOR`
  saturation affects resource availability individuals actually experience.

## LB-S14 — Population change does not rewrite everyone (counter)

A regional population statistic changes; a specific, otherwise-unaffected individual retains
its own state unchanged.

- **Rules invoked:** ECOL-01, ECOL-02.
- **Result: covered.** `process_demographics()` writes only `WorldUpdate(population_cohorts_
set=...)` — no code path constructs or touches any named entity's own `EntityUpdate` from a
cohort-count change.

## LB-S15 — Predator-prey pressure

Predator abundance increases prey pressure, which changes ecological state and later
individual consequences. Kept schematic — no detailed food-web simulator is designed.

- **Rules invoked:** ECOL-04 (partial extension).
- **Result: partially covered, honestly uncertain rather than claimed either way.** An
  individual-level `ecological_predator` role classification exists
  (`src/content_semantics/role.py`), and general density/scarcity pressure (ECOL-04) is real —
  but no aggregate predator-count-to-prey-pressure formula specific to predation was found.
  Recorded as PARTIAL rather than either SUPPORTED (which would overclaim) or MISSING (which
  would underclaim what general pressure mechanisms already provide).

## LB-S16 — Death with persistent history

A subject dies, can no longer act, and its history/relationships/world consequences persist.

- **Rules invoked:** LIFE-03, ID-05, REACH-04, HP-01 (all reused directly).
- **Result: covered — reconfirms rather than newly discovers.** `_transfer_inherited_feud()`
  and `_seed_dying_wish()` (already established across Batches 01/02) confirm exactly this
  pattern; this scenario checks it holds when read from Lifecycle's own vantage point, which
  it does without requiring new evidence.

---

## Cross-batch note

LB-S04/S05 and Batch 04's own SPC-S04/S05/S13 are, in large part, the same underlying evidence
read from two families' vantage points — Environment's own exposure-establishment claim
(ENV-02) and Life/Body's own consequence-ownership claim (BODY-07) are two halves of one causal
chain, deliberately kept as two rules in two families rather than one rule spanning both, since
each half answers a genuinely distinct question (does a condition exist vs. who owns what
happens because of it).

LB-S07's and LB-S09's findings are this batch's own most significant new material: BODY-05
(no HP recovery mechanism exists at all) and SURV-04 (specific inert timestamp fields, not the
needs themselves) are both confirmed, real gaps — recorded honestly rather than assumed away,
consistent with every prior batch's own practice of naming absence rather than working around
it.

ECOL-03's finding (population decline is statistical, not individual-event-driven) is this
batch's single most load-bearing discovery — it means the causal loop this family's own
purpose statement describes (individual → aggregate → individual) is currently only half-real:
the aggregate → individual direction (ECOL-04) works; the individual → aggregate direction does
not yet exist for population counts specifically.
