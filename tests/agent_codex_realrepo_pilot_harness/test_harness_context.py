from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from tools.agent_codex_realrepo_pilot_harness.authority import issue_live_authority
from tools.agent_codex_realrepo_pilot_harness.boundary import invoke_after_authority
from tools.agent_codex_realrepo_pilot_harness.preflight import (
    PilotHarnessContext,
    ordinary_preflight,
)
from tools.agent_codex_realrepo_pilot_harness.proofs import (
    assert_post_run_proof,
    capture_policy_baseline,
    capture_tree,
    tree_digest,
)
from tools.agent_codex_posttool_adapter.errors import IdentityValidationError


TICKET = "TCK-20260801-MONITORING-WRITER-STATUS-STALE"
EXECUTION = "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1722500000000-deadbeef"


def _write_shape(root: Path) -> PilotHarnessContext:
    request = root / "pilot_requests" / f"{TICKET}.yaml"
    candidate = root / "tickets" / "todos" / f"{TICKET}.md"
    target = root / "tickets" / "done" / "TCK-20260721-MONITORING-WRITER-UNIFICATION.md"
    for path in (request, candidate, target):
        path.parent.mkdir(parents=True, exist_ok=True)
    request.write_text(yaml.safe_dump({"ticket_id": TICKET, "human_owner": "tnhan", "rollback_plan_summary": "restore scratch bytes"}))
    candidate.write_text("candidate\n")
    target.write_text("---\nstatus: active\nphase: open\n---\n# old\n\n## Status\nOPEN\n")
    monitoring = root / "agent-monitoring"
    monitoring.mkdir()
    for name in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
        (monitoring / name).write_text('{"historical":true}\n')
    baseline = tree_digest(capture_tree(root))
    policy = {
        "version": 1,
        "candidate_ticket_id": TICKET,
        "request_sha256": hashlib.sha256(request.read_bytes()).hexdigest(),
        "baseline_sha256": baseline,
        "target_path": "tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md",
        "target_transitions": {
            "status": ["active", "historical"],
            "phase": ["open", "done"],
            "body_status": ["OPEN", "DONE"],
        },
        "allowed_paths": [
            "tickets/todos/TCK-20260801-MONITORING-WRITER-STATUS-STALE.md",
            "tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md",
            "working_log.csv",
            "docs/REGISTRY.yaml",
            "staging_artifacts/TCK-20260801-MONITORING-WRITER-STATUS-STALE/proof.json",
        ],
        "monitoring_suffixes": {
            "runs.jsonl": [{"ticket_id": TICKET, "execution_id": EXECUTION, "provider": "codex", "run_id": "pilot-run"}],
            "events.jsonl": [{"ticket_id": TICKET, "execution_id": EXECUTION, "provider": "codex", "run_id": "pilot-run", "seq": 1}],
            "tools.jsonl": [{"ticket_id": TICKET, "execution_id": EXECUTION, "provider": "codex", "run_id": "pilot-run", "seq": 1}],
        },
    }
    policy_path = root / "pilot_evidence" / "policy.json"
    policy_path.parent.mkdir()
    policy_path.write_text(json.dumps(policy))
    return PilotHarnessContext(
        repo_root=root,
        ticket_id=TICKET,
        execution_id=EXECUTION,
        candidate_path="tickets/todos/TCK-20260801-MONITORING-WRITER-STATUS-STALE.md",
        request_path=f"pilot_requests/{TICKET}.yaml",
        policy_path="pilot_evidence/policy.json",
        enabled_hook_events=frozenset({"PostToolUse"}),
        enabled_writer_names=frozenset({"write_line", "write_lines"}),
        concurrent_runs=(),
    )


def test_preflight_captures_validated_immutable_context_before_claim_or_invoker(tmp_path):
    context = _write_shape(tmp_path / "scratch")

    result = ordinary_preflight(context)

    assert result.policy.candidate_ticket_id == TICKET
    assert result.baseline_digest == result.policy.baseline_sha256
    assert result.request.ticket_id == TICKET


