"""Entry point for running the QualityHub in a separate process (broker mode).

Usage:
    python -m src.simulation_quality.worker
"""
from __future__ import annotations
import json
import logging
import os
import signal
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

logger = logging.getLogger(__name__)


class _HealthHandler(BaseHTTPRequestHandler):
    hub: Any = None

    def do_GET(self) -> None:
        if self.path == "/health":
            payload = {"status": "ok", "feed_mode": "broker"}
            if self.hub is not None:
                try:
                    payload["current_tick"] = self.hub._tick
                    payload["run_id"] = self.hub._run_id
                except Exception:
                    pass
                try:
                    from src.simulation_quality.pillars import PillarId

                    payload["pillar_event_counts"] = {
                        pid.value: self.hub._accumulators[pid].snapshot()["event_count"]
                        for pid in PillarId
                    }
                except Exception:
                    pass
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


class QualityWorker:
    """Orchestrates broker-mode quality scoring in a dedicated process."""

    def __init__(self) -> None:
        from src.simulation_quality.feed import BrokerQualityFeed, build_feed_from_env
        from src.simulation_quality.persistence import QualityPersistence
        from src.simulation_quality.quality_hub import QualityHub
        from src.simulation_quality.scorers import build_all_scorers
        from src.simulation_quality.weights import ScoringWeights

        weights_path = os.environ.get(
            "QUALITY_WEIGHTS_PATH", "config/simulation_quality/scoring_weights.yaml"
        )
        grade_path = os.environ.get(
            "QUALITY_GRADE_PATH", "config/simulation_quality/grade_thresholds.yaml"
        )
        detection_path = os.environ.get(
            "QUALITY_DETECTION_PATH", "config/simulation_quality/detection_params.yaml"
        )
        profile = os.environ.get("QUALITY_PROFILE", "default")
        run_id = os.environ.get("QUALITY_RUN_ID", "broker_worker")
        run_dir = os.environ.get("QUALITY_RUN_DIR", f"data/runs/{run_id}")

        weights = ScoringWeights.load(weights_path, grade_path, detection_path, profile)
        scorers = build_all_scorers(weights)
        persistence = QualityPersistence(run_dir)

        self._feed = BrokerQualityFeed(
            broker_url=os.environ.get("QUALITY_BROKER_URL"),
            stream_name=os.environ.get("QUALITY_STREAM_NAME"),
            consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
        )
        self._hub = QualityHub(scorers, weights, persistence, run_id)
        self._persistence = persistence
        self._stop_event = threading.Event()
        self._stale_watchdog: threading.Timer | None = None

        logger.info(
            "QualityWorker: resolved broker config — url=%s stream=%s group=%s",
            self._feed._broker_url, self._feed._stream_name, self._feed._consumer_group,
        )

    def run(self) -> None:
        port = int(os.environ.get("QUALITY_WORKER_PORT", "8082"))
        _HealthHandler.hub = self._hub
        http_server = HTTPServer(("", port), _HealthHandler)
        http_thread = threading.Thread(target=http_server.serve_forever, daemon=True, name="quality-health-server")
        http_thread.start()
        logger.info("QualityWorker health server on :%d", port)

        def _sigterm_handler(signum: int, frame: Any) -> None:
            logger.info("QualityWorker: SIGTERM received — shutting down")
            self._stop_event.set()

        signal.signal(signal.SIGTERM, _sigterm_handler)
        signal.signal(signal.SIGINT, _sigterm_handler)

        self._feed.start(self._hub)
        logger.info("QualityWorker: broker feed started")

        stale_seconds = int(os.environ.get("QUALITY_STALE_WARNING_SECONDS", "30"))

        def _warn_if_no_events_consumed() -> None:
            if self._feed.events_consumed_count == 0:
                logger.warning(
                    "QualityWorker: no events received on stream=%s after %ds — check "
                    "producer-side SIM_STREAM_NAME/RPG_STREAM_NAME/SIM_REDIS_URL/RPG_REDIS_URL "
                    "env vars match this worker's resolved broker config (logged above)",
                    self._feed._stream_name, stale_seconds,
                )

        self._stale_watchdog = threading.Timer(stale_seconds, _warn_if_no_events_consumed)
        self._stale_watchdog.daemon = True
        self._stale_watchdog.start()

        self._stop_event.wait()

        self._stale_watchdog.cancel()
        self._feed.stop()
        report = self._hub.get_quality_report()
        self._persistence.write_report(report)
        self._persistence.shutdown()
        http_server.shutdown()
        logger.info("QualityWorker: shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    QualityWorker().run()
