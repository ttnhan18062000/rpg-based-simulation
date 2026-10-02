"""Shared fixtures for the drawing-tool tests.

`workspace` (autouse) points `config.WORKSPACE` at a temp dir for every test. Every module under
`visual_assets/drawing` reads it as `config.WORKSPACE` at call time, so one patch reaches all of them;
`tests/visual_assets/test_boundaries.py` and `unit/test_workspace_isolation.py` guard that rule.

`needs_aseprite` (marker) skips a test unless the Aseprite binary and bwrap are present, as CI sees it.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from visual_assets.drawing import config as drawing_config


def aseprite_available() -> bool:
    return Path(drawing_config.ASEPRITE).exists() and shutil.which("bwrap") is not None


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_aseprite: requires the Aseprite binary and bwrap (skipped otherwise)")


def pytest_collection_modifyitems(items):
    if aseprite_available():
        return
    skip = pytest.mark.skip(reason="requires aseprite and bwrap")
    for item in items:
        if "needs_aseprite" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(drawing_config, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


@pytest.fixture
def ws(workspace):
    """Alias: the high-level tests name the workspace `ws`."""
    return workspace
