"""SimQ as a run observer (decision 80 B): what ``Kernel.__init__`` and ``Kernel.shutdown`` used to build and call inline.

The composition root passes ``default_observer_factories()`` to ``Kernel(observers=...)``; the engine imports nothing from this package.
The behaviour is the one the kernel had: the feed comes from ``QUALITY_SCORING_DISABLED`` / ``QUALITY_FEED_MODE``, an in-process feed builds the hub
(a build failure is logged and leaves SimQ off for the run), a broker feed builds no hub (the external QualityWorker scores) and is only stopped.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, Tuple

from src.engine.run_observers import RunContext, RunObserverFactory

logger = logging.getLogger(__name__)


class QualityRunObserver:
    def __init__(self, feed: Any, hub: Any = None) -> None:
        self.feed = feed
        self.hub = hub

    @property
    def persistence(self) -> Any:
        return getattr(self.hub, "_persistence", None)

    def on_envelope(self, envelope: Any) -> None:
        if self.hub is not None:
            self.hub.on_envelope(envelope)

    def start(self) -> None:
        if self.hub is not None:
            self.feed.start(self.hub)

    def stop_intake(self) -> None:
        try:
            self.feed.stop()
        except Exception:
            logger.warning("SimQ feed stop failed (non-fatal)")

    def finish(self) -> None:
        if self.hub is None:
            return
        try:
            report = self.hub.get_quality_report()
            persistence = self.persistence
            if persistence is not None:
                persistence.write_report(report)
                persistence.shutdown()
        except Exception:
            logger.warning("SimQ final report write failed during shutdown (non-fatal)")


def quality_observer_factory(context: RunContext) -> Optional[QualityRunObserver]:
    from src.simulation_quality.feed import BrokerQualityFeed, build_feed_from_env

    feed = build_feed_from_env()
    if feed is None:
        return None
    if isinstance(feed, BrokerQualityFeed):
        return QualityRunObserver(feed)
    from src.simulation_quality.persistence import QualityPersistence
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.scorers import build_all_scorers
    from src.simulation_quality.weights import ScoringWeights

    try:
        weights = ScoringWeights.load(
            "config/simulation_quality/scoring_weights.yaml",
            "config/simulation_quality/grade_thresholds.yaml",
            "config/simulation_quality/detection_params.yaml",
            os.environ.get("QUALITY_PROFILE", "default"),
        )
        hub = QualityHub(
            scorers=build_all_scorers(weights),
            weights=weights,
            persistence=QualityPersistence(context.run_dir or f"data/runs/{context.run_id}"),
            run_id=context.run_id,
        )
    except Exception:
        logger.warning("SimQ hub construction failed (non-fatal) — quality scoring disabled for this run")
        return QualityRunObserver(feed)
    return QualityRunObserver(feed, hub)


def default_observer_factories() -> Tuple[RunObserverFactory, ...]:
    """What every caller that carried SimQ before decision 80 B passes to ``Kernel(observers=...)``."""
    return (quality_observer_factory,)
