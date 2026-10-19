"""Shared by every `tests/visual_assets` package (drawing and store).

`needs_aseprite` (marker) skips a test unless the Aseprite binary and bwrap are present, as CI sees it. It lives
here, not in a sub-package conftest, so it applies and is registered however the tests are selected.

Strict mode (`VISUAL_ASSETS_REQUIRE_ASEPRITE=1`, see `strict_aseprite.py`, ADR D10) turns that skip into a failure
and also fails when the binary is not the pinned version, so a local run that quietly skipped cannot pass.
"""

from __future__ import annotations

import shutil
from functools import cache
from pathlib import Path

import pytest

from tests.visual_assets import strict_aseprite
from visual_assets.drawing import config as drawing_config
from visual_assets.drawing.backend import sandbox


def aseprite_available() -> bool:
    """Binary and bwrap are present and bwrap can actually build a sandbox here (cached probe, see `sandbox.bwrap_problem`)."""
    return Path(drawing_config.ASEPRITE).exists() and shutil.which("bwrap") is not None and sandbox.bwrap_problem() is None


def skip_reason() -> str:
    """Starts with `requires aseprite and bwrap`, which `tools/ci_aseprite_skip_line.SKIP_MARKER` counts."""
    if Path(drawing_config.ASEPRITE).exists() and shutil.which("bwrap") is not None and (problem := sandbox.bwrap_problem()):
        return f"requires aseprite and bwrap (bwrap cannot run on this host: {problem})"
    return "requires aseprite and bwrap (real Aseprite runs locally only, ADR D10)"


@cache
def _strict_problem(binary: str, pinned: str) -> str | None:
    present = Path(binary).exists()
    return strict_aseprite.strict_problem(
        binary_present=present,
        bwrap_present=shutil.which("bwrap") is not None,
        version_output=strict_aseprite.read_version(binary) if present else "",
        pinned=pinned,
        bwrap_problem=sandbox.bwrap_problem() if present and shutil.which("bwrap") is not None else None,
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_aseprite: requires the Aseprite binary and bwrap (skipped otherwise)")


def pytest_collection_modifyitems(items):
    if strict_aseprite.strict_requested() or aseprite_available():
        return
    skip = pytest.mark.skip(reason=skip_reason())
    for item in items:
        if "needs_aseprite" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _strict_aseprite(request):
    if "needs_aseprite" not in request.keywords or not strict_aseprite.strict_requested():
        return
    problem = _strict_problem(str(drawing_config.ASEPRITE), drawing_config.ASEPRITE_VERSION)
    if problem:
        pytest.fail(problem, pytrace=False)
