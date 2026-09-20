"""Tests for tools/mechanism_registry/mechanism_registry_changed_code_check.py.

TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION. Flags a diff that changes
`implemented_by`-cited code without touching the citing mechanism's own registry entry --
the mechanical version of the parity ledger's own decayed "update your entry when behavior
changes" rule.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import tools.mechanism_registry.mechanism_registry_changed_code_check as changed_code_check
from tools.mechanism_registry.mechanism_registry_changed_code_check import (
    check_drift,
    check_drift_for_ticket,
    check_replacements,
    get_changed_files_for_ticket,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _registry(mechanisms):
    return {"mechanisms": mechanisms}


# ---------------------------------------------------------------------------
# check_drift -- the core AC #3 controls
# ---------------------------------------------------------------------------


def test_negative_control_flags_code_changed_with_no_registry_change():
    """AC #3's own synthetic negative control: a changed cited file with no registry change at
    all -- the detector WOULD flag this."""
    old_data = _registry([
        {"id": "foo", "implemented_by": ["src/foo.py::FooSystem"], "state": "done"},
    ])
    new_data = old_data  # identical -- registry untouched in this diff
    changed_files = {"src/foo.py"}

    findings = check_drift(old_data, new_data, changed_files)

    assert len(findings) == 1
    assert findings[0].mechanism_id == "foo"
    assert findings[0].changed_cited_files == ["src/foo.py"]


def test_positive_control_does_not_flag_when_entry_changed_too():
    """AC #3's own positive control: code changed AND the mechanism's own entry changed in the
    same diff (state, verified, or implemented_by itself) -- the detector would NOT flag this,
    since the entry was kept in sync with the code, which is exactly the discipline this detector
    exists to check for."""
    old_data = _registry([
        {"id": "foo", "implemented_by": ["src/foo.py::FooSystem"], "state": "partial"},
    ])
    new_data = _registry([
        {"id": "foo", "implemented_by": ["src/foo.py::FooSystem"], "state": "done"},
    ])
    changed_files = {"src/foo.py"}

    findings = check_drift(old_data, new_data, changed_files)

    assert findings == []


def test_no_finding_when_cited_file_not_in_changed_set():
    old_data = _registry([{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"]}])
    new_data = old_data
    findings = check_drift(old_data, new_data, {"src/unrelated.py"})
    assert findings == []


def test_no_finding_for_mechanism_with_no_implemented_by():
    old_data = _registry([{"id": "foo", "state": "gap"}])
    new_data = old_data
    findings = check_drift(old_data, new_data, {"src/foo.py"})
    assert findings == []


def test_symbol_suffix_stripped_before_matching_changed_files():
    """implemented_by entries are `path::Symbol` -- only the path half should match a changed
    file path, never the symbol."""
    old_data = _registry([{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"]}])
    new_data = old_data
    findings = check_drift(old_data, new_data, {"src/foo.py"})
    assert len(findings) == 1
    assert findings[0].changed_cited_files == ["src/foo.py"]


def test_multiple_cited_files_only_changed_ones_reported():
    old_data = _registry([{
        "id": "foo",
        "implemented_by": ["src/foo.py::A", "src/bar.py::B", "src/baz.py::C"],
    }])
    new_data = old_data
    findings = check_drift(old_data, new_data, {"src/foo.py", "src/baz.py"})
    assert len(findings) == 1
    assert findings[0].changed_cited_files == ["src/baz.py", "src/foo.py"]


# ---------------------------------------------------------------------------
# check_replacements
# ---------------------------------------------------------------------------


def test_replacement_detected_when_implemented_by_points_elsewhere():
    old_data = _registry([{"id": "foo", "implemented_by": ["src/old.py::Old"]}])
    new_data = _registry([{"id": "foo", "implemented_by": ["src/new.py::New"]}])

    findings = check_replacements(old_data, new_data)

    assert len(findings) == 1
    assert findings[0].mechanism_id == "foo"
    assert findings[0].old_implemented_by == ["src/old.py::Old"]
    assert findings[0].new_implemented_by == ["src/new.py::New"]


def test_first_binding_is_not_a_replacement():
    """A mechanism going from no implemented_by to a real one is a first binding, not a
    replacement -- the signal this reports is specifically about an EXISTING citation being
    overwritten, the shape of this session's own real trauma misattribution incident."""
    old_data = _registry([{"id": "foo", "state": "done"}])  # no implemented_by at all
    new_data = _registry([{"id": "foo", "state": "done", "implemented_by": ["src/new.py::New"]}])

    findings = check_replacements(old_data, new_data)

    assert findings == []


def test_unchanged_implemented_by_is_not_a_replacement():
    old_data = _registry([{"id": "foo", "implemented_by": ["src/foo.py::Foo"]}])
    new_data = old_data
    assert check_replacements(old_data, new_data) == []


# ---------------------------------------------------------------------------
# report-only guarantee + CLI
# ---------------------------------------------------------------------------


