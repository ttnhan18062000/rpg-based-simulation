"""Tests for tools/gate_checks/done_checker_static.py (TCK-20260705-GATE-DET-DONE-CHECKER).

Coverage-honesty requirement (SEQUENCE.md decision 4): every check function below has at least
one fixture proving it catches a real violation it claims to catch, not just that it runs on the
happy path.
"""

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.done_checker_static import (  # noqa: E402
    _find_flagged_data_run_files,
    _frontmatter_has_unregistered_tags,
    _git_status_touched_paths,
    _git_ticket_commits_touched_paths,
    _git_touched_paths,
    _parse_docs_to_update,
    _parse_resolved_not_applicable_docs,
    _path_touched,
    check_data_runs_clean,
    check_docs_to_update_coverage,
    check_frontmatter_valid,
    check_migration_complete,
    check_monitoring_write_recorded,
    check_registry_entry_regenerated,
    check_staging_artifacts_complete,
    check_tag_drift,
    check_ticket_finalized,
    check_ticket_location,
    check_working_log_exactly_one_row,
    check_working_log_no_row_yet,
    classify_checklist_failure,
    clean_data_runs_early,
    run_finalize_selfcheck,
    run_static_precheck,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_PROTECTED_PATHS = ["docs/REGISTRY.yaml", "tickets/working_log.csv", "agent-monitoring/data"]


def _protected_paths_git_status() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--"] + _PROTECTED_PATHS,
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture(scope="module", autouse=True)
def _fail_if_this_module_touches_tracked_monitoring_files():
    """Scope 4 regression guard (TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES): every test
    below runs against the real checkout as cwd unless it isolates via tmp_path/monkeypatch.chdir
    -- a missed isolation gap (like the one this ticket fixed in
    test_cli_still_importable_and_callable_as_plain_functions, which called
    run_finalize_selfcheck() with no isolation and so unconditionally regenerated the real
    docs/REGISTRY.yaml) must fail loudly here, not ship silently as a tracked-file diff on the
    next commit. Module-scoped rather than per-test: cheap (one git-status pair for the whole
    file, not ~150), and still catches any test in this module that leaves one of these three
    real paths modified, regardless of which test it was.
    """
    before = _protected_paths_git_status()
    yield
    after = _protected_paths_git_status()
    assert before == after, (
        "a test in this module modified a tracked monitoring file it should not have.\n"
        f"git status before this module's tests:\n{before}\n"
        f"git status after:\n{after}"
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


def test_data_runs_clean_absent_start_ts_no_ticket_context_is_indeterminate(tmp_path):
    """TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS: an absent start_ts with no ticket_id
    to look up a run record is INDETERMINATE, not FAIL — the hand-orchestrated CLI path's original
    bug was reading this identically to a real dirty-repo finding."""
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    old = runs_dir / "old_run.json"
    old.write_text("{}", encoding="utf-8")
    old_epoch = time.mktime(time.strptime("2020-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(old, (old_epoch, old_epoch))

    status, evidence = check_data_runs_clean(None, runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "INDETERMINATE"
    assert "--start-ts" in evidence


def test_data_runs_clean_present_garbage_start_ts_still_flags_any_file(tmp_path):
    """AC4/pipeline fail-closed rule: an explicit-but-unparsable start_ts (not merely absent)
    still flags every file, unchanged from before this ticket."""
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    old = runs_dir / "old_run.json"
    old.write_text("{}", encoding="utf-8")
    old_epoch = time.mktime(time.strptime("2020-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(old, (old_epoch, old_epoch))

    status, _ = check_data_runs_clean("not-a-date", runs_dir=runs_dir, proof_dir=proof_dir)
    assert status == "FAIL"


def test_data_runs_clean_resolves_start_ts_from_own_run_record_pass(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    data_root = tmp_path / "agent-monitoring" / "data"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leftover = runs_dir / "old_run.json"
    leftover.write_text("{}", encoding="utf-8")
    old_epoch = time.mktime(time.strptime("2026-07-01T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leftover, (old_epoch, old_epoch))

    _write_jsonl(
        data_root / "2026-W27" / "runs.jsonl",
        [{"run_id": "TCK-FAKE", "start_ts": "2026-07-05T00:00:00Z"}],
    )

    status, evidence = check_data_runs_clean(
        None, ticket_id="TCK-FAKE", runs_dir=runs_dir, proof_dir=proof_dir, data_root=data_root
    )
    assert status == "PASS"
    assert "run record" in evidence


def test_data_runs_clean_resolves_start_ts_from_own_run_record_fail(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    data_root = tmp_path / "agent-monitoring" / "data"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)

    leaked = runs_dir / "leaked_run.json"
    leaked.write_text("{}", encoding="utf-8")
    new_epoch = time.mktime(time.strptime("2026-07-06T00:00:00", "%Y-%m-%dT%H:%M:%S"))
    os.utime(leaked, (new_epoch, new_epoch))

    _write_jsonl(
        data_root / "2026-W27" / "runs.jsonl",
        [{"run_id": "TCK-FAKE", "start_ts": "2026-07-05T00:00:00Z"}],
    )

    status, evidence = check_data_runs_clean(
        None, ticket_id="TCK-FAKE", runs_dir=runs_dir, proof_dir=proof_dir, data_root=data_root
    )
    assert status == "FAIL"
    assert str(leaked) in evidence


def test_data_runs_clean_ticket_id_with_no_matching_run_record_is_indeterminate(tmp_path):
    runs_dir = tmp_path / "data" / "runs"
    proof_dir = tmp_path / "reports" / "release_proof"
    data_root = tmp_path / "agent-monitoring" / "data"
    runs_dir.mkdir(parents=True)
    proof_dir.mkdir(parents=True)
    _write_jsonl(data_root / "2026-W27" / "runs.jsonl", [{"run_id": "TCK-OTHER", "start_ts": "2026-07-05T00:00:00Z"}])

    status, evidence = check_data_runs_clean(
        None, ticket_id="TCK-FAKE", runs_dir=runs_dir, proof_dir=proof_dir, data_root=data_root
    )
    assert status == "INDETERMINATE"
    assert "--start-ts" in evidence


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


def test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt():
    doc_path = Path(__file__).parent.parent.parent / ".claude" / "agents" / "done-checker.md"
    content = doc_path.read_text(encoding="utf-8")
    assert "clean_data_runs_early" in content
    assert "Step 0a" in content


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


def test_working_log_exactly_one_row_legitimate_reopen_passes(tmp_path):
    # TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN: a ticket
    # legitimately closed BLOCKED, then later reopened and closed DONE, has two real rows with
    # two DIFFERENT statuses -- this must PASS, not read as a duplicate Finalize run.
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [
        ["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "BLOCKED", "investigation complete, pending review", "none"],
        ["2026-07-05T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "reopened and resolved", "stored_artifacts/TCK-FAKE"],
    ])

    status, evidence = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path)
    assert status == "PASS"
    assert "legitimate reopen" in evidence


def test_working_log_exactly_one_row_two_blocked_rows_still_fails(tmp_path):
    # A real duplicate isn't only two DONE rows -- two rows at the SAME non-DONE status (e.g.
    # BLOCKED written twice by an accidental double-run) must still fail as a duplicate.
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [
        ["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "BLOCKED", "x", "none"],
        ["2026-07-02T00:00:00Z", "TCK-FAKE", "Fake", "BLOCKED", "y", "none"],
    ])

    status, evidence = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path)
    assert status == "FAIL"
    assert "duplicate Finalize run" in evidence


def test_working_log_exactly_one_row_three_statuses_no_duplicate_passes(tmp_path):
    # A ticket reopened twice (BLOCKED -> INPROGRESS -> DONE, three genuinely distinct statuses)
    # must still pass -- the check keys on (ticket_id, status), not a hardcoded two-row shape.
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [
        ["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "BLOCKED", "x", "none"],
        ["2026-07-03T00:00:00Z", "TCK-FAKE", "Fake", "INPROGRESS", "y", "none"],
        ["2026-07-05T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "z", "stored_artifacts/TCK-FAKE"],
    ])

    status, _ = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path)
    assert status == "PASS"


# ---------------------------------------------------------------------------
# TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET: these two checks must see a just-staged,
# not-yet-consolidated working_log row at a ticket's own close, without depending on a later
# consolidation run (AC2), and the reopen-vs-duplicate distinction must still hold across a row
# split between the canonical CSV and a pending shard (AC3).
# ---------------------------------------------------------------------------


def _write_working_log_shard(data_root: Path, batch: str, week: str, row: dict) -> None:
    path = data_root / week / f"{batch}.working_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_working_log_no_row_yet_fails_when_row_only_pending_in_shard(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [])
    data_root = tmp_path / "agent-monitoring" / "data"
    _write_working_log_shard(data_root, "some-branch", "2026-W27", {
        "timestamp": "2026-07-01T00:00:00Z", "ticket_id": "TCK-FAKE", "title": "Fake",
        "status": "DONE", "summary": "x", "artifacts_path": "none",
    })

    status, evidence = check_working_log_no_row_yet("TCK-FAKE", csv_path=csv_path, data_root=data_root)
    assert status == "FAIL"
    assert "pending working_log shard" in evidence


def test_working_log_exactly_one_row_passes_via_pending_shard_only(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [])
    data_root = tmp_path / "agent-monitoring" / "data"
    _write_working_log_shard(data_root, "some-branch", "2026-W27", {
        "timestamp": "2026-07-01T00:00:00Z", "ticket_id": "TCK-FAKE", "title": "Fake",
        "status": "DONE", "summary": "x", "artifacts_path": "stored_artifacts/TCK-FAKE",
    })

    status, _ = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path, data_root=data_root)
    assert status == "PASS"


def test_working_log_exactly_one_row_reopen_across_csv_and_pending_shard_passes(tmp_path):
    """AC3: a legitimate reopen where the FIRST close already consolidated (its row is in the
    CSV) and the SECOND close is still pending (not yet consolidated) must still read as a
    reopen, not a duplicate -- the two sources are checked together, not independently."""
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [
        ["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "BLOCKED", "investigation complete", "none"],
    ])
    data_root = tmp_path / "agent-monitoring" / "data"
    _write_working_log_shard(data_root, "some-branch", "2026-W27", {
        "timestamp": "2026-07-05T00:00:00Z", "ticket_id": "TCK-FAKE", "title": "Fake",
        "status": "DONE", "summary": "reopened and resolved", "artifacts_path": "stored_artifacts/TCK-FAKE",
    })

    status, evidence = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path, data_root=data_root)
    assert status == "PASS"
    assert "legitimate reopen" in evidence


def test_working_log_exactly_one_row_duplicate_across_csv_and_pending_shard_fails(tmp_path):
    """The dual-writer duplicate class this check exists to catch, now split across the two
    sources: a DONE row already in the CSV, and a SECOND DONE row for the same ticket still
    pending in a shard -- must still FAIL, exactly as if both were in the same CSV."""
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [
        ["2026-07-01T00:00:00Z", "TCK-FAKE", "Fake", "DONE", "First write.", "stored_artifacts/TCK-FAKE"],
    ])
    data_root = tmp_path / "agent-monitoring" / "data"
    _write_working_log_shard(data_root, "some-branch", "2026-W27", {
        "timestamp": "2026-07-01T00:05:00Z", "ticket_id": "TCK-FAKE", "title": "Fake",
        "status": "DONE", "summary": "Second write.", "artifacts_path": "stored_artifacts/TCK-FAKE",
    })

    status, evidence = check_working_log_exactly_one_row("TCK-FAKE", csv_path=csv_path, data_root=data_root)
    assert status == "FAIL"
    assert "duplicate Finalize run" in evidence


def test_working_log_no_row_yet_ignores_pending_shard_for_a_different_ticket(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    _write_csv(csv_path, [])
    data_root = tmp_path / "agent-monitoring" / "data"
    _write_working_log_shard(data_root, "some-branch", "2026-W27", {
        "timestamp": "2026-07-01T00:00:00Z", "ticket_id": "TCK-OTHER", "title": "Other",
        "status": "DONE", "summary": "x", "artifacts_path": "none",
    })

    status, _ = check_working_log_no_row_yet("TCK-FAKE", csv_path=csv_path, data_root=data_root)
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


def test_check_frontmatter_valid_fails_on_unregistered_tag(tmp_path):
    # TCK-20260720-TAG-TOUCHPOINT-CLEANUP: proves the pre-existing enforcement gap is closed —
    # check_frontmatter_valid must now thread a real registry through validate_file/
    # validate_directory so an unregistered tag actually produces FAIL, not a silent PASS.
    # ticket_id must embed a date >= TAG_TAXONOMY_EFFECTIVE_DATE (20260704) — "TCK-FAKE" (used by
    # every other fixture in this file) has no embedded date and is exempt from tag checking
    # entirely, which would make this test pass for the wrong reason. The path must also contain
    # a "tickets" component — detect_content_type() only resolves to the "ticket" schema (the one
    # that actually calls _check_tags) when "tickets" is in path.parts; every other
    # check_frontmatter_valid fixture in this file places ticket_path directly under tmp_path,
    # which resolves to "doc" instead and never exercises tag validation at all.
    ticket_id = "TCK-20260731-FAKE"
    ticket_path = tmp_path / "tickets" / "inprogress" / f"{ticket_id}.md"
    ticket_path.parent.mkdir(parents=True)
    ticket_path.write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier="standard").replace(
            "tags: []", "tags: [totally-unregistered-test-tag-xyz]"
        ),
        encoding="utf-8",
    )
    staging_dir = tmp_path / "staging_artifacts" / ticket_id
    _write_artifact_dir(staging_dir, ticket_id)

    status, evidence = check_frontmatter_valid(
        ticket_id, "standard", ticket_path=ticket_path, staging_dir=staging_dir
    )
    assert status == "FAIL"
    assert "totally-unregistered-test-tag-xyz" in evidence
    assert "is not in the tag registry" in evidence


# ---------------------------------------------------------------------------
# _frontmatter_has_unregistered_tags
# ---------------------------------------------------------------------------

# These tests call check_tags_registered() against the real, live registries/tag_registry.jsonl
# (load_registry() has no test-fixture hook — it always resolves to the repo root regardless of
# cwd, mirroring validate_frontmatter.py::main()'s own real-registry-only usage). "cognition"/
# "world" are confirmed-stable seed tags (registered 2026-07-06, append-only registry); the
# unregistered-tag fixtures use an invented name guaranteed not to collide with any real entry.


def test_frontmatter_has_unregistered_tags_detects_real_violation(tmp_path):
    ticket_id = "TCK-FAKE"
    ticket_path = tmp_path / f"{ticket_id}.md"
    ticket_path.write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier="standard").replace(
            "tags: []", "tags: [totally-unregistered-test-tag-xyz]"
        ),
        encoding="utf-8",
    )
    staging_dir = tmp_path / "staging_artifacts" / ticket_id

    assert _frontmatter_has_unregistered_tags(
        ticket_id, "standard", ticket_path=ticket_path, staging_dir=staging_dir
    ) is True


def test_frontmatter_has_unregistered_tags_false_when_all_registered(tmp_path):
    ticket_id = "TCK-FAKE"
    ticket_path = tmp_path / f"{ticket_id}.md"
    ticket_path.write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier="standard").replace(
            "tags: []", "tags: [cognition, world]"
        ),
        encoding="utf-8",
    )
    staging_dir = tmp_path / "staging_artifacts" / ticket_id

    assert _frontmatter_has_unregistered_tags(
        ticket_id, "standard", ticket_path=ticket_path, staging_dir=staging_dir
    ) is False


def test_frontmatter_has_unregistered_tags_checks_staging_artifacts_too(tmp_path):
    ticket_id = "TCK-FAKE"
    ticket_path = tmp_path / f"{ticket_id}.md"
    ticket_path.write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier="standard").replace(
            "tags: []", "tags: [cognition]"
        ),
        encoding="utf-8",
    )
    staging_dir = tmp_path / "staging_artifacts" / ticket_id
    staging_dir.mkdir(parents=True)
    (staging_dir / "plan.md").write_text(
        ARTIFACT_FM.format(ticket_id=ticket_id, artifact_type="plan").replace(
            "tags: []", "tags: [totally-unregistered-test-tag-xyz]"
        ),
        encoding="utf-8",
    )

    assert _frontmatter_has_unregistered_tags(
        ticket_id, "standard", ticket_path=ticket_path, staging_dir=staging_dir
    ) is True


