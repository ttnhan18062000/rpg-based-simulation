#!/usr/bin/env python3
"""SimQ standing evaluation harness.

Diffs calibration grades against committed anchors (grade_anchors.json).
Use --dry-run to read existing data/calibration/ reports without re-running the engine.
With no --scenario, an engine re-run (non --dry-run) defaults to fast-tier scenarios only
(<=500t); pass --include-slow to also re-run SLOW-tier (1000t/2000t) scenarios.

Usage:
    python3 tools/evaluate_simq.py --dry-run
    python3 tools/evaluate_simq.py
    python3 tools/evaluate_simq.py --include-slow
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

GRADE_ORDER = ["F", "D", "C", "B", "A", "S"]

DEFAULT_ANCHORS = Path("tests/simulation_quality/fixtures/grade_anchors.json")
CALIBRATION_ROOT = Path("data/calibration")
WORLDS_ROOT = Path("data/worlds")


def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    if actual not in GRADE_ORDER or anchor not in GRADE_ORDER:
        return False
    return abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance


def _extract_pillar_grades(report: dict[str, Any]) -> dict[str, str]:
    return {pillar: data["grade"] for pillar, data in report.get("pillars", {}).items()}


def _parse_run_key(run_key: str) -> tuple[str, int, int]:
    """Split a run_key into (profile_name, seed, ticks).

    The prefix is always the calibration *profile* name (grade_anchors.json
    keys are named after the profile, e.g. `urban_political_selfmodel_probe`),
    which is not necessarily the same as the *world* directory name — see
    `_resolve_world_name`.
    """
    m = re.match(r"^(.+)_seed(\d+)_(\d+)t$", run_key)
    if not m:
        raise ValueError(f"Cannot parse run_key: {run_key!r}")
    return m.group(1), int(m.group(2)), int(m.group(3))


def _resolve_world_name(profile_name: str) -> str:
    """Find the real `data/worlds/{world_name}/` directory backing a profile.

    Profile names are usually identical to their world name, but a profile
    can be a more specific variant of a world (e.g. the probe fixture
    `urban_political_selfmodel_probe` scores the `urban_political` world
    under a different scoring profile). Try the full profile name first,
    then progressively strip trailing `_segment` tokens until a real world
    directory is found.
    """
    segments = profile_name.split("_")
    for cutoff in range(len(segments), 0, -1):
        candidate = "_".join(segments[:cutoff])
        if (WORLDS_ROOT / candidate).is_dir():
            return candidate
    raise ValueError(
        f"Cannot resolve a world directory for profile {profile_name!r} — "
        f"no prefix of it matches a directory under {WORLDS_ROOT}/"
    )


def _load_calibration_report(run_key: str) -> dict[str, Any] | None:
    path = CALIBRATION_ROOT / run_key / "quality_report.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _warn_if_run_health_guard_failed(run_key: str) -> None:
    """--dry-run's non-fatal counterpart to calibrate_simq.py's hard-fail guard.

    literal `make evaluate` (--dry-run) never re-runs the engine, so it cannot
    observe a live queue drop or SURVIVAL entry itself — it can only read back
    the RunHealthRecord sidecar calibrate_simq.py wrote the last time this run_key
    was actually calibrated. Per the ticket's own stated default (hard-fail for
    calibration, warn for ad-hoc evaluation), this warns rather than exits non-zero.
    """
    from src.simulation_quality.run_health import RunHealthRecord

    sidecar_path = CALIBRATION_ROOT / run_key / "quality_report.run_health.json"
    if not sidecar_path.exists():
        print(
            f"WARNING: {run_key!r} has no quality_report.run_health.json — cannot verify "
            "the SimQ event-loss guard for this run (predates this guard, or the sidecar "
            "write failed).",
            file=sys.stderr,
        )
        return
    try:
        health = RunHealthRecord.from_dict(json.loads(sidecar_path.read_text()))
    except Exception as exc:
        print(f"WARNING: {run_key!r} quality_report.run_health.json unreadable: {exc}", file=sys.stderr)
        return
    if not health.guard_passed:
        print(
            f"WARNING: {run_key!r} run integrity guard FAILED last time it was calibrated "
            f"(dropped_count={health.dropped_count}, "
            f"pressure_mode_final={health.pressure_mode_final}, "
            f"survival_triggered={health.survival_triggered}) — grades for this run may be "
            "unreliable. Re-run calibration (without --dry-run) to get a valid report.",
            file=sys.stderr,
        )


def _run_calibration(world_name: str, profile_name: str, seed: int, ticks: int, run_key: str) -> None:
    """Run calibration, writing the report under CALIBRATION_ROOT/{run_key}.

    `--output` must be pinned to `run_key` explicitly: `calibrate_simq.py`'s
    own default output directory is derived from `--name` (the world), which
    only matches `run_key` (derived from the profile) when profile and world
    share a name. `_load_calibration_report` always looks up by `run_key`.
    """
    import tools.calibrate_simq as cal_mod

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "calibrate_simq",
            "--name", world_name,
            "--profile", profile_name,
            "--seed", str(seed),
            "--ticks", str(ticks),
            "--output", str(CALIBRATION_ROOT / run_key),
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


def _select_scenarios(anchor_keys: list[str], scenario: str | None, dry_run: bool, include_slow: bool) -> list[str]:
    """Choose which run_keys to process, per evaluate_simq's own CLI contract.

    An explicit --scenario always wins. --dry-run reads already-computed reports (cheap
    regardless of tier) so it is never tier-filtered. Otherwise (a real engine re-run), default
    to fast-tier only (<=500t) -- matches `make simq-full-audit-full`'s documented contract --
    unless --include-slow opts back into the full corpus. A key that fails to parse is kept
    (treated as fast) rather than silently dropped; its own parse failure is surfaced later by
    the per-scenario loop, not swallowed here.
    """
    if scenario:
        return [scenario]
    if dry_run or include_slow:
        return list(anchor_keys)
    fast_keys = []
    for k in anchor_keys:
        try:
            _, _, ticks = _parse_run_key(k)
        except ValueError:
            fast_keys.append(k)
            continue
        if ticks <= 500:
            fast_keys.append(k)
    return fast_keys


def main() -> None:
    parser = argparse.ArgumentParser(description="SimQ evaluation harness")
    parser.add_argument("--dry-run", action="store_true", help="Read existing calibration data; do not re-run engine")
    parser.add_argument("--scenario", type=str, default=None, help="Run a single scenario by run_key")
    parser.add_argument("--anchors", type=str, default=str(DEFAULT_ANCHORS), help="Path to grade_anchors.json")
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Also re-run SLOW-tier (>500t) scenarios (default engine re-run is fast-tier only, <=500t)",
    )
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

    scenarios = _select_scenarios(anchor_keys, args.scenario, args.dry_run, args.include_slow)

    all_rows: list[dict[str, str]] = []
    missing_count = 0
    error_count = 0

    for run_key in scenarios:
        if run_key not in all_anchors:
            print(f"WARNING: {run_key!r} not in anchor file — skipping", file=sys.stderr)
            continue

        if not args.dry_run:
            try:
                profile_name, seed, ticks = _parse_run_key(run_key)
                world_name = _resolve_world_name(profile_name)
            except ValueError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                error_count += 1
                continue
            print(f"[evaluate] Running engine: {run_key} (world={world_name} profile={profile_name}) ...", flush=True)
            try:
                _run_calibration(world_name, profile_name, seed, ticks, run_key)
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

        if args.dry_run:
            _warn_if_run_health_guard_failed(run_key)

        actual_grades = _extract_pillar_grades(report)
        anchor_grades = {p: v["grade"] for p, v in all_anchors[run_key].items()}
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
