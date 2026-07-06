#!/usr/bin/env python3
"""SimQ standing evaluation harness.

Diffs calibration grades against committed anchors (grade_anchors.json).
Use --dry-run to read existing data/calibration/ reports without re-running the engine.

Usage:
    python3 tools/evaluate_simq.py --dry-run
    python3 tools/evaluate_simq.py
    python3 tools/evaluate_simq.py --scenario dungeon_crawl_seed42_200t --dry-run

Exit codes:
    0 — all scenarios pass within ±1 band (MISSING treated as warning, not error)
    1 — at least one REGRESS detected
    2 — setup error (anchor file missing, invalid JSON, or unknown grade)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

GRADE_ORDER = ["D", "C", "B", "A", "S"]

DEFAULT_ANCHORS = Path("tests/simulation_quality/fixtures/grade_anchors.json")
CALIBRATION_ROOT = Path("data/calibration")


def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    if actual not in GRADE_ORDER or anchor not in GRADE_ORDER:
        return False
    return abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance


def _extract_pillar_grades(report: dict[str, Any]) -> dict[str, str]:
    return {pillar: data["grade"] for pillar, data in report.get("pillars", {}).items()}


def _parse_run_key(run_key: str) -> tuple[str, int, int]:
    m = re.match(r"^(.+)_seed(\d+)_(\d+)t$", run_key)
    if not m:
        raise ValueError(f"Cannot parse run_key: {run_key!r}")
    return m.group(1), int(m.group(2)), int(m.group(3))


def _load_calibration_report(run_key: str) -> dict[str, Any] | None:
    path = CALIBRATION_ROOT / run_key / "quality_report.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _run_calibration(name: str, seed: int, ticks: int) -> None:
    import tools.calibrate_simq as cal_mod

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "calibrate_simq",
            "--name", name,
            "--seed", str(seed),
            "--ticks", str(ticks),
        ]
        cal_mod.main()
    finally:
        sys.argv = old_argv


def _compare(
    run_key: str,
    actual_grades: dict[str, str],
    anchor_grades: dict[str, str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pillar, anchor in anchor_grades.items():
        actual = actual_grades.get(pillar)
        if actual is None:
            rows.append({"run_key": run_key, "pillar": pillar, "anchor": anchor, "actual": "—", "status": "MISSING"})
        elif _within_band(actual, anchor):
            rows.append({"run_key": run_key, "pillar": pillar, "anchor": anchor, "actual": actual, "status": "PASS"})
        else:
            rows.append({"run_key": run_key, "pillar": pillar, "anchor": anchor, "actual": actual, "status": "REGRESS"})
    return rows


def _print_table(rows: list[dict[str, str]]) -> None:
    header = f"{'run_key':<40}  {'pillar':<12}  {'anchor':<7}  {'actual':<7}  {'status':<8}"
    print(header)
    print("-" * len(header))
    for r in rows:
        marker = "  <<" if r["status"] == "REGRESS" else ""
        print(
            f"{r['run_key']:<40}  {r['pillar']:<12}  {r['anchor']:<7}  {r['actual']:<7}  {r['status']:<8}{marker}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="SimQ evaluation harness")
    parser.add_argument("--dry-run", action="store_true", help="Read existing calibration data; do not re-run engine")
    parser.add_argument("--scenario", type=str, default=None, help="Run a single scenario by run_key")
    parser.add_argument("--anchors", type=str, default=str(DEFAULT_ANCHORS), help="Path to grade_anchors.json")
    args = parser.parse_args()

    anchors_path = Path(args.anchors)
    if not anchors_path.exists():
        print(f"ERROR: anchor file not found: {anchors_path}", file=sys.stderr)
        sys.exit(2)
    try:
        all_anchors: dict[str, Any] = json.loads(anchors_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {anchors_path}: {exc}", file=sys.stderr)
        sys.exit(2)

    # Strip metadata keys (start with _)
    anchor_keys = [k for k in all_anchors if not k.startswith("_")]

    if args.scenario:
        scenarios = [args.scenario]
    else:
        scenarios = anchor_keys

    all_rows: list[dict[str, str]] = []
    missing_count = 0
    error_count = 0

    for run_key in scenarios:
        if run_key not in all_anchors:
            print(f"WARNING: {run_key!r} not in anchor file — skipping", file=sys.stderr)
            continue

        if not args.dry_run:
            try:
                name, seed, ticks = _parse_run_key(run_key)
            except ValueError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                error_count += 1
                continue
            print(f"[evaluate] Running engine: {run_key} ...", flush=True)
            try:
                _run_calibration(name, seed, ticks)
            except SystemExit:
                pass
            except Exception as exc:
                print(f"ERROR: calibration failed for {run_key}: {exc}", file=sys.stderr)
                error_count += 1
                continue

        report = _load_calibration_report(run_key)
        if report is None:
            print(f"WARNING: no calibration report for {run_key} — skipping", file=sys.stderr)
            missing_count += 1
            continue

        actual_grades = _extract_pillar_grades(report)
        anchor_grades = all_anchors[run_key]
        rows = _compare(run_key, actual_grades, anchor_grades)
        all_rows.extend(rows)

    if error_count > 0:
        sys.exit(2)

    _print_table(all_rows)
    print()

    total = len(all_rows)
    regressions = sum(1 for r in all_rows if r["status"] == "REGRESS")
    missing = sum(1 for r in all_rows if r["status"] == "MISSING")
    print(f"Summary: {total} pillars checked — {regressions} regressions — {missing} missing")

    if regressions > 0:
        print(f"\n  {regressions} REGRESS pillar(s) detected. Update anchors or fix the regression.")
        sys.exit(1)
    if missing_count > 0:
        print(f"\n  {missing_count} scenario(s) had no calibration data (run without --dry-run to generate).")

    sys.exit(0)


if __name__ == "__main__":
    main()
