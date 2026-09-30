---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO
phase: open
date: 2026-09-30
tags: [world]
---

# TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO

## Title
`DemographicCycleService`'s birth/death cycle computes `net = int(count * 0.01)`, which truncates
to zero below 100 — the largest seeded bracket in the entire 9-world corpus is 6, so the cycle
cannot act on its own seeded inputs until another system inflates a cohort ~17×

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found 2026-09-30 while closing `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-
SEEDED` as `STALE-PREMISE`. That ticket's premise ("no world seeds `population_cohorts`") is false —
worlds do seed cohorts. But its own Implementation Notes flagged a distinct, deliberately
unresolved question: whether the per-200-tick birth/death math produces any *observable* change at
realistic seeded counts, noting "a 2% rate may round to zero every cycle."

**It does round to zero, and this is settled by arithmetic rather than by measurement.**
`src/domains/demographics/cohort.py:377-381`:

```python
births = cohort.count * cohort.birth_rate     # birth_rate = 0.02
deaths = cohort.count * cohort.mortality_rate # mortality_rate = 0.01
net = int(births - deaths)                    # == int(count * 0.01)
if net == 0:
    continue
```

`net >= 1` requires `count >= 100`. Real seeded counts are far below that: `hometown` declares the
corpus's largest population, 13, which `_seed_population_cohorts` (`worldbuilding/compiler.py:190`)
splits 30/50/20 into `{young: 4, adult: 6, elder: 3}`. The largest bracket in the corpus is **6**,
giving `net = int(0.06) = 0`.

**Consequences at seeded scale:** the `continue` fires for every bracket of every region; no
`WorldUpdate` is produced from this service and no `POPULATION_BIRTH`/`POPULATION_DEATH`
`WorldEvent` is emitted by it. There is no accumulator — the truncated fractional remainder is
discarded each cycle rather than carried, so the shortfall never adds up over time either.

> **⚠️ This paragraph originally read "cohort counts are frozen … for the life of every run,"
> settled by arithmetic. That is FALSE and was disproven by a runtime probe the same day — counts
> do move in 4 of 21 worlds and 30 population events were emitted. See Implementation Notes for
> the correction, what survives, and the unresolved attribution question. Do not act on the
> paragraph above without reading it.**

**This is the second, independent reason the demographic cohort cycle does nothing** — behind the
false "never seeded" premise sat a real defect of a completely different shape. The mechanism is
seeded, reached, and its guard opens; it is the arithmetic inside that is inert.

## Scope
- Fix the truncation so a sub-1.0 net delta is not silently discarded. Two candidate directions,
  **not chosen here** — this needs a design call before implementation:
  - **Fractional accumulator:** carry the remainder on the cohort (a new durable field) so
    fractional growth accrues across cycles and applies when it crosses 1.0. Preserves the declared
    rates; adds durable state that needs a typed model, lifecycle, and determinism review.
  - **Rate/scale re-basing:** treat `count` as a coarser abstraction (or raise the rates, or
    lengthen `COHORT_INTERVAL`) so a realistic cohort produces a whole-number delta per cycle.
    No new state; changes the declared demographic constants, so it is a balance decision.
- Decide whether `POPULATION_BIRTH`/`POPULATION_DEATH` `WorldEvent`s are expected to appear in a
  normal run. Nothing currently consumes them in a way that has been checked; confirm before
  treating their absence as the headline symptom.
- Add a regression test pinning that a realistically-seeded cohort actually changes over a
  corpus-length run, so this cannot silently re-freeze.

## Out of Scope
- The `STALE-PREMISE` seeding question — settled, and its ticket is closed.
- `migrate_cohorts`' own `max(1, int(cohort.count * 0.30))` (`cohort.py:281`). That path uses a
  `max(1, ...)` floor and so does **not** truncate to zero; it is not affected by this defect.
  Whether migration is separately reachable is a different question, not opened here.
- `population_young_births_delta` (`apply_plan.py:129-136`) — the independent humanoid-birth nudge
  path. See Assumptions.
- Any change to the mechanism registry's `demographic_cohort_cycle` entry — owned by
  `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE`.

## Acceptance Criteria
- [ ] A design decision recorded between the accumulator and re-basing directions (or a third),
      with the reasoning, before any implementation.
