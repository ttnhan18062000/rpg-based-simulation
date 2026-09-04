"""Tests for tools/agent-monitoring/done_ticket_monitoring_coverage.py
(TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT).

Mirrors tests/tools/test_security_gate_firing_check.py's design: synthetic-fixture unit tests for
the classification logic (mocking load_jsonl and a tmp_path tickets/done/ tree), plus a live-corpus
integration test asserting today's known-correct finding — never a tmp_path copy for that
assertion, which would make it vacuous.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "done_ticket_monitoring_coverage.py"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import done_ticket_monitoring_coverage as dtmc  # noqa: E402
from done_ticket_monitoring_coverage import build_coverage_section  # noqa: E402

_MODULE_SOURCE = _MODULE_PATH.read_text()
_MODULE_AST = ast.parse(_MODULE_SOURCE)


def _imported_names() -> set:
    names = set()
    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


def _write_ticket(done_dir: Path, rel_path: str, ticket_id: str | None, extra_frontmatter: str = "") -> None:
    path = done_dir / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if ticket_id is None:
        path.write_text("# No frontmatter here\n", encoding="utf-8")
    else:
        path.write_text(
            f"---\nstatus: active\nlayer: ai\nticket_id: {ticket_id}\n{extra_frontmatter}---\n\n# {ticket_id}\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Reuse-not-reimplement / regression guards
# ---------------------------------------------------------------------------

def test_reuses_shared_load_data_glob_not_a_second_loader():
    imported = _imported_names()
    assert "load_data_glob" in imported
    assert "RUNS_FILE" in imported


def test_never_imports_the_stale_sqlite_index_path():
    """The specific bug this ticket's own Investigate phase found (trusting a lazily-rebuilt,
    stale SQLite index that wrongly reported real same-session tickets as missing) must never
    silently regress back in."""
    imported = _imported_names()
    assert "_load_runs_and_events" not in imported


# ---------------------------------------------------------------------------
# Synthetic-fixture unit tests
# ---------------------------------------------------------------------------

def test_covered_and_missing_classification(tmp_path):
    done_dir = tmp_path / "tickets" / "done"
    _write_ticket(done_dir, "TCK-A.md", "TCK-A")
    _write_ticket(done_dir, "TCK-B.md", "TCK-B")

    fake_runs = [{"run_id": "TCK-A", "final_status": "DONE"}]
    with patch.object(dtmc, "load_data_glob", return_value=fake_runs):
        report = build_coverage_section(done_dir=done_dir)

    assert report["total_done_tickets_checked"] == 2
    assert report["covered_count"] == 1
    assert report["missing_count"] == 1
    assert report["missing"][0]["ticket_id"] == "TCK-B"


def test_legacy_no_frontmatter_ticket_falls_back_to_filename_stem(tmp_path):
    done_dir = tmp_path / "tickets" / "done"
    _write_ticket(done_dir, "METRICS-01.md", None)

    with patch.object(dtmc, "load_data_glob", return_value=[]):
        report = build_coverage_section(done_dir=done_dir)

    assert report["total_done_tickets_checked"] == 1
    assert report["missing"][0]["ticket_id"] == "METRICS-01"
    assert report["unparseable_count"] == 0


def test_sequence_and_readme_index_files_excluded(tmp_path):
    done_dir = tmp_path / "tickets" / "done"
    folder = done_dir / "some-epic-folder"
    folder.mkdir(parents=True)
    (folder / "SEQUENCE.md").write_text("# not a ticket\n", encoding="utf-8")
    (done_dir / "README.md").write_text("# not a ticket\n", encoding="utf-8")
    _write_ticket(done_dir, "some-epic-folder/TCK-C.md", "TCK-C")

    with patch.object(dtmc, "load_data_glob", return_value=[{"run_id": "TCK-C"}]):
        report = build_coverage_section(done_dir=done_dir)

    assert report["total_done_tickets_checked"] == 1


def test_empty_done_dir_produces_empty_report_not_error(tmp_path):
    done_dir = tmp_path / "tickets" / "done"
    done_dir.mkdir(parents=True)
    with patch.object(dtmc, "load_data_glob", return_value=[]):
        report = build_coverage_section(done_dir=done_dir)
    assert report["total_done_tickets_checked"] == 0
    assert report["missing"] == []


def test_missing_done_dir_produces_empty_report_not_error(tmp_path):
    done_dir = tmp_path / "tickets" / "does_not_exist"
    with patch.object(dtmc, "load_data_glob", return_value=[]):
        report = build_coverage_section(done_dir=done_dir)
    assert report["total_done_tickets_checked"] == 0


def test_run_id_with_none_value_never_counts_as_covered(tmp_path):
    done_dir = tmp_path / "tickets" / "done"
    _write_ticket(done_dir, "TCK-D.md", "TCK-D")
    # A malformed run record with run_id=None must not accidentally satisfy any ticket lookup.
    with patch.object(dtmc, "load_data_glob", return_value=[{"run_id": None}]):
        report = build_coverage_section(done_dir=done_dir)
    assert report["missing"][0]["ticket_id"] == "TCK-D"


def test_derivation_string_present_and_explains_freshness_choice():
    with patch.object(dtmc, "load_data_glob", return_value=[]):
        report = build_coverage_section(done_dir=Path("/nonexistent"))
    assert "derivation" in report
    assert "stale" in report["derivation"] or "index" in report["derivation"]


def test_done_ticket_monitoring_coverage_reads_runs_across_multiple_week_folders(tmp_path, monkeypatch):
    done_dir = tmp_path / "tickets" / "done"
    _write_ticket(done_dir, "TCK-WEEK1.md", "TCK-WEEK1")
    _write_ticket(done_dir, "TCK-WEEK2.md", "TCK-WEEK2")

    data_dir = tmp_path / "agent-monitoring" / "data"
    week1 = data_dir / "2026-W01"
    week1.mkdir(parents=True)
    (week1 / "runs.jsonl").write_text(
        json.dumps({"run_id": "TCK-WEEK1", "final_status": "DONE"}) + "\n", encoding="utf-8",
    )
    week2 = data_dir / "2026-W02"
    week2.mkdir(parents=True)
    (week2 / "runs.jsonl").write_text(
        json.dumps({"run_id": "TCK-WEEK2", "final_status": "DONE"}) + "\n", encoding="utf-8",
    )

    monkeypatch.setattr(dtmc, "RUNS_FILE", data_dir)
    report = build_coverage_section(done_dir=done_dir)

    missing_ids = {m["ticket_id"] for m in report["missing"]}
    assert "TCK-WEEK1" not in missing_ids
    assert "TCK-WEEK2" not in missing_ids
    assert report["covered_count"] == 2


# ---------------------------------------------------------------------------
# Live-corpus integration tests — real, known-correct findings
# ---------------------------------------------------------------------------

def test_live_corpus_confirms_the_one_known_current_gap():
    report = build_coverage_section()
    missing_ids = {m["ticket_id"] for m in report["missing"]}
    assert "TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND" in missing_ids


def test_live_corpus_does_not_false_positive_this_sessions_own_recent_tickets():
    # The exact regression the stale-index bug produced — re-derive against the real, current
    # runs.jsonl and confirm these are correctly classified as covered.
    report = build_coverage_section()
    missing_ids = {m["ticket_id"] for m in report["missing"]}
    for real_recent_ticket in (
        "TCK-20260805-COMBAT-SKILL",
        "TCK-20260805-COGNITION-STRATEGY-SKILL",
        "TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX",
    ):
        assert real_recent_ticket not in missing_ids, (
            f"{real_recent_ticket} wrongly reported missing — possible stale-index regression"
        )


def test_cli_runs_against_real_corpus_and_prints_json():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert set(report.keys()) == {
        "total_done_tickets_checked", "covered_count", "missing", "missing_count",
        "unparseable", "unparseable_count", "derivation",
    }


def test_causes_zero_diff_on_real_corpus():
    def _porcelain():
        return subprocess.run(
            ["git", "status", "--porcelain", "--", "agent-monitoring/", "tickets/done/"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
        ).stdout

    pre = _porcelain()
    build_coverage_section()
    post = _porcelain()
    assert pre == post, f"done_ticket_monitoring_coverage mutated tracked state: pre={pre!r} post={post!r}"
