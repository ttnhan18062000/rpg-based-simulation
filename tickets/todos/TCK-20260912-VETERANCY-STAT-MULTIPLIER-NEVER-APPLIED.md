---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED
phase: open
date: 2026-09-12
tags: [world, architecture]
---

# TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED

## Title
`VeterancyService.get_stat_multiplier(rank)` has zero real callers — veterancy accumulates correctly but never affects combat stats

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD`'s own
earned-progression audit, while confirming `veterancy_points`/`veterancy_rank` are real,
accumulated progression worth carrying forward at survivor reconstruction.

`VeterancyService.process_points()` (`src/progression/veterancy.py:28-45`) is real and live —
wired through `src/engine/patches.py`/`src/engine/apply.py`, correctly accumulating
`veterancy_points` and incrementing `veterancy_rank` as points cross thresholds
(`get_points_to_next_rank(rank) = 10 * (2 ** rank)`). Confirmed via grep this accumulation
mechanism has real callers and genuinely runs.

`VeterancyService.get_stat_multiplier(rank)` (`veterancy.py:19-25`) — the function whose own
docstring says it provides "+5% to physical/magical output" per rank — has **zero real callers
anywhere in `src/`**. Confirmed via a full grep for `get_stat_multiplier`. Veterancy rank
accumulates correctly, tracked, persisted, carried forward — and never affects a single combat
stat, ever. This is the same "earned progression with no mechanical effect" shape as the
knowledge/investigation-layer and behavior-analytics-pipeline findings from the prior batch: a
real subsystem that computes something and nothing downstream consumes it.

## Scope
- Determine whether `get_stat_multiplier()` should be wired into `SkillScalingService.
  get_effective_stats()`/`LevelingService.recalculate_combat_stats()` (the real combat-stat
  derivation chain, confirmed in the origin ticket's own investigation) — this is a real design
  decision (does veterancy rank apply as a flat multiplier on final stats, or should it be
  folded into the base/attribute contribution some other way?), not something to resolve
  unilaterally. Route through peer review before implementing.
- Check whether `get_stat_multiplier()`'s own formula (`1.0 + rank * 0.05`) is still the intended
  design, or whether it predates other combat-stat changes and needs re-deriving — don't assume
  the dead function's own numbers are still correct just because they're unused, verify against
  current balance intent if any documentation exists.
- If wired: real test evidence that a high-veterancy-rank entity's combat stats genuinely differ
  from a same-attributes/same-equipment, zero-veterancy entity.

## Out of Scope
- `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD`'s own fix — that ticket
  carries `veterancy_points`/`veterancy_rank` forward regardless of this ticket's disposition,
  since preserving real earned state is correct even while its downstream application is
  separately incomplete. Not reopened here.
- Any other combat-stat formula change beyond wiring in the veterancy multiplier specifically.

## Acceptance Criteria
- [ ] Real evidence confirms `get_stat_multiplier()` has zero callers (already established in the
      origin ticket; re-verify as current when this ticket is picked up).
- [ ] A peer-routed decision: wire the multiplier in (and where/how), or formally document
      veterancy rank as tracked-but-cosmetic (no mechanical effect), obtained before
      implementation.
- [ ] If wired: real test evidence of a stat difference attributable to veterancy rank alone.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD` (origin — found during
  its own earned-progression field audit)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/progression/veterancy.py` (`VeterancyService.get_stat_multiplier()`, `process_points()`)
- `src/engine/rpg_depth.py` (`SkillScalingService.get_effective_stats()`)
- `src/progression/leveling.py` (`LevelingService.recalculate_combat_stats()`)

## Assumptions / Open Questions
- Whether veterancy should mechanically affect combat stats at all, or was always meant to be a
  tracked-but-cosmetic rank display, is the real open question — not pre-judged here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
