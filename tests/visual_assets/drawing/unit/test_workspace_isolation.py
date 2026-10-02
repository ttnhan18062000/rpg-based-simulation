"""Guards that the shared `workspace` fixture really isolates every module (no Aseprite needed).

Every module reads `config.NAME` at call time. If one imported a value (`from ...config import WORKSPACE`)
the patch would not reach it and a test could silently use the real ~/.cache workspace. These tests
observe each patched name from the module that consumes it.
"""

from __future__ import annotations

import subprocess

import pytest

from visual_assets.drawing import api, config
from visual_assets.drawing.backend import lua_runner, sandbox
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.workspace import jobs, locks, revisions


def test_fixture_moves_the_workspace_off_the_real_cache(workspace):
    assert config.WORKSPACE == workspace
    assert ".cache" not in workspace.parts or "pytest" in str(workspace)


def test_every_workspace_consumer_sees_the_patched_workspace(workspace):
    assert revisions.sprite_dir("x") == workspace / "sprites" / "x"
    with jobs.Job() as job:
        assert job.parent == workspace / ".jobs"
    assert not (workspace / ".jobs" / job.name).exists()
    with locks.SpriteLock("x"):
        assert (workspace / "sprites" / "x" / ".lock").exists()
    assert api.list_sprites() == []
    # a revision planted in the temp workspace must be what `list_sprites` reports (not the real cache's contents)
    d = workspace / "sprites" / "demo"
    d.mkdir(parents=True, exist_ok=True)
    (d / "r0001.aseprite").write_bytes(b"x")
    assert api.list_sprites() == [{"name": "demo", "latest": "r0001", "revisions": 1}]


def test_timeout_and_binary_are_read_from_config_at_call_time(monkeypatch, tmp_path):
    seen = {}

    def fake_run(cmd, **kw):
        seen["timeout"] = kw["timeout"]
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)
    monkeypatch.setattr(config, "JOB_TIMEOUT_S", 7.5)
    monkeypatch.setattr(config, "ASEPRITE", "/opt/not-the-real-aseprite")
    sandbox.bwrap(tmp_path, ["--script", "x.lua"])
    assert seen["timeout"] == 7.5
    assert "/opt/not-the-real-aseprite" in seen["cmd"]


def test_pinned_template_hash_is_read_from_config_at_call_time(monkeypatch):
    lua_runner.check_lua_template()  # the real pin matches the real template
    monkeypatch.setattr(config, "LUA_SHA256", "0" * 64)
    with pytest.raises(AdapterError, match="pinned hash"):
        lua_runner.check_lua_template()


def test_max_file_bytes_is_read_from_config_at_call_time(monkeypatch, tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    (job / "out.aseprite").write_bytes(b"x" * 20)
    monkeypatch.setattr(config, "MAX_FILE_BYTES", 10)
    with pytest.raises(AdapterError, match="did not produce a valid output file"):
        revisions.publish("s", job)
    assert not (config.WORKSPACE / "sprites" / "s").exists()  # nothing was created, nothing published
