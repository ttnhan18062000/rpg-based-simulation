import ast
from multiprocessing import Barrier, Process, Queue
from pathlib import Path
import json

import pytest

from tools.agent_codex_realrepo_pilot_harness.preflight import ordinary_preflight, load_contained_policy
from tools.agent_codex_realrepo_pilot_harness.errors import RootAdmissionRefused
from tools.agent_codex_realrepo_pilot_harness.authority import issue_live_authority
from tools.agent_codex_realrepo_pilot_harness.policy import ExpectedWritePolicy, load_policy_file
from tools.agent_codex_realrepo_pilot_harness.boundary import invoke_after_authority
from tools.agent_codex_realrepo_pilot_harness.proofs import (
    assert_expected_changes,
    capture_tree,
)
from tools.agent_codex_realrepo_pilot_harness.rollback import ScratchConfigAdapter


def _race_executor_claim(root: str, barrier: Barrier, results: Queue) -> None:
    from tools.agent_codex_pilot_executor.claims import ClaimRefusedError, acquire_claim

    barrier.wait()
    try:
        acquire_claim(
            Path(root),
            "TCK-20260801-MONITORING-WRITER-STATUS-STALE",
            "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1722500000000-deadbeef",
        )
        results.put("acquired")
    except ClaimRefusedError:
        results.put("refused")


