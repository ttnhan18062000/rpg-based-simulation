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
        from src.simulation_quality.scorers.agency import AgencyScorer
        from src.simulation_quality.scorers.combat import CombatScorer
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
        run_dir = os.environ.get("QUALITY_RUN_DIR", "data/runs/quality_worker")
        run_id = os.environ.get("QUALITY_RUN_ID", "broker_worker")

        weights = ScoringWeights.load(weights_path, grade_path, detection_path, profile)
        scorers = [AgencyScorer(weights), CombatScorer(weights)]
        persistence = QualityPersistence(run_dir)

        self._feed = BrokerQualityFeed(
            broker_url=os.environ.get("QUALITY_BROKER_URL", "redis://localhost:6379"),
            stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events"),
            consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
        )
        self._hub = QualityHub(scorers, weights, persistence, run_id)
        self._persistence = persistence
        self._stop_event = threading.Event()

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

        self._stop_event.wait()

        self._feed.stop()
        report = self._hub.get_quality_report()
        self._persistence.write_report(report)
        self._persistence.shutdown()
        http_server.shutdown()
        logger.info("QualityWorker: shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    QualityWorker().run()
