"""Tests for tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 4)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_codex_pilot_guardrails.baseline_manifest_gate import (
    assert_pilot_baseline_preserved,
    capture_pilot_baseline,
)
from tools.agent_codex_pilot_guardrails.errors import PilotManifestDriftError

_FILES = ("runs.jsonl", "events.jsonl", "tools.jsonl")


def _build_synthetic_monitoring_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "agent-monitoring"
    directory.mkdir()
    for filename in _FILES:
        (directory / filename).write_text('{"a": 1}\n{"a": 2}\n{"a": 3}\n', encoding="utf-8")
    return directory


def test_append_only_change_between_pre_and_post_does_not_raise(tmp_path):
    directory = _build_synthetic_monitoring_dir(tmp_path)
    pre = capture_pilot_baseline(directory)

    for filename in _FILES:
        with open(directory / filename, "a", encoding="utf-8") as f:
            f.write('{"a": 4}\n')

    post = capture_pilot_baseline(directory)
    assert_pilot_baseline_preserved(pre, post)  # must not raise


def test_mutated_pre_existing_line_raises_pilot_manifest_drift_error(tmp_path):
    # Negative control: without this, a fail-closed gate that never exercises the failure path
    # would prove nothing (test_plan.md's Anti-Drift Test Guards).
    directory = _build_synthetic_monitoring_dir(tmp_path)
    pre = capture_pilot_baseline(directory)

    target = directory / "runs.jsonl"
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    lines[0] = '{"a": 999}\n'
    target.write_text("".join(lines), encoding="utf-8")

    post = capture_pilot_baseline(directory)
    with pytest.raises(PilotManifestDriftError):
        assert_pilot_baseline_preserved(pre, post)
