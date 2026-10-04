---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT
phase: done
date: 2026-09-14
tags: [performance, testing]
---

# TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT

## Title
`assert_perf_threshold()` defaults to `hard=False`, so a perf-threshold breach only warns and can
never fail a test — a diagnosed defect, confirmed live with real breaching-but-green evidence

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Unlike the three sibling tickets filed alongside this one (`TCK-20260914-COOPERATION-FIND-PENDING-
OFFER-COST-OBSERVED`, `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`,
`TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`), **this ticket IS a diagnosed defect, not a
report-only observation** — the mechanism was read directly and the failure mode is confirmed, not
just measured.

`tests/tools/perf_assertions.py::assert_perf_threshold()`:

```python
def assert_perf_threshold(
    actual: float, limit: float, message: str, *, op: str = "<=", hard: bool = False,
) -> bool:
    ...
    ok = _OPS[op](actual, limit)
    detail = f"{message} (actual={actual!r} {op} limit={limit!r} -> {'OK' if ok else 'BREACHED'})"
    return perf_check(ok, detail, hard=hard)
```

`hard` defaults to `False`. On a breach, `perf_check(ok=False, ..., hard=False)` emits a
`PerformanceThresholdWarning` and returns `False` — it does **not** raise, so pytest reports the
test green regardless of the breach. Every call site that does not explicitly pass `hard=True`
inherits this silently — no error, no warning that would fail CI, just a `PerformanceThresholdWarning`
in the captured warnings summary that nobody is required to read.

