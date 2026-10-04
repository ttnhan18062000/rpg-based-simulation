"""The ratchet's blocking policy (TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING).

`REPORT_ONLY_TOOLS` findings are listed but never fail `check`; `SKIPPABLE_TOOLS` may fail to run without failing it,
and a skipped tool is "not measured", never "gone". The CLI tests reuse the scratch-repository fixtures of
test_code_health_ratchet_registry.py; the skip tests replace the tool runners with copies of the captured output.
"""
from __future__ import annotations

import json
import shutil

import pytest

from tests.codebase.test_code_health_ratchet_registry import (  # noqa: F401  (pytest fixtures)
    _f,
    _rows,
    _run,
    _scan_arg,
    repo,
    seeded,
)
from codebase.health import ratchet, registry, scan
from codebase.health.ratchet import REPORT_ONLY_TOOLS, SKIPPABLE_TOOLS, compare, format_report, format_summary

_FILES = {
    "ruff": "ruff.json",
    "complexipy": "complexipy.json",
    "line_count": "line_count.json",
    "ast_grep": "ast_grep.json",
    "jscpd": "jscpd",
}


def _drop_rows(repo, tool: str) -> int:
    """Remove a tool's rows from the scratch registry, so its current findings read as new; returns how many."""
    path = repo / "reg.jsonl"
    lines = path.read_text().splitlines()
    kept = [line for line in lines if json.loads(line)["tool"] != tool]
    path.write_text("\n".join(kept) + "\n")
    return len(lines) - len(kept)


def _fake_tools(monkeypatch, repo, failing=()):
    """Tool runners that copy the captured output into the scan directory; `failing` ones cannot run."""

    def runner(name):
        def run(root, out_dir):
            if name in failing:
                raise scan.ToolUnavailableError(f"{name}: cannot run")
            source, target = repo / "scan" / _FILES[name], out_dir / _FILES[name]
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy(source, target)

        return run

    monkeypatch.setattr(scan, "_SCANNERS", {name: runner(name) for name in scan.ALL_TOOLS})


# ── The two sets ──────────────────────────────────────────────────────────────


def test_the_policy_sets():
    assert REPORT_ONLY_TOOLS == {"jscpd"}
    assert SKIPPABLE_TOOLS == {"jscpd"}


def test_a_blocking_tool_can_never_be_skippable():
    assert SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS


# ── Report-only versus blocking, at the ratchet ───────────────────────────────


@pytest.mark.parametrize("tool", sorted(REPORT_ONLY_TOOLS))
def test_a_new_report_only_finding_is_listed_and_does_not_block(tool):
    result = compare([_f("a.py", "R1", 2, tool=tool)], [])
    assert result.failed and not result.blocking_failed, "`failed` keeps its meaning for the hooks"
    report = format_report(result)
    assert "(report-only)" in report and report.splitlines()[-1].startswith("OK:") and "1 report-only" in report
    assert "Report-only findings" in format_summary(result)


@pytest.mark.parametrize("tool", ["ruff", "complexipy", "line_count", "ast_grep"])
def test_a_new_blocking_finding_blocks(tool):
    result = compare([_f("a.py", "R1", 2, tool=tool)], [])
    assert result.blocking_failed and format_report(result).splitlines()[-1].startswith("FAIL:")


def test_a_worse_report_only_finding_does_not_block_but_a_worse_blocking_one_does():
    rows = _rows([_f("a.py", "R1", 1, tool="jscpd"), _f("a.py", "F401", 1)])
    assert not compare([_f("a.py", "R1", 3, tool="jscpd"), _f("a.py", "F401", 1)], rows).blocking_failed
    assert compare([_f("a.py", "R1", 1, tool="jscpd"), _f("a.py", "F401", 3)], rows).blocking_failed


def test_the_summary_counts_and_lists_only_blocking_violations_in_its_header():
    result = compare([_f("a.py", "R1", 2, tool="jscpd"), _f("b.py", "E722", 1)], [])
    text = format_summary(result, ["b.py"])
    assert "1 new or worse blocking violations" in text and "Report-only findings" in text


# ── Report-only versus blocking, through the CLI ──────────────────────────────


def test_check_exits_0_and_lists_a_new_jscpd_finding(seeded, capsys):
    assert _drop_rows(seeded, "jscpd")
    assert _run(seeded, "check", *_scan_arg(seeded), "--annotate") == 0
    out = capsys.readouterr().out
    assert "(report-only)" in out and "::error::" not in out


def test_check_exits_1_on_a_new_ast_grep_finding(seeded, capsys):
    path = seeded / "scan" / "ast_grep.json"
    record = {"file": str(seeded / "sample_src" / "bad.py"), "range": {"start": {"line": 0}}, "ruleId": "E3"}
    path.write_text(json.dumps([record]))
    assert _run(seeded, "check", *_scan_arg(seeded), "--annotate") == 1
    out = capsys.readouterr().out
    assert "ast_grep E3" in out and "(report-only)" not in out and "::error::code-health:" in out


@pytest.mark.parametrize("tool", ["ruff", "complexipy", "line_count"])
def test_check_exits_1_on_a_new_blocking_tool_finding(seeded, tool, capsys):
    assert _drop_rows(seeded, tool)
    assert _run(seeded, "check", *_scan_arg(seeded), "--annotate") == 1
    assert "::error::code-health:" in capsys.readouterr().out


