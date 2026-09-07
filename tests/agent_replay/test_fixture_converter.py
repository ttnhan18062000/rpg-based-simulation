"""Tests for tools/agent_replay/fixture_converter.py (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, AC #2)."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_converter import (  # noqa: E402
    convert_ticket_to_fixture,
    write_conversion_log,
)
from agent_replay.fixture_envelope import load_fixture  # noqa: E402

_DONE_DIR = _REPO_ROOT / "tickets" / "done"
_STORED_ARTIFACTS_ROOT = _REPO_ROOT / "stored_artifacts"
_MONITORING_ROOT = _REPO_ROOT / "agent-monitoring"

# The ticket the one hand-built example fixture is itself sourced from — confirmed to carry real
# Scope/Investigate/Plan/Review events.jsonl rows and a complete stored_artifacts/ dir.
_CONVERTIBLE_TICKET_ID = "TCK-20260721-ORCHESTRATION-CONTRACT-ADR"


def test_fixture_converter_handles_convertible_ticket(tmp_path):
    result = convert_ticket_to_fixture(
        _CONVERTIBLE_TICKET_ID,
        _DONE_DIR / f"{_CONVERTIBLE_TICKET_ID}.md",
        _STORED_ARTIFACTS_ROOT / _CONVERTIBLE_TICKET_ID,
        _MONITORING_ROOT,
        tmp_path,
    )

    assert result.converted is True, result.reason
    assert result.fixture_path is not None
    assert result.review_output_fidelity == "reconstructed_from_truncated_summary"

    fixture = load_fixture(result.fixture_path)
    assert fixture.source["ticket_id"] == _CONVERTIBLE_TICKET_ID
    assert [p.phase for p in fixture.phases] == ["Scope", "Investigate", "Plan", "Review"]


def test_fixture_converter_logs_exclusion_reason_for_unconvertible_ticket(tmp_path):
    fake_ticket_id = "TCK-20260907-DOES-NOT-EXIST-FIXTURE-CONVERTER-TEST"
    fake_ticket_path = tmp_path / f"{fake_ticket_id}.md"
    fake_ticket_path.write_text(
        "---\nlayer: ai\n---\n\n# Fake\n\n## Tier\nstandard\n", encoding="utf-8"
    )
    fake_stored_artifacts_dir = tmp_path / "stored_artifacts_missing" / fake_ticket_id

    result = convert_ticket_to_fixture(
        fake_ticket_id,
        fake_ticket_path,
        fake_stored_artifacts_dir,
        _MONITORING_ROOT,
        tmp_path / "fixtures_out",
    )

    assert result.converted is False
    assert result.fixture_path is None
    assert result.reason is not None and "stored_artifacts" in result.reason

    log_path = write_conversion_log([result], tmp_path / "conversion_log.yaml")
    log_text = log_path.read_text(encoding="utf-8")
    assert fake_ticket_id in log_text
    assert "stored_artifacts" in log_text
