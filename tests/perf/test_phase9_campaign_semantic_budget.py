import time
from src.domains.campaigns.spec import CampaignSpecLoader
from src.domains.campaigns.runner import SimulationAnalysisRunner
from src.domains.campaigns.schema import CampaignEvent
from tests.tools.perf_assertions import assert_perf_threshold


def test_campaign_semantic_budget_overhead():
    # Setup a scenario spec
    yaml_content = """
campaign_id: budget_perf_test_campaign
seed: 888
ticks: 10
world_pack: phase1_adventure_seed
actors:
  count: 5
  start_region: hometown
  start_level: 1
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
"""
    spec = CampaignSpecLoader.load_from_yaml(yaml_content)

    # Let's generate a substantial amount of events to test real workload
    injected_events = []
    for t in range(1, 11):
        for eid in range(1, 6):
            injected_events.append(CampaignEvent(
                event_id=f"evt_{t}_{eid}",
                tick=t,
                entity_id=eid,
                category="combat",
                event_type="combat_loss",
                details={"target": "beast"}
            ))

    runner = SimulationAnalysisRunner()
    
    t0 = time.perf_counter_ns()
    result = runner.run(spec, injected_events=injected_events)
    t1 = time.perf_counter_ns()
    
    # Semantic evaluation overhead is the classification and scorecard generation time
    overhead_ms = result.performance_summary["arc_classification_ms"] + result.performance_summary["scorecard_generation_ms"]
    avg_overhead_per_tick = overhead_ms / spec.ticks
    
    print(f"Total Campaign Overhead Time: {overhead_ms:.4f} ms")
    print(f"Average Overhead per Tick: {avg_overhead_per_tick:.4f} ms")
    
    # Assert average overhead per tick is strictly bounded under 5ms
    assert_perf_threshold(
        avg_overhead_per_tick, 5.0,
        "Average campaign semantic overhead per tick", op="<",
    )

