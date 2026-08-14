"""Containment integration tests for tools/agent_codex_runtime_shadow/
(TCK-20260730-CODEX-RUNTIME-SHADOW, Step 10).

Reuses tools.agent_replay_codex.{containment,provenance_check,codex_config_guard}'s real,
already-tested primitives unmodified (imported, not reimplemented) around a real
run_shadow_comparison() call against a synthetic, disposable git repo — never the real project
repo's tickets/ or agent-monitoring/.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.agent_replay_codex.codex_config_guard import (
    assert_committed_config_hook_free,
    assert_config_bytes_unchanged,
    snapshot_config_bytes,
)
from tools.agent_replay_codex.containment import assert_no_diff, capture_snapshot
from tools.agent_replay_codex.errors import ContainmentViolationError
from tools.agent_replay_codex.provenance_check import assert_no_codex_provider_writes
from tools.agent_codex_runtime_shadow.shadow_comparison import run_shadow_comparison

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TICKET_ID = "FAKE-CODEX-RUNTIME-SHADOW-TICKET"

_PLAN_MD = "# Plan\n\nNo unresolved questions here.\n"

_FIXTURE_YAML_TEMPLATE = """\
version: 1
source:
  ticket_id: {ticket_id}
  ticket_path: tickets/inprogress/{ticket_id}.md
  events_run_id: {ticket_id}
  stored_artifacts_dir: {stored_artifacts_dir}
  tier: standard
phases:
  - phase: Scope
    agent: ticket-scoper
    input:
      tags: []
      conflicts: []
    output:
      status: ok
    transition: ok
  - phase: Investigate
    agent: investigator
    input: {{}}
    output:
      status: ok
    transition: ok
  - phase: Plan
    agent: planner
    input:
      plan_path: {plan_path}
    output:
      status: ok
    transition: ok
  - phase: Review
    agent: architecture-reviewer
    input: {{}}
    output:
      verdict: APPROVED
    transition: APPROVED
"""


def _init_synthetic_repo(tmp_path):
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    (tmp_path / "agent-monitoring").mkdir(parents=True)
    (tmp_path / ".codex").mkdir(parents=True)

    (tmp_path / "tickets" / "inprogress" / "FAKE.md").write_text("line one\n", encoding="utf-8")
    for filename in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
        (tmp_path / "agent-monitoring" / filename).write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    (tmp_path / ".codex" / "config.toml").write_text("# hook-free synthetic config\n", encoding="utf-8")

    for root_name in ("stored_artifacts", "staging_artifacts"):
        ticket_dir = tmp_path / root_name / _TICKET_ID
        ticket_dir.mkdir(parents=True)
        (ticket_dir / "investigation.md").write_text("x", encoding="utf-8")
        (ticket_dir / "test_plan.md").write_text("x", encoding="utf-8")
        (ticket_dir / "plan.md").write_text(_PLAN_MD, encoding="utf-8")

    plan_path = tmp_path / "stored_artifacts" / _TICKET_ID / "plan.md"
    stored_artifacts_dir = tmp_path / "stored_artifacts" / _TICKET_ID
    fixture_path = tmp_path / "fixture.yaml"
    fixture_path.write_text(
        _FIXTURE_YAML_TEMPLATE.format(
            ticket_id=_TICKET_ID,
            plan_path=str(plan_path),
            stored_artifacts_dir=f"{stored_artifacts_dir}/",
        ),
        encoding="utf-8",
    )

    (tmp_path / "intentional-divergences.md").write_text("# no entries\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", "add", "-A"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    return fixture_path


def test_shadow_run_produces_zero_diff_in_tickets_and_monitoring(tmp_path):
    fixture_path = _init_synthetic_repo(tmp_path)

    pre = capture_snapshot(tmp_path)
    result = run_shadow_comparison(
        fixture_path,
        tmp_path / "staging_artifacts",
        tmp_path / "intentional-divergences.md",
    )
    post = capture_snapshot(tmp_path)

    assert_no_diff(pre, post)
    assert result.phase_order_match is True
    assert result.terminal_status_match is True
    assert result.gate_policy_match is True
    assert result.artifact_requirements_match is True


def test_shadow_run_writes_no_codex_provider_record():
    assert_no_codex_provider_writes(_REPO_ROOT / "agent-monitoring")


def test_negative_control_detects_a_synthetic_codex_provider_record(tmp_path):
    monitoring_dir = tmp_path / "agent-monitoring"
    monitoring_dir.mkdir()
    (monitoring_dir / "runs.jsonl").write_text(
        json.dumps({"run_id": "FAKE", "provider": "codex"}) + "\n", encoding="utf-8"
    )
    (monitoring_dir / "events.jsonl").write_text("", encoding="utf-8")
    (monitoring_dir / "tools.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(ContainmentViolationError):
        assert_no_codex_provider_writes(monitoring_dir)


def test_committed_codex_config_remains_hook_free_and_byte_identical(tmp_path):
    fixture_path = _init_synthetic_repo(tmp_path)

    pre_config = snapshot_config_bytes(_REPO_ROOT)
    run_shadow_comparison(
        fixture_path,
        tmp_path / "staging_artifacts",
        tmp_path / "intentional-divergences.md",
    )
    post_config = snapshot_config_bytes(_REPO_ROOT)

    assert_config_bytes_unchanged(pre_config, post_config)
    assert_committed_config_hook_free(_REPO_ROOT)
