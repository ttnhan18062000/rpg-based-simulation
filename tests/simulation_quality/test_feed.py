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


def test_inprocess_feed_start_stop_no_thread_leak():
    hub = _MockHub()
    feed = InProcessQualityFeed()
    feed.start(hub)
    assert feed._worker is not None
    assert feed._worker.is_alive()
    feed.stop()
    assert feed._worker is None


def test_inprocess_feed_health_reports_status():
    hub = _MockHub()
    feed = InProcessQualityFeed()
    feed.start(hub)
    try:
        health = feed.health()
        assert "status" in health
        assert health["mode"] == "inprocess"
    finally:
        feed.stop()


def test_inprocess_feed_health_when_stopped():
    feed = InProcessQualityFeed()
    health = feed.health()
    assert health["status"] == "STOPPED"


def test_broker_feed_start_raises_not_implemented():
    hub = _MockHub()
    feed = BrokerQualityFeed()
    with pytest.raises(NotImplementedError):
        feed.start(hub)


def test_broker_feed_stop_is_noop():
    feed = BrokerQualityFeed()
    feed.stop()


def test_quality_feed_mode_enum_values():
    assert QualityFeedMode.INPROCESS == "inprocess"
    assert QualityFeedMode.BROKER == "broker"
