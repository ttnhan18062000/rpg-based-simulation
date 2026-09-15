"""Tests for tools/gate_checks/sidecar_attribution_coverage_check.py
(TCK-20260915-SIDECAR-ATTRIBUTION-GAP, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).
"""
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from sidecar_attribution_coverage_check import (  # noqa: E402
    ATTRIBUTION_RATE_FLOOR,
    check_sidecar_attribution_coverage,
    compute_attribution_rate,
)

_NOW = datetime.now(timezone.utc)


def _row(run_id, days_ago=0):
    ts = (_NOW - timedelta(days=days_ago)).isoformat()
    return {"run_id": run_id, "ts": ts}


def test_passes_on_no_recent_rows():
    old_rows = [_row(None, days_ago=30)]
    results = check_sidecar_attribution_coverage(tools=old_rows, floor=90.0)
    assert results[0]["status"] == "PASS"


def test_compute_attribution_rate():
    rows = [_row("TCK-A"), _row("TCK-B"), _row(None), _row(None)]
    rate, attributed, total = compute_attribution_rate(tools=rows)
    assert total == 4
    assert attributed == 2
    assert rate == 50.0


def test_passes_when_rate_at_or_above_floor():
    rows = [_row("TCK-A"), _row("TCK-B"), _row("TCK-C"), _row(None)]
    results = check_sidecar_attribution_coverage(tools=rows, floor=75.0)
    assert results[0]["status"] == "PASS"


def test_fails_when_rate_drops_below_floor():
    rows = [_row("TCK-A"), _row(None), _row(None), _row(None)]
    results = check_sidecar_attribution_coverage(tools=rows, floor=75.0)
    assert results[0]["status"] == "FAIL"
    assert "25.0%" in results[0]["evidence"]


def test_rows_outside_the_14_day_window_are_excluded():
    rows = [_row("TCK-A", days_ago=0), _row(None, days_ago=100)]
    rate, attributed, total = compute_attribution_rate(tools=rows)
    assert total == 1
    assert rate == 100.0


def test_floor_may_only_increase_never_used_to_paper_over_a_regression():
    assert ATTRIBUTION_RATE_FLOOR == 73.0, (
        "ATTRIBUTION_RATE_FLOOR changed -- if this is because attribution coverage genuinely "
        "improved, raise this value to match (never lower it to paper over a new regression; "
        "see the module's own docstring for why this is a floor ratchet, the mirror image of a "
        "ceiling ratchet)"
    )


def test_real_corpus_is_at_or_above_the_ratchet_floor():
    results = check_sidecar_attribution_coverage()
    assert results[0]["status"] == "PASS", (
        f"real corpus attribution rate dropped below the ratchet floor "
        f"({ATTRIBUTION_RATE_FLOOR}%): {results[0]['evidence']}"
    )


def test_makefile_wires_sidecar_attribution_coverage_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "sidecar-attribution-coverage-check:" in makefile_text
    assert "sidecar_attribution_coverage_check.py" in makefile_text
    assert "sidecar-attribution-coverage-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
