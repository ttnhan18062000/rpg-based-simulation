---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS
phase: open
date: 2026-09-14
tags: [strategy, cognition, world]
---

# TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS

## Title
`region_danger_seen`'s belief synthesis is permanently unreachable today — two of its own required preconditions have zero real callers anywhere in the live pipeline

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed as the required follow-up from
`TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN`'s own investigation, per
that ticket's explicit acceptance criteria ("If the answer is 'effectively unreachable,' a
follow-up ticket is filed"). **Filed, not built** — this ticket names the real defects; it does
not fix them.

That investigation set out to determine whether `InformationBeliefPhase.apply()`'s
`region_danger_seen` synthesis branch (`src/domains/information/phase.py`) ever completes its full
conjunction (an actor co-located with an actively-scarred region matching one of its own untested
location leads) under realistic conditions. The answer is not "rare" and not "the measurement
budget was too short" — it is **structurally, permanently unreachable today**, for two independent,
fully dead code paths, each individually sufficient to block the conjunction on its own:

**Defect 1 — `state.local_scars` can never be populated in a real run.** `LocalScarState` is
constructed in exactly 2 places in the whole codebase:
`RegionalConsequenceService.create_battlefield_scar()` and `.create_raid_scar()`
(`src/world/consequences.py`). Neither has a single real caller anywhere — confirmed via exhaustive
grep of both method names and of `RegionalConsequenceService` itself. The only real usage of that
service is `.process_recovery()` (`src/engine/apply_plan.py:101`), which only *decays*
already-existing scars, never creates one. `has_active_scar`'s own bounds-check
(`src/domains/information/phase.py`) therefore iterates an always-empty `state.local_scars` in
every real run today.

**Defect 2 — no real production blocker ever carries a subject a location lead's own subject could
match.** The only real consumer that drives navigation toward an untested location lead's own
coordinate is `ResolveBlockerScorer` (`src/ai/goals/scorers.py`), gated on `blocker.kind ==
"material"` with `blocker.subject == lead.subject`. The real, live blocker producer
(`src/systems/strategic_systems/intelligence.py`'s inference logic) does create `kind="material"`
blockers, but only ever with generic subjects (`"resource"`, `"out_of_stock"`, `"liquidity"`,
`"capacity"`) — never a real material-name subject like `"iron_ore"`. The **only** place in the
entire codebase that ever constructs a `material`-kind blocker with `subject="iron_ore"` is
`src/perf/scenarios.py:248`, a synthetic performance-benchmark fixture, not a real production call
site. An entity holding a real, untested `iron_ore` location lead therefore has no live mechanism
ever driving it toward that lead's own coordinate.

**Empirical confirmation**: a real 2000-tick `Kernel.tick_once()` run against `frontier_living_world`
(seed=42) — 4x the prior ticket's own 500-tick measurement — saw zero scars ever created and zero
material blockers for `iron_ore` ever appear, across the entire run, matching both defects exactly.
Full detail, including the counter table, in
`stored_artifacts/TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN/investigation.md`.

## Scope
- Decide whether and how to wire `create_battlefield_scar()`/`create_raid_scar()` to a real trigger
  (a real death event, a real raid-resolution event) — not decided here. Candidates to weigh, not
  to assume: hook into the existing `ENTITY_DEATH`/`CAMP_RAID` `WorldEventCategory` production
  sites, or a narrower, more targeted trigger specific to what `region_danger_seen` actually needs.
- Decide whether and how a real production blocker producer should ever carry a material-name
  subject a location lead could match (i.e., make `ResolveBlockerScorer`'s own travel-toward-lead
  branch for material blockers reachable with real content) — not decided here.
- Whichever direction(s) are chosen, add a real test proving the full `region_danger_seen`
  conjunction actually fires under a constructed (not merely mocked-past) real scenario — the
  same false-positive-shaped acceptance bar this whole investigation lineage has used throughout
  (prove the mechanism actually completes, not just that its individual pieces are individually
  reachable).
- Consider whether Defect 1 and Defect 2 are better split into two separate implementation
  tickets once a direction is chosen for each — they are independent root causes with no shared
  fix shape, bundled here only because they share the same downstream symptom this investigation
  was scoped to.

## Out of Scope
- Re-investigating whether the conjunction is reachable — already conclusively answered (it is
  not, for the two reasons above), not to be re-litigated here.
- `resolve_location_lead_region_id()`'s own correctness — already proven (300/300) by
  `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` and not in question.
- Whether `region_danger_seen` is even the right mechanism/worth keeping at all versus removing it
  — a real, legitimate question raised by finding two of its own three preconditions permanently
  dead, but a design decision for peer/user, not assumed here either way.

## Acceptance Criteria
- [ ] A real design decision on how (or whether) to make `state.local_scars` populated in a real
      run, brought to peer/user review before implementation.
- [ ] A real design decision on how (or whether) to make a real material-name-subject blocker
      reachable in production, brought to peer/user review before implementation.
- [ ] If either or both are fixed: a real test proving the full `region_danger_seen` conjunction
      fires under a constructed real scenario, not just that each precondition is independently
      reachable.
- [ ] No implementation without the design decisions above.

## Related Tickets
- `TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN` (done — the investigation
  that found both defects named here)
- `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING` (done — proved
  `resolve_location_lead_region_id()` itself works, the investigation this whole lineage started
  from)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` § "Leads (Knowledge)"
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-230`

## Related Stored Artifacts
`stored_artifacts/TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN/investigation.md`
— the full investigation naming both defects, with the empirical 2000-tick confirmation.

## Related Code Areas
- `src/world/consequences.py` (`RegionalConsequenceService.create_battlefield_scar()`/
  `.create_raid_scar()` — the two dead scar-creation methods)
- `src/systems/strategic_systems/intelligence.py` (real blocker-inference logic — never produces a
  material-name-subject blocker)
- `src/ai/goals/scorers.py` (`ResolveBlockerScorer` — the real, but currently-unreachable-for-this-
  case, travel-toward-lead consumer)
- `src/domains/information/phase.py` (`InformationBeliefPhase.apply()`'s `region_danger_seen`
  branch — the downstream symptom)
- `src/perf/scenarios.py:248` (the only place `subject="iron_ore"` is ever used on a
  `material`-kind blocker — a synthetic fixture, not a real producer)

## Assumptions / Open Questions
- Whether these two defects are worth fixing at all (vs. `region_danger_seen` being removed as a
  currently-aspirational mechanism) is not assumed either way — a real question for whoever picks
  this ticket up to bring to peer/user, not decided here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
