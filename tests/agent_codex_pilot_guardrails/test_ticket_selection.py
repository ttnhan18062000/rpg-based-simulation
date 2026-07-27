"""Tests for tools/agent_codex_pilot_guardrails/ticket_selection.py::select_pilot_candidate
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 2)."""
from __future__ import annotations

import pytest
import yaml

from tools.agent_codex_pilot_guardrails.errors import (
    MissingHumanOwnerError,
    MissingRollbackPlanError,
    PilotManifestValidationError,
)
from tools.agent_codex_pilot_guardrails.pilot_manifest import PilotRequest
from tools.agent_codex_pilot_guardrails.ticket_selection import select_pilot_candidate


def _write_request(pilot_requests_dir, ticket_id, data):
    pilot_requests_dir.mkdir(parents=True, exist_ok=True)
    path = pilot_requests_dir / f"{ticket_id}.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_accepts_candidate_with_both_fields_present(tmp_path):
    ticket_id = "TCK-99999999-EXAMPLE"
    _write_request(
        tmp_path,
        ticket_id,
        {
            "ticket_id": ticket_id,
            "human_owner": "jane.doe@example.com",
            "rollback_plan_summary": "Disable the Codex adapter config toggle and restart.",
        },
    )
    request = select_pilot_candidate(ticket_id, tmp_path)
    assert request == PilotRequest(
        ticket_id=ticket_id,
        human_owner="jane.doe@example.com",
        rollback_plan_summary="Disable the Codex adapter config toggle and restart.",
    )


def test_rejects_candidate_missing_rollback_plan(tmp_path):
    ticket_id = "TCK-99999999-EXAMPLE"
    _write_request(
        tmp_path, ticket_id, {"ticket_id": ticket_id, "human_owner": "jane.doe@example.com"}
    )
    with pytest.raises(MissingRollbackPlanError):
        select_pilot_candidate(ticket_id, tmp_path)


def test_rejects_candidate_missing_human_owner(tmp_path):
    ticket_id = "TCK-99999999-EXAMPLE"
    _write_request(
        tmp_path,
        ticket_id,
        {
            "ticket_id": ticket_id,
            "rollback_plan_summary": "Disable the Codex adapter config toggle and restart.",
        },
    )
    with pytest.raises(MissingHumanOwnerError):
        select_pilot_candidate(ticket_id, tmp_path)


def test_rejects_missing_pilot_request_file_with_named_error(tmp_path):
    # Not a bare FileNotFoundError — a named, catchable PilotManifestValidationError.
    with pytest.raises(PilotManifestValidationError):
        select_pilot_candidate("TCK-NO-SUCH-TICKET", tmp_path)