def test_ordinary_preflight_refuses_project_root_before_loader(monkeypatch):
    project_root = Path(__file__).parents[2]
    called = False

    def loader(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("tools.agent_codex_realrepo_pilot_harness.preflight.load_policy_file", loader)

    with pytest.raises(RootAdmissionRefused):
        ordinary_preflight(project_root, "TCK-20260801-MONITORING-WRITER-STATUS-STALE")

    assert called is False


def test_authority_requires_both_exact_consent_values():
    with pytest.raises(PermissionError):
        issue_live_authority({"CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1"})
    with pytest.raises(PermissionError):
        issue_live_authority({"CODEX_REALREPO_PILOT_LIVE_CONSENT": "1"})
    assert issue_live_authority({
        "CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1",
        "CODEX_REALREPO_PILOT_LIVE_CONSENT": "1",
    }) is not None


def test_policy_is_bound_to_its_captured_bytes(tmp_path):
    policy_path = tmp_path / "pilot-policy.json"
    policy_path.write_text('{"version":1,"candidate_ticket_id":"TCK-001","request_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","baseline_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","target_path":"tickets/done/x.md","target_transitions":{"status":["active","historical"],"phase":["open","done"],"body_status":["OPEN","DONE"]},"allowed_paths":["tickets/done/x.md"],"monitoring_suffixes":{"runs.jsonl":[],"events.jsonl":[],"tools.jsonl":[]}}')
    policy = load_policy_file(policy_path, "TCK-001")
    policy_path.write_text(policy_path.read_text() + " ")

    assert policy.verify_unchanged() is False
    assert isinstance(policy, ExpectedWritePolicy)


def test_invoker_is_not_constructed_until_dual_authority_exists():
    constructed = []

    def invoker(*_args):
        constructed.append(True)

    with pytest.raises(PermissionError):
        invoke_after_authority(None, None, invoker)
    assert constructed == []


def test_fake_invoker_runs_only_with_authority_and_never_needs_a_process():
    calls = []
    authority = issue_live_authority({
        "CODEX_LIVE_PILOT_HUMAN_SIGNOFF": "1",
        "CODEX_REALREPO_PILOT_LIVE_CONSENT": "1",
    })

    with pytest.raises(PermissionError, match="preflight"):
        invoke_after_authority(authority, None, lambda root: calls.append(root))
    assert calls == []


def test_proof_accepts_declared_lifecycle_write_and_rejects_unrelated_ticket(tmp_path):
    root = tmp_path / "scratch"
    target = root / "tickets" / "done" / "historical.md"
    candidate = root / "tickets" / "inprogress" / "candidate.md"
    target.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    target.write_text("before")
    candidate.write_text("open")
    before = capture_tree(root)
    target.write_text("after")
    candidate.write_text("done")
    assert_expected_changes(
        before, capture_tree(root), {"tickets/done/historical.md", "tickets/inprogress/candidate.md"}
    )
    (root / "tickets" / "done" / "other.md").write_text("unexpected")
    with pytest.raises(ValueError, match="not allowlisted"):
        assert_expected_changes(
            before, capture_tree(root), {"tickets/done/historical.md", "tickets/inprogress/candidate.md"}
        )


def test_rollback_restores_exact_scratch_config_and_requires_owner_identity(tmp_path):
    root = tmp_path / "scratch"
    config = root / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_bytes(b"# hook-free\n")
    adapter = ScratchConfigAdapter.capture(root, ".codex/config.toml", "owner-a")
    adapter.enable(b"# temporary hook\n")
    with pytest.raises(PermissionError):
        adapter.restore("owner-b")
    adapter.restore("owner-a")
    assert config.read_bytes() == b"# hook-free\n"
    assert adapter.is_hook_free() is True


@pytest.mark.parametrize("target", ["/absolute.md", "../escaped.md", "tickets/../escaped.md"])
def test_policy_refuses_unsafe_target_paths_before_a_harness_can_use_them(tmp_path, target):
    policy_path = tmp_path / "pilot-policy.json"
    policy_path.write_text(json.dumps({
        "version": 1,
        "candidate_ticket_id": "TCK-001",
        "target_path": target,
        "target_transitions": {
            "status": ["active", "historical"],
            "phase": ["open", "done"],
            "body_status": ["OPEN", "DONE"],
        },
        "allowed_paths": ["tickets/done/x.md"],
        "monitoring_suffixes": {"runs.jsonl": [], "events.jsonl": [], "tools.jsonl": []},
    }))
    with pytest.raises(ValueError, match="safe relative"):
        load_policy_file(policy_path, "TCK-001")


def test_policy_refuses_non_string_transition_entries(tmp_path):
    policy_path = tmp_path / "pilot-policy.json"
    policy_path.write_text(
        '{"version":1,"candidate_ticket_id":"TCK-001","target_path":"tickets/done/x.md","transitions":[3]}'
    )
    with pytest.raises(ValueError, match="transitions"):
        load_policy_file(policy_path, "TCK-001")


def test_monitoring_prefix_proof_rejects_rewrite_and_allows_append():
    from tools.agent_codex_realrepo_pilot_harness.proofs import assert_monitoring_prefixes

    before = {"runs.jsonl": [b'{"old":1}\n']}
    assert_monitoring_prefixes(before, {"runs.jsonl": [b'{"old":1}\n', b'{"new":2}\n']})
    with pytest.raises(ValueError, match="prefix"):
        assert_monitoring_prefixes(before, {"runs.jsonl": [b'{"old":2}\n']})


def test_contained_policy_loader_refuses_escape_before_opening_policy(tmp_path, monkeypatch):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("not a policy")
    opened = False

    def loader(*_args):
        nonlocal opened
        opened = True

    monkeypatch.setattr("tools.agent_codex_realrepo_pilot_harness.preflight.load_policy_file", loader)
    with pytest.raises(RootAdmissionRefused, match="escapes"):
        load_contained_policy(scratch, outside, "TCK-001")
    assert opened is False


def test_rollback_adapter_refuses_the_real_project_config_before_write():
    project_config = Path(__file__).parents[2] / ".codex" / "config.toml"
    with pytest.raises(RootAdmissionRefused):
        ScratchConfigAdapter.capture(project_config.parent.parent, ".codex/config.toml", "owner-a")


def test_rollback_adapter_refuses_paths_outside_its_scratch_root(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_bytes(b"outside\n")

    with pytest.raises(RootAdmissionRefused, match="safe relative|escapes"):
        ScratchConfigAdapter.capture(root, "../outside.toml", "owner-a")


def test_rollback_adapter_preserves_non_config_scratch_paths(tmp_path):
    root = tmp_path / "scratch"
    config = root / ".codex" / "config.toml"
    unrelated = root / "tickets" / "candidate.md"
    config.parent.mkdir(parents=True)
    unrelated.parent.mkdir(parents=True)
    config.write_bytes(b"# disabled\n")
    unrelated.write_bytes(b"candidate evidence\n")

    adapter = ScratchConfigAdapter.capture(root, ".codex/config.toml", "owner-a")
    adapter.enable(b"# temporarily enabled\n")
    adapter.restore("owner-a")

    assert unrelated.read_bytes() == b"candidate evidence\n"


def test_harness_boundary_modules_do_not_import_or_construct_process_transport():
    root = Path(__file__).parents[2]
    forbidden_calls = {"Popen", "run", "call", "system", "exec", "execv", "spawn"}
    for relative in (
        "tools/agent_codex_realrepo_pilot_harness/boundary.py",
        "tools/agent_codex_realrepo_pilot_harness/rollback.py",
    ):
        tree = ast.parse((root / relative).read_text())
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        calls = {
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))
        }
        assert "subprocess" not in imported
        assert calls.isdisjoint(forbidden_calls)


def test_harness_reuses_executor_claim_lock_for_same_ticket_race(tmp_path):
    barrier, results = Barrier(2), Queue()
    workers = [Process(target=_race_executor_claim, args=(str(tmp_path), barrier, results)) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=10)
        assert worker.exitcode == 0
    assert sorted(results.get(timeout=2) for _ in workers) == ["acquired", "refused"]
