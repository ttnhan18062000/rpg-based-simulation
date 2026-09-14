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
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
