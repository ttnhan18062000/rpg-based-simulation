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


def test_provider_field_coverage_against_real_corpus_is_populated():
    # TCK-20260730-CLAUDE-EXECUTION-IDENTITY closed the earlier real-corpus coverage gap.
    # Keep this as a lightweight integration assertion without depending on an exact run count:
    # later legitimate identity-bearing executions may append additional records.
    assert provider_field_coverage(_REAL_AGENT_MONITORING_DIR) >= 1


def test_provider_field_coverage_resolves_sharded_real_repo_runs_source(tmp_path):
    """TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION: provider_field_coverage must stream
    every agent-monitoring/data/<week>/runs.jsonl shard, not a single hardcoded top-level
    runs.jsonl path."""
    monitoring_dir = tmp_path / "agent-monitoring"
    data_dir = monitoring_dir / "data"
    for week in ("2026-W01", "2026-W02", "unknown-week"):
        (data_dir / week).mkdir(parents=True)
    (data_dir / "2026-W01" / "runs.jsonl").write_text(
        '{"provider": "claude"}\n{"provider": null}\n', encoding="utf-8"
    )
    (data_dir / "2026-W02" / "runs.jsonl").write_text('{"provider": "claude"}\n', encoding="utf-8")
    (data_dir / "unknown-week" / "runs.jsonl").write_text("{}\n", encoding="utf-8")

    assert provider_field_coverage(monitoring_dir) == 2
