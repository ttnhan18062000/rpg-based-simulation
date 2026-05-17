# Compliance IDs: PERF-013
import json
import sys
import logging
from pathlib import Path

# Milestone 6: Performance Regression Gate
# Logic ID: RPG-PERF-013 (Regression Detection)
# Policy: max(baseline * 1.15, baseline + 3.0ms)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Thresholds
RELATIVE_THRESHOLD = 1.15  # 15% regression allowed
ABSOLUTE_THRESHOLD_MS = 3.0 # 3ms absolute regression allowed
MEMORY_RSS_LIMIT_MB = 20.0  # 20MB absolute RSS growth allowed

def check_regression():
    """
    Compare current performance reports against committed baselines.
    Returns True if stable, False if regressions detected.
    """
    baseline_dir = Path("tests/perf/baselines")
    report_dir = Path("reports/perf")
    
    if not baseline_dir.exists():
        logger.error(f"Baseline directory {baseline_dir} not found. Run with --update-baselines to establish.")
        return False

    baseline_files = list(baseline_dir.glob("*.json"))
    if not baseline_files:
        logger.error(f"No baseline files found in {baseline_dir}.")
        return False

    regressions = []
    improvements = []
    scenarios_checked = 0
    
    for b_file in sorted(baseline_files):
        r_file = report_dir / b_file.name
        if not r_file.exists():
            # In CI, we expect all smoke baselines to have a corresponding report
            logger.warning(f"Report for {b_file.name} not found. Skipping scenario {b_file.stem}.")
            continue
            
        scenarios_checked += 1
        with open(b_file) as f:
            baseline = json.load(f)
        with open(r_file) as f:
            latest = json.load(f)
            
        scenario = b_file.stem
        
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
    print(f" PERFORMANCE REGRESSION REPORT ({scenarios_checked} scenarios checked)")
    print("="*80)

    if regressions:
        logger.error(f"Detected {len(regressions)} performance regressions:")
        for r in regressions:
            print(f"  [FAIL] {r}")
    
    if improvements:
        logger.info(f"Detected {len(improvements)} performance improvements:")
        for i in improvements:
            print(f"  [PASS] {i}")

    if not regressions:
        print("-" * 80)
        logger.info("Performance regression check PASSED.")
        print("="*80 + "\n")
        return True
    
    print("-" * 80)
    logger.error("Performance regression check FAILED.")
    print("="*80 + "\n")
    return False

if __name__ == "__main__":
    if not check_regression():
        sys.exit(1)
    sys.exit(0)
