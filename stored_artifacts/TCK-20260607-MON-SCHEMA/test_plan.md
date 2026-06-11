---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260607-MON-SCHEMA
artifact_type: test_plan
tags: [mon, schema]
---

# Test Plan — TCK-20260607-MON-SCHEMA

## Regression Surface
No existing tests affected — this is new infrastructure with no dependencies on existing code.

## New Tests Required
Infrastructure tests (manual verification for this ticket):

1. `record_run.py` — appends valid JSON line, rejects missing required fields
2. `record_events.py` — appends valid JSON lines, truncates summary > 200 chars, rejects invalid status
3. `validate.py` — exits 0 on empty JSONL files
4. `query.py` — runs without error on empty JSONL files
5. `generate_retro.py --all` — produces a RETRO-ALL.md in agent-monitoring/retro/

## Scoped Pytest Commands
```
# No unit tests added in this ticket — infrastructure only.
# Manual smoke tests:
python3 tools/agent-monitoring/record_run.py --data '{"run_id":"test","start_ts":"2026-06-07T00:00:00Z","workflow":"test","tier":"standard","final_status":"DONE"}'
python3 tools/agent-monitoring/validate.py
python3 tools/agent-monitoring/query.py --runs
python3 tools/agent-monitoring/generate_retro.py --all
```

## Anti-Drift Test Guards
- `agent-monitoring/runs.jsonl` and `events.jsonl` must remain valid JSONL (one JSON object per line, no trailing commas).
- Both files should always be readable by `json.loads()` on each non-empty line.
