"""Shared pin for tests that run a real ``Kernel`` and must not depend on host speed.

TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER: several test files each carried an identical local copy of this
class; a guard in ``tests/architecture/`` now flags any new local copy.
"""
from __future__ import annotations

from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor


class PinnedNormalGovernor(ResourceGovernor):
    """Pins ``RuntimeMode.NORMAL`` so the outcome does not depend on host speed.

    The default governor derives its mode from wall-clock signals, so identical code and seed can give different outcomes on a slow or
    loaded host. ``force_mode`` is a no-op so the mid-tick wall-clock throttle cannot flip the mode either. ``zeroes_signals`` makes the Kernel
    feed the governors the same zeroed signals as ``audit_mode``, so the per-phase budgets (``PhaseBudgetGovernor``: scan policy and movement
    and strategic budgets switch at absolute 10 and 15 ms phase costs) cannot read the host's speed either; pinning only the mode left them live
    (TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR). Pair it with ``LocalSequentialExecutor``.
    Under ``audit_mode=True`` the Kernel zeroes the signals itself, so the pin is redundant there.
    """

    zeroes_signals = True

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None
