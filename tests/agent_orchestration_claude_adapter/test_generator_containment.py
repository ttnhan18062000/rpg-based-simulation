"""Generator write-guard and output-shape tests (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER).

Covers test_plan.md item 8 (`test_generator_output_matches_representation_schema_shape`), run
against `tmp_path` per Review-phase Fix B — this test only checks output shape, so it must not
rewrite the committed `agent-orchestration/rendered/claude-adapter.yaml` as a side effect. The
zero-git-diff-under-`.claude/` proof lives entirely in test_claude_containment.py (Step 8), the one
test that legitimately runs the generator against the real repo root.

Also covers the generator's own write-guard (refuses writes outside
`agent-orchestration/rendered/` without the explicit opt-in flag), mirroring
tests/agent_orchestration/test_validator_no_network_calls.py's equivalent guard tests for the
predecessor package's generator.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tools.agent_orchestration_claude_adapter.generator import (
    ClaudeAdapterWriteGuardError,
    build_claude_adapter_representation,
    render_claude_adapter,
)

_REPO_ROOT = Path(__file__).parent.parent.parent


def test_generator_output_matches_representation_schema_shape(tmp_path):
    output_path = render_claude_adapter(_REPO_ROOT, tmp_path, allow_outside_contract=True)

    assert output_path.exists()
    data = yaml.safe_load(output_path.read_text(encoding="utf-8"))

    assert data["claude_adapter_schema_version"] == 1
    assert data["source_workflow_id"] == "implement-ticket"

    assert isinstance(data["phase_order"], list) and len(data["phase_order"]) == 12
    assert all(isinstance(p, str) for p in data["phase_order"])

    assert isinstance(data["terminal_statuses"], list) and len(data["terminal_statuses"]) == 15
    for entry in data["terminal_statuses"]:
        assert {"value", "kind", "phases"} <= entry.keys()


def test_build_claude_adapter_representation_derives_purely_from_load_paths():
    representation = build_claude_adapter_representation(_REPO_ROOT)

    # phase_order must match the phases[].name list from load_contract() exactly, in order.
    assert representation["phase_order"] == [p["name"] for p in representation["phases"]]

    # Security-Review's conditional_absent shape (tiers/condition/if_false) must pass through
    # unmodified from workflows/implement-ticket.yaml, not collapsed into a generic "skipped".
    security_review = next(p for p in representation["phases"] if p["name"] == "Security-Review")
    assert security_review["if_false"] == "conditional_absent"

    investigate = next(p for p in representation["phases"] if p["name"] == "Investigate")
    assert investigate["tiers"]["hotfix"] == "skipped_event"


def test_render_claude_adapter_refuses_writes_outside_rendered_dir_without_flag(tmp_path):
    outside_dir = tmp_path / "outside_rendered_dir"
    with pytest.raises(ClaudeAdapterWriteGuardError):
        render_claude_adapter(_REPO_ROOT, outside_dir)
    assert not outside_dir.exists()


def test_render_claude_adapter_allows_writes_outside_with_explicit_flag(tmp_path):
    outside_dir = tmp_path / "outside_rendered_dir"
    output_path = render_claude_adapter(_REPO_ROOT, outside_dir, allow_outside_contract=True)
    assert output_path.exists()


def test_render_claude_adapter_never_targets_dot_claude_directory():
    dot_claude_target = _REPO_ROOT / ".claude" / "rendered_scratch"
    with pytest.raises(ClaudeAdapterWriteGuardError):
        render_claude_adapter(_REPO_ROOT, dot_claude_target)
    assert not dot_claude_target.exists()
