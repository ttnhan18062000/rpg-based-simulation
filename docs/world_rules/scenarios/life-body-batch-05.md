---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-10-09"
---

# Scenario Bank: Life / Body / Survival / Ecology (Batch 05)

**Purpose/scope.** Nineteen scenarios (LB-S17 and LB-S18 added 2026-10-08, LB-S19 added 2026-10-09) used to pressure-test the Lifecycle, Body/Condition,
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
- **Result: permitted, not currently realised (revised `2026-10-01`).** No current mechanism lets a defeated subject survive. `KILL` and terminal `DEFEAT` (opportunity attack, `is_lethal=False`) are both recorded, classified, final deaths. The former hero `REBIRTH` previously cited here was an undeclared resurrection and has been retired (`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`; see LIFE-02 and STR-02). The scenario's actual requirement, no *accidental* `defeat = death` assumption, still holds: each death is a declared lifecycle classification, never an implicit consequence of HP reaching zero.

## LB-S03 — HP zero boundary

HP reaches zero. What semantic transition is actually implied?

- **Rules invoked:** BODY-01 (HP is a materialized abstraction), BODY-02 (zero HP triggers
  classification, not one automatic outcome).
- **Result: covered for cause; fate not currently realised (revised 2026-10-01).** Reaching `new_hp <= 0` still triggers a real classification, never an assumed one. Combat classifies `KILL` or terminal `DEFEAT` by the attack's own lethality (`is_lethal`; opportunity attacks are non-lethal), not by the subject's role. Lifecycle then records the death with a declared cause (`COMBAT`, `DEFEAT`, `HAZARD`, `STARVATION`, `SLEEP_DEPRIVATION`). The former role- and generation-dependent branch (`REBIRTH`/`PERMADEATH`) was retired, and the `generation` field removed. Zero HP is a necessary trigger for cause classification. Fate is not currently classified: every zero-HP outcome today is a final death, and no declared route to continued existence exists (permitted by LIFE-02 and BODY-02, not required).

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


## LB-S17 — A broke worker forages wild land and eats what it carries (SURV-06, decision 29) (added 2026-10-08)

A worker who cannot pay for a meal walks out of town to wild land, gathers wild food, carries it,
and eats it when hungry. The patch it stripped is dry for a while and then grows back. Where the
land holds no wild food, the same worker cannot forage, and nothing feeds it for free.

- **Rules invoked:** SURV-06 (a person meets hunger by eating food it carries, which it may
  forage; decision 29's amendment: wild food belongs to the land, by biome, outside
  settlements), SURV-07 with decision 27 (a need with no open way pulls toward the step that
  opens one), RES-05 (regrowth by a declared process), Bible 03 (conservation).
