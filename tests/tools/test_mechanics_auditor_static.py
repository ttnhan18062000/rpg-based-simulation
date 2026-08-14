"""Tests for tools/gate_checks/mechanics_auditor_static.py (TCK-20260705-GATE-DET-MECHANICS-AUDITOR).

Coverage-honesty requirement: every check function below has at least one fixture proving it
catches a real violation it claims to catch, not just that it runs on the happy path.
"""

import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.mechanics_auditor_static import (  # noqa: E402
    audit_verified_by_claims,
    check_test_path,
    verify_entry_test_path,
)


def _write_ledger(tmp_path, filename, entries):
    (tmp_path / filename).write_text(yaml.safe_dump(entries))


def test_test_path_existence_check_passes_for_real_passing_test(tmp_path):
    (tmp_path / "test_ok_file.py").write_text("def test_ok():\n    assert True\n")

    status, evidence = check_test_path("test_ok_file.py::test_ok", base_dir=tmp_path)

    assert status == "PASS"
    assert "test_ok_file.py::test_ok" in evidence


def test_test_path_existence_check_fails_for_genuinely_failing_test(tmp_path):
    (tmp_path / "test_fail_file.py").write_text(
        "def test_fails():\n    assert 1 == 2, 'custom fail message'\n"
    )

    status, evidence = check_test_path("test_fail_file.py::test_fails", base_dir=tmp_path)

    assert status == "FAIL"
    assert "custom fail message" in evidence


def test_test_path_existence_check_fails_for_nonexistent_file(tmp_path):
    status, evidence = check_test_path("tests/does_not_exist.py::test_x", base_dir=tmp_path)

    assert status == "FAIL"
    assert "does not exist" in evidence
    assert "tests/does_not_exist.py" in evidence


def test_null_test_path_fails_not_crashes():
    status_none, evidence_none = check_test_path(None)
    status_empty, evidence_empty = check_test_path("")

    assert status_none == "FAIL"
    assert "null/missing" in evidence_none
    assert status_empty == "FAIL"
    assert "null/missing" in evidence_empty


def test_backtick_wrapped_test_path_is_parsed(tmp_path):
    (tmp_path / "test_backtick_file.py").write_text("def test_ok():\n    assert True\n")

    status, evidence = check_test_path(
        "`test_backtick_file.py::test_ok`", base_dir=tmp_path
    )

    assert status == "PASS"
    assert "test_backtick_file.py::test_ok" in evidence


def test_legacy_tests_v2_path_fails_cleanly_as_stale(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("subprocess.run must not be called for a tests_v2/ citation")

    monkeypatch.setattr("gate_checks.mechanics_auditor_static.subprocess.run", _boom)

    status, evidence = check_test_path("tests_v2/test_old.py::test_x", base_dir=tmp_path)

    assert status == "FAIL"
    assert "tests_v2" in evidence
    assert "does not exist" in evidence


def test_parenthetical_annotation_suffix_is_unparseable_and_fails_gracefully(tmp_path):
    raw = "`tests/tools/test_x.py` (indirectly via `Y` and `Z` flow)"

    status, evidence = check_test_path(raw, base_dir=tmp_path)

    assert status == "FAIL"
    assert raw in evidence


def test_multi_citation_test_path_policy(tmp_path):
    (tmp_path / "a.py").write_text("def test_pass():\n    assert True\n")
    (tmp_path / "b.py").write_text("def test_fail():\n    assert False\n")

    status, evidence = check_test_path("a.py::test_pass, b.py::test_fail", base_dir=tmp_path)

    assert status == "FAIL"
    assert "a.py::test_pass" in evidence
    assert "b.py::test_fail" in evidence


def test_check_is_scoped_not_full_suite(tmp_path, monkeypatch):
    (tmp_path / "scoped_file.py").write_text("def test_ok():\n    assert True\n")

    captured = {}

    def _fake_run(args, **kwargs):
        captured["args"] = args

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Result()

    monkeypatch.setattr("gate_checks.mechanics_auditor_static.subprocess.run", _fake_run)

    check_test_path("scoped_file.py::test_ok", base_dir=tmp_path)

    assert "scoped_file.py::test_ok" in captured["args"]
    assert "tests/" not in captured["args"]


def test_verified_by_field_present_and_shaped_correctly(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": None,
        },
    ])

    result = verify_entry_test_path("CM-001", ledger_dir=tmp_path, base_dir=tmp_path)

    assert result["verified_by"] == ["static:mechanics_auditor_static"]


