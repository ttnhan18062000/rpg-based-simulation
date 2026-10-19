---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS
artifact_type: investigation
tags: []
---

# Investigation (2026-10-13, base rpg-single-pr aa7cd239e)

## The harness contract (read from tools/test_architecture/rpg_gate_run.py)
`compute(RunArtifacts(world, seed, ticks, sha, state, run_dir))` runs AFTER `kernel.shutdown()` flushed `data/runs/<run_id>/simulation_events.jsonl`. `state` is the FINAL state only. Metrics module: `src/observability/rpg_gate_metrics.py` (compute, pool). Config (worlds x 5 seeds x 5000 ticks, the R2 stop line on `O2.seeds_with_survivors`) is already in tests/simulation_quality/rpg_gate/config.yaml; known reds file is empty.

## What typed records a run leaves today
- `simulation_events.jsonl`: curated events (entity_killed, combat_damage, demographic_mortality, resource_harvested, conservation_law_verified, ...) PLUS the H6 channel (`starvation_channel_live`, `starvation_death_record`, `starvation_channel_tally`).
- NOT in the event stream: resolver transfers (who ate what from which source, forages, inn meals, shop sales, wages, coin moves). They exist only as `intent_results` on each tick's `EntityUpdate`. The final `state` has no history of them.
- Per-tick positions are not recorded (V5 needs every entity-tick).
- FEEDING_KILL and MEAT_DECAYED are `WorldEvent` categories (src/domains/world_emergence) and CORPSE_FOOD is a transfer source kind; whether the first two reach `simulation_events.jsonl` is unverified.
- Final-state facts available directly: entity kinds, alive flags, lifecycle death_reason/cause, corpses, ground items, treasuries (`global_resources`), total coin (`total_coin(state)`).

## Consequence for the design
V1 (food from nothing), V2 (meat balance), V4 (diet gates), V6 (no minted coin) and V7 (liveness), O4, O5, O6 need counts of transfers by (kind group, source kind) over the whole run; V5 and O2-over-time need per-tick observation. The final state cannot supply them. The H6 pattern solves it: a bounded, non-authoritative, run-scoped OBSERVER (class-level state cleared in `reset_run_state`, called from `run_state.extract_events`) that accumulates counts and writes ONE closing tally event, so `compute` reads typed records from the event file and never touches live state. The tally must carry a liveness header like H6 so a silent channel reads as no-data (harness_error), never as zero violations.
