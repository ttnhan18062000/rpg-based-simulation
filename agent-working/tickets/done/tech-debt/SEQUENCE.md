# Implementation Sequence — tech-debt

Accumulated follow-up tickets from `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE` and
`TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY` (both DONE), plus 2 pre-existing disclosed
findings from the push-migration epic. Ordered per explicit user decision: the 4 contained,
self-scoped bug fixes first, then the quest-generation pair (the second depends on the first
being practically meaningful, even though both are independently implementable/testable).

## Order

1. **TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP** (hotfix) — `faction_monopoly`/
   `faction_conquest_degenerate` can never fire; `territory_ownership_changed` never carries the
   `faction_territory_pct` payload key either construction path's own scorer expects.
2. **TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE** (unknown tier — read ticket) —
   `test_all_enhancement_flags_default_to_off_or_shadow` fails against Phase 1's
   `ENABLE_PUSH_EVENT_SHAPERS=ON` deliberate default.
3. **TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG** (hotfix) —
   `test_scale_performance_and_footprint` places all 100 entities at the same tile, tripping a
   real `LAW-SPAWN-OCCUPANCY` violation.
4. **TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG** (standard) — `event_extractor.py`'s "quest_event"
   has no quest-type filter, mislabels every AI strategic goal as a quest.
5. **TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING** (standard) — the real quest system is
   unreachable from live gameplay; `GuildAction.visit()` has zero callers. Touches the AI
   strategic-decision/action-selection layer — a real gameplay-behavior change, not just an
   observability fix. Treat with more scrutiny than the others.
6. **TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP** (standard) — 3 of 5 quest kinds
   have no progress-evaluator wiring. Independently implementable/testable, but only practically
   meaningful once #5 lands (no real quests exist to reach these evaluators otherwise).

## Notes

- #1-#4 are independent of each other and of #5-#6 — no cross-dependency in implementation, just
  the user's own requested ordering.
- #6 depends on #5 for practical significance, not for its own tests (its own unit tests use
  hand-constructed `QuestState` fixtures, independent of whether #5 has landed).
