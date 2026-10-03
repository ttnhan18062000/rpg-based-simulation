---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION
artifact_type: test_plan
tags: [observability, engine, economy, faction, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION

## Tests

- `tests/unit/observability/test_event_shapers_economy_faction.py` (new, 20 tests): registry
  extension; all 7 EconomyShaper events (6 source_kind branches + rejected-intent no-op);
  `paid_info_changed_goal`'s prior-state-dependent condition (both emit and non-emit cases); all 8
  FactionShaper events including diplomatic-pair dedup and the `alliance_proposed`
  prior-state-conditional case (both NEUTRAL→ALLIED and already-ALLIED cases); `resource_seized`'s
  positive-tension-delta gate; both `world_events_add`-driven events; an unrelated category
  producing no event.
- Full `tests/unit/observability/`: 793 passed, 6 skipped (up from 779 pre-ticket).
- Real kernel integration: `dungeon_crawl_seed42_500t` with `ENABLE_PUSH_EVENT_SHAPERS=SHADOW`,
  event-type counts captured via a monkeypatched `run_shadow_shapers` — `diplomatic_transition: 29`
  and `hazard_drain_applied: 10` match this session's earlier raw-event investigation of the same
  world/seed exactly.

## Out of scope

Corpus-wide event-for-event comparison and performance re-validation —
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s scope.