def test_main_always_exits_zero():
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry/mechanism_registry_changed_code_check.py",
         "--base", "HEAD", "--head", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_make_target_runs_clean():
    result = subprocess.run(
        ["make", "mechanism-registry-changed-code-check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_unresolvable_base_ref_reports_skipped_not_a_crash():
    """A base ref that doesn't exist (e.g. a shallow CI checkout missing origin/main) should
    report SKIPPED and still exit 0 -- report-only means never crashing the build either."""
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry/mechanism_registry_changed_code_check.py",
         "--base", "definitely-not-a-real-ref-xyz"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "SKIPPED" in result.stdout


# ---------------------------------------------------------------------------
# check_drift_for_ticket / get_changed_files_for_ticket -- close-time, ticket-scoped mode
# (TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE)
#
# Uses a disposable temp git repo (never this repo's own history) with `_REPO_ROOT` monkeypatched
# for the call's duration, so planted commits never touch real state.
# ---------------------------------------------------------------------------


def _init_temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "src").mkdir()
    (repo / "registries").mkdir()
    return repo


def _write_registry(repo: Path, mechanisms: list) -> None:
    import yaml
    with open(repo / "registries" / "mechanisms.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump({"mechanisms": mechanisms}, f)


def _commit(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@test.com",
         "commit", "-q", "-m", message],
        cwd=repo, check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _in_temp_repo(monkeypatch, repo: Path):
    monkeypatch.setattr(changed_code_check, "_REPO_ROOT", repo)


def test_planted_drift_case_fires(tmp_path, monkeypatch):
    repo = _init_temp_repo(tmp_path)
    (repo / "src" / "foo.py").write_text("v1\n")
    _write_registry(repo, [{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"]}])
    base_sha = _commit(repo, "base: seed registry and foo.py")

    (repo / "src" / "foo.py").write_text("v2 -- behavior changed\n")
    _commit(repo, "TCK-FAKE-PLANTED-DRIFT: change foo.py without updating its mechanism entry")

    _in_temp_repo(monkeypatch, repo)
    drift, replacements = check_drift_for_ticket("TCK-FAKE-PLANTED-DRIFT", base_ref=base_sha)

    assert len(drift) == 1
    assert drift[0].mechanism_id == "foo"
    assert drift[0].changed_cited_files == ["src/foo.py"]
    assert replacements == []


def test_planted_no_drift_case_is_silent(tmp_path, monkeypatch):
    repo = _init_temp_repo(tmp_path)
    (repo / "src" / "foo.py").write_text("v1\n")
    _write_registry(repo, [{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"], "state": "partial"}])
    base_sha = _commit(repo, "base: seed registry and foo.py")

    (repo / "src" / "foo.py").write_text("v2 -- behavior changed\n")
    _write_registry(repo, [{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"], "state": "done"}])
    _commit(repo, "TCK-FAKE-PLANTED-NO-DRIFT: change foo.py and update its mechanism entry too")

    _in_temp_repo(monkeypatch, repo)
    drift, replacements = check_drift_for_ticket("TCK-FAKE-PLANTED-NO-DRIFT", base_ref=base_sha)

    assert drift == []
    assert replacements == []


def test_uncommitted_working_tree_changes_are_detected(tmp_path, monkeypatch):
    """A hand-orchestrated closer running this before their own final commit must still see
    drift -- the mechanism cannot be defeated by check-before-commit ordering."""
    repo = _init_temp_repo(tmp_path)
    (repo / "src" / "foo.py").write_text("v1\n")
    _write_registry(repo, [{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"]}])
    base_sha = _commit(repo, "base: seed registry and foo.py")

    (repo / "src" / "foo.py").write_text("v2 -- uncommitted change\n")  # never committed

    _in_temp_repo(monkeypatch, repo)
    changed = get_changed_files_for_ticket("TCK-FAKE-NEVER-COMMITTED", base_ref=base_sha)
    assert "src/foo.py" in changed

    drift, _ = check_drift_for_ticket("TCK-FAKE-NEVER-COMMITTED", base_ref=base_sha)
    assert len(drift) == 1
    assert drift[0].mechanism_id == "foo"


def test_cross_ticket_contamination_avoided(tmp_path, monkeypatch):
    """A second, unrelated ticket's commit on the same branch must not bleed into this ticket's
    own changed_files -- the whole reason a branch-wide diff was rejected as the definition."""
    repo = _init_temp_repo(tmp_path)
    (repo / "src" / "foo.py").write_text("v1\n")
    (repo / "src" / "bar.py").write_text("v1\n")
    _write_registry(repo, [
        {"id": "foo", "implemented_by": ["src/foo.py::FooSystem"]},
        {"id": "bar", "implemented_by": ["src/bar.py::BarSystem"]},
    ])
    base_sha = _commit(repo, "base: seed registry, foo.py, bar.py")

    (repo / "src" / "foo.py").write_text("v2\n")
    _commit(repo, "TCK-FAKE-MINE: change foo.py")

    (repo / "src" / "bar.py").write_text("v2\n")
    _commit(repo, "TCK-FAKE-OTHER: change bar.py -- unrelated ticket, same branch")

    _in_temp_repo(monkeypatch, repo)
    changed = get_changed_files_for_ticket("TCK-FAKE-MINE", base_ref=base_sha)
    assert "src/foo.py" in changed
    assert "src/bar.py" not in changed


def test_ticket_id_cli_path_never_fails_even_with_findings(tmp_path, monkeypatch, capsys):
    repo = _init_temp_repo(tmp_path)
    (repo / "src" / "foo.py").write_text("v1\n")
    _write_registry(repo, [{"id": "foo", "implemented_by": ["src/foo.py::FooSystem"]}])
    base_sha = _commit(repo, "base: seed registry and foo.py")

    (repo / "src" / "foo.py").write_text("v2\n")
    _commit(repo, "TCK-FAKE-CLI-PATH: change foo.py")

    _in_temp_repo(monkeypatch, repo)
    exit_code = main(["--ticket-id", "TCK-FAKE-CLI-PATH", "--base", base_sha])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "1 drift finding(s)" in out
    assert "foo" in out
