# Compliance IDs: PERF-013
import json
import sys
import logging
from pathlib import Path

# Milestone 6: Performance Regression Gate
# Logic ID: RPG-PERF-013 (Regression Detection)
# Policy: max(baseline * 1.15, baseline + 3.0ms)
#
# Exit codes (a local convention for this unwired tool; PERF-M2-T03 replaces it with the
# contract's outcome vocabulary):
#   0  every baseline was compared and none regressed
#   1  at least one regression
#   2  no regression, but a scenario was not comparable (different profile or length, missing or
#      malformed report) or nothing was compared at all
# (TCK-20261004-PERF-REGRESSION-CHECK-NO-SILENT-PASS)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Thresholds
RELATIVE_THRESHOLD = 1.15  # 15% regression allowed
ABSOLUTE_THRESHOLD_MS = 3.0 # 3ms absolute regression allowed
MEMORY_RSS_LIMIT_MB = 20.0  # 20MB absolute RSS growth allowed

BASELINE_DIR = Path("tests/perf/baselines")
REPORT_DIR = Path("reports/perf")

EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_NOT_COMPARABLE = 2


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _load(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return None, f"cannot read {path}: {e}"
    if not isinstance(data, dict):
        return None, f"{path} is not a JSON object"
    return data, None


def not_comparable_reason(baseline, latest):
    """Return why two records cannot be compared, or None when they can."""
    problems = []
    for field in ("profile", "sample_ticks"):
        if field not in baseline or field not in latest:
            missing = [side for side, rec in (("baseline", baseline), ("report", latest)) if field not in rec]
            problems.append(f"{field} missing from {' and '.join(missing)}")
        elif baseline[field] != latest[field]:
            problems.append(f"{field} differs: baseline={baseline[field]!r} report={latest[field]!r}")
    if "warmup_ticks" in baseline and "warmup_ticks" in latest and baseline["warmup_ticks"] != latest["warmup_ticks"]:
        problems.append(
            f"warmup_ticks differs: baseline={baseline['warmup_ticks']!r} report={latest['warmup_ticks']!r}"
        )
    for side, rec in (("baseline", baseline), ("report", latest)):
        if not _is_number((rec.get("tick_ms") or {}).get("avg") if isinstance(rec.get("tick_ms"), dict) else None):
            problems.append(f"{side} has no numeric tick_ms.avg")
        if not _is_number((rec.get("mem_rss_mb") or {}).get("max") if isinstance(rec.get("mem_rss_mb"), dict) else None):
            problems.append(f"{side} has no numeric mem_rss_mb.max")
    return "; ".join(problems) if problems else None


def check_regression(baseline_dir=None, report_dir=None):
    """
    Compare current performance reports against committed baselines.
    Returns an exit code: 0 passed, 1 regressions detected, 2 not comparable (see module header).
    """
    baseline_dir = Path(baseline_dir) if baseline_dir is not None else BASELINE_DIR
    report_dir = Path(report_dir) if report_dir is not None else REPORT_DIR

    if not baseline_dir.exists():
        logger.error(f"Baseline directory {baseline_dir} not found. Run with --update-baselines to establish.")
        return EXIT_NOT_COMPARABLE

    baseline_files = list(baseline_dir.glob("*.json"))
    if not baseline_files:
        logger.error(f"No baseline files found in {baseline_dir}.")
        return EXIT_NOT_COMPARABLE

    regressions = []
    improvements = []
    not_comparable = []
    scenarios_checked = 0

    for b_file in sorted(baseline_files):
        scenario = b_file.stem
        r_file = report_dir / b_file.name
        if not r_file.exists():
            not_comparable.append(f"{scenario}: no report at {r_file}")
            continue

        baseline, err = _load(b_file)
        if err:
            not_comparable.append(f"{scenario}: {err}")
            continue
        latest, err = _load(r_file)
        if err:
            not_comparable.append(f"{scenario}: {err}")
            continue

        reason = not_comparable_reason(baseline, latest)
        if reason:
            not_comparable.append(f"{scenario}: {reason}")
            continue

        scenarios_checked += 1

        # 1. Total Compute Regression (Average)
        b_avg = baseline["tick_ms"]["avg"]
        l_avg = latest["tick_ms"]["avg"]

        # Dual Threshold: Allow jitter on small numbers, strict on large numbers
        limit = max(b_avg * RELATIVE_THRESHOLD, b_avg + ABSOLUTE_THRESHOLD_MS)

        if l_avg > limit:
            regressions.append(
                f"TOTAL: {scenario} avg increased from {b_avg:.2f}ms to {l_avg:.2f}ms "
                f"(Limit: {limit:.2f}ms, Delta: {l_avg - b_avg:+.2f}ms)"
            )
        elif l_avg < b_avg * 0.80: # Significant improvement (20%)
            improvements.append(f"TOTAL: {scenario} avg decreased from {b_avg:.2f}ms to {l_avg:.2f}ms")

        # 2. Phase-level Regressions (p95)
        # We track phase-level to catch regressions hidden by total tick improvements
        b_phases = baseline.get("phase_breakdown", {})
        l_phases = latest.get("phase_breakdown", {})

        for phase, b_stats in b_phases.items():
            if phase in l_phases:
                l_stats = l_phases[phase]
                b_p95 = b_stats.get("p95", 0.0)
                l_p95 = l_stats.get("p95", 0.0)

                phase_limit = max(b_p95 * RELATIVE_THRESHOLD, b_p95 + ABSOLUTE_THRESHOLD_MS)
                if l_p95 > phase_limit:
                    regressions.append(
                        f"PHASE: {scenario} {phase} p95 increased from {b_p95:.2f}ms to {l_p95:.2f}ms "
                        f"(Limit: {phase_limit:.2f}ms, Delta: {l_p95 - b_p95:+.2f}ms)"
                    )

        # 3. Memory Regression (Max RSS)
        b_rss = baseline["mem_rss_mb"]["max"]
        l_rss = latest["mem_rss_mb"]["max"]
        if l_rss > b_rss + MEMORY_RSS_LIMIT_MB:
             regressions.append(
                 f"MEMORY: {scenario} max RSS increased from {b_rss:.1f}MB to {l_rss:.1f}MB "
                 f"(Threshold: +{MEMORY_RSS_LIMIT_MB}MB)"
             )

    print("\n" + "="*80)
    print(
        f" PERFORMANCE REGRESSION REPORT ({scenarios_checked} compared, "
        f"{len(not_comparable)} not comparable, {len(regressions)} regressions)"
    )
    print("="*80)

    if regressions:
        logger.error(f"Detected {len(regressions)} performance regressions:")
        for r in regressions:
            print(f"  [FAIL] {r}")

    if improvements:
        logger.info(f"Detected {len(improvements)} performance improvements:")
        for i in improvements:
            print(f"  [PASS] {i}")

    if not_comparable:
        logger.warning(f"{len(not_comparable)} scenario(s) not comparable:")
        for n in not_comparable:
            print(f"  [SKIP] {n}")

    print("-" * 80)
    if regressions:
        logger.error("Performance regression check FAILED.")
        print("="*80 + "\n")
        return EXIT_FAILED

    if not_comparable or scenarios_checked == 0:
        logger.warning("Performance regression check NOT COMPARABLE: not every baseline was compared.")
        print("="*80 + "\n")
        return EXIT_NOT_COMPARABLE

    logger.info("Performance regression check PASSED.")
    print("="*80 + "\n")
    return EXIT_PASSED

if __name__ == "__main__":
    sys.exit(check_regression())
