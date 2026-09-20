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

from tools.mechanism_registry.mechanism_registry_changed_code_check import (
    check_drift,
    check_replacements,
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
