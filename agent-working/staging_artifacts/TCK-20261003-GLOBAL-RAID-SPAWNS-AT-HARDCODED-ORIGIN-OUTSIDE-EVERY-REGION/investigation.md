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
It records what the measurement did not cover, the two things that went wrong during implementation,
and the facts that constrained the fix.

Base: `958aa103d`.

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
