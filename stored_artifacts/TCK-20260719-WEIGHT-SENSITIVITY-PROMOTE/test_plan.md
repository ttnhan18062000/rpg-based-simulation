---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE

## Regression Surface

- `tests/tools/test_cost_proxy.py` — unaffected (no change to `cost_proxy.py`'s constants or
  formula), must stay green as a regression guard.
- `tests/tools/test_validate_agent_monitoring.py` — unaffected, same guard.
- No existing test references `experiments/cost_proxy_calibration/validate_rank_order.py` (it had
  zero test coverage before promotion, per this repo's `experiments/` exemption) — nothing to
  break by deleting it.

## New Tests Required (`tests/tools/test_weight_sensitivity_check.py`)

- `_score_with_weights` matches the hand-computable formula for a mixed tool-row group.
- `_score_with_weights` on an empty group is `0.0`.
- `SHIPPED_WEIGHTS` reflects `cost_proxy.py`'s real live constants, not a second hardcoded copy
  (guards against silent drift if `cost_proxy.py`'s weights ever change).
- Pure-Python Spearman correlation: identical rankings → `1.0`; fully reversed → `-1.0`; fewer
  than 2 keys → `None`.
- `compute_weight_sensitivity_report()` basic grouping/ranking correctness against a small
  hand-computable fixture.
- A `(run_id, seq)` group with tool rows but no matching event is silently skipped, not a crash.
- Empty input (`{}`, `{}`, `{}`) does not crash, returns zeroed/empty report shape.
- A group that reorders materially between baseline and candidate weights shows a nonzero
  `rank_delta` — the core signal this whole tool exists to surface.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_weight_sensitivity_check.py -q
python3 -m pytest tests/tools/test_cost_proxy.py tests/tools/test_validate_agent_monitoring.py -q
```

## Manual/CLI Verification (beyond unit tests)

- `python3 tools/agent-monitoring/weight_sensitivity_check.py --candidate-weights '<Fit C JSON>'`
  against the real live corpus — must run cleanly and produce output consistent with the original
  experiment's findings (same order of magnitude Spearman correlation, same class of rank-delta
  movers).
- `python3 tools/agent-monitoring/weight_sensitivity_check.py` (no args) must exit non-zero with a
  clear, standard argparse error (`--candidate-weights` is `required=True`) — never a silent
  no-op or a crash with a Python traceback.
- `python3 tools/agent-monitoring/weight_sensitivity_check.py --candidate-weights 'not json'` must
  print a clear `ERROR:` message and exit 1, not crash with an uncaught `JSONDecodeError`.
- `python3 tools/agent-monitoring/weight_sensitivity_check.py --candidate-weights '{"bash": 1}'`
  (missing keys) must print a clear `ERROR:` message naming the missing keys and exit 1.
- `make agent-monitoring-weight-check ARGS='--candidate-weights "..."'` must work end to end
  through the new Makefile target.

## Anti-Drift Test Guards

- The `SHIPPED_WEIGHTS`-reads-real-constants test is load-bearing — it's what prevents this
  promoted tool from silently drifting out of sync with `cost_proxy.py` the way the pre-promotion
  experiment script's own hardcoded `W_SHIPPED` copy could have.
- The material-reorder test proves the tool actually detects what it's meant to detect, not just
  that it runs without crashing on well-behaved input.
