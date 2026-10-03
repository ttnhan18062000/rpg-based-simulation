---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
artifact_type: investigation
tags: [temporal, determinism, world]
---

# Investigation — TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY

## Trigger

The codex temporal-axis proposal (`docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md`) §9
names four categories of conflict (conflicting calendar constants, an aging conflict, an instantaneous-routine
conflict, a cadence-duration conflation) but explicitly defers resolving them — its own header states "this
document does not approve implementation, change an existing plan." This investigation confirms those
findings directly against the real codebase, with exact citations, and extends them (a fourth tick
convention the proposal didn't name) so a plan-owner decision can be made on real evidence rather than the
proposal's illustrative framing alone.

## Method

Direct code investigation (grep + read), not a design exercise: located every live tick/calendar constant,
the real movement-duration formula, real distances in compiled world content, and the real age/lifecycle
thresholds, then computed what those numbers imply together (e.g. max lifespan in days under the documented
calendar).

## Findings

### 1. Four incompatible tick/calendar conventions live in code today (not two)

| Convention | Value | Source |
|---|---|---|
| World Evolution Bible | 1 tick ≈ 36s; 100 ticks = 1 hour; 2,400 ticks = 1 day | `docs/mechanics/05_world_evolution.md:20-22` |
| Raid system | `TICKS_PER_DAY = 100` | `src/world/raid.py:20` — directly aliases raid's "day" to the Bible's "hour," not its "day" |
| Cohort/ecology cycle | `COHORT_INTERVAL: int = 200` ticks | `src/domains/demographics/cohort.py:325`, shared with `ResourceEcologyService.ECOLOGY_INTERVAL` — birth/death/ecology run on their own clock, unrelated to either of the above |
| (Proposal's own citation, confirmed) | raw unlabeled intervals: 30/50/100/200/500/1000/2000/5000 ticks scattered across systems | per proposal §9.1, not independently re-verified line-by-line in this pass |

The cohort/ecology 200-tick cycle was not named in the proposal's own §9.1 — it is a previously-undocumented
fourth convention found in this investigation.

### 2. Movement has a real, working duration formula — the only one in the engine

- `src/core/state.py:306`: `move_cost: float = 10.0` (default)
- `src/core/state.py:311`: `readiness_speed: float = 10.0` (default)
- `src/engine/legality.py:178`: `readiness_cost = (entity.combat.move_cost * terrain_cost) / max(0.1, move_speed_mult)`
- `src/engine/rpg_depth.py:299-300`: `terrain_cost` defaults to `1.0` on `PLAIN`
- `src/engine/apply.py:127-128`: readiness regenerates `+readiness_speed` per tick, capped at 100

Net: on plain terrain at default stats, `readiness_cost == readiness_speed` — one entity moves **1 tile per
tick**, unthrottled (regen exactly matches cost). This is a real, if narrow, anchor for "how long does an
action take" — and it directly confirms the proposal's own §9.5 finding: combat's separate `speed` attribute
is never consulted anywhere in this path, so the engine already has three incoherent duration-adjacent
inputs (readiness-speed for movement, a stamina path, and an unused combat `speed` stat) rather than one.

### 3. Real distance, computed against the movement formula

`data/content/world_modules/*.yaml` `grid_bounds` fields, both composed together in the
`frontier_living_world` corpus world:
- `frontier_village_core`: `[10,10,40,40]` → center ≈ (25,25)
- `goblin_camp_conflict`: `[95,20,125,55]` → center ≈ (110,37)

Distance ≈ 87 tiles. At the 1-tile/tick baseline from Finding 2, crossing that distance costs **~87 ticks**
— roughly 3,132 real-world-equivalent seconds at the Bible's 36s/tick, or **~3.6% of a 2,400-tick day**.
Travel between two real, composed-together world locations is trivially fast relative to "a day" under the
current numbers, before any pathing or terrain friction is added.

### 4. Age/lifecycle math, exact — the proposal's aging conflict quantified

- `src/core/state.py:146`: `max_age_ticks: int = 10000`
- `src/domains/demographics/cohort.py:52-58` (`get_age_bracket()`): young `<3000`, adult `<7000`, elder `≥7000`

At the Bible's 2,400 ticks/day: maximum lifespan = 10000/2400 = **4.17 days**; the elder threshold hits at
7000/2400 = **2.92 days**. This is not an approximation or an edge case — it is what the current code
produces today, for every entity, under the one calendar convention the Bible itself calls authoritative.
Also flagged in `rpg_design_roadmap.md`'s pre-existing Known Open Items as a duplicate-representation
concern (`get_age_bracket()`'s string tiers vs. `IdentityComponent.life_stage`'s enum) — a related but
distinct finding, not resolved by this investigation.

### 5. No per-action duration system exists outside movement

Grepped `src/engine/combat.py`, `src/systems/harvest_system.py`, `src/systems/crafting.py`,
`src/systems/economy_systems/crafting.py` for any `action_cost`/`turn_cost`/`duration_ticks`-shaped pattern:
zero hits. Combat resolution and craft/harvest actions all resolve same-tick today — there is no existing
"how long does this take" concept anywhere except movement's readiness-cost formula (Finding 2). A universal
duration formula, if built, has exactly one existing pattern to generalize from and three domains (combat,
craft, harvest) with nothing to migrate away from, only to add fresh.

### 6. The one balance-testing tool that exists has never been run

`src/lab/metamorphic.py` is real and CI-tested. `data/lab_sessions/` does not exist on disk — zero recorded
sessions. This matches `rpg_design_roadmap.md`'s pre-existing finding (its own Sequencing rules section,
citing idea 37) that this tool has never validated real content end-to-end.

## Conclusion

This is not "the framework is right, just needs numbers." The tick-unit substrate itself is internally
inconsistent — four conventions that don't reduce to one clock — and the one lifecycle number that is
concrete today (age brackets vs. max age) is already wrong by 2-3 orders of magnitude under the documented
authority. Movement is the only subsystem with a real duration formula to generalize from; combat, crafting,
and harvesting have nothing. This confirms, with exact numbers, exactly the sequencing the proposal's own
§17 already argued for: a calendar-authority decision and a duration-formula direction have to be settled
before any M3+ balance ticket can produce real numbers — see `plan.md` for the concrete options this
investigation surfaces for that decision.
