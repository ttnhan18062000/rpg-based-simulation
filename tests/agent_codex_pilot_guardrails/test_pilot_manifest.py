"""Tests for tools/agent_codex_pilot_guardrails/pilot_manifest.py
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 1)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tools.agent_codex_pilot_guardrails.errors import (
    MissingHumanOwnerError,
    MissingRollbackPlanError,
    PilotManifestValidationError,
)
from tools.agent_codex_pilot_guardrails.pilot_manifest import PilotRequest, load_pilot_request


def _write_yaml(tmp_path, data):
    path = tmp_path / "candidate.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_well_formed_request_loads_successfully(tmp_path):
    path = _write_yaml(
        tmp_path,
        {
            "ticket_id": "TCK-99999999-EXAMPLE",
            "human_owner": "jane.doe@example.com",
            "rollback_plan_summary": "Disable the Codex adapter config toggle and restart.",
        },
    )
    request = load_pilot_request(path)
    assert request == PilotRequest(
        ticket_id="TCK-99999999-EXAMPLE",
        human_owner="jane.doe@example.com",
        rollback_plan_summary="Disable the Codex adapter config toggle and restart.",
    )


def test_missing_rollback_plan_raises(tmp_path):
    path = _write_yaml(
        tmp_path,
        {"ticket_id": "TCK-99999999-EXAMPLE", "human_owner": "jane.doe@example.com"},
    )
    with pytest.raises(MissingRollbackPlanError):
        load_pilot_request(path)


def test_missing_human_owner_raises(tmp_path):
    path = _write_yaml(
        tmp_path,
        {
            "ticket_id": "TCK-99999999-EXAMPLE",
            "rollback_plan_summary": "Disable the Codex adapter config toggle and restart.",
        },
    )
    with pytest.raises(MissingHumanOwnerError):
        load_pilot_request(path)


def test_empty_whitespace_only_human_owner_raises(tmp_path):
    path = _write_yaml(
        tmp_path,
        {
            "ticket_id": "TCK-99999999-EXAMPLE",
            "human_owner": "   ",
            "rollback_plan_summary": "Disable the Codex adapter config toggle and restart.",
        },
    )
    with pytest.raises(MissingHumanOwnerError):
        load_pilot_request(path)


def test_empty_whitespace_only_rollback_plan_raises(tmp_path):
    path = _write_yaml(
        tmp_path,
        {
            "ticket_id": "TCK-99999999-EXAMPLE",
            "human_owner": "jane.doe@example.com",
            "rollback_plan_summary": "  \n  ",
        },
    )
    with pytest.raises(MissingRollbackPlanError):
        load_pilot_request(path)


def test_prose_mention_without_structured_fields_still_raises(tmp_path):
    # Free-text body mentions "owner" and "rollback" in prose without the structured YAML
    # fields — proves the check reads structured data, not keyword-greps ticket prose.
    path = _write_yaml(
        tmp_path,
        {
            "ticket_id": "TCK-99999999-EXAMPLE",
            "notes": (
                "The owner of this task has a rollback plan documented elsewhere, but this "
                "field is not the structured human_owner/rollback_plan_summary field."
            ),
        },
    )
    with pytest.raises(MissingHumanOwnerError):
        load_pilot_request(path)


def test_missing_file_raises():
    with pytest.raises(PilotManifestValidationError):
        load_pilot_request(Path("/nonexistent/pilot_requests/does-not-exist.yaml"))
