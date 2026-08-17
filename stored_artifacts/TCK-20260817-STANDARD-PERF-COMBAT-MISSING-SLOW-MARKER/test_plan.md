---
status: active
layer: performance
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER
tags: [testing, bug, performance]
---

# Test Plan: TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER

## Normal Flow
- `pytest tests/perf/test_perf_combat.py -m "not slow"` — 0 tests collected (fully excluded from
  the fast lane after the marker is added).
- `pytest tests/perf/test_perf_combat.py -m "slow" --resource-budget large` — all 4 parametrized
  cases (`[10]`, `[50]`, `[100]`, `[500]`) pass, matching the real CI `slow` job's own invocation.

## Edge Cases
- Confirm the marker applies to the whole parametrized function (all 4 cases), not just `[500]` —
  pytest markers on a parametrized function apply to every generated test id automatically; verify
  via `--collect-only -m "slow"` showing all 4 ids.

## Failure Modes
- If `--resource-budget large`'s 600s per-test wall-clock cap and 8GB memory cap are somehow still
  insufficient on the real CI runner (unlikely given local `[500]` measured ~440ms compute time,
  well under any budget concern), that would be a new, different finding requiring escalation — not
  expected, but worth confirming during the real test run rather than assuming.

## Regression-Prone Paths
- Confirm no other test in `tests/perf/test_perf_combat.py` (there is only the one parametrized
  function) is affected differently.

## Test Commands
```
.venv/bin/python3 -m pytest tests/perf/test_perf_combat.py --collect-only -m "not slow" -q
.venv/bin/python3 -m pytest tests/perf/test_perf_combat.py --collect-only -m "slow" -q
.venv/bin/python3 -m pytest tests/perf/test_perf_combat.py -m "slow" --resource-budget large -v
```