def test_frontmatter_has_unregistered_tags_hotfix_skips_staging_dir(tmp_path):
    ticket_id = "TCK-FAKE"
    ticket_path = tmp_path / f"{ticket_id}.md"
    ticket_path.write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier="hotfix").replace(
            "tags: []", "tags: [cognition]"
        ),
        encoding="utf-8",
    )
    # staging_dir deliberately not created — a hotfix ticket has none. If the helper didn't skip
    # it correctly, `.rglob()` on a nonexistent dir would either error or (if implemented wrong)
    # silently miss the branch guard; asserting False here proves the hotfix-skip path runs.
    staging_dir = tmp_path / "staging_artifacts" / ticket_id

    assert _frontmatter_has_unregistered_tags(
        ticket_id, "hotfix", ticket_path=ticket_path, staging_dir=staging_dir
    ) is False


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
    # 8 conditions as of TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK
    # (was 7, added temporal_week_consistency; was 6, added docs_to_update_coverage
    # per TCK-20260802-DOC-COVERAGE-CHECK; was 5, added ticket_field_values_valid
    # per TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM; was 5 originally: 5->6->7->8).
    assert len(results) == 8
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


def test_run_static_precheck_blocks_on_bad_priority(tmp_path, monkeypatch):
    # TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM: a ticket cannot reach READY_TO_CLOSE with a
    # non-canonical body ## Priority — proven here at the same run_static_precheck level the real
    # Verify-phase gate reads from, mirroring test_run_static_precheck_surfaces_fail_not_masked's
    # own pattern for a different condition.
    _scaffold_precheck_repo(tmp_path)
    ticket_path = tmp_path / "tickets" / "inprogress" / "TCK-FAKE.md"
    ticket_path.write_text(
        ticket_path.read_text().rstrip() + "\n\n## Priority\nP1: High\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["ticket_field_values_valid"]["status"] == "FAIL"
    assert "P1: High" in by_condition["ticket_field_values_valid"]["evidence"]
    # Other checks still present and not swallowed by the one FAIL.
    assert by_condition["ticket_location"]["status"] == "PASS"


def test_run_static_precheck_passes_valid_priority(tmp_path, monkeypatch):
    _scaffold_precheck_repo(tmp_path)
    ticket_path = tmp_path / "tickets" / "inprogress" / "TCK-FAKE.md"
    ticket_path.write_text(
        ticket_path.read_text().rstrip() + "\n\n## Priority\nP1\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["ticket_field_values_valid"]["status"] == "PASS"


def test_done_checker_new_check_wired_and_returns_pass_with_evidence(tmp_path, monkeypatch):
    # TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK: the new 8th Part A
    # check must be present, must always PASS (report-only, never blocks a ticket
    # close), and must degrade gracefully against a fixture repo that creates no
    # agent-monitoring/data/ directory at all — mirroring
    # verify_referential_integrity.py's own load_all_weeks() precedent (an empty
    # glob, not an exception, for a missing data_dir).
    _scaffold_precheck_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    assert len(results) == 8
    by_condition = {r["condition"]: r for r in results}
    assert "temporal_week_consistency" in by_condition
    assert by_condition["temporal_week_consistency"]["status"] == "PASS"
    assert by_condition["temporal_week_consistency"]["evidence"]  # non-trivial evidence string


# ---------------------------------------------------------------------------
# classify_checklist_failure (TCK-20260706-MONITORING-REASON-CODE)
# ---------------------------------------------------------------------------


def test_classify_checklist_failure_all_pass_returns_none():
    checklist = [
        {"condition": "ticket_location", "status": "PASS", "evidence": "ok"},
        {"condition": "staging_artifacts_complete", "status": "NA", "evidence": "hotfix — n/a"},
    ]
    assert classify_checklist_failure(checklist) is None


def _write_tag_rejection_fixture(tmp_path, ticket_id="TCK-FAKE", tier="standard"):
    """Real on-disk ticket (+ staging artifacts, for non-hotfix tiers) whose `tags:` frontmatter
    includes an unregistered tag — the fixture `classify_checklist_failure`'s independent
    `_frontmatter_has_unregistered_tags` re-check now reads, replacing the old evidence-text
    marker match."""
    ticket_dir = tmp_path / "tickets" / "inprogress"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / f"{ticket_id}.md").write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier=tier).replace(
            "tags: []", "tags: [totally-unregistered-test-tag-xyz]"
        ),
        encoding="utf-8",
    )
    staging_dir = tmp_path / "staging_artifacts" / ticket_id
    _write_artifact_dir(staging_dir, ticket_id)


def test_classify_checklist_failure_tag_registry_rejection(tmp_path, monkeypatch):
    _write_tag_rejection_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    checklist = [
        {"condition": "ticket_location", "status": "PASS", "evidence": "ok"},
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": "tickets/inprogress/TCK-FAKE.md: tags: 'totally-unregistered-test-tag-xyz' "
            "is not in the tag registry — register it first",
        },
    ]
    assert classify_checklist_failure(checklist, ticket_id="TCK-FAKE", tier="standard") == "tag_registry_rejection"


def test_classify_checklist_failure_generic_dod_failure():
    checklist = [
        {"condition": "working_log_no_row_yet", "status": "FAIL", "evidence": "duplicate row found"},
    ]
    assert classify_checklist_failure(checklist) == "dod_condition_failed"


def test_classify_checklist_failure_scans_past_leading_pass_entries(tmp_path, monkeypatch):
    _write_tag_rejection_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    checklist = [
        {"condition": "ticket_location", "status": "PASS", "evidence": "ok"},
        {"condition": "data_runs_clean", "status": "PASS", "evidence": "ok"},
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": "tags: 'totally-unregistered-test-tag-xyz' is not in the tag registry",
        },
    ]
    assert classify_checklist_failure(checklist, ticket_id="TCK-FAKE", tier="standard") == "tag_registry_rejection"


