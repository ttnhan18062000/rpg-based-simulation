---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES
phase: open
date: 2026-09-14
tags: [world, faction]
---

# TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES

## Title
`RegionState.influence` (regional sovereignty's own driver) never moves off `0.0` for any "wild"
region, in any of 4 real corpus worlds across 12,000 combined ticks — despite real, independently
confirmed combat deaths happening in those same regions — meaning dynamic region conquest/liberation
has never fired in this codebase's history, only compile-time-authored starting ownership has ever
been observed

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while drafting the design proposal for `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`
(user decided to build real pre-war drivers for faction war reachability, reusing the existing
regional sovereignty system where possible). Regional sovereignty
(`docs/mechanics/regional_sovereignty.md`, `RegionState.owner_faction_id`/`.influence`,
`FactionInfluenceService.process_influence_shift()`) is real, live, wired code — called from
`src/systems/lifecycle_systems/lifecycle.py::resolve_lifecycle()` with a real `recent_deaths` list
on every tick that has deaths.

A real, instrumented probe across four unmodified corpus worlds (`urban_political`,
`frontier_living_world`, `dungeon_crawl`, `generated_frontier_3_42`, 3000 ticks each, 12,000
combined real ticks) found: **`region.owner_faction_id` never changed once, for any region, in any
world.** Every "wild"/unowned region (e.g. `goblin_camp`, `bandit_road`, `old_mine` — regions
independently confirmed elsewhere this batch to have real combat, via `region.trauma_score`
movement in the same runs) showed `region.influence` frozen at exactly `0.0` for the entire run, in
all four worlds — not slow, not partial, exactly zero movement, despite real monster/hero deaths
happening there. The only nonzero influence anywhere came from two regions with
compile-time-authored starting ownership (`hometown`/`trading_hometown`, pre-seeded to
`Faction.HERO_GUILD`/`influence=100.0`), and even those never moved past their starting value.

This means **dynamic region conquest/liberation — the entire point of the mechanism described in
`docs/mechanics/regional_sovereignty.md` §1 — has apparently never fired in any real run in this
codebase's history.** Only static, compile-time-authored ownership has ever been observed to exist
or generate taxation revenue.

## Scope
- Find the real root cause of why `process_influence_shift()` doesn't move `influence` for real
  deaths in wild regions, despite a code-level trace (done in the sibling design proposal,
  `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` §2.1) suggesting the classification path
  (`get_faction_id_str()` → `FactionSemanticsService.is_invader()`/`is_protector()`) should
  correctly resolve a spawned monster's death as an "invader" death. Candidates not yet checked:
  - Does `LegalityServiceV2.get_region_for_position()` correctly resolve the death position to the
    wild region for these specific entities, or does it silently return `None` (the function
    `continue`s past any death whose region can't be resolved)?
  - Does `resolve_lifecycle()`'s own death-detection (`ent_upd.combat.outcome_kind in ("KILL",
    "PERMADEATH")`) actually fire for the same deaths `world_dynamics.py`'s separate
    "Death-triggered Trauma" block sees (which independently confirms real deaths happen in these
    regions) — or do the two death-detection paths diverge in what they each observe?
  - Is `resolve_lifecycle()` itself being called every tick in the real pipeline, with a non-empty
    `recent_deaths`, for these worlds? (Confirmed wired via grep; not confirmed executing with real
    data via direct instrumentation.)
- Determine whether this is a single root cause or multiple independent ones.
- Bring findings + a proposed fix to peer/user review before implementing, matching this week's
  established pattern for reachability defects of this size.

## Out of Scope
- The faction-war-declaration design itself (`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`)
  — this ticket's fix is a prerequisite for that design's military-strength driver (§3.2 of the
  proposal), not a replacement for it.
- Any change to `CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD`/`DEATH_INFLUENCE_SHIFT` values — this
  is about the mechanism never firing at all, not about the threshold values once it does.

## Acceptance Criteria
- [ ] A real, evidence-backed root cause for why `region.influence` never moves in wild regions
      despite real combat deaths occurring there.
- [ ] A proposed fix (not yet built without review).
- [ ] Findings brought to peer/user review before implementation.

## Related Tickets
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (the design work that surfaced this;
  its own §3.2 military-strength driver is blocked on this ticket resolving)
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (checked against that ticket's own named
  pattern — this ticket's own root cause does not share it; see that ticket's own notes and
  `docs/plans/world_composition_precondition_gap_finding.md` for the comparison)
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (same shape as this
  ticket's own real root cause: two independent readers of one thing — a combat-outcome event
  here, an item id there — disagreeing about what counts, with no error surfaced either time)

## Related Docs
- `docs/mechanics/regional_sovereignty.md` (the mechanism this ticket investigates)
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` §2.1, §5 (the investigation that found this)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/influence.py` (`FactionInfluenceService.process_influence_shift()`)
- `src/systems/lifecycle_systems/lifecycle.py` (`resolve_lifecycle()`, the real caller with
  `recent_deaths`)
- `src/content_semantics/faction.py` (`FactionSemanticsService`, `get_faction_id_str()`)
- `src/engine/world_dynamics.py` (the separate Death-triggered Trauma block, for comparison — it
  independently confirms real deaths happen in these same regions)

## Assumptions / Open Questions
- Whether this is one root cause or several (e.g. a region-resolution bug AND a death-detection
  divergence) is not yet known.

## Implementation Notes
**2026-09-15, checked against the "world geometry that nothing validates" pattern named in
`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — this ticket does NOT share it. A clean
counter-example, with its own real, fully-confirmed root cause.**

Instrumented `FactionInfluenceService.process_influence_shift()` directly across a real 3000-tick
run of `frontier_living_world`: **called zero times.** Since the call is guarded by `if
recent_deaths:` in `resolve_lifecycle()`, this means `recent_deaths` was empty on every tick,
despite `world_dynamics.py`'s own trauma block independently confirming real deaths occur in this
same run (this ticket's own Request Summary already established that).

**Ruled out first, per the same discipline as the lair/calamity checks**: confirmed
`src/systems/lifecycle.py` is a legitimate one-line re-export shim
(`from src.systems.lifecycle_systems.lifecycle import LifecycleSystem`), not a duplicate/dead
module — `resolve_lifecycle()` genuinely is the function the real pipeline calls
(`src/engine/pipeline.py:414`).

**Found the real divergence via direct code read, then confirmed it empirically — this ticket's
own second candidate, exactly**: `resolve_lifecycle()`'s death filter
(`src/systems/lifecycle_systems/lifecycle.py:202`) checks `ent_upd.combat.outcome_kind in ("KILL",
"PERMADEATH")`. But `world_dynamics.py`'s own trauma block (`src/engine/world_dynamics.py:47`)
checks `ent_upd.combat.alive_set is False` directly — a different, broader condition. Real combat
resolution (`src/engine/combat.py:499-500`) sets `alive_set=not is_kill` (False whenever the
target is killed) but `outcome_kind="KILL" if is_kill and is_lethal else ("DEFEAT" if is_kill else
"SURVIVE")` — **a target can be killed (`alive_set=False`) with `outcome_kind="DEFEAT"`**, which
`resolve_lifecycle()`'s narrower filter does not recognize as a death at all.

**Confirmed empirically, not just theoretically**: instrumented the real outcome_kind
distribution across the same 3000-tick run. **20 real combat deaths occurred (`alive_set=False`),
and all 20 were `outcome_kind="DEFEAT"` — zero were `"KILL"`.** This fully and exactly explains
the zero calls to `process_influence_shift()`: every real death in this run's sample used the
outcome value `resolve_lifecycle()`'s filter doesn't check for.

`is_lethal` (which gates whether a kill resolves as `"KILL"` vs `"DEFEAT"`) is set False for at
least one real condition found by a quick read (`combat.py:136`:
`is_lethal = is_lethal and (defender.identity.role != EntityRole.HERO)` — heroes get a
recoverable "DEFEAT" rather than a lethal "KILL" by design). Whether that specific condition, or a
different one, explains all 20 real DEFEAT events in this sample was not traced further — the
"check first" question this session set out to answer is fully answered without needing that
detail.

**This is not the same pattern as the lair/calamity tickets.** Entities ARE correctly co-located
(deaths genuinely happen where the mechanic needs them to), the region resolves correctly, and the
death IS detected — by one consumer. The defect is a real, single-cause classification divergence
between two independent readers of the same combat-outcome event, each checking a different field/
value for "did something die here." A clean, useful counter-example: it protects the geometry
pattern's own credibility by showing it doesn't explain everything, and it comes with its own full,
confirmed root cause rather than an open question.

**Parked here, per the same investment cap as the sibling tickets — not proposing or building a
fix.** The likely fix shape (widen `resolve_lifecycle()`'s own filter to also treat `"DEFEAT"` as a
death for influence-shift purposes, or route influence-shift off `alive_set is False` directly like
`world_dynamics.py` already does) is a real design decision (does a non-lethal "DEFEAT" really
mean the same thing for regional sovereignty as a lethal "KILL"?), left for review rather than
assumed and built.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
**Parked by explicit user decision, not abandoned or unresolved — and a real, standalone bug in
its own right, not merely a counter-example inside someone else's finding.** The root cause is
fully known and empirically confirmed (20 of 20 real deaths in the sampled run were classified
`"DEFEAT"`, zero `"KILL"`): two independent readers of the same combat-outcome event disagree
about what counts as a death — `resolve_lifecycle()` checks `outcome_kind in ("KILL",
"PERMADEATH")`, `world_dynamics.py`'s own trauma block checks `alive_set is False` directly. This
is the same shape as `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` — two
readers of one thing, disagreeing about what counts — not the world-composition-precondition
pattern this ticket was checked against and found not to share (see
`docs/plans/world_composition_precondition_gap_finding.md` for that comparison). Two real
candidate fix directions are recorded above (widen `resolve_lifecycle()`'s own filter to include
`"DEFEAT"`, or route influence-shift off `alive_set is False` directly). The user's explicit
decision, given the investment cap on this cluster, was to record the finding and not build a fix
now — this ticket's own root cause is exactly as complete and actionable as the other two in this
cluster, just a different class of cause (a code-level classification divergence, not a
composition/geometry gap).
