---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION
phase: open
date: 2026-09-13
tags: [cognition, combat]
---

# TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION

## Title
`TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION`'s fix sets `max_active_projects=0` permanently on a raid mob — a raider that survives its raid can never take any project again, for the rest of its life, because "mid-raid" was encoded as a permanent property instead of a state

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`RaidService.spawn_raid()` now sets each spawned mob's `strategic.profile.max_active_projects = 0`
at spawn time (`TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION`), fixing a
real regression where a raiding `goblin_raider`'s navigation target was hijacked by a newly-
reachable `GuildNeedScorer` project assignment. The fix is correct for the raid itself and the
right size for a P0 hotfix — but the value is set once, at spawn, on a durable field with no
consumer that ever changes it back.

**The gap, disclosed rather than built around**: "this entity is mid-raid" is a *state* — true while
the raid is active, false once it resolves (the raid mob dies, the raid target is reached, or
however a raid concludes for a surviving mob). `max_active_projects=0` encodes it as a *permanent
property* instead. Nothing in the codebase currently clears it. A `goblin_raider` that survives its
own raid (flees, is never engaged, or the raid mechanic simply lets it linger) is permanently
excluded from the project/goal system for the rest of its in-world life — it can never harvest,
never form a party, never do anything the generic Tier-4 economic scorers would otherwise let it
do, even though the reason it was excluded (the raid) is long over.

## Scope
- Determine whether a real lifecycle event already exists (or should exist) that marks a raid as
  concluded for a given mob, and whether restoring `max_active_projects` to its own class/kind
  default at that point is the right fix, or whether raid mobs should keep some other permanent
  reduced capacity for a different, real reason (e.g. `difficulty_tier=4` combat mobs may be
  intentionally simple entities regardless of raid status — check whether that's a real, separate
  design intent before assuming it isn't).
- If a real "raid concluded" signal is chosen: real test coverage that a surviving raid mob's
  project capacity is restored, not just that it starts at zero.

## Out of Scope
- Re-litigating the hotfix's own `max_active_projects=0`-at-spawn choice — that fix stands; this
  ticket is about the missing un-set, not the set.
- A general audit of every other place a durable field is set once at spawn with no lifecycle
  consumer — this ticket is scoped to this one confirmed instance.

## Acceptance Criteria
- [ ] A real design decision on whether/how a raid mob's project capacity should be restored,
      brought to peer/user review before implementation.
- [ ] If restoration is chosen: real test coverage for a surviving mob regaining capacity.
- [ ] No implementation without that review — filed, not built, per explicit instruction.

## Related Tickets
- `TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION` (done — the fix whose own
  side effect this ticket names)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/raid.py` (`RaidService.spawn_raid()`, where `max_active_projects=0` is set)
- `src/core/strategic.py` (`CognitionProfile.max_active_projects`)

## Assumptions / Open Questions
- Whether raid mobs have any real, intended lifecycle event marking "the raid is over for this
  specific entity" is the central open question — not resolved here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