def test_classify_checklist_failure_returns_first_fail_when_multiple():
    checklist = [
        {"condition": "working_log_no_row_yet", "status": "FAIL", "evidence": "duplicate row"},
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": "tags: 'foo' is not in the tag registry",
        },
    ]
    # First FAIL wins — documented tie-break, not left ambiguous. Called with no ticket_id/tier
    # too, proving the backward-compatible default path never even reaches the tag re-check.
    assert classify_checklist_failure(checklist) == "dod_condition_failed"


def test_classify_checklist_failure_condition_key_used_not_evidence_text(tmp_path, monkeypatch):
    # Anti-drift guard: a fixture ticket whose real tags are all registered, but whose evidence
    # text happens to contain the literal old marker string as an unrelated quoted example — must
    # NOT trigger tag_registry_rejection. Proves classification keys off `condition` + an
    # independent registry re-check, never off evidence text content.
    ticket_id = "TCK-FAKE"
    ticket_dir = tmp_path / "tickets" / "inprogress"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / f"{ticket_id}.md").write_text(
        TICKET_FM.format(ticket_id=ticket_id, tier="standard").replace(
            "tags: []", "tags: [cognition]"
        ),
        encoding="utf-8",
    )
    staging_dir = tmp_path / "staging_artifacts" / ticket_id
    _write_artifact_dir(staging_dir, ticket_id)
    monkeypatch.chdir(tmp_path)

    checklist = [
        {
            "condition": "frontmatter_valid",
            "status": "FAIL",
            "evidence": 'unrelated failure — note: some other tag once said "is not in the tag registry" as an example',
        },
    ]
    assert classify_checklist_failure(checklist, ticket_id=ticket_id, tier="standard") == "dod_condition_failed"


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


def test_migration_complete_epic_is_na(tmp_path):
    """TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP: epic tier gets the same NA
    treatment as hotfix -- no real epic ticket, flat or folder-closed, has ever had its own
    stored_artifacts/{ticket_id}/; an epic's investigation/plan/test_plan work belongs to its
    child tickets, not the epic ticket itself."""
    status, _ = check_migration_complete(
        "TCK-FAKE", "epic",
        staging_dir=tmp_path / "staging_artifacts" / "TCK-FAKE",
        stored_dir=tmp_path / "stored_artifacts" / "TCK-FAKE",
    )
    assert status == "NA"


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


def test_ticket_finalized_passes_for_folder_closed_epic(tmp_path, monkeypatch):
    """TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP: an epic ticket closed via
    CLAUDE.md's own folder-move rule lives at tickets/done/{folder}/{ticket_id}.md, one level
    deep -- must PASS, not FAIL on a flat-path-only check."""
    (tmp_path / "tickets" / "done" / "some-epic").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "some-epic" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_ticket_finalized("TCK-FAKE")
    assert status == "PASS"
    assert "some-epic" in evidence


