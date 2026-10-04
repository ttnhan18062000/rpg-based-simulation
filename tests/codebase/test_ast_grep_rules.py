"""Tests for the ast-grep rule pack in codebase/rules/ and its adapter (TCK-20261004-AST-GREP-RULE-PACK-ADVISORY).

The rule tests run the real `ast-grep` binary from the `lint` dependency group. A missing binary is a failure with
a message, never a silent pass: the code-health jobs sync that group.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from codebase.gates import staged_ratchet
from codebase.health import __main__ as health_cli
from codebase.health import registry, scan
from codebase.health.adapters import MODULE_SYMBOL, adapt_ast_grep
from codebase.health.findings import TOOL_AST_GREP, Finding
from codebase.health.registry import Row

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG = _REPO_ROOT / "codebase" / "rules" / "sgconfig.yml"


def _binary() -> str:
    beside = Path(sys.executable).parent / "ast-grep"
    if beside.exists():
        return str(beside)
    pytest.fail("ast-grep is not installed: run `uv sync` (it is in the `lint` dependency group)")


def _ast_grep(*args: str, cwd: Path = _REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run([_binary(), *args], cwd=cwd, capture_output=True, text=True, check=False)


# ── The rules themselves ──────────────────────────────────────────────────────


def test_every_rule_passes_its_valid_and_invalid_cases():
    done = _ast_grep("test", "--config", str(_CONFIG), "--skip-snapshot-tests")
    assert done.returncode == 0, done.stdout + done.stderr


def test_every_rule_file_has_a_rule_test_file():
    rules = {p.stem for p in (_CONFIG.parent / "rules").glob("*.yml")}
    tests = {p.stem.removesuffix("-test") for p in (_CONFIG.parent / "rule-tests").glob("*-test.yml")}
    assert rules and rules == tests


_SAMPLE = '''\
from src.engine.cadence import should_run, _internal


class Service:
    def run(self):
        try:
            go()
        except ValueError:
            pass

    def create_v2_app(self):
        return 1


def outer():
    def inner():
        try:
            go()
        except OSError:
            pass
    return inner
'''


@pytest.fixture
def scanned(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text(_SAMPLE)
    done = _ast_grep("scan", "--config", str(_CONFIG), "src", "--json=compact", cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    return tmp_path, json.loads(done.stdout)


def test_a_scan_reports_each_rule_once_per_violation(scanned):
    _, records = scanned
    assert sorted(r["ruleId"] for r in records) == [
        "e3-silent-except", "e3-silent-except", "n3-private-name-import", "n4-version-marker-name",
    ]


# ── The adapter ───────────────────────────────────────────────────────────────


def test_adapter_keys_findings_by_enclosing_symbol_and_never_by_line(scanned):
    root, records = scanned
    findings = adapt_ast_grep(records, str(root))
    assert {(f.file, f.symbol, f.tool, f.rule, f.value) for f in findings} == {
        ("src/sample.py", MODULE_SYMBOL, TOOL_AST_GREP, "n3-private-name-import", 1),
        ("src/sample.py", "Service.run", TOOL_AST_GREP, "e3-silent-except", 1),
        ("src/sample.py", "Service.create_v2_app", TOOL_AST_GREP, "n4-version-marker-name", 1),
        ("src/sample.py", "outer.inner", TOOL_AST_GREP, "e3-silent-except", 1),
    }
    assert all(f.line for f in findings)


def test_a_moved_violation_keeps_its_key(scanned):
    root, records = scanned
    before = {f.key for f in adapt_ast_grep(records, str(root))}
    shifted = "# a new first line\n" + (root / "src" / "sample.py").read_text()
    (root / "src" / "sample.py").write_text(shifted)
    moved = [dict(r, range={"start": {"line": r["range"]["start"]["line"] + 1}}) for r in records]
    assert {f.key for f in adapt_ast_grep(moved, str(root))} == before


def test_counts_add_up_within_one_symbol_and_an_unreadable_file_falls_back_to_module(tmp_path):
    record = {"file": "src/gone.py", "ruleId": "e3-silent-except", "range": {"start": {"line": 4}}}
    findings = adapt_ast_grep([record, record], str(tmp_path))
    assert findings == [Finding("src/gone.py", MODULE_SYMBOL, TOOL_AST_GREP, "e3-silent-except", 2)]


# ── Seeding only this tool ────────────────────────────────────────────────────


def _row(file, tool, rule, symbol=None, reviewed=False, added="2026-09-01"):
    return Row(file, symbol, tool, rule, 3, 3, added, reviewed, None)


def _scratch_repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "codebase" / "baselines").mkdir(parents=True)
    scan_dir = tmp_path / "scan"
    scan_dir.mkdir()
    record = {"file": "src/a.py", "ruleId": "e3-silent-except", "range": {"start": {"line": 0}}}
    (scan_dir / scan.AST_GREP_JSON).write_text(json.dumps([record]))
    return scan_dir, registry.registry_path(tmp_path)


def test_seed_tool_adds_only_that_tools_rows_and_leaves_every_other_row_byte_identical(tmp_path):
    scan_dir, path = _scratch_repo(tmp_path)
    registry.write_rows(path, [_row("src/a.py", "ruff", "ANN001"), _row("src/a.py", "complexipy", "cognitive-complexity", "f")])
    before = path.read_text()
    assert health_cli.main(["--root", str(tmp_path), "seed", "--tool", "ast_grep", "--from", str(scan_dir)]) == 0
    after = path.read_text()
    assert set(before.splitlines()) < set(after.splitlines())
    new = [json.loads(line) for line in set(after.splitlines()) - set(before.splitlines())]
    assert [(r["tool"], r["rule"], r["symbol"], r["value"]) for r in new] == [("ast_grep", "e3-silent-except", "<module>", 1)]


def test_reseeding_a_tool_needs_force_and_keeps_review_data(tmp_path, capsys):
    scan_dir, path = _scratch_repo(tmp_path)
    registry.write_rows(path, [_row("src/a.py", "ast_grep", "e3-silent-except", MODULE_SYMBOL, reviewed=True)])
    argv = ["--root", str(tmp_path), "seed", "--tool", "ast_grep", "--from", str(scan_dir)]
    assert health_cli.main(argv) == 2 and "use --force" in capsys.readouterr().err
    assert health_cli.main([*argv, "--force"]) == 0
    row = registry.load_rows(path, tmp_path, check_files=False)[0]
    assert (row.reviewed, row.added_date, row.value, row.ceiling) == (True, "2026-09-01", 1, 1)


def test_seed_rejects_an_unknown_tool(tmp_path):
    with pytest.raises(SystemExit):
        health_cli.main(["--root", str(tmp_path), "seed", "--tool", "sg"])


# ── A missing binary is loud; the staged hook never needs it ──────────────────


def test_a_missing_binary_is_a_tool_unavailable_error_naming_ast_grep_never_sg(tmp_path, monkeypatch):
    asked: list[str] = []

    def not_found(name):
        asked.append(name)
        return None

    monkeypatch.setattr(scan.shutil, "which", not_found)
    monkeypatch.setattr(scan.sys, "executable", str(tmp_path / "bin" / "python"))
    with pytest.raises(scan.ToolUnavailableError, match="ast-grep not found"):
        scan.run_scan(tmp_path, tmp_path / "out", ("ast_grep",))
    assert asked == ["ast-grep"]


def test_ast_grep_is_in_the_full_scan_but_not_the_snapshot_set():
    assert "ast_grep" in scan.ALL_TOOLS and "ast_grep" not in scan.OFFLINE_TOOLS


def test_the_staged_hook_ignores_ast_grep_rows_and_does_not_need_the_binary(tmp_path, monkeypatch, capsys):
    (tmp_path / "src").mkdir()
    (tmp_path / "codebase" / "baselines").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[tool.ruff.lint]\nselect = ["E722"]\n')
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    registry.write_rows(
        registry.registry_path(tmp_path), [_row("src/a.py", "ast_grep", "e3-silent-except", "f")]
    )

    def boom(*_a, **_k):
        raise AssertionError("the staged hook must not look for ast-grep")

    monkeypatch.setattr(scan, "_find", boom)
    assert staged_ratchet.run(tmp_path, ["src/a.py"]) == 0
    assert "skipped" not in capsys.readouterr().out
