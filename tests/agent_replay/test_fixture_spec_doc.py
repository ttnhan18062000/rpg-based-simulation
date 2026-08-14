"""Static content checks for docs/ai/replay_fixture_spec.md (TCK-20260721-CODEX-REPLAY-PROOF).

Mirrors tests/tools/test_monitoring_bypass_fix.py's established pattern of `Path.read_text()` +
substring assertions against a doc/source file, applied here to the new fixture spec doc rather
than a `.claude/workflows/*.js` file.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SPEC_DOC_PATH = _REPO_ROOT / "docs" / "ai" / "replay_fixture_spec.md"

_FORBIDDEN_SCRIPTS = (
    "post_tool_hook.py",
    "pre_tool_hook.py",
    "record_run.py",
    "record_events.py",
)


def _read_spec_doc() -> str:
    return _SPEC_DOC_PATH.read_text(encoding="utf-8")


def test_spec_doc_exists():
    assert _SPEC_DOC_PATH.exists()


def test_spec_doc_cites_adr_contract_representation():
    text = _read_spec_doc()
    assert "docs/architecture/agent_orchestration_contract.md" in text
    assert "Contract Representation and Format" in text


def test_spec_doc_states_unconditional_hook_prohibition():
    text = _read_spec_doc()
    for script in _FORBIDDEN_SCRIPTS:
        assert script in text, f"spec doc does not name forbidden script {script!r}"
    assert "unconditional" in text.lower()


def test_spec_doc_cites_truncation_caps():
    text = _read_spec_doc()
    assert "200" in text
    assert "120" in text
    assert "docs/agent-monitoring/schema.md" in text


def test_spec_doc_states_fail_closed_law():
    text = _read_spec_doc()
    assert "fail-closed" in text.lower()
    assert "FixtureValidationError" in text
