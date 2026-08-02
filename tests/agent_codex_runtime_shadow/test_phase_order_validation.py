"""Tests for tools/agent_codex_runtime_shadow/phase_order.py (TCK-20260730-CODEX-RUNTIME-SHADOW,
Step 3)."""
from __future__ import annotations

import pytest

from tools.agent_codex_runtime_shadow.errors import PhaseOrderViolationError
from tools.agent_codex_runtime_shadow.matrix import load_supported_matrix
from tools.agent_codex_runtime_shadow.phase_order import validate_phase_order


def test_phase_order_violation_detected():
    matrix = load_supported_matrix()
    with pytest.raises(PhaseOrderViolationError):
        validate_phase_order(["Scope", "Plan", "Investigate"], matrix)
    with pytest.raises(PhaseOrderViolationError):
        validate_phase_order(["Investigate", "Scope"], matrix)


def test_valid_in_order_prefix_passes():
    matrix = load_supported_matrix()
    validate_phase_order(["Scope", "Investigate"], matrix)
    validate_phase_order(["Scope", "Investigate", "Plan", "Review"], matrix)
