"""Opt-in live transport fixture; default tests must never request it."""
from __future__ import annotations

import os
import shutil

import pytest


@pytest.fixture(scope="session")
def real_codex_live_transport():
    if shutil.which("codex") is None:
        pytest.skip("codex CLI not on PATH")
    if os.environ.get("CODEX_REALREPO_PILOT_LIVE_CONSENT") != "1":
        pytest.skip(
            "real Codex transport requires CODEX_REALREPO_PILOT_LIVE_CONSENT=1 "
            "(not set) — skipping, not failing"
        )
    pytest.skip("no real transport invocation is authorized in this ticket")
