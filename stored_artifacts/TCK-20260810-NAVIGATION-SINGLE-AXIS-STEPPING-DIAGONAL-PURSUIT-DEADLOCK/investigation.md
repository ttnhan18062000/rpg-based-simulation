---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK
artifact_type: investigation
tags: [combat, engine]
---

# Investigation: TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK

## Question
Why did the specific mutually-pursuing pair traced in `TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-
SNAPSHOT-NEVER-RETARGETS` stop freezing outright post-fix, but still never converge to melee
range — and how common is this in the real corpus?

## Method
1. Analytical: a standalone Python re-implementation of `get_next_step()`'s own tie-break rule,
   fed the exact real corpus positions of the traced pair, to confirm the mechanism without
   needing a live kernel.
2. Empirical: 5 new direct unit tests against the real `NavigationSystem.get_next_step()`.
3. Prevalence: a live, non-mocked `Kernel.tick_once()` loop across 3 seeds × up to 8 corpus
   worlds, 2000 ticks each, tracking every tick whether any two entities' own
   `task.payload["target_id"]` mutually point at each other, and for how many consecutive ticks
   their Manhattan distance stays constant while >1.

## Finding — Mechanism
`NavigationSystem.get_next_step()` (`src/systems/world_systems/navigation.py:99-103`):
```python
if abs(dx) > abs(dy):
    return (pos[0] + (1 if dx > 0 else -1), pos[1])
else:
    return (pos[0], pos[1] + (1 if dy > 0 else -1))
```
On an exact diagonal offset (`|dx| == |dy|`), the condition `abs(dx) > abs(dy)` is False, so the
function ALWAYS takes the Y-axis branch. When two entities are mutually, reactively pursuing
each other (both live-retargeting to the other's CURRENT position every tick, per
`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`) and land on a perfectly diagonal offset, BOTH
entities' own step resolves to Y — and because they're moving toward each other, their Y-moves
perfectly cancel each other's progress. The Manhattan distance between them stays fixed forever.

Confirmed exactly via a standalone re-implementation fed the real traced pair's positions
((57,59) and (58,60)): the pure-Python trace reproduces the identical, real oscillation observed
in the live corpus run, tick-for-tick.

**Critically, this requires MUTUAL pursuit, not merely a diagonal starting offset.** A
single-sided pursuer chasing a static (non-reactive) target converges normally: as the pursuer's
own position changes each tick, the tie between `|dx|` and `|dy|` naturally breaks asymmetrically
(the pursuer approaches via a staircase path — alternating X and Y steps — reaching the target in
a bounded number of ticks). Verified with the same standalone re-implementation.

## Finding — Real Corpus Prevalence
Live, non-mocked corpus measurement, 3 seeds (42/123/456):

| World | Seed 42 | Seed 123 | Seed 456 |
|---|---|---|---|
| dungeon_crawl | **991-tick deadlock, 1 pair** | 0 | 0 |
| urban_political | 0 | 2-tick max streak (transient) | 0 |
| wilderness_survival | 0 | — | — |
| crowded_frontier | 1-tick max streak (transient) | — | — |
| swamp_border_world | 0 | — | — |
| hero_guild_routing | 9-tick max streak (transient) | — | — |

Only 1 pair, in 1 world, at 1 seed, across the entire sample reached a genuine, sustained
(≥20-tick) deadlock. Every other combination showed either zero mutual-pursuit interactions on
an exact diagonal offset, or trivially short (1-9 tick) coincidental ties that resolved normally
on the next tick — a normal, expected part of the staircase convergence path, not a deadlock.

## Disposition
Document-and-defer, per the ticket's own Scope item 4. The mechanism is real, confirmed, and
fully deterministic — but real-world prevalence is a specific, coincidental spawn-geometry
occurrence, not a systemic pattern. A core stepping-algorithm change (e.g. true 8-directional
movement) was judged disproportionate to the real, measured impact.

## Documentation
Extended `docs/engine/known_limitations.md` §1.1 (Spatial / Navigation), which already
acknowledged "Linear Stepping Only" in general terms, with the specific, confirmed mechanism and
real prevalence data. Cross-referenced from `docs/engine/contracts/tactical_contract.md` §3.

## Test Coverage Added
5 new tests in `tests/unit/movement/test_navigation_get_next_step.py` — the first direct test
coverage `get_next_step()` has ever had. Characterizes the current, real behavior (both the
normal convergence case and the confirmed deadlock case) so a future stepping-algorithm change
can't silently alter this documented limitation without an intentional test update.

## Unrelated Regression Found and Fixed
While running the regression sweep, found `tests/unit/world/test_terrain_weighting.py::
test_terrain_readiness_success` asserting a stale, pre-`TCK-20260809-COMBAT-PACING-READINESS-
MOVEMENT-DECOUPLE` expectation (`readiness_delta == -80.0`) that ticket's own already-intentional
divergence (§2.38) had already removed — that ticket's own scoped test sweep never included
`tests/unit/world/`. Fixed the assertion to match the already-documented, already-intentional
behavior (`readiness_delta == 0.0`).
