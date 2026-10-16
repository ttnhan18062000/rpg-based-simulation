"""A bwrap that cannot build its namespace (AppArmor unprivileged-userns restriction, #555) gives one clear AdapterError, and the probe
that tells "installed" from "works here" is cached. The subprocess is faked: no bwrap and no Aseprite needed; runs in CI."""

from __future__ import annotations

import subprocess

import pytest

from visual_assets.drawing.backend import sandbox
from visual_assets.drawing.errors import AdapterError

USERNS_STDERR = b"bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted\n"


class FakeProc:
    def __init__(self, returncode: int, stderr: bytes):
        self.returncode, self._stderr = returncode, stderr

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def communicate(self, timeout=None):
        return b"", self._stderr


@pytest.fixture(autouse=True)
def _fresh_probe():
    sandbox.bwrap_problem.cache_clear()
    yield
    sandbox.bwrap_problem.cache_clear()


def _fake_popen(monkeypatch, returncode: int, stderr: bytes):
    monkeypatch.setattr(sandbox.subprocess, "Popen", lambda *a, **k: FakeProc(returncode, stderr))


def test_userns_signature_raises_the_clear_error(monkeypatch, tmp_path):
    _fake_popen(monkeypatch, 1, USERNS_STDERR)
    with pytest.raises(AdapterError) as err:
        sandbox.bwrap(tmp_path, ["--version"])
    for needle in ("AppArmor", "bwrap-userns-restrict", "#555"):
        assert needle in str(err.value)


def test_another_failure_is_returned_unchanged(monkeypatch, tmp_path):
    _fake_popen(monkeypatch, 1, b"bwrap: execvp aseprite: No such file or directory\n")
    done = sandbox.bwrap(tmp_path, ["--version"])
    assert done.returncode == 1 and b"No such file" in done.stderr


def test_the_signature_on_a_successful_run_is_not_an_error(monkeypatch, tmp_path):
    _fake_popen(monkeypatch, 0, USERNS_STDERR)
    assert sandbox.bwrap(tmp_path, ["--version"]).returncode == 0


def _fake_run(monkeypatch, returncode: int, stderr: bytes):
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode, b"", stderr)

    monkeypatch.setattr(sandbox.subprocess, "run", run)
    return calls


def test_probe_passes_and_is_cached(monkeypatch):
    calls = _fake_run(monkeypatch, 0, b"")
    assert sandbox.bwrap_problem() is None
    assert sandbox.bwrap_problem() is None
    assert len(calls) == 1
    assert calls[0][:2] == ["bwrap", "--unshare-all"]


def test_probe_names_the_userns_cause(monkeypatch):
    _fake_run(monkeypatch, 1, USERNS_STDERR)
    assert sandbox.bwrap_problem() == sandbox.USERNS_MESSAGE


def test_probe_reports_another_failure_and_a_missing_binary(monkeypatch):
    _fake_run(monkeypatch, 3, b"bwrap: something else\n")
    assert "exit 3" in sandbox.bwrap_problem()
    sandbox.bwrap_problem.cache_clear()

    def missing(cmd, **kwargs):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(sandbox.subprocess, "run", missing)
    assert sandbox.bwrap_problem() == "bwrap is not installed"