def test_scoped_by_entry_id_not_whole_ledger(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "A-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
        {
            "id": "A-002", "text": "y", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/bar.py", "test_path": "tests/does_not_exist.py::test_bar",
        },
        {
            "id": "A-003", "text": "z", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/baz.py", "test_path": "tests/unit/test_baz.py",
        },
    ])

    result = verify_entry_test_path("A-002", ledger_dir=tmp_path, base_dir=tmp_path)

    assert result["entry_id"] == "A-002"
    assert "A-001" not in str(result)
    assert "A-003" not in str(result)


def test_audit_passes_honest_static_pass_claim(tmp_path):
    (tmp_path / "test_ok_file.py").write_text("def test_ok():\n    assert True\n")
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "H-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "test_ok_file.py::test_ok",
        },
    ])
    rows = [{
        "entry_id": "H-001",
        "status": "PARITY",
        "verified_by": ["static:mechanics_auditor_static", "llm"],
        "Finding": "matches formula exactly",
    }]

    result = audit_verified_by_claims(rows, ledger_dir=tmp_path, base_dir=tmp_path)

    assert len(result) == 1
    assert result[0]["entry_id"] == "H-001"
    assert result[0]["honesty_status"] == "PASS"


def test_audit_detects_step_0_skipped_on_verified_status_entry(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "S-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])
    rows = [{
        "entry_id": "S-001",
        "status": "PARITY",
        "verified_by": ["llm"],
        "Finding": "matches formula",
    }]

    result = audit_verified_by_claims(rows, ledger_dir=tmp_path, base_dir=tmp_path)

    assert len(result) == 1
    assert result[0]["entry_id"] == "S-001"
    assert result[0]["honesty_status"] == "FAIL"
    assert "skipped" in result[0]["evidence"].lower()


def test_audit_detects_falsely_cited_static_pass(tmp_path):
    (tmp_path / "test_fail_file.py").write_text(
        "def test_fails():\n    assert False\n"
    )
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "F-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "test_fail_file.py::test_fails",
        },
    ])
    rows = [{
        "entry_id": "F-001",
        "status": "PARITY",
        "verified_by": ["static:mechanics_auditor_static", "llm"],
        "Finding": "matches formula exactly",
    }]

    result = audit_verified_by_claims(rows, ledger_dir=tmp_path, base_dir=tmp_path)

    assert len(result) == 1
    assert result[0]["entry_id"] == "F-001"
    assert result[0]["honesty_status"] == "FAIL"
    assert "falsely cited" in result[0]["evidence"].lower()


def test_audit_passes_honest_llm_only_claim_on_non_verified_status_entry(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "N-001", "text": "x", "status": "missing", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": None,
        },
    ])
    rows = [{
        "entry_id": "N-001",
        "status": "MISSING",
        "verified_by": ["llm"],
        "Finding": "no implementation found",
    }]

    result = audit_verified_by_claims(rows, ledger_dir=tmp_path, base_dir=tmp_path)

    assert result == []


def test_audit_scoped_by_row_not_whole_ledger(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "A-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
        {
            "id": "A-002", "text": "y", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/bar.py", "test_path": "tests/does_not_exist.py::test_bar",
        },
        {
            "id": "A-003", "text": "z", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/baz.py", "test_path": "tests/unit/test_baz.py",
        },
    ])
    rows = [{
        "entry_id": "A-002",
        "status": "PARITY",
        "verified_by": ["llm"],
        "Finding": "no static tag cited",
    }]

    result = audit_verified_by_claims(rows, ledger_dir=tmp_path, base_dir=tmp_path)

    assert len(result) <= 1
    assert "A-001" not in str(result)
    assert "A-003" not in str(result)


def test_audit_never_overrides_agent_status_classification(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "K-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])
    rows = [{
        "entry_id": "K-001",
        "status": "PARITY",
        "verified_by": ["llm"],
        "Finding": "matches formula",
    }]

    result = audit_verified_by_claims(rows, ledger_dir=tmp_path, base_dir=tmp_path)

    assert len(result) == 1
    assert "status" not in result[0]
    assert "Status" not in result[0]
    assert set(result[0].keys()) == {"entry_id", "honesty_status", "evidence"}
