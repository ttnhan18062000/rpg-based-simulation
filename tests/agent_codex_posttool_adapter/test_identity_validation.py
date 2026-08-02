"""Tests for tools/agent_codex_posttool_adapter/identity.py (Step 3)."""
from __future__ import annotations

import pytest

from tools.agent_codex_posttool_adapter.errors import IdentityValidationError
from tools.agent_codex_posttool_adapter.identity import validate_identity

_TICKET_ID = "TCK-20260730-CODEX-POSTTOOL-ADAPTER"
_VALID_EXECUTION_ID = f"codex-{_TICKET_ID}-1700000000000-deadbeef"


def test_execution_id_shape_validated_against_monitoring_schema():
    validate_identity("codex", _VALID_EXECUTION_ID, _TICKET_ID)

    with pytest.raises(IdentityValidationError):
        validate_identity("codex", "codex-TCK-99999999-OTHER-1700000000000-deadbeef", _TICKET_ID)

    with pytest.raises(IdentityValidationError):
        validate_identity("codex", f"claude-{_TICKET_ID}-1700000000000-deadbeef", _TICKET_ID)

    with pytest.raises(IdentityValidationError):
        validate_identity("codex", f"codex-{_TICKET_ID}-1700000000000-nothex1", _TICKET_ID)

    with pytest.raises(IdentityValidationError):
        validate_identity("codex", _VALID_EXECUTION_ID, "not-a-ticket-id")


def test_provider_field_must_be_exactly_codex_literal():
    with pytest.raises(IdentityValidationError):
        validate_identity("claude", _VALID_EXECUTION_ID, _TICKET_ID)
    with pytest.raises(IdentityValidationError):
        validate_identity("Codex", _VALID_EXECUTION_ID, _TICKET_ID)
    with pytest.raises(IdentityValidationError):
        validate_identity("", _VALID_EXECUTION_ID, _TICKET_ID)
