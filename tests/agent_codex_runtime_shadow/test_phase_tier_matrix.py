"""Tests for tools/agent_codex_runtime_shadow/matrix.py (TCK-20260730-CODEX-RUNTIME-SHADOW,
Step 2)."""
from __future__ import annotations

import pytest

from tools.agent_codex_runtime_shadow.errors import (
    ContractVersionMismatchError,
    UnsupportedPhaseError,
    UnsupportedTierError,
)
from tools.agent_codex_runtime_shadow.matrix import (
    SupportedMatrix,
    load_supported_matrix,
    validate_contract_version,
    validate_phase_names,
    validate_tier,
)


def test_phase_tier_matrix_reads_real_implement_ticket_yaml():
    matrix = load_supported_matrix()
    assert matrix.tier == "standard"
    assert matrix.phases == ["Scope", "Investigate", "Plan", "Review"]
    assert matrix.workflow_version == 2


def test_rejects_hotfix_tier():
    matrix = load_supported_matrix()
    with pytest.raises(UnsupportedTierError):
        validate_tier("hotfix", matrix)


@pytest.mark.parametrize(
    "phase_name",
    ["Implement", "Architecture-Verify", "Test", "Parity", "Security-Review", "Verify", "Finalize"],
)
def test_rejects_unsupported_phase(phase_name):
    matrix = load_supported_matrix()
    with pytest.raises(UnsupportedPhaseError):
        validate_phase_names(["Scope", phase_name], matrix)


def test_accepts_the_one_supported_slice():
    matrix = load_supported_matrix()
    validate_tier("standard", matrix)
    validate_phase_names(["Scope", "Investigate", "Plan", "Review"], matrix)


def test_contract_version_mismatch_rejected():
    # validate_contract_version() checks this package's own _VERIFIED_AGAINST_WORKFLOW_VERSION
    # against the real implement-ticket.yaml's workflow_version -- not a per-fixture value
    # (TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION). Simulate a real
    # implement-ticket.yaml drift by constructing a matrix with a mismatched workflow_version,
    # rather than passing a declared_version argument (the function no longer takes one).
    real_matrix = load_supported_matrix()
    drifted_matrix = SupportedMatrix(
        tier=real_matrix.tier, phases=real_matrix.phases, workflow_version=9999
    )
    with pytest.raises(ContractVersionMismatchError):
        validate_contract_version(drifted_matrix)


def test_contract_version_accepted_when_matrix_matches_verified_version():
    matrix = load_supported_matrix()
    validate_contract_version(matrix)  # must not raise
