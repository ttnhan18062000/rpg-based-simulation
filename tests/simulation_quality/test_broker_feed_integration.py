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
    with patch("src.observability.stream.consumer.RedisStreamConsumer") as mock_cls:
        mock_consumer = MagicMock()
        mock_consumer.connect.return_value = False
        mock_cls.return_value = mock_consumer
        feed.start(hub)

    assert feed.health()["status"] == "unavailable"
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


@pytest.mark.slow
def test_no_env_vars_set_broker_mode_producer_consumer_share_stream_name(monkeypatch) -> None:
    """TCK-20260702-OBSISO-BROKER-CONFIG AC #1: with zero QUALITY_*/SIM_STREAM_* env vars
    set, the producer (RedisStreamAdapter via get_event_stream_adapter()) and the consumer
    (BrokerQualityFeed) resolve to the same stream key purely through ObservabilityConfig's
    shared defaults — no manual stream-name alignment required."""
    import time
    from src.simulation_quality.feed import BrokerQualityFeed
    from src.observability.stream.factory import get_event_stream_adapter, reset_event_stream_adapter
    from src.observability.events import SimulationEvent

    for var in (
        "QUALITY_SCORING_DISABLED", "QUALITY_FEED_MODE", "QUALITY_STREAM_NAME",
        "QUALITY_BROKER_URL", "QUALITY_CONSUMER_GROUP",
        "SIM_STREAM_NAME", "RPG_STREAM_NAME", "SIM_REDIS_URL", "RPG_REDIS_URL",
        "SIM_STREAM_BACKEND", "RPG_STREAM_BACKEND",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QUALITY_FEED_MODE", "broker")
    monkeypatch.setenv("SIM_STREAM_BACKEND", "redis")

    reset_event_stream_adapter()
    try:
        feed = BrokerQualityFeed()
        assert feed._stream_name == "simulation:events"

        received = []
        hub = MagicMock()
        hub.on_envelope.side_effect = lambda envelope: received.append(envelope)

        feed.start(hub)
        try:
            adapter = get_event_stream_adapter()
            event = SimulationEvent(
                event_type="action_executed",
                event_category="strategy",
                tick=1,
                severity="INFO",
                source_system="test",
                message="broker-config integration test",
            )
            adapter.publish(event)
            adapter.flush()

            deadline = time.time() + 5.0
            while time.time() < deadline and not received:
                time.sleep(0.1)

            assert received, (
                "BrokerQualityFeed never received the published event — "
                "producer/consumer stream-name resolution diverged"
            )
        finally:
            feed.stop()
    finally:
        reset_event_stream_adapter()
