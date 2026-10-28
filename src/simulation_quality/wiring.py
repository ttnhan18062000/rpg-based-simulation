"""Builds the SimQ feed and in-process hub for one run (moved out of ``Kernel.__init__`` unchanged)."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, Tuple

from src.simulation_quality.feed import BrokerQualityFeed, build_feed_from_env
from src.simulation_quality.persistence import QualityPersistence
from src.simulation_quality.quality_hub import QualityHub
from src.simulation_quality.scorers import build_all_scorers
from src.simulation_quality.weights import ScoringWeights

logger = logging.getLogger(__name__)


def build_quality_wiring(run_id: str, run_dir: Optional[str]) -> Tuple[Optional[Any], Optional[Any]]:
    """Return ``(feed, hub)`` for the run: ``feed`` from the environment (None when SimQ is off), ``hub`` only for an in-process feed whose construction succeeded.

    A hub construction failure is logged and leaves ``hub`` None, so quality scoring is disabled for that run without failing it."""
    feed = build_feed_from_env()
    if feed is None or isinstance(feed, BrokerQualityFeed):
        return feed, None
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
            persistence=QualityPersistence(run_dir or f"data/runs/{run_id}"),
            run_id=run_id,
        )
        return feed, hub
    except Exception:  # noqa: BLE001 - SimQ is advisory: any construction failure disables scoring for the run, never the run itself
        logger.warning("SimQ hub construction failed (non-fatal) — quality scoring disabled for this run")
        return feed, None
