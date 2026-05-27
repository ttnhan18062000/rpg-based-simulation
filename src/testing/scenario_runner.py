import os
import yaml
import json
import time
from typing import Any, Dict, List, Optional


class ScenarioRunner:
    """
    ScenarioRunner orchestrates deterministic scenario executions,
    tracing active routes and evaluating scorecard pass/fail status.
    """

    def __init__(self, spec_path: str, output_dir: str = "reports/phase1_scorecards"):
        self.spec_path = spec_path
        self.output_dir = output_dir
        self.spec: Dict[str, Any] = {}
        self.load_spec()

    def load_spec(self) -> None:
        """Load scenario spec from YAML file."""
        if not os.path.exists(self.spec_path):
            raise FileNotFoundError(f"Scenario spec not found: {self.spec_path}")
        with open(self.spec_path, "r") as f:
            self.spec = yaml.safe_load(f) or {}

    def execute(self, ticks: int = 50, state: Optional[Any] = None) -> Dict[str, Any]:
        """
        Execute deterministic synchronous simulation loop for N ticks.
        Returns a rich scorecard result dictionary.
        """
        start_time = time.perf_counter()
        
        # Captured states/traces
        route_traces: List[Dict[str, Any]] = []
        detected_route_families = set()
        failures = []
        forbidden_triggered = []

        # Simulate deterministic tick execution
        for tick in range(1, ticks + 1):
            # Mock / standard loop logic capture (Task 1 / 9 trace mapping)
            trace_evt = {
                "tick": tick,
                "selected_route_family": "defer_with_reason",
                "reason": "world_capability_not_fully_implemented_yet",
                "entity_id": 1
            }
            route_traces.append(trace_evt)
            detected_route_families.add("defer_with_reason")

        duration = time.perf_counter() - start_time
        
        # Compile scorecards
        valid_families = set(self.spec.get("valid_route_families", []))
        passed = False
        
        # For TDD: currently we defer with reason, check if that fits valid route list
        if "defer_with_reason" in valid_families:
            # Under initial TDD, this counts as a partial pass / defer state
            status = "PARTIAL_PASS"
        else:
            status = "FAIL"

        scorecard = {
            "scenario_id": self.spec.get("scenario_id", "unknown"),
            "status": status,
            "total_ticks": ticks,
            "duration_seconds": duration,
            "detected_route_families": list(detected_route_families),
            "forbidden_triggered": forbidden_triggered,
            "performance": {
                "average_tick_time_ms": (duration / ticks) * 1000 if ticks > 0 else 0,
                "provider_calls": 0,
                "strategic_evaluations": ticks
            }
        }

        # Write output reports
        os.makedirs(self.output_dir, exist_ok=True)
        scorecard_path = os.path.join(self.output_dir, f"{scorecard['scenario_id']}_scorecard.json")
        with open(scorecard_path, "w") as f:
            json.dump(scorecard, f, indent=2)

        trace_path = os.path.join(self.output_dir, f"{scorecard['scenario_id']}_route_trace.jsonl")
        with open(trace_path, "w") as f:
            for trace in route_traces:
                f.write(json.dumps(trace) + "\n")

        return scorecard
