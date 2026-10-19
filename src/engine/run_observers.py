"""Run observers: what the kernel offers a consumer of a run's event envelopes (decision 80 B).

The kernel knows no observer type. A composition root (the API engine manager, the CLI, a harness) passes ``RunObserverFactory`` callables to ``Kernel(observers=...)``;
the kernel builds each once the run directory is known, hands the recorder one fan-out, and drives the four stages below. A run observer reads event envelopes after the
tick, on the recorder's drain thread. It reads no state and writes none, so it cannot change a run's hash.

Shutdown order is part of the contract (TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD): ``stop_intake`` first, then the recorder joins its drain
thread and drains once more, and only then ``finish`` may close files the drain thread was writing.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol, Sequence, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunContext:
    """What a factory needs to build an observer: the run id and the directory the run's artifacts go to."""

    run_id: str
    run_dir: str


class RunObserver(Protocol):
    def on_envelope(self, envelope: Any) -> None:
        """One event envelope, on the recorder's drain thread (and in its final synchronous drain)."""

    def start(self) -> None:
        """After the event recorder exists."""

    def stop_intake(self) -> None:
        """Before the event recorder shuts down."""

    def finish(self) -> None:
        """After the event recorder has shut down and drained."""


RunObserverFactory = Callable[[RunContext], Optional[RunObserver]]


class RunObservers:
    """The built observers of one run, in registration order."""

    def __init__(self, observers: Sequence[RunObserver] = ()) -> None:
        self._observers: Tuple[RunObserver, ...] = tuple(observers)

    @classmethod
    def build(cls, factories: Sequence[RunObserverFactory], context: RunContext) -> "RunObservers":
        """Call each factory once; a factory returning None adds nothing. A factory that raises propagates (it is the factory's job to absorb a failure that must not stop a run)."""
        built = []
        for factory in factories:
            observer = factory(context)
            if observer is not None:
                built.append(observer)
        return cls(built)

    def __iter__(self):
        return iter(self._observers)

    def __len__(self) -> int:
        return len(self._observers)

    def of_type(self, kind: type) -> Optional[Any]:
        for observer in self._observers:
            if isinstance(observer, kind):
                return observer
        return None

    def on_envelope(self, envelope: Any) -> None:
        """Fan one envelope out in registration order; one observer raising does not stop the next (the recorder logs per call, never skips the file write)."""
        for observer in self._observers:
            try:
                observer.on_envelope(envelope)
            except Exception:
                logger.exception("run observer %s failed on an envelope", type(observer).__name__)

    def start(self) -> None:
        self._each("start")

    def stop_intake(self) -> None:
        self._each("stop_intake")

    def finish(self) -> None:
        self._each("finish")

    def _each(self, stage: str) -> None:
        for observer in self._observers:
            try:
                getattr(observer, stage)()
            except Exception:
                logger.warning("run observer %s failed in %s (non-fatal)", type(observer).__name__, stage, exc_info=True)
