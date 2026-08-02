"""Tests for tools/agent_codex_runtime_shadow/required_artifacts.py
(TCK-20260730-CODEX-RUNTIME-SHADOW, Step 5)."""
from __future__ import annotations

import pytest

from tools.agent_codex_runtime_shadow.errors import RequiredArtifactMissingError
from tools.agent_codex_runtime_shadow.required_artifacts import check_required_artifacts


@pytest.mark.parametrize("phase", ["Investigate", "Plan"])
def test_required_artifact_missing_detected(tmp_path, phase):
    ticket_id = "FAKE-TICKET"
    (tmp_path / ticket_id).mkdir()

    with pytest.raises(RequiredArtifactMissingError):
        check_required_artifacts(phase, ticket_id, tmp_path)


def test_required_artifact_present_passes(tmp_path):
    ticket_id = "FAKE-TICKET"
    ticket_dir = tmp_path / ticket_id
    ticket_dir.mkdir()
    (ticket_dir / "investigation.md").write_text("x", encoding="utf-8")
    (ticket_dir / "test_plan.md").write_text("x", encoding="utf-8")
    (ticket_dir / "plan.md").write_text("x", encoding="utf-8")

    assert check_required_artifacts("Investigate", ticket_id, tmp_path) == [
        "investigation.md",
        "test_plan.md",
    ]
    assert check_required_artifacts("Plan", ticket_id, tmp_path) == ["plan.md"]


def test_phase_with_no_required_artifact_is_a_no_op(tmp_path):
    ticket_id = "FAKE-TICKET"
    assert check_required_artifacts("Scope", ticket_id, tmp_path) == []
    assert check_required_artifacts("Review", ticket_id, tmp_path) == []
