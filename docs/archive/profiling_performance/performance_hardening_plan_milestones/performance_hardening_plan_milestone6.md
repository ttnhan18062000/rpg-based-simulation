---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 6 — Regression Gate and Baseline Policy

## Goal

Prevent future optimization work from regressing performance or semantics.

The checklist claims CI/CD enforces a 15% performance regression threshold.  The tests also show a baseline comparison pattern allowing 20% regression or 5ms, whichever is larger.  This needs to be made strict and useful.

## Tasks

| Task                                      | Narrow implementation logic                                                | Files / area                       |
| ----------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------- |
| M6.1 Commit stable perf baselines         | Store baseline JSON for smoke scenarios only.                              | `tests/perf/baselines/`            |
| M6.2 Add baseline schema validation       | Fail if baseline file misses required metrics.                             | `scripts/check_perf_regression.py` |
| M6.3 Use dual thresholds                  | Use relative and absolute threshold. Example: `max(3ms, baseline * 1.15)`. | regression script                  |
| M6.4 Gate by metric type                  | Total compute, phase compute, memory max, memory delta.                    | regression script                  |
| M6.5 Add “needs baseline update” workflow | Baselines only updated intentionally, not automatically.                   | docs / scripts                     |
| M6.6 Fail on skipped baseline in CI       | Local can skip. CI cannot skip.                                            | pytest config                      |

## Acceptance checklist

```text
[ ] CI fails if baseline file is missing.
[ ] CI fails if benchmark schema is invalid.
[ ] CI compares compute metrics, not wall-clock polluted TPS.
[ ] Regression threshold is explicit and documented.
[ ] Baseline update requires intentional command/review.
[ ] Memory regression is checked separately from speed regression.
[ ] Phase-level regressions are visible even if total tick is still under cap.
```

## Exit condition

Performance regression becomes hard to sneak in.

---
