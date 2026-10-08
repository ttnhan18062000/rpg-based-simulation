---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT
phase: done
date: 2026-10-06
tags: [performance, observability, documentation]
---

# TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT

## Title
Correct the operational-flags matrix to the flags the kernel really reads, and fix the test-matrix row that overclaims `FORCE_REPLAY_OFF` coverage

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
Filed by perf-planner on 2026-10-06 from the item the perf-planner handover listed as
"not filed: check the other FORCE_* flags". The user approved the P1-doc change on 2026-10-06.

`docs/engine/matrices/observability_operational_controls_matrix.md` (P1) §2 lists four runtime flags.
Checked against `main` at `80a0b7ea2`:

| Flag | Matrix says | Code |
|---|---|---|
| `FORCE_REPLAY_OFF` | Safe; emergency stop of the replay sink | Nothing in `src/` reads it. The kernel's real switch is lowercase `no_replay` (`src/engine/kernel.py` about line 222: sets `GovernorPolicy.replay_allowed=False`; also `self._no_replay` about line 242). |
| `SELECT_PROFILE` | Safe; startup/reset only | Nothing in `src/` reads it. |
| `FORCE_DEGRADED` | Safe; "accelerates shedding" | Nothing in `src/` reads it. The purpose is also stale: degraded modes shed no work in shipped runs (`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`, #380). |
| `FORCE_NORMAL` | Forbidden | Real: `ProfileValidator.validate_flags` rejects it, plus `BYPASS_GOVERNOR` and `DISABLE_RESOURCE_CEILINGS` (`src/config/validator.py` about line 66). |

Also:
- `validate_flags` checks `SURVIVAL_ONLY` + `REPLAY_ENABLED` combinations, but nothing in `src/` reads
  either flag.
- `docs/engine/matrices/observability_test_matrix.md` lists "`FORCE_REPLAY_OFF` flag active → sink never
  called" as covered. `tests/unit/core/test_operational_flags.py::test_safe_operational_flags_accepted`
  only checks the kernel does not raise; the flag is silently ignored. Unknown flags are ignored
  generally (`test_flags_cannot_alter_authoritative_semantics` relies on that).

No determinism or gameplay effect: unknown flags are no-ops. This is P1-doc drift plus one overclaiming
test row, the same class as the 7 engine docs corrected in #380.

## Scope
1. Matrix §2: list the flags the kernel actually reads that are operational (at least `no_replay`;
   check `no_frame_pacing`, `audit_mode`, `perf_tracker`, `force_full_scan`, `audit_dirty_set` in
   `Kernel.__init__` and decide which belong in an operational table vs. test/audit-only), and the
   forbidden list as enforced. Mark `FORCE_REPLAY_OFF`, `SELECT_PROFILE`, `FORCE_DEGRADED` as
   "not implemented" (keep the rows, so the drift is visible), and drop "accelerates shedding".
2. Matrix: note that `SURVIVAL_ONLY` / `REPLAY_ENABLED` are validated but unread.
3. Test matrix: replace the `FORCE_REPLAY_OFF` row with the real `no_replay` behaviour, pointing at a
   test that pins it.
4. Test: add a test that `flags={"no_replay": True}` sets `replay_allowed=False` on the kernel's
   policy and that the replay sink is not written (pick the strongest observable that does not need
   `src/` changes). Keep `test_safe_operational_flags_accepted`, but stop citing it as obedience proof.
5. Parity ledger `docs/parity_ledger/infrastructure.yaml`: add or update an entry for operational-flag
   obedience (status `verified` for `no_replay` + forbidden list, test path from step 4).
6. `make knowledge-index-update` after the doc edits.

## Out of Scope
- Implementing `FORCE_DEGRADED`, `SELECT_PROFILE` or `FORCE_REPLAY_OFF`, or renaming `no_replay`.
  Any `src/` change. If the fix seems to need one, stop and report to perf-planner.
- Removing the `SURVIVAL_ONLY` / `REPLAY_ENABLED` validator checks (that is a `src/` change).
- The archived copies under `docs/archive/engine_matrices/`.

## Acceptance Criteria
1. Every flag in the matrix §2 is either read by `src/` (with the file cited) or marked not implemented
   or forbidden; no "Safe" row names a flag nothing reads.
2. The test matrix cites no test for behaviour that test does not assert.
3. A new test fails if `no_replay` stops disabling replay (mutation proof: remove the `no_replay`
   branch locally, the test fails for that reason, then restore).
4. Parity ledger entry present with a passing `test_path`.
5. No file under `src/` changed.

## Related Tickets
- `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS` (#380; shedding docs corrected)
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (#379)
- `TCK-20260418-RESOURCE-OBSERVABILITY-M7` (origin of the flag table)

## Related Docs
- `docs/engine/matrices/observability_operational_controls_matrix.md` (P1)
- `docs/engine/matrices/observability_test_matrix.md`
- `docs/engine/contracts/concurrent_integrity_contract.md` ("Operational flag law")
- `docs/engine/contracts/resource_governor_contract.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS/investigation.md`

## Related Code Areas
- `src/engine/kernel.py` (`Kernel.__init__` flag reads; read only)
- `src/config/validator.py` (`ProfileValidator.validate_flags`; read only)
- `tests/unit/core/test_operational_flags.py`

## Assumptions / Open Questions
- Gate: docs + tests only, no `src/`, so it is outside the partial-lift file list. It still rides the
  next perf batch PR; perf-planner decides the batch.
- Whether `concurrent_integrity_contract.md`'s "Operational flag law" needs a wording touch is for the
  investigation to decide; it states rules, not a flag list.

## Implementation Notes
- **2026-10-08, re-check against `origin/main` `28d0af111` (after Phase A, #448) before starting:** the ticket's table still holds. `FORCE_REPLAY_OFF`, `SELECT_PROFILE`, `FORCE_DEGRADED`
  are read nowhere in `src/`; `ProfileValidator.validate_flags` (`src/config/validator.py:66`) still rejects `FORCE_NORMAL`, `BYPASS_GOVERNOR`, `DISABLE_RESOURCE_CEILINGS`, and
  `SURVIVAL_ONLY` / `REPLAY_ENABLED` are only validated. The kernel reads `audit_mode`, `audit_dirty_set`, `perf_tracker`, `force_full_scan` (`kernel.py:84-87`), `no_replay` (`:198`, `:218`,
  re-applied after each governor evaluation at `:566`) and `no_frame_pacing` (`:217`, used at `:467`). **New finding:** `perf_tracker` is stored in `Kernel._perf_tracker` and read nowhere.
  Phase A added a profile field `signal_contract`, not a flag; a flag cannot override it. The `FORCE_DEGRADED` row was already corrected by #380.
- Matrix section 1 now names all three enforced forbidden flags; section 2 is split into flags the kernel reads (with where), audit and test flags, not-implemented flags (rows kept), forbidden flags and validated-but-unread flags. `perf_tracker` is documented as accepted and unread. `concurrent_integrity_contract.md` and `resource_governor_contract.md` name none of these flags, so they needed no wording change (the ticket's open question).
- Test matrix: the `FORCE_REPLAY_OFF` row is replaced by `no_replay` (what it asserts and the test that pins it), plus rows for the unimplemented flags, the validated-but-unread pair and the forbidden flags; the exception name is corrected from `SecurityError` to `ConfigValidationError`.
- **Mutation proof:** disabling both `no_replay` branches in `kernel.py` (`__init__` and `_phase_init`) makes `test_no_replay_stops_the_replay_sink` fail with `assert 6 == 0` (the sink received 6 events); `kernel.py` restored, `git diff` clean.
- **Finding, not fixed (src/ out of scope):** `Kernel.__init__` validates flags (`self.validate(flags)`, `kernel.py:321`) after it has created the event recorder (`:264`), so a Kernel that rejects a flag leaks its background workers (a thread-leak guard caught 6). The forbidden-flag tests therefore call `ProfileValidator.validate_flags` directly; noted in INFRA-428's support boundary.

## Test Summary
- `tests/unit/core/test_operational_flags.py`: 10 passed (7 new): `no_replay` stops the sink and leaves the hash unchanged; the three unimplemented flags and the two validated-but-unread flags change nothing; each forbidden flag is rejected; the contradictory pair is rejected. `test_safe_operational_flags_accepted` is kept and its docstring no longer presents it as obedience proof.
- `tests/unit/tools`, `tests/docs`, `tests/parity` and the file above: 719 passed, 2 skipped, 1 xfailed. `tests/static` and `tests/architecture`: 194 passed. `uv run make code-health`: 0 new, 0 worse, 57 improved. No file under `src/` changed.

## Files Changed
- `docs/engine/matrices/observability_operational_controls_matrix.md`, `docs/engine/matrices/observability_test_matrix.md`, `docs/parity_ledger/infrastructure.yaml` (INFRA-428), `tests/unit/core/test_operational_flags.py`.

## Completion Summary
The operational-flags matrix now lists only controls the code reads, with where, and marks the rest not implemented, forbidden, validated-but-unread or no-effect. The test matrix cites tests that assert what it claims, including a mutation-proven test of the kernel's real replay switch, `no_replay`. Parity entry INFRA-428. No `src/` change.
