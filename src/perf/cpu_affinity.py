"""The CPU set a perf run is allowed to use, as a canonical range string (schema 1.5, ``identity.runtime.cpu_affinity``).

``logical_cores`` and ``hardware_class`` read the host and do not change when a run is pinned (``taskset``, ``systemd-run -p AllowedCPUs=4-5``); two runs on
different CPU sets are different conditions, so the set is recorded and blocking.
"""

from __future__ import annotations

import os
from typing import Callable, Iterable, List, Optional, Set

UNKNOWN = "unknown"


def format_cpu_ranges(cpus: Iterable[int]) -> str:
    """``{4, 5}`` -> ``"4-5"``, ``{0..5}`` -> ``"0-5"``, ``{0, 2, 3}`` -> ``"0,2-3"``; a lone CPU is just its number; empty is ``""``."""
    ordered = sorted(set(cpus))
    parts: List[str] = []
    start = prev = None  # type: Optional[int]
    for cpu in ordered:
        if start is None:
            start = prev = cpu
        elif cpu == prev + 1:
            prev = cpu
        else:
            parts.append(_span(start, prev))
            start = prev = cpu
    if start is not None:
        parts.append(_span(start, prev))
    return ",".join(parts)


def _span(first: int, last: int) -> str:
    return str(first) if first == last else f"{first}-{last}"


def allowed_cpus(getter: Optional[Callable[[int], Set[int]]] = None) -> Optional[Set[int]]:
    """The CPUs this process may run on, or ``None`` where the platform cannot say (no ``os.sched_getaffinity``)."""
    getter = getter or getattr(os, "sched_getaffinity", None)
    if getter is None:
        return None
    try:
        return set(getter(0))
    except OSError:
        return None


def collect_cpu_affinity(getter: Optional[Callable[[int], Set[int]]] = None, unknown: str = UNKNOWN) -> str:
    """The canonical range string of the allowed CPUs, or ``unknown`` where the platform cannot say."""
    cpus = allowed_cpus(getter)
    return format_cpu_ranges(cpus) if cpus else unknown
