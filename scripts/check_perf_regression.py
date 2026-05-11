import json
import os
import sys

BASELINE_PATH = "reports/perf/baseline.json"
LATEST_PATH = "reports/perf/latest.json"
THRESHOLD = 0.15  # 15% tolerance

def check_regression():
    if not os.path.exists(BASELINE_PATH):
        print(f"⚠️ No baseline found at {BASELINE_PATH}. Skipping regression check.")
        return

    if not os.path.exists(LATEST_PATH):
        print(f"❌ Latest report not found at {LATEST_PATH}")
        sys.exit(1)

    with open(BASELINE_PATH, 'r') as f:
        baseline = json.load(f)
    
    with open(LATEST_PATH, 'r') as f:
        latest = json.load(f)

    print(f"📊 Comparing {latest['scenario']} against baseline...")
    
    # Check throughput (higher is better)
    b_tput = baseline["throughput_ips"]
    l_tput = latest["throughput_ips"]
    tput_diff = (l_tput - b_tput) / b_tput
    
    # Check duration (lower is better)
    b_dur = baseline["duration_ms"]
    l_dur = latest["duration_ms"]
    dur_diff = (l_dur - b_dur) / b_dur

    print(f"Throughput: {b_tput:.2f} -> {l_tput:.2f} ({tput_diff:+.2%})")
    print(f"Duration:   {b_dur:.2f}ms -> {l_dur:.2f}ms ({dur_diff:+.2%})")

    failed = False
    if tput_diff < -THRESHOLD:
        print(f"❌ REGRESSION: Throughput dropped by {abs(tput_diff):.2%}, exceeding {THRESHOLD:.2%} threshold.")
        failed = True
    
    if dur_diff > THRESHOLD:
        print(f"❌ REGRESSION: Duration increased by {dur_diff:.2%}, exceeding {THRESHOLD:.2%} threshold.")
        failed = True

    if failed:
        sys.exit(1)
    else:
        print("✅ No significant performance regressions detected.")

if __name__ == "__main__":
    check_regression()
