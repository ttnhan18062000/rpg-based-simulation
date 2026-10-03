# Plan — TCK-20260630-SIMQ-TIMEGATE

## Ordered Steps

### Step 1 — Read detection_params.yaml (DONE)
Exact threshold values captured in investigation.md. Key values:
- zero_harvest_after_tick=100, zero_crafting_after_tick=200, zero_trade_after_tick=300
- zero_quests_after_tick=200, zero_chronicle_after_tick=300
- progression_frozen_by_tick=200, xp_plateau_by_tick=50
- stasis_gate_ticks=5

### Step 2 — Write per-pillar time-gate unit tests
File: `tests/simulation_quality/test_timegate_penalties.py`
- 4 classes (ECONOMY, PROGRESSION, NARRATIVE, AGENCY)
- ~24 tests total — all fast (event injection, no engine run)
- Discoverable via `pytest -k timegate` because filename contains "timegate"
- Uses existing conftest.py `scoring_weights` session fixture
- Follows exact same _ctx()/_env() helper pattern as existing scorer tests

### Step 3 — Run 1000-tick calibrations
```bash
cd /home/vboxuser/Work/rpg-based-simulation
python3 tools/calibrate_simq.py --name sandbox_world --seed 42 --ticks 1000
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 1000
```
Output goes to:
- `data/calibration/sandbox_world_seed42_1000t/`
- `data/calibration/dungeon_crawl_seed42_1000t/`

### Step 4 — Skip simq_routing_test_seed42_500t
`data/calibration/simq_routing_test_seed42_500t/` already exists from ROUTING-TEST ticket.
No re-run needed.

### Step 5 — Run tests, verify acceptance
```bash
pytest tests/simulation_quality/test_timegate_penalties.py -v --timeout=60
pytest tests/simulation_quality/ -k timegate -v
pytest tests/simulation_quality/ -v --timeout=120 -m "not slow"
```

### Step 6 — Check parity ledger
Check infrastructure.yaml for SimQ time-gate entries. Update test_path if new tests cover
existing entries.

### Step 7 — Commit
Stage test file, calibration data, agent-monitoring/, ticket. Commit.

## Architecture Notes
- Unit tests inject events directly — NO durable state mutation
- No new engine behavior added — tests only
- Calibration output is observability data, not durable simulation state
- Verdict: APPROVED (architecture review phase 4)
