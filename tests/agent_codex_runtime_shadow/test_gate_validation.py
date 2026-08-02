"""Tests for tools/agent_codex_runtime_shadow/gate_validation.py (TCK-20260730-CODEX-RUNTIME-SHADOW,
Step 4)."""
from __future__ import annotations

import pytest

from tools.agent_codex_runtime_shadow.errors import RequiredGateMissingError
from tools.agent_codex_runtime_shadow.gate_validation import validate_required_gate
from tools.agent_replay.fixture_envelope import PhaseEntry


def _entry(phase: str, output: dict) -> PhaseEntry:
    return PhaseEntry(phase=phase, agent="some-agent", input={}, output=output, transition="ok")


def test_required_gate_missing_detected():
    entry = _entry("Review", {"status": "ok"})
    with pytest.raises(RequiredGateMissingError):
        validate_required_gate(entry)


def test_required_gate_present_passes():
    entry = _entry("Review", {"verdict": "APPROVED"})
    validate_required_gate(entry)


def test_non_review_phase_is_a_no_op_even_without_verdict():
    entry = _entry("Scope", {"status": "ok"})
    validate_required_gate(entry)