def test_policy_baseline_excludes_only_the_policy_bytes(tmp_path):
    root = tmp_path / "scratch"
    policy = root / "pilot_evidence" / "policy.json"
    ordinary = root / "tickets" / "candidate.md"
    policy.parent.mkdir(parents=True)
    ordinary.parent.mkdir(parents=True)
    ordinary.write_text("candidate\n")
    policy.write_text('{"first": true}')

    first = capture_policy_baseline(root, policy)
    policy.write_text('{"second": true}')

    assert capture_policy_baseline(root, policy) == first
    assert "pilot_evidence/policy.json" not in first
    assert first["tickets/candidate.md"] == b"candidate\n"


def test_boundary_accepts_only_a_captured_preflight_before_constructing_invoker(tmp_path):
    context = _write_shape(tmp_path / "scratch")
    admitted = ordinary_preflight(context)
    authority = issue_live_authority({
        "CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1",
        "CODEX_REALREPO_PILOT_LIVE_CONSENT": "1",
    })
    calls: list[Path] = []

    assert invoke_after_authority(authority, admitted, lambda root: calls.append(root)) is None
    assert calls == [context.repo_root.resolve()]


@pytest.mark.parametrize("mutator", ["missing_request", "bad_owner", "bad_surface", "bad_baseline"])
def test_preflight_refuses_invalid_evidence_before_a_claim_write(tmp_path, mutator):
    context = _write_shape(tmp_path / "scratch")
    root = context.repo_root
    if mutator == "missing_request":
        (root / context.request_path).unlink()
    elif mutator == "bad_owner":
        (root / context.request_path).write_text("ticket_id: " + TICKET + "\nhuman_owner: ''\nrollback_plan_summary: rollback\n")
    elif mutator == "bad_surface":
        context = context.__class__(**{**context.__dict__, "enabled_hook_events": frozenset({"PreToolUse"})})
    else:
        (root / context.candidate_path).write_text("drift\n")

    with pytest.raises(Exception):
        ordinary_preflight(context)
    assert not (root / "claims").exists()


def test_preflight_refuses_a_traversal_shaped_ticket_id_before_derived_path_io(tmp_path):
    context = _write_shape(tmp_path / "scratch")
    traversal = replace(context, ticket_id="../TCK-20260801-MONITORING-WRITER-STATUS-STALE")

    with pytest.raises(IdentityValidationError, match="ticket_id"):
        ordinary_preflight(traversal)
    assert not (context.repo_root / "claims").exists()


def test_preflight_refuses_symlinked_scratch_tree_before_any_invoker(tmp_path):
    context = _write_shape(tmp_path / "scratch")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n")
    (context.repo_root / "escape-link").symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        ordinary_preflight(context)


def test_post_run_proof_requires_exact_historical_fields_and_declared_suffixes(tmp_path):
    context = _write_shape(tmp_path / "scratch")
    admitted = ordinary_preflight(context)
    before = admitted.baseline_tree
    target = context.repo_root / "tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md"
    target.write_text("---\nstatus: historical\nphase: done\n---\n# old\n\n## Status\nDONE\n")
    for name, rows in admitted.policy.monitoring_suffixes.items():
        with (context.repo_root / "agent-monitoring" / name).open("a") as stream:
            for row in rows:
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")

    assert_post_run_proof(admitted, capture_tree(context.repo_root))

    target.write_text("---\nstatus: historical\nphase: done\nextra: forbidden\n---\n# old\n\n## Status\nDONE\n")
    with pytest.raises(ValueError, match="exactly"):
        assert_post_run_proof(admitted, capture_tree(context.repo_root))


def test_post_run_proof_rejects_an_extra_monitoring_row(tmp_path):
    context = _write_shape(tmp_path / "scratch")
    admitted = ordinary_preflight(context)
    target = context.repo_root / "tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md"
    target.write_text("---\nstatus: historical\nphase: done\n---\n# old\n\n## Status\nDONE\n")
    for name, rows in admitted.policy.monitoring_suffixes.items():
        with (context.repo_root / "agent-monitoring" / name).open("a") as stream:
            for row in rows:
                stream.write(json.dumps(row) + "\n")
    (context.repo_root / "agent-monitoring" / "runs.jsonl").open("a").write('{"unexpected":true}\n')
    with pytest.raises(ValueError, match="suffix"):
        assert_post_run_proof(admitted, capture_tree(context.repo_root))
