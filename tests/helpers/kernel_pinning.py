"""Shared pin for tests that run a real ``Kernel`` and must not depend on host speed.

TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER: four test files each carried an identical local copy of this
class, and a guard in ``tests/architecture/`` now flags a fifth.
"""
from __future__ import annotations

from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor


class PinnedNormalGovernor(ResourceGovernor):
    """Pins ``RuntimeMode.NORMAL`` so the outcome does not depend on host speed.

    The default governor derives its mode from wall-clock signals, so identical code and seed can give different outcomes on a slow or
    loaded host. ``force_mode`` is a no-op so the mid-tick wall-clock throttle cannot flip the mode either. Pair it with
    ``LocalSequentialExecutor`` and a large ``max_tick_budget_ms`` where the test needs a fully deterministic tick.
    """

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None
