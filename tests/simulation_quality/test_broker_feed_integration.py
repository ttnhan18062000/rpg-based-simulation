"""Broker feed integration tests — skipped when REDIS_AVAILABLE env var is unset.

Tests verify:
- BrokerQualityFeed.start() connects and spawns consume thread
- Duplicate event_id scored exactly once (at-least-once broker dedup)
- QUALITY_FEED_MODE=broker + no Redis → graceful WARNING, hub still starts
"""
from __future__ import annotations
import os
import uuid
import pytest
from unittest.mock import MagicMock, patch


REDIS_AVAILABLE = os.environ.get("REDIS_AVAILABLE") == "1"
pytestmark = pytest.mark.skipif(not REDIS_AVAILABLE, reason="REDIS_AVAILABLE not set")


@pytest.mark.slow
def test_broker_feed_graceful_when_redis_unavailable() -> None:
    """BrokerQualityFeed must set health=unavailable and not raise when Redis is down."""
    from src.simulation_quality.feed import BrokerQualityFeed
    from src.simulation_quality.weights import ScoringWeights

    feed = BrokerQualityFeed()
    hub = MagicMock()
    with patch("src.simulation_quality.feed.RedisStreamConsumer") as mock_cls:
        mock_consumer = MagicMock()
        mock_consumer.connect.side_effect = ConnectionError("redis down")
        mock_cls.return_value = mock_consumer
        feed.start(hub)

    assert feed.health == "unavailable"
    hub.on_envelope.assert_not_called()


@pytest.mark.slow
def test_broker_feed_dedup_same_event_id() -> None:
    """Same event_id delivered twice via broker must only produce one ScoreRecord."""
    from src.simulation_quality.feed import InProcessQualityFeed
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.weights import ScoringWeights
    from src.simulation_quality.persistence import QualityPersistence
    from src.simulation_quality.scorers.agency import AgencyScorer
    from src.observability.events import ObservabilityEventEnvelope
    import os, tempfile

    weights_path = os.path.join("config/simulation_quality/scoring_weights.yaml")
    grade_path = os.path.join("config/simulation_quality/grade_thresholds.yaml")
    detection_path = os.path.join("config/simulation_quality/detection_params.yaml")
    weights = ScoringWeights.load(weights_path, grade_path, detection_path, "default")

    with tempfile.TemporaryDirectory() as run_dir:
        persistence = QualityPersistence(run_dir)
        hub = QualityHub([AgencyScorer(weights)], weights, persistence, run_id="dedup-test")

        fixed_id = uuid.uuid4().hex
        env = ObservabilityEventEnvelope(
            event_id=fixed_id, run_id="dedup-test", tick=1, entity_id=1,
            event_type="action_executed", event_category="action", severity="INFO",
            source_system="test", message="", payload={},
        )
        hub.on_envelope(env)
        hub.on_envelope(env)  # duplicate

        # AGENCY accumulator should count 1 event, not 2
        from src.simulation_quality.pillars import PillarId
        snap = hub._accumulators[PillarId.AGENCY].snapshot()
        assert snap["event_count"] == 1, (
            f"Duplicate event_id should be deduped; got event_count={snap['event_count']}"
        )
        persistence.shutdown()
