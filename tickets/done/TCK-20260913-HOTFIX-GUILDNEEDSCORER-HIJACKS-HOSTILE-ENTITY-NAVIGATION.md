---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION
phase: done
date: 2026-09-13
tags: [cognition, combat]
---

# TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION

## Title
A raid-spawned `goblin_raider` has no strategic representation of its raid task, so once `ENABLE_GUILD_QUEST_GENERATION` actually reaches a real run, `GuildNeedScorer` freely assigns it a guild project and its navigation target is overwritten from its raid destination to the guild building

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Real regression found by CI on `flag-propagation-batch` (PR #182), confirmed by revert-and-compare,
not the wall-clock non-determinism it superficially resembled (identical failure value across 5
repeated runs, not intermittent). `tests/integration/world/test_camp_raid_targeting.py::
test_camp_triggered_raid_spawns_real_raiders_anchored_and_targeted_correctly` failed:
`goblin_raider` entities spawned by a camp-triggered raid targeted `(15.0, 31.0)` (the world's
`town_hall`) instead of `(25.0, 25.0)` (the real settlement the raid should target).

**First hypothesis, tried and rejected — recorded because it's a real correction, not because it
was right.** `GuildNeedScorer.score()`/`GuildVisitPhase.resolve()` have no faction filter, so the
initial fix scoped both to `Faction.HERO_GUILD`. That broke a real, live, intended case: an
instrumented check of `frontier_marches` (this batch's own real acceptance-signal corpus run)
showed `GuildAction.visit()`'s own real firing entity, and several other legitimate positive
`GuildNeedScorer` scores in that same world, belong to `TOWN_COUNCIL`/`NEUTRAL`/`MONSTER_HORDE`-
faction entities (guard, merchant, scout, sentinel, leader) — this repo's generic Tier-4 economic
scorers (`EatScorer`/`SleepScorer`/`TownScorer`/`GuildNeedScorer`) are not hero-only by design; any
entity with spare strategic capacity runs them. Restricting to `HERO_GUILD` broke
`tests/unit/engine/test_kernel_feature_flags_propagation.py::
test_guild_quest_generation_fires_in_unmodified_corpus_profile_without_env_var` — this batch's own
real acceptance-signal test — which is what caught the mistake before it shipped. Reverted.

**Real root cause, confirmed via `RaidService.spawn_raid()`'s own source** (`src/world/raid.py`):
a raid mob's `navigation.target` is a raw assignment (`replace(mob, navigation=replace(mob.
navigation, target=target))`) with **no accompanying strategic project or objective** — nothing
in the strategic layer represents "this entity is mid-raid." Since the mob's `strategic.projects`
starts empty, `GuildNeedScorer`'s own capacity check (`len(strat.projects) < profile.
max_active_projects`, default 3) sees full spare capacity and freely assigns a real guild project,
which then drives `navigation.target` to the guild building via the normal project-arrival
machinery — clobbering the raid's own directly-assigned target. This was structurally invisible
before `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` landed, since
`ENABLE_GUILD_QUEST_GENERATION` never reached `ON` in any real run before that. Verified directly,
twice: forcing the flag `OFF` restores correct raider targeting; the `ON` case shows the exact
guild-project hijack for all 3 raiders in the failing integration test's own scenario.

This is the same "looks-live-and-isn't, turns out to have a real bug once reached" pattern this
whole arc keeps finding — but more severe than most: it doesn't merely no-op, it actively breaks
existing hostile-creature behavior. It also validates the caution the propagation ticket's own
original filing raised before the blast-radius measurement reopened seeding as the leading option:
"turning on an unknown number of dormant features in one change is not something to discover after
merging." Discovered here post-merge-readiness (an already-open PR reported ready) because the
regression sweep for that batch scoped `tests/integration/kernel/` but not
`tests/integration/world/` — a real gap in that sweep's own scope, not just bad luck.

## Scope
- Give raid-spawned mobs (`RaidService.spawn_raid()`) `max_active_projects=0` on their own
  `CognitionProfile`, the narrow, correct signal that a single-purpose combat mob doesn't run the
  generic project/goal system at all — without touching `GuildNeedScorer`/`GuildVisitPhase` or any
  other scorer's own logic, and without affecting any other monster-spawning path (only
  `spawn_raid()`'s own mobs are touched; the general `spawn_monster()` factory, used by every other
  real spawn site, is untouched).
- Real test coverage: a real `RaidService.spawn_raid()` mob fed into `GuildNeedScorer` directly
  must score zero utility even with the flag `ON` and a real `town_hall` present.
- Re-run `tests/integration/world/test_camp_raid_targeting.py` directly to confirm the real
  regression is fixed, not just that a new unit test passes in isolation.
- Re-confirm this batch's own real acceptance-signal test
  (`test_guild_quest_generation_fires_in_unmodified_corpus_profile_without_env_var`) still passes —
  the fix must not re-break the thing the rejected first attempt broke.

## Out of Scope
- Auditing every other Tier-4 economic scorer (`EatScorer`, `SleepScorer`, `TownScorer`) for the
  same "no strategic representation of an externally-assigned task" shape — this ticket found and
  fixed the one confirmed live instance (raid mobs vs. `GuildNeedScorer`); a general audit of
  whether other externally-driven navigation assignments (if any exist) share this exposure is a
  real follow-up, not fixed here — scope creep risk on a P0 hotfix is worse than a narrower fix.
- A full strategic-project representation of the raid task itself (a real `ProjectState`/
  `ObjectiveState` for "raiding") — architecturally more correct in the abstract, but a materially
  larger change (new project kind, arbitration-priority tuning against other tier candidates,
  verifying navigation-target derivation matches byte-for-byte) than a P0 hotfix should carry.
  `max_active_projects=0` is the narrow, correct-enough signal for what a raid mob actually needs:
  no project system at all.
- Re-scoping `PaidInformationTransactionSystem`/other still-inert mechanisms for the same shape —
  unrelated, still unreachable, no evidence of this specific hijack pattern.

## Acceptance Criteria
- [x] Root cause identified via real code reading, not the first plausible-looking hypothesis —
      the faction-filter attempt is recorded as rejected, with the real evidence that rejected it.
- [x] Raid-spawned mobs given `max_active_projects=0`, narrowly scoped to `RaidService.spawn_raid()`.
- [x] Real test proving a real spawned raid mob never scores guild utility.
- [x] `tests/integration/world/test_camp_raid_targeting.py` passes again, confirmed directly (3
      repeated runs, not a single sample).
- [x] This batch's own real acceptance-signal test re-confirmed still passing.
- [x] Full `tests/integration/` suite re-run (not the narrower prior selection) to catch any other
      similarly-exposed side effect of this batch's propagation fix — 911 passed, 6 skipped, 0
      failures.

## Related Tickets
- `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (done — the fix
  that made this dormant bug reachable for the first time)
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (done — the ticket this
  propagation fix was originally for)

