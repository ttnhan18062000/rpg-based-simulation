---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT
phase: open
date: 2026-09-14
tags: [observability, world]
---

# TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT

## Title
Two supposedly-parallel `_BOSS_KINDS` constants have silently drifted apart — `event_shapers.py`'s
copy is missing `"dragonkin"`, which `event_extractor.py`'s copy includes — meaning Lair-occupant
kills may be classified differently by two observability code paths that should agree

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while investigating `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s Finding 4/5.
`src/observability/event_shapers.py` defines `_BOSS_KINDS = frozenset(("world_boss",
"ancient_sentinel"))`. `src/observability/event_extractor.py` defines its own separate
`_BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel", "dragonkin"))`. These two constants
share a name and an obvious intent (classify which entity kinds count as "boss" for observability
purposes) but have drifted apart — one recognizes `dragonkin` (the Lair-occupant kind spawned by
`check_for_lair_spawn()` in `src/world/boss.py`) as a boss kind, the other does not.

Lower stakes than the gameplay-facing defects in the sibling ticket (this affects event
classification/telemetry shape, not the encounter itself), but it's a real, concrete instance of
the same "two things that should stay identical didn't" pattern — worth fixing on its own since it's
small and independent of any fix decision the sibling ticket is waiting on.

## Scope
- Confirm which of the two lists is correct (almost certainly `event_extractor.py`'s, since
  `dragonkin` is a real spawned kind per `src/world/boss.py::check_for_lair_spawn()`) by checking
  each constant's actual downstream usage/consumers.
- Reconcile the two constants — either extract a single shared constant both modules import, or, if
  architecture calls for them staying separate declarations, update `event_shapers.py`'s copy to
  include `"dragonkin"` and add a comment/test asserting they stay in sync.
- Small, targeted fix — do not restructure the observability event-shaping pipeline beyond this.

## Out of Scope
- The maturity/trauma gate reachability question, and the tier-5/loot defects — tracked in the
  sibling ticket, not this one.
- Any other observability constant beyond this one pair.

## Acceptance Criteria
- [ ] Both `_BOSS_KINDS` constants agree on membership (via a shared constant, or verified-identical
      duplicate declarations with a regression test preventing future drift).
- [ ] A test exists asserting `dragonkin` (and any other real boss/Lair-occupant kind) is classified
      consistently by both `event_shapers.py` and `event_extractor.py`.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)

## Related Docs
- None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/observability/event_shapers.py` (`_BOSS_KINDS`)
- `src/observability/event_extractor.py` (`_BOSS_KINDS`)
- `src/world/boss.py` (`check_for_lair_spawn()`, the real producer of `dragonkin` entities)

## Assumptions / Open Questions
- Whether any other entity kind besides `dragonkin` is missing from one list and not the other was
  not exhaustively checked here — only the one confirmed discrepancy is documented; whoever picks
  this up should diff the two full sets, not just add `dragonkin`.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
