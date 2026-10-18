"""Keep the SessionStart hook offline in every tools test: the `for:<role>` issue list (one `gh` call) is opt-in per test."""
import os
import tempfile
from pathlib import Path

import pytest

# The runtime base the shared search server would use if a test did not isolate it, captured at import, before any test
# can change the environment. `search_shared.state_dir()` refuses it under pytest
# (TCK-20261018-SEARCH-SHARED-SERVER-CWD-AND-TEST-RUNTIME-ISOLATION). Never compare listings of it: live sessions write there.
os.environ.setdefault(
    "RPG_SEARCH_TEST_REAL_RUNTIME_BASE",
    str(Path(os.environ.get("XDG_RUNTIME_DIR") or Path(tempfile.gettempdir()) / f"rpg-search-{os.getuid()}").resolve()),
)


@pytest.fixture(autouse=True)
def _no_session_start_issue_lookup(monkeypatch):
    monkeypatch.setenv("SESSION_START_ISSUES", "off")


@pytest.fixture(autouse=True)
def _search_shared_off_by_default(monkeypatch):
    """No tools test may start a detached shared search server (TCK-20261012-SEARCH-MCP-SHARED-MODEL); the few tests
    of the shared-server lifecycle opt in explicitly, inside a tmp XDG_RUNTIME_DIR."""
    monkeypatch.setenv("RPG_SEARCH_SHARED", "0")


@pytest.fixture(autouse=True)
def _tmp_runtime_dir_for_every_tools_test(tmp_path, monkeypatch):
    """Every tools test gets its own XDG_RUNTIME_DIR, so nothing that reaches `search_shared` (a lock, a state dir, a
    server) can touch the live `$XDG_RUNTIME_DIR/rpg-search`. Tests that need a runtime dir of their own still set theirs."""
    runtime = tmp_path / "_xdg_runtime"
    runtime.mkdir(mode=0o700, exist_ok=True)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
