import json
import os
import sys
from typing import Tuple, Dict, Any

class BehaviorObservabilityRolloutGate:
    """Validates the behavior observability rollout report against stability, safety, determinism and budget metrics."""
    def __init__(self, report_path: str, max_overhead_percent: float = 3.0) -> None:
        self.report_path = report_path
        self.max_overhead_percent = max_overhead_percent

    def validate(self) -> Tuple[bool, str]:
        if not os.path.exists(self.report_path):
            return False, f"Missing behavior rollout report: {self.report_path}"

        try:
            with open(self.report_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            return False, f"Failed to parse behavior report: {str(e)}"

        if data.get("overhead_percent", 0.0) > self.max_overhead_percent:
            return False, f"Observability overhead too high: ({data.get('overhead_percent')}%) exceeds budget ({self.max_overhead_percent}%)"

        if not data.get("deterministic", False):
            return False, "Simulation determinism mismatch between observability ON and OFF"

        if not data.get("runtime_profiling_works", False):
            return False, "Runtime profiling failed when behavior features are OFF"

        if not data.get("queue_nonblocking", False):
            return False, "Queue full blocks the simulation tick"

        if not data.get("worker_isolated", False):
            return False, "Worker failure is not isolated from simulation engine"

        if not data.get("postrun_deferred", False):
            return False, "Post-run analysis cannot be deferred"

        if not data.get("behavior_artifacts_optional", False):
            return False, "Behavior artifacts are not treated as optional"

        if data.get("critical_events_dropped", False):
            return False, "Critical events were dropped under pressure"

        return True, "Behavior observability rollout is safe for production based on current profile budget run data metrics."

if __name__ == "__main__":
    path = "reports/behavior_observability_rollout_report.json" if len(sys.argv) < 2 else sys.argv[1]
    gate = BehaviorObservabilityRolloutGate(path)
    res, reason = gate.validate()
    print(f"Gate Verification Result: {res}")
    print(f"Reasoning: {reason}")
    sys.exit(0 if res else 1)
