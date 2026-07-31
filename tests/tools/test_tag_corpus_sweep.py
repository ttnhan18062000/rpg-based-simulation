"""Tests for the full-corpus tag/category repair sweep (TCK-20260720-TAG-CORPUS-REPAIR-SWEEP):

tools/tag_report.py's `collect_sweep_files`, `tag_issues`, `sweep_file_rows`, and
tools/tag_corpus_sweep.py's `run_sweep`/`print_report`/`build_json_report`/CLI.

Groups:
  1. collect_sweep_files — multi-root walk, SEQUENCE.md skip only, no date cutoff
  2. tag_issues — pure per-tag violation classifier
  3. sweep_file_rows — per-file row builder, crash tolerance
  4. run_sweep / print_report / build_json_report — orchestration and output shaping
  5. CLI — report-only guarantees (no --fix, zero real-corpus writes)
"""

import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tag_report import collect_sweep_files, sweep_file_rows, tag_issues  # noqa: E402
from tag_corpus_sweep import build_json_report, print_report, run_sweep  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent
_SWEEP_SCRIPT = _TOOLS_DIR / "tag_corpus_sweep.py"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_md(root: Path, rel: str, frontmatter: str, body: str = "# Doc\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


_VALID_CATEGORIES = frozenset({"subsystem-topic", "process-skill-signal", "quality-attribute", "meta-process"})


# ---------------------------------------------------------------------------
# Group 1 — collect_sweep_files
# ---------------------------------------------------------------------------


def test_sweep_walks_all_four_corpus_roots(tmp_path):
    _make_md(tmp_path, "tickets/done/TCK-20260705-A.md", "tags: [faction]")
    _make_md(tmp_path, "tickets/inprogress/TCK-20260705-B.md", "tags: [faction]")
    _make_md(tmp_path, "tickets/todos/TCK-20260705-C.md", "tags: [faction]")
    _make_md(tmp_path, "stored_artifacts/TCK-20260705-D/plan.md", "tags: [faction]")

    relative_paths, skip_reasons, _skipped_paths = collect_sweep_files(tmp_path)

    assert set(relative_paths) == {
        "tickets/done/TCK-20260705-A.md",
        "tickets/inprogress/TCK-20260705-B.md",
        "tickets/todos/TCK-20260705-C.md",
        "stored_artifacts/TCK-20260705-D/plan.md",
    }
    assert sum(skip_reasons.values()) == 0


def test_sweep_skips_sequence_md_at_every_level(tmp_path):
    _make_md(tmp_path, "tickets/todos/some-folder/other.md", "tags: [faction]")
    seq_todos = tmp_path / "tickets/todos/some-folder/SEQUENCE.md"
    seq_todos.write_text("# Sequence index\n", encoding="utf-8")
    seq_done = tmp_path / "tickets/done/other-folder/SEQUENCE.md"
    seq_done.parent.mkdir(parents=True, exist_ok=True)
    seq_done.write_text("# Sequence index\n", encoding="utf-8")

    relative_paths, skip_reasons, skipped_paths = collect_sweep_files(tmp_path)

    assert "tickets/todos/some-folder/SEQUENCE.md" not in relative_paths
    assert "tickets/done/other-folder/SEQUENCE.md" not in relative_paths
    assert "tickets/todos/some-folder/other.md" in relative_paths
    assert skip_reasons["sequence_index_file"] == 2
    assert set(skipped_paths["sequence_index_file"]) == {
        "tickets/todos/some-folder/SEQUENCE.md",
        "tickets/done/other-folder/SEQUENCE.md",
    }


def test_sweep_missing_corpus_roots_return_empty(tmp_path):
    relative_paths, skip_reasons, skipped_paths = collect_sweep_files(tmp_path)

    assert relative_paths == []
    assert sum(skip_reasons.values()) == 0
    assert skipped_paths == {}


# ---------------------------------------------------------------------------
# Group 2 — tag_issues
# ---------------------------------------------------------------------------


def test_sweep_flags_unregistered_tag():
    assert tag_issues("some-unregistered-tag", {}, _VALID_CATEGORIES) == ["unregistered"]


def test_sweep_does_not_flag_phase_n_tag_as_unregistered():
    issues = tag_issues("phase-5", {}, _VALID_CATEGORIES)
    assert "unregistered" not in issues
    assert issues == []


def test_sweep_flags_invalid_category_for_registered_tag_with_stale_category():
    registry = {"some-tag": {"tag": "some-tag", "category": "retired-category", "added_date": "2026-01-01", "note": ""}}

    issues = tag_issues("some-tag", registry, _VALID_CATEGORIES)

    assert issues == ["invalid_category"]
    assert "unregistered" not in issues


def test_sweep_invalid_category_does_not_fire_for_unregistered_tag():
    issues = tag_issues("never-registered", {}, frozenset())

    assert issues == ["unregistered"]
    assert "invalid_category" not in issues


def test_sweep_invalid_category_never_fires_for_phase_n_tags():
    issues = tag_issues("phase-5", {}, frozenset())
    assert "invalid_category" not in issues


def test_sweep_flags_non_canonical_form_independent_of_registration():
    # (a) unregistered + non-canonical -> both fire
    unregistered_issues = tag_issues("Combat", {}, _VALID_CATEGORIES)
    assert set(unregistered_issues) == {"unregistered", "non_canonical_form"}

    # (b) registered-but-non-canonical -> only non_canonical_form fires
    registry = {"Combat": {"tag": "Combat", "category": "subsystem-topic", "added_date": "2026-01-01", "note": ""}}
    registered_issues = tag_issues("Combat", registry, _VALID_CATEGORIES)
    assert registered_issues == ["non_canonical_form"]


def test_sweep_multi_issue_tag_produces_multiple_rows():
    registry = {"Some_Tag": {"tag": "Some_Tag", "category": "retired-category", "added_date": "2026-01-01", "note": ""}}

    issues = tag_issues("Some_Tag", registry, _VALID_CATEGORIES)

    assert set(issues) == {"invalid_category", "non_canonical_form"}
    assert len(issues) == 2


# ---------------------------------------------------------------------------
# Group 3 — sweep_file_rows
# ---------------------------------------------------------------------------


def test_sweep_does_not_apply_taxonomy_date_cutoff():
    text = "---\nticket_id: TCK-20260101-OLD\ntags: [totally-unregistered-tag]\n---\n\n# Old\n"

    rows = sweep_file_rows("tickets/done/TCK-20260101-OLD.md", text, {}, _VALID_CATEGORIES)

    assert rows == [
        {"file": "tickets/done/TCK-20260101-OLD.md", "tag": "totally-unregistered-tag", "issue": "unregistered"}
    ]


def test_sweep_does_not_apply_taxonomy_date_cutoff_when_ticket_id_missing():
    text = "---\ntags: [totally-unregistered-tag]\n---\n\n# No ticket_id\n"

    rows = sweep_file_rows("stored_artifacts/legacy/notes.md", text, {}, _VALID_CATEGORIES)

    assert len(rows) == 1
    assert rows[0]["issue"] == "unregistered"


def test_sweep_multi_issue_tag_produces_multiple_rows_via_sweep_file_rows():
    registry = {"Some_Tag": {"tag": "Some_Tag", "category": "retired-category", "added_date": "2026-01-01", "note": ""}}
    text = "---\ntags: [Some_Tag]\n---\n\n# Doc\n"

    rows = sweep_file_rows("stored_artifacts/x/plan.md", text, registry, _VALID_CATEGORIES)

    assert len(rows) == 2
    assert {row["issue"] for row in rows} == {"invalid_category", "non_canonical_form"}
    assert {row["file"] for row in rows} == {"stored_artifacts/x/plan.md"}
    assert {row["tag"] for row in rows} == {"Some_Tag"}


def test_sweep_no_frontmatter_fixture_produces_zero_rows():
    fixture = _REPO_ROOT / "stored_artifacts/TCK-20260623-FIX-INVENTORY-DEFAULTS/plan.md"
    text = fixture.read_text(encoding="utf-8")

    rows = sweep_file_rows(
        "stored_artifacts/TCK-20260623-FIX-INVENTORY-DEFAULTS/plan.md", text, {}, _VALID_CATEGORIES
    )

    assert rows == []


def test_sweep_no_tags_key_fixture_produces_zero_rows():
    fixture = _REPO_ROOT / "stored_artifacts/TCK-20260607-MON-DASHBOARD/investigation.md"
    text = fixture.read_text(encoding="utf-8")

    rows = sweep_file_rows(
        "stored_artifacts/TCK-20260607-MON-DASHBOARD/investigation.md", text, {}, _VALID_CATEGORIES
    )

    assert rows == []


def test_sweep_unparseable_frontmatter_produces_zero_rows_not_a_crash():
    text = "---\nthis line has no colon\n---\n\n# Broken\n"

    rows = sweep_file_rows("tickets/todos/broken.md", text, {}, _VALID_CATEGORIES)

    assert rows == []


# ---------------------------------------------------------------------------
# Group 4 — run_sweep / print_report / build_json_report
# ---------------------------------------------------------------------------


def test_sweep_json_and_stdout_output_shapes_agree_on_row_count(tmp_path, capsys):
    _make_md(tmp_path, "tickets/done/TCK-20260705-A.md", "tags: [some-unregistered-tag, Combat]")
    _make_md(tmp_path, "tickets/todos/TCK-20260705-B.md", "tags: [phase-5]")

    result = run_sweep(tmp_path)
    json_report = build_json_report(result)

    print_report(result)
    captured = capsys.readouterr()
    printed_row_lines = [line for line in captured.out.splitlines() if line.count("\t") == 2]

    assert len(json_report["rows"]) == len(result["rows"])
    assert len(printed_row_lines) == len(result["rows"])
    assert len(result["rows"]) > 0


def test_run_sweep_against_real_corpus_produces_no_crash_and_structural_rows():
    result = run_sweep(_REPO_ROOT)

    assert result["scanned_files"] > 0
    assert isinstance(result["rows"], list)
    for row in result["rows"]:
        assert set(row.keys()) == {"file", "tag", "issue"}
        assert row["issue"] in {"unregistered", "invalid_category", "non_canonical_form"}


# ---------------------------------------------------------------------------
# Group 5 — CLI: report-only guarantees
# ---------------------------------------------------------------------------


def test_sweep_has_no_fix_flag_exposed():
    help_result = subprocess.run(
        [sys.executable, str(_SWEEP_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    usage_line = help_result.stdout.splitlines()[0]
    assert usage_line.startswith("usage:")
    assert "--fix" not in usage_line
    assert "[-f" not in usage_line

    fix_result = subprocess.run(
        [sys.executable, str(_SWEEP_SCRIPT), "--fix"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert fix_result.returncode != 0


def test_sweep_against_real_corpus_produces_zero_filesystem_writes():
    before = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(_REPO_ROOT)
    ).stdout

    result = subprocess.run(
        [sys.executable, str(_SWEEP_SCRIPT), "--root", str(_REPO_ROOT)],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0

    after = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(_REPO_ROOT)
    ).stdout

    assert before == after
