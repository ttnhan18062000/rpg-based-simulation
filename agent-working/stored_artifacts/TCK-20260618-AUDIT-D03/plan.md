# D03 Audit Plan

## Approach
Run-sim method. Two 200-tick runs (seeds 42 and 137). Observe metric windows,
simulation events, entity chunk data for goal variety, movement, resource use, quest activity.

## Data Sources
- data/runs/{run_id}/metric_windows.jsonl
- data/runs/{run_id}/simulation_events.jsonl
- data/runs/{run_id}/chunk_000*.json (REFINED_UPDATE events)
- data/worlds/sandbox_world/world.yaml (pre-condition bug found and fixed)
