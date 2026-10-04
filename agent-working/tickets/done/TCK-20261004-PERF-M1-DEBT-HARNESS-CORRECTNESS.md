---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS
phase: done
date: 2026-10-04
tags: [performance, testing, bug]
---

# TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS

## Title
PERF-M1-T02: fix the long-run harness's work-debt accounting and test it with non-empty debt

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Released by the owner's partial lift of the RPG-core entry gate on 2026-10-04
(`performance_optimization_roadmap.md`, "Gate definition and partial lift"), which allows M1 to
edit `src/perf/long_run_harness.py`.

`LongRunStabilityHarness` (`src/perf/long_run_harness.py`, around line 211) computes
`candidate_count = sum(len(q) for q in kernel.state.work_debt.values())`. `work_debt` is
`Dict[str, int]` (`src/core/state.py`; PERF-D3: capacity debt is an integer counter per system), so
`len()` on an `int` raises `TypeError` on the first sample in which any debt exists. The
`if kernel.state.work_debt else 0` guard hides this while debt is empty, which is the case in every
fixture today. This is defect PA-02, found in the M0 audit and confirmed still present on 2026-10-03.
The `work_debt` sum on the line above is correct.

## Scope
- Fix `candidate_count` so it is defined for integer debt. Decide, with a reason written in the
  ticket, whether it means the number of systems with non-zero debt or is removed as a duplicate of
  `work_debt`. Do not keep a field whose meaning nobody can state
- Specification tests with non-zero debt and exact expected counts: one system with debt, several
  systems, a system whose debt returns to zero, and empty debt
- A run of the harness on a short fixture that really accumulates debt (for example a profile
  with a low phase budget, or a seeded `work_debt` in the initial state). Prove the samples report
  exactly the debt the state holds at each sampled tick
- Non-interference: show that sampling reads state only. The proof digest
  (`CanonicalStateHasher.get_hash`) of a run with sampling must equal the same run without
  sampling, at the same ticks
- Update `docs/performance/` text that describes the harness's debt fields, if there is any

## Out of Scope
- `src/engine/governor.py`, `src/engine/kernel.py` and the other gated files: no edit
- Changing what counts as work debt or how the governor consumes it (PERF-D3 is closed)
- Any baseline or capacity claim. Numbers from this harness stay provisional under the entry gate
- Combat-heavy scenarios: `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` is open

## Acceptance Criteria
1. With non-zero integer debt, the harness samples without error, and `work_debt` and the chosen
   `candidate_count` meaning match hand-computed values exactly
2. At least one test drives real (not mocked) debt accumulation through the kernel and checks the
   sampled values against `kernel.state.work_debt` at the same tick
3. The sampling-on and sampling-off runs produce equal proof digests at every compared tick
4. Revert test: putting back the old `len()` line makes the new tests fail with `TypeError`
   (record the output)
5. `tests/certification/test_cert_long_run_stability.py` still passes

## Related Tickets
- `TCK-20260913-PERF-M0-SOURCE-AUDIT` (PA-02 finding)
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` (avoid its path)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md` (PERF-M1-T02)
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (gate section)

## Related Stored Artifacts
- none

## Related Code Areas
- `src/perf/long_run_harness.py` (edit allowed)
- `src/core/state.py` (`work_debt`, read only)
- `tests/certification/test_cert_long_run_stability.py`

## Assumptions / Open Questions
- Any parity ledger entry (`infrastructure.yaml`) that cites the harness's debt fields must be
  updated with the fix
- If accumulating real debt is impossible without editing a gated file, stop and report it.
  Do not edit the gated file

## Implementation Notes
- Decision: `candidate_count` is renamed `systems_with_debt` = number of systems whose integer debt is > 0. The sum is already `work_debt`; the count shows whether debt is concentrated or spread, which the sum cannot. The old name promised a meaning nobody could state for an integer counter (PERF-D3). It had no consumer (not in `to_dict()`, no test, no doc), so the rename is safe.
- Three single-line edits in `src/perf/long_run_harness.py` (field, computation, constructor argument); line count unchanged, so docs citing `:225` and `:267` stay valid.
- Nothing in `src/` adds debt; it is only seeded into the initial state. The kernel drains `max_worker_count` per system per tick (`drain_debt`, floored at 0 in `apply.py:323`). So the tests seed debt through a wrapped scenario builder and let the real kernel drain it (`max_worker_count=1`), or hold it constant (`max_worker_count=0`).
- Determinism: tests use `audit_mode=True` and the `idle` scenario (no combat).
- No docs or parity-ledger entry cites the field (searched `docs/performance`, `docs/parity_ledger`, `docs/engine`).

## Test Summary
- New `tests/unit/perf/test_long_run_harness_debt.py`: 7 passed (4 parametrized debt shapes incl. empty; returns-to-zero; samples equal recorded kernel state at the same tick with warmup and sparse interval; harness digests equal a bare kernel loop at every tick).
- Revert proof (AC4): restoring the old `len()` line makes 6 tests fail with `TypeError: object of type 'int' has no len()` at `long_run_harness.py:211` (the empty-debt case still passes, which is why the defect was latent).
- AC2 as met: "real accumulation" is "seeded, then drained by the real kernel". In `src/`, nothing ever increases `AuthoritativeState.work_debt`: the only producer is the scheduler's `DRAIN_DEBT` item, whose executor `work_debt_update` is `-max_worker_count` (drain only); `apply.py:323` clamps at 0; dropped work goes to `RuntimeStatus` counters, not to `work_debt`; only `src/certification/scenarios.py::inject_work_debt` seeds it. So seeding is the only route (perf-planner confirmed this independently).
- AC5 NOT verified at full size (accepted by perf-planner as a stated known gap, not a pass). `test_cert_long_run_stability.py` is marked `slow` and `extra_slow`, so CI's `-m "not slow and not extra_slow"` never runs it. It does not read the renamed field (grep: 0 matches for `candidate_count`). Details: `tests/certification/test_cert_long_run_stability.py` cannot finish here. Under the default `medium` resource budget all three tests hit the 60 s limit (`TimeoutError` from `tests/conftest.py:90`); with `--resource-budget off` the determinism-parity test alone did not finish within 590 s under a 3 GB cap. Not caused by this change (a time limit, not an assertion). Substitute: a reduced metropolis run (200 ticks, 100 entities, interval 50) completes and reports `work_debt` 0 and `systems_with_debt` 0 at all 4 samples.

## Files Changed
- `src/perf/long_run_harness.py`
- `tests/unit/perf/test_long_run_harness_debt.py` (new)

## Completion Summary
The harness's debt count no longer crashes on integer debt: `candidate_count` became `systems_with_debt`. 7 new tests pass and reverting the line makes 6 fail with `TypeError`. AC5 is a known gap: the full certification test cannot finish on this machine, so only a reduced smoke run was done.
