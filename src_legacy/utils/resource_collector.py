"""Background thread that periodically updates process resource metrics."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

_collector_thread: threading.Thread | None = None


def start_resource_collector(interval: float = 2.0) -> None:
    """Launch a daemon thread that updates CPU/RAM gauges every *interval* seconds."""
    global _collector_thread
    if _collector_thread is not None:
        return  # Already running

    def _collect_loop() -> None:
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not installed — resource metrics disabled.")
            return

        from src_legacy.utils.metrics import (
            PROCESS_CPU_PERCENT,
            PROCESS_MEMORY_RSS,
            PROCESS_MEMORY_VMS,
            PROCESS_THREAD_COUNT,
        )

        proc = psutil.Process()
        # Prime CPU measurement (first call always returns 0.0)
        proc.cpu_percent(interval=None)

        while True:
            try:
                PROCESS_CPU_PERCENT.set(proc.cpu_percent(interval=None))
                mem = proc.mind.memory_info()
                PROCESS_MEMORY_RSS.set(mem.rss)
                PROCESS_MEMORY_VMS.set(mem.vms)
                PROCESS_THREAD_COUNT.set(proc.num_threads())
            except Exception:
                logger.debug("Resource collection tick failed", exc_info=True)

            time.sleep(interval)

    _collector_thread = threading.Thread(target=_collect_loop, daemon=True, name="resource-collector")
    _collector_thread.start()
    logger.info("Resource collector started (interval=%.1fs)", interval)
