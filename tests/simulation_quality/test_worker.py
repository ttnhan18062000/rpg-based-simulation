"""Unit tests for QualityWorker's env-var default resolution.

TCK-20260702-OBSISO-BROKER-CONFIG:
- G1: QualityWorker must not hardcode a stale stream-name/broker-url default independently
  of BrokerQualityFeed's own ObservabilityConfig-backed fallback.
- Step 3: QUALITY_RUN_DIR defaults from the already-resolved run_id, not a fixed literal, so
  distinct QUALITY_RUN_ID values don't collide on the same output directory.
- Startup diagnosability (ticket Scope item 3, filed as a DOD_BLOCKED gap and fixed post-Verify):
  the worker logs its resolved (url, stream, group) triple at INFO on construction, and warns
  if zero events have been consumed after QUALITY_STALE_WARNING_SECONDS — this is the failure
  that was previously silent when G1's mismatch existed.
"""
from __future__ import annotations
import logging
import os
import threading
import time
import pytest


_WEIGHTS_PATH = os.path.abspath("config/simulation_quality/scoring_weights.yaml")
_GRADE_PATH = os.path.abspath("config/simulation_quality/grade_thresholds.yaml")
_DETECTION_PATH = os.path.abspath("config/simulation_quality/detection_params.yaml")


def test_quality_worker_stream_name_defaults_to_observability_config(monkeypatch, tmp_path):
    from src.observability.config import ObservabilityConfig
    from src.simulation_quality.worker import QualityWorker

    for var in (
        "QUALITY_STREAM_NAME", "QUALITY_BROKER_URL", "SIM_STREAM_NAME", "RPG_STREAM_NAME",
        "SIM_REDIS_URL", "RPG_REDIS_URL",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))

    worker = QualityWorker()

    assert worker._feed._stream_name == "simulation:events"
    assert worker._feed._stream_name == ObservabilityConfig.get_stream_name()
    assert worker._feed._broker_url == ObservabilityConfig.get_redis_url()

    monkeypatch.setenv("QUALITY_STREAM_NAME", "custom:events")
    monkeypatch.setenv("QUALITY_BROKER_URL", "redis://custom-host:6379/1")
    overridden_worker = QualityWorker()
    assert overridden_worker._feed._stream_name == "custom:events"
    assert overridden_worker._feed._broker_url == "redis://custom-host:6379/1"


def test_quality_worker_run_dir_defaults_to_run_id(monkeypatch, tmp_path):
    from src.simulation_quality.worker import QualityWorker

    monkeypatch.delenv("QUALITY_RUN_DIR", raising=False)
    monkeypatch.setenv("QUALITY_RUN_ID", "my-run")
    monkeypatch.setenv("QUALITY_WEIGHTS_PATH", _WEIGHTS_PATH)
    monkeypatch.setenv("QUALITY_GRADE_PATH", _GRADE_PATH)
    monkeypatch.setenv("QUALITY_DETECTION_PATH", _DETECTION_PATH)
    monkeypatch.chdir(tmp_path)

    worker = QualityWorker()

    assert worker._persistence._run_dir == "data/runs/my-run"


def test_quality_worker_logs_resolved_broker_config_at_init(monkeypatch, tmp_path, caplog):
    from src.simulation_quality.worker import QualityWorker

    monkeypatch.delenv("QUALITY_STREAM_NAME", raising=False)
    monkeypatch.delenv("QUALITY_BROKER_URL", raising=False)
    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))

    with caplog.at_level(logging.INFO, logger="src.simulation_quality.worker"):
        QualityWorker()

    assert "resolved broker config" in caplog.text
    assert "simulation:events" in caplog.text


def test_quality_worker_warns_when_no_events_consumed_after_stale_window(monkeypatch, tmp_path, caplog):
    import signal as signal_module
    from src.simulation_quality.worker import QualityWorker

    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))
    monkeypatch.setenv("QUALITY_STALE_WARNING_SECONDS", "0")
    monkeypatch.setenv("QUALITY_WORKER_PORT", "0")
    monkeypatch.setattr(signal_module, "signal", lambda *a, **kw: None)

    worker = QualityWorker()

    with caplog.at_level(logging.WARNING, logger="src.simulation_quality.worker"):
        run_thread = threading.Thread(target=worker.run, daemon=True)
        run_thread.start()
        time.sleep(0.3)
        worker._stop_event.set()
        run_thread.join(timeout=5)

    assert not run_thread.is_alive()
    assert "no events received" in caplog.text
    assert "SIM_STREAM_NAME" in caplog.text


def test_quality_worker_no_warning_when_events_were_consumed(monkeypatch, tmp_path, caplog):
    import signal as signal_module
    from src.simulation_quality.worker import QualityWorker

    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))
    monkeypatch.setenv("QUALITY_STALE_WARNING_SECONDS", "0")
    monkeypatch.setenv("QUALITY_WORKER_PORT", "0")
    monkeypatch.setattr(signal_module, "signal", lambda *a, **kw: None)

    worker = QualityWorker()
    worker._feed.events_consumed_count = 1

    with caplog.at_level(logging.WARNING, logger="src.simulation_quality.worker"):
        run_thread = threading.Thread(target=worker.run, daemon=True)
        run_thread.start()
        time.sleep(0.3)
        worker._stop_event.set()
        run_thread.join(timeout=5)

    assert not run_thread.is_alive()
    assert "no events received" not in caplog.text


def test_quality_worker_hub_has_all_ten_pillars_represented(monkeypatch, tmp_path):
    """TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX: broker-mode hub must score all 10 pillars,
    not the AgencyScorer/CombatScorer-only pair worker.py previously hardcoded."""
    from src.simulation_quality.pillars import PillarId
    from src.simulation_quality.worker import QualityWorker

    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))

    worker = QualityWorker()

    represented = {
        scorer.PILLAR_ID
        for scorers in worker._hub.SCORER_REGISTRY.values()
        for scorer in scorers
    }
    assert represented == set(PillarId)


def test_quality_worker_health_payload_includes_per_pillar_event_counts(monkeypatch, tmp_path):
    import json
    import urllib.request

    from http.server import HTTPServer

    from src.observability.events import ObservabilityEventEnvelope
    from src.simulation_quality.worker import QualityWorker, _HealthHandler

    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))

    worker = QualityWorker()
    envelope = ObservabilityEventEnvelope(
        event_id="ev-1",
        run_id="test_run",
        tick=1,
        entity_id=1,
        event_type="action_executed",
        event_category="strategy",
        severity="INFO",
        source_system="test",
        message="test action",
        payload={},
    )
    worker._hub.on_envelope(envelope)

    _HealthHandler.hub = worker._hub
    http_server = HTTPServer(("127.0.0.1", 0), _HealthHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    try:
        port = http_server.server_address[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as resp:
            data = json.loads(resp.read())
    finally:
        http_server.shutdown()
        http_thread.join(timeout=5)

    assert "pillar_event_counts" in data
    assert data["pillar_event_counts"]["AGENCY"] == 1
    assert set(data["pillar_event_counts"].keys()) == {
        "COGNITION", "AGENCY", "COMBAT", "FACTION", "ECONOMY",
        "PROGRESSION", "SOCIAL", "INFORMATION", "WORLD", "NARRATIVE",
    }
