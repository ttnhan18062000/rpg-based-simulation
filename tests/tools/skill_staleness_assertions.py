"""Shared soft-check assertion helper for zero-invocation skill-staleness checks.

SOFT MONITOR (TCK-20260819-SKILL-STALENESS-SOFT-WARNING): whether a domain-specific skill
(e.g. `combat-mechanics`, `systems-economy`) ever accrues a real invocation depends on which
PRs happen to land and touch that domain — not something a test author or CI can force, and
some tracked skills may legitimately never accrue a real invocation by design. A skill's
grace-period expiry (`SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS`, see
`tools/agent-monitoring/generate_retro.py:536`: `if (today - added_date).days >=
SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS:`) is purely calendar-driven, so a real-corpus test
against `compute_zero_invocation_skill_flags()` can flip from pass to fail on any given day
independent of any code change. Unlike `tests/tools/perf_assertions.py`'s STOPGAP (which is
tied to a concrete future fix — engine hardware-profiling work landing in
src/perf/profiles.py — after which it reverts to hard), this mechanism has no analogous
owning future engineering effort that will convert it back to hard: there is no single event
that "finishes" skill-invocation coverage. It is a durable, open-ended soft monitor —
corpus- and calendar-driven — that self-clears per skill the moment that skill records a real
invocation or stays within its grace period; until then a flag miss on the 2 real-corpus tests
that use this helper emits a warning instead of failing the build. See
docs/testing/regression_policy.md for the general regression-vs-not framework this mechanism
extends (§3 "Soft Monitors — Alert Only").

This is NOT a license to silently degrade correctness checks. Use `hard=True` for anything
that is not genuinely a "is this skill's real-world usage signal current" question —
`compute_zero_invocation_skill_flags()`'s own logic/structural/source-inspection tests stay
hard failures, exactly the class of check `perf_assertions.py`'s docstring describes as
non-negotiable.
"""
from __future__ import annotations

import os
import warnings


class SkillStalenessWarning(UserWarning):
    """A tracked skill was flagged as zero-invocation-stale on the real corpus.

    Non-blocking by design (durable soft monitor) — see this module's docstring for the
    rationale. The warning message carries the actual flagged skill name(s), the grace
    period, and the originating test's identity.
    """


def _current_test_id() -> str:
    """Best-effort test identity for the warning message, without requiring a fixture.

    pytest sets PYTEST_CURRENT_TEST during test execution to something like
    "tests/tools/test_x.py::test_y (call)" — strip the trailing " (phase)" suffix.
    """
    current = os.environ.get("PYTEST_CURRENT_TEST")
    if current:
        return current.split(" ")[0]
    return "<unknown test>"


def skill_staleness_check(ok: bool, message: str, *, hard: bool = False) -> bool:
    """Report a zero-invocation skill-staleness check result.

    Args:
        ok: Whether the check passed.
        message: Human-readable description of what was checked (include the flagged
            skill name(s) and grace period in the message — this function does not format
            them for you).
        hard: If True, a failing check raises AssertionError (a normal hard gate) — use
            for correctness checks that happen to live alongside this mechanism but are not
            actually a corpus-currency question. If False (default), a failing check emits
            SkillStalenessWarning instead of failing the test.

    Returns:
        True if `ok`. False if `ok` is False and `hard` is False (the warning path);
        never returns False when `hard=True` — that path raises instead.
    """
    if ok:
        return True
    full_message = f"[{_current_test_id()}] {message}"
    if hard:
        raise AssertionError(full_message)
    warnings.warn(full_message, SkillStalenessWarning, stacklevel=3)
    return False
