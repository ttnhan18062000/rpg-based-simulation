"""Locust scenario for the HTTP API (never the simulation tick).

API keys come from a pool file and rotate round-robin PER REQUEST (not per user): with no think time one user
sends tens to hundreds of requests a second, far above one key's refill of 3/s, so a per-user key would measure
the per-key bucket (capacity 30, refill 3/s, src/api/admission_control.py) instead of the API. The pool therefore
carries at most about 3 x len(pool) requests/s before 429s start (250 keys: about 750 req/s).
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
_request_counter = itertools.count()  # shared by all users of this Locust process (gevent: one thread, no lock needed)


class ApiUser(HttpUser):
    wait_time = lambda self: 0  # noqa: E731 -- no think time

    def on_start(self) -> None:
        if not _KEYS:
            raise RuntimeError(f"no load-test keys at {KEYS_FILE}; run tools/loadtest/keys.py first")

    def _next_key(self) -> str:
        return _KEYS[0] if SINGLE_KEY else _KEYS[next(_request_counter) % len(_KEYS)]

    def _get(self, path: str, auth: bool = True) -> None:
        headers = {"X-API-Key": self._next_key()} if auth else None
        with self.client.get(path, headers=headers, catch_response=True) as response:
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
