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
    compute_attribution_rate,
)

_NOW = datetime.now(timezone.utc)


def _row(run_id, days_ago=0):
    ts = (_NOW - timedelta(days=days_ago)).isoformat()
    return {"run_id": run_id, "ts": ts}


def test_compute_attribution_rate():
    rows = [_row("TCK-A"), _row("TCK-B"), _row(None), _row(None)]
    rate, attributed, total = compute_attribution_rate(tools=rows)
    assert total == 4
    assert attributed == 2
    assert rate == 50.0


def test_rows_outside_the_14_day_window_are_excluded():
    rows = [_row("TCK-A", days_ago=0), _row(None, days_ago=100)]
    rate, attributed, total = compute_attribution_rate(tools=rows)
    assert total == 1
    assert rate == 100.0


def test_compute_attribution_rate_on_no_recent_rows_returns_none():
    old_rows = [_row(None, days_ago=30)]
    rate, attributed, total = compute_attribution_rate(tools=old_rows)
    assert rate is None
    assert attributed == 0
    assert total == 0


def test_makefile_wires_sidecar_attribution_coverage_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "sidecar-attribution-coverage-check:" in makefile_text
    assert "sidecar_attribution_coverage_check.py" in makefile_text
    assert "sidecar-attribution-coverage-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )
