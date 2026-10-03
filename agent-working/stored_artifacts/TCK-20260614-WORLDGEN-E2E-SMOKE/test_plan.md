# Test Plan — TCK-20260614-WORLDGEN-E2E-SMOKE

## Bash smoke (runtime)
```bash
python3 -m src cli --ticks 10 --seed 42 --world wilderness_survival   # PASS
python3 -m src cli --ticks 10 --seed 42 --world urban_political        # PASS
python3 -m src cli --ticks 10 --seed 42 --world dungeon_crawl          # PASS
python3 -m src cli --ticks 10 --seed 42 --world generated_frontier_3_42 # PASS
```

## Integration (compile path)
```bash
python3 -m pytest tests/integration/worldassembly/test_e2e_smoke.py -q  # 4/4 PASS
```

## Triage
No failures requiring hotfix tickets. Watchdog trip on wilderness_survival is engine throttle (not a crash).
