"""Keep the SessionStart hook offline in every tools test: the `for:<role>` issue list (one `gh` call) is opt-in per test."""
import pytest


@pytest.fixture(autouse=True)
def _no_session_start_issue_lookup(monkeypatch):
    monkeypatch.setenv("SESSION_START_ISSUES", "off")


@pytest.fixture(autouse=True)
def _search_shared_off_by_default(monkeypatch):
    """No tools test may start a detached shared search server (TCK-20261012-SEARCH-MCP-SHARED-MODEL); the few tests
    of the shared-server lifecycle opt in explicitly, inside a tmp XDG_RUNTIME_DIR."""
    monkeypatch.setenv("RPG_SEARCH_SHARED", "0")
