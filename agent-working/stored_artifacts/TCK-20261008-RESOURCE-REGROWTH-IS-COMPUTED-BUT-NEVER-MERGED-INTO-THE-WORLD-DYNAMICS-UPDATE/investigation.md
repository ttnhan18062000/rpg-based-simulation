---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE
artifact_type: investigation
tags: [ecology, economy, resource]
---

# Investigation

## Finding
`process_ecology` runs on the ECOLOGY_INTERVAL (200) multiples (world_dynamics cadence 50 lines up with them) and returns `nodes_add`, `next_node_id_set`, `node_updates` and `world_events_add`. `WorldDynamicsSystem.resolve_dynamics` used only the first two. Probe: 1000 ticks of crowded_frontier seed 42, every node's charge delta per tick: regrown by kind `{}`, harvested `{herb_patch: 5, berry_thicket: 8, wood_node: 8}`.

## Measurement (pinned NORMAL governor, audit_mode, budget off, LocalSequentialExecutor, seeds 42-46, 1500 ticks; base = origin/main 753f98ea9; new arm run twice, 15/15 digests identical)
Mean (SD) over 5 seeds, base to new. Probe `probes/regrow_ms.py`, driver `probes/job2.sh` + `probes/jobs2.txt`, per-run rows `probes/regrowth_runs.jsonl`.

| world | metric | base | new |
|---|---|---|---|
| crowded_frontier | alive t=1000 | 6.2 (2.2) | 5.0 (1.4) |
| | alive t=1100 | 2.8 (1.6) | 2.4 (0.5) |
| | deaths | 37.6 (1.5) | 37.8 (0.8) |
| | starvation deaths | 11.8 (5.3) | 10.0 (3.5) |
| | charges harvested | 11.4 (3.6) | 17.2 (5.2) |
| | charges regrown | 0 | 11.8 (3.3) |
| frontier_living_world | alive t=1000 | 15.4 (2.7) | 13.8 (3.6) |
| | alive t=1100 | 13.4 (3.4) | 11.6 (3.2) |
| | deaths | 43.2 (2.4) | 43.8 (2.6) |
| | starvation deaths | 14.4 (2.2) | 14.6 (2.5) |
| | charges harvested | 12.4 (1.3) | 19.4 (3.0) |
| | charges regrown | 0 | 13.2 (1.3) |
| urban_political | alive t=1000 | 12.2 (3.0) | 12.4 (4.0) |
| | alive t=1100 | 6.8 (3.5) | 6.2 (3.0) |
| | deaths | 23.8 (3.0) | 25.0 (2.3) |
| | starvation deaths | 10.8 (2.3) | 13.4 (1.5) |
| | charges harvested | 12.4 (1.3) | 19.4 (3.0) |
| | charges regrown | 0 | 13.2 (1.3) |

Reading: harvested charges rise about 50 percent because the nodes now refill. Population outcomes move within about 1 SD (the largest shift is urban_political starvation, +2.6 against an SD of 1.5 to 2.3, five seeds). Reported, not tuned. Regrowth is wood and herb only on the existing corpus; the world's node count is unchanged (ecology seeding is untouched).
