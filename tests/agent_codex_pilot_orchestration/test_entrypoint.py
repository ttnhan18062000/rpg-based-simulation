from __future__ import annotations

import json
import subprocess
import sys
import hashlib
import ast
from pathlib import Path

import pytest

from tools.agent_codex_pilot_entrypoint.preparation import prepare_context, prepare_policy
from tools.agent_codex_realrepo_pilot_harness.proofs import capture_policy_baseline, tree_digest


def test_prepare_policy_binds_fixed_candidate_and_excludes_its_own_policy(tmp_path):
    root = tmp_path
    request = root / "pilot_requests" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml"
    target = root / "tickets" / "done" / "TCK-20260721-MONITORING-WRITER-UNIFICATION.md"
    request.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    candidate = root / "tickets" / "inprogress" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("candidate\n")
    request.write_text("ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE\nhuman_owner: tnhan\nrollback_plan_summary: restore\n")
    target.write_text("---\nstatus: active\nphase: open\n---\n\n## Status\nOPEN\n")

    result = prepare_policy(root, "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-deadbeef")
    data = json.loads(result.policy_path.read_text())

    assert data["candidate_ticket_id"] == "TCK-20260801-MONITORING-WRITER-STATUS-STALE"
    assert ".codex/config.toml" in data["allowed_paths"]
    assert "tickets/inprogress/TCK-20260801-MONITORING-WRITER-STATUS-STALE.md" in data["allowed_paths"]
    assert "tickets/done/TCK-20260801-MONITORING-WRITER-STATUS-STALE.md" in data["allowed_paths"]
    assert "tickets/working_log.csv" in data["allowed_paths"]
    assert "docs/REGISTRY.yaml" in data["allowed_paths"]
    assert data["baseline_sha256"] == result.baseline_sha256
    assert data["bounded_tool_suffix"]["max_tool_calls"] == 200
    assert data["bounded_tool_suffix"]["execution_id"] == "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-deadbeef"


def test_prepare_policy_refuses_when_fixed_candidate_is_missing(tmp_path):
    request = tmp_path / "pilot_requests" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml"
    request.parent.mkdir(parents=True)
    request.write_text("ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE\nhuman_owner: tnhan\nrollback_plan_summary: restore\n")

    with pytest.raises(ValueError, match="fixed candidate is missing"):
        prepare_policy(tmp_path, "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-deadbeef")


def test_prepare_context_uses_only_fixed_candidate_paths(tmp_path):
    root = tmp_path
    request = root / "pilot_requests" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml"
    candidate = root / "tickets" / "inprogress" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.md"
    request.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    request.write_text("ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE\nhuman_owner: tnhan\nrollback_plan_summary: restore\n")
    candidate.write_text("candidate\n")

    context = prepare_context(root, "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-deadbeef")

    assert context.ticket_id == "TCK-20260801-MONITORING-WRITER-STATUS-STALE"
    assert context.candidate_path == "tickets/inprogress/TCK-20260801-MONITORING-WRITER-STATUS-STALE.md"
    assert context.enabled_hook_events == frozenset({"PostToolUse"})


def test_policy_is_deterministic_for_unchanged_injected_root(tmp_path):
    root = tmp_path
    request = root / "pilot_requests" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml"
    candidate = root / "tickets" / "inprogress" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.md"
    request.parent.mkdir(parents=True); candidate.parent.mkdir(parents=True)
    request.write_text("ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE\nhuman_owner: tnhan\nrollback_plan_summary: restore\n")
    candidate.write_text("candidate\n")
    first = prepare_policy(root, "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-a")
    second = prepare_policy(root, "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-b")
    assert first.baseline_sha256 == second.baseline_sha256


def test_prepared_policy_detects_later_baseline_drift(tmp_path):
    root = tmp_path
    request = root / "pilot_requests" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml"
    candidate = root / "tickets" / "inprogress" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.md"
    request.parent.mkdir(parents=True); candidate.parent.mkdir(parents=True)
    request.write_text("ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE\nhuman_owner: tnhan\nrollback_plan_summary: restore\n")
    candidate.write_text("before\n")
    prepared = prepare_policy(root, "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-a")
    candidate.write_text("after\n")
    assert prepared.baseline_sha256 != tree_digest(capture_policy_baseline(root, prepared.policy_path))


def test_entrypoint_package_has_no_subprocess_or_live_invocation_import():
    package = Path(__file__).parents[2] / "tools" / "agent_codex_pilot_entrypoint"
    forbidden = {"subprocess", "invoke_live_transport", "execute_controlled_pilot"}
    source = "\n".join(path.read_text() for path in package.glob("*.py"))
    assert all(token not in source for token in forbidden)


def test_prepare_only_cli_emits_context_evidence_without_invocation(tmp_path):
    request = tmp_path / "pilot_requests" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml"
    candidate = tmp_path / "tickets" / "inprogress" / "TCK-20260801-MONITORING-WRITER-STATUS-STALE.md"
    request.parent.mkdir(parents=True); candidate.parent.mkdir(parents=True)
    request.write_text("ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE\nhuman_owner: tnhan\nrollback_plan_summary: restore\n")
    candidate.write_text("candidate\n")
    result = subprocess.run([sys.executable, "-m", "tools.agent_codex_pilot_entrypoint", "--repo-root", str(tmp_path), "--execution-id", "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-a"], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["mode"] == "prepare-only"
