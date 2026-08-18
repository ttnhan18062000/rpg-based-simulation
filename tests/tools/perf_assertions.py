"""Shared soft-threshold assertion helper for performance/resource-threshold checks.

STOPGAP (TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING): right-sizing a hard-coded
performance threshold (tick compute time, memory delta, overhead %, RSS, throughput, p95
latency, etc.) against real, variable CI hardware is an ongoing engine-performance-
engineering problem, not a one-time test-fixing pass — see
docs/engine/performance_contract.md (Hardware Classes A/B/C) and
docs/performance/perf_baseline_policy.md for the calibration methodology this stopgap sits
on top of. Until that real profiling/hardware-classification effort lands (every `PERF_*`
profile in src/perf/profiles.py is hardcoded to HardwareClass.CLASS_A today, regardless of
actual runtime hardware), a threshold miss in tests/perf/, tests/arena/, and the
performance-only assertions in tests/certification/ is downgraded from a hard test failure
to a `PerformanceThresholdWarning` — visible in pytest's warnings summary (`-rw`),
non-blocking, and carrying the actual value, the limit, and the test identity, so the
accumulated warning history can drive that future engineering effort.

This is NOT a license to silently degrade correctness checks. Use `hard=True` for anything
that is not genuinely a "what's the right calibration number" question — hash/state
equality, invariant checks, structural correctness, gate-logic-against-synthetic-fixtures,
etc. stay hard failures. See docs/testing/regression_policy.md for the general
regression-vs-not framework this mechanism extends (§3 "Soft Monitors — Alert Only").

REVISIT: this stopgap should be revisited and reverted to hard assertions once real
engine-performance-engineering profiling work (right-sizing thresholds per hardware class)
lands. Tracked in TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING's Assumptions/Open
Questions — do not treat this as a permanent, silent weakening of the test suite.
"""
from __future__ import annotations

import os
import warnings
from typing import Callable, Dict


class PerformanceThresholdWarning(UserWarning):
    """A performance/resource threshold was missed.

    Non-blocking by design (temporary stopgap) — see this module's docstring for the
    rationale and the revisit condition. The warning message carries the actual measured
    value, the limit it was compared against, and the originating test's identity.
    """


def _current_test_id() -> str:
    """Best-effort test identity for the warning message, without requiring a fixture.

    pytest sets PYTEST_CURRENT_TEST during test execution to something like
    "tests/perf/test_x.py::test_y (call)" — strip the trailing " (phase)" suffix.
    """
    current = os.environ.get("PYTEST_CURRENT_TEST")
    if current:
        return current.split(" ")[0]
    return "<unknown test>"


_OPS: Dict[str, Callable[[float, float], bool]] = {
    "<=": lambda a, l: a <= l,
    "<": lambda a, l: a < l,
    ">=": lambda a, l: a >= l,
    ">": lambda a, l: a > l,
}


def perf_check(ok: bool, message: str, *, hard: bool = False) -> bool:
    """Report a performance/resource-threshold check result.

    Args:
        ok: Whether the check passed.
        message: Human-readable description of what was checked (include the actual
            value and limit in the message — this function does not format them for you).
        hard: If True, a failing check raises AssertionError (a normal hard gate) — use
            for correctness checks that happen to live in a perf-adjacent file but are not
            actually threshold-calibration questions. If False (default), a failing check
            emits PerformanceThresholdWarning instead of failing the test.

    Returns:
        True if `ok`. False if `ok` is False and `hard` is False (the warning path);
        never returns False when `hard=True` — that path raises instead.
    """
    if ok:
        return True
    full_message = f"[{_current_test_id()}] {message}"
    if hard:
        raise AssertionError(full_message)
    warnings.warn(full_message, PerformanceThresholdWarning, stacklevel=3)
    return False


def assert_perf_threshold(
    actual: float,
    limit: float,
    message: str,
    *,
    op: str = "<=",
    hard: bool = False,
) -> bool:
    """Compare `actual` against `limit` using comparison `op` (default "<=").

    On breach: hard=False (default) emits PerformanceThresholdWarning with the actual
    value, the limit, the comparison operator, and the test identity, instead of failing
    the test. hard=True raises AssertionError as a normal hard gate.

    Args:
        actual: The measured value.
        limit: The threshold `actual` is compared against.
        message: Human-readable description of what is being measured (e.g.
            "p95 tick compute time"). The actual/limit/op detail is appended automatically.
        op: One of "<", "<=", ">", ">=". Default "<=" (actual must not exceed limit).
        hard: See `perf_check`.

    Returns:
        True if within threshold. False if breached and hard=False (never returns on a
        breach when hard=True — that path raises instead).
    """
    if op not in _OPS:
        raise ValueError(f"Unsupported comparison op: {op!r} (expected one of {sorted(_OPS)})")
    ok = _OPS[op](actual, limit)
    detail = f"{message} (actual={actual!r} {op} limit={limit!r} -> {'OK' if ok else 'BREACHED'})"
    return perf_check(ok, detail, hard=hard)
