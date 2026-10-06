---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE
phase: open
date: 2026-10-05
tags: [strategy, cognition, combat]
---

# TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE

## Title
`panic += region_trauma * 0.5` feeds an uncapped per-death counter into a 0-1 dread score with a 0.4
flee threshold — so **one death in a region makes most entities flee and two makes all of them**,
at any HP and any bravery. This is the progression-starvation chain's root cause.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary

> **CORRECTION 2026-10-05, planner. The headline evidence in this ticket did not reproduce, and the
> priority is lowered from P0 to P1 on that basis. The defect is still real; the claim that it is the
> dominant gate is withdrawn.**
>
> `rpg-implementer` re-ran the same read-only forced-decision probe (`forced_brain.py`, `crowded_frontier`,
> real states, live hostile at Manhattan <= 1) on a post-#344 tree, where identical runs no longer
> diverge. **The old "`PANIC_RETREAT` 143 of 147 (97%)" does not reproduce.** New result over **353**
> forced calls: `PANIC_RETREAT` **141 (40%)**, **`BRACKETING` 194 (55%)**, `ATTACK` 15 (4%), plain move 3.
> 27 of the 141 flees are at hp < 0.4; 114 at hp >= 0.4.
>
> The population also changed (353 calls vs 147), so this is **not** attributable to #344 alone and the
> implementer correctly declines to call it a pure #344 effect. Both numbers and the population change
> are reported in its ticket.
>
> **What survives unchanged:** trauma contributes to **every** recomputed flee (143 of 143 at
> `trauma >= 0.8` on `crowded_frontier`), panic **saturates at trauma 3.0**, and the units mismatch this
> ticket describes is arithmetic about the mapping, not a measurement. So the **ratification request is
> unchanged in substance.**
>
> **What is withdrawn:** "everyone flees", and this ticket's status as the dominant gate on the
> progression-starvation chain. The larger non-attack outcome is `BRACKETING` at 55%, which is **not an
> appraisal problem at all** — see `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`.
> If that investigation shows `BRACKETING` is itself appraisal-driven, this priority should be revisited.
>
> **Still do not implement before ratification.** Lowering the priority does not change that, and the
> owner should be told the rate moved before being asked to ratify a mapping on it.

**The measurement is `rpg-implementer`'s**, taken across three probes while closing
`TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`, and filed by
`rpg-planner` on the implementer's report. **It is the third and final gate of the
`TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` diagnosis** and the only one still open.

### The chain, for context — three gates, not one

The decision-driven `ATTACK` path fires 0-2 times per 1000-2000 ticks while the incidental
opportunity-attack mechanic fires 181-2177. A month of investigation attributed this to perception,
scoring, tuning, and then to the goal-dispatch discard (`#291`). All of those were upstream of the
real sequence:

1. **Sticky task.** A pursuit `ENTITY_MOVE` never terminated, so `evaluate_entity_intent` was never
   re-invoked. Measured: **1953 of 1953** samples of a live entity at full readiness within one tile
   of its live target, with the tactical pass **not called that tick**. *Fixed* in the attack-path
   ticket (`pursuit_reached_attack_range` / `pursuit_completion_update`).
2. **Brain cadence.** A completed task leaves the entity idle, and `should_run(strategic cadence=10)`
   delays the brain ~5 ticks. *Deliberately not fixed* — it needs `scheduler.py` (contested) and gate
   3 makes it worthless.
3. **This ticket.**

### The finding

Forced read-only `evaluate_entity_intent` on real `crowded_frontier` states, every entity with a live
catalog-hostile at Manhattan ≤ 1, 2000 ticks — **147 calls**:

| decision | count |
|---|---|
| `PANIC_RETREAT` | **143 (97%)** |
| plain `ENTITY_MOVE` (no reason) | 3 |
| `ATTACK` | **1** |

**116 of the 143 flees were at hp ≥ 0.4.** Examples: hp **0.81**, bravery **0.84**; hp **0.99**,
bravery **0.52**. `if emotion.is_fleeing` is checked in `tactical.py` **before** the hostile scan and
before any attack can be considered, so a fleeing entity never evaluates an attack at all.

### The driver, isolated

A second probe recomputed each documented term of `AppraisalSystem.evaluate_emotional_state` on the
same 5-neighbour saliency-filtered input the tactical pass uses, for all 147 states (145 fleeing):

| term | flees it contributed to |
|---|---|
| **regional trauma** | **145 of 145** (alone in ~118; with low-HP in ~27) |
| outnumbered (`hostiles > allies*2`) | **0** |
| nemesis / grudge | **0** |

> **The planner's saliency-bias hypothesis is REFUTED.** It predicted the outnumbered ratio was
> biased by the 5-neighbour saliency window. That term never contributed to a single flee. Recorded
> because a refuted hypothesis is worth as much as a confirmed one here — it was the reason the
> investigation was allowed to continue before any contested file was touched.

**The mechanism is a units mismatch between two documented scales.**

