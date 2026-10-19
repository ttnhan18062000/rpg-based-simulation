"""Start `python -m src serve` for a test and wait until it answers, instead of sleeping a fixed time.

A server that compiles an authored world takes several seconds to come up, and how long depends on host load, so a fixed `time.sleep` made the tests that
use it fail with ConnectionRefused. `start_server` polls `/health` until it is ready (default 30 s) and, if the process exits or never comes up, fails
loudly with the server's own output."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from typing import IO, Mapping, Optional, Sequence, Tuple

import requests

READY_TIMEOUT_SECONDS = 30.0
POLL_INTERVAL_SECONDS = 0.25


def _output(log: IO[bytes]) -> str:
    log.flush()
    log.seek(0)
    return log.read().decode("utf-8", errors="replace")[-4000:]


def start_server(port: int, extra_args: Sequence[str] = (), env: Optional[Mapping[str, str]] = None,
                 timeout: float = READY_TIMEOUT_SECONDS) -> Tuple["subprocess.Popen[bytes]", IO[bytes]]:
    """Launch the server on `port` and return (process, log) once `/health` answers. The caller terminates the process and closes the log."""
    cmd = [sys.executable, "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR", *extra_args]
    log = tempfile.TemporaryFile()
    server = subprocess.Popen(cmd, env={**os.environ, **(env or {})}, stdout=log, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise AssertionError(f"the server on port {port} exited with code {server.returncode} before it was ready. Its output:\n{_output(log)}")
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=1.0).status_code < 500:
                return server, log
        except requests.RequestException:
            pass
        time.sleep(POLL_INTERVAL_SECONDS)
    server.terminate()
    server.wait()
    raise AssertionError(f"the server on port {port} was not ready after {timeout:.0f} s. Its output:\n{_output(log)}")


def stop_server(server: "subprocess.Popen[bytes]", log: IO[bytes]) -> None:
    server.terminate()
    server.wait()
    log.close()
