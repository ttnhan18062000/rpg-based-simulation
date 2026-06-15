# Plan — TCK-20260614-WORLDGEN-E2E-SMOKE

## Steps
1. Confirm all 4 composition YAML files exist in data/content/world_compositions/
2. Run `python3 -m src.worldbuilding.cli generate ...` to ensure generated composition is present
3. Run `python3 -m src cli --ticks 10 --seed 42 --world <id>` for each of 4 worlds
4. Triage any failures: data bug → fix here; engine bug → hotfix ticket
5. Run integration test suite for compile-path validation
6. Write batch epic monitoring record

## Execution
All 4 compositions already resolved in data/worlds/. Smoke runs confirmed PASS.
