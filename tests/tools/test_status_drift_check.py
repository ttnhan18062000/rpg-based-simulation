"""Tests for tools/gate_checks/status_drift_check.py (TCK-20260718-STATUS-DRIFT-REPAIR).

Coverage-honesty requirement (SEQUENCE.md decision 4, see workflow_meta_conformance's own test
module): every check function below has at least one fixture proving it catches a real violation
it claims to catch, not just that it runs on the happy path.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.status_drift_check import (  # noqa: E402
    check_runs_jsonl_final_status_drift,
    check_status_drift,
    check_ticket_status_drift,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_MODULE_PATH = _REPO_ROOT / "tools" / "gate_checks" / "status_drift_check.py"


def _write_ticket(tmp_path, name, status_body, blank_line=False):
    sep = "\n\n" if blank_line else "\n"
    (tmp_path / name).write_text(
        "---\nstatus: historical\n---\n\n"
        f"# {name}\n\n## Title\nFixture\n\n## Status{sep}{status_body}\n\n## Tier\nstandard\n"
    )


def _write_runs_jsonl(tmp_path, records, filename="runs.jsonl"):
    path = tmp_path / filename
    path.write_text("\n".join(json.dumps(r) for r in records) + ("\n" if records else ""))
    return path


# ---------------------------------------------------------------------------
# check_ticket_status_drift
# ---------------------------------------------------------------------------


def test_clean_corpus_passes(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-CLEAN-A.md", "DONE")
    _write_ticket(tmp_path, "TCK-20260101-CLEAN-B.md", "DONE", blank_line=True)
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_stale_ticket_status_flagged(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-STALE.md", "OPEN")
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "TCK-20260101-STALE.md" in results[0]["evidence"]
    assert "OPEN" in results[0]["evidence"]


def test_epic_tier_exception_ignored_by_value(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-EPIC-A.md", "EPIC_SCOPED")
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_bare_scoped_no_longer_exempt_after_tightening(tmp_path):
    # TCK-20260718-STATUS-FACET-CANONICAL tightened EPIC_TIER_VALUES from
    # {"EPIC_SCOPED", "SCOPED"} to {"EPIC_SCOPED"} once the corpus's one remaining bare "SCOPED"
    # ticket was normalized by the predecessor STATUS-MULTILINE-FIX ticket — the dashboard's own
    # canonical statuses list only recognizes EPIC_SCOPED, so this checker must reject exactly what
    # the dashboard wouldn't recognize as canonical, not more.
    _write_ticket(tmp_path, "TCK-20260101-EPIC-B.md", "SCOPED")
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "SCOPED" in results[0]["evidence"]


def test_legacy_naming_file_ignored_by_pattern(tmp_path):
    _write_ticket(tmp_path, "resource_v2_fixture_e9_9.md", "OPEN")
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_same_line_colon_status_format_not_newly_flagged(tmp_path):
    (tmp_path / "TCK-20260101-COLON-FORMAT.md").write_text(
        "---\nstatus: historical\n---\n\n# fixture\n\n## Status: INPROGRESS\n\n## Tier\nstandard\n"
    )
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# check_runs_jsonl_final_status_drift
# ---------------------------------------------------------------------------


def test_lowercase_final_status_flagged(tmp_path):
    runs_path = _write_runs_jsonl(tmp_path, [
        {"run_id": "TCK-FIXTURE-1", "final_status": "done"},
    ])
    results = check_runs_jsonl_final_status_drift(runs_path)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "TCK-FIXTURE-1" in results[0]["evidence"]


def test_legacy_runs_jsonl_shape_ignored(tmp_path):
    runs_path = _write_runs_jsonl(tmp_path, [
        {"run_id": "LEGACY-1", "status": "done", "started_at": "2026-01-01T00:00:00Z"},
    ])
    results = check_runs_jsonl_final_status_drift(runs_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_runs_jsonl_clean_uppercase_passes(tmp_path):
    runs_path = _write_runs_jsonl(tmp_path, [
        {"run_id": "TCK-FIXTURE-2", "final_status": "DONE"},
    ])
    results = check_runs_jsonl_final_status_drift(runs_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# check_status_drift — aggregate
# ---------------------------------------------------------------------------


def test_check_status_drift_aggregates_both_scans(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-STALE.md", "OPEN")
    runs_path = _write_runs_jsonl(tmp_path, [
        {"run_id": "TCK-FIXTURE-1", "final_status": "done"},
    ])
    results = check_status_drift(tmp_path, runs_path)
    statuses = {r["status"] for r in results}
    assert statuses == {"FAIL"}
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Architecture guard — read-only
# ---------------------------------------------------------------------------


def test_check_is_read_only(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-STALE.md", "OPEN")
    runs_path = _write_runs_jsonl(tmp_path, [
        {"run_id": "TCK-FIXTURE-1", "final_status": "done"},
    ])
    ticket_path = tmp_path / "TCK-20260101-STALE.md"
    before_ticket = ticket_path.read_bytes()
    before_ticket_mtime = os.path.getmtime(ticket_path)
    before_runs = runs_path.read_bytes()
    before_runs_mtime = os.path.getmtime(runs_path)

    check_status_drift(tmp_path, runs_path)

    assert ticket_path.read_bytes() == before_ticket
    assert os.path.getmtime(ticket_path) == before_ticket_mtime
    assert runs_path.read_bytes() == before_runs
    assert os.path.getmtime(runs_path) == before_runs_mtime


# ---------------------------------------------------------------------------
# CLI contract — MARKER:-prefixed JSON, non-zero exit on FAIL
# ---------------------------------------------------------------------------


def test_marker_json_output_contract(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-CLEAN.md", "DONE")
    runs_path = _write_runs_jsonl(tmp_path, [{"run_id": "TCK-FIXTURE-1", "final_status": "DONE"}])

    proc = subprocess.run(
        [sys.executable, str(_MODULE_PATH), str(tmp_path), str(runs_path)],
        capture_output=True, text=True, check=True,
    )
    output_line = proc.stdout.strip()
    assert output_line.startswith("MARKER:")
    payload = json.loads(output_line[len("MARKER:"):])
    assert isinstance(payload, list)
    for entry in payload:
        assert set(entry.keys()) == {"status", "evidence"}
        assert entry["status"] in {"PASS", "FAIL"}


def test_exit_code_nonzero_on_any_fail_zero_on_clean(tmp_path):
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    _write_ticket(clean_dir, "TCK-20260101-CLEAN.md", "DONE")
    clean_runs = _write_runs_jsonl(clean_dir, [{"run_id": "TCK-FIXTURE-1", "final_status": "DONE"}])

    clean_proc = subprocess.run(
        [sys.executable, str(_MODULE_PATH), str(clean_dir), str(clean_runs)],
        capture_output=True, text=True,
    )
    assert clean_proc.returncode == 0

    stale_dir = tmp_path / "stale"
    stale_dir.mkdir()
    _write_ticket(stale_dir, "TCK-20260101-STALE.md", "OPEN")
    stale_runs = _write_runs_jsonl(stale_dir, [{"run_id": "TCK-FIXTURE-1", "final_status": "DONE"}])

    stale_proc = subprocess.run(
        [sys.executable, str(_MODULE_PATH), str(stale_dir), str(stale_runs)],
        capture_output=True, text=True,
    )
    assert stale_proc.returncode != 0


# ---------------------------------------------------------------------------
# Multi-line body extraction (TCK-20260718-STATUS-MULTILINE-FIX) — the checker now uses
# parse_body_section directly instead of a first-token-only regex, so it must catch shapes the old
# regex silently passed as "DONE" while the real dashboard showed a garbled multi-line value.
# ---------------------------------------------------------------------------


def test_uses_real_dashboard_extraction_function(tmp_path):
    """Anti-drift guard: this module must call the same parse_body_section the dashboard's
    ingest.py uses, not a reimplemented regex — see TCK-20260718-STATUS-MULTILINE-FIX."""
    import gate_checks.status_drift_check as module
    from generate_registry import parse_body_section as real_parse_body_section
    assert module.parse_body_section is real_parse_body_section


def test_stray_trailing_line_after_done_flagged(tmp_path):
    """A leftover 'INPROGRESS' line directly under 'DONE' (no blank line) — the old first-token
    regex captured only 'DONE' and missed this; parse_body_section captures the whole multi-line
    block, exactly as the dashboard does."""
    _write_ticket(tmp_path, "TCK-20260101-STRAY-LINE.md", "DONE\nINPROGRESS")
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "STRAY-LINE" in results[0]["evidence"]


def test_done_bleeding_into_trailing_bold_block_flagged(tmp_path):
    """A legacy-format file with no '## Tier' heading after '## Status' — DONE bleeds into a
    trailing bold-text block because there's no next '## ' heading to stop the section at."""
    (tmp_path / "TCK-20260101-BOLD-BLEED.md").write_text(
        "---\nstatus: historical\n---\n\n# fixture\n\n## Status\nDONE\n\n"
        "**Tier:** standard\n**Type:** chore\n**Priority:** P1\n"
    )
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "BOLD-BLEED" in results[0]["evidence"]
    assert "Tier" in results[0]["evidence"]


def test_done_with_trailing_content_after_proper_tier_heading_passes(tmp_path):
    """Once a file has a real '## Tier' heading, DONE resolves cleanly again — proves the fix is
    the missing-heading-boundary bug, not a blanket rejection of anything after DONE."""
    _write_ticket(tmp_path, "TCK-20260101-CLEAN-TIER.md", "DONE")
    results = check_ticket_status_drift(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"