# ── A tool that cannot run ────────────────────────────────────────────────────


def test_jscpd_unavailable_exits_0_with_the_note_a_warning_and_an_ok_verdict(seeded, monkeypatch, capsys):
    _fake_tools(monkeypatch, seeded, failing={"jscpd"})
    summary = seeded / "summary.md"
    assert _run(seeded, "check", "--summary-out", str(summary), "--annotate") == 0
    out = capsys.readouterr().out
    note = "jscpd could not run (report-only); its findings were not measured"
    assert out.count("::warning::") == 1 and f"::warning::code-health: {note}" in out
    assert "::error::" not in out and note in out
    assert [l for l in out.splitlines() if l.startswith(("OK:", "FAIL:"))][0].startswith("OK:")
    text = summary.read_text()
    assert "**Code health:** OK" in text and note in text


def test_jscpd_unavailable_leaves_its_rows_out_of_gone_and_still_checks_the_rest(seeded, monkeypatch, capsys):
    before = (seeded / "reg.jsonl").read_bytes()
    jscpd_rows = [r for r in registry.load_rows(seeded / "reg.jsonl", seeded, check_files=False) if r.tool == "jscpd"]
    assert jscpd_rows
    _fake_tools(monkeypatch, seeded, failing={"jscpd"})
    assert _run(seeded, "check") == 0
    out = capsys.readouterr().out
    assert " 0 gone," in out and "gone (not a failure" not in out
    assert (seeded / "reg.jsonl").read_bytes() == before, "check never writes the registry"
    # a stale jscpd report from an earlier scan must not be read as a measurement either
    stale = seeded / "reports" / "code_health" / "scan" / "jscpd"
    stale.mkdir(parents=True)
    (stale / "jscpd-report.json").write_text('{"duplicates": []}')
    assert _run(seeded, "check") == 0 and " 0 gone," in capsys.readouterr().out
    # the other tools are still compared
    assert _drop_rows(seeded, "ruff")
    assert _run(seeded, "check") == 1


@pytest.mark.parametrize("tool", ["ruff", "complexipy", "line_count", "ast_grep"])
def test_any_other_tool_unavailable_exits_2(seeded, monkeypatch, capsys, tool):
    _fake_tools(monkeypatch, seeded, failing={tool})
    summary = seeded / "summary.md"
    assert _run(seeded, "check", "--summary-out", str(summary), "--annotate") == 2
    out = capsys.readouterr().out
    assert f"::error::code-health could not run: {tool}: cannot run" in out
    assert "could not run:" in summary.read_text()


def test_a_jscpd_timeout_is_a_skip_not_a_hang_and_not_exit_2(seeded, monkeypatch, capsys):
    import subprocess

    def stalled(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    (seeded / "Makefile").write_text("JSCPD_VERSION = 5.4.0\n")
    real_jscpd = scan._SCANNERS["jscpd"]
    _fake_tools(monkeypatch, seeded)  # every tool but jscpd copies captured output
    monkeypatch.setitem(scan._SCANNERS, "jscpd", real_jscpd)
    monkeypatch.setattr(scan.subprocess, "run", stalled)
    assert _run(seeded, "check") == 0
    out = capsys.readouterr().out
    assert "jscpd could not run (report-only); its findings were not measured" in out
    assert [l for l in out.splitlines() if l.startswith(("OK:", "FAIL:"))][0].startswith("OK:")


def test_the_jscpd_run_has_a_timeout_and_the_other_tools_have_none(monkeypatch, tmp_path):
    import subprocess

    seen = {}

    def fake(command, **kwargs):
        seen[command[0]] = kwargs.get("timeout")
        return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")

    (tmp_path / "Makefile").write_text("JSCPD_VERSION = 5.4.0\n")
    monkeypatch.setattr(scan.subprocess, "run", fake)
    scan._scan_jscpd(tmp_path, tmp_path)
    assert seen["npx"] == scan.JSCPD_TIMEOUT_S and 0 < scan.JSCPD_TIMEOUT_S <= 600
    scan._scan_ruff(tmp_path, tmp_path)
    assert seen[scan.sys.executable] is None


def test_the_timeout_names_the_command_and_the_limit(monkeypatch, tmp_path):
    import subprocess

    def stalled(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(scan.subprocess, "run", stalled)
    with pytest.raises(scan.ToolUnavailableError, match=r"timed out after 7s"):
        scan._run(["npx", "jscpd"], tmp_path, (0,), timeout=7)


def test_an_unusable_registry_exits_2(seeded, monkeypatch):
    _fake_tools(monkeypatch, seeded)
    (seeded / "reg.jsonl").write_text("{not json\n")
    assert _run(seeded, "check") == 2


def test_from_dir_never_skips_a_tool(seeded):
    (seeded / "scan" / "jscpd" / "jscpd-report.json").unlink()
    assert _run(seeded, "check", *_scan_arg(seeded)) == 2


@pytest.mark.parametrize("command", [["seed", "--force"], ["tighten", "--yes"]])
def test_seed_and_tighten_refuse_when_jscpd_cannot_run(seeded, monkeypatch, command):
    _fake_tools(monkeypatch, seeded, failing={"jscpd"})
    before = (seeded / "reg.jsonl").read_bytes()
    assert _run(seeded, *command) == 2
    assert (seeded / "reg.jsonl").read_bytes() == before, "the registry stays byte-identical"