- **Kernel spec (`mechanic_scenario`, `tests/mechanic_scenarios/`, through
  `tests/helpers/scenario.py`).** The same staging runs in two arms, differing only in the
  biome of the wild region next to the settlement:
  - **Staging:** a compiled world with a settlement that has an inn, and one wild region beside
    it, outside the settlement bounds. Worker W is a people-kind, non-cautious, with 0 gold and
    no carried food, starting inside the settlement with hunger already pressing (past the
    point where decision 27's pull applies). There are no hostiles. The window covers the walk
    out, the gathering, the eating, and at least one regrowth interval of the node.
  - **Main arm (the wild region is a HIGH-fertility biome, e.g. `near_forest`, with its
    wild-food node or nodes placed by the biome table):** W leaves the settlement and gathers
    at a wild-food node. The node's charges fall, and W's inventory gains the wild-food item by
    the same amount. Later W eats from what it carries: its hunger falls, and its carried count
    falls by one per meal. W's gold is unchanged and no inn meal is served to it. Conservation
    holds: the item enters only by gathering and leaves only by eating. Once a node is stripped
    to 0 (`RESOURCE_DEPLETED`), it refills later (`RESOURCE_RECOVERED`). All effects are read
    from authoritative state, not log lines.
  - **Control arm (the same region with a NONE biome, e.g. `old_mine`, so the biome table places
    no wild food):** W gathers no wild food and never holds any. No meal lowers W's hunger
    without payment. W's hunger keeps rising inside the window. Whether W dies is not an
    observable here.
  - **Why the control:** it proves the main arm's food came from the land, through foraging,
    and not from engine charity or a free meal. It also proves that the biome decides whether
    wild food exists.
  - **Also checked in the main arm:** no wild-food node sits inside the settlement bounds.
- **Result (2026-10-09): covered in its no-inn form** since #454 (`0b4f12af7`) by
  `tests/mechanic_scenarios/test_forage_loop_wild_food.py` (5 passed). It is staged with no inn
  in reach, because free meals stay on until the parked removal
  (`TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL`) lands. The full
  form, a broke worker who forages although an inn is in reach, waits for that removal.
- **Earlier result (2026-10-08): revealed missing rule implementation on main.** No world places wild
  food by biome. The one food node in each of the three measured worlds sits on town land, and
  EAT consumes no carried food (SURV-06's evidence). Expected to be **covered** once decision
  27's PR (Lane B) lands and this spec passes at kernel level.


## LB-S18 — Starvation weakens first and kills over days (SURV-02 amendment, decision 36) (added 2026-10-08)

A creature with no food, a person or an animal, crosses the starvation line, becomes weaker
within hours, starts losing health only later, and dies after about two to three days. One that
eats does none of this.

- **Rules invoked:** SURV-02 (crossing a threshold has real consequences; decision 36 makes
  them staged), SURV-07 (the pull to eat), Bible 05 §1 (2,400 ticks = 1 day).
- **Kernel spec (`mechanic_scenario`).** Two arms, differing only in access to food:
  - **Staging:** a compiled world with one people-kind subject S, a non-combatant, at full HP and
    full stats, with hunger just below the starvation line and no hostiles or ambient hazard.
    The window runs to at least 3.5 days (8,400 ticks) after S crosses the line.
  - **Main arm (no food reachable: no inn, no wild food, nothing carried, no money):**
    - S crosses the line.
    - **Stage 1, weakened:** within the first in-game hours past the line, S's capacity is
      degraded (slower recovery, a lower combat-effectiveness term), with no HP loss yet, or HP
      loss well below today's 2 per tick.
    - **Stage 2, starving:** later, S loses HP slowly.
    - **Death:** S dies of starvation between 2 and 3 days after crossing the line. It is alive
      at 1 day and dead by 3.5 days.
    - Each stage change is read from authoritative state.
  - **Control arm (an inn within reach, with money or a free meal):** S eats before or soon after
    the line, its hunger falls back below it, any weakening clears, and S is alive at the end.
  - **Why the control:** it proves the weakening and the death come from the unmet need, not
    from the staging.
  - **Second kind (added 2026-10-09, decision 42):** the main arm is repeated with one non-people
    living kind (for example a wolf), staged the same way. The same stage order holds, sized by
    that kind's own profile. The rule is not a people-only rule.
  - **Engineering, not observable:** the exact stage thresholds, the effects' sizes and the HP
    rate. The spec checks the stage order and the 2-to-3-day window only.
- **Result (2026-10-08): revealed contradiction on main.** `hunger >= 95.0` costs 2 HP per tick
  (`src/engine/apply.py`), so S dies about 50 ticks after the line (SURV-02's amendment
  evidence). Expected to be **covered** with Lane A's decision-36 ticket.

---

## LB-S19 — Extreme sleep debt weakens, then collapses the subject where it stands, with no HP loss (SURV-02 amendment, decision 41) (added 2026-10-09)

A creature, person or animal, that has gone far too long without sleep is weaker first, then
falls asleep where it stands, cannot act while asleep, and wakes once enough of the debt is slept
off. Its health never drops from lack of sleep. A rested one does none of this.

- **Rules invoked:** SURV-02 (crossing a threshold has real consequences; decision 41 makes
  sleep debt end in collapse, not in HP loss), Bible 01 (biological pressures: sleep debt
  accrues 0.05 per tick).
- **Kernel spec (`mechanic_scenario`).** Two arms, differing only in starting sleep debt:
  - **Staging:** a compiled world with one people-kind subject S, a non-combatant, at full HP,
    with hunger low (well below every hunger stage, so starvation cannot confound the reading),
    no hostiles and no ambient hazard. S is part way along a long committed walk across open
    ground, so a collapse shows as a stop away from any bed. The window runs until S has woken
    and walked on.
  - **Main arm (sleep debt just below the collapse line, above the weakened line):**
    - **Stage 1, weakened:** at staging, S's capacity is degraded (slower recovery, a lower
      combat-effectiveness term). It is not collapsed and still acts.
    - **Collapse:** within a few ticks S's debt reaches the collapse line, and S falls asleep
      where it stands, on the tile it occupied, not at a bed. Its committed walk stops.
    - **While collapsed:** S takes no action and does not move, and its sleep debt falls.
    - **Wake:** once its debt falls below the wake line, S can act again and resumes deciding
      (it may walk on). The weakening clears once its debt is below the weakened line.
    - **No HP loss:** S's HP is never lower than at staging at any tick in the window.
    - Each stage change is read from authoritative state.
  - **Control arm (sleep debt low):** S is not weakened and never collapses, completes or
    continues its walk, and its HP is unchanged.
  - **Why the control:** it proves the weakening and the collapse come from the debt, not from
    the staging or the walk.
  - **Second kind (added 2026-10-09, decision 42):** the main arm is repeated with one non-people
    living kind (for example a wolf), staged the same way. The same stage order holds, sized by
    that kind's own profile. The rule is not a people-only rule.
  - **Engineering, not observable:** the weakened threshold and effect sizes, the collapse line
    (decision 41 sets it at 98), the wake line, and the rest rate. The spec checks the stage
    order, "no action while collapsed", waking, and "no HP loss" only. rpg-planner's suggested
    numbers (2026-10-09): weakened at 80, reusing the existing attack x0.8 EXHAUSTION hook in
    `combat.py` plus regen x0.5 as in decision 36's `src/engine/starvation.py`, collapse at 98,
    and wake below about 60.
- **Result (2026-10-09): revealed contradiction on main.** `sleep_debt >= 98.0` costs 1 HP per
  tick (Bible 01, biological pressures), so S loses HP from the first tick past the line and
  dies about 100 ticks later, still walking. Expected to be **covered** with the decision-41 code
  ticket (`TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS`).

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
