---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS
artifact_type: test_plan
tags: [simulation-quality, economy, adventure]
---

# test_plan.md — TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS

## Regression Surface (existing tests that must pass)

- `tests/unit/domains/adventure/` (if present) — `AdventureRouteScorer`/`AdventureRouteGenerator`
  unit tests must be unaffected, since this ticket makes no scoring/generation code changes (the
  investigation concluded the behavior is correct, not a bug — see investigation.md).
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` — ECONOMY anchors must be
  unaffected (no scoring change).

## New Tests Required (per AC)

Since the investigation's conclusion is "confirmed correct behavior, no fix" (AC3's documented
outcome, not AC2's fix-and-verify path), no new production test is required — there is no new
code path to cover. Documentation of the finding (AC3) is verified by direct diff review, not a
test.

## Scoped Pytest Commands

```
pytest tests/unit/domains/adventure/ -q
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

## Anti-Drift Test Guards

None new — no behavior changed, so no regression surface was created for future drift to hide in.
