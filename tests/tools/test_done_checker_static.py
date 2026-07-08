"""Tests for tools/gate_checks/done_checker_static.py (TCK-20260705-GATE-DET-DONE-CHECKER).

Coverage-honesty requirement (SEQUENCE.md decision 4): every check function below has at least
one fixture proving it catches a real violation it claims to catch, not just that it runs on the
happy path.
"""

import csv
import os
import sys
import time
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.done_checker_static import (  # noqa: E402
    _find_flagged_data_run_files,
    check_data_runs_clean,
    check_frontmatter_valid,
    check_migration_complete,
    check_staging_artifacts_complete,
    check_ticket_finalized,
    check_ticket_location,
    check_working_log_exactly_one_row,
    check_working_log_no_row_yet,
    classify_checklist_failure,
    clean_data_runs_early,
    run_finalize_selfcheck,
    run_static_precheck,
)

TICKET_FM = """---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: {ticket_id}
phase: open
date: 2026-07-05
tags: []
---

# {ticket_id}

## Title
Fixture ticket

## Tier
{tier}
"""

ARTIFACT_FM = """---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: {ticket_id}
artifact_type: {artifact_type}
tags: []
---

# {artifact_type}

Some content.
"""


def _write_ticket(path: Path, ticket_id: str, tier: str = "standard") -> None:
    path.write_text(TICKET_FM.format(ticket_id=ticket_id, tier=tier), encoding="utf-8")


