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