- `region.trauma_score` is an **uncapped per-death counter**: `+1.0` per death, no ceiling, instability
  threshold **50.0**, exactly as Bible 05 §2 states (`world_dynamics.py:54-55`).
- `panic` is a **0-1 dread score** with a **flee threshold of 0.4**.
- The appraisal does `panic += region_trauma * 0.5`, feeding the raw counter straight in.

Consequences, arithmetic:

| region trauma | panic contribution | effect |
|---|---|---|
| 1.0 (one death) | +0.5 | flees unless bravery > 0.33 |
| 2.0 (two deaths) | +1.0 | **flees at any bravery**, any HP |

Traced on `crowded_frontier`, all regions compile at `0.0`: **tick 3** one death → `goblin_camp` 1.0;
**tick 6** two deaths → `bandit_road` 2.0. Decay is ~4% over a few ticks, so the state persists. By
tick 6 the world is one in which every entity in a region where two things have died runs from
everything, forever.

**Nothing defines the mapping.** Bible 04 and 05 do not say how `trauma_score` maps to panic. The
trauma term dates to the initial V2 commit. The `E52F` ticket's own text speaks of
`trauma_score > 0.5`, which only makes sense against a 0-1 scale — so the two scales were
conflated early and never reconciled.

## Scope
1. Decide and record the trauma → dread mapping. **This is a semantics choice, not an obvious fix**
   (see Assumptions for the options and the planner's recommendation). It needs the rule owner or the
   owner; do **not** pick it inside implementation.
2. Implement the ratified mapping in `AppraisalSystem.evaluate_emotional_state`.
3. Re-measure the 147-call probe after the change: the decision mix with a live hostile adjacent, and
   the decision-path `execute_attack` / `resolve_attack` counts on **both** `crowded_frontier` and
   `frontier_living_world`. **Report them whatever they are**, including if attacks stay at zero.
4. State the behavioural consequence. Entities will stop fleeing in situations where they currently
   flee, on every world. That is a disclosed re-baseline, not a silent improvement, and the SimQ
   anchors will move.
5. Document the mapping in the Mechanics Bible (04 or 05, wherever dread belongs) so the next reader
   cannot re-conflate the scales, and update `docs/parity_ledger/strategic_cognition.yaml`.
6. Add an invariant test that no **single** appraisal term can cross the flee threshold on its own,
   whatever the ratified mapping is. See Assumptions — this is worth having independently of option 1
   versus 2.

## Out of Scope
- **Tuning the flee threshold (0.4) or bravery's weight.** Owner decision 7 parks tuning. This ticket
  is about two scales that disagree, not about where the threshold should sit.
- **Changing `trauma_score`'s own definition or the 50.0 instability threshold.** Bible-stated law.
  Fix the consumer, not the law.
- **The trauma producer's defects.** Deaths credited to an overlapping neighbour
  (`TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`) and passive deaths adding no trauma
  at all are real and separately owned by Lane B. **They do not fix the scale** — see Assumptions.
- Gates 1 and 2 of the chain. Gate 1 is fixed; gate 2 is deliberately not.
- `scheduler.py`. Contested, and not implicated.

## Acceptance Criteria
- [ ] The mapping is ratified by the owner or the rule owner **before** implementation, recorded with
      who decided and when.
- [ ] Scope 3's re-measurement is reported for both worlds, including zeros, on a tree that has
      `TCK-20261005-DIRTY-SET-…` (PR #344) so the numbers are reproducible rather than samples.
- [ ] The no-single-term-decides invariant has a test.
- [ ] The Bible records the mapping; `strategic_cognition.yaml` updated.
- [ ] The behavioural consequence is stated, with the SimQ anchor movement named rather than
      discovered later.
- [ ] Determinism sweep green; any moved fixture explained, not regenerated.
- [ ] A deliberate-attack test (a tactical decision that sets an offensive ENTITY_ACT) on a world or seed with MEASURED hostile contact, i.e. an in-reach count K > 0 stated in the test, shows >= N deliberate attacks after the fix and fewer before (control arm). N is left for this ticket's investigation to set from the measured contact. K in reach must come from approach, not spawn adjacency (checked by the first in-reach decision's tick relative to spawn), or the test would skip the very gate under suspicion. The campaign episode test (`TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`) is NOT this signal; its XPASS is a bonus. The landing PR also re-measures that test's attempts, K and in-reach and records them in the campaign ticket (its revisit trigger).

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — **this is the chain's root cause.** Its
  `SEQUENCE.md` records item (1) as having answered the root question; that is now the first of three
  gates. **Correct that file when this lands, not before.**
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — produced all three
  measurements; closes with the three-gate map.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done) — the original 181-2177 vs 0-2
  split. Its verdict (the dispatch discard) was a real defect but not the reason combat is starved.
- `TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH` — risk evaluation, adjacent; re-read
  against this finding before acting on it.
