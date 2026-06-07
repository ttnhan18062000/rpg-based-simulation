# Test Plan — TCK-20260607-MON-RETRO

## Regression Surface
No existing tests affected — new tooling only.

## New Tests Required
Manual smoke tests:

1. `python3 tools/agent-monitoring/validate.py` — exits 0 on empty JSONL files
2. `python3 tools/agent-monitoring/query.py --runs` — "No matching runs." output
3. `python3 tools/agent-monitoring/generate_retro.py --all` — produces RETRO-ALL.md
4. `make agent-monitoring-validate` — passes through correctly
5. `make agent-monitoring-query ARGS="--status failed"` — runs correctly

## Scoped Pytest Commands
```
python3 tools/agent-monitoring/validate.py
python3 tools/agent-monitoring/query.py --runs
python3 tools/agent-monitoring/generate_retro.py --all
```

## Anti-Drift Test Guards
- validate.py must be idempotent — running twice gives the same result.
- generate_retro.py must not fail on empty JSONL files (0 runs, 0 events).
