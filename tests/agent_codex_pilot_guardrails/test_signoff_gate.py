"""Tests for tools/agent_codex_pilot_guardrails/signoff_gate.py
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 6)."""
from __future__ import annotations

import pytest
import yaml

from tools.agent_codex_pilot_guardrails.errors import PilotSignoffNotGrantedError
from tools.agent_codex_pilot_guardrails.signoff_gate import (
    PILOT_SIGNOFF_ENV_VAR,
    require_pilot_signoff,
)
from tools.agent_codex_pilot_guardrails.ticket_selection import select_pilot_candidate


def test_require_pilot_signoff_raises_when_env_var_unset():
    with pytest.raises(PilotSignoffNotGrantedError):
        require_pilot_signoff(env={})


def test_require_pilot_signoff_raises_on_truthy_but_not_exact_value():
    with pytest.raises(PilotSignoffNotGrantedError):
        require_pilot_signoff(env={PILOT_SIGNOFF_ENV_VAR: "true"})


def test_require_pilot_signoff_raises_on_zero_value():
    with pytest.raises(PilotSignoffNotGrantedError):
        require_pilot_signoff(env={PILOT_SIGNOFF_ENV_VAR: "0"})


def test_require_pilot_signoff_passes_on_exact_string_one():
    require_pilot_signoff(env={PILOT_SIGNOFF_ENV_VAR: "1"})  # must not raise


def test_successful_ticket_selection_does_not_itself_satisfy_signoff(tmp_path):
    ticket_id = "TCK-99999999-EXAMPLE"
    request_path = tmp_path / f"{ticket_id}.yaml"
    request_path.write_text(
        yaml.safe_dump(
            {
                "ticket_id": ticket_id,
                "human_owner": "jane.doe@example.com",
                "rollback_plan_summary": "Disable the Codex adapter config toggle and restart.",
            }
        ),
        encoding="utf-8",
    )

    # Selection succeeds independently of sign-off — the two gates are separate calls, and
    # selection's success is never itself read as sign-off.
    select_pilot_candidate(ticket_id, tmp_path)

    with pytest.raises(PilotSignoffNotGrantedError):
        require_pilot_signoff(env={})
