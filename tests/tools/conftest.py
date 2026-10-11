"""Keep the SessionStart hook offline in every tools test: the `for:<role>` issue list (one `gh` call) is opt-in per test."""
import pytest


@pytest.fixture(autouse=True)
def _no_session_start_issue_lookup(monkeypatch):
    monkeypatch.setenv("SESSION_START_ISSUES", "off")
