"""Tests for tools/agent_replay_codex/entry_criterion.py (TCK-20260721-CODEX-REPLAY-PARITY, Step 1).

MONITORING-WRITER-UNIFICATION is already confirmed DONE (investigation.md), so the positive case
is expected to pass immediately — this guard exists to make future removal of writer.py a hard,
loud failure here rather than a silent one.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_replay_codex.entry_criterion import assert_monitoring_writer_landed
from tools.agent_replay_codex.errors import EntryCriterionNotMetError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_assert_monitoring_writer_landed_passes_against_real_repo():
    assert_monitoring_writer_landed(_REPO_ROOT / "tools")


def test_assert_monitoring_writer_landed_raises_when_writer_missing(tmp_path):
    (tmp_path / "agent-monitoring").mkdir()
    with pytest.raises(EntryCriterionNotMetError):
        assert_monitoring_writer_landed(tmp_path)
