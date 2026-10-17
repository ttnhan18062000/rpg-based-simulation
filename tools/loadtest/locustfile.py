"""Locust scenario for the HTTP API (never the simulation tick).

One API key per Locust user, taken from a pool file, so the per-key admission bucket
(capacity 30, refill 3/s, src/api/admission_control.py) is not what gets measured.
LOADTEST_SINGLE_KEY=1 makes every user share key 0 (used once to show the pool works).
429 responses are failures with message ``admission_429``; 5xx are ``server_5xx_<code>``; other
statuses >= 400 are ``http_<code>``. Transport errors are reported by Locust itself (status 0).
No wait between tasks: the offered load is set by the user count.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path

from locust import HttpUser, task

from tools.loadtest.summary import classify_failure  # needs PYTHONPATH=<repo root> (run.py sets it)

KEYS_FILE = Path(os.environ.get("LOADTEST_KEYS_FILE", Path(__file__).resolve().parent / ".keys.txt"))
SINGLE_KEY = os.environ.get("LOADTEST_SINGLE_KEY") == "1"

_KEYS = [line.strip() for line in KEYS_FILE.read_text().splitlines() if line.strip()] if KEYS_FILE.exists() else []
_user_counter = itertools.count()


class ApiUser(HttpUser):
    wait_time = lambda self: 0  # noqa: E731 -- no think time

    def on_start(self) -> None:
        index = next(_user_counter)
        if not _KEYS:
            raise RuntimeError(f"no load-test keys at {KEYS_FILE}; run tools/loadtest/keys.py first")
        key = _KEYS[0] if SINGLE_KEY else _KEYS[index % len(_KEYS)]
        self.headers = {"X-API-Key": key}

    def _get(self, path: str, auth: bool = True) -> None:
        with self.client.get(path, headers=self.headers if auth else None, catch_response=True) as response:
            message = classify_failure(response.status_code)
            if message:
                response.failure(message)
            else:
                response.success()

    @task(3)
    def live_status(self) -> None:
        self._get("/api/v1/observability/live/status")

    @task(2)
    def state(self) -> None:
        self._get("/api/v1/state")

    @task(2)
    def live_health(self) -> None:
        self._get("/api/v1/observability/live/health")

    @task(1)
    def entities(self) -> None:
        self._get("/api/v1/entities")

    @task(2)
    def health(self) -> None:
        self._get("/health", auth=False)
