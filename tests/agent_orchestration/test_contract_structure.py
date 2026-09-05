"""Structural tests for the agent-orchestration/ contract (TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

Covers file existence/parseability, the per-phase tier-applicability matrix, the `version` field's
documented versioning scheme, and the two anti-drift guards (no orchestrator pseudo-agent role
file, finalizer's documented inline-prompt exception).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

from agent_orchestration.loader import load_contract
from tools.agent_codex_pilot_guardrails.enabled_surface import EVIDENCED_WRITER_FUNCTIONS

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACT_DIR = _REPO_ROOT / "agent-orchestration"
_HOOK_SURFACE_POLICY_PATH = _CONTRACT_DIR / "hook-surface-policy.yaml"

_CODEX_CAPABILITY_MATRIX_EVENTS = {
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PreCompact",
    "PostCompact",
    "UserPromptSubmit",
    "SubagentStop",
    "Stop",
    "SessionStart",
    "SubagentStart",
}

_ACTIVATION_PREREQUISITE_IDS = {
    "human_approval",
    "scratch_first_verification",
    "project_trust_review",
    "hook_trust_review",
    "failure_timeout_fail_open",
    "redacted_output",
    "out_of_band_diagnostics",
    "reviewed_config_diff",
    "one_action_rollback",
}


def _load_hook_surface_policy() -> dict:
    return yaml.safe_load(_HOOK_SURFACE_POLICY_PATH.read_text(encoding="utf-8"))

_EXPECTED_TIER_MATRIX = {
    "Scope": {"standard": "full", "hotfix": "full"},
    "Investigate": {"standard": "full", "hotfix": "skipped_event"},
    "Plan": {"standard": "full", "hotfix": "skipped_event"},
    "Review": {"standard": "full", "hotfix": "skipped_event"},
    "Implement": {"standard": "full", "hotfix": "full"},
    "Document-Update": {"standard": "full", "hotfix": "full"},
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
        _CONTRACT_DIR / "hook-surface-policy.yaml",
    ]
    for path in required_files:
        assert path.exists(), f"missing required contract file: {path}"
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict), f"{path} does not parse to a YAML mapping"

    role_paths = sorted((_CONTRACT_DIR / "roles").glob("*.yaml"))
    assert len(role_paths) == 11, f"expected exactly 11 role files, found {len(role_paths)}: {role_paths}"
    for path in role_paths:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict), f"{path} does not parse to a YAML mapping"


def test_hook_surface_policy_file_exists_and_parses():
    path = _CONTRACT_DIR / "hook-surface-policy.yaml"
    assert path.exists(), f"missing required contract file: {path}"
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
        / "stored_artifacts"
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
    assert len(bundle.roles) == 11


def test_load_contract_includes_hook_surface_policy():
    bundle = load_contract(_REPO_ROOT)
    assert bundle.hook_surface_policy["hook_surface_policy_version"] == 1
    assert bundle.hook_surface_policy["providers"]
    assert bundle.hook_surface_policy["activation_candidates"]
    assert bundle.hook_surface_policy["activation_prerequisites"]


def test_load_contract_validates_continuation_policy_and_terminal_statuses():
    bundle = load_contract(_REPO_ROOT)
    assert bundle.continuation_policy.mode == "continue_until_terminal_or_hard_gate"
    assert bundle.continuation_policy.instruction.strip()
    assert bundle.continuation_policy.non_gates
    assert len(bundle.terminal_statuses) == 16  # was 15; TEST_SCOPE_COVERAGE_FAILED added 2026-08-18
    assert {entry["value"] for entry in bundle.terminal_statuses} >= {
        "DONE", "EPIC_SCOPED", "NEEDS_HUMAN_INPUT", "NEEDS_CHANGES", "BLOCKED",
        "DOD_BLOCKED", "CONFLICTS_DETECTED", "TAGS_NOT_REGISTERED", "SECURITY_BLOCKED",
        "TESTS_FAILED", "DOC_STALENESS_BLOCKED",
    }


def test_new_contract_file_wired_into_readme_and_manifest():
    contract = yaml.safe_load((_CONTRACT_DIR / "contract.yaml").read_text(encoding="utf-8"))
    governed_paths = {entry["path"]: entry for entry in contract["governs"]}
    assert "hook-surface-policy.yaml" in governed_paths
    assert governed_paths["hook-surface-policy.yaml"]["version_field"] == "hook_surface_policy_version"

    readme_text = (_CONTRACT_DIR / "README.md").read_text(encoding="utf-8")
    assert "hook-surface-policy.yaml" in readme_text
    assert "hook_surface_policy_version" in readme_text


def test_policy_represents_claude_three_enabled_events():
    policy = _load_hook_surface_policy()
    assert set(policy["providers"]["claude"]["enabled_events"]) == {
        "PreToolUse", "PostToolUse", "SubagentStop",
    }


def test_policy_represents_claude_four_available_events():
    # TCK-20260904-TEST-SCOPER-HANG-GUARD: only the four events this repo's own investigation has
    # direct evidence for (Claude Code docs + the installed binary's own validation schema) —
    # deliberately not the full ~32-event product vocabulary, per this ticket's Anti-Drift Hazards.
    policy = _load_hook_surface_policy()
    assert set(policy["providers"]["claude"]["available_events"]) == {
        "PreToolUse", "PostToolUse", "Stop", "SubagentStop",
    }


def test_policy_represents_codex_ten_available_events():
    policy = _load_hook_surface_policy()
    assert set(policy["providers"]["codex"]["available_events"]) == _CODEX_CAPABILITY_MATRIX_EVENTS
    assert len(policy["providers"]["codex"]["available_events"]) == 10


def test_policy_represents_codex_zero_enabled_events():
    policy = _load_hook_surface_policy()
    assert policy["providers"]["codex"]["enabled_events"] == []

    config_path = _REPO_ROOT / ".codex" / "config.toml"
    with open(config_path, "rb") as f:
        assert tomllib.load(f) == {}


def test_policy_normalized_vocabulary_matches_hook_events_yaml():
    policy = _load_hook_surface_policy()
    hook_events = yaml.safe_load((_CONTRACT_DIR / "hook-events.yaml").read_text(encoding="utf-8"))
    normalized_ids = {entry["id"] for entry in hook_events["hook_types"]}

    for provider in policy["providers"].values():
        assert set(provider["enabled_events"]) <= normalized_ids

    # The policy must never re-declare its own independent copy of the normalized list.
    assert "hook_types" not in policy
    assert "normalized_events" not in policy


def test_hook_events_yaml_normalized_vocabulary_includes_subagent_stop():
    hook_events = yaml.safe_load((_CONTRACT_DIR / "hook-events.yaml").read_text(encoding="utf-8"))
    assert {entry["id"] for entry in hook_events["hook_types"]} == {
        "PreToolUse", "PostToolUse", "SubagentStop",
    }


def test_only_codex_post_tool_use_is_an_activation_candidate():
    policy = _load_hook_surface_policy()
    candidates = policy["activation_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["provider"] == "codex"
    assert candidates[0]["event"] == "PostToolUse"
    assert not any(c["provider"] == "codex" and c["event"] == "PreToolUse" for c in candidates)


def test_activation_candidate_writer_subset_is_write_line_and_write_lines():
    policy = _load_hook_surface_policy()
    candidate = policy["activation_candidates"][0]
    assert set(candidate["writer_functions"]) == EVIDENCED_WRITER_FUNCTIONS


def test_activation_prerequisites_cover_all_nine_named_items():
    policy = _load_hook_surface_policy()
    ids = {entry["id"] for entry in policy["activation_prerequisites"]}
    assert ids == _ACTIVATION_PREREQUISITE_IDS
    for entry in policy["activation_prerequisites"]:
        assert entry["description"].strip()


def test_activation_prerequisites_do_not_imply_authorization():
    policy = _load_hook_surface_policy()
    forbidden_keys = {"approved", "granted", "authorized"}
    for entry in policy["activation_prerequisites"] + policy["activation_candidates"]:
        for key in forbidden_keys:
            assert entry.get(key) is not True, (
                f"entry {entry} carries authorization-implying key {key!r} with a true value"
            )
