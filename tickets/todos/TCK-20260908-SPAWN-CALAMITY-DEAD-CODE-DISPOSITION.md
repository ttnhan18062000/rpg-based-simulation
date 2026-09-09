---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION
phase: open
date: 2026-09-08
tags: [world, architecture]
---

# TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION

## Title
Determine whether `EntityGenerator.spawn_calamity()` is genuinely dead code or an unimplemented/unwired mechanic

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found during `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN`'s survey of `state.maturity`
consumers: `EntityGenerator.spawn_calamity()` (`src/world/generator.py:238-251`) has the same
`state.maturity`-scaled stat pattern (HP/ATK/DEF/level) as `spawn_stronghold()`
(`generator.py:254-266`), which has a real, reachable caller
(`influence.py:94`). A repo-wide grep (including tests) at the time found **zero callers of
`spawn_calamity()` anywhere** — it was recorded as confirmed dead code with zero observed runtime
impact, and a judgment call was made not to file a separate ticket for it given that.

**Filed anyway per peer review (`rpg-feature-planning`, 2026-09-08)**: this session's own recent
history has a real base rate against the "harmless dead code" judgment call —
`decay_stale_beliefs()` (see `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`, re-scoped from
dead-code cleanup to "wire an unimplemented, doc-documented mechanic" after investigation) and the
camp-raid discard stub (`TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`, discarding valid raid
composition instead of using it) were both initially framed as inert/low-value findings and both
turned out to be real unimplemented mechanics, one of them compliance-tracked in docs. The pattern
suggests dead code in this codebase is often where an unbuilt feature is hiding, not truly inert —
worth a cheap, dedicated look rather than a same-ticket aside.

## Scope
- Re-confirm the "zero callers" finding is still accurate (a fresh grep, not trusting the prior
  survey's own snapshot).
- Determine whether `spawn_calamity()` was ever intended to be wired to a real caller (check
  `docs/mechanics/05_world_evolution.md` for any calamity-spawning mechanic that should route
  through an `EntityGenerator` call rather than, or in addition to, `CalamityService`'s own
  region-level `calamity_intensity` mechanism) — i.e. is this a genuinely orphaned duplicate of
  `CalamityService`'s calamity handling, or a distinct, never-wired "spawn a calamity as an entity"
  mechanic that the Mechanics Bible or another doc actually describes.
- Record a disposition: **remove** (confirmed truly orphaned, no doc/mechanic depends on it — safe
  deletion, not a shim) or **wire it in** (a real unimplemented mechanic exists and this is its
  intended entry point — re-scope as a standard-tier feature ticket if so, same as the belief-decay
  precedent).
- This is a hotfix-tier disposition-only ticket. If the disposition is "wire it in," do not
  implement that wiring here — re-file as its own standard-tier ticket with real scope, per the
  belief-decay precedent, rather than scope-creeping this one.

## Out of Scope
- `spawn_stronghold()` — already confirmed reachable and correct, not in question here.
- `CalamityService.apply()`'s own maturity-accrual mechanism — already investigated and accepted
  in `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN`, not reopened here.
- Actually implementing a wiring fix if that's the disposition — re-file per Scope above.

## Acceptance Criteria
- [ ] Fresh, re-confirmed grep evidence for whether `spawn_calamity()` has zero callers.
- [ ] A real disposition (remove / wire-in-as-new-ticket / confirmed-fine-as-is-with-reason)
      recorded with rationale, checked against `docs/mechanics/05_world_evolution.md`.
- [ ] If "remove": the dead method is deleted along with any dead-only test coverage referencing
      it, verified via the existing `src/world/` test suite passing unchanged.
- [ ] If "wire in": a new standard-tier ticket is filed with real scope; this ticket closes
      recording that handoff, no code changed here.

## Related Tickets
- `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (origin of this finding)
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (precedent: same "dead code" framing,
  re-scoped to a real unimplemented mechanic after investigation)
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (precedent: a discard stub that looked inert but
  discarded valid, usable composition)

## Related Docs
- `docs/mechanics/05_world_evolution.md` (calamity mechanics — check for a described entity-spawn
  path that would justify `spawn_calamity()`'s existence)

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/world/generator.py` (`EntityGenerator.spawn_calamity()`, `spawn_stronghold()` for
  comparison)
- `src/world/calamity.py` (`CalamityService`, the region-level calamity mechanism this may or may
  not duplicate)

## Assumptions / Open Questions
- Whether "spawn a calamity as an entity" and "raise a region's `calamity_intensity`" were always
  meant to be two distinct mechanics, or whether `spawn_calamity()` is a superseded/abandoned
  earlier design for what `CalamityService` now does differently, is the central question — not
  assumed either way here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
