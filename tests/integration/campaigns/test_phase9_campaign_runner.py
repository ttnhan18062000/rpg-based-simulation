from src.domains.campaigns.spec import CampaignSpecLoader
from src.domains.campaigns.runner import CampaignRunner


def test_campaign_runner_executes_small_campaign():
    yaml_content = """
campaign_id: small_test_campaign
seed: 42
ticks: 5
world_pack: phase1_adventure_seed
actors:
  count: 3
  start_region: hometown
  start_level: 1
  class_distribution:
    warrior: 2
    mage: 1
  trait_distribution:
    brave: 1.0
initial_world_pressures:
  - weak_starting_equipment
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
"""
    spec = CampaignSpecLoader.load_from_yaml(yaml_content)
    runner = CampaignRunner()
    result = runner.run(spec)
    
    assert result.campaign_id == "small_test_campaign"
    assert result.final_state is not None
    assert result.final_state.tick == 5
    assert len(result.entity_arc_reports) == 3
    assert result.performance_summary["campaign_ticks"] == 5


def test_campaign_runner_outputs_entity_and_world_arc_reports():
    yaml_content = """
campaign_id: reports_campaign
seed: 42
ticks: 2
world_pack: phase1_adventure_seed
actors:
  count: 2
  start_region: hometown
  start_level: 1
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
"""
    spec = CampaignSpecLoader.load_from_yaml(yaml_content)
    runner = CampaignRunner()
    result = runner.run(spec)
    
    assert len(result.entity_arc_reports) == 2
    assert len(result.world_arc_reports) == 0


def test_campaign_runner_is_deterministic_for_same_seed():
    yaml_content = """
campaign_id: determinism_campaign
seed: 99
ticks: 3
world_pack: phase1_adventure_seed
actors:
  count: 2
  start_region: hometown
  start_level: 1
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
"""
    spec = CampaignSpecLoader.load_from_yaml(yaml_content)
    runner = CampaignRunner()
    res1 = runner.run(spec)
    res2 = runner.run(spec)
    
    assert res1.final_state.fingerprint()["state_hash"] == res2.final_state.fingerprint()["state_hash"]