- `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` — chain item (5), blocked until combat
  volume is not starved. **This is what was starving it.**
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — the producer side; coupled, not a fix.
- `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-…` (#344) — until merged, every number here is a
  sample.

## Related Docs
- `docs/mechanics/05_world_evolution.md` §2 — trauma `+1.0` per death, instability 50.0
- `docs/mechanics/04_strategic_cognition.md` — where the dread mapping should be documented
- `docs/parity_ledger/strategic_cognition.yaml`

## Related Stored Artifacts
_(the three probes were run by `rpg-implementer` and are not committed — ask for them rather than
rewriting one)_

## Related Code Areas
- `src/engine/cognition.py::AppraisalSystem.evaluate_emotional_state` — the `panic += region_trauma *
  0.5` term. **Lane A, uncontested.**
- `src/engine/tactical.py` — the `if emotion.is_fleeing` check, before the hostile scan
- `src/engine/world_dynamics.py:54-55` — the `+1.0`-per-death producer (**Lane B**)
- `get_region_trauma` / `get_region_for_position` — the appraisal's read path

## Assumptions / Open Questions

- **Added 2026-10-05 by the planner, after Lane B's region-lookup work: this ticket's trauma numbers
  were measured while the producer and the consumer of `region_trauma` disagreed about region
  membership, so they are not yet values.** The appraisal reads trauma through
  `DomainView.get_region_for_position`; the producer writes it through
  `SpatialQueryService.get_region_at`. Before `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER`
  the two applied different edge conventions (closed vs half-open), so an entity could appraise a
  different region's trauma than the one its own deaths accumulated into. Both now route through
  `src/core/region_resolution.py::resolve_region_among`.
  **Consequence for this ticket:** the units argument is unaffected (trauma 1.0 flees unless
  bravery > 0.33, trauma 2.0 flees at any bravery — that is arithmetic about the mapping, not a
  measurement). But the **observed** 143-of-147 `PANIC_RETREAT` rate, and the per-region trauma that
  drove it, must be **re-measured on `main` now that the region-lookup fix is landing**, before this
  ticket's evidence is cited to the owner or the rule owner. Lane B measured the credit-distribution
  effect on `frontier_living_world` as real but modest (credited-to-no-region 23 -> 16,
  `hometown` 7 -> 12 via the inclusive-edge fix); it is not zero.
  This does **not** weaken the ratification request, and it is **not** a reason to start implementing.
- **The three options, from the implementer, with the planner's recommendation.**
  1. **Normalise against the documented scale:** `dread = min(1, trauma / UNSTABLE_THRESHOLD) * k`.
  2. **Cap the term below the flee threshold** (e.g. max 0.3) so trauma biases but never decides alone.
  3. Leave the term and fix the producer only.

  **(3) is not a fix** — correcting which region is credited changes *whose* trauma it is, not the
  scale, and two deaths would still panic a region.

  **The planner recommends (1) in shape, with (2)'s insight kept as an invariant rather than as an
  alternative.** (1) is principled: it makes the units agree using the Bible's own `50.0` instability
  threshold as the saturation point, which is a documented boundary rather than an invented number,
  and it means a region with two deaths is correctly *not* treated as unstable. (2) alone leaves two
  incompatible scales wired together behind a clamp. But (2) names a real invariant — **no single
  appraisal term should cross the flee threshold on its own** — which is worth asserting whatever
  mapping is chosen, because it is what would have made this defect visible as a test failure years
  ago. `k` and the curve (linear, log, or saturating) remain the open parameter and are the owner's.
- **Coupling to the producer, which the implementer raised and is worth keeping:** these trauma values
  come from the same Death-triggered Trauma block Lane B found to be misattributing deaths across
  overlapping regions. So **which region claims a death today determines who flees.** Worse,
  `get_region_trauma(pos)` resolves through `get_region_for_position`, which for an overlapping point
  picks *one* region — so the appraisal and the producer may not even be reading the same region for
  the same position. Fixing the mapping here and the credit there are independent, but neither
  measurement is stable until both land.
- **Every number in this ticket is a single run on a branch lacking #344**, hence a sample rather than
  a value. The direction (97% flee, trauma in 145 of 145) is far too large to be noise; the exact
  counts are not load-bearing.
- Why this survived so long: nothing in the Bible defines the mapping, so there was no document for a
  parity check to disagree with, and no test asserted a bound on any single term's contribution.
- **Hypothesis (n=1, one seed; from the campaign-test grid, `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS`):** in seed 1337 the only in-reach decision (entity 18, tick 32, hp 1.0) chose SAFETY_PRESSURE_RETREAT, and the only ATTACK decision (entity 47, tick 33) was made from outside combat range; contact came at ticks 32 to 33, by approach. So in that campaign the defect looks like "entities never close to reach because they retreat at full HP" rather than "entities in reach do not attack". It matches the earlier flee-gate finding on the standard worlds (PANIC_RETREAT on 97% of contact evaluations), but this is one seed and 10 to 14 perceived-hostile decisions per run, not a rate.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
