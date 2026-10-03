# Investigation — TCK-20260614-WORLDGEN-E2E-SMOKE

## CLI invocation confirmed
- Sim: `python3 -m src cli --ticks 10 --seed 42 --world <world_id>`
- Compile: `python3 -m src.worldbuilding.cli compile <world_id>` or `make world-compile WORLD=<id>`
- Resolve composition: `python3 -m src.worldbuilding.cli resolve <world_id>`

## Worlds found in data/worlds/ (pre-compiled)
- wilderness_survival/
- urban_political/
- dungeon_crawl/
- generated_frontier_3_42/

## Integration test file
Already present at tests/integration/worldassembly/test_e2e_smoke.py (from WORLDDAT-COMPOSE agent)

## Pre-existing issues
- wilderness_survival had a watchdog trip (mid-tick emergency throttle at 96.57ms) — this is an engine throttle mechanism, NOT a simulation failure; LifecycleOutcome.SUCCESS confirmed.
