"""Tests for tools/agent-monitoring/verify_temporal_week_consistency.py
(TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK).

Mirrors tests/tools/test_verify_referential_integrity.py's own structure:
synthetic-fixture unit tests against a hand-built tmp_path multi-week directory
tree, then one real-corpus smoke test at the end.

test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly is the
single most important correctness guard in this suite — a naive, uniform
"flag every mismatch the same way" implementation passes every other test in this
file trivially while failing this one, and would immediately false-positive on
the first real long-running/paused ticket that crosses an ISO-week boundary.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "agent-monitoring"))

import migrate_monitoring_data  # noqa: E402
import verify_temporal_week_consistency as vtwc  # noqa: E402
from verify_temporal_week_consistency import (  # noqa: E402
    compute_temporal_week_consistency_report,
    GENUINE_ANOMALY,
    EXPECTED_DIVERGENCE,
    TOOLS_FIELD_PRIORITY,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_DATA_DIR = _REPO_ROOT / "agent-monitoring" / "data"


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n" if records else "")


# ---------------------------------------------------------------------------
# 1. tools.jsonl baseline — match, no finding
# ---------------------------------------------------------------------------

def test_tools_ts_matches_folder_no_finding(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "2026-W10" / "tools.jsonl",
        [{"run_id": "TCK-BASELINE", "seq": 1, "tool": "Read", "ts": "2026-03-04T12:00:00.000Z"}],
    )

    report = compute_temporal_week_consistency_report(data_dir=data_dir)

    assert report.tools.mismatches == []
    assert report.tools.checked == 1
    assert report.tools.matched == 1


# ---------------------------------------------------------------------------
# 2. tools.jsonl mismatch — genuine anomaly
# ---------------------------------------------------------------------------

def test_tools_ts_mismatch_flagged_as_genuine_anomaly(tmp_path):
    data_dir = tmp_path / "data"
    # ts is in 2026-W10, but the row physically lives in the 2026-W11 folder.
    _write_jsonl(
        data_dir / "2026-W11" / "tools.jsonl",
        [{"run_id": "TCK-ANOMALY", "seq": 3, "tool": "Bash", "ts": "2026-03-04T12:00:00.000Z"}],
    )

    report = compute_temporal_week_consistency_report(data_dir=data_dir)

    assert len(report.tools.mismatches) == 1
    violation = report.tools.mismatches[0]
    assert violation["run_id"] == "TCK-ANOMALY"
    assert violation["seq"] == 3
    assert violation["computed_week"] == "2026-W10"
    assert violation["week_folder"] == "2026-W11"
    assert report.tools.category_label == GENUINE_ANOMALY
    # Must not be lumped into any other source's bucket.
    assert report.events.mismatches == []
    assert report.runs.mismatches == []


# ---------------------------------------------------------------------------
# 3. runs.jsonl earlier-week divergence — expected, NOT an anomaly
#    (highest-priority correctness guard in this suite)
# ---------------------------------------------------------------------------

def test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly(tmp_path):
    data_dir = tmp_path / "data"
    # start_ts is in 2026-W10 (session start of a long-running ticket), but the
    # runs.jsonl row is written (and physically lands) in 2026-W14.
    _write_jsonl(
        data_dir / "2026-W14" / "runs.jsonl",
        [
            {
                "run_id": "TCK-LONGRUNNING",
                "start_ts": "2026-03-04T12:00:00.000Z",
                "tier": "epic",
            }
        ],
    )

    report = compute_temporal_week_consistency_report(data_dir=data_dir)

    assert report.runs.category_label == EXPECTED_DIVERGENCE
    assert len(report.runs.mismatches) == 1
    violation = report.runs.mismatches[0]
    assert violation["run_id"] == "TCK-LONGRUNNING"
    assert violation["computed_week"] == "2026-W10"
    assert violation["week_folder"] == "2026-W14"
    # Must NOT be present in tools' or events' genuine-anomaly-style bucket.
    assert report.tools.mismatches == []
    assert report.events.mismatches == []
    # A naive uniform implementation would tag this "genuine anomaly" — guard
    # against that regression explicitly.
    assert report.runs.category_label != GENUINE_ANOMALY


# ---------------------------------------------------------------------------
# 4. unknown-week exemption — one record per source
# ---------------------------------------------------------------------------

def test_unknown_week_records_exempt_no_finding_either_way(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "unknown-week" / "tools.jsonl",
        [{"run_id": "TCK-UNKNOWN", "seq": 1, "tool": "Read"}],
    )
    _write_jsonl(
        data_dir / "unknown-week" / "events.jsonl",
        [{"run_id": "TCK-UNKNOWN", "seq": 1, "phase": "Scope"}],
    )
    _write_jsonl(
        data_dir / "unknown-week" / "runs.jsonl",
        [{"run_id": "TCK-UNKNOWN", "start_ts": 1781425809.0960267}],
    )

    report = compute_temporal_week_consistency_report(data_dir=data_dir)

    for finding in (report.tools, report.events, report.runs):
        assert finding.exempt_unknown_week == 1, finding
        assert finding.matched == 0, finding
        assert finding.mismatches == [], finding
        assert finding.checked == 0, finding


# ---------------------------------------------------------------------------
# 5. No usable timestamp field in a known folder — skipped, not match/mismatch
# ---------------------------------------------------------------------------

def test_no_usable_timestamp_field_in_known_folder_skipped_not_counted_as_match_or_mismatch(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "2026-W20" / "runs.jsonl",
        [{"run_id": "TCK-NOFIELD", "tier": "hotfix"}],
    )

    report = compute_temporal_week_consistency_report(data_dir=data_dir)

    assert report.runs.skipped_unparseable == 1
    assert report.runs.checked == 0
    assert report.runs.matched == 0
    assert report.runs.mismatches == []
    assert report.runs.exempt_unknown_week == 0


# ---------------------------------------------------------------------------
# 6. Field-priority lists genuinely imported, not re-declared
# ---------------------------------------------------------------------------

def test_field_priority_reused_from_migration_not_reinvented():
    assert vtwc.RUNS_FIELD_PRIORITY is migrate_monitoring_data.RUNS_FIELD_PRIORITY
    assert vtwc.EVENTS_FIELD_PRIORITY is migrate_monitoring_data.EVENTS_FIELD_PRIORITY
    # tools.jsonl's single-field constant is a new, independent constant — not a
    # violation of the "import, don't re-type" guard (see module docstring).
    assert TOOLS_FIELD_PRIORITY == ["ts"]


# ---------------------------------------------------------------------------
# 7. Report text distinguishes anomaly from expected divergence unambiguously
# ---------------------------------------------------------------------------

def test_report_distinguishes_anomaly_from_expected_divergence_in_text(tmp_path):
    data_dir = tmp_path / "data"
    _write_jsonl(
        data_dir / "2026-W21" / "tools.jsonl",
        [{"run_id": "TCK-ANOMALY-TXT", "seq": 1, "tool": "Read", "ts": "2026-01-01T00:00:00.000Z"}],
    )
    _write_jsonl(
        data_dir / "2026-W21" / "runs.jsonl",
        [{"run_id": "TCK-DIVERGENCE-TXT", "start_ts": "2026-01-01T00:00:00.000Z"}],
    )

    report = compute_temporal_week_consistency_report(data_dir=data_dir)
    text = report.to_text()

    assert "GENUINE ANOMALIES" in text
    assert "EXPECTED DIVERGENCE" in text
    assert "NOT BUGS" in text
    assert "POSSIBLE DIVERGENCES" in text
    # The two category labels must not appear in the same source's section only —
    # confirm both concrete findings' counts are present.
    assert str(len(report.tools.mismatches)) in text
    assert str(len(report.runs.mismatches)) in text
    assert "TCK-ANOMALY-TXT" in text
    assert "TCK-DIVERGENCE-TXT" in text


# ---------------------------------------------------------------------------
# 8. Real-corpus smoke test — does NOT assert zero mismatches
# ---------------------------------------------------------------------------

def test_real_corpus_smoke_run():
    report = compute_temporal_week_consistency_report(data_dir=_REAL_DATA_DIR)

    for finding in (report.tools, report.events, report.runs):
        assert finding.checked >= 0
        assert finding.matched >= 0
        assert finding.exempt_unknown_week >= 0
        assert finding.skipped_unparseable >= 0
        assert isinstance(finding.mismatches, list)

    text = report.to_text()
    assert "Temporal Week Consistency Report" in text
