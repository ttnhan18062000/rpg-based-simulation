"""Readiness wait for tests that boot `python -m src serve` as a subprocess."""
from __future__ import annotations

import subprocess
import time

import requests

POLL_INTERVAL_SECONDS = 0.1
READY_TIMEOUT_SECONDS = 30.0


def wait_for_server_ready(
    server: subprocess.Popen,
    port: int,
    *,
    timeout: float = READY_TIMEOUT_SECONDS,
    interval: float = POLL_INTERVAL_SECONDS,
) -> None:
    """Block until GET /health answers 200, or fail with the server's process state.

    /health is the only route exempt from API-key auth (src/api/server.py), so no
    credentials are needed. Fails fast if the subprocess has already exited.
    """
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout
    last_error = "no response yet"
    while True:
        returncode = server.poll()
        if returncode is not None:
            raise AssertionError(
                f"server on port {port} exited before becoming ready "
                f"(returncode={returncode}); last probe: {last_error}"
            )
        try:
            resp = requests.get(url, timeout=1.0)
            if resp.status_code == 200:
                return
            last_error = f"HTTP {resp.status_code}"
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"server on port {port} not ready after {timeout:.0f}s "
                f"(still running, server.poll()={server.poll()}); last probe: {last_error}"
            )
        time.sleep(interval)