def test_ticket_finalized_prefers_flat_path_over_nested_if_both_exist(tmp_path, monkeypatch):
    # Should never happen in practice (a ticket can't close at two locations at once), but the
    # flat path is the common case and should win deterministically if it somehow does.
    (tmp_path / "tickets" / "done" / "some-epic").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    _write_ticket(tmp_path / "tickets" / "done" / "some-epic" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_ticket_finalized("TCK-FAKE")
    assert status == "PASS"
    assert evidence.startswith("tickets/done/TCK-FAKE.md")


def test_ticket_finalized_still_fails_when_folder_nested_but_also_in_inprogress(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done" / "some-epic").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "some-epic" / "TCK-FAKE.md", "TCK-FAKE")
    _write_ticket(tmp_path / "tickets" / "inprogress" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_ticket_finalized("TCK-FAKE")
    assert status == "FAIL"
    assert "still exists" in evidence


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


def test_run_finalize_selfcheck_leaves_a_pending_shard_and_canonical_file_untouched(tmp_path, monkeypatch):
    """AC2 (TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES): a pending per-branch shard
    present alongside the canonical tools.jsonl must survive a real run_finalize_selfcheck() call
    byte-identical — neither file is this function's business. Written after confirming by direct
    source read that done_checker_static.py never calls monitoring_consolidation's
    consolidate_*() anywhere (grep for "consolidat" in the module: only docstring prose, no call
    sites) — the shard-consolidation symptom test-architecture-implementer originally reported
    against the full `pytest tests/` run traces to generate_retro.py's generate() (which does
    unconditionally call consolidate_all() with no data_dir override), not to this file. Filed as
    a sibling ticket rather than folded into this one's scope. This test still pins the correct,
    literal AC2 behavior for done_checker_static.py itself, which was already correct — it just
    was never verified isolated-and-explicit before.
    """
    _scaffold_finalize_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    data_dir = tmp_path / "agent-monitoring" / "data"
    canonical_tools = data_dir / "tools.jsonl"
    canonical_tools.parent.mkdir(parents=True, exist_ok=True)
    canonical_tools.write_text('{"session_id":"real","tool":"Bash"}\n', encoding="utf-8")
    pending_shard = data_dir / "some-other-branch.tools.jsonl"
    pending_shard.write_text('{"session_id":"pending","tool":"Read"}\n', encoding="utf-8")
    canonical_before = canonical_tools.read_bytes()
    shard_before = pending_shard.read_bytes()

    run_finalize_selfcheck("TCK-FAKE", "standard")

    assert canonical_tools.read_bytes() == canonical_before
    assert pending_shard.exists(), "the pending shard must not be deleted"
    assert pending_shard.read_bytes() == shard_before


def test_run_finalize_selfcheck_all_pass(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    assert len(results) == 4
    assert all(r["status"] == "PASS" for r in results), results


def test_run_finalize_selfcheck_surfaces_missing_registry_entry(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    (tmp_path / "tickets" / "done" / "TCK-FAKE.md").unlink()
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["registry_entry_regenerated"]["status"] == "FAIL"


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


# ---------------------------------------------------------------------------
# check_monitoring_write_recorded
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""), encoding="utf-8")


def test_check_monitoring_write_recorded_fails_when_run_missing(tmp_path):
    runs_path = tmp_path / "2026-W23" / "runs.jsonl"
    events_path = tmp_path / "2026-W23" / "events.jsonl"
    _write_jsonl(runs_path, [{"run_id": "TCK-OTHER"}])
    _write_jsonl(events_path, [{"run_id": "TCK-OTHER"}])

    status, evidence = check_monitoring_write_recorded("TCK-FAKE", data_root=tmp_path)
    assert status == "FAIL"
    assert "No row with run_id == TCK-FAKE" in evidence


def test_check_monitoring_write_recorded_fails_when_events_missing(tmp_path):
    runs_path = tmp_path / "2026-W23" / "runs.jsonl"
    events_path = tmp_path / "2026-W23" / "events.jsonl"
    _write_jsonl(runs_path, [{"run_id": "TCK-FAKE"}])
    _write_jsonl(events_path, [{"run_id": "TCK-OTHER"}])

    status, evidence = check_monitoring_write_recorded("TCK-FAKE", data_root=tmp_path)
    assert status == "FAIL"
    assert "zero matching rows" in evidence


def test_check_monitoring_write_recorded_passes_when_both_present(tmp_path):
    runs_path = tmp_path / "2026-W23" / "runs.jsonl"
    events_path = tmp_path / "2026-W23" / "events.jsonl"
    _write_jsonl(runs_path, [{"run_id": "TCK-FAKE"}])
    _write_jsonl(events_path, [{"run_id": "TCK-FAKE"}, {"run_id": "TCK-FAKE"}])

    status, evidence = check_monitoring_write_recorded("TCK-FAKE", data_root=tmp_path)
    assert status == "PASS"
    assert "TCK-FAKE" in evidence


def test_check_monitoring_write_recorded_applies_under_hotfix_tier(tmp_path):
    # The function takes no `tier` argument at all — this documents and locks in that it
    # cannot special-case hotfix, per CLAUDE.md's Hard Rule ("including hotfix").
    runs_path = tmp_path / "2026-W23" / "runs.jsonl"
    events_path = tmp_path / "2026-W23" / "events.jsonl"
    _write_jsonl(runs_path, [])
    _write_jsonl(events_path, [])

    status, _ = check_monitoring_write_recorded("TCK-HOTFIX-FAKE", data_root=tmp_path)
    assert status == "FAIL"

    _write_jsonl(runs_path, [{"run_id": "TCK-HOTFIX-FAKE"}])
    _write_jsonl(events_path, [{"run_id": "TCK-HOTFIX-FAKE"}])
    status, _ = check_monitoring_write_recorded("TCK-HOTFIX-FAKE", data_root=tmp_path)
    assert status == "PASS"


def test_check_monitoring_write_recorded_finds_pair_in_non_current_week(tmp_path):
    old_week = tmp_path / "2026-W23"
    _write_jsonl(old_week / "runs.jsonl", [{"run_id": "TCK-OLD-WEEK"}])
    _write_jsonl(old_week / "events.jsonl", [{"run_id": "TCK-OLD-WEEK"}])
    # A newer, unrelated week folder must not be required or interfered with.
    new_week = tmp_path / "2026-W36"
    _write_jsonl(new_week / "runs.jsonl", [{"run_id": "TCK-OTHER"}])
    _write_jsonl(new_week / "events.jsonl", [{"run_id": "TCK-OTHER"}])

    status, evidence = check_monitoring_write_recorded("TCK-OLD-WEEK", data_root=tmp_path)
    assert status == "PASS"
    assert "TCK-OLD-WEEK" in evidence


def test_check_monitoring_write_recorded_still_fails_when_absent_from_all_weeks(tmp_path):
    _write_jsonl(tmp_path / "2026-W23" / "runs.jsonl", [{"run_id": "TCK-OTHER-1"}])
    _write_jsonl(tmp_path / "2026-W36" / "runs.jsonl", [{"run_id": "TCK-OTHER-2"}])

    status, evidence = check_monitoring_write_recorded("TCK-NOWHERE", data_root=tmp_path)
    assert status == "FAIL"
    assert "No row with run_id == TCK-NOWHERE" in evidence


# ---------------------------------------------------------------------------
# check_tag_drift
# ---------------------------------------------------------------------------

_DRIFT_TICKET_TEMPLATE = """---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: {ticket_id}
phase: open
date: 2026-07-31
tags: {tags}
---

# {ticket_id}

## Title
Fixture ticket

## Files Changed
{files_changed}

## Related Code Areas
{related_code_areas}

## Completion Summary
"""


def _write_drift_ticket(path: Path, ticket_id: str, tags, files_changed="", related_code_areas=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _DRIFT_TICKET_TEMPLATE.format(
            ticket_id=ticket_id,
            tags=tags,
            files_changed=files_changed,
            related_code_areas=related_code_areas,
        ),
        encoding="utf-8",
    )


def test_check_tag_drift_flags_mismatch(tmp_path):
    # "dashboard" is a real, live-registered subsystem-topic tag (registries/tag_registry.jsonl).
    ticket_path = tmp_path / "TCK-FAKE.md"
    _write_drift_ticket(
        ticket_path,
        "TCK-FAKE",
        tags="[workflows]",
        files_changed="- src/api/agent_ops_dashboard/routes.py",
    )

    status, evidence = check_tag_drift("TCK-FAKE", ticket_path=ticket_path)
    assert status == "FLAGGED"
    assert "dashboard" in evidence


def test_check_tag_drift_clean_when_tags_cover_candidates(tmp_path):
    ticket_path = tmp_path / "TCK-FAKE.md"
    _write_drift_ticket(
        ticket_path,
        "TCK-FAKE",
        tags="[dashboard]",
        files_changed="- src/api/agent_ops_dashboard/routes.py",
    )

    status, evidence = check_tag_drift("TCK-FAKE", ticket_path=ticket_path)
    assert status == "CLEAN"
    assert "dashboard" in evidence


def test_check_tag_drift_no_candidates_is_clean(tmp_path):
    ticket_path = tmp_path / "TCK-FAKE.md"
    _write_drift_ticket(
        ticket_path,
        "TCK-FAKE",
        tags="[]",
        files_changed="- some/unrelated/path.py",
        related_code_areas="- another/unrelated/path.py",
    )

    status, evidence = check_tag_drift("TCK-FAKE", ticket_path=ticket_path)
    assert status == "CLEAN"
    assert "no candidate tags" in evidence


def test_check_tag_drift_not_in_run_finalize_selfcheck_checks_tuple(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_finalize_selfcheck("TCK-FAKE", "standard")
    conditions = [r["condition"] for r in results]
    assert conditions == [
        "migration_complete",
        "ticket_finalized",
        "working_log_exactly_one_row",
        "registry_entry_regenerated",
    ]
    assert "tag_drift" not in conditions


# ---------------------------------------------------------------------------
# check_registry_entry_regenerated
# ---------------------------------------------------------------------------


def test_check_registry_entry_regenerated_passes_when_entry_present(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_registry_entry_regenerated("TCK-FAKE")
    assert status == "PASS"
    assert "TCK-FAKE" in evidence


def test_check_registry_entry_regenerated_fails_when_entry_absent(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    status, evidence = check_registry_entry_regenerated("TCK-FAKE")
    assert status == "FAIL"
    assert "TCK-FAKE" in evidence


def test_check_registry_entry_regenerated_nonzero_tool_exit_does_not_fail(tmp_path, monkeypatch):
    # A doc missing frontmatter anywhere in docs/ drives generate_registry()'s own exit code to
    # nonzero — unrelated to the closing ticket's own entry, which is present here. Proves AC #2:
    # this must not turn into a FAIL, and the call must not raise.
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    nofm = tmp_path / "docs" / "engine" / "nofm.md"
    nofm.parent.mkdir(parents=True, exist_ok=True)
    nofm.write_text("# No frontmatter\n\nBody.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_registry_entry_regenerated("TCK-FAKE")
    assert status == "PASS"
    assert "TCK-FAKE" in evidence


def test_check_registry_entry_regenerated_applies_under_hotfix_tier(tmp_path, monkeypatch):
    # The function takes no `tier` argument at all — mirrors check_monitoring_write_recorded's
    # precedent: applies identically regardless of tier context.
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    status, _ = check_registry_entry_regenerated("TCK-HOTFIX-FAKE")
    assert status == "FAIL"

    _write_ticket(tmp_path / "tickets" / "done" / "TCK-HOTFIX-FAKE.md", "TCK-HOTFIX-FAKE")
    status, _ = check_registry_entry_regenerated("TCK-HOTFIX-FAKE")
    assert status == "PASS"


def test_registry_entry_check_ordering_guard_fails_if_ticket_still_inprogress(tmp_path, monkeypatch):
    # collect_tickets() only walks tickets/done/*.md — a ticket still sitting in
    # tickets/inprogress/ must not be found, guarding against a future regression where this check
    # is accidentally moved to run before the Finalize agent's own move-to-done step.
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "inprogress" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_registry_entry_regenerated("TCK-FAKE")
    assert status == "FAIL"
    assert "TCK-FAKE" in evidence


def test_claude_md_documents_registry_regen_trigger():
    doc_path = Path(__file__).parent.parent.parent / "CLAUDE.md"
    content = doc_path.read_text(encoding="utf-8")
    assert "regenerated unconditionally" in content
    assert "git add docs/REGISTRY.yaml" in content


# ---------------------------------------------------------------------------
# _parse_docs_to_update (TCK-20260802-DOC-COVERAGE-CHECK)
# ---------------------------------------------------------------------------


def test_parse_docs_extracts_multiple_bullets():
    section = (
        "- `docs/mechanics/03_economic_laws.md`: harvesting yield formula changes\n"
        "- `docs/engine/known_limitations.md`: new scope boundary\n"
        "- `docs/parity_ledger/town_resource.yaml`: entry TR-12 status update\n"
    )
    assert _parse_docs_to_update(section) == [
        "docs/mechanics/03_economic_laws.md",
        "docs/engine/known_limitations.md",
        "docs/parity_ledger/town_resource.yaml",
    ]


def test_parse_docs_none_variants():
    for text in ("", "None", "None.", "N/A", "n/a", "  none.  "):
        assert _parse_docs_to_update(text) == [], repr(text)


def test_parse_docs_ignores_non_bullet_prose():
    section = "This ticket may eventually need to update docs/mechanics/x.md but nothing is decided yet."
    assert _parse_docs_to_update(section) == []


def test_parse_docs_none_with_trailing_rationale_prose():
    # Reproduces the real observed failure (TCK-20260803-DOCS-STRUCTURE-AUDIT's own logged
    # Verify-failure text: "fails the static none-phrase/bullet parser due to trailing rationale
    # prose") — "None." plus an extra rationale sentence, not byte-identical to "none.".
    section = "None. This ticket is documentation-prose-only and touches no docs/ files directly."
    assert _parse_docs_to_update(section) == []


def test_parse_docs_none_prefix_with_later_bullet_still_parses():
    # Guards against Option (a)'s false-PASS risk (see plan.md Decision section): a "None"-led
    # opening clause must not swallow a genuine bullet that follows later in the same section.
    section = (
        "None of the initially-considered docs needed changes, but on reflection:\n"
        "- `docs/mechanics/x.md`: reason\n"
    )
    assert _parse_docs_to_update(section) == ["docs/mechanics/x.md"]


def test_parse_docs_strips_line_number_suffix():
    # TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX: reproduces the real observed failure form
    # (TCK-20260804-EXPANSION-RATE-WIRING's logged evidence text) — a `:line` suffix baked inside
    # the backticks must not be captured into the extracted path.
    section = "- `docs/agent-monitoring/schema.md:287`: reason\n"
    assert _parse_docs_to_update(section) == ["docs/agent-monitoring/schema.md"]


def test_parse_docs_line_suffix_multiple_bullets_mixed_with_bare():
    section = (
        "- `docs/agent-monitoring/schema.md:287`: reason one\n"
        "- `docs/mechanics/x.md`: reason two\n"
    )
    assert _parse_docs_to_update(section) == [
        "docs/agent-monitoring/schema.md",
        "docs/mechanics/x.md",
    ]


def test_parse_docs_does_not_strip_compliance_id_suffix():
    # Real corpus precedent (checked during TCK-20260804-AGENT-DEF-GAP-FIXES review) — a
    # `::COMPLIANCE-ID` suffix is not a line number and must survive uncut.
    section = "- `docs/parity_ledger/world_dynamics.yaml::WORLD-103`: reason\n"
    assert _parse_docs_to_update(section) == ["docs/parity_ledger/world_dynamics.yaml::WORLD-103"]


def test_parse_docs_does_not_strip_comma_range_suffix():
    # Real corpus precedent — a comma-separated line range is not a single `:digits` suffix and
    # must survive uncut.
    section = "- `docs/x.md:3,5`: reason\n"
    assert _parse_docs_to_update(section) == ["docs/x.md:3,5"]


# ---------------------------------------------------------------------------
# Resolved-conditional bullet marker (TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED)
# ---------------------------------------------------------------------------


def test_parse_docs_excludes_resolved_conditional_bullet():
    section = (
        "- `docs/mechanics/04_strategic_cognition.md`: **Resolved during implementation, "
        "condition not met — this doc does not need updating.** Team-Up was scoped as "
        "appraisal-only.\n"
    )
    assert _parse_docs_to_update(section) == []


def test_parse_resolved_not_applicable_docs_extracts_marked_bullet():
    section = (
        "- `docs/mechanics/04_strategic_cognition.md`: **Resolved during implementation, "
        "condition not met — this doc does not need updating.** Team-Up was scoped as "
        "appraisal-only.\n"
    )
    assert _parse_resolved_not_applicable_docs(section) == [
        "docs/mechanics/04_strategic_cognition.md"
    ]


def test_parse_docs_marker_tolerates_line_wrap_and_extra_whitespace():
    section = (
        "- `docs/mechanics/04_strategic_cognition.md`: Resolved during\n"
        "  implementation, condition   not met. No further action needed.\n"
    )
    assert _parse_docs_to_update(section) == []
    assert _parse_resolved_not_applicable_docs(section) == [
        "docs/mechanics/04_strategic_cognition.md"
    ]


def test_parse_docs_mixed_unconditional_and_resolved_bullets():
    section = (
        "- `docs/mechanics/x.md`: unconditional, must update\n"
        "- `docs/mechanics/y.md`: Resolved during implementation, condition not met.\n"
    )
    assert _parse_docs_to_update(section) == ["docs/mechanics/x.md"]
    assert _parse_resolved_not_applicable_docs(section) == ["docs/mechanics/y.md"]


# ---------------------------------------------------------------------------
# _git_touched_paths (TCK-20260802-DOC-COVERAGE-CHECK)
# ---------------------------------------------------------------------------


def test_git_touched_paths_reflects_real_status(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    # git status --porcelain collapses a wholly-new untracked directory to the directory path
    # itself (trailing slash), not the individual file inside it — this is real git behavior, not
    # a wrapper bug; _path_touched (tested separately below) handles the directory-prefix case.
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "new_file.md").write_text("content", encoding="utf-8")

    touched = _git_touched_paths("TCK-FAKE", root=tmp_path)
    assert "docs/" in touched


def test_git_touched_paths_individual_file_in_tracked_directory(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "existing.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    (tmp_path / "docs" / "new_file.md").write_text("content", encoding="utf-8")
    touched = _git_touched_paths("TCK-FAKE", root=tmp_path)
    assert "docs/new_file.md" in touched


def test_git_touched_paths_fails_open_on_non_repo(tmp_path):
    # tmp_path has no .git directory at all.
    assert _git_touched_paths("TCK-FAKE", root=tmp_path) == set()


# ---------------------------------------------------------------------------
# _git_ticket_commits_touched_paths / _git_touched_paths union
# (TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES)
# ---------------------------------------------------------------------------


def _init_repo_with_base(tmp_path: Path) -> None:
    """Real repo with one commit, and refs/remotes/origin/main pointed at it -- simulates a real
    branch's own merge-base with origin/main without needing an actual remote."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("base", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", base_sha], cwd=tmp_path, check=True,
    )


def _commit_all(tmp_path: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=tmp_path, check=True)


def test_ticket_commits_touched_paths_includes_a_committed_doc_change(tmp_path):
    """The ticket's own AC: a doc edit committed mid-session (not left uncommitted until
    Finalize) must still be found, when the commit carries this ticket's own ID prefix."""
    _init_repo_with_base(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "committed.md").write_text("content", encoding="utf-8")
    _commit_all(tmp_path, "TCK-FAKE: add doc")

    touched = _git_ticket_commits_touched_paths("TCK-FAKE", root=tmp_path, base_ref="origin/main")
    assert "docs/committed.md" in touched


def test_ticket_commits_touched_paths_does_not_cross_attribute_to_a_different_ticket(tmp_path):
    """The PR-review finding this ticket-scoping fix exists for: a batch branch with commit A
    (ticket A, touches docs/a.md) and commit B (ticket B, no docs) -- closing B must NOT see
    docs/a.md as touched by it, only A's own commit query should."""
    _init_repo_with_base(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("content", encoding="utf-8")
    _commit_all(tmp_path, "TCK-AAAA: touches docs/a.md")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "b.py").write_text("content", encoding="utf-8")
    _commit_all(tmp_path, "TCK-BBBB: unrelated code change")

    touched_by_b = _git_ticket_commits_touched_paths("TCK-BBBB", root=tmp_path, base_ref="origin/main")
    assert "docs/a.md" not in touched_by_b
    assert "src/b.py" in touched_by_b

    touched_by_a = _git_ticket_commits_touched_paths("TCK-AAAA", root=tmp_path, base_ref="origin/main")
    assert "docs/a.md" in touched_by_a
    assert "src/b.py" not in touched_by_a


def test_git_touched_paths_unions_committed_and_uncommitted(tmp_path):
    """A ticket that commits one doc edit mid-session and leaves a second one uncommitted must
    see both — the union is the whole point of the fix."""
    _init_repo_with_base(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "committed.md").write_text("content", encoding="utf-8")
    _commit_all(tmp_path, "TCK-FAKE: add doc")
    (tmp_path / "docs" / "uncommitted.md").write_text("content", encoding="utf-8")

    touched = _git_touched_paths("TCK-FAKE", root=tmp_path, base_ref="origin/main")
    assert "docs/committed.md" in touched
    assert "docs/uncommitted.md" in touched


def test_ticket_commits_touched_paths_fails_open_when_base_ref_missing(tmp_path):
    """No refs/remotes/origin/main at all -- e.g. a shallow clone or origin/main never fetched.
    Must return an empty set, not raise."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    _commit_all(tmp_path, "TCK-FAKE: init")

    assert _git_ticket_commits_touched_paths("TCK-FAKE", root=tmp_path, base_ref="origin/main") == set()


def test_git_touched_paths_falls_back_to_status_only_when_base_ref_missing(tmp_path):
    """When origin/main is unavailable, _git_touched_paths must still return whatever
    _git_status_touched_paths alone found -- never crash, never silently drop the working-tree
    signal along with the unavailable branch-diff signal."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    _commit_all(tmp_path, "TCK-FAKE: init")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "uncommitted.md").write_text("content", encoding="utf-8")

    touched = _git_touched_paths("TCK-FAKE", root=tmp_path, base_ref="origin/main")
    assert "docs/" in touched


# ---------------------------------------------------------------------------
# _path_touched (TCK-20260802-DOC-COVERAGE-CHECK)
# ---------------------------------------------------------------------------


def test_path_touched_exact_match():
    assert _path_touched("docs/x.md", {"docs/x.md"}) is True


def test_path_touched_directory_prefix_match():
    assert _path_touched("docs/newsubsystem/x.md", {"docs/newsubsystem/"}) is True


def test_path_touched_no_match():
    assert _path_touched("docs/x.md", {"docs/y.md"}) is False


# ---------------------------------------------------------------------------
# check_docs_to_update_coverage (TCK-20260802-DOC-COVERAGE-CHECK)
# ---------------------------------------------------------------------------


def test_docs_coverage_hotfix_forward_half_still_skips(tmp_path, monkeypatch):
    # TCK-20260904-DOC-COVERAGE-REVERSE-CHECK, Decision 3: the forward half still requires no
    # investigation.md under hotfix tier (a real structural absence, genuinely unchanged) — this
    # is isolated here by making the reverse half trivially PASS (no git repo at all, so
    # _git_touched_paths() fails open to {}, so there is no docs/ path to check reverse coverage
    # against). Replaces the old test_docs_coverage_hotfix_is_na, which asserted a bare
    # unconditional NA that Decision 3 deliberately removes.
    base = tmp_path / "staging_artifacts"  # directory does not even exist
    monkeypatch.chdir(tmp_path)
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "hotfix", base_dir=base)
    assert status == "PASS"
    assert "does not exist" not in evidence


def test_docs_coverage_missing_investigation_file_fails(tmp_path):
    base = tmp_path / "staging_artifacts"
    (base / "TCK-FAKE").mkdir(parents=True)
    # investigation.md intentionally absent
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "FAIL"
    assert "investigation.md" in evidence


def _write_investigation(base: Path, ticket_id: str, docs_section_body: str) -> Path:
    directory = base / ticket_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "investigation.md"
    path.write_text(
        ARTIFACT_FM.format(ticket_id=ticket_id, artifact_type="investigation")
        + f"\n## Docs Requiring Update\n{docs_section_body}\n\n## Parity Ledger Overlap\nNone.\n",
        encoding="utf-8",
    )
    return path


def test_docs_coverage_no_section_heading_passes(tmp_path, monkeypatch):
    # monkeypatch.chdir isolates _git_touched_paths() from the real repo's own working-tree
    # state — the reverse check (TCK-20260904-DOC-COVERAGE-REVERSE-CHECK) now always calls it,
    # unlike the old forward-only logic, which never did for an empty-required-docs fixture.
    base = tmp_path / "staging_artifacts"
    directory = base / "TCK-FAKE"
    directory.mkdir(parents=True)
    (directory / "investigation.md").write_text(
        ARTIFACT_FM.format(ticket_id="TCK-FAKE", artifact_type="investigation"),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_docs_coverage_explicit_none_passes(tmp_path, monkeypatch):
    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_docs_coverage_none_with_trailing_rationale_passes(tmp_path, monkeypatch):
    # End-to-end regression test for the actual observed FAIL, at the exact call site
    # (check_docs_to_update_coverage) that produced it for TCK-20260803-DOCS-STRUCTURE-AUDIT,
    # TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE, TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION.
    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "None. This ticket only touches tooling/test files, no docs/ content changes needed.",
    )
    monkeypatch.chdir(tmp_path)
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_docs_coverage_none_prefix_but_real_bullet_still_required(tmp_path, monkeypatch):
    # A "None of the..." opening clause followed by a real, untouched bullet must still FAIL —
    # confirms the Option (b) remainder-check keeps working end-to-end, not just at parse level.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "None of the originally-scoped docs, but on reflection:\n"
        "- `docs/mechanics/x.md`: reason\n",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/mechanics/x.md" in evidence


def test_docs_coverage_unparseable_non_none_section_fails(tmp_path):
    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "Probably docs/mechanics/x.md but not sure yet.")
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "FAIL"
    assert "no docs/ path could be parsed" in evidence


def test_docs_coverage_all_flagged_paths_touched_passes(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs" / "mechanics").mkdir(parents=True)
    (tmp_path / "docs" / "mechanics" / "x.md").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "- `docs/mechanics/x.md`: reason")
    # Reverse-check needs a resolvable ticket file declaring the same touched docs/ path
    # (TCK-20260904-DOC-COVERAGE-REVERSE-CHECK) — real Verify-time calls always have one; this
    # fixture's earlier absence was a pre-existing gap in the fixture, not a case the reverse
    # check should skip.
    _write_reverse_ticket(tmp_path, "TCK-FAKE", files_changed="- `docs/mechanics/x.md`: reason")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "PASS"
    assert "docs/mechanics/x.md" in evidence


def test_docs_coverage_line_suffix_bullet_matches_bare_git_path(tmp_path, monkeypatch):
    # End-to-end regression test for the actual observed FAIL
    # (TCK-20260804-EXPANSION-RATE-WIRING's logged evidence text: "BLOCKED - docs_to_update_coverage
    # failed on investigation.md bullet format (:line baked inside backticks)") — a `:line`-suffixed
    # bullet must correctly match `git status`'s bare-path form.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs" / "agent-monitoring").mkdir(parents=True)
    (tmp_path / "docs" / "agent-monitoring" / "schema.md").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "- `docs/agent-monitoring/schema.md:287`: reason")
    # Reverse-check needs a resolvable ticket file declaring the same touched docs/ path
    # (TCK-20260904-DOC-COVERAGE-REVERSE-CHECK) — see note on the sibling test above.
    _write_reverse_ticket(
        tmp_path, "TCK-FAKE", files_changed="- `docs/agent-monitoring/schema.md:287`: reason"
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "PASS"
    assert "docs/agent-monitoring/schema.md" in evidence


def test_docs_coverage_missing_flagged_path_fails(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    # No docs/mechanics/x.md ever created — nothing for git to show as touched.

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "- `docs/mechanics/x.md`: reason")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "FAIL"
    assert "docs/mechanics/x.md" in evidence


def test_docs_coverage_resolved_conditional_bullet_untouched_passes(tmp_path, monkeypatch):
    # Core new case (TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED): a bullet
    # correctly written in Format 1 at investigation time because its need depended on an
    # implementation-time choice, then genuinely resolved as not-applicable, must PASS even though
    # its doc was never touched.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    # docs/mechanics/04_strategic_cognition.md deliberately never created — nothing touches it.

    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "- `docs/mechanics/04_strategic_cognition.md`: **Resolved during implementation, "
        "condition not met — this doc does not need updating.** Team-Up was scoped as "
        "appraisal-only.",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "PASS"
    assert "docs/mechanics/04_strategic_cognition.md" in evidence


def test_docs_coverage_resolved_conditional_bullet_touched_anyway_still_passes(tmp_path, monkeypatch):
    # The marker must not somehow break the already-touched case.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs" / "mechanics").mkdir(parents=True)
    (tmp_path / "docs" / "mechanics" / "04_strategic_cognition.md").write_text(
        "content", encoding="utf-8"
    )

    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "- `docs/mechanics/04_strategic_cognition.md`: Resolved during implementation, "
        "condition not met, but touched anyway for an unrelated reason.",
    )
    # Reverse-check needs a resolvable ticket file declaring the same touched docs/ path
    # (TCK-20260904-DOC-COVERAGE-REVERSE-CHECK) — see note on the earlier sibling tests above.
    _write_reverse_ticket(
        tmp_path, "TCK-FAKE",
        files_changed="- `docs/mechanics/04_strategic_cognition.md` — touched anyway",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "PASS"


def test_docs_coverage_resolved_marker_does_not_exempt_sibling_unconditional_bullet(
    tmp_path, monkeypatch
):
    # Proves the marker doesn't leak exemption to sibling bullets in the same section: the
    # unconditional bullet's doc is untouched and must still FAIL, even though the resolved-marker
    # bullet in the same section correctly requires nothing.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    # docs/mechanics/x.md (unconditional) deliberately never created.

    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "- `docs/mechanics/x.md`: unconditional, must update\n"
        "- `docs/mechanics/04_strategic_cognition.md`: Resolved during implementation, "
        "condition not met.",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "FAIL"
    assert "docs/mechanics/x.md" in evidence
    assert "docs/mechanics/04_strategic_cognition.md" not in evidence


def test_docs_coverage_ignores_behavior_changed_entirely():
    # Signature/design guard: the function only ever accepts ticket_id/tier/base_dir — there is
    # no behavior_changed-shaped parameter to accidentally wire up, unlike doc_staleness_check.py's
    # gate (TCK-20260802-DOC-UPDATE-DISCIPLINE), which this check deliberately does not mirror.
    import inspect

    params = list(inspect.signature(check_docs_to_update_coverage).parameters)
    assert params == ["ticket_id", "tier", "base_dir"]


# ---------------------------------------------------------------------------
# check_docs_to_update_coverage — reverse direction (TCK-20260904-DOC-COVERAGE-REVERSE-CHECK)
# ---------------------------------------------------------------------------

_REVERSE_TICKET_TEMPLATE = """---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: {ticket_id}
phase: open
date: 2026-09-04
tags: []
---

# {ticket_id}

## Title
Fixture ticket

## Tier
{tier}

## Files Changed
{files_changed}

## Related Docs
{related_docs}

## Completion Summary
"""


def _write_reverse_ticket(
    tmp_path, ticket_id, files_changed="None.", related_docs="None.", tier="standard",
    location="tickets/inprogress",
) -> Path:
    directory = tmp_path / location
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{ticket_id}.md"
    path.write_text(
        _REVERSE_TICKET_TEMPLATE.format(
            ticket_id=ticket_id, tier=tier, files_changed=files_changed, related_docs=related_docs,
        ),
        encoding="utf-8",
    )
    return path


def _git_init(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)


def _git_commit_baseline(tmp_path, tracked_dir: str):
    # Commits a placeholder inside `tracked_dir` so it (and every ancestor directory) is already
    # tracked — a file added later inside it then shows up individually in `git status
    # --porcelain`, not collapsed to the nearest wholly-new directory (confirmed empirically: a
    # brand-new `docs/` in a fresh repo collapses to `?? docs/` regardless of nesting depth).
    d = tmp_path / tracked_dir
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=tmp_path, check=True)


def test_reverse_docs_coverage_fails_when_touched_doc_not_in_files_changed_or_related_docs(
    tmp_path, monkeypatch
):
    _git_init(tmp_path)
    _git_commit_baseline(tmp_path, "docs/mechanics")
    (tmp_path / "docs" / "mechanics" / "combat.md").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    _write_reverse_ticket(tmp_path, "TCK-FAKE", files_changed="- src/combat/engine.py")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/mechanics/combat.md" in evidence


def test_reverse_docs_coverage_passes_when_touched_doc_appears_in_files_changed(tmp_path, monkeypatch):
    _git_init(tmp_path)
    _git_commit_baseline(tmp_path, "docs/mechanics")
    (tmp_path / "docs" / "mechanics" / "combat.md").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    _write_reverse_ticket(
        tmp_path, "TCK-FAKE",
        files_changed="- `docs/mechanics/combat.md` — updated for new formula",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS"


def test_reverse_docs_coverage_passes_when_touched_doc_appears_in_related_docs_only(
    tmp_path, monkeypatch
):
    _git_init(tmp_path)
    _git_commit_baseline(tmp_path, "docs/mechanics")
    (tmp_path / "docs" / "mechanics" / "combat.md").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    _write_reverse_ticket(
        tmp_path, "TCK-FAKE",
        files_changed="None.",
        related_docs="- docs/mechanics/combat.md",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS"


def test_reverse_docs_coverage_directory_collapse_tolerance(tmp_path, monkeypatch):
    # Mirrors _path_touched's own docstring example: a wholly-new untracked directory collapses to
    # its own path (`?? docs/newsubsystem/`) in git status --porcelain, rather than listing every
    # file inside it — the reverse check must still recognize a declared path under it as covered.
    _git_init(tmp_path)
    _git_commit_baseline(tmp_path, "docs")
    (tmp_path / "docs" / "newsubsystem").mkdir(parents=True)
    (tmp_path / "docs" / "newsubsystem" / "foo.md").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    _write_reverse_ticket(
        tmp_path, "TCK-FAKE",
        files_changed="- `docs/newsubsystem/foo.md` — new doc",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS"


def test_reverse_docs_coverage_ITEM_INSTANCE_HISTORY_style_non_docs_path_is_out_of_scope(
    tmp_path, monkeypatch
):
    # Decision 2's disclosed limitation: a touched non-docs/ path (the real
    # TCK-20260831-ITEM-INSTANCE-HISTORY incident's actual gap was src/core/state.py) can never be
    # flagged by this docs/-only reverse check, undeclared or not.
    _git_init(tmp_path)
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "src" / "core" / "state.py").write_text("content", encoding="utf-8")

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    _write_reverse_ticket(tmp_path, "TCK-FAKE")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS"


def test_reverse_docs_coverage_hotfix_tier_behavior(tmp_path, monkeypatch):
    # Decision 3: the reverse half runs identically under hotfix tier — no investigation.md
    # dependency, no NA branch — and can independently FAIL, not merely PASS.
    _git_init(tmp_path)
    _git_commit_baseline(tmp_path, "docs/mechanics")
    (tmp_path / "docs" / "mechanics" / "combat.md").write_text("content", encoding="utf-8")

    _write_reverse_ticket(tmp_path, "TCK-FAKE", tier="hotfix")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "hotfix", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/mechanics/combat.md" in evidence

    _write_reverse_ticket(
        tmp_path, "TCK-FAKE", tier="hotfix",
        files_changed="- `docs/mechanics/combat.md` — hotfix update",
    )
    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "hotfix", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS"


def test_reverse_docs_coverage_catches_a_doc_committed_mid_session_with_clean_tree(
    tmp_path, monkeypatch
):
    """TCK-20260916-DOC-COVERAGE-CHECK-BLIND-TO-COMMITTED-CHANGES's own real fixture case: a doc
    edit genuinely committed earlier in a hand-orchestrated session, with a fully clean working
    tree by the time this check runs (`git status --porcelain` alone would see nothing), must
    still be recognized when it's NOT declared -- proving the branch-diff half is doing real work,
    not that the fixture only exercises the pre-existing uncommitted-change path."""
    _init_repo_with_base(tmp_path)
    (tmp_path / "docs" / "mechanics").mkdir(parents=True)
    (tmp_path / "docs" / "mechanics" / "combat.md").write_text("content", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    # Commit message carries the ticket's own ID prefix (this repo's real Commit Convention) --
    # required for the ticket-scoped commit lookup to find it at all.
    subprocess.run(["git", "commit", "-q", "-m", "TCK-FAKE: committed mid-session"], cwd=tmp_path, check=True)
    # Working tree is now fully clean -- confirm that directly, so this test can't silently pass
    # for the wrong reason (an accidental leftover uncommitted change).
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True, check=True,
    ).stdout
    assert status.strip() == "", "fixture setup bug: working tree must be clean for this test"

    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    _write_reverse_ticket(tmp_path, "TCK-FAKE", files_changed="None.")
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/mechanics/combat.md" in evidence

    # Now declare it -- must PASS, this is the ticket's own AC #1.
    _write_reverse_ticket(
        tmp_path, "TCK-FAKE",
        files_changed="- `docs/mechanics/combat.md` — committed mid-session",
    )
    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS"


def test_reverse_docs_coverage_multi_ticket_batch_branch_does_not_cross_attribute(
    tmp_path, monkeypatch
):
    """PR review finding on this same ticket, before merge: this repo's own standing practice is
    one branch per BATCH, not per ticket. A branch-wide diff (the pre-review version of this fix)
    would attribute ticket A's own committed docs/a.md to ticket B closing later on the same
    branch, forcing B to redundantly declare a doc it never touched just to pass the gate. Ticket-
    scoped commit lookup must not do that: closing B (clean tree) with docs/a.md undeclared must
    PASS; closing A must see docs/a.md as touched."""
    _init_repo_with_base(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("content", encoding="utf-8")
    _commit_all(tmp_path, "TCK-AAAA: touches docs/a.md")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "b.py").write_text("content", encoding="utf-8")
    _commit_all(tmp_path, "TCK-BBBB: unrelated code change, no docs")
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True, check=True,
    ).stdout
    assert status.strip() == "", "fixture setup bug: working tree must be clean for this test"

    base = tmp_path / "staging_artifacts"
    monkeypatch.chdir(tmp_path)

    # Closing TCK-BBBB: docs/a.md is real, on the branch, but belongs to a different ticket's own
    # commit -- must not be attributed to B, so the reverse check PASSes without B declaring it.
    _write_investigation(base, "TCK-BBBB", "None.")
    _write_reverse_ticket(tmp_path, "TCK-BBBB", files_changed="None.")
    status, evidence = check_docs_to_update_coverage(
        "TCK-BBBB", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "PASS", f"TCK-BBBB must not be blamed for TCK-AAAA's own doc: {evidence}"

    # Closing TCK-AAAA: docs/a.md IS its own commit's file -- must be seen as touched, and FAIL
    # if undeclared, exactly like the single-ticket case.
    _write_investigation(base, "TCK-AAAA", "None.")
    _write_reverse_ticket(tmp_path, "TCK-AAAA", files_changed="None.")
    status, evidence = check_docs_to_update_coverage(
        "TCK-AAAA", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/a.md" in evidence


def test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident(tmp_path, monkeypatch):
    # Historical-incident regression fixture (AC #3): reconstructs
    # TCK-20260831-RACE-RELATIONS-MATRIX's pre-hand-patch state — Document-Update added
    # docs/mechanics/02_combat_laws.md coverage for the is_hostile_compat extension, but the
    # ticket's own Files Changed/Related Docs never recorded it (RETRO-2026-W36's "What to
    # change?" note). This is a deliberately-incomplete fixture reconstruction, not a copy of the
    # real post-patch tickets/done/TCK-20260831-RACE-RELATIONS-MATRIX.md file.
    # TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS: the reverse half now calls
    # _git_status_touched_paths()/_git_ticket_commits_touched_paths() directly (so sibling-
    # attribution and the REGISTRY.yaml exclusion can apply to only the reverse check) instead of
    # the combined _git_touched_paths() — mock the forward half's own call (unchanged) plus the
    # uncommitted half specifically, since the forward half's own `touched` lookup still goes
    # through _git_touched_paths().
    monkeypatch.setattr(
        "gate_checks.done_checker_static._git_touched_paths",
        lambda ticket_id, root=Path("."), base_ref="origin/main": {"docs/mechanics/02_combat_laws.md"},
    )
    monkeypatch.setattr(
        "gate_checks.done_checker_static._git_status_touched_paths",
        lambda root=Path("."): {"docs/mechanics/02_combat_laws.md"},
    )
    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-20260831-RACE-RELATIONS-MATRIX", "None.")
    _write_reverse_ticket(
        tmp_path,
        "TCK-20260831-RACE-RELATIONS-MATRIX",
        files_changed="- src/domains/combat_engagement/hostility.py — is_hostile_compat extension",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-20260831-RACE-RELATIONS-MATRIX", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/mechanics/02_combat_laws.md" in evidence


# ---------------------------------------------------------------------------
# check_docs_to_update_coverage — sibling attribution + REGISTRY.yaml exclusion
# (TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS)
# ---------------------------------------------------------------------------


def _mock_uncommitted(monkeypatch, paths: set) -> None:
    monkeypatch.setattr(
        "gate_checks.done_checker_static._git_status_touched_paths",
        lambda root=Path("."): set(paths),
    )
    monkeypatch.setattr(
        "gate_checks.done_checker_static._git_ticket_commits_touched_paths",
        lambda ticket_id, root=Path("."), base_ref="origin/main": set(),
    )


def test_sibling_attribution_each_ticket_claims_its_own_uncommitted_doc(tmp_path, monkeypatch):
    """AC3: two in-progress tickets A and B, uncommitted docs/a.md (claimed by A) and docs/b.md
    (claimed by B) — checking A passes (docs/b.md is B's, not A's problem) and checking B passes
    (docs/a.md is A's, not B's problem)."""
    _write_investigation(tmp_path / "staging_artifacts", "TCK-A", "None.")
    _write_investigation(tmp_path / "staging_artifacts", "TCK-B", "None.")
    _write_reverse_ticket(tmp_path, "TCK-A", files_changed="- `docs/a.md`: A's own doc")
    _write_reverse_ticket(tmp_path, "TCK-B", files_changed="- `docs/b.md`: B's own doc")
    monkeypatch.chdir(tmp_path)
    _mock_uncommitted(monkeypatch, {"docs/a.md", "docs/b.md"})

    status_a, evidence_a = check_docs_to_update_coverage("TCK-A", "standard", base_dir=Path("staging_artifacts"))
    assert status_a == "PASS", evidence_a
    status_b, evidence_b = check_docs_to_update_coverage("TCK-B", "standard", base_dir=Path("staging_artifacts"))
    assert status_b == "PASS", evidence_b


def test_sibling_attribution_unclaimed_doc_still_fails_both(tmp_path, monkeypatch):
    """AC3 continued: an uncommitted docs/c.md claimed by neither A nor B still FAILs for both —
    sibling attribution narrows blame, it does not create a blind spot for a genuinely undeclared
    doc."""
    _write_investigation(tmp_path / "staging_artifacts", "TCK-A", "None.")
    _write_investigation(tmp_path / "staging_artifacts", "TCK-B", "None.")
    _write_reverse_ticket(tmp_path, "TCK-A", files_changed="- `docs/a.md`: A's own doc")
    _write_reverse_ticket(tmp_path, "TCK-B", files_changed="- `docs/b.md`: B's own doc")
    monkeypatch.chdir(tmp_path)
    _mock_uncommitted(monkeypatch, {"docs/a.md", "docs/b.md", "docs/c.md"})

    status_a, evidence_a = check_docs_to_update_coverage("TCK-A", "standard", base_dir=Path("staging_artifacts"))
    assert status_a == "FAIL"
    assert "docs/c.md" in evidence_a
    status_b, evidence_b = check_docs_to_update_coverage("TCK-B", "standard", base_dir=Path("staging_artifacts"))
    assert status_b == "FAIL"
    assert "docs/c.md" in evidence_b


def test_sibling_attribution_only_applies_to_done_tickets_also_in_uncommitted_status(tmp_path, monkeypatch):
    """A ticket in tickets/done/ that is NOT itself part of the uncommitted git status (an
    already-committed prior closure) is not treated as a same-batch sibling — its declared docs
    must not excuse an otherwise-undeclared path for the ticket being checked."""
    _write_investigation(tmp_path / "staging_artifacts", "TCK-CHECKED", "None.")
    _write_reverse_ticket(tmp_path, "TCK-CHECKED", files_changed="None.")
    # TCK-PRIOR is a done ticket, but NOT in the mocked uncommitted status below.
    _write_reverse_ticket(tmp_path, "TCK-PRIOR", files_changed="- `docs/a.md`: prior work", location="tickets/done")
    monkeypatch.chdir(tmp_path)
    _mock_uncommitted(monkeypatch, {"docs/a.md"})

    status, evidence = check_docs_to_update_coverage("TCK-CHECKED", "standard", base_dir=Path("staging_artifacts"))
    assert status == "FAIL"
    assert "docs/a.md" in evidence


def test_registry_yaml_alone_never_fails_reverse_check(tmp_path, monkeypatch):
    """AC4: an uncommitted change to docs/REGISTRY.yaml alone never FAILs the reverse check — it's
    regenerated unconditionally at every close, not evidence of an undeclared doc edit."""
    _write_investigation(tmp_path / "staging_artifacts", "TCK-REG", "None.")
    _write_reverse_ticket(tmp_path, "TCK-REG", files_changed="None.")
    monkeypatch.chdir(tmp_path)
    _mock_uncommitted(monkeypatch, {"docs/REGISTRY.yaml"})

    status, evidence = check_docs_to_update_coverage("TCK-REG", "standard", base_dir=Path("staging_artifacts"))
    assert status == "PASS", evidence
    assert "no docs/ path(s) touched" in evidence


def test_registry_yaml_excluded_alongside_a_real_undeclared_doc(tmp_path, monkeypatch):
    """REGISTRY.yaml's exclusion must not mask a genuinely undeclared doc touched at the same
    time — only REGISTRY.yaml itself is dropped from the touched set."""
    _write_investigation(tmp_path / "staging_artifacts", "TCK-REG2", "None.")
    _write_reverse_ticket(tmp_path, "TCK-REG2", files_changed="None.")
    monkeypatch.chdir(tmp_path)
    _mock_uncommitted(monkeypatch, {"docs/REGISTRY.yaml", "docs/undeclared.md"})

    status, evidence = check_docs_to_update_coverage("TCK-REG2", "standard", base_dir=Path("staging_artifacts"))
    assert status == "FAIL"
    assert "docs/undeclared.md" in evidence
    assert "docs/REGISTRY.yaml" not in evidence


# ---------------------------------------------------------------------------
# run_static_precheck — docs_to_update_coverage wiring (TCK-20260802-DOC-COVERAGE-CHECK)
# ---------------------------------------------------------------------------


def test_run_static_precheck_includes_docs_to_update_coverage_condition(tmp_path, monkeypatch):
    _scaffold_precheck_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    conditions = {r["condition"] for r in results}
    assert "docs_to_update_coverage" in conditions


def test_run_static_precheck_wires_reverse_check_blocking(tmp_path, monkeypatch):
    # TCK-20260904-DOC-COVERAGE-REVERSE-CHECK, Decision 4: no run_static_precheck code change was
    # needed for the reverse half — it already folds check_docs_to_update_coverage's returned
    # (status, evidence) into the existing docs_to_update_coverage entry. This proves a
    # reverse-check FAIL surfaces through that same aggregation rather than being silently
    # absorbed into a PASS from the (still-passing) forward half. _write_ticket's own fixture
    # ticket (via _scaffold_precheck_repo) has no Files Changed/Related Docs section at all, so any
    # touched docs/ path is trivially undeclared.
    _scaffold_precheck_repo(tmp_path)
    _git_init(tmp_path)
    _git_commit_baseline(tmp_path, "docs/mechanics")
    (tmp_path / "docs" / "mechanics" / "x.md").write_text("content", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    by_condition = {r["condition"]: r for r in results}
    assert by_condition["docs_to_update_coverage"]["status"] == "FAIL"
    assert "docs/mechanics/x.md" in by_condition["docs_to_update_coverage"]["evidence"]


# ---------------------------------------------------------------------------
# implement-ticket.js Verify-prompt wiring (TCK-20260802-DOC-COVERAGE-CHECK) — static
# source-text test, mirrors tests/tools/test_doc_staleness_gate_wiring.py's established pattern
# (no JS test runner exists for .claude/workflows/*.js in this repo).
# ---------------------------------------------------------------------------

_IMPLEMENT_TICKET_JS_PATH = Path(__file__).parent.parent.parent / ".claude" / "workflows" / "implement-ticket.js"


def test_verify_prompt_cites_condition_6_alongside_static_conditions():
    text = _IMPLEMENT_TICKET_JS_PATH.read_text(encoding="utf-8")
    idx = text.find("Before checking conditions")
    assert idx != -1
    line_end = text.find("\n", idx)
    line = text[idx:line_end]
    assert "conditions 3, 4, 6, 7, 10, 12" in line


def test_verify_prompt_condition_6_precedes_static_precheck_invocation():
    text = _IMPLEMENT_TICKET_JS_PATH.read_text(encoding="utf-8")
    condition_idx = text.find("Before checking conditions 3, 4, 6, 7, 10, 12")
    invoke_idx = text.find("run_static_precheck('${tid}'")
    assert condition_idx != -1
    assert invoke_idx != -1
    assert condition_idx < invoke_idx


def test_verify_prompt_mentions_reverse_check_or_updated_condition_language():
    # TCK-20260904-DOC-COVERAGE-REVERSE-CHECK: the same static-script-citation sentence must now
    # also describe the reverse direction, not only the forward direction it originally documented.
    text = _IMPLEMENT_TICKET_JS_PATH.read_text(encoding="utf-8")
    idx = text.find("Before checking conditions 3, 4, 6, 7, 10, 12")
    assert idx != -1
    invoke_idx = text.find("run_static_precheck('${tid}'")
    sentence = text[idx:invoke_idx]
    assert "TCK-20260904-DOC-COVERAGE-REVERSE-CHECK" in sentence
    assert "reverse" in sentence.lower()


# ─── CLI entry point (TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE) ──────
#
# Before this ticket, tools/gate_checks/done_checker_static.py had no __main__/argparse and was
# consumed exclusively via `python3 -c "..."` by the formal pipeline. Running it "the obvious way"
# imported the module, printed only an unrelated SyntaxWarning on a fresh compile, and exited 0 --
# indistinguishable from a clean pass. These tests pin the fix: a real CLI that produces readable
# output and a non-zero exit on a known-failing condition, without changing any existing
# function-level import path.

_DONE_CHECKER_PATH = _TOOLS_DIR / "gate_checks" / "done_checker_static.py"


def _run_cli(args, cwd):
    return subprocess.run(
        [sys.executable, "-B", str(_DONE_CHECKER_PATH), *args],
        capture_output=True, text=True, cwd=cwd,
    )


def _seed_ticket(tmp_path, ticket_id, tier="hotfix"):
    ticket_dir = tmp_path / "tickets" / "inprogress"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    (ticket_dir / f"{ticket_id}.md").write_text(
        "---\nstatus: active\nlayer: misc\nauthority: P1\naudience: agent\n"
        f"ticket_id: {ticket_id}\nphase: open\ndate: 2026-09-14\ntags: []\n---\n\n"
        f"# {ticket_id}\n\n## Title\nFake\n\n## Status\nOPEN\n\n## Tier\n{tier}\n\n"
        "## Priority\nP1\n",
        encoding="utf-8",
    )
    return ticket_dir / f"{ticket_id}.md"


def test_cli_prints_readable_output_and_exits_nonzero_on_known_failure(tmp_path):
    ticket_id = "TCK-CLI-FAIL-TEST"
    _seed_ticket(tmp_path, ticket_id, tier="hotfix")
    result = _run_cli(["--ticket-id", ticket_id, "--part", "finalize"], tmp_path)
    assert result.stdout.strip(), "expected non-empty stdout -- silence is exactly the regression"
    assert result.returncode != 0
    assert "working_log_exactly_one_row" in result.stdout
    assert "FAIL" in result.stdout
    assert "RESULT: FAIL" in result.stdout


def test_cli_exits_zero_and_prints_pass_when_all_precheck_conditions_pass(tmp_path):
    ticket_id = "TCK-CLI-PASS-TEST"
    _seed_ticket(tmp_path, ticket_id, tier="hotfix")
    (tmp_path / "tickets" / "working_log.csv").write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n", encoding="utf-8"
    )
    result = _run_cli(["--ticket-id", ticket_id, "--part", "precheck"], tmp_path)
    assert result.stdout.strip()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_cli_bare_default_skips_precheck_for_an_already_closed_ticket(tmp_path):
    """AC1 (TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS): a ticket already in
    tickets/done/ with a clean finalize state gives RESULT: PASS under the bare CLI (no --part),
    with a note explaining precheck was skipped — precheck's own conditions (ticket_location,
    working_log_no_row_yet, etc.) assume the ticket is still in tickets/inprogress/ and would
    false-FAIL here otherwise.
    """
    _scaffold_finalize_repo(tmp_path, ticket_id="TCK-CLOSED-FAKE")
    # TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES: the bare CLI no longer regenerates the
    # tracked registry, so a clean finalize state means the closer already regenerated it.
    check_registry_entry_regenerated("TCK-CLOSED-FAKE", root=tmp_path)
    result = _run_cli(["--ticket-id", "TCK-CLOSED-FAKE"], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout
    assert "skipping precheck" in result.stdout
    assert "[precheck]" not in result.stdout
    assert "[finalize]" in result.stdout


def test_cli_explicit_part_both_still_runs_precheck_on_a_closed_ticket(tmp_path):
    """AC2: --part both set explicitly forces precheck to run even post-closure, so behavior is
    unchanged when asked for — precheck is expected to report real FAILs here (the ticket is no
    longer in tickets/inprogress/), which is correct: the point is that precheck RAN, not that it
    passed.
    """
    _scaffold_finalize_repo(tmp_path, ticket_id="TCK-CLOSED-FAKE-2")
    result = _run_cli(["--ticket-id", "TCK-CLOSED-FAKE-2", "--part", "both"], tmp_path)
    assert "[precheck]" in result.stdout
    assert "[finalize]" in result.stdout
    assert "skipping precheck" not in result.stdout


def test_cli_tier_auto_detected_from_ticket_body_when_omitted(tmp_path):
    ticket_id = "TCK-CLI-TIER-TEST"
    _seed_ticket(tmp_path, ticket_id, tier="epic")
    result = _run_cli(["--ticket-id", ticket_id, "--part", "precheck"], tmp_path)
    assert "tier=epic" in result.stdout


def test_cli_explicit_tier_overrides_auto_detection(tmp_path):
    ticket_id = "TCK-CLI-TIER-OVERRIDE-TEST"
    _seed_ticket(tmp_path, ticket_id, tier="epic")
    result = _run_cli(["--ticket-id", ticket_id, "--tier", "hotfix", "--part", "precheck"], tmp_path)
    assert "tier=hotfix" in result.stdout


def test_cli_still_importable_and_callable_as_plain_functions(tmp_path, monkeypatch):
    """Pins the Scope constraint that the formal pipeline's own python3 -c call sites keep
    working unchanged: run_static_precheck/run_finalize_selfcheck must still be plain,
    directly-importable functions, not routed through the new CLI.

    TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES: this test used to call
    run_finalize_selfcheck() with no tmp_path/chdir isolation at all — since
    check_registry_entry_regenerated() (one of the 4 aggregated checks) unconditionally
    regenerates docs/REGISTRY.yaml against whatever `root=Path(".")` resolves to, every real
    pytest run of this file overwrote the actual repo's tracked docs/REGISTRY.yaml as a side
    effect of a test that only meant to check the function's return shape. Isolated the same way
    every other run_finalize_selfcheck test in this file already is. Verified: temporarily
    reverting this isolation reproduces a real docs/REGISTRY.yaml diff and is caught by this
    module's own _fail_if_this_module_touches_tracked_monitoring_files guard fixture.
    """
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    assert callable(run_static_precheck)
    assert callable(run_finalize_selfcheck)
    result = run_finalize_selfcheck("TCK-DOES-NOT-EXIST", "hotfix")
    assert isinstance(result, list)
    assert all({"condition", "status", "evidence"} <= set(item) for item in result)


def test_no_syntax_warning_under_dash_w_error_on_a_fresh_compile():
    """The escape-sequence fix: a fresh (-B, no cached .pyc) import under -W error must not raise
    SyntaxError. This is the exact symptom a hand-orchestrating session hit before this ticket --
    a SyntaxWarning on first import, silently absorbed by the bytecode cache afterward."""
    result = subprocess.run(
        [
            sys.executable, "-W", "error", "-B", "-c",
            "import sys; sys.path.insert(0, 'tools/gate_checks'); sys.path.insert(0, 'tools'); "
            "import done_checker_static",
        ],
        capture_output=True, text=True, cwd=str(_TOOLS_DIR.parent),
    )
    assert result.returncode == 0, result.stderr


# ── TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES ────────────────────────────────────────────

_DISPOSITION_TICKET_TAIL = (
    "\n## Disposition\n{value}\n\n## Disposition Rationale\n{rationale}\n"
)


def _write_disposition_ticket(tmp_path, ticket_id="TCK-DISP", value="STALE-PREMISE",
                              rationale="Premise false since 791e6bf6b.", with_rationale=True):
    done = tmp_path / "tickets" / "done"
    done.mkdir(parents=True, exist_ok=True)
    text = TICKET_FM.format(ticket_id=ticket_id, tier="standard")
    if with_rationale:
        text += _DISPOSITION_TICKET_TAIL.format(value=value, rationale=rationale)
    else:
        text += f"\n## Disposition\n{value}\n"
    (done / f"{ticket_id}.md").write_text(text, encoding="utf-8")


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _init_repo_with_origin_main(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")


def test_disposition_closure_with_evidence_passes_without_staging_artifacts(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path)
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-DISP", "standard")
    assert status == "PASS" and "STALE-PREMISE" in evidence


def test_disposition_closure_passes_full_finalize_selfcheck(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path)
    _write_csv(tmp_path / "tickets" / "working_log.csv",
               [["2026-09-30T00:00:00Z", "TCK-DISP", "Disposition", "DONE", "x", ""]])
    monkeypatch.chdir(tmp_path)
    results = run_finalize_selfcheck("TCK-DISP", "standard")
    assert all(r["status"] in ("PASS", "NA") for r in results), results


def test_disposition_with_uncited_rationale_fails_naming_the_requirement(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path, rationale="Trust me, nothing to build here.")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-DISP", "standard")
    assert status == "FAIL" and "no evidence" in evidence


def test_disposition_with_empty_rationale_fails(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path, rationale="")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-DISP", "standard")
    assert status == "FAIL" and "empty" in evidence


def test_disposition_without_rationale_section_fails(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path, with_rationale=False)
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-DISP", "standard")
    assert status == "FAIL" and "missing" in evidence


def test_disposition_with_unknown_value_fails(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path, value="MAYBE")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-DISP", "standard")
    assert status == "FAIL" and "MAYBE" in evidence


def test_disposition_with_committed_src_change_fails(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "thing.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "TCK-DISP: changed code after all")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-DISP", "standard")
    assert status == "FAIL" and "src/thing.py" in evidence


def test_disposition_ignores_src_change_from_another_tickets_commit(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    _write_disposition_ticket(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "other.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "src")
    _git(tmp_path, "commit", "-q", "-m", "TCK-OTHER: unrelated change")
    monkeypatch.chdir(tmp_path)
    assert check_migration_complete("TCK-DISP", "standard")[0] == "PASS"


def test_ticket_without_disposition_still_fails_migration_when_artifacts_missing(tmp_path, monkeypatch):
    _init_repo_with_origin_main(tmp_path)
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-PLAIN.md", "TCK-PLAIN")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_migration_complete("TCK-PLAIN", "standard")
    assert status == "FAIL" and "Missing or empty" in evidence


def test_registry_check_is_read_only_by_default_and_reports_stale_file(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    registry = tmp_path / "docs" / "REGISTRY.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text("# Generated: 2000-01-01\n[]\n", encoding="utf-8")
    before = registry.read_bytes()
    monkeypatch.chdir(tmp_path)
    status, evidence = check_registry_entry_regenerated("TCK-FAKE", regenerate=False)
    assert status == "FAIL" and "stale" in evidence and "make docs-registry" in evidence
    assert registry.read_bytes() == before


def test_registry_check_read_only_passes_when_disk_file_has_entry(tmp_path, monkeypatch):
    (tmp_path / "tickets" / "done").mkdir(parents=True)
    _write_ticket(tmp_path / "tickets" / "done" / "TCK-FAKE.md", "TCK-FAKE")
    monkeypatch.chdir(tmp_path)
    check_registry_entry_regenerated("TCK-FAKE")  # default: regenerates, writes the file
    before = (tmp_path / "docs" / "REGISTRY.yaml").read_bytes()
    status, _ = check_registry_entry_regenerated("TCK-FAKE", regenerate=False)
    assert status == "PASS"
    assert (tmp_path / "docs" / "REGISTRY.yaml").read_bytes() == before


def test_finalize_selfcheck_default_still_regenerates_the_registry(tmp_path, monkeypatch):
    _scaffold_finalize_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    run_finalize_selfcheck("TCK-FAKE", "standard")
    assert (tmp_path / "docs" / "REGISTRY.yaml").exists()


def test_cli_does_not_write_registry_without_flag_and_does_with_it(tmp_path, monkeypatch, capsys):
    from gate_checks import done_checker_static as dcs
    _scaffold_finalize_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    dcs.main(["--ticket-id", "TCK-FAKE", "--part", "finalize"])
    assert not (tmp_path / "docs" / "REGISTRY.yaml").exists()
    dcs.main(["--ticket-id", "TCK-FAKE", "--part", "finalize", "--regenerate-registry"])
    assert (tmp_path / "docs" / "REGISTRY.yaml").exists()


def test_delivery_process_guide_carries_disposition_rule_exactly_once():
    guide = (_REPO_ROOT / "docs" / "guides" / "delivery_process.md").read_text(encoding="utf-8")
    assert guide.count("### Closing a ticket with no implementation") == 1
    for value in ("STALE-PREMISE", "NO-MECHANISM", "DUPLICATE", "SUPERSEDED", "WONT-DO"):
        assert value in guide
    assert "--regenerate-registry" in guide
