"""Shared by every `tests/visual_assets` package (drawing and store).

`needs_aseprite` (marker) skips a test unless the Aseprite binary and bwrap are present, as CI sees it. It lives
here, not in a sub-package conftest, so it applies and is registered however the tests are selected.
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
