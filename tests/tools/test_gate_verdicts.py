"""TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES: the `gate_verdicts` record, its writer, and the gate CLIs
that emit it. Every test runs in a scratch cwd so nothing reaches the real monitoring data root."""
from __future__ import annotations

import base64
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.agent_working_paths import TICKETS

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "agent-monitoring"))

import gate_verdicts  # noqa: E402
from gate_checks import attest_gate, doc_staleness_check, plan_gate_static, post_native_run_check  # noqa: E402

done_checker_static = importlib.import_module("gate_checks.done_checker_static")
validate_mod = importlib.import_module("validate")


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch cwd with recording switched on (the autouse conftest guard is lifted)."""
    monkeypatch.delenv(gate_verdicts.ENV_NO_RECORD, raising=False)
    monkeypatch.delenv(gate_verdicts.ENV_EXECUTION_MODE, raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _rows(root: Path) -> list[dict]:
    rows = []
    for shard in root.glob("agent-working/agent-monitoring/data/*/*.gate_verdicts.jsonl"):
        rows.extend(json.loads(line) for line in shard.read_text().splitlines() if line.strip())
    return rows


def _valid(**over) -> dict:
    base = dict(gate_id="cli:demo", gate_type="static_check", verdict="PASS", blocking=False,
                inputs_ref={"cmd_sha": "x"}, execution_mode="hand")
    base.update(over)
    return gate_verdicts.build_record(**base)


class TestRecord:
    def test_built_record_is_valid_and_ids_are_unique(self):
        a, b = _valid(), _valid()
        assert gate_verdicts.validate_record(a) == []
        assert a["gate_verdict_id"] != b["gate_verdict_id"]

    @pytest.mark.parametrize("missing", ["gate_id", "verdict", "inputs_ref", "gate_verdict_id", "ts"])
    def test_missing_required_field_is_rejected(self, missing):
        record = _valid()
        del record[missing]
        assert any(missing in p for p in gate_verdicts.validate_record(record))

    def test_empty_verdict_and_bad_types_are_rejected(self):
        assert gate_verdicts.validate_record(_valid(verdict=""))
        assert gate_verdicts.validate_record({**_valid(), "blocking": "yes"})
        assert gate_verdicts.validate_record({**_valid(), "execution_mode": "robot"})
        assert gate_verdicts.validate_record({**_valid(), "sub_results": {"c": "MAYBE"}})
        assert gate_verdicts.validate_record("not an object")

    def test_blocking_false_is_valid(self):
        assert gate_verdicts.validate_record(_valid(blocking=False)) == []

    def test_gate_id_comes_from_gate_policy_else_cli_prefix(self):
        assert gate_verdicts.gate_id_for("plan_gate_static", "plan_has_unresolved_questions_heading") == (
            "Plan:gate_checks.plan_gate_static.plan_has_unresolved_questions_heading")
        assert gate_verdicts.gate_id_for("done_checker_static", "run_finalize_selfcheck").startswith("Finalize:")
        assert gate_verdicts.gate_id_for("post_native_run_check") == "cli:post_native_run_check"
        assert gate_verdicts.gate_id_for("done_checker_static", "run_static_precheck") == "cli:done_checker_static"


class TestWriter:
    def test_writes_one_valid_row(self, scratch):
        row = gate_verdicts.record_gate_verdict(gate_id="cli:demo", gate_type="static_check", verdict="FAIL",
                                                blocking=True, inputs_ref={"cmd_sha": "x"}, ticket_id="TCK-1")
        rows = _rows(scratch)
        assert rows == [row] and rows[0]["verdict"] == "FAIL" and rows[0]["execution_mode"] == "hand"

    def test_env_guard_and_flag_write_nothing(self, scratch, monkeypatch):
        fields = dict(gate_id="cli:demo", gate_type="static_check", verdict="PASS", blocking=False, inputs_ref={"a": 1})
        assert gate_verdicts.record_gate_verdict(enabled=False, **fields) is None
        monkeypatch.setenv(gate_verdicts.ENV_NO_RECORD, "1")
        assert gate_verdicts.record_gate_verdict(**fields) is None
        assert _rows(scratch) == []

    def test_execution_mode_env_labels_the_row(self, scratch, monkeypatch):
        monkeypatch.setenv(gate_verdicts.ENV_EXECUTION_MODE, "workflow")
        row = gate_verdicts.record_gate_verdict(gate_id="cli:demo", gate_type="static_check", verdict="PASS",
                                                blocking=False, inputs_ref={"a": 1})
        assert row["execution_mode"] == "workflow"

    def test_unwritable_root_warns_once_and_does_not_raise(self, scratch, capsys):
        (scratch / "agent-working").write_text("a file where the data root's parent must be")
        row = gate_verdicts.record_gate_verdict(gate_id="cli:demo", gate_type="static_check", verdict="PASS",
                                                blocking=False, inputs_ref={"a": 1})
        err = capsys.readouterr().err
        assert row is None and err.count("WARNING: gate verdict not recorded") == 1

    def test_invalid_row_is_not_written(self, scratch, capsys):
        row = gate_verdicts.record_gate_verdict(gate_id="cli:demo", gate_type="static_check", verdict="",
                                                blocking=False, inputs_ref={"a": 1})
        assert row is None and _rows(scratch) == [] and "missing verdict" in capsys.readouterr().err


class TestCliSites:
    def test_done_checker_failing_and_passing_rows_carry_sub_results(self, scratch, monkeypatch, capsys):
        monkeypatch.setattr(done_checker_static, "run_finalize_selfcheck", lambda *a, **k: [
            {"condition": "ticket_finalized", "status": "PASS", "evidence": "e"},
            {"condition": "migration_complete", "status": "FAIL", "evidence": "e"}])
        monkeypatch.setattr(done_checker_static, "run_advisory_checks", lambda *a, **k: [])
        assert done_checker_static.main(["--ticket-id", "TCK-1", "--tier", "hotfix", "--part", "finalize"]) == 1
        monkeypatch.setattr(done_checker_static, "run_finalize_selfcheck", lambda *a, **k: [
            {"condition": "ticket_finalized", "status": "PASS", "evidence": "e"}])
        assert done_checker_static.main(["--ticket-id", "TCK-2", "--tier", "hotfix", "--part", "finalize"]) == 0
        failing, passing = _rows(scratch)
        assert (failing["verdict"], failing["blocking"]) == ("FAIL", True)
        assert failing["sub_results"] == {"finalize.ticket_finalized": "PASS", "finalize.migration_complete": "FAIL"}
        assert (passing["verdict"], passing["blocking"], passing["ticket_id"]) == ("PASS", False, "TCK-2")
        assert passing["gate_id"].startswith("Finalize:") and passing["inputs_ref"]["cmd_sha"]
        assert "RESULT: PASS" in capsys.readouterr().out

    def _stub_both(self, monkeypatch, closed):
        monkeypatch.setattr(done_checker_static, "check_ticket_finalized", lambda t: ("PASS" if closed else "FAIL", "e"))
        monkeypatch.setattr(done_checker_static, "run_static_precheck", lambda *a, **k: [
            {"condition": "ticket_location", "status": "FAIL", "evidence": "e"}])
        monkeypatch.setattr(done_checker_static, "run_finalize_selfcheck", lambda *a, **k: [
            {"condition": "ticket_finalized", "status": "PASS", "evidence": "e"}])
        monkeypatch.setattr(done_checker_static, "run_advisory_checks", lambda *a, **k: [])

    def test_part_both_on_a_closed_ticket_records_a_nonblocking_post_close_precheck_row(self, scratch, monkeypatch, capsys):
        self._stub_both(monkeypatch, closed=True)
        assert done_checker_static.main(["--ticket-id", "TCK-1", "--tier", "hotfix", "--part", "both"]) == 0
        precheck, finalize = _rows(scratch)
        assert precheck["gate_id"] != finalize["gate_id"] and finalize["gate_id"].startswith("Finalize:")
        assert (precheck["verdict"], precheck["blocking"], precheck["phase"]) == ("FAIL", False, "Verify")
        assert precheck["inputs_ref"]["post_close"] is True
        assert set(precheck["sub_results"]) == {"precheck.ticket_location"}
        assert (finalize["verdict"], finalize["blocking"]) == ("PASS", False)
        assert "post_close" not in finalize["inputs_ref"]
        assert "WARNING" in capsys.readouterr().out

    def test_part_both_on_an_open_ticket_records_a_blocking_precheck_row_under_its_own_gate(self, scratch, monkeypatch):
        self._stub_both(monkeypatch, closed=False)
        assert done_checker_static.main(["--ticket-id", "TCK-1", "--tier", "hotfix", "--part", "both"]) == 1
        precheck, finalize = _rows(scratch)
        assert (precheck["verdict"], precheck["blocking"]) == ("FAIL", True)
        assert "post_close" not in precheck["inputs_ref"]
        assert precheck["gate_id"] != finalize["gate_id"]
        assert (finalize["verdict"], finalize["blocking"]) == ("PASS", False)

    def test_done_checker_no_record_writes_nothing(self, scratch, monkeypatch):
        monkeypatch.setattr(done_checker_static, "run_finalize_selfcheck", lambda *a, **k: [])
        monkeypatch.setattr(done_checker_static, "run_advisory_checks", lambda *a, **k: [])
        done_checker_static.main(["--ticket-id", "TCK-1", "--tier", "hotfix", "--part", "finalize", "--no-record"])
        assert _rows(scratch) == []

    def test_plan_gate_cli_passing_and_failing(self, scratch, capsys):
        ok, bad = scratch / "ok.md", scratch / "bad.md"
        ok.write_text("# Plan\n\n## Unresolved Questions\n\nNone.\n")
        bad.write_text("# Plan\n\n## Unresolved Questions\n\nWhich owner decides X?\n")
        assert plan_gate_static.main(["--plan-path", str(ok)]) == 0
        assert plan_gate_static.main(["--plan-path", str(bad), "--ticket-id", "TCK-9"]) == 1
        passing, failing = _rows(scratch)
        assert (passing["verdict"], failing["verdict"], failing["blocking"], failing["ticket_id"]) == ("PASS", "FAIL", True, "TCK-9")
        assert failing["gate_id"].startswith("Plan:")

    def test_post_native_run_check_records_one_row_with_sub_results(self, scratch, monkeypatch):
        ticket = scratch / TICKETS / "inprogress" / "TCK-5.md"
        ticket.parent.mkdir(parents=True)
        ticket.write_text("x")
        outcomes = iter([0, 1, 0])

        def fake_run(cmd, **kwargs):
            assert kwargs["env"][gate_verdicts.ENV_EXECUTION_MODE] == "workflow"
            return subprocess.CompletedProcess(cmd, next(outcomes), stdout="", stderr="")

        monkeypatch.setattr(post_native_run_check.subprocess, "run", fake_run)
        assert post_native_run_check.run("TCK-5", repo=scratch, out=lambda *_: None) == 1
        (row,) = _rows(scratch)
        assert row["execution_mode"] == "workflow" and row["verdict"] == "FAIL" and row["blocking"] is True
        assert row["sub_results"] == {"done_checker_static": "PASS", "validate_frontmatter": "FAIL", "ticket_field_values": "PASS"}

    def test_doc_staleness_cli_records_and_strips_its_options(self, scratch, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["doc_staleness_check.py", "true", "src/a.py", "--docs-to-update", "docs/x.md",
                                          "--execution-mode", "pipeline"])
        import runpy
        runpy.run_path(str(REPO_ROOT / "tools" / "gate_checks" / "doc_staleness_check.py"), run_name="__main__")
        (row,) = _rows(scratch)
        assert row["verdict"] == "FAIL" and row["blocking"] is True and row["execution_mode"] == "pipeline"
        marker = json.loads(capsys.readouterr().out.split("MARKER:")[1])
        assert marker[0]["status"] == "FAIL"

    def test_doc_staleness_passing_case_records_pass(self, scratch, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["doc_staleness_check.py", "false", "src/a.py"])
        import runpy
        runpy.run_path(str(REPO_ROOT / "tools" / "gate_checks" / "doc_staleness_check.py"), run_name="__main__")
        (row,) = _rows(scratch)
        assert (row["verdict"], row["blocking"], row["execution_mode"]) == ("PASS", False, "hand")

    def test_attest_gate_passing_case_records_pass(self, scratch):
        attest_gate.main(["--nonce", "n", "--gate-id", "demo_gate", "--cmd-b64", base64.b64encode(b"true").decode()])
        (row,) = _rows(scratch)
        assert (row["verdict"], row["blocking"], row["inputs_ref"]["exit_code"]) == ("PASS", False, 0)

    def test_attest_gate_persists_the_attest_line_without_the_mac(self, scratch, capsys):
        cmd = "echo hi; exit 3"
        assert attest_gate.main(["--nonce", "n", "--gate-id", "demo_gate", "--cmd-b64",
                                 base64.b64encode(cmd.encode()).decode()]) == 0
        (row,) = _rows(scratch)
        assert row["gate_id"] == "demo_gate" and row["verdict"] == "FAIL" and row["blocking"] is True
        assert row["inputs_ref"]["exit_code"] == 3 and row["inputs_ref"]["stdout_sha"] == gate_verdicts.sha256_hex("hi\n")
        assert "mac" not in json.dumps(row)
        assert capsys.readouterr().out.startswith("ATTEST:")

    def test_attest_gate_keeps_the_wrapped_command_from_recording_a_second_row(self, scratch):
        cmd = f"{sys.executable} -c \"import os;print(os.environ['GATE_VERDICT_NO_RECORD'])\""
        _, out = attest_gate.attest("n", "g", cmd)
        assert out.strip() == "1"


class TestValidatePy:
    def test_check_flags_an_invalid_row_and_accepts_a_valid_one(self, tmp_path):
        week = tmp_path / "2026-W41"
        week.mkdir()
        (week / "b.gate_verdicts.jsonl").write_text(json.dumps(_valid()) + "\n" + json.dumps({"ts": "t"}) + "\n")
        errors = validate_mod.check_gate_verdicts(tmp_path)
        assert len(errors) == 1 and "b.gate_verdicts.jsonl#2" in errors[0] and "missing gate_id" in errors[0]

    def test_check_is_quiet_without_shards(self, tmp_path):
        assert validate_mod.check_gate_verdicts(tmp_path) == []
