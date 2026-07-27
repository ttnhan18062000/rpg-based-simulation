"""Tests for tools/agent_codex_pilot_guardrails/ticket_selection.py::assert_no_concurrent_claim
and provider_field_coverage (TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 2)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_codex_pilot_guardrails.errors import ConcurrentProviderClaimError
from tools.agent_codex_pilot_guardrails.ticket_selection import (
    assert_no_concurrent_claim,
    provider_field_coverage,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"


def test_no_concurrent_claim_passes_for_single_provider():
    records = [{"ticket_id": "TCK-EXAMPLE", "provider": "claude", "end_ts": None}]
    assert_no_concurrent_claim("TCK-EXAMPLE", records)  # must not raise


def test_no_concurrent_claim_passes_when_other_provider_run_is_finished():
    records = [
        {"ticket_id": "TCK-EXAMPLE", "provider": "claude", "end_ts": None},
        {"ticket_id": "TCK-EXAMPLE", "provider": "codex", "end_ts": "2026-07-27T00:00:00Z"},
    ]
    assert_no_concurrent_claim("TCK-EXAMPLE", records)  # must not raise: codex run is finished


def test_concurrent_claim_by_two_providers_raises():
    records = [
        {"ticket_id": "TCK-EXAMPLE", "provider": "claude", "end_ts": None},
        {"ticket_id": "TCK-EXAMPLE", "provider": "codex", "end_ts": None},
    ]
    with pytest.raises(ConcurrentProviderClaimError):
        assert_no_concurrent_claim("TCK-EXAMPLE", records)


def test_concurrent_claim_check_ignores_unrelated_ticket_ids():
    records = [
        {"ticket_id": "TCK-EXAMPLE", "provider": "claude", "end_ts": None},
        {"ticket_id": "TCK-OTHER", "provider": "codex", "end_ts": None},
    ]
    assert_no_concurrent_claim("TCK-EXAMPLE", records)  # must not raise: different ticket_id


def test_provider_field_coverage_against_real_corpus_is_currently_zero():
    # Confirms investigation.md Risk #3's finding: no real agent-monitoring/runs.jsonl record
    # carries a provider field today (.claude/workflows/implement-ticket.js never constructs
    # one). This is the documented gap, not a bug to "fix" here — assert_no_concurrent_claim
    # above is real, tested code that is currently unexercised by real production data. A green
    # pass on the synthetic tests above must not be mistaken for proof this check works against
    # live traffic.
    assert provider_field_coverage(_REAL_AGENT_MONITORING_DIR) == 0
