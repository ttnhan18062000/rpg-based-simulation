---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 0 — Freeze Audit Baseline

## Goal

Create a stable baseline before touching logic. Without this, every later optimization result is untrustworthy.

## Tasks

| Task                                          | Narrow implementation logic                                                                                             | Files / area                      |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| M0.1 Create audit branch                      | Branch from current uploaded source state. Name it clearly, e.g. `opt-profiler-hardening`.                              | Git                               |
| M0.2 Preserve current benchmark output        | Run current perf tests once and save raw JSON/report output. Do not “fix” anything yet.                                 | `tests/perf/*`                    |
| M0.3 Preserve current semantic test output    | Run unit/integration subset around kernel, pipeline, dirty, worker, resource, movement.                                 | `tests/unit`, `tests/integration` |
| M0.4 Create optimization audit ledger         | Add `docs/optimization_audit_ledger.md`. Track each issue, source file, test file, status, and proof type.              | `docs/`                           |
| M0.5 Mark current known risks as `not proven` | Add entries for profiler timing, frame pacing, DirtySet lifecycle, replay benchmark isolation, local/concurrent parity. | checklist / ledger                |

## Acceptance checklist

```text
[ ] Current baseline perf reports saved.
[ ] Current semantic test report saved.
[ ] Known issues recorded before implementation.
[ ] No source behavior changed in this milestone.
[ ] Every future milestone has a before/after comparison target.
```

## Required command set

```bash
pytest tests/unit/kernel tests/unit/core tests/integration/kernel tests/integration/pipeline -q
pytest tests/perf -q -m perf
```

Blunt truth: skipping this milestone is how you end up arguing from vibes instead of evidence.

---
