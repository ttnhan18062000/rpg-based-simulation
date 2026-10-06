"""TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION: outcome and adjudication rows, derived outcomes, the CLI,
and the native-versus-backstop false_pass. Fixtures live in tmp_path; nothing reaches the real data root."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "agent-monitoring"))

import gate_ledger  # noqa: E402
import gate_verdicts  # noqa: E402
from gate_checks import post_native_run_check  # noqa: E402

WEEK = "2026-W41"


def _shard(root: Path) -> Path:
    path = root / WEEK / "t.gate_verdicts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _put(root: Path, *rows: dict) -> None:
    with _shard(root).open("a") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _verdict(vid, ts, blocking, ticket="TCK-1", gate="cli:g", inputs=None, mode="hand") -> dict:
    return {"ts": ts, "gate_verdict_id": vid, "execution_mode": mode, "ticket_id": ticket, "gate_id": gate,
            "gate_type": "static_check", "verdict": "FAIL" if blocking else "PASS", "blocking": blocking,
            "inputs_ref": inputs if inputs is not None else {"cmd_sha": "a"}}


def _view(root: Path) -> dict:
    return {v["gate_verdict_id"]: v for v in gate_ledger.resolved_view(gate_ledger.load_rows(root))}


class TestDerivation:
    def test_block_then_pass_is_fixed_and_rerun(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True), _verdict("b", "2026-10-06T02:00:00Z", False))
        view = _view(tmp_path)
        assert (view["a"]["outcome"], view["a"]["outcome_source"], view["a"]["followup_verdict_id"]) == ("fixed_and_rerun", "derived", "b")
        assert view["b"]["outcome"] is None

    def test_block_then_same_inputs_block_is_rerun_no_change(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True), _verdict("b", "2026-10-06T02:00:00Z", True))
        assert _view(tmp_path)["a"]["outcome"] == "rerun_no_change"

    def test_block_then_block_with_different_inputs_has_no_derived_outcome(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True), _verdict("b", "2026-10-06T02:00:00Z", True, inputs={"cmd_sha": "z"}))
        assert _view(tmp_path)["a"]["outcome"] is None

    def test_lone_block_is_unresolved_and_other_tickets_or_gates_do_not_count(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True),
             _verdict("b", "2026-10-06T02:00:00Z", False, ticket="TCK-2"), _verdict("c", "2026-10-06T03:00:00Z", False, gate="cli:other"))
        view = gate_ledger.resolved_view(gate_ledger.load_rows(tmp_path))
        assert [v["gate_verdict_id"] for v in gate_ledger.unresolved(view)] == ["a"]

    def test_explicit_outcome_beats_derived(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True), _verdict("b", "2026-10-06T02:00:00Z", False))
        gate_ledger.record_outcome("a", "overridden", note="owner waived", data_root=tmp_path)
        entry = _view(tmp_path)["a"]
        assert (entry["outcome"], entry["outcome_source"]) == ("overridden", "explicit")


class TestRecording:
    def test_outcome_and_adjudication_rows_are_valid_and_append_only(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True))
        out = gate_ledger.record_outcome("a", "stopped", data_root=tmp_path)
        adj = gate_ledger.record_adjudication("a", "true_block", "owner", "it was right", data_root=tmp_path)
        assert gate_verdicts.validate_record(out) == [] and gate_verdicts.validate_record(adj) == []
        assert len(gate_ledger.load_rows(tmp_path)) == 3

    def test_unknown_verdict_id_is_rejected(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True))
        with pytest.raises(KeyError):
            gate_ledger.record_outcome("nope", "stopped", data_root=tmp_path)
        assert len(gate_ledger.load_rows(tmp_path)) == 1

    def test_invalid_values_are_refused(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True))
        with pytest.raises(ValueError):
            gate_ledger.record_outcome("a", "shrugged", data_root=tmp_path)
        with pytest.raises(ValueError):
            gate_ledger.record_adjudication("a", "true_block", "owner", "", data_root=tmp_path)

    def test_later_adjudication_supersedes_and_both_rows_are_kept(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True))
        gate_ledger.record_adjudication("a", "false_block", "reviewer", "first look", data_root=tmp_path)
        gate_ledger.record_adjudication("a", "true_block", "owner", "second look", data_root=tmp_path)
        entry = _view(tmp_path)["a"]
        assert (entry["adjudication"], entry["adjudicated_by"]) == ("true_block", "owner")
        assert sum(r.get("row_kind") == "adjudication" for r in gate_ledger.load_rows(tmp_path)) == 2


class TestCli:
    def test_cli_outcome_adjudicate_list_and_unknown_id(self, tmp_path, capsys):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True))
        root = ["--data-root", str(tmp_path)]
        assert gate_ledger.main(root + ["list", "--unresolved"]) == 0
        assert "a  TCK-1" in capsys.readouterr().out
        assert gate_ledger.main(root + ["outcome", "--gate-verdict-id", "a", "--outcome", "overridden"]) == 0
        assert gate_ledger.main(root + ["adjudicate", "--gate-verdict-id", "a", "--adjudication", "false_block",
                                        "--by", "owner", "--reason", "gate was wrong"]) == 0
        capsys.readouterr()
        gate_ledger.main(root + ["list", "--unresolved"])
        assert capsys.readouterr().out == ""
        assert gate_ledger.main(root + ["outcome", "--gate-verdict-id", "zzz", "--outcome", "stopped"]) == 2
        assert "unknown gate_verdict_id" in capsys.readouterr().err


class TestBackstop:
    @pytest.fixture(autouse=True)
    def _recording_on(self, monkeypatch):
        monkeypatch.delenv(gate_verdicts.ENV_NO_RECORD, raising=False)

    def _native_pass(self, root):
        _put(root, _verdict("n1", "2026-10-06T01:00:00Z", False, ticket="TCK-5", gate="finalize_selfcheck", mode="workflow"),
             _verdict("n2", "2026-10-06T01:00:01Z", False, ticket="TCK-5", gate="doc_staleness", mode="workflow"))

    def test_native_pass_contradicted_by_backstop_gets_exactly_one_false_pass(self, tmp_path):
        self._native_pass(tmp_path)
        first = gate_ledger.backstop_adjudicate("TCK-5", "done_checker_static", data_root=tmp_path, target=_shard(tmp_path))
        again = gate_ledger.backstop_adjudicate("TCK-5", "done_checker_static", data_root=tmp_path, target=_shard(tmp_path))
        assert [r["gate_verdict_id"] for r in first] == ["n1"] and again == []
        view = _view(tmp_path)
        assert (view["n1"]["adjudication"], view["n1"]["adjudicated_by"]) == ("false_pass", "orchestrator-backstop")
        assert view["n2"]["adjudication"] is None

    def test_hand_rows_and_other_tickets_are_not_adjudicated(self, tmp_path):
        _put(tmp_path, _verdict("h", "2026-10-06T01:00:00Z", False, ticket="TCK-5", gate="finalize_selfcheck", mode="hand"),
             _verdict("o", "2026-10-06T01:00:00Z", False, ticket="TCK-6", gate="finalize_selfcheck", mode="workflow"))
        assert gate_ledger.backstop_adjudicate("TCK-5", "done_checker_static", data_root=tmp_path, target=_shard(tmp_path)) == []

    def test_recording_guard_disables_it(self, tmp_path, monkeypatch):
        self._native_pass(tmp_path)
        monkeypatch.setenv(gate_verdicts.ENV_NO_RECORD, "1")
        assert gate_ledger.backstop_adjudicate("TCK-5", "done_checker_static", data_root=tmp_path) == []

    def test_post_native_run_check_calls_the_backstop_for_each_failed_check(self, tmp_path, monkeypatch):
        ticket = tmp_path / "agent-working" / "tickets" / "inprogress" / "TCK-5.md"
        ticket.parent.mkdir(parents=True)
        ticket.write_text("x")
        outcomes = iter([1, 0, 0])
        monkeypatch.setattr(post_native_run_check.subprocess, "run",
                            lambda cmd, **kw: subprocess.CompletedProcess(cmd, next(outcomes), stdout="", stderr=""))
        calls = []
        monkeypatch.setattr(post_native_run_check.gate_ledger, "backstop_adjudicate", lambda t, n: calls.append((t, n)))
        monkeypatch.setattr(post_native_run_check.gate_verdicts, "record_gate_verdict", lambda **kw: None)
        assert post_native_run_check.run("TCK-5", repo=tmp_path, out=lambda *_: None) == 1
        assert calls == [("TCK-5", "done_checker_static")]