def _write_artifact_dir(directory: Path, ticket_id: str, filenames=("plan.md", "investigation.md", "test_plan.md")) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    artifact_type_map = {"plan.md": "plan", "investigation.md": "investigation", "test_plan.md": "test_plan"}
    for name in filenames:
        (directory / name).write_text(
            ARTIFACT_FM.format(ticket_id=ticket_id, artifact_type=artifact_type_map[name]),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# check_staging_artifacts_complete
# ---------------------------------------------------------------------------


def test_staging_artifacts_missing_file_fails_naming_it(tmp_path):
    base = tmp_path / "staging_artifacts"
    directory = base / "TCK-FAKE"
    directory.mkdir(parents=True)
    (directory / "plan.md").write_text("plan content", encoding="utf-8")
    (directory / "investigation.md").write_text("investigation content", encoding="utf-8")
    # test_plan.md intentionally omitted

    status, evidence = check_staging_artifacts_complete("TCK-FAKE", "standard", base_dir=base)
    assert status == "FAIL"
    assert "test_plan.md" in evidence


def test_staging_artifacts_empty_file_fails(tmp_path):
    base = tmp_path / "staging_artifacts"
    directory = base / "TCK-FAKE"
    directory.mkdir(parents=True)
    (directory / "plan.md").write_text("plan content", encoding="utf-8")
    (directory / "investigation.md").write_text("investigation content", encoding="utf-8")
    (directory / "test_plan.md").write_text("   \n", encoding="utf-8")  # whitespace-only

    status, evidence = check_staging_artifacts_complete("TCK-FAKE", "standard", base_dir=base)
    assert status == "FAIL"
    assert "test_plan.md" in evidence


def test_staging_artifacts_all_present_passes(tmp_path):
    base = tmp_path / "staging_artifacts"
    directory = base / "TCK-FAKE"
    _write_artifact_dir(directory, "TCK-FAKE")

    status, _ = check_staging_artifacts_complete("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_staging_artifacts_hotfix_is_na_regardless_of_missing_directory(tmp_path):
    base = tmp_path / "staging_artifacts"  # directory does not even exist

    status, evidence = check_staging_artifacts_complete("TCK-FAKE", "hotfix", base_dir=base)
    assert status == "NA"
    assert status != "PASS"


# ---------------------------------------------------------------------------
# check_data_runs_clean
# ---------------------------------------------------------------------------


def test_data_runs_clean_empty_dirs_passes(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    status, _ = check_data_runs_clean("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "PASS"


def test_data_runs_clean_file_before_start_ts_passes(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leftover = runs_dir / "old_run.json"
    leftover.write_text("{}", encoding="utf-8")
    # Set mtime to well before start_ts.
    old_epoch = time.mktime(time.strptime("2026-07-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leftover, (old_epoch, old_epoch))

    status, _ = check_data_runs_clean("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "PASS"


def test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leaked = runs_dir / "leaked_run.json"
    leaked.write_text("{}", encoding="utf-8")
    new_epoch = time.mktime(time.strptime("2026-07-06T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leaked, (new_epoch, new_epoch))

    status, evidence = check_data_runs_clean("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "FAIL"
    assert str(leaked) in evidence


def test_data_runs_clean_unparsable_start_ts_flags_any_file(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    old = runs_dir / "old_run.json"
    old.write_text("{}", encoding="utf-8")
    old_epoch = time.mktime(time.strptime("2020-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(old, (old_epoch, old_epoch))

    status, _ = check_data_runs_clean(None, runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "FAIL"


# ---------------------------------------------------------------------------
# clean_data_runs_early (TCK-20260708-DATA-RUNS-CLEANUP-TIMING)
# ---------------------------------------------------------------------------


def test_clean_data_runs_early_detects_and_removes_leftover_artifacts(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leaked = runs_dir / "leaked_run.json"
    leaked.write_text("{}", encoding="utf-8")
    new_epoch = time.mktime(time.strptime("2026-07-06T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leaked, (new_epoch, new_epoch))

    status, evidence = clean_data_runs_early("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "CLEANED"
    assert str(leaked) in evidence
    assert not leaked.exists()

    followup_status, _ = check_data_runs_clean("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert followup_status == "PASS"


def test_clean_data_runs_early_preserves_files_older_than_start_ts(tmp_path):
    """Mirrors test_data_runs_clean_file_before_start_ts_passes exactly — this is the
    earlier-started-session safety guard test_plan.md calls "not optional."

    Note: this test covers only the mtime-lower-bound guarantee (earlier start_ts); it does not
    and cannot exercise the concurrent-overlap case where another session is still actively
    writing at the moment this checkpoint fires — see "Residual Risk: Concurrent-Session Overlap
    Window" in plan.md.
    """
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leftover = runs_dir / "old_run.json"
    leftover.write_text("{}", encoding="utf-8")
    old_epoch = time.mktime(time.strptime("2026-07-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leftover, (old_epoch, old_epoch))

    status, _ = clean_data_runs_early("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "PASS"
    assert leftover.exists()


def test_clean_data_runs_early_reuses_check_data_runs_clean_definition(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    before = runs_dir / "before.json"
    before.write_text("{}", encoding="utf-8")
    before_epoch = time.mktime(time.strptime("2026-07-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(before, (before_epoch, before_epoch))

    at_start = runs_dir / "at_start.json"
    at_start.write_text("{}", encoding="utf-8")
    at_epoch = time.mktime(time.strptime("2026-07-06T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(at_start, (at_epoch, at_epoch))

    after = proof_dir / "after.json"
    after.write_text("{}", encoding="utf-8")
    after_epoch = time.mktime(time.strptime("2026-07-07T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(after, (after_epoch, after_epoch))

    start_ts = "2026-07-05T00:00:00Z"
    canonical_flagged = {str(f) for f in _find_flagged_data_run_files(start_ts, runs_dir, proof_dir)}
    assert canonical_flagged == {str(at_start), str(after)}

    check_status, check_evidence = check_data_runs_clean(start_ts, runs_dir=runs_dir, proof_dir=proof_dir)
    assert check_status == "FAIL"
    for f in canonical_flagged:
        assert f in check_evidence

    clean_status, clean_evidence = clean_data_runs_early(start_ts, runs_dir=runs_dir, proof_dir=proof_dir)
    assert clean_status == "CLEANED"
    for f in canonical_flagged:
        assert f in clean_evidence
    assert before.exists()
    assert not at_start.exists()
    assert not after.exists()


def test_clean_data_runs_early_returns_fail_on_deletion_error(tmp_path, monkeypatch):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leaked = runs_dir / "leaked_run.json"
    leaked.write_text("{}", encoding="utf-8")
    new_epoch = time.mktime(time.strptime("2026-07-06T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leaked, (new_epoch, new_epoch))

    def _raise_unlink(self):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "unlink", _raise_unlink)

    status, evidence = clean_data_runs_early("2026-07-05T00:00:00Z", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "FAIL"
    assert "permission denied" in evidence
    assert str(leaked) in evidence


def test_data_runs_clean_status_appears_in_failure_recovery_reference_table():
    doc_path = Path(__file__).parent.parent.parent / "docs" / "ai" / "ticket-lifecycle.md"
    content = doc_path.read_text(encoding="utf-8")
    assert "DATA_RUNS_CLEAN_FAILED" in content


# ---------------------------------------------------------------------------
# check_ticket_location
# ---------------------------------------------------------------------------


def test_ticket_location_present_passes(tmp_path):
    inprogress = tmp_path / "tickets" / "inprogress"
    inprogress.mkdir(parents=True)
    _write_ticket(inprogress / "TCK-FAKE.md", "TCK-FAKE")

    status, _ = check_ticket_location("TCK-FAKE", inprogress_dir=inprogress)
    assert status == "PASS"


def test_ticket_location_absent_fails(tmp_path):
    inprogress = tmp_path / "tickets" / "inprogress"
    inprogress.mkdir(parents=True)

    status, evidence = check_ticket_location("TCK-FAKE", inprogress_dir=inprogress)
    assert status == "FAIL"
    assert "TCK-FAKE.md" in evidence


# ---------------------------------------------------------------------------
# check_working_log_no_row_yet / check_working_log_exactly_one_row
# ---------------------------------------------------------------------------


def _write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "ticket_id", "title", "status", "summary", "artifacts_path"])
        for row in rows:
            writer.writerow(row)


def test_working_log_no_row_yet_passes_when_absent(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [["2026-07-01T00:00:00Z", "TCK-OTHER", "Other", "DONE", "x", "stored_artifacts/TCK-OTHER"]])

    status, _ = check_working_log_no_row_yet("TCK-FAKE", csv_path=csv_path)
    assert status == "PASS"


def test_working_log_no_row_yet_fails_with_duplicate_wording(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"]])

    status, evidence = check_working_log_no_row_yet("TCK-FAKE", csv_path=csv_path)
    assert status == "FAIL"
    assert "pre-existing row at Verify time" in evidence
    assert "duplicate/re-run" in evidence


def test_working_log_no_row_yet_detects_malformed_column_order(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    # Malformed row: ticket_id shifted into column 1 (timestamp's slot), per
    # TCK-20260705-WORKING-LOG-BACKFILL's Reason A finding.
    _write_csv(csv_path, [["TCK-FAKE", "2026-07-01", "standard", "bug", "x", "stored_artifacts/TCK-FAKE"]])

    status, _ = check_working_log_no_row_yet("TCK-FAKE", csv_path=csv_path)
    assert status == "FAIL"


def test_working_log_exactly_one_row_zero_case_fails(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [])

    status, evidence = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path)
    assert status == "FAIL"
    assert "no working_log row found" in evidence


def test_working_log_exactly_one_row_duplicate_case_fails_distinct_wording(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [
        ["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"],
        ["2026-07-02T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"],
    ])

    status, evidence = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path)
    assert status == "FAIL"
    assert "duplicate Finalize run" in evidence
    assert "no working_log row found" not in evidence


def test_working_log_exactly_one_row_passes(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"]])

    status, _ = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path)
    assert status == "PASS"


# ---------------------------------------------------------------------------
# check_frontmatter_valid
# ---------------------------------------------------------------------------


def test_frontmatter_valid_ticket_and_artifacts_pass(tmp_path):
    ticket_path = tmp_path / "TCK-FAKE.md"
    _write_ticket(ticket_path, "TCK-FAKE")

    staging_dir = tmp_path / "staging_artifacts" / "TCK-FAKE"
    _write_artifact_dir(staging_dir, "TCK-FAKE")

    status, _ = check_frontmatter_valid("TCK-FAKE", "standard", ticket_path=ticket_path, staging_dir=staging_dir)
    assert status == "PASS"


def test_frontmatter_valid_fails_when_artifact_missing_required_field(tmp_path):
    ticket_path = tmp_path / "TCK-FAKE.md"
    _write_ticket(ticket_path, "TCK-FAKE")

    staging_dir = tmp_path / "staging_artifacts" / "TCK-FAKE"
    staging_dir.mkdir(parents=True)
    (staging_dir / "plan.md").write_text(
        ARTIFACT_FM.format(ticket_id="TCK-FAKE", artifact_type="plan"), encoding="utf-8"
    )
    (staging_dir / "investigation.md").write_text(
        ARTIFACT_FM.format(ticket_id="TCK-FAKE", artifact_type="investigation"), encoding="utf-8"
    )
    # test_plan.md satisfies `doc`'s schema (status/layer/authority/audience) but omits
    # ticket_id/artifact_type, required by `artifact`'s schema. If check_frontmatter_valid forgot
    # to pass content_type_override="artifact", this would silently fall through to `doc` and
    # incorrectly PASS.
    (staging_dir / "test_plan.md").write_text(
        """---
status: historical
layer: ai
authority: P2
audience: agent
tags: []
---

# test_plan

Some content.
""",
        encoding="utf-8",
    )

    status, evidence = check_frontmatter_valid(
        "TCK-FAKE", "standard", ticket_path=ticket_path, staging_dir=staging_dir
    )
    assert status == "FAIL"
    assert "artifact_type" in evidence or "ticket_id" in evidence


# ---------------------------------------------------------------------------
# run_static_precheck (aggregate)
# ---------------------------------------------------------------------------


def _scaffold_precheck_repo(tmp_path, ticket_id="TCK-FAKE", tier="standard"):
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "inprogress" / f"{ticket_id}.md", ticket_id, tier=tier)

    staging_dir = tmp_path / "staging_artifacts" / ticket_id
    _write_artifact_dir(staging_dir, ticket_id)

    (tmp_path / "data" / "runs").mkdir(parents=True)
    (tmp_path / "reports" / "release_proof").mkdir(parents=True)

    csv_path = tmp_path / "tickets" / "working_log.csv"
    _write_csv(csv_path, [])


def test_run_static_precheck_all_pass_eligible(tmp_path, monkeypatch):
    _scaffold_precheck_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    assert len(results) == 5
    statuses = {r["condition"]: r["status"] for r in results}
    assert all(s in ("PASS", "NA") for s in statuses.values()), statuses


def test_run_static_precheck_surfaces_fail_not_masked(tmp_path, monkeypatch):
    _scaffold_precheck_repo(tmp_path)
    # Break one check: pre-existing working_log row for this ticket.
    csv_path = tmp_path / "tickets" / "working_log.csv"
    _write_csv(csv_path, [["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"]])
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["working_log_no_row_yet"]["status"] == "FAIL"
    # Other checks still present and not swallowed by the one FAIL.
    assert by_condition["ticket_location"]["status"] == "PASS"


# ---------------------------------------------------------------------------
# classify_checklist_failure (TCK-20260706-MONITORING-REASON-CODE)
# ---------------------------------------------------------------------------


def test_classify_checklist_failure_all_pass_returns_none():
    checklist = [
        {"condition": "ticket_location", "status": "PASS", "evidence": "ok"},
        {"condition": "staging_artifacts_complete", "status": "NA", "evidence": "hotfix — n/a"},
    ]
    assert classify_checklist_failure(checklist) is None


def test_classify_checklist_failure_tag_registry_rejection():
    checklist = [
        {"condition": "ticket_location", "status": "PASS", "evidence": "ok"},
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": "tickets/inprogress/TCK-FAKE.md: tags: 'some-tag' is not in the tag registry — register it first",
        },
    ]
    assert classify_checklist_failure(checklist) == "tag_registry_rejection"


def test_classify_checklist_failure_generic_dod_failure():
    checklist = [
        {"condition": "working_log_no_row_yet", "status": "FAIL", "evidence": "duplicate row found"},
    ]
    assert classify_checklist_failure(checklist) == "dod_condition_failed"


def test_classify_checklist_failure_scans_past_leading_pass_entries():
    checklist = [
        {"condition": "ticket_location", "status": "PASS", "evidence": "ok"},
        {"condition": "data_runs_clean", "status": "PASS", "evidence": "ok"},
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": "tags: 'foo' is not in the tag registry",
        },
    ]
    assert classify_checklist_failure(checklist) == "tag_registry_rejection"


def test_classify_checklist_failure_returns_first_fail_when_multiple():
    checklist = [
        {"condition": "working_log_no_row_yet", "status": "FAIL", "evidence": "duplicate row"},
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": "tags: 'foo' is not in the tag registry",
        },
    ]
    # First FAIL wins — documented tie-break, not left ambiguous.
    assert classify_checklist_failure(checklist) == "dod_condition_failed"


# ---------------------------------------------------------------------------
# check_migration_complete
# ---------------------------------------------------------------------------


def test_migration_complete_hotfix_is_na(tmp_path):
    status, _ = check_migration_complete(
        "TCK-FAKE", "hotfix",
        staging_dir=tmp_path / "staging_artifacts" / "TCK-FAKE",
        stored_dir=tmp_path / "stored_artifacts" / "TCK-FAKE",
    )
    assert status == "NA"


def test_migration_complete_all_pass(tmp_path):
    stored_dir = tmp_path / "stored_artifacts" / "TCK-FAKE"
    _write_artifact_dir(stored_dir, "TCK-FAKE")
    staging_dir = tmp_path / "staging_artifacts" / "TCK-FAKE"  # absent

    status, _ = check_migration_complete("TCK-FAKE", "standard", staging_dir=staging_dir, stored_dir=stored_dir)
    assert status == "PASS"


def test_migration_complete_missing_file_fails_naming_it(tmp_path):
    stored_dir = tmp_path / "stored_artifacts" / "TCK-FAKE"
    _write_artifact_dir(stored_dir, "TCK-FAKE", filenames=("investigation.md", "test_plan.md"))
    staging_dir = tmp_path / "staging_artifacts" / "TCK-FAKE"

    status, evidence = check_migration_complete("TCK-FAKE", "standard", staging_dir=staging_dir, stored_dir=stored_dir)
    assert status == "FAIL"
    assert "plan.md" in evidence


def test_migration_complete_staging_not_cleaned_fails(tmp_path):
    stored_dir = tmp_path / "stored_artifacts" / "TCK-FAKE"
    _write_artifact_dir(stored_dir, "TCK-FAKE")
    staging_dir = tmp_path / "staging_artifacts" / "TCK-FAKE"
    _write_artifact_dir(staging_dir, "TCK-FAKE")  # still present alongside complete stored_dir

    status, evidence = check_migration_complete("TCK-FAKE", "standard", staging_dir=staging_dir, stored_dir=stored_dir)
    assert status == "FAIL"
    assert "not cleaned" in evidence


# ---------------------------------------------------------------------------
# check_ticket_finalized
# ---------------------------------------------------------------------------


def test_ticket_finalized_passes(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, _ = check_ticket_finalized("TCK-FAKE")
    assert status == "PASS"


def test_ticket_finalized_fails_when_still_in_inprogress(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    _write_ticket(tmp_path / "tickets" / "inprogress" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_ticket_finalized("TCK-FAKE")
    assert status == "FAIL"
    assert "still exists" in evidence


def test_ticket_finalized_fails_when_not_moved_to_done(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    status, evidence = check_ticket_finalized("TCK-FAKE")
    assert status == "FAIL"
    assert "does not exist" in evidence


# ---------------------------------------------------------------------------
# run_finalize_selfcheck (aggregate)
# ---------------------------------------------------------------------------


def _scaffold_finalize_repo(tmp_path, ticket_id="TCK-FAKE"):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / f"{ticket_id}.md", ticket_id)

    stored_dir = tmp_path / "stored_artifacts" / ticket_id
    _write_artifact_dir(stored_dir, ticket_id)

    csv_path = tmp_path / "tickets" / "working_log.csv"
    _write_csv(csv_path, [["2026-07-05T00:00:00Z", ticket_id, "Fake", "DONE", "x", f"stored_artifacts/{ticket_id}"]])


def test_run_finalize_selfcheck_all_pass(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    assert len(results) == 3
    assert all(r["status"] == "PASS" for r in results), results


def test_run_finalize_selfcheck_surfaces_incomplete_stored_artifacts(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    # Remove plan.md from stored_artifacts to simulate the 101-case "incomplete" class.
    (tmp_path / "stored_artifacts" / "TCK-FAKE" / "plan.md").unlink()
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["migration_complete"]["status"] == "FAIL"


def test_run_finalize_selfcheck_zero_rows_fails(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    _write_csv(tmp_path / "tickets" / "working_log.csv", [])
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["working_log_exactly_one_row"]["status"] == "FAIL"


def test_run_finalize_selfcheck_duplicate_rows_fails(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    _write_csv(tmp_path / "tickets" / "working_log.csv", [
        ["2026-07-05T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"],
        ["2026-07-05T01:00:00Z", "TCK-FAKE", "Fake", "DONE", "x", "stored_artifacts/TCK-FAKE"],
    ])
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["working_log_exactly_one_row"]["status"] == "FAIL"
