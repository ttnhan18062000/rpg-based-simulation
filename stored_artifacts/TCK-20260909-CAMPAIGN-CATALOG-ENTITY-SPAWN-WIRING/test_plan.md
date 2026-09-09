---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING
artifact_type: test_plan
tags: [world, content, architecture]
---

# Test Plan — TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING

Not yet implemented — planned tests, for peer review alongside `plan.md`.

1. **Unit**: `_build_initial_state()`'s "no alive carry-forwards" branch, for
   `campaign_life_arc`'s own real `world_composition`/`perspective`, returns a non-empty
   `entities` dict alongside the already-populated `regions`/`places` (matches the exact real
   entity count/composition already confirmed by hand in `investigation.md` — 15 entities for
   `frontier_living_world`/`hero_guild_perspective`).
2. **Unit/regression**: the survivor-reconstruction branch (real carry-forwards from a prior
   episode) is unaffected — same entity count/identity as before this change, confirmed by a real
   before/after comparison test (construct a `CampaignState` with real `persistent_entities`, call
   `_build_initial_state()`, assert the reconstructed entities match the carry-forward data exactly
   as the existing tests for this branch already verify).
3. **Integration, real production path**: a real `CampaignOrchestrator.run_episode()` call (not a
   lower-level unit call) for a `campaign_life_arc`-shaped manifest, confirming:
   - `kernel._current_tick_event_count` is non-zero for at least some ticks past tick 2 (not just
     tick 1's one-time seeding).
   - The episode runs to something close to its configured `tick_limit` rather than stalling at
     ~52 (the exact bound TBD during implementation — not "exactly `tick_limit`", since real
     gameplay may still legitimately end early via a real victory/failure condition, but
     materially past the old stall point).
   - No `scenario_stalled` event fires (or, if determinism means a much-later stall is still
     possible for a different, legitimate reason, that it isn't the same ~52-tick pattern).
4. **Regression**: full scoped suite —
   `tests/unit/domains/campaigns/ tests/integration/campaigns/ tests/integration/scenarios/
   tests/integration/worldassembly/ tests/unit/certification/ tests/integration/certification/
   -m "not slow and not extra_slow"` — must pass with no new failures (the certification/
   worldassembly suites are included since this ticket is the first live consumer of a pipeline
   those suites already cover; any latent gap in shared code should surface there too).
5. **If the position-resolution gap is deferred** (per `plan.md`'s recommendation): no test
   asserts distinct entity positions in this ticket — explicitly noted, not silently absent.

## Actual result (post-implementation)

Position resolution was NOT deferred without a fix — the co-location risk was verified real (a
sustained hard-law violation), so item 5 above was superseded: the interim scatter workaround does
get real test coverage. Final tests, all in `tests/integration/campaigns/
test_catalog_entity_spawn_wiring.py` (new, 4 tests, `@pytest.mark.slow`, all real — no mocking):

1. `test_episode_zero_spawns_real_entities_matching_the_world_composition` — real entities present,
   matching `frontier_living_world`'s own resolved kinds (16 entities after the `data/worlds/`
   directory switch, up from the originally-observed 15 under the poorer `data/content/` copy).
2. `test_episode_zero_entities_are_scattered_not_co_located` — every entity on a distinct tile.
3. `test_real_campaign_episode_does_not_stall_early` — via `CampaignOrchestrator.run_episode()`
   itself, confirms `completed_tick >= 65` (configured limit 70) — no ~52-tick stall regression.
4. `test_real_campaign_episode_event_stream_is_plausible_not_degenerate` — via the same real
   `ScenarioRuntimeService` construction `run_episode()` uses internally, with a
   `kernel._event_listeners` hook attached (`run_episode()`'s own `event_recorder` parameter,
   confirmed during implementation, only ever surfaces `scenario_objective_progressed`/`completed`/
   `stalled` — never the kernel-generated combat/cooperation/hard-law stream needed here). Asserts
   zero `InvariantViolation`, ≥3 distinct `combat_initiated` events, `cooperation_event` under 50%
   of total activity.

All 4 pass. Full scoped regression (`tests/unit/domains/campaigns/ tests/integration/campaigns/
tests/integration/scenarios/ tests/integration/worldassembly/ tests/unit/certification/
tests/integration/certification/ tests/unit/engine/ tests/unit/api/test_read_model_cache.py
-m "not slow and not extra_slow"`) — 587 passed, 2 skipped, 44 deselected, 0 failed.
