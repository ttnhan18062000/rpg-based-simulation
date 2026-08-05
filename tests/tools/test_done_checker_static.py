"""Tests for tools/gate_checks/done_checker_static.py (TCK-20260705-GATE-DET-DONE-CHECKER).

Coverage-honesty requirement (SEQUENCE.md decision 4): every check function below has at least
one fixture proving it catches a real violation it claims to catch, not just that it runs on the
happy path.
"""

import csv
import os
import subprocess
import sys
import time
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.done_checker_static import (  # noqa: E402
    _find_flagged_data_run_files,
    _frontmatter_has_unregistered_tags,
    _git_touched_paths,
    _parse_docs_to_update,
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
    # 7 conditions as of TCK-20260802-DOC-COVERAGE-CHECK (was 6, added ticket_field_values_valid
    # per TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM; was 5 originally). New 7th:
    # docs_to_update_coverage.
    assert len(results) == 7
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
    runs_path = tmp_path / "runs.jsonl"
    events_path = tmp_path / "events.jsonl"
    _write_jsonl(runs_path, [{"run_id": "TCK-OTHER"}])
    _write_jsonl(events_path, [{"run_id": "TCK-OTHER"}])

    status, evidence = check_monitoring_write_recorded(
        "TCK-FAKE", runs_path=runs_path, events_path=events_path
    )
    assert status == "FAIL"
    assert "No row with run_id == TCK-FAKE" in evidence


def test_check_monitoring_write_recorded_fails_when_events_missing(tmp_path):
    runs_path = tmp_path / "runs.jsonl"
    events_path = tmp_path / "events.jsonl"
    _write_jsonl(runs_path, [{"run_id": "TCK-FAKE"}])
    _write_jsonl(events_path, [{"run_id": "TCK-OTHER"}])

    status, evidence = check_monitoring_write_recorded(
        "TCK-FAKE", runs_path=runs_path, events_path=events_path
    )
    assert status == "FAIL"
    assert "zero matching rows" in evidence


def test_check_monitoring_write_recorded_passes_when_both_present(tmp_path):
    runs_path = tmp_path / "runs.jsonl"
    events_path = tmp_path / "events.jsonl"
    _write_jsonl(runs_path, [{"run_id": "TCK-FAKE"}])
    _write_jsonl(events_path, [{"run_id": "TCK-FAKE"}, {"run_id": "TCK-FAKE"}])

    status, evidence = check_monitoring_write_recorded(
        "TCK-FAKE", runs_path=runs_path, events_path=events_path
    )
    assert status == "PASS"
    assert "TCK-FAKE" in evidence


def test_check_monitoring_write_recorded_applies_under_hotfix_tier(tmp_path):
    # The function takes no `tier` argument at all — this documents and locks in that it
    # cannot special-case hotfix, per CLAUDE.md's Hard Rule ("including hotfix").
    runs_path = tmp_path / "runs.jsonl"
    events_path = tmp_path / "events.jsonl"
    _write_jsonl(runs_path, [])
    _write_jsonl(events_path, [])

    status, _ = check_monitoring_write_recorded(
        "TCK-HOTFIX-FAKE", runs_path=runs_path, events_path=events_path
    )
    assert status == "FAIL"

    _write_jsonl(runs_path, [{"run_id": "TCK-HOTFIX-FAKE"}])
    _write_jsonl(events_path, [{"run_id": "TCK-HOTFIX-FAKE"}])
    status, _ = check_monitoring_write_recorded(
        "TCK-HOTFIX-FAKE", runs_path=runs_path, events_path=events_path
    )
    assert status == "PASS"


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

    touched = _git_touched_paths(root=tmp_path)
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
    touched = _git_touched_paths(root=tmp_path)
    assert "docs/new_file.md" in touched


def test_git_touched_paths_fails_open_on_non_repo(tmp_path):
    # tmp_path has no .git directory at all.
    assert _git_touched_paths(root=tmp_path) == set()


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


def test_docs_coverage_hotfix_is_na(tmp_path):
    base = tmp_path / "staging_artifacts"  # directory does not even exist
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "hotfix", base_dir=base)
    assert status == "NA"


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


def test_docs_coverage_no_section_heading_passes(tmp_path):
    base = tmp_path / "staging_artifacts"
    directory = base / "TCK-FAKE"
    directory.mkdir(parents=True)
    (directory / "investigation.md").write_text(
        ARTIFACT_FM.format(ticket_id="TCK-FAKE", artifact_type="investigation"),
        encoding="utf-8",
    )
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_docs_coverage_explicit_none_passes(tmp_path):
    base = tmp_path / "staging_artifacts"
    _write_investigation(base, "TCK-FAKE", "None.")
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_docs_coverage_none_with_trailing_rationale_passes(tmp_path):
    # End-to-end regression test for the actual observed FAIL, at the exact call site
    # (check_docs_to_update_coverage) that produced it for TCK-20260803-DOCS-STRUCTURE-AUDIT,
    # TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE, TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION.
    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "None. This ticket only touches tooling/test files, no docs/ content changes needed.",
    )
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
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=Path("staging_artifacts"))
    assert status == "PASS"
    assert "docs/mechanics/x.md" in evidence


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


def test_docs_coverage_ignores_behavior_changed_entirely():
    # Signature/design guard: the function only ever accepts ticket_id/tier/base_dir — there is
    # no behavior_changed-shaped parameter to accidentally wire up, unlike doc_staleness_check.py's
    # gate (TCK-20260802-DOC-UPDATE-DISCIPLINE), which this check deliberately does not mirror.
    import inspect

    params = list(inspect.signature(check_docs_to_update_coverage).parameters)
    assert params == ["ticket_id", "tier", "base_dir"]


# ---------------------------------------------------------------------------
# run_static_precheck — docs_to_update_coverage wiring (TCK-20260802-DOC-COVERAGE-CHECK)
# ---------------------------------------------------------------------------


def test_run_static_precheck_includes_docs_to_update_coverage_condition(tmp_path, monkeypatch):
    _scaffold_precheck_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    results = run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")
    conditions = {r["condition"] for r in results}
    assert "docs_to_update_coverage" in conditions


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
