"""TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY: report-only Proof Plan presence check."""

import inspect
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from gate_checks import done_checker_static as dcs  # noqa: E402
from gate_checks.proof_plan_advisory import MANDATORY_FIELDS, check_proof_plan_fields  # noqa: E402

TID = "TCK-20990101-EXAMPLE"

FULL_TABLE = """# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | invariant | ch03 §1; TOWN-122 | conserved | `pytest tests/x.py` |
| 2 | unit | regression | oracle: unresolved | no drift | `pytest tests/y.py` |

## Scoped Pytest Commands
x
"""


def _plan(tmp_path, text, where="staging"):
    root = tmp_path / ("staging_artifacts" if where == "staging" else "stored_artifacts") / TID
    root.mkdir(parents=True)
    (root / "test_plan.md").write_text(text, encoding="utf-8")
    return dict(staging_dir=tmp_path / "staging_artifacts", stored_dir=tmp_path / "stored_artifacts")


def test_complete_table_is_ok_including_oracle_unresolved(tmp_path):
    status, ev = check_proof_plan_fields(TID, "standard", **_plan(tmp_path, FULL_TABLE))
    assert status == "OK", ev


def test_stored_artifacts_location_is_read_after_migration(tmp_path):
    status, _ = check_proof_plan_fields(TID, "standard", **_plan(tmp_path, FULL_TABLE, where="stored"))
    assert status == "OK"


def test_missing_cell_and_missing_column_are_named_per_criterion(tmp_path):
    text = FULL_TABLE.replace("| ch03 §1; TOWN-122 |", "|  |")
    status, ev = check_proof_plan_fields(TID, "standard", **_plan(tmp_path, text))
    assert status == "WARN"
    assert "AC 1: missing oracle source" in ev
    assert "AC 2" not in ev

    no_col = "## Proof Plan\n| AC | level | proof kind |\n|---|---|---|\n| 1 | unit | invariant |\n"
    tmp2 = tmp_path / "b"
    tmp2.mkdir()
    status, ev = check_proof_plan_fields(TID, "standard", **_plan(tmp2, no_col))
    assert status == "WARN"
    for f in ("oracle source", "expected effect", "selected commands"):
        assert f in ev
    assert "missing level" not in ev and ", level" not in ev  # the level column exists


def test_ac_block_layout(tmp_path):
    ok = (
        "## Proof Plan\n### AC1\n- **level**: unit\n- **proof kind**: invariant\n"
        "- **oracle source**: ch03 §1; TOWN-122\n- **expected effect**: conserved\n"
        "- **selected commands**: `pytest tests/x.py`\n"
    )
    assert check_proof_plan_fields(TID, "standard", **_plan(tmp_path, ok))[0] == "OK"
    bad = ok.replace("- **expected effect**: conserved\n", "")
    tmp2 = tmp_path / "b"
    tmp2.mkdir()
    status, ev = check_proof_plan_fields(TID, "standard", **_plan(tmp2, bad))
    assert status == "WARN" and "AC1: missing expected effect" in ev


def test_no_testable_criterion_one_line_is_ok(tmp_path):
    text = "## Proof Plan\nNo testable acceptance criterion: pure agent-prose change.\n"
    status, ev = check_proof_plan_fields(TID, "standard", **_plan(tmp_path, text))
    assert status == "OK" and "no testable" in ev


def test_missing_section_and_missing_file_warn_not_raise(tmp_path):
    status, ev = check_proof_plan_fields(TID, "standard", **_plan(tmp_path, "# Test Plan\n\n## Other\nx\n"))
    assert status == "WARN"
    assert all(f in ev for f in MANDATORY_FIELDS)
    status, ev = check_proof_plan_fields("TCK-20990101-ABSENT", "standard", staging_dir=tmp_path / "s", stored_dir=tmp_path / "t")
    assert status == "WARN" and "no test_plan.md" in ev


@pytest.mark.parametrize("tier", ["hotfix", "epic"])
def test_non_standard_tiers_are_not_applicable(tmp_path, tier):
    assert check_proof_plan_fields(TID, tier, staging_dir=tmp_path, stored_dir=tmp_path)[0] == "NA"


def test_disposition_closure_is_not_applicable(tmp_path):
    done = tmp_path / "tickets" / "done"
    done.mkdir(parents=True)
    (done / f"{TID}.md").write_text("# t\n\n## Disposition\nSUPERSEDED\n", encoding="utf-8")
    status, ev = check_proof_plan_fields(
        TID, "standard", staging_dir=tmp_path / "s", stored_dir=tmp_path / "t", tickets_dir=tmp_path / "tickets"
    )
    assert status == "NA" and "Disposition" in ev


def test_check_is_read_only(tmp_path):
    kw = _plan(tmp_path, FULL_TABLE.replace("| ch03 §1; TOWN-122 |", "|  |"))
    path = tmp_path / "staging_artifacts" / TID / "test_plan.md"
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    check_proof_plan_fields(TID, "standard", **kw)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_unreadable_plan_degrades_to_warn(tmp_path):
    root = tmp_path / "staging_artifacts" / TID
    root.mkdir(parents=True)
    (root / "test_plan.md").write_bytes(b"\xff\xfe\x00bad")
    status, ev = check_proof_plan_fields(TID, "standard", staging_dir=tmp_path / "staging_artifacts", stored_dir=tmp_path / "x")
    assert status == "WARN" and "could not evaluate" in ev


def test_advisory_never_enters_precheck_or_exit_code(tmp_path, monkeypatch, capsys):
    # The precheck list keeps its PASS/FAIL/NA vocabulary and exactly its existing conditions.
    assert "test_plan_proof_fields" not in inspect.getsource(dcs.run_static_precheck)
    assert "test_plan_proof_fields" not in inspect.getsource(dcs.run_finalize_selfcheck)
    monkeypatch.setattr(
        dcs, "run_advisory_checks",
        lambda t, tier: [{"condition": "test_plan_proof_fields", "status": "WARN", "evidence": "missing x"}],
    )
    monkeypatch.setattr(dcs, "run_finalize_selfcheck", lambda *a, **k: [])
    rc = dcs.main(["--ticket-id", TID, "--tier", "standard", "--part", "finalize"])
    out = capsys.readouterr().out
    assert "[advisory] test_plan_proof_fields: WARN" in out
    assert rc == 0 and "RESULT: PASS" in out


def test_field_list_matches_investigator_prose():
    text = (REPO / ".claude/agents/investigator.md").read_text(encoding="utf-8")
    section = text.split("## Proof Plan", 1)[1].split("\n## ", 1)[0]
    mandatory = section.split("Mandatory per criterion:", 1)[1].split("Optional", 1)[0]
    names = set(re.findall(r"^- \*\*([^*]+)\*\*", mandatory, re.MULTILINE))
    assert names == set(MANDATORY_FIELDS)
