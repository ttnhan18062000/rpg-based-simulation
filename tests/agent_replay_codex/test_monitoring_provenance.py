"""Tests for tools/agent_replay_codex/provenance_check.py (TCK-20260721-CODEX-REPLAY-PARITY,
Step 9). Passes unconditionally — no codex CLI or consent required.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent_replay_codex.errors import ContainmentViolationError
from tools.agent_replay_codex.provenance_check import assert_no_codex_provider_writes

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_real_monitoring_corpus_has_zero_codex_provider_records():
    assert_no_codex_provider_writes(_REPO_ROOT / "agent-monitoring")


def test_negative_control_raises_on_a_codex_provider_record(tmp_path):
    monitoring_dir = tmp_path / "agent-monitoring"
    monitoring_dir.mkdir()
    (monitoring_dir / "runs.jsonl").write_text(
        json.dumps({"run_id": "FAKE", "provider": "codex"}) + "\n", encoding="utf-8"
    )
    (monitoring_dir / "events.jsonl").write_text("", encoding="utf-8")
    (monitoring_dir / "tools.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(ContainmentViolationError):
        assert_no_codex_provider_writes(monitoring_dir)