- [ ] A realistically-seeded cohort (counts 3–6) measurably changes over a corpus-length run.
- [ ] Whatever direction is chosen, the fractional remainder is not silently discarded.
- [ ] If the fix adds durable state, it satisfies the Durable State Rule: typed model, stable
      location, defined lifecycle, inspection visibility, tests.
- [ ] Determinism preserved — verify the state hash is stable across repeated identical runs.
- [ ] A regression test that fails if net delta returns to truncating to zero at seeded counts.
- [ ] If `WorldEvent` emission becomes newly live, confirm its consumers handle a non-empty stream.

## Related Tickets
- `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` — closed
  `STALE-PREMISE`; its Implementation Notes flagged this question and explicitly declined to
  answer it. This ticket answers it.
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — the classification epic whose closure
  surfaced this.
- `TCK-20260831-POPULATION-COHORT-SEEDING` — shipped the seeding this defect sits behind.
- `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE` — owns the separate birth-nudge path.
- `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` — registry-side corrections
  (written, not yet committed as of 2026-09-30).

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — retired 2026-09-30; its §6 is the
  false premise this defect was hiding behind.
- `docs/plans/unreachable_mechanism_classification.md` — the `STALE-PREMISE` verdict and evidence.
- `docs/mechanics/05_world_evolution.md` — the demographic/ecology chapter this must stay
  consistent with; check whether it states expected population dynamics, and update it plus the
  `world_dynamics.yaml` parity entry if behaviour changes.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/demographics/cohort.py:341-400` (`DemographicCycleService.process_demographics`,
  the defect at `:377-381`)
- `src/domains/demographics/cohort.py:28-62` (`PopulationCohort`, where an accumulator field would
  live)
- `src/worldbuilding/compiler.py:177-203, 449` (`_seed_population_cohorts`, the 30/50/20 split and
  the counts that make the truncation bite)
- `src/engine/world_dynamics.py:178-179` (the production caller)
- `src/engine/apply_plan.py:120-137` (cohort write path, incl. the separate birth nudge)
- `src/core/updates.py:857-887` (`population_cohorts_set` and its merge rule)

## Assumptions / Open Questions
- **Counts are not permanently capped below 100.** `population_young_births_delta`
  (`apply_plan.py:129-136`, fed from `src/world/reproduction_humanoid.py:68`) grows the `young`
  cohort independently of this cycle, so a bracket could in principle cross 100 and make the math
  live. **This has not been measured** — the claim here is that the cycle is inert at *seeded*
  counts, which is certain, not that counts can never rise. Worth measuring as part of the fix:
  if the nudge path routinely pushes cohorts over 100, the severity is lower than it looks.
- `migrate_cohorts` can concentrate population into one region (target gets
  `existing + emigrant_count`), another route above 100. Also unmeasured, same caveat.
- Whether frozen cohorts have any *observable* downstream effect is unconfirmed. `src/world/
  camp.py:148` and `src/world/reproduction_humanoid.py:68` both read
  `population_cohorts["young"]`, so there are real consumers — but whether their behaviour would
  visibly differ under changing counts has not been checked. This governs whether the fix is
  user-visible or bookkeeping-only, and should be settled before choosing a direction.
- The 0.02/0.01 rates have no cited source. Check whether they are a Mechanics Bible value or an
  unsourced constant before re-basing them — re-basing a Bible value requires a parity-ledger and
  possibly an `intentional_divergences.md` entry.

## Implementation Notes

### 2026-09-30 — CORRECTION: the Request Summary overclaims. Read this before acting on it.

A runtime probe by `agent-working-implementer` (21 corpus worlds × 300 ticks, seed 42, `origin/main`
`833b60306`; `cohort.py` byte-identical to this branch) found `process_demographics` ran 63 times,
**emitted 30 `POPULATION_BIRTH`/`POPULATION_DEATH` events in 6 of 21 worlds, and cohort totals
changed in 4** (`dungeon_crawl` 32→29, `highland_traverse` 18→19, `simq_scale_stress_seed42` 68→69).
The other 15 stayed frozen.

**So this ticket's "never emits an event / counts frozen in every run, settled by arithmetic" is
false as written.** The error was extrapolating a compile-time fact across a whole run — the very
single-world overgeneralisation that `docs/plans/world_composition_precondition_gap_finding.md` was
retired for on the same day. The ticket's own Assumptions section named the two growth paths that
break the extrapolation and the Request Summary ignored them.

**What survives, now verified across every world rather than one.** I compiled all 9 loadable
corpus compositions and read every region's per-bracket counts:

| world | regions | max bracket | total |
|---|---|---|---|
| `dungeon_crawl` | 2 | 3 | 12 |
| `frontier_extended` | 10 | 6 | 56 |
| `frontier_living_world` | 7 | 6 | 46 |
| `highland_traverse` | 5 | 6 | 18 |
| `swamp_border_world` | 4 | 6 | 26 |
| `urban_political` | 3 | 6 | 27 |
| `wilderness_survival` | 4 | 3 | 11 |
| `generated_frontier_3_42` | 6 | 6 | 44 |
| `simq_scale_stress_seed42` | 13 | 6 | 68 |

**The largest bracket in the entire corpus is 6, and no bracket anywhere reaches 100.** So
`net = int(count * 0.01) == 0` for every bracket of every world **at compile time**, in all 9
worlds and not just the one originally checked. The truncation is real and universal at seeding.
What is *not* established is that it stays that way for a whole run.

### The attribution is not settled, and this is the open question

`process_demographics` **cannot decrease a count.** `births = count * 0.02`, `deaths =
count * 0.01`, so `births - deaths == count * 0.01 >= 0` and `net = int(...) >= 0` always. The
rates are never overridden anywhere: `_seed_population_cohorts` leaves both at the dataclass
defaults (`compiler.py:177-205` docstring says so explicitly), and the only `mortality_rate *= 2.0`
in the tree (`cohort.py:104`) is a docstring describing *entity attribute* modifiers, not a write
to a cohort field. Confirmed by grep across `src/`.

**Therefore `dungeon_crawl` 32→29 cannot have come from this service**, and the +1 changes are
equally consistent with a different writer. Two other paths write cohort counts:
- `population_young_births_delta` (`apply_plan.py:129-136`, fed from
  `reproduction_humanoid.py:68`) — adds to `young` directly, independent of this cycle.
- `migrate_cohorts` (`cohort.py:281-302`) — moves population between regions; its
  `max(1, int(count * 0.30))` has a floor and does **not** truncate to zero.

Against that, `cohort.py:388-390` is the **only** emitter of `POPULATION_BIRTH`/`POPULATION_DEATH`
in `src/` (verified by grep), so 30 emitted events do mean `net != 0` fired 30 times — which
requires some bracket to have reached ≥100 *during* the run, from a seed of ≤6. Both facts are
solid and they are in tension. Resolving that tension is the first task.

Note also `dungeon_crawl` compiles to a total of **12** here versus the probe's starting 32. That
discrepancy is unexplained and should be reconciled before either dataset is trusted — likely a
parameterised-module difference (`dungeon_crawl` uses `module_refs` with
`parameters: danger_scale: 2`, unlike the plain `modules:` list other compositions use).

### What this changes about the ticket

- **Severity is lower than filed.** Not "the mechanism never does anything" but "the mechanism is
  inert at seeded scale, and only escapes that when another system inflates a cohort ~17× first."
  Still a real defect — a rate-driven cycle that cannot act on its own seeded inputs — but P1 may
  be too high. Re-rate after the attribution question is answered.
- **First task is now attribution, not fixing.** Determine which writer produced each observed
  change before designing a fix. A fix aimed at the truncation is wasted if the observed movement
  came from reproduction.
- The two candidate directions in Scope are unchanged, but neither should be chosen until the
  above is resolved.

Raw probe data: `stored_artifacts/TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE/
runtime_probe_output.jsonl` (pending that batch's commit). Registry entry
`demographic_cohort_cycle` is now `corpus_run`/`observed` with this nuance.

**Credit:** the overclaim was caught by `agent-working-implementer`'s runtime probe, not by me. It
is the correct instrument for an absence claim — exactly the lesson
`TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` exists to institutionalise, and I
had just finished writing that lesson up when I made the same mistake in this ticket.

## Test Summary
_(not started)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
