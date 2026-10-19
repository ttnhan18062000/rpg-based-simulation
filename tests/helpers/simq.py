"""Reading a kernel's SimQ run observer in tests (decision 80 B): the kernel holds run observers, not a hub."""
from __future__ import annotations

from typing import Any, Optional

from src.simulation_quality.observer import QualityRunObserver


def quality_observer_of(kernel: Any) -> Optional[QualityRunObserver]:
    return kernel.observers.of_type(QualityRunObserver)


def quality_hub_of(kernel: Any) -> Any:
    observer = quality_observer_of(kernel)
    return observer.hub if observer is not None else None


def quality_feed_of(kernel: Any) -> Any:
    observer = quality_observer_of(kernel)
    return observer.feed if observer is not None else None
