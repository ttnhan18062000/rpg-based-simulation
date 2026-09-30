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

> **⚠️ One narrowing, 2026-09-30.** This paragraph originally also claimed "cohort counts are
> frozen at their compile-time seed values for the life of every run." **That part is withdrawn** —
> counts do move in 4 of 21 worlds, via a writer that is *not* this service. Everything else above
> is confirmed by a 21-world × 300-tick runtime probe: 0 `POPULATION_BIRTH` and 0
> `POPULATION_DEATH` events anywhere, largest bracket ever observed = 8. See Implementation Notes.

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

### 2026-09-30 — CONFIRMED BY RUNTIME EVIDENCE, with one claim narrowed

This section records two rounds of correction. The net result: **the defect is confirmed, more
strongly than when filed** — by runtime measurement rather than by arithmetic alone. One
subsidiary claim ("counts frozen") was wrong and is withdrawn.

**Round 1 — a runtime probe appeared to disprove the ticket.** `agent-working-implementer` ran 21
corpus worlds × 300 ticks (seed 42, `origin/main` `833b60306`; `cohort.py` byte-identical to this
branch) and reported 30 `POPULATION_BIRTH`/`POPULATION_DEATH` events in 6 worlds plus cohort totals
changing in 4. I conceded the whole premise.

**Round 2 — that reading was a probe artifact, and the concession was too broad.** The probe's
event filter matched any category *containing* the substring `POPULATION`, so all 30 events were
`POPULATION_MIGRATION`. Re-run with exact category names:

> **0 `POPULATION_BIRTH` and 0 `POPULATION_DEATH` events, in every one of the 21 worlds. Largest
> bracket count ever observed at any point in any run: 8.** 63 `process_demographics` calls, 30
> `POPULATION_MIGRATION` events in 6 worlds.

So the core claim holds and is now **runtime-verified, not just arithmetic**: no bracket anywhere
ever approaches 100, `net` is always 0, and the birth/death cycle never fires in any corpus world.
The registry entry `demographic_cohort_cycle` is accordingly `corpus_run`/**`contradicted`** (seeded
21/21, births/deaths never fire) — not `observed`.

**What IS withdrawn: "cohort counts are frozen for the life of every run."** Counts do move
(`dungeon_crawl` 32→29, `highland_traverse` 18→19, `simq_scale_stress_seed42` 68→69). That was a
real overclaim — it extrapolated a compile-time fact across a whole run and ignored this ticket's
own Assumptions section, which already named the two other writers. The movement is **not**
attributed to `process_demographics` and tracing it is this ticket's work (see below).

**Compile-time counts, all 9 loadable corpus compositions, per region per bracket:**

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

**Largest bracket at compile time is 6; largest ever observed mid-run is 8. Nothing reaches 100.**
So `net = int(count * 0.01) == 0` for every bracket of every world, at seeding and throughout a
300-tick run. The truncation is real, universal, and now measured rather than inferred.

### Open: what actually moves the counts

`process_demographics` **cannot decrease a count.** `births = count * 0.02`,
`deaths = count * 0.01`, so `births - deaths == count * 0.01 >= 0` and `net = int(...) >= 0`
always. The rates are never overridden anywhere: `_seed_population_cohorts` leaves both at the
dataclass defaults (`compiler.py:177-205` says so explicitly), and the only `mortality_rate *= 2.0`
in the tree (`cohort.py:104`) is a docstring describing *entity attribute* modifiers, not a cohort
field write. Verified by grep across `src/`.

That impossibility is what exposed the probe artifact: a decrease (`dungeon_crawl` 32→29) could not
have come from this service, which prompted the re-run that found the substring-filter bug. With
0 birth/death events confirmed, there is no longer any tension — `cohort.py:388-390` is the only
emitter of those categories in `src/`, and it never fired.

**So the observed movement has another source, and tracing it is this ticket's first task.** Two
known writers:
- `population_young_births_delta` (`apply_plan.py:129-136`, fed from
  `reproduction_humanoid.py:68`) — adds to `young` directly, independent of this cycle.
- `migrate_cohorts` (`cohort.py:281-302`) — moves population between regions; its
  `max(1, int(count * 0.30))` floor means it does **not** truncate to zero. The 30
  `POPULATION_MIGRATION` events in 6 worlds make this the leading candidate.

Migration alone should conserve a world's total, so `dungeon_crawl` 32→29 (a net loss of 3) is the
most diagnostic case — either migration is not conservative, or a third writer exists.

**Unreconciled measurement discrepancy:** `dungeon_crawl` compiles to 2 regions / total 12 by my
path (`WorldAssemblyResolver.assemble()` → `WorldCompiler.compile(spec, seed=42)`) but 4 regions /
total 32 by the probe's (`WorldRepository.load_world_with_context`, the same entry point
`tools/execution_census.py` uses). Two compile entry points disagree about the same world's region
count. That is worth its own look regardless of this ticket — it means "the corpus" is a different
set of worlds depending on which loader you ask.

### What this changes about the ticket

- **Severity stands at P1.** The runtime probe strengthened the case: the birth/death cycle is
  confirmed never to fire in any of 21 worlds, not merely predicted not to.
- **First task is tracing the count movement**, not fixing the truncation — the two are separate,
  and the fix direction should be chosen knowing which writer is actually active.
- The two candidate directions in Scope are unchanged.

Raw probe + script: `stored_artifacts/TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE/
runtime_probe.py` and `runtime_probe_output.jsonl`, committed at `0a96cdd9d` on branch
`retro-hardening-and-mechanism-verdict-evidence` (local, readable via the shared object store).

**Process note, worth keeping.** The first probe result looked like a clean disproof and I conceded
the entire premise rather than only the part that was actually contradicted. What recovered it was
checking one arithmetic invariant — `net` can never be negative — against the reported data, which
located the filter bug. Two lessons: a runtime probe is the right instrument for an absence claim
(the reason `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` exists), *and* a probe
is itself an instrument that can be wrong, so a contradicting measurement deserves the same
scrutiny as the claim it contradicts. Concede exactly what is disproven, not more.

## Test Summary
_(not started)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
