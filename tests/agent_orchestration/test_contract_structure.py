"""Structural tests for the agent-orchestration/ contract (TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

Covers file existence/parseability, the per-phase tier-applicability matrix, the `version` field's
documented versioning scheme, and the two anti-drift guards (no orchestrator pseudo-agent role
file, finalizer's documented inline-prompt exception).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from agent_orchestration.loader import load_contract

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACT_DIR = _REPO_ROOT / "agent-orchestration"

_EXPECTED_TIER_MATRIX = {
    "Scope": {"standard": "full", "hotfix": "full"},
    "Investigate": {"standard": "full", "hotfix": "skipped_event"},
    "Plan": {"standard": "full", "hotfix": "skipped_event"},
    "Review": {"standard": "full", "hotfix": "skipped_event"},
    "Implement": {"standard": "full", "hotfix": "full"},
    "Architecture-Verify": {"standard": "full", "hotfix": "skipped_event"},
    "Test": {"standard": "full", "hotfix": "full"},
    "Parity": {"standard": "conditional", "hotfix": "conditional"},
    "Security-Review": {"standard": "conditional", "hotfix": "conditional"},
    "Verify": {"standard": "full", "hotfix": "full"},
    "Finalize": {"standard": "full", "hotfix": "full"},
}


def test_agent_orchestration_dir_has_required_files():
    required_files = [
        _CONTRACT_DIR / "contract.yaml",
        _CONTRACT_DIR / "workflows" / "implement-ticket.yaml",
        _CONTRACT_DIR / "skills.yaml",
        _CONTRACT_DIR / "monitoring-schema.yaml",
        _CONTRACT_DIR / "hook-events.yaml",
    ]
    for path in required_files:
        assert path.exists(), f"missing required contract file: {path}"
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict), f"{path} does not parse to a YAML mapping"

    role_paths = sorted((_CONTRACT_DIR / "roles").glob("*.yaml"))
    assert len(role_paths) == 10, f"expected exactly 10 role files, found {len(role_paths)}: {role_paths}"
    for path in role_paths:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict), f"{path} does not parse to a YAML mapping"


def test_workflow_covers_both_tiers():
    workflow = yaml.safe_load((_CONTRACT_DIR / "workflows" / "implement-ticket.yaml").read_text(encoding="utf-8"))
    phases_by_name = {phase["name"]: phase for phase in workflow["phases"]}

    assert set(phases_by_name) == set(_EXPECTED_TIER_MATRIX)
    for name, expected_tiers in _EXPECTED_TIER_MATRIX.items():
        actual_tiers = phases_by_name[name]["tiers"]
        assert actual_tiers == expected_tiers, f"phase {name!r}: expected {expected_tiers}, got {actual_tiers}"

    # Security-Review's conditional_absent behavior must stay distinct from Investigate/Plan/
    # Review/Architecture-Verify's skipped_event — both are "conditional" tier values above, but
    # their if_false outcomes must differ.
    assert phases_by_name["Security-Review"]["if_false"] == "conditional_absent"
    assert phases_by_name["Parity"]["if_false"] == "skipped_event"
    for name in ("Investigate", "Plan", "Review", "Architecture-Verify"):
        assert phases_by_name[name]["tiers"]["hotfix"] == "skipped_event"


def test_contract_yaml_has_versioning_field_and_documented_scheme():
    contract = yaml.safe_load((_CONTRACT_DIR / "contract.yaml").read_text(encoding="utf-8"))
    assert isinstance(contract["version"], int)
    assert contract["version"] == 1

    plan_path = (
        _REPO_ROOT
        / "staging_artifacts"
        / "TCK-20260721-ORCHESTRATION-CONTRACT-CORE"
        / "plan.md"
    )
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "integer generation number" in plan_text


def test_roles_never_include_orchestrator_pseudo_agent():
    roles_dir = _CONTRACT_DIR / "roles"
    for path in roles_dir.glob("*.yaml"):
        assert "implement-ticket-orchestrator" not in path.stem.lower()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        role_id = str(data.get("role_id", "")).lower()
        assert "implement-ticket-orchestrator" not in role_id


def test_finalizer_role_entry_documents_inline_prompt_exception():
    finalizer_path = _CONTRACT_DIR / "roles" / "finalizer.yaml"
    data = yaml.safe_load(finalizer_path.read_text(encoding="utf-8"))
    assert data["has_agent_file"] is False
    assert data.get("inline_prompt_exception")
    assert len(data["inline_prompt_exception"].strip()) > 0


def test_load_contract_succeeds_against_the_real_contract():
    bundle = load_contract(_REPO_ROOT)
    assert bundle.contract["version"] == 1
    assert len(bundle.roles) == 10
