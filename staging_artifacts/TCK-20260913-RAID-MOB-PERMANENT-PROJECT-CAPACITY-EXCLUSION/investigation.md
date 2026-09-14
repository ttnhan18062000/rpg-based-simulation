# Investigation — TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION

**Per this ticket's own explicit acceptance criteria: "No implementation without that review —
filed, not built, per explicit instruction." This document brings findings and a design question
to peer/user review. Nothing in `src/` or `tests/` is changed by this investigation.**

## The fix site itself

`src/world/raid.py::RaidService.spawn_raid()` sets `max_active_projects=0` once, at spawn time, on
every `goblin_raider` mob. No other code reads, clears, or otherwise touches that field afterward —
confirmed by an exhaustive grep for `max_active_projects` across `src/`: the only two hits are the
single class-wide dataclass default (`src/core/strategic.py:394`,
`CognitionProfile.max_active_projects: int = 3`) and this one write site. There is no "raid
concluded" signal anywhere in the codebase for this ticket's proposed fix to hook into.

## Is `difficulty_tier=4` itself a real, separate reason for reduced capacity?

No — checked directly, per the ticket's own instruction to verify this before assuming otherwise.
`DIFFICULTY_TIERS` (`src/world/spawn_config.py`) only scales combat/reward stats (`hp`, `atk`,
`def_stat`, `xp`, `gold`, `level_min/max`) — it has no `max_active_projects` field and nothing else
in the generator reads `difficulty_tier` to affect project capacity. The hotfix ticket
(`TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION`) explicitly notes that
other real `difficulty_tier=4` factions ("frontier_marches' own scout/sentinel/leader") legitimately
run the full generic project/goal system with no capacity reduction. So `difficulty_tier=4` is not
a real, separate design reason for permanently zero capacity — the zeroing is purely a raid-specific
patch tied to the mob's temporary mid-raid task, not a tier-based simplification. This rules out one
of the two branches the ticket's own Scope asked to check.

## Is there any existing "raid concluded" signal, anywhere?

Checked three places a signal like this could plausibly already exist:

1. **Entity-level state.** No `raid_id`, `raid_active`, or equivalent field exists on `EntityState`
   or `CognitionProfile` linking a spawned mob back to a specific raid instance, or marking whether
   that raid is still in progress for it. The only raid-adjacent durable field anywhere is
   `CampState.last_raid_tick` (`src/core/state.py:1261`) — camp-level (tracks when the *camp* last
   triggered a raid, for its own 500-tick cadence gate), not mob-level, and carries no "this specific
   mob's raid is over" meaning.
2. **A distinct raid AI/behavior mode.** `docs/parity_ledger/world_dynamics.yaml` (WORLD-033,
   status `verified`, P0) records "Raid mobs use raid AI state" as a legacy-verified fact, but
   grepping `src/ai/` and `src/strategy/` for any `raid`-related code turns up nothing — there is no
   distinct "raid AI state" implementation in the current V2 codebase. In practice, a raid mob today
   is just a generic hostile with a spawn-time navigation target and (since the hotfix)
   `max_active_projects=0`; "raid state" is not tracked as its own mode anywhere, it is only
   *implied* by those two spawn-time settings. WORLD-033 appears to describe legacy (pre-V2)
   behavior carried forward as a documentation fact, not a currently-implemented mechanism.
3. **A "raid outcome" resolution mechanism.** `docs/world/raid_boss_camp_contract.md`'s own "Raid
   outcome" section states: "Raid reaches settlement → settlement takes damage, faction influence
   decreases" and "Raiders killed before reaching settlement → raid suppressed; trauma reduced."
   Grepped for any real implementation of this (`raid_reached`, `raid_suppressed`, or similar) —
   **zero matches in `src/`.** This appears to be either aspirational/legacy documentation with no
   V2 implementation, or a mechanic realized entirely through generic systems (ordinary combat
   damage, ordinary trauma adjustments) with no explicit "raid concluded" event marking it as such.
   Either way, it is not a signal this ticket's fix could hook into today — it doesn't exist as a
   detectable event.

**Conclusion: there is no real "raid concluded" signal anywhere in the codebase today, at any
level (mob, camp, or world) — not just missing for this one field.** Building one would be new
lifecycle infrastructure, not a small follow-up to the hotfix.

## The one directly relevant existing design commitment: WORLD-034

`docs/parity_ledger/world_dynamics.yaml`'s WORLD-034 (`verified`, P0): **"Raid mobs do not return
home."** This is a real, intentional design decision already on record — raid mobs are not meant to
navigate back to their origin once their raid concludes (by death, by reaching the target, or
otherwise). It's the closest existing precedent to "raid mobs have a deliberately different,
reduced lifecycle after their raid" — but it answers a *physical navigation* question ("does it go
home"), not the *project-eligibility* question this ticket is about ("can it ever do anything else
again"). A raid mob could, in principle, never navigate home and still become eligible for
whatever local opportunistic behavior the generic project/goal system would otherwise offer it
right where it ends up — those are logically separable questions, even though WORLD-034 shows the
project owners have already made *one* permanent-divergence decision about this entity class. It's
evidence worth weighing, not a settled answer to this ticket's own question.

## Options for peer/user review

1. **Leave `max_active_projects=0` permanent, as-is.** Justification would be: a raid mob's entire
   purpose is the raid; WORLD-034 already establishes raid mobs are intentionally not meant to
   return to a normal peacetime lifecycle. Cost: the disclosed behavior stands — a raid mob that
   survives its own raid (flees, is never engaged, or simply lingers) is permanently locked out of
   the project system for the rest of its in-world life, forever, with no future work needed. Risk:
   this was originally framed by the hotfix ticket as an accepted narrow side effect of a P0 fix,
   not as an intentional permanent design choice — this option effectively promotes it to one after
   the fact, which the user/peer may or may not actually want.
2. **Restore capacity via a real "raid concluded" signal — build one.** Requires deciding what
   "concluded" means for a *surviving* mob (death already implicitly "resolves" the mob regardless
   of capacity, so this only matters for survivors) — plausible candidates: reaching the raid
   target (win condition, but no explicit detection exists today either), a fixed number of ticks
   since raid spawn (crude, arbitrary, no existing precedent for a raid-duration timeout), or
   disengaging from all raid-relevant hostiles for N ticks (closest to a real "combat is over"
   signal, but "raid-relevant" would need its own definition). None of these has any existing
   scaffolding to build on — this is genuinely new lifecycle infrastructure, larger than "small,"
   matching this batch's own recurring pattern where a ticket framed as small turned out to need
   real new design work once investigated.
3. **Restore capacity unconditionally on some existing, cheaper signal** (e.g., N ticks after
   spawn, independent of any real "raid" tracking) as a cruder approximation. Cheaper than Option 2,
   but manufactures a fake signal with no connection to whether the raid the mob was part of is
   actually over — trading one disclosed-but-honest gap for an undisclosed, arbitrary one. Not
   recommended without a real reason a fixed-tick heuristic reflects reality here.

## No recommendation between 1/2/3 — this is the design question for peer/user

Per the ticket's own instruction, this investigation stops here rather than picking one. The real
open question is whether "raid mobs never regain project eligibility" is an acceptable permanent
behavior (given WORLD-034's adjacent precedent) or a real gap worth building new lifecycle
infrastructure for (given that no such infrastructure exists anywhere today, for any entity class,
to hook a "raid concluded" fix into).
