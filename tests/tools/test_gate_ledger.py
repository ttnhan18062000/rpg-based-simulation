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


# ---------------------------------------------------------------------------
# TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO
# ---------------------------------------------------------------------------

import generate_retro  # noqa: E402

TS = "2026-10-06T01:00:00Z"  # ISO week 2026-W41


def _fixture_ledger(root: Path) -> None:
    """3 gates: `cli:big` has 6 adjudicated verdicts (2 false blocks), `cli:small` 2, `cli:none` none."""
    rows = []
    for i in range(6):
        rows.append(_verdict(f"big{i}", TS, True, ticket=f"TCK-B{i}", gate="cli:big"))
    for i in range(2):
        rows.append(_verdict(f"small{i}", TS, True, ticket=f"TCK-S{i}", gate="cli:small", mode="workflow"))
    rows.append(_verdict("none0", TS, False, ticket="TCK-N", gate="cli:none"))
    _put(root, *rows)
    for i in range(6):
        gate_ledger.record_adjudication(f"big{i}", "false_block" if i < 2 else "true_block", "owner", "ruled", data_root=root)
    gate_ledger.record_adjudication("small0", "true_block", "owner", "ruled", data_root=root)
    gate_ledger.record_adjudication("small1", "false_pass", "orchestrator-backstop", "ruled", data_root=root)


class TestReport:
    def test_per_gate_cells_follow_the_adjudicated_count(self, tmp_path):
        _fixture_ledger(tmp_path)
        text = gate_ledger.render_section(gate_ledger.load_rows(tmp_path), "2026-W41", 9)
        big = next(line for line in text.splitlines() if "`cli:big`" in line)
        small = next(line for line in text.splitlines() if "`cli:small`" in line)
        none = next(line for line in text.splitlines() if "`cli:none`" in line)
        assert "2/6 (33%)" in big
        assert "too few adjudicated (n=2, false blocks 0)" in small and "%" not in small
        assert "not adjudicated" in none

    def test_counts_modes_outcomes_and_unresolved(self, tmp_path):
        _put(tmp_path, _verdict("a", "2026-10-06T01:00:00Z", True), _verdict("b", "2026-10-06T02:00:00Z", False),
             _verdict("c", "2026-10-06T03:00:00Z", True, ticket="TCK-2", mode="workflow"))
        gate_ledger.record_outcome("c", "overridden", data_root=tmp_path)
        (g,) = gate_ledger.report(gate_ledger.load_rows(tmp_path))
        assert (g["verdicts"], g["blocking"], g["unresolved"]) == (3, 2, 0)
        assert dict(g["by_mode"]) == {"hand": 2, "workflow": 1}
        assert dict(g["outcomes_derived"]) == {"fixed_and_rerun": 1} and dict(g["outcomes_recorded"]) == {"overridden": 1}

    def test_unknown_ruling_is_not_counted_as_adjudicated(self, tmp_path):
        _put(tmp_path, _verdict("a", TS, True))
        gate_ledger.record_adjudication("a", "unknown", "owner", "cannot tell", data_root=tmp_path)
        assert gate_ledger.report(gate_ledger.load_rows(tmp_path))[0]["adjudicated"] == 0

    def test_week_filter_uses_the_verdict_timestamp(self, tmp_path):
        _put(tmp_path, _verdict("a", TS, True), _verdict("b", "2026-09-01T01:00:00Z", True, ticket="TCK-2"))
        assert gate_ledger.report(gate_ledger.load_rows(tmp_path), "2026-W41")[0]["verdicts"] == 1

    def test_report_cli_prints_the_section(self, tmp_path, capsys):
        _fixture_ledger(tmp_path)
        assert gate_ledger.main(["--data-root", str(tmp_path), "report", "--week", "2026-W41"]) == 0
        assert "2/6 (33%)" in capsys.readouterr().out


class TestRetroGatesSection:
    def test_dark_instrument_and_zero_rows_wording(self):
        assert "Instrument not running" in gate_ledger.render_section([], "2026-W41", 0)
        quiet = gate_ledger.render_section([_verdict("a", "2026-09-01T00:00:00Z", True)], "2026-W41", 1)
        assert "No gate verdicts this period" in quiet and "1 records outside" in quiet and "Instrument not running" not in quiet

    def test_retro_without_gate_shards_renders_the_dark_wording(self, tmp_path, monkeypatch):
        monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", tmp_path)
        section = generate_retro._gates_section("2026-W41")
        assert "## Gates" in section and "Instrument not running" in section

    def test_retro_with_the_fixture_renders_the_table(self, tmp_path, monkeypatch):
        _fixture_ledger(tmp_path)
        monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", tmp_path)
        section = generate_retro._gates_section("2026-W41")
        assert "| gate_id |" in section and "2/6 (33%)" in section
        assert "## Gates" in generate_retro.generate([], [], "2026-W41", "2026-W41", gates=section)

    def test_regenerating_keeps_hand_written_notes_without_force(self, tmp_path, monkeypatch):
        _fixture_ledger(tmp_path)
        monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", tmp_path)
        section = generate_retro._gates_section("2026-W41")
        out = tmp_path / "RETRO.md"
        out.write_text("# old\n\n## Notes\n\nhand written finding\n")
        report = generate_retro.generate([], [], "2026-W41", "2026-W41", gates=section)
        status = generate_retro._write_report_preserving_notes(report, out, force=False)
        text = out.read_text()
        assert "preserved" in status and "hand written finding" in text and "## Gates" in text
        assert text.index("## Gates") < text.index("hand written finding")

    def test_a_failing_ledger_read_never_fails_the_retro(self, monkeypatch):
        monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", None)
        assert generate_retro._gates_section("2026-W41") is None
