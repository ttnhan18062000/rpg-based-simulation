---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION
artifact_type: investigation
tags: [world, root-cause]
---

# Investigation — global raid anchored at `(0,0)`

The ticket body carries the measurement table and the code trail. **This file does not restate them.**
It records what the measurement did not cover, what went wrong during implementation, and the facts
that decided the outcome.

Base: `958aa103d`.

> **READ §6 FIRST. The outcome is RETIREMENT, not the re-anchoring fix.**
> §2–§4 below were written while re-anchoring was the plan and describe that attempt. They are kept
> because the reasoning is what led to the withdrawal, but **they are not the outcome.** §6 records
> why re-anchoring was implemented, measured and then withdrawn, and §3's "the fix was narrowed"
> and §4's "AC-6 not measured" are both superseded there.

## 1. Not a discovery — a measured answer to a recorded question

`TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done) fixed the camp caller, deliberately left this one
byte-identical, and recorded in its own Open Questions: *"Confirm whether the existing global (non-camp)
raid path should keep its `(0,0)` assumption or share the same target-selection logic."*
`check_for_raid`'s docstring admitted the same thing. Checked `todos/` and `inprogress/` for an existing
ticket first — none. So the behaviour was known and the consequence was not; this supplies the
consequence.

## 2. The fact that constrained the fix: every corpus world has exactly one CITY

Measured by compiling each world (`WorldRepository.load_world_with_context` + `WorldCompiler.compile`,
seed 42):

| world | regions | places | kinds |
|---|---|---|---|
| `frontier_marches` | 9 | 4 | CITY 1, CAMP 1, RUIN 1, NEST 1 |
| `crowded_frontier` | 4 | 2 | CITY 1, CAMP 1 |
| `frontier_living_world` | 8 | 4 | CITY 1, CAMP 1, RUIN 1, NEST 1 |
| `urban_political` | 3 | 1 | CITY 1 |

This mattered because `PlaceState`'s own docstring warns that Place content migration was a separate
child ticket, so "are there even any CITY places?" was a live risk: if there were none, anchoring on a
city would have **silently disabled every global raid** — worse than the defect. Verified rather than
assumed.

## 3. Two things went wrong in implementation, both caught by tests

Recorded because they are the reusable part.

**(a) The first implementation changed raid frequency, not just placement.** Requiring a CITY and
returning no raid without one suppressed raids entirely in city-less worlds. That broke
`tests/integration/world/test_phase9_stability.py::test_1000_tick_stability`, which passes on untouched
base — confirmed by reverting. The defect was *where* raiders spawn, not *whether* raids happen, so the
fix was narrowed: `global_raid_anchor()` falls back from a city to a region centre, and only a world
with neither yields no raid. Raid frequency is now unchanged by construction.

**(b) A pre-existing test became vacuously green.**
`test_calamity_raid_spawn_positions_unchanged_by_spawn_raid_extraction` recomputed expected spawn
positions from a zero origin, and its fixture had no places. Under the first implementation
`check_for_raid` returned empty, so `for i, mob in enumerate(update.entities_add)` never executed and
the test **passed while asserting nothing**. It was only visible because the suite count moved by one.
Rewritten to recompute from `global_raid_anchor()`, with an explicit `assert update.entities_add` so a
future change cannot silently empty it again. A position test that passes vacuously is worse than one
that fails.

## 4. What the measurement did not cover

- **The camp-triggered path never fired** in either probed world within 1100 ticks (it needs
  `camp.maturity >= RAID_MATURITY_THRESHOLD`), so there is **no measured baseline of a "correct" raid's
  coordinates** — only the in-repo code at `src/world/camp.py`. The camp path is untouched here and
  asserted unchanged, but a measured comparison would need that gate reached or forced.
- The probe covered 2 worlds / 2 seeds / 4 raid events. It is a true result for that corpus, not a
  proof about every world configuration.
- No post-fix full-sim re-measurement was run. AC-6 asks for one; the unit tests pin the geometry
  deterministically, but the corpus-level effect of raiders now being live inside regions (engagements,
  influence, population) is **not measured** and is named as such in the ticket's Completion Summary.

## 5. Discipline notes carried from earlier in this session

- Any per-tick counting run must set `audit_mode=True` and raise `max_tick_budget_ms`, or
  `kernel.py:612-620` drops authoritative result items and the counts measure the throttle
  (`INFRA-273`). The probe behind this ticket did both and reported `dropped_work_total == 0`.
- Every behavioural test here was confirmed to fail on the unfixed code by restoring the `(0,0)`
  literals and re-running. The unit test's failure coordinates `(4.0, -25.0) (5.0, -25.0) (6.0, -25.0)`
  **match the full-sim probe's `frontier_marches`/42 tick-500 observation exactly**, which is
  independent corroboration between a 1100-tick instrumented run and a unit fixture.

## 6. The re-anchoring fix was implemented, measured, and WITHDRAWN

Recorded in full because the withdrawal is the substance of this ticket, not a footnote.

Re-anchoring (`global_raid_anchor()`: a CITY, else a region centre, as both origin and target) was
built, unit-tested and committed as `509009d41`. A post-fix corpus measurement then ran it against a
same-harness pre-fix control arm — `audit_mode=True`, `max_tick_budget_ms=1e9`,
`LocalSequentialExecutor`, `dropped_work_total == 0` in all 8 runs, each world repeated with a
byte-identical signature. The control arm reproduced the pre-fix table exactly, which calibrates the
harness.

**It did what it claimed, and it was still the wrong change. Four measured reasons:**

1. **11 of 12 re-anchored spawns were STILL outside every region.** `hometown` is 30 wide
   (`[10,10,40,40]`) around a city at `(25,25)` — half-width 15 — while the spawn ring is
   `SANCTUARY_RADIUS + 10 = 25`. A radius-25 ring around a city centred in a 30-wide region
   *necessarily* lands outside it. **My AC-2/AC-3 test passed only because my fixture used a 60-wide
   region**; it asserted a property real corpus worlds do not satisfy. That is the sharpest lesson
   here: a green test on an unrepresentative fixture.
2. **A second `(0,0)` defect swallows the raid on the flight path.** `src/engine/tactical.py:141`
   `PANIC_RETREAT` overwrites a raider's target with the same hardcoded `(0.0, 0.0)` within 15–38
   ticks of spawn; 10 of 12 raiders walked *past* the city to the world origin and idled there
   permanently. Three such literals exist (`:141`, `:247`, `:483`). Filed as
   `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`. **So re-anchoring would have
   shipped a feature that still did not function.**
3. **Downstream, the result was split and in one world null.** `frontier_marches`: zero raider combat
   in both arms, zero raider deaths, **bit-identical** final influence and ownership — the fix bought
   literally nothing. `crowded_frontier`: raider-as-defender attacks 6 → 158, 3 raiders killed,
   `hometown` influence +15 of a 200-point scale. **Raiders killed nothing in any run, and
   `owner_faction_id` changed in no region in either arm.**
4. **It activated a behaviour the world has never had**, which is a gameplay change with a balance
   footprint — the class `owner_decision_memo.md` row 7 parks — and it made the `Bug Fix` rationale
   class wrong.

The rule layer independently ruled the same way (`world-rule-catalog-design`, relayed owner ruling,
now memo row 9): **PLACE-01** rules out a geometric region centre as a destination (a bare coordinate
is not a Place), and **CAUSE-01 / ID-04 / ORG-03** require a raid to have a real causal and
organizational origin, which a world clock is not. Also noted: the predicate should be "is a settlement
Place" (SETT-01), not `== CITY`, if this ever returns as a feature.

### 6a. One correction to the earlier baseline

The post-fix agent's own pre-fix arm found that **`crowded_frontier`/500's three raiders DID move**
(30–33 Manhattan), contradicting the earlier probe's "all 12 raiders had not moved". Spawn coordinates
matched exactly between the two harnesses, so the divergence is on the movement side — different end
tick, or the earlier run lacked `audit_mode`. **Unexplained, and recorded rather than smoothed over.**
It does not affect the retirement: 12/12 off-region at spawn is the load-bearing fact and both
harnesses agree on it.

### 6b. Also measured: influence is not globally pinned at 0.0

Refines §5 of the sovereignty investigation, which said most regions sit at exactly `0.0`. More
precisely: regions **where nothing happens** stay bit-exactly `0.0` (5 of 9 in `frontier_marches`), but
`hometown` starts at 100 and drifts, `goblin_camp` reaches 35–55, `bandit_road` moves ±5–15. The
important half of the earlier claim stands: **a functioning raid that killed three of its own raiders
inside a settled region moved that region's influence by 15 of 200 points and flipped no owner.** The
influence/ownership channel remains essentially unresponsive to raids.
