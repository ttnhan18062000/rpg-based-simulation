"""Tests for the code-health ratchet, registry and CLI (TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY).

The CLI tests run in a scratch repository (`--root`) built from the captured tool output in
tests/fixtures/code_health/; they never touch the real registry or run any tool.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from codebase.health import registry, scan
from codebase.health.__main__ import main
from codebase.health.adapters import adapt_ruff
from codebase.health.findings import Finding
from codebase.health.ratchet import compare, format_report
from codebase.health.registry import Row, RegistryError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "code_health"
_TODAY = date(2026, 10, 2)


def _f(file: str, rule: str, value: int, symbol: str | None = None, tool: str = "ruff", line: int | None = None) -> Finding:
    return Finding(file, symbol, tool, rule, value, line)


def _rows(findings: list[Finding]) -> list[Row]:
    return registry.seed_rows(findings, _TODAY)


# ── Ratchet semantics ─────────────────────────────────────────────────────────


def test_baseline_seeded_from_the_same_scan_passes():
    scan_result = [_f("a.py", "F401", 3), _f("a.py", "f", 40, symbol="a.f", tool="complexipy")]
    result = compare(scan_result, _rows(scan_result))
    assert not result.failed and result.unchanged == 2
    assert format_report(result).endswith("OK: 0 new, 0 worse, 0 improved, 0 gone, 2 unchanged")


def test_a_violation_with_no_baseline_row_fails():
    baseline = [_f("a.py", "F401", 1)]
    result = compare([*baseline, _f("b.py", "E722", 1)], _rows(baseline))
    assert result.failed
    assert [f.key for f in result.new] == [("b.py", None, "ruff", "E722")]
    assert "NEW violations" in format_report(result)


def test_a_value_above_the_ceiling_fails_and_equal_or_lower_does_not():
    rows = _rows([_f("a.py", "F401", 3)])
    worse = compare([_f("a.py", "F401", 4)], rows)
    assert worse.failed and worse.worse[0][1].ceiling == 3
    assert "WORSE than baseline" in format_report(worse)
    assert not compare([_f("a.py", "F401", 3)], rows).failed
    assert not compare([_f("a.py", "F401", 2)], rows).failed


def test_the_same_key_at_a_different_line_is_unchanged():
    baseline = [_f("a.py", "C901", 1, line=10)]
    result = compare([_f("a.py", "C901", 1, line=400)], _rows(baseline))
    assert not result.failed and result.unchanged == 1


def test_a_symbol_less_ruff_finding_that_moves_lines_is_not_new():
    raw = json.loads((_FIXTURES / "ruff.json").read_text(encoding="utf-8"))
    rows = _rows(adapt_ruff(raw, "/FIXTURE_ROOT"))
    for record in raw:
        record["location"]["row"] += 57
    result = compare(adapt_ruff(raw, "/FIXTURE_ROOT"), rows)
    assert not result.failed and not result.new and not result.gone


def test_improved_and_gone_rows_are_reported_but_never_fail():
    rows = _rows([_f("a.py", "F401", 5), _f("b.py", "E722", 1)])
    result = compare([_f("a.py", "F401", 2)], rows)
    assert not result.failed
    assert [(f.value, r.ceiling) for f, r in result.improved] == [(2, 5)]
    assert [r.file for r in result.gone] == ["b.py"]
    report = format_report(result)
    assert "improved" in report and "gone" in report and report.splitlines()[-1].startswith("OK:")


def test_the_report_caps_each_section():
    findings = [_f(f"f{i}.py", "F401", 1) for i in range(30)]
    report = format_report(compare(findings, []), limit=5)
    assert "NEW violations (no baseline row) (30)" in report and "... and 25 more" in report


# ── Registry: seeding, ordering, delete, tighten ──────────────────────────────


def test_seeded_rows_are_unreviewed_with_ceiling_equal_to_value_and_stamped():
    (row,) = _rows([_f("a.py", "F401", 7)])
    assert (row.value, row.ceiling, row.reviewed, row.added_date, row.retiring_ticket) == (7, 7, False, "2026-10-02", None)


def test_rows_round_trip_sorted_by_key(tmp_path):
    path = tmp_path / "reg.jsonl"
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    registry.write_rows(path, _rows([_f("b.py", "X", 1), _f("a.py", "Z", 1), _f("a.py", "Y", 1)]))
    loaded = registry.load_rows(path, tmp_path)
    assert [(r.file, r.rule) for r in loaded] == [("a.py", "Y"), ("a.py", "Z"), ("b.py", "X")]
    assert path.read_text().splitlines() == sorted(path.read_text().splitlines(), key=lambda s: (json.loads(s)["file"], json.loads(s)["rule"]))


def test_reseed_carries_over_review_data_resets_measurements_and_drops_vanished_keys():
    earlier = [
        Row("a.py", None, "ruff", "F401", 5, 5, "2026-01-01", True, "TCK-20260101-X"),
        Row("gone.py", None, "ruff", "F401", 1, 1, "2026-01-01", False, None),
    ]
    reseeded = {
        r.file: r
        for r in registry.seed_rows([_f("a.py", "F401", 8), _f("new.py", "F401", 2)], _TODAY, previous=earlier)
    }
    assert set(reseeded) == {"a.py", "new.py"}
    kept = reseeded["a.py"]
    assert (kept.reviewed, kept.retiring_ticket, kept.added_date) == (True, "TCK-20260101-X", "2026-01-01")
    assert (kept.value, kept.ceiling) == (8, 8)
    fresh = reseeded["new.py"]
    assert (fresh.reviewed, fresh.retiring_ticket, fresh.added_date) == (False, None, "2026-10-02")


def test_a_duplication_row_touching_a_same_name_pair_file_links_that_ticket_and_nothing_else_is_linked():
    dup = _f("src/strategy/capacity.py", "duplicate-block", 12, symbol="dup:src/strategy/other.py", tool="jscpd")
    other = _f("src/x.py", "duplicate-block", 9, symbol="dup:src/strategy/cognition_capacity.py", tool="jscpd")
    unrelated = _f("src/x.py", "duplicate-block", 9, symbol="dup:src/y.py", tool="jscpd")
    ruff_on_pair_file = _f("src/core/items.py", "D102", 4)
    rows = {r.file + str(r.symbol): r.retiring_ticket for r in _rows([dup, other, unrelated, ruff_on_pair_file])}
    assert rows["src/strategy/capacity.pydup:src/strategy/other.py"] == registry.SAME_NAME_PAIRS_TICKET
    assert rows["src/x.pydup:src/strategy/cognition_capacity.py"] == registry.SAME_NAME_PAIRS_TICKET
    assert rows["src/x.pydup:src/y.py"] is None
    assert rows["src/core/items.pyNone"] is None


def test_delete_row_removes_exactly_one_and_raises_for_a_missing_key():
    rows = _rows([_f("a.py", "X", 1), _f("b.py", "X", 1)])
    remaining = registry.delete_row(rows, ("a.py", None, "ruff", "X"))
    assert [r.file for r in remaining] == ["b.py"]
    with pytest.raises(KeyError):
        registry.delete_row(rows, ("zzz.py", None, "ruff", "X"))


def test_tighten_lowers_improved_rows_deletes_gone_rows_and_never_loosens():
    rows = _rows([_f("a.py", "X", 5), _f("b.py", "X", 3), _f("c.py", "X", 2)])
    tightened, changes = registry.tighten(rows, [_f("a.py", "X", 2), _f("c.py", "X", 9)])
    assert {r.file: r.ceiling for r in tightened} == {"a.py": 2, "c.py": 2}  # a lowered, b deleted, c (worse) untouched
    assert {r.file: r.value for r in tightened}["a.py"] == 2
    assert len(changes) == 2


# ── Registry validator: one test per rejection ────────────────────────────────


def _write(path: Path, *entries: dict) -> Path:
    path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    return path


def _entry(**overrides) -> dict:
    base = {"file": "a.py", "symbol": None, "tool": "ruff", "rule": "F401", "value": 1, "ceiling": 1,
            "added_date": "2026-10-02", "reviewed": False, "retiring_ticket": None}
    return {**base, **overrides}


def test_validator_rejects_a_row_with_a_missing_required_field(tmp_path):
    (tmp_path / "a.py").write_text("")
    entry = _entry()
    del entry["ceiling"]
    path = _write(tmp_path / "reg.jsonl", entry)
    problems = registry.validate_file(path, tmp_path)
    assert any("missing required field 'ceiling'" in p for p in problems)
    with pytest.raises(RegistryError):
        registry.load_rows(path, tmp_path)


def test_validator_rejects_a_duplicate_key(tmp_path):
    (tmp_path / "a.py").write_text("")
    path = _write(tmp_path / "reg.jsonl", _entry(), _entry(value=9, ceiling=9))
    problems = registry.validate_file(path, tmp_path)
    assert any("duplicate key" in p for p in problems)


def test_validator_rejects_a_file_path_that_does_not_exist(tmp_path):
    path = _write(tmp_path / "reg.jsonl", _entry(file="no/such/file.py"))
    problems = registry.validate_file(path, tmp_path)
    assert any("file does not exist: no/such/file.py" in p for p in problems)
    assert registry.validate_file(path, tmp_path, check_files=False) == []


def test_validator_rejects_a_missing_partner_file_of_a_clone_pair(tmp_path):
    (tmp_path / "a.py").write_text("")
    path = _write(tmp_path / "reg.jsonl", _entry(tool="jscpd", rule="duplicate-block", symbol="dup:gone.py"))
    assert any("file does not exist: gone.py" in p for p in registry.validate_file(path, tmp_path))


@pytest.mark.parametrize(
    ("override", "fragment"),
    [({"value": -1}, "'value'"), ({"ceiling": "3"}, "'ceiling'"), ({"reviewed": "no"}, "'reviewed'"), ({"file": ""}, "'file'")],
)
def test_validator_rejects_wrongly_typed_fields(tmp_path, override, fragment):
    (tmp_path / "a.py").write_text("")
    path = _write(tmp_path / "reg.jsonl", _entry(**override))
    assert any(fragment in p for p in registry.validate_file(path, tmp_path, check_files=False))


def test_validator_reports_invalid_json_and_accepts_a_missing_file(tmp_path):
    path = tmp_path / "reg.jsonl"
    path.write_text("{not json\n")
    assert any("not valid JSON" in p for p in registry.validate_file(path, tmp_path))
    assert registry.validate_file(tmp_path / "absent.jsonl", tmp_path) == []


# ── CLI end to end, in a scratch repository ───────────────────────────────────


@pytest.fixture
def repo(tmp_path):
    """A scratch repository with the sample source, a config, and a staged scan of it."""
    shutil.copytree(_FIXTURES / "sample_src", tmp_path / "sample_src")
    (tmp_path / "pyproject.toml").write_text("[tool.complexipy]\nmax-complexity-allowed = 15\n")
    scan_dir = tmp_path / "scan"
    (scan_dir / "jscpd").mkdir(parents=True)
    ruff = (_FIXTURES / "ruff.json").read_text().replace("/FIXTURE_ROOT", str(tmp_path))
    (scan_dir / "ruff.json").write_text(ruff)
    shutil.copy(_FIXTURES / "complexipy.json", scan_dir / "complexipy.json")
    shutil.copy(_FIXTURES / "line_count.json", scan_dir / "line_count.json")
    shutil.copy(_FIXTURES / "jscpd-report.json", scan_dir / "jscpd" / "jscpd-report.json")
    return tmp_path


def _run(repo: Path, *args: str) -> int:
    # The sample's jscpd names are relative to sample_src, so that is the scanned directory here.
    return main(["--root", str(repo), "--registry", str(repo / "reg.jsonl"), "--scan-root", "sample_src", *args])


def _scan_arg(repo: Path) -> list[str]:
    return ["--from", str(repo / "scan")]


def _edit_ruff(repo: Path, edit) -> None:
    path = repo / "scan" / "ruff.json"
    data = json.loads(path.read_text())
    edit(data)
    path.write_text(json.dumps(data))


def test_check_passes_on_a_registry_seeded_from_the_same_scan(seeded, capsys):
    rows = registry.load_rows(seeded / "reg.jsonl", seeded)
    assert rows and all(r.reviewed is False for r in rows)
    assert {r.tool for r in rows} == {"ruff", "complexipy", "jscpd", "line_count"}
    assert _run(seeded, "check", *_scan_arg(seeded)) == 0
    assert capsys.readouterr().out.strip().splitlines()[-1].startswith("OK:")


@pytest.fixture
def seeded(repo):
    assert _run(repo, "seed", *_scan_arg(repo)) == 0
    return repo


def test_check_fails_when_a_violation_is_added_with_no_row(seeded):
    new = {"code": "E722", "filename": str(seeded / "sample_src" / "nested.py"), "location": {"row": 1, "column": 1}}
    _edit_ruff(seeded, lambda data: data.append(new))
    assert _run(seeded, "check", *_scan_arg(seeded)) == 1


def test_check_fails_when_a_value_rises_above_its_ceiling(seeded):
    extra = {"code": "E722", "filename": str(seeded / "sample_src" / "bad.py"), "location": {"row": 99, "column": 1}}
    _edit_ruff(seeded, lambda data: data.append(extra))  # bad.py already has one E722
    assert _run(seeded, "check", *_scan_arg(seeded)) == 1


def test_check_passes_when_the_same_violations_only_move_lines(seeded):
    def move(data):
        for record in data:
            record["location"]["row"] += 40

    _edit_ruff(seeded, move)
    assert _run(seeded, "check", *_scan_arg(seeded)) == 0


def test_check_reports_a_deleted_source_file_as_gone_not_as_an_invalid_registry(seeded, capsys):
    (seeded / "sample_src" / "nested.py").unlink()
    assert _run(seeded, "check", *_scan_arg(seeded)) == 0
    assert _run(seeded, "validate") == 2  # the validator itself still flags the dead path


def test_delete_command_removes_a_row_and_exits_2_for_a_missing_one(seeded):
    before = len(registry.load_rows(seeded / "reg.jsonl", seeded))
    assert _run(seeded, "delete", "sample_src/bad.py", "ruff", "E722") == 0
    assert len(registry.load_rows(seeded / "reg.jsonl", seeded)) == before - 1
    assert _run(seeded, "delete", "sample_src/bad.py", "ruff", "E722") == 2


def test_seed_refuses_to_overwrite_without_force(seeded):
    assert _run(seeded, "seed", *_scan_arg(seeded)) == 2
    assert _run(seeded, "seed", *_scan_arg(seeded), "--force") == 0


def test_tighten_command_lowers_a_ceiling_without_confirmation(seeded):
    # Duplicate one finding first so the seed has a count of 2, then drop one: lowered, not deleted.
    _edit_ruff(seeded, lambda data: data.append(dict(data[0])))
    assert _run(seeded, "seed", *_scan_arg(seeded), "--force") == 0
    _edit_ruff(seeded, lambda data: data.pop())
    assert _run(seeded, "tighten", *_scan_arg(seeded)) == 0
    assert _run(seeded, "check", *_scan_arg(seeded)) == 0


def test_tighten_refuses_to_delete_rows_without_yes_and_writes_nothing(seeded, capsys):
    before = (seeded / "reg.jsonl").read_text()
    (seeded / "scan" / "ruff.json").write_text("[]")  # a partial scan: every ruff row looks gone
    assert _run(seeded, "tighten", *_scan_arg(seeded)) == 2
    assert (seeded / "reg.jsonl").read_text() == before
    assert "refusing" in capsys.readouterr().err
    assert _run(seeded, "tighten", *_scan_arg(seeded), "--yes") == 0
    assert (seeded / "reg.jsonl").read_text() != before


def test_reseed_keeps_review_data_for_keys_that_persist(seeded):
    path = seeded / "reg.jsonl"
    rows = registry.load_rows(path, seeded, check_files=False)
    marked = rows[0]
    edited = [replace(marked, reviewed=True, retiring_ticket="TCK-20260101-X", added_date="2026-01-01"), *rows[1:]]
    registry.write_rows(path, edited)
    assert _run(seeded, "seed", *_scan_arg(seeded), "--force") == 0
    after = {r.key: r for r in registry.load_rows(path, seeded, check_files=False)}
    kept = after[marked.key]
    assert (kept.reviewed, kept.retiring_ticket, kept.added_date) == (True, "TCK-20260101-X", "2026-01-01")
    assert all(r.reviewed is False for key, r in after.items() if key != marked.key)


def test_list_validate_and_unusable_inputs(seeded, capsys):
    assert _run(seeded, "validate") == 0
    capsys.readouterr()
    assert _run(seeded, "list", "--tool", "jscpd") == 0
    assert "jscpd" in capsys.readouterr().out
    assert _run(seeded, "check", "--from", str(seeded / "nowhere")) == 2


# ── Configuration and hygiene ─────────────────────────────────────────────────


def test_code_health_make_target_runs_the_ratchet_and_is_phony():
    makefile = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^\.PHONY:.*\bcode-health\b", makefile, re.M)
    recipe = re.search(r"^code-health:.*\n((?:\t.*\n)+)", makefile, re.M)
    assert recipe and "codebase.health check" in recipe.group(1)


def test_jscpd_pin_is_read_from_the_makefile_and_the_complexity_limit_from_pyproject():
    assert re.fullmatch(r"\d+\.\d+\.\d+", scan.jscpd_version(_REPO_ROOT / "Makefile"))
    assert scan.complexity_limit(_REPO_ROOT / "pyproject.toml") == 15


def test_code_health_package_uses_package_imports_only():
    for path in (_REPO_ROOT / "tools" / "code_health").glob("*.py"):
        assert "sys.path" not in path.read_text(encoding="utf-8"), path


def test_row_dataclass_is_frozen():
    row = replace(_rows([_f("a.py", "X", 1)])[0], value=2)
    assert row.value == 2
    with pytest.raises(AttributeError):
        setattr(row, "value", 3)
