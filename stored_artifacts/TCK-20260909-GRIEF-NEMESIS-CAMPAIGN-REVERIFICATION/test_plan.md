# Test Plan — TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION

This ticket's own "test evidence" is the real-run investigation itself, not committed automated
tests (a pure investigation/determination ticket, no code changed). Evidence trail:

## Real multi-episode run (nemesis + grief episode-boundary)
- 3-episode `frontier_living_world` campaign, 150 ticks/episode, seed 42, real
  `scenario_event_recorder` collecting episode-boundary events, real per-episode
  `data/runs/{run_id}/simulation_events.jsonl` read directly for mid-tick events.
- Episode 0: 150 ticks completed, 765 real events, 13/16 entities alive at end.
- Episodes 1-2: both stalled at ~tick 52 with a real `LAW-SPAWN-OCCUPANCY` violation — traced to
  all 13 survivors reconstructing at `(0.0, 0.0)`.
- Result: `nemesis_relation_formed` and grief's episode-boundary path — **BLOCKED**, real evidence
  recorded, not negative.

## Real single-episode run (grief mid-episode path)
- 500-tick single-episode `frontier_living_world` run, seed 7, `Kernel._event_listeners` hooked
  directly for ground-truth per-tick observation.
- 4 real `lifecycle.active` True→False transitions observed directly (real deaths).
- Zero `grief_urgency_triggered` events.
- Root-cause check: for each of the 4 real deaths, every other alive entity's
  `entity.social.trust_history` toward the dead entity checked directly — all empty, for the
  entire run, despite 2470 real `cooperation_event`s.
- Result: grief's mid-episode path — **INCONCLUSIVE**, precondition (`ALLY_TRUST_THRESHOLD=0.30`)
  never met by any real death in this run; not evidence the detection mechanism itself is broken.

No regression test suite run — no production code was changed by this ticket.
