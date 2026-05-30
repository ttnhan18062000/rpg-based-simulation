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

        # Setup state if not provided
        if state is None:
            # Construct a basic authoritative state to feed the tick loop
            from src.core.state import AuthoritativeState
            from src.core.builder import V2EntityBuilder
            from src.core.registries import ResourceRegistry
            from src.core.state import ResourceNodeState
            
            # Spawn the first actor from spec
            actor_spec = self.spec.get("actors", [{}])[0]
            actor_id = actor_spec.get("id", 1)
            
            hero = (V2EntityBuilder(actor_id)
                    .kind(actor_spec.get("role", "HERO"))
                    .location(0.0, 0.0)
                    .identity(class_id=actor_spec.get("class_id", "warrior"))
                    .inventory(gold=actor_spec.get("gold", 60))
                    .build())
            
            # Register self-model aspects
            from src.core.self_model import SelfModelBundle, SelfAwarenessComponent, NeedInterpretationComponent
            perceived_w = tuple(self.spec.get("initial_pressure", ["weak_weapon"]))
            sm = SelfModelBundle(
                self_awareness=SelfAwarenessComponent(perceived_weaknesses=perceived_w),
                needs=NeedInterpretationComponent(active_needs={})
            )
            from dataclasses import replace as dataclass_replace
            hero = dataclass_replace(hero, self_model=sm)

            # Generate a standard resource node for opportunities
            node = ResourceNodeState(
                id=101, kind="node_wood", position=(1.0, 1.0), yields_item="wood_log",
                remaining_charges=5, max_charges=5, required_ticks=10
            )

            state = AuthoritativeState(
                tick=0,
                seed=42,
                entities={hero.id: hero},
                resource_nodes={node.id: node}
            )

        from src.engine.pipeline import AuthoritativeApplyPipeline
        from src.engine.apply import ApplyPath

        current_state = state
        provider_calls = 0

        # Simulate deterministic tick execution
        for tick in range(1, ticks + 1):
            # Gather opportunities for routing decisions
            from src.world.providers.resources import ResourceOpportunityProvider
            hero_ent = current_state.entities.get(1) or list(current_state.entities.values())[0]
            opps = ResourceOpportunityProvider.get_opportunities(hero_ent, current_state)
            provider_calls += 1

            # Inject active variables into state
            from dataclasses import replace as dataclass_replace
            current_state = dataclass_replace(
                current_state,
                pressure_signals={
                    "ENABLE_WORLD_CAPABILITY_LAYER": 1.0,
                    "ENABLE_SELF_MODEL_COGNITION": 1.0,
                    "ENABLE_ADVENTURE_ROUTING": 1.0,
                    "ENABLE_BELIEF_ASSIMILATION": 1.0,
                }
            )

            # Run apply pipeline refine
            from src.core.updates import StateUpdate
            update = StateUpdate()
            refined_update = AuthoritativeApplyPipeline.refine(current_state, update)
            
            # Apply update to state
            next_state = ApplyPath.apply_generation(current_state, refined_update, next_tick=tick)
            
            # Retrieve routing results
            hero_post = next_state.entities.get(hero_ent.id)
            last_family = "defer_with_reason"
            if hero_post and hero_post.identity.properties:
                last_family = hero_post.identity.properties.get("last_routing_family", "defer_with_reason")

            trace_evt = {
                "tick": tick,
                "selected_route_family": last_family,
                "reason": "executed_via_authoritative_loop",
                "entity_id": hero_ent.id
            }
            route_traces.append(trace_evt)
            detected_route_families.add(last_family)
            
            # Detect forbidden behaviors
            for forbidden in self.spec.get("forbidden_behavior", []):
                # Simple detectors
                if forbidden == "buy_without_gold" and last_family == "buy_upgrade" and hero_post.inventory.gold < 0:
                    forbidden_triggered.append(forbidden)

            current_state = next_state

        duration = time.perf_counter() - start_time
        
        # Compile scorecards
        valid_families = set(self.spec.get("valid_route_families", []))
        passed = False
        
        # Verify scorecard status based on detected routes vs spec valid routes
        matched = detected_route_families & valid_families
        if len(matched) == len(detected_route_families):
            status = "PASS"
        elif matched:
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
                "provider_calls": provider_calls,
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
