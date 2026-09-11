---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION
phase: done
date: 2026-09-08
tags: [world, architecture]
---

# TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION

## Title
`EntityGenerator.spawn_calamity()` confirmed superseded by `CalamityService`'s live `spawn_monster()` call — deleted

## Status
DONE

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
- [x] Fresh, re-confirmed grep evidence for whether `spawn_calamity()` has zero callers.
      `grep -rn "spawn_calamity" --include="*.py" .` (2026-09-11, pre-deletion): exactly one hit —
      the method's own definition. Zero callers anywhere, including tests.
- [x] A real disposition recorded with rationale, checked against
      `docs/mechanics/05_world_evolution.md`. **Remove** — confirmed superseded, not missing.
      `docs/mechanics/05_world_evolution.md` describes `CalamityService.process_world_dynamics()`'s
      own calamity-spawn mechanic (§ line ~450+: `CALAMITY_MIN_INTERVAL`/`CALAMITY_FORCE_INTERVAL`/
      `calamity_intensity > 0.3` gating) with no mention of `spawn_calamity()` or its
      maturity-scaled stat formula anywhere — the Bible was already written against the real,
      live mechanism (`generator.spawn_monster(kind="world_boss", ...)`), confirming no doc/mechanic
      depended on the dead method. No Bible correction needed.
- [x] Deleted: the dead method, with no dead-only test coverage to remove (it had none). Verified
      via `tests/unit/world/test_calamity_raid.py`, `test_stronghold.py`, `test_world_dynamics.py`
      passing unchanged, plus `tests/refactor/test_import_compatibility.py`.
- [x] Not applicable — disposition is remove, not wire-in.

**Surprise worth flagging, beyond confirmed-superseded**: the two implementations don't just use
different formulas, they land at wildly different power levels. `spawn_calamity()`'s hardcoded
formula gives `hp = 5000 * (1.0 + maturity * 0.5)` (5000-7500+ HP). The live path
(`spawn_monster(kind="world_boss", difficulty_tier=4)`) uses the generic `DIFFICULTY_TIERS[4]`
multiplier (`hp=4.0`) against a 50-HP monster base — roughly 200 HP before RNG-scaled
`evolution_level`, orders of magnitude weaker than what `spawn_calamity()` would have produced.
Both are still "spawn an entity when a calamity check fires" structurally, so the superseded
determination holds, but this is a real design-intent gap (was the live "world_boss" always meant
to be this much weaker than the abandoned Tier-5 design implies?), not just numeric noise. Flagged
to peer review rather than acted on — out of this ticket's own disposition-only scope.

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
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/systems/world_systems/generator.py` — `spawn_calamity()` deleted; `spawn_monster()` and
  `spawn_stronghold()` untouched and confirmed live
- `src/world/calamity.py` (`CalamityService.process_world_dynamics()`, the live calamity mechanism
  this duplicated)
- `src/world/spawn_config.py` (`DIFFICULTY_TIERS`, the real scaling table the live path uses —
  see the power-level discrepancy flagged in Acceptance Criteria)

## Assumptions / Open Questions
- ~~Whether "spawn a calamity as an entity" and "raise a region's `calamity_intensity`" were always
  meant to be two distinct mechanics, or whether `spawn_calamity()` is a superseded/abandoned
  earlier design for what `CalamityService` now does differently, is the central question — not
  assumed either way here.~~ **Resolved (2026-09-11), per peer review during
  `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`**: `CalamityService.process_world_dynamics()`
  (`src/world/calamity.py:23-77`, confirmed live and wired) already spawns a calamity entity
  directly — `generator.spawn_monster(kind="world_boss", pos=target_region.center,
  difficulty_tier=4)` — as part of its own real, tick-gated calamity check
  (`CALAMITY_MIN_INTERVAL`/`CALAMITY_FORCE_INTERVAL` against the highest-`calamity_intensity`
  region). This directly confirms `EntityGenerator.spawn_calamity()` is a **superseded duplicate**,
  not a missing/unwired mechanic — the live path already spawns a calamity entity, just via
  `spawn_monster()` with `kind="world_boss"` rather than via `spawn_calamity()` itself. Also note:
  the file path in this ticket's own header is stale — `spawn_calamity()` now lives at
  `src/systems/world_systems/generator.py:238`, not `src/world/generator.py:238-251`.

## Implementation Notes
Removed the `spawn_calamity()` method (`src/systems/world_systems/generator.py:238-253`) cleanly —
it had no test coverage to remove alongside it (unlike `BiologicalSystem.update()`, which came
with an entire orphaned test file). Left `spawn_monster()` and `spawn_stronghold()`, its siblings
in `EntityGenerator`, untouched — both confirmed live.

While comparing the two implementations' actual stat output (not just confirming "both spawn an
entity"), found the live `spawn_monster(kind="world_boss", difficulty_tier=4)` call produces a
character roughly 25-35x weaker (by HP) than what the deleted `spawn_calamity()` would have. Both
are still the same *kind* of mechanism — an entity spawned by a real, tick-gated calamity check —
so the superseded/delete disposition holds regardless, but this magnitude gap is worth someone with
game-balance context looking at separately; not expanded into here per this ticket's own
disposition-only scope.

## Test Summary
- `pytest tests/unit/world/test_calamity_raid.py tests/unit/world/test_stronghold.py
  tests/unit/world/test_world_dynamics.py -q` — 17 passed.
- `pytest tests/refactor/test_import_compatibility.py -q` — 3 passed.
- Final sweep: `grep -rn "spawn_calamity" --include="*.py" .` — zero hits.

## Files Changed
- `src/systems/world_systems/generator.py` — `spawn_calamity()` method removed

## Completion Summary
Confirmed superseded, not missing: `CalamityService.process_world_dynamics()` already spawns a
calamity entity via its own live `spawn_monster(kind="world_boss", ...)` call as part of a real,
tick-gated check. `docs/mechanics/05_world_evolution.md` was already written against that live
mechanism with no mention of the dead method or its formula, confirming nothing depended on it.
Deleted the method (no accompanying test existed). Flagged, but did not act on, a real power-level
discrepancy between the two implementations' formulas (~25-35x HP difference) discovered while
verifying they were behaviorally equivalent enough to call this a duplicate rather than a distinct
mechanic — out of scope for this disposition-only ticket.
