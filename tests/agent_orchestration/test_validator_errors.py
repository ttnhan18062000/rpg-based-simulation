"""Tests for tools/agent_orchestration/loader.py's ContractValidationError (TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

Table-driven over malformed-contract cases, mirroring tools/agent_replay/fixture_envelope.py's
FixtureValidationError pattern: each case asserts both the named exception type and a message
substring naming the exact file path and field.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from agent_orchestration.errors import ContractValidationError
from agent_orchestration.loader import load_contract

_REPO_ROOT = Path(__file__).parent.parent.parent
_REAL_CONTRACT_DIR = _REPO_ROOT / "agent-orchestration"


def _copy_contract_to(tmp_path: Path) -> Path:
    dest = tmp_path / "agent-orchestration"
    shutil.copytree(_REAL_CONTRACT_DIR, dest)
    return dest


def test_contract_yaml_missing_version_raises_named_error(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    contract_path = contract_dir / "contract.yaml"
    data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    del data["version"]
    contract_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(tmp_path)
    assert str(contract_path) in str(excinfo.value)
    assert "version" in str(excinfo.value)


@pytest.mark.parametrize("bad_policy, expected", [
    ({"instruction": "x", "non_gates": ["ordinary progress"]}, "mode"),
    ({"mode": "unknown", "instruction": "x", "non_gates": ["ordinary progress"]}, "mode"),
    ({"mode": "continue_until_terminal_or_hard_gate", "instruction": "", "non_gates": ["ordinary progress"]}, "instruction"),
    ({"mode": "continue_until_terminal_or_hard_gate", "instruction": "x", "non_gates": ["needs human input"]}, "reserved terminal"),
])
def test_continuation_policy_malformed_or_terminal_non_gate_is_rejected(tmp_path, bad_policy, expected):
    contract_dir = _copy_contract_to(tmp_path)
    workflow_path = contract_dir / "workflows" / "implement-ticket.yaml"
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    data["continuation_policy"] = bad_policy
    workflow_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(ContractValidationError, match=expected):
        load_contract(tmp_path)


def test_role_yaml_missing_required_field_raises_named_error(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    role_path = contract_dir / "roles" / "ticket-scoper.yaml"
    data = yaml.safe_load(role_path.read_text(encoding="utf-8"))
    del data["role_id"]
    role_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(tmp_path)
    assert str(role_path) in str(excinfo.value)
    assert "role_id" in str(excinfo.value)


def test_non_mapping_yaml_root_raises_named_error(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    contract_path = contract_dir / "contract.yaml"
    contract_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(tmp_path)
    assert str(contract_path) in str(excinfo.value)
    assert "not a mapping" in str(excinfo.value)


def _load_hook_surface_policy(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    policy_path = contract_dir / "hook-surface-policy.yaml"
    return policy_path, yaml.safe_load(policy_path.read_text(encoding="utf-8"))


def _write_and_expect_error(tmp_path, policy_path, data, expected_substrings):
    policy_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(tmp_path)
    for substring in expected_substrings:
        assert substring in str(excinfo.value), (
            f"expected {substring!r} in error message, got: {excinfo.value}"
        )


def test_hook_surface_policy_missing_version_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    del data["hook_surface_policy_version"]
    _write_and_expect_error(tmp_path, policy_path, data, [str(policy_path), "hook_surface_policy_version"])


def test_hook_surface_policy_missing_providers_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    del data["providers"]
    _write_and_expect_error(tmp_path, policy_path, data, [str(policy_path), "providers"])


def test_hook_surface_policy_provider_missing_enabled_events_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    del data["providers"]["claude"]["enabled_events"]
    _write_and_expect_error(tmp_path, policy_path, data, [str(policy_path), "enabled_events"])


def test_hook_surface_policy_enabled_event_not_normalized_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["providers"]["claude"]["enabled_events"] = ["Stop"]
    _write_and_expect_error(tmp_path, policy_path, data, [str(policy_path), "not normalized"])


def test_hook_surface_policy_enabled_event_not_in_available_events_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["providers"]["codex"]["available_events"] = ["PostToolUse"]
    data["providers"]["codex"]["enabled_events"] = ["PreToolUse"]
    _write_and_expect_error(
        tmp_path, policy_path, data, [str(policy_path), "providers.codex.available_events"]
    )


def test_hook_surface_policy_activation_candidate_event_not_available_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["activation_candidates"][0]["event"] = "NotARealEvent"
    _write_and_expect_error(
        tmp_path, policy_path, data, [str(policy_path), "activation_candidates[0]", "available_events"]
    )


def test_hook_surface_policy_prerequisite_missing_id_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    del data["activation_prerequisites"][0]["id"]
    _write_and_expect_error(tmp_path, policy_path, data, [str(policy_path), "activation_prerequisites[0]", "id"])


def test_hook_surface_policy_prerequisite_missing_description_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    del data["activation_prerequisites"][0]["description"]
    _write_and_expect_error(
        tmp_path, policy_path, data, [str(policy_path), "activation_prerequisites[0]", "description"]
    )


def test_hook_surface_policy_prerequisite_duplicate_id_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["activation_prerequisites"][1]["id"] = data["activation_prerequisites"][0]["id"]
    _write_and_expect_error(tmp_path, policy_path, data, [str(policy_path), "duplicate id"])


def test_hook_surface_policy_prerequisite_with_approved_true_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["activation_prerequisites"][0]["approved"] = True
    _write_and_expect_error(
        tmp_path, policy_path, data, [str(policy_path), "authorization-implying key 'approved'"]
    )


def test_hook_surface_policy_candidate_with_granted_true_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["activation_candidates"][0]["granted"] = True
    _write_and_expect_error(
        tmp_path, policy_path, data, [str(policy_path), "authorization-implying key 'granted'"]
    )


def test_hook_surface_policy_prerequisite_with_authorized_true_raises_named_error(tmp_path):
    policy_path, data = _load_hook_surface_policy(tmp_path)
    data["activation_prerequisites"][0]["authorized"] = True
    _write_and_expect_error(
        tmp_path, policy_path, data, [str(policy_path), "authorization-implying key 'authorized'"]
    )
