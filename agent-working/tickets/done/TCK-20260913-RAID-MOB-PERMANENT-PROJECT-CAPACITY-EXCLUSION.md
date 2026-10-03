---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION
phase: done
date: 2026-09-13
tags: [cognition, combat]
---

# TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION

## Title
`TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION`'s fix sets `max_active_projects=0` permanently on a raid mob — a raider that survives its raid can never take any project again, for the rest of its life, because "mid-raid" was encoded as a permanent property instead of a state

## Status
DONE

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
- [x] A real design decision on whether/how a raid mob's project capacity should be restored,
      brought to peer/user review before implementation. **Decision: close document-only. Left
      as-is because no declared intent supports changing it — not because permanence was chosen
      as a design intent.** See Completion Summary for the exact disposition peer required.
- [ ] If restoration is chosen: real test coverage for a surviving mob regaining capacity. **N/A —
      restoration was not chosen.**
- [x] No implementation without that review — filed, not built, per explicit instruction. Honored:
      zero source/test changes at any point in this ticket's lifecycle.

## Related Tickets
- `TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION` (done — the fix whose own
  side effect this ticket names)

## Related Docs
None yet.

## Related Stored Artifacts
`staging_artifacts/TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION/investigation.md` —
full investigation: no "raid concluded" signal exists anywhere in the codebase (mob, camp, or
world level); `difficulty_tier=4` confirmed NOT a real separate reason for reduced capacity
(other tier-4 factions run the full project system); the one real, relevant existing design
commitment is `docs/parity_ledger/world_dynamics.yaml`'s WORLD-034 ("Raid mobs do not return
home," verified, P0) — evidence worth weighing but not a settled answer, since it's a navigation
question, not a project-eligibility one. 3 options laid out for peer/user review, no
recommendation given between them per this ticket's own instruction.

## Related Code Areas
- `src/world/raid.py` (`RaidService.spawn_raid()`, where `max_active_projects=0` is set)
- `src/core/strategic.py` (`CognitionProfile.max_active_projects`)

## Assumptions / Open Questions
- Whether raid mobs have any real, intended lifecycle event marking "the raid is over for this
  specific entity" is the central open question — not resolved here.

## Implementation Notes
**2026-09-14: investigation complete, blocked on design review — no code changed.** Summary (full
detail in staging_artifacts/investigation.md):
- No "raid concluded" signal exists anywhere: not on `EntityState`, not a raid-instance id, nothing
  in `raid.py` or `camp.py` beyond the camp-level `last_raid_tick` cadence field (which tracks the
  camp's own next-raid-eligibility, not any individual mob's raid status).
- `difficulty_tier=4` ruled out as a real, separate justification for permanent reduced capacity —
  checked directly (per this ticket's own instruction): `DIFFICULTY_TIERS` only scales combat/
  reward stats, and other real tier-4 factions run the full project system with no reduction.
- The one real, relevant existing design commitment found: `docs/parity_ledger/
  world_dynamics.yaml`'s WORLD-034 ("Raid mobs do not return home," verified, P0) — a genuine
  precedent for raid mobs having a permanently-diverged lifecycle, but it answers a navigation
  question, not this ticket's project-eligibility question; noted as evidence, not treated as
  settling the decision.
- Also found, as adjacent context rather than in-scope: `docs/world/raid_boss_camp_contract.md`'s
  own documented "Raid outcome" mechanic (settlement damage / raid suppression) has **zero**
  matching implementation anywhere in `src/` — likely legacy-only documentation or an
  emergent-rather-than-explicit mechanic. Not this ticket's problem to fix, but relevant: it means
  even a world-level "raid concluded" event doesn't exist today for a mob-level fix to borrow from.
- 3 options laid out (leave permanent / build a real "raid concluded" signal / use a cruder
  proxy signal), no recommendation given between them, per the ticket's own explicit instruction.
  Design question sent to peer/user for review.

**2026-09-14: closed, document-only, per peer/user review of the investigation above.** Peer's
exact decision, recorded verbatim in substance since the wording itself is load-bearing (an earlier
draft of peer's own framing said "document as intended" and was explicitly corrected before
landing here):

- Raid-spawned mobs are permanently excluded from the project system; a survivor never regains
  eligibility.
- **Nothing declares this either way.** All 6 Mechanics Bible chapters, the engine contracts
  (`docs/engine/*.md`), and every `max_active_projects` mention in `docs/` (3 hits, all generic
  `CognitionProfile` cap discussion in archive/design docs, none mentioning raid mobs) were
  checked — no statement that raid survivors should or shouldn't regain eligibility. Recorded as a
  verified absence, with where this looked, so nobody re-derives it.
- `WORLD-034` ("raid mobs do not return home," verified P0) is real declared intent about the same
  entities, adjacent rather than governing — it concerns navigation, not project capacity. It is
  *consistent* with permanence and is not authority for it.
- The exclusion originates as a side effect of
  `TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION`, not from a design
  decision — `max_active_projects=0` was the correct minimal signal for that ticket's own
  navigation-hijack problem; permanence was never itself decided by anyone.
- **Left as-is because no declared intent supports changing it, not because permanence was
  chosen.** If raid survivors should rejoin the goal system, that is a future design decision
  requiring a "raid concluded" lifecycle signal, which does not exist anywhere today. The 3 options
  in investigation.md remain the record of what building that fix would involve, so a future
  pickup doesn't have to redo this investigation.

## Test Summary
_(none — no implementation; this is a document-only closure)_

## Files Changed
_(none — investigation and disposition only; zero source/test changes across this ticket's entire
lifecycle, per its own "No implementation without review" constraint, honored through closure)_

## Completion Summary
Closed document-only. The permanent `max_active_projects=0` exclusion on surviving raid mobs is
current, undeclared behavior — an accepted side effect of a P0 hotfix, not a design decision either
way — and stays as-is because no declared intent (Mechanics Bible, engine contracts, or otherwise)
supports changing it. Should this ever need revisiting, the 3 options and the full precedent
survey in investigation.md are the starting point; the central blocker (no "raid concluded" signal
exists anywhere in the codebase) would need solving first regardless of which option is chosen.
