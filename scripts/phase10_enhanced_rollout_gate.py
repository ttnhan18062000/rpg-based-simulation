import json
import os
from typing import Tuple, Dict, Any

class RolloutGate:
    """Validates the simulation rollout reports against performance, safety and determinism metrics."""
    def __init__(self, report_path: str, budget_ms: float = 25.0) -> None:
        self.report_path = report_path
        self.budget_ms = budget_ms

    def validate(self) -> Tuple[bool, str]:
        if not os.path.exists(self.report_path):
            return False, f"Missing report: {self.report_path}"

        try:
            with open(self.report_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            return False, f"Failed to parse report: {str(e)}"

        if data.get("avg_tick_ms", 0.0) > self.budget_ms:
            return False, f"Performance regression: average tick time ({data.get('avg_tick_ms')} ms) exceeds budget ({self.budget_ms} ms)"

        if not data.get("deterministic", False):
            return False, "Determinism failure detected in the run"

        if data.get("forbidden_behaviors"):
            return False, f"Forbidden behavior count > 0: {data.get('forbidden_behaviors')}"

        if data.get("hard_law_violations"):
            return False, f"Hard law violations count > 0: {data.get('hard_law_violations')}"

        if data.get("dropped_critical_traces", 0) > 0:
            return False, "Dropped critical traces detected"

        if not data.get("memory_caps_respected", False):
            return False, "Memory capacity caps were not respected"

        # Bounded probabilistic language to avoid absolute certainty claims
        return True, "Rollout is safe for production based on current profile budget run data metrics."

if __name__ == "__main__":
    import sys
    path = "reports/phase10_rollout_report.json" if len(sys.argv) < 2 else sys.argv[1]
    gate = RolloutGate(path)
    res, reason = gate.validate()
    print(f"Gate Verification Result: {res}")
    print(f"Reasoning: {reason}")
    sys.exit(0 if res else 1)
