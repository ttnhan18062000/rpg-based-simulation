# Suggested file 1: tests/helpers/runtime.py

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

import requests


def python_executable() -> str:
    """Return the exact Python executable running the current pytest process."""
    return sys.executable


def module_cmd(*args: str) -> list[str]:
    """Build a portable command for `python -m src ...` tests."""
    return [python_executable(), "-m", "src", *args]


def run_src_module(*args: str, env: dict[str, str] | None = None, timeout: float = 30.0) -> subprocess.CompletedProcess:
    """Run `python -m src ...` portably across Windows/Linux/macOS."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    return subprocess.run(
        module_cmd(*args),
        env=merged_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def get_free_port() -> int:
    """Return a currently free localhost TCP port for API/server tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_http(url: str, *, timeout: float = 10.0, interval: float = 0.1) -> None:
    """Wait until a local HTTP service responds, or fail with a useful error."""
    deadline = time.time() + timeout
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=1.0)
            if response.status_code < 500:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(interval)

    raise AssertionError(f"Server did not become ready at {url}. Last error: {last_error}")


@contextmanager
def run_src_server(*args: str, port: int | None = None, timeout: float = 10.0):
    """
    Start `python -m src serve ...` and terminate it after the test.

    Example:
        with run_src_server("serve", "--log-level", "ERROR") as base_url:
            resp = requests.get(f"{base_url}/health")
    """
    actual_port = port or get_free_port()
    cmd = module_cmd(*args, "--port", str(actual_port))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    base_url = f"http://127.0.0.1:{actual_port}"

    try:
        wait_for_http(f"{base_url}/health", timeout=timeout)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5.0)


def parse_json_lines(output: str) -> list[dict]:
    """Extract JSON log lines from mixed stdout/stderr output."""
    records: list[dict] = []

    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return records


def assert_completed_replay_dir(path: str | Path) -> dict:
    """Assert replay directory contains a completed manifest and at least one chunk."""
    replay_dir = Path(path)
    manifest_path = replay_dir / "manifest.json"

    assert manifest_path.exists(), f"Missing replay manifest: {manifest_path}"

    manifest = json.loads(manifest_path.read_text())
    assert manifest.get("status") == "COMPLETED"
    assert "chunks" in manifest
    assert any(replay_dir.glob("chunk_*.json")), f"Missing replay chunks in {replay_dir}"

    return manifest
