"""Tests for tools/agent-monitoring/verify_referential_integrity.py
(TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY).

Mirrors tests/tools/test_migrate_monitoring_data.py's own structure: synthetic-
fixture unit tests against a hand-built tmp_path multi-week directory tree (never
the real agent-monitoring/data/ directory for these), then one real-corpus smoke
test at the end.

The cross-week test (test_cross_week_run_id_not_flagged) is the single most
important guard in this suite — it is the one test a same-week-scoped
implementation would fail while passing every other test trivially. Its fixture is
modeled on real corpus shapes confirmed in investigation.md (e.g.
TCK-20260820-EPIC-WORLD-RENDERING-CORE's runs-in-W34/events-in-W35 split), not a
synthetic guess.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "agent-monitoring"))

from verify_referential_integrity import compute_referential_integrity_report  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_DATA_DIR = _REPO_ROOT / "agent-monitoring" / "data"


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n" if records else "")


# ---------------------------------------------------------------------------
# 1. Baseline correctness (Scope scenario a)
# ---------------------------------------------------------------------------

def test_same_week_only_join_baseline(tmp_path):
    data_dir = tmp_path / "data"
    week = data_dir / "2026-W10"
    _write_jsonl(week / "runs.jsonl", [{"run_id": "TCK-BASELINE", "tier": "hotfix"}])
    _write_jsonl(week / "events.jsonl", [{"run_id": "TCK-BASELINE", "seq": 1, "phase": "Implement"}])
    _write_jsonl(week / "tools.jsonl", [{"run_id": "TCK-BASELINE", "seq": 1, "tool": "Read"}])

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.events_violations == []
    assert report.tools_violations == []
    assert report.events_checked == 1
    assert report.tools_checked == 1


# ---------------------------------------------------------------------------
# 2. Cross-week join — the highest-priority correctness guard
# ---------------------------------------------------------------------------

def test_cross_week_run_id_not_flagged(tmp_path):
    data_dir = tmp_path / "data"
    run_id = "TCK-CROSSWEEK-EPIC"
    # runs.jsonl row lands in W10; events/tools for the same run_id land in W11 —
    # mirroring the real corpus's confirmed TCK-20260820-EPIC-WORLD-RENDERING-CORE
    # W34-runs/W35-events split (investigation.md's Real Corpus Characteristics).
    _write_jsonl(data_dir / "2026-W10" / "runs.jsonl", [{"run_id": run_id, "tier": "epic"}])
    _write_jsonl(
        data_dir / "2026-W11" / "events.jsonl",
        [{"run_id": run_id, "seq": 1, "phase": "Implement"}],
    )
    _write_jsonl(
        data_dir / "2026-W11" / "tools.jsonl",
        [{"run_id": run_id, "seq": 1, "tool": "Edit"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.events_violations == [], (
        "a run_id whose events row lands in a different week folder than its own "
        "runs.jsonl row must NOT be flagged — a same-week-scoped implementation "
        "would fail this assertion"
    )
    assert report.tools_violations == [], (
        "a tools row must be matched against events across ALL week folders, not "
        "just the tools row's own week folder"
    )


# ---------------------------------------------------------------------------
# 3. Genuine orphans must be flagged (Scope scenarios c, d)
# ---------------------------------------------------------------------------

def test_orphan_tools_row_no_matching_event_anywhere_is_flagged(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(data_dir / "2026-W12" / "events.jsonl", [{"run_id": "TCK-OTHER", "seq": 1}])
    _write_jsonl(
        data_dir / "2026-W12" / "tools.jsonl",
        [{"run_id": "TCK-ORPHAN-TOOLS", "seq": 5, "tool": "Bash"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert len(report.tools_violations) == 1
    violation = report.tools_violations[0]
    assert violation["run_id"] == "TCK-ORPHAN-TOOLS"
    assert violation["seq"] == 5
    assert violation["week_folder"] == "2026-W12"


def test_orphan_event_no_matching_run_anywhere_is_flagged(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(data_dir / "2026-W13" / "runs.jsonl", [{"run_id": "TCK-OTHER-RUN"}])
    _write_jsonl(
        data_dir / "2026-W13" / "events.jsonl",
        [{"run_id": "TCK-ORPHAN-EVENT", "seq": 2, "phase": "Scope"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert len(report.events_violations) == 1
    violation = report.events_violations[0]
    assert violation["run_id"] == "TCK-ORPHAN-EVENT"
    assert violation["week_folder"] == "2026-W13"


# ---------------------------------------------------------------------------
# 4. Documented exceptions must NOT be flagged (Scope scenario e)
# ---------------------------------------------------------------------------

def test_retrieval_event_run_id_excluded_from_check(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "2026-W14" / "events.jsonl",
        [{"run_id": "RETRIEVAL-EVENT-some-slug", "seq": 1, "phase": "retrieval"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.events_violations == []
    assert report.events_checked == 0


def test_null_run_id_tools_row_excluded_from_check(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "2026-W15" / "tools.jsonl",
        [{"run_id": None, "seq": 1, "tool": "Read"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.tools_violations == []
    assert report.tools_checked == 0


def test_negative_and_zero_seq_tools_rows_excluded_from_check(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "2026-W16" / "tools.jsonl",
        [
            {"run_id": "TCK-SHADOW", "seq": -1, "tool": "Read"},
            {"run_id": "TCK-SHADOW", "seq": 0, "tool": "Read"},
        ],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.tools_violations == []
    assert report.tools_checked == 0


# ---------------------------------------------------------------------------
# 5. Anti-drift / regression-prone-path guards, derived from real corpus findings
# ---------------------------------------------------------------------------

def test_duplicate_event_key_does_not_break_lookup(tmp_path):
    data_dir = tmp_path / "data"
    # Two distinct events rows sharing one (run_id, seq) key — the real corpus has
    # 145 such keys (legacy-schema duplicate alongside a current-schema record).
    _write_jsonl(
        data_dir / "2026-W17" / "events.jsonl",
        [
            {"run_id": "TCK-DUP-KEY", "seq": 1, "phase": "Scope", "schema_gen": "legacy"},
            {"run_id": "TCK-DUP-KEY", "seq": 1, "phase": "Scope", "schema_gen": "current"},
        ],
    )
    _write_jsonl(
        data_dir / "2026-W17" / "tools.jsonl",
        [{"run_id": "TCK-DUP-KEY", "seq": 1, "tool": "Read"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.tools_violations == []


def test_unknown_week_folder_included_in_join(tmp_path):
    data_dir = tmp_path / "data"
    # Case 1: run in unknown-week, event in a real ISO week.
    _write_jsonl(data_dir / "unknown-week" / "runs.jsonl", [{"run_id": "TCK-UNKNOWN-A"}])
    _write_jsonl(
        data_dir / "2026-W18" / "events.jsonl",
        [{"run_id": "TCK-UNKNOWN-A", "seq": 1, "phase": "Implement"}],
    )
    # Case 2: event in unknown-week, run in a real ISO week.
    _write_jsonl(data_dir / "2026-W18" / "runs.jsonl", [{"run_id": "TCK-UNKNOWN-B"}])
    _write_jsonl(
        data_dir / "unknown-week" / "events.jsonl",
        [{"run_id": "TCK-UNKNOWN-B", "seq": 1, "phase": "Implement"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)

    assert report.events_violations == []


# ---------------------------------------------------------------------------
# 6. Report format contract (AC #4)
# ---------------------------------------------------------------------------

def test_report_output_matches_validate_py_style(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(data_dir / "2026-W19" / "events.jsonl", [{"run_id": "TCK-ORPHAN", "seq": 1}])
    _write_jsonl(
        data_dir / "2026-W19" / "tools.jsonl",
        [{"run_id": "TCK-ORPHAN-TOOLS", "seq": 1, "tool": "Read"}],
    )

    report = compute_referential_integrity_report(data_dir=data_dir)
    text = report.to_text()

    assert "Check 1: events.run_id -> runs.run_id" in text
    assert "Check 2: tools.(run_id, seq) -> events.(run_id, seq)" in text
    assert "Violations" in text
    assert str(len(report.events_violations)) in text
    assert str(len(report.tools_violations)) in text
    # Concrete sample, not just a boolean.
    assert "TCK-ORPHAN-TOOLS" in text


# ---------------------------------------------------------------------------
# 7. Real-corpus smoke test — does NOT assert zero violations
# ---------------------------------------------------------------------------

def test_real_corpus_smoke_run():
    report = compute_referential_integrity_report(data_dir=_REAL_DATA_DIR)

    assert report.events_checked >= 0
    assert report.tools_checked >= 0
    assert isinstance(report.events_violations, list)
    assert isinstance(report.tools_violations, list)
    # Deliberately NOT asserting zero violations — investigation.md documents
    # ~17,274 real Check-2 orphans and 18 real Check-1 orphans currently existing
    # in the corpus; asserting zero here would be false on its face.
    text = report.to_text()
    assert "Referential Integrity Report" in text