This is already named, in the abstract, in
`docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`'s
own "Verified current-state gaps and migration" table (existing row: "`tests/tools/
perf_assertions.py` | Threshold checks default to `PerformanceThresholdWarning`; a breach can leave
pytest green"). **This ticket exists because a concrete, live instance of that already-known gap
was confirmed** while investigating `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`:

`tests/perf/test_perf_metropolis.py::test_perf_metropolis_stress` (1000 entities) already breached
both of its own thresholds with `ENABLE_COMBAT_ENGAGEMENT` OFF — avg TPS 1.8 against a limit of 3.0
(`op=">"`), and p99 tick time 1147ms against a limit of 500ms (`op="<"`) — and still reported
`1 passed, 2 warnings`. The test only turned red once the flag was enabled, and even then the real
failure was a wall-clock `TimeoutError` from the pytest harness's own resource budget
(`tests/conftest.py`), not this perf gate — the gate itself never fired in either state. A
500-entity companion test (`test_perf_metropolis_longevity`) shows the identical pattern: avg TPS
1.51-4.82 across multiple runs against a limit of 5.0, always reported green.

## Scope
- Decide the real migration path for `assert_perf_threshold()` and its call sites, per M4's own
  stated constraint ("These limitations are not permission to flip every warning or informational
  job to blocking at once. A noisy permanently-red gate trains maintainers to ignore it. Migration
  requires debt classification, stable thresholds, measured false-positive/false-negative behavior,
  named owners, and an expiry for every temporary exception.") — this ticket does not presuppose
  flipping every call site to `hard=True`.
- Inventory every existing `assert_perf_threshold()` call site and its current pass/fail history to
  distinguish stable thresholds (safe to make hard) from noisy/already-breaching ones (need
  recalibration first, per the metropolis tests' own now-confirmed breaching-green state).
- Consider whether the default itself (`hard=False`) should change, versus requiring every call site
  to opt in explicitly — a real design decision this ticket should investigate, not settle here.

## Out of Scope
- Recalibrating or fixing the specific breaching thresholds this ticket found (metropolis stress/
  longevity) — that's tracked in the sibling report-only tickets and the M4 gap-table row, not this
  ticket's own job, which is the gate mechanism itself.
- The re-tier of `test_perf_metropolis_stress` to `extra_slow`/`resource_budget_large` — already
  done and unrelated to this defect (a tier change, not a threshold change).

## Acceptance Criteria
- [x] A real migration plan exists (or this ticket concludes the M4 epic's own `PERF-M4-T02`/`T07`-shaped
  work already supersedes it and closes as a duplicate/superseded finding).
- [x] (moot, see Implementation Notes) Whichever calls sites are deemed stable enough to harden get `hard=True` with named-owner
  sign-off, per M4's own stated migration discipline.
- [x] The gap-table row in `performance_m4_baseline_gate_a_epic.md` is updated to reference this
  ticket's own disposition once resolved.

## Related Tickets
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` — where the concrete instance was found.
- `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED`,
  `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`,
  `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED` — report-only sibling tickets from the same
  investigation, kept separate since those are unexamined cost observations, not diagnosed defects.

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
  (existing gap-table row + "Confirmed field evidence, 2026-09-14" note)

## Related Code Areas
- `tests/tools/perf_assertions.py::assert_perf_threshold`, `perf_check`
- `tests/perf/test_perf_metropolis.py` (the two confirmed breaching-green call sites)

## Assumptions / Open Questions
- Whether other `assert_perf_threshold()` call sites across `tests/perf/`, `tests/arena/`, etc. show
  the same already-breaching pattern — not inventoried here, left to this ticket's own scope.

## Implementation Notes
### perf-planner dispatch notes, 2026-10-04

- **Intended disposition: close as superseded (AC1's second branch).** No `hard=True` flip in this
  ticket. Reasons to verify and cite, not assume:
  1. The call-site inventory this ticket's Scope asks for already exists: `tools/perf/perf_threshold_inventory.py`
     (M2-T01, PR #306) and `docs/performance/performance_clause_inventory.md` §7; checked in CI by
     `tests/tools/test_perf_inventories_committed_in_sync.py`. Regenerate it with the tool and quote the
     current counts (soft default, explicit `hard=False`, `hard=True`, pass-through wrappers).
  2. The owner's gate decision (roadmap, "Gate definition and partial lift", item 2): "no soft check
     becomes blocking" until the gate lifts. AC2 cannot be met now without breaking that.
  3. The migration path is M4's own: tripwire calibration and selected hard checks
     (`performance_m4_baseline_gate_a_epic.md` gap-table row + PERF-M4-T02/T07), under PERF-D4.
     Name the M4 candidate IDs that own the work after reading the epic; do not guess them.
- **The default question** (Scope item 3: should `hard=False` stay the default?) is recorded as an open
  input to that M4 work, with the two options and their trade-off, not decided here.
- **AC3.** Update the M4 gap-table row (line ~53) and the "Confirmed field evidence" note (~line 80) to
  point at this ticket's disposition and the M4 owner IDs.
- **Tier.** Stays `standard`. The staging artifacts can be short: `investigation.md` = the regenerated
  inventory counts plus the metropolis breaching-green evidence; `plan.md` = the disposition and doc
  edits; `test_plan.md` = the inventory sync test and `validate_frontmatter`. No `src/` or `tests/` edit.

**Disposition (perf-implementer, 2026-10-04): closed as superseded, AC1's second branch.**
- Inventory regenerated with `tools/perf/perf_threshold_inventory.py`: 55 call sites (49 `assert_perf_threshold`,
  6 `perf_check`); 0 literal `hard=True`, 0 explicit `hard=False`, 52 with `hard` absent, 3 passing it through
  a variable (`tests/perf/conftest.py` x2, `test_perf_regression_baseline.py:40`), all soft in practice.
- Owner's gate rule (roadmap, gate item 2): "no soft check becomes blocking". AC2 is therefore moot: no call site hardened.
- M4 owners, read from the epic table: PERF-M4-T02 (PR-fast performance tripwire), PERF-M4-T07 (evidence-bundle
  contract), PERF-M4-T10 (benchmark manifest and preflight, no-silent-skip), under PERF-D4.
- Default question (keep `hard=False` default vs require every site to choose) recorded in the M4 gap-table row as an
  open input; trade-off in `investigation.md`. Not decided.
- Edited: the `perf_assertions.py` gap-table row and the "Confirmed field evidence" note in the M4 epic.

## Test Summary
Docs only. `tests/tools/test_perf_inventories_committed_in_sync.py` and frontmatter validation run at close.

## Files Changed
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
- `docs/performance/benchmark_identity_schema.md` (F13: 66 -> 55 call sites, per clause inventory §7)
- `agent-working/tickets/` (this ticket), `agent-working/staging_artifacts/`/`stored_artifacts/` (3 artifacts)

## Completion Summary
Closed as superseded by M4 (PERF-M4-T02, T07, T10). No `src/` or `tests/` change; no call site hardened.
