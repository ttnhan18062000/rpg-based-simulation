"""Shared fixtures for the drawing-tool tests.

`workspace` (autouse) points `config.WORKSPACE` at a temp dir for every test. Every module under
`visual_assets/drawing` reads it as `config.WORKSPACE` at call time, so one patch reaches all of them;
`tests/visual_assets/test_boundaries.py` and `unit/test_workspace_isolation.py` guard that rule.

(The `needs_aseprite` marker and its skip hook live in `tests/visual_assets/conftest.py`.)
"""

from __future__ import annotations

import pytest

from visual_assets.drawing import config as drawing_config


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(drawing_config, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


@pytest.fixture
def ws(workspace):
    """Alias: the high-level tests name the workspace `ws`."""
    return workspace
