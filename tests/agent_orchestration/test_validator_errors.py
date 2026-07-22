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
