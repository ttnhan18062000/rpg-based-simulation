---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM
phase: open
date: 2026-09-15
tags: [combat]
---

# TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM

## Title
`SensoryFilter.filter_saliency`'s hostility scoring reads the raw 4-value legacy `Faction` enum
instead of `EntityIdentityResolver`'s resolved `faction_id`, silently collapsing distinct
content-driven hostile factions into the same bucket — real but not the primary blocker for
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`

## Status
BLOCKED — **folded into `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` as its Group C site C1**
(2026-10-02, per owner decision 7's approved work order, `docs/plans/systemic_world/roadmap.md` §8 item
2). This site is `src/engine/cognition.py:44`, re-verified at `origin/main` `4c133297b` as still present
and still at line 44. **Do not implement it here** — one writer, one branch; the sweep owns the shared
catalog helper that every site including this one must use, and a separate fix would create the second
hostility predicate the sweep exists to prevent.

**One substantive change to this ticket's own finding, not just a re-home.** Its recorded **0.5% real
impact** was measured for one specific consumer and should **not** be inherited. `CombatEngageScorer`
calls `SensoryFilter.filter_saliency` on the line immediately above its own hostility test
(`src/ai/goals/scorers.py:107-108`), so this filter shapes the candidate set that
`TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (work-order item 1) will start
acting on — and that path was measured on 2026-10-02 to be high-volume, not marginal: `COMBAT_ENGAGE` is
the most frequent goal winner (485/1767 and 568/1744 competitions). The sweep's `test_plan.md` requires
re-measurement rather than carrying 0.5% forward.

Close this ticket when the sweep closes. The sweep's `plan.md` ("Docs and parity") carries that
instruction so it is not forgotten.

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while investigating `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`.
`SensoryFilter.filter_saliency` (`src/engine/cognition.py:44`) scores a neighbor's hostility with
`ent.identity.faction != subject.identity.faction` — the raw legacy `Faction` enum (`int = 0`,
`src/core/state.py:583`), a 4-value type (`HERO_GUILD`/`TOWN_COUNCIL`/`MONSTER_HORDE`/`NEUTRAL`)
predating the content-driven catalog faction system. It does not go through
`EntityIdentityResolver`, which `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` fixed specifically
because the legacy enum collapses most real catalog factions into `"neutral"`/coarse buckets — that
fix never reached this consumer, since it reads the raw field directly.

**Confirmed by direct probe against real `crowded_frontier` entities**: the legacy enum collapses
`bandit_company` (4 entities), `goblin_warband` (9), and `orc_clan` (5) — three genuinely distinct,
mutually-hostile real factions (confirmed hostile by catalog content) — into a single
`Faction.MONSTER_HORDE` bucket. So the `!=` check, and the +200/+500-nemesis/+grudge saliency bonus
gated on it, never fires between any of these three factions' entities.

**Measured real-world impact and found it small**: a 2000-tick instrumented run of
`crowded_frontier` found a real hostile target was dropped from the saliency `max_targets=5` cut
only 3 of 617 opportunities (0.5%) — worlds this small rarely have more than 5 real neighbors in
range at once, so the missing bonus almost never changes the outcome. **Real bug, not the
operative blocker for the sibling investigation** — filed as its own small, independently-fixable
finding rather than folded into that ticket's own scope.

## Scope
- Change `SensoryFilter.filter_saliency`'s hostility check to use `EntityIdentityResolver`'s
  resolved `faction_id` (matching `tactical.py`'s own hostiles-loop and `combat_engagement`'s
  `is_hostile_compat` usage), not the raw `entity.identity.faction` legacy enum.
- Add a regression test covering the exact collapse case found here (two entities from distinct,
  catalog-hostile factions that share the same legacy `Faction` enum value must still score the
  hostility bonus).

## Out of Scope
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own remaining scope — this finding is
  real but measured to be a minor contributor, not the primary blocker; that investigation
  continues independently.
- Any other consumer of the raw `entity.identity.faction` field not yet audited — this ticket fixes
  the one confirmed instance (`filter_saliency`); a broader audit of other raw-field reads is not
  in scope here.

## Acceptance Criteria
- `filter_saliency`'s hostility scoring uses the same resolved faction identity as the rest of the
  targeting/combat pipeline.
- New regression test passes; existing `tests/unit/` combat/cognition/tactical suites still pass.

## Related Tickets
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (parent investigation that surfaced
  this, measured its real-world impact as small, and continues independently)
- `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (fixed the same underlying legacy-enum problem
  for `EntityIdentityResolver`'s own consumers; this ticket closes the one consumer that fix missed)

## Related Docs
_(none)_

## Related Stored Artifacts
_(none — hotfix tier)_

## Related Code Areas
- `src/engine/cognition.py::SensoryFilter.filter_saliency`
- `src/entities/identity_resolver.py::EntityIdentityResolver`

## Assumptions / Open Questions
_(none)_

## Implementation Notes
_(none yet — not yet implemented)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
