"""Tests for the package registry and its validator (TCK-20261004-PACKAGE-REGISTRY-VALIDATOR).

What asserts what: the real-repo test checks ONLY that the committed file loads and has no `schema`
problem. It never checks completeness against the live tree: this module runs in the tools-a-e job,
which is not advisory, so a completeness check here would fail the PR of any domain that adds a top-level
`src/` package, skipping the soak. Both completeness checks are tested in scratch-repo fixtures only.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from codebase.structure import packages
from codebase.structure.packages import (
    COMPLETENESS,
    SCHEMA,
    RegistryError,
    validate_file,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _row(package: str, **over: object) -> dict:
    row = {
        "package": package, "purpose": f"{package} purpose", "layer": "domain", "status": "active",
        "strictness_tier": "baseline", "exemplar_modules": [], "do_not_imitate": [], "system": None,
        "audit_decision": "keep", "added_date": "2026-10-04", "reviewed": False,
    }
    row.update(over)
    return row


def _scratch(tmp_path: Path, rows: list[dict], pkgs: tuple[str, ...] = ("alpha", "beta"), git: bool = True) -> Path:
    for name in pkgs:
        (tmp_path / "src" / name).mkdir(parents=True)
        (tmp_path / "src" / name / "mod.py").write_text("x = 1\n")
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries" / "system_registry.jsonl").write_text(json.dumps({"system": "combat"}) + "\n")
    reg = tmp_path / packages.REGISTRY_REL_PATH
    reg.parent.mkdir(parents=True)
    reg.write_text("".join(json.dumps(r) + "\n" for r in rows))
    if git:
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    return tmp_path


def _problems(root: Path, kinds=(SCHEMA, COMPLETENESS)) -> list[str]:
    return [str(p) for p in validate_file(packages.registry_path(root), root, kinds)]


def _clean(tmp_path: Path) -> Path:
    return _scratch(tmp_path, [_row("alpha"), _row("beta")])


# ── Real repository: schema only ──────────────────────────────────────────────


def test_committed_registry_loads_and_is_schema_valid():
    rows = packages.load_rows(packages.registry_path(), _REPO_ROOT, (SCHEMA,))
    assert rows
    assert [r["package"] for r in rows] == sorted({r["package"] for r in rows})


# ── Scratch repositories ──────────────────────────────────────────────────────


def test_clean_scratch_repo_has_no_problems(tmp_path):
    assert _problems(_clean(tmp_path)) == []


def test_exemplars_do_not_imitate_and_system_accepted(tmp_path):
    root = _scratch(tmp_path, [
        _row("alpha", exemplar_modules=["src/alpha/mod.py"], system="combat",
             do_not_imitate=[{"path": "src/alpha/mod.py", "reason": "too long"}]),
        _row("beta", audit_decision="merge-candidate into alpha", status="legacy"),
    ])
    assert _problems(root) == []


@pytest.mark.parametrize("change, fragment", [
    ({"surprise": 1}, "unknown field 'surprise'"),
    ({"layer": "nowhere"}, "field 'layer'"),
    ({"status": "dead"}, "field 'status'"),
    ({"strictness_tier": "gold"}, "field 'strictness_tier'"),
    ({"reviewed": "no"}, "field 'reviewed'"),
    ({"added_date": "yesterday"}, "ISO date"),
    ({"audit_decision": "delete"}, "field 'audit_decision'"),
    ({"audit_decision": "merge-candidate into ghost"}, "merge target has no row"),
    ({"system": "ghost"}, "names no row"),
    ({"exemplar_modules": ["src/alpha/nope.py"]}, "cited path does not exist"),
    ({"exemplar_modules": ["a", "b", "c", "d"]}, "at most 3"),
    ({"do_not_imitate": [{"path": "src/alpha/nope.py", "reason": "r"}]}, "cited path does not exist"),
    ({"do_not_imitate": [{"path": "src/alpha/mod.py"}]}, "{path, reason}"),
])
def test_schema_defects_are_reported_as_schema(tmp_path, change, fragment):
    root = _scratch(tmp_path, [_row("alpha", **change), _row("beta")])
    found = validate_file(packages.registry_path(root), root)
    assert any(p.kind == SCHEMA and fragment in p.message for p in found), [str(p) for p in found]
    assert not [p for p in found if p.kind == COMPLETENESS]


def test_missing_required_field(tmp_path):
    bad = _row("alpha")
    del bad["purpose"]
    root = _scratch(tmp_path, [bad, _row("beta")])
    assert any("missing required field 'purpose'" in p for p in _problems(root))


def test_duplicate_package_and_bad_json(tmp_path):
    root = _scratch(tmp_path, [_row("alpha"), _row("alpha"), _row("beta")])
    reg = packages.registry_path(root)
    reg.write_text(reg.read_text() + "{not json\n")
    found = _problems(root)
    assert any("duplicate package 'alpha'" in p for p in found)
    assert any("not valid JSON" in p for p in found)


def test_tracked_package_without_a_row_is_completeness(tmp_path):
    root = _scratch(tmp_path, [_row("alpha")])
    found = validate_file(packages.registry_path(root), root)
    assert [(p.kind, p.message) for p in found] == [(COMPLETENESS, "tracked top-level package has no row: src/beta")]


def test_row_for_a_missing_package_is_completeness(tmp_path):
    root = _scratch(tmp_path, [_row("alpha"), _row("beta"), _row("ghost")])
    found = validate_file(packages.registry_path(root), root)
    assert [p.kind for p in found] == [COMPLETENESS]
    assert "ghost" in found[0].message


def test_untracked_directory_is_not_a_package(tmp_path):
    root = _clean(tmp_path)
    (root / "src" / "clutter").mkdir()
    (root / "src" / "clutter" / "x.py").write_text("y = 2\n")
    assert _problems(root) == []


def test_kinds_filter_separates_the_classes(tmp_path):
    root = _scratch(tmp_path, [_row("alpha")])
    assert _problems(root, (SCHEMA,)) == []
    assert len(_problems(root, (COMPLETENESS,))) == 1


def test_non_git_root_falls_back_to_directories(tmp_path):
    root = _scratch(tmp_path, [_row("alpha")], git=False)
    assert [p for p in _problems(root) if "src/beta" in p]


def test_load_rows_raises_with_the_problems(tmp_path):
    root = _scratch(tmp_path, [_row("alpha", layer="nowhere"), _row("beta")])
    with pytest.raises(RegistryError) as exc:
        packages.load_rows(packages.registry_path(root), root)
    assert any(p.kind == SCHEMA for p in exc.value.problems)


# ── CLI ───────────────────────────────────────────────────────────────────────


def test_cli_exit_codes(tmp_path, capsys):
    root = _scratch(tmp_path, [_row("alpha")])
    assert packages.main(["validate", "--root", str(root)]) == 1
    assert "src/beta" in capsys.readouterr().out
    assert packages.main(["validate", "--root", str(root), "--schema-only"]) == 0
    reg = packages.registry_path(root)
    reg.write_text(reg.read_text() + json.dumps(_row("beta")) + "\n")
    assert packages.main(["validate", "--root", str(root)]) == 0


# ── CI wiring ─────────────────────────────────────────────────────────────────


def test_ci_step_is_advisory_in_the_code_health_job():
    workflow = yaml.safe_load((_REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["code-health"]["steps"]
    step = next(s for s in steps if s.get("name") == "Package registry")
    assert step["run"] == "python3 -m codebase.structure.packages validate"
    assert step["continue-on-error"] is True