## Related Docs
None — no doc claims raid mobs run the project/goal system; nothing to correct.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/world/raid.py` (`RaidService.spawn_raid()`)
- `src/ai/goals/scorers.py` (`GuildNeedScorer.score()` — read, not modified; its existing capacity
  check is what the fix relies on)
- `src/core/strategic.py` (`CognitionProfile.max_active_projects`)

## Assumptions / Open Questions
- Whether other Tier-4 economic scorers have their own version of this exposure (an externally-
  assigned navigation target with no strategic representation) is a real open question,
  deliberately not resolved here (see Out of Scope).

## Implementation Notes
`RaidService.spawn_raid()` now sets each spawned mob's `strategic.profile.max_active_projects = 0`
alongside the existing `navigation.target` assignment, in the same `replace()` call. This makes
`GuildNeedScorer`'s own existing capacity check (`len(strat.projects) >= profile.
max_active_projects` → `0 >= 0` → `True`) correctly return zero utility for any raid mob,
regardless of flag state, without adding a new check to the scorer itself — the scorer's own logic
was already correct for this input once the input's own capacity is honest about being zero.

The rejected faction-filter attempt is left out of the final diff entirely (reverted cleanly, not
left as dead code) — see Request Summary for why it was wrong, not just that it was tried.

## Test Summary
- New: `tests/unit/world/test_calamity_raid.py::test_calamity_raid_spawning` extended to assert
  `mob.strategic.profile.max_active_projects == 0` for every spawned raid mob.
- New: `tests/unit/ai/test_guild_need_scorer.py::TestRealRaidMobNeverScoresGuild::
  test_real_spawned_raid_mob_scores_zero_guild_utility` — a real `RaidService.spawn_raid()` mob fed
  directly into `GuildNeedScorer`, flag `ON`, real `town_hall` present, scores zero.
- `tests/integration/world/test_camp_raid_targeting.py` — 3 repeated runs, all passing.
- `tests/unit/engine/test_kernel_feature_flags_propagation.py` (this batch's own real acceptance
  signal) — re-confirmed passing after the fix, not just before it.
- `tests/unit/world/`, `tests/unit/ai/`, `tests/unit/engine/`, `tests/unit/strategic/`,
  `tests/architecture/`, `tests/unit/cognition/`, `tests/unit/domains/information/`,
  `tests/certification/` — 1229 passed, 2 skipped, 0 failures.
- Full `tests/integration/` (`-m "not slow and not extra_slow"`, run in 3 chunks to stay within
  available memory) — 911 passed, 6 skipped, 0 failures.

## Files Changed
- `src/world/raid.py` — `spawn_raid()` zeroes spawned mobs' `max_active_projects`.
- `tests/unit/world/test_calamity_raid.py` — extended existing test with the new assertion.
- `tests/unit/ai/test_guild_need_scorer.py` — new end-to-end regression test.

## Completion Summary
Fixed a real, confirmed regression this batch's own propagation fix exposed. The first fix attempt
(faction-scoping `GuildNeedScorer`/`GuildVisitPhase` to heroes) was tried, found to break a real,
live, intended case in this batch's own acceptance-signal corpus profile, and reverted — recorded
here rather than hidden. The real root cause: raid-spawned mobs get a raw `navigation.target`
assignment with no accompanying strategic project, so any capacity-gated scorer that becomes
reachable can freely claim their navigation. Fixed narrowly by zeroing raid mobs' own project
capacity at spawn time — correct because a raid mob's entire purpose is the raid, not by touching
any scorer's own logic. Confirmed via the original failing test (3 repeated runs), this batch's own
acceptance signal (re-confirmed intact), and a full `tests/integration/` + broad unit sweep with no
other side effects found.
