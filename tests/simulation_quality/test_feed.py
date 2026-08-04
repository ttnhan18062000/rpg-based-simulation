from __future__ import annotations
import os
import pytest

from src.simulation_quality.feed import (
    BrokerQualityFeed,
    InProcessQualityFeed,
    QualityFeedMode,
    build_feed_from_env,
)


class _MockHub:
    def __init__(self):
        self.calls = []

    def on_envelope(self, envelope):
        self.calls.append(envelope)


def test_build_feed_returns_inprocess_by_default(monkeypatch):
    monkeypatch.delenv("QUALITY_FEED_MODE", raising=False)
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)
    feed = build_feed_from_env()
    assert isinstance(feed, InProcessQualityFeed)


def test_build_feed_returns_inprocess_when_explicitly_set(monkeypatch):
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)
    feed = build_feed_from_env()
    assert isinstance(feed, InProcessQualityFeed)


def test_build_feed_returns_none_when_disabled(monkeypatch):
    monkeypatch.setenv("QUALITY_SCORING_DISABLED", "1")
    feed = build_feed_from_env()
    assert feed is None


def test_build_feed_returns_broker_feed(monkeypatch):
    monkeypatch.setenv("QUALITY_FEED_MODE", "broker")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)
    feed = build_feed_from_env()
    assert isinstance(feed, BrokerQualityFeed)


def test_build_feed_raises_for_unknown_mode(monkeypatch):
    monkeypatch.setenv("QUALITY_FEED_MODE", "kafka")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)
    with pytest.raises(ValueError, match="kafka"):
        build_feed_from_env()


def test_inprocess_feed_start_stores_hub_reference():
    hub = _MockHub()
    feed = InProcessQualityFeed()
    feed.start(hub)
    assert feed._hub is hub
    feed.stop()
    assert feed._hub is None


def test_inprocess_feed_health_reports_status():
    hub = _MockHub()
    feed = InProcessQualityFeed()
    feed.start(hub)
    health = feed.health()
    assert "status" in health
    assert health["mode"] == "inprocess"
    assert health["status"] == "HEALTHY"
    feed.stop()


def test_inprocess_feed_health_when_stopped():
    feed = InProcessQualityFeed()
    health = feed.health()
    assert health["status"] == "STOPPED"


def test_broker_feed_skips_gracefully_when_redis_unavailable():
    hub = _MockHub()
    feed = BrokerQualityFeed(broker_url="redis://127.0.0.1:19999")
    # Should not raise — sets health to "unavailable" when Redis is not reachable
    feed.start(hub)
    health = feed.health()
    assert health["mode"] == "broker"
    assert health["status"] == "unavailable"


def test_broker_feed_stop_is_noop():
    feed = BrokerQualityFeed()
    feed.stop()


def test_quality_feed_mode_enum_values():
    assert QualityFeedMode.INPROCESS == "inprocess"
    assert QualityFeedMode.BROKER == "broker"


def test_broker_stream_name_defaults_to_observability_config(monkeypatch):
    from src.observability.config import ObservabilityConfig

    for var in ("QUALITY_STREAM_NAME", "SIM_STREAM_NAME", "RPG_STREAM_NAME"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QUALITY_FEED_MODE", "broker")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)

    feed = build_feed_from_env()
    assert isinstance(feed, BrokerQualityFeed)
    assert feed._stream_name == "simulation:events"
    assert feed._stream_name == ObservabilityConfig.get_stream_name()

    monkeypatch.setenv("QUALITY_STREAM_NAME", "custom:events")
    overridden_feed = build_feed_from_env()
    assert overridden_feed._stream_name == "custom:events"


def test_broker_url_defaults_to_observability_config(monkeypatch):
    from src.observability.config import ObservabilityConfig

    for var in ("QUALITY_BROKER_URL", "SIM_REDIS_URL", "RPG_REDIS_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QUALITY_FEED_MODE", "broker")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)

    feed = build_feed_from_env()
    assert isinstance(feed, BrokerQualityFeed)
    assert feed._broker_url == ObservabilityConfig.get_redis_url()

    monkeypatch.setenv("QUALITY_BROKER_URL", "redis://custom-host:6379/1")
    overridden_feed = build_feed_from_env()
    assert overridden_feed._broker_url == "redis://custom-host:6379/1"
