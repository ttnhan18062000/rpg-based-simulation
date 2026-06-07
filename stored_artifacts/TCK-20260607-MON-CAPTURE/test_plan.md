# Test Plan — TCK-20260607-MON-CAPTURE

## Regression Surface
- `.claude/workflows/implement-ticket.js` — changes to the workflow script
- `CLAUDE.md` — new rules added

## New Tests Required
Manual verification:
1. Run implement-ticket with a hotfix ticket → confirm runs.jsonl + events.jsonl have entries
2. Run implement-ticket on a ticket that fails tests → confirm TESTS_FAILED run record exists with events up to Test phase
3. Confirm monitoring-write agent failure (simulate by temporarily breaking record_run.py) does NOT fail the workflow

## Scoped Pytest Commands
```
# No automated test added (workflow script testing is manual).
# Smoke test after implementation:
python3 tools/agent-monitoring/validate.py
```

## Anti-Drift Test Guards
- validate.py can cross-check runs.jsonl vs events.jsonl for orphaned runs.
