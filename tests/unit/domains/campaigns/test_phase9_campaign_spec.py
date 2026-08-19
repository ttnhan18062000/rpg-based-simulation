import pytest
from src.domains.campaigns.spec import CampaignSpecLoader


def test_campaign_spec_loads_from_yaml():
    yaml_content = """
campaign_id: first_30_days_adventurers
seed: 42
ticks: 3000
world_pack: phase1_adventure_seed
actors:
  count: 30
  start_region: hometown
  start_level: 1
  class_distribution:
    warrior: 10
    ranger: 10
    mage: 10
  trait_distribution:
    brave: 0.25
    cautious: 0.25
    industrious: 0.25
    curious: 0.25
initial_world_pressures:
  - weak_starting_equipment
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
"""
    spec = CampaignSpecLoader.load_from_yaml(yaml_content)
    assert spec.campaign_id == "first_30_days_adventurers"
    assert spec.seed == 42
    assert spec.ticks == 3000
    assert spec.actors.count == 30
    assert spec.actors.start_region == "hometown"
    assert spec.actors.class_distribution["warrior"] == 10
    assert "weak_starting_equipment" in spec.initial_world_pressures
    assert "cautious_growth" in spec.expected_arc_families
    assert "action_after_death" in spec.forbidden_behavior


def test_campaign_spec_requires_expected_arc_families():
    yaml_content = """
campaign_id: first_30_days_adventurers
seed: 42
ticks: 3000
world_pack: phase1_adventure_seed
actors:
  count: 30
  start_region: hometown
  start_level: 1
expected_arc_families: []
forbidden_behavior:
  - action_after_death
"""
    with pytest.raises(ValueError, match="expected_arc_families cannot be empty"):
        CampaignSpecLoader.load_from_yaml(yaml_content)


def test_campaign_spec_requires_forbidden_behavior_rules():
    yaml_content = """
campaign_id: first_30_days_adventurers
seed: 42
ticks: 3000
world_pack: phase1_adventure_seed
actors:
  count: 30
  start_region: hometown
  start_level: 1
expected_arc_families:
  - cautious_growth
forbidden_behavior: []
"""
    with pytest.raises(ValueError, match="forbidden_behavior rules cannot be empty"):
        CampaignSpecLoader.load_from_yaml(yaml_content)


def test_campaign_spec_rejects_exact_action_script_as_required_path():
    yaml_content = """
campaign_id: first_30_days_adventurers
seed: 42
ticks: 3000
world_pack: phase1_adventure_seed
actors:
  count: 30
  start_region: hometown
  start_level: 1
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
exact_action_path:
  - move_north
"""
    with pytest.raises(ValueError, match="Campaign spec cannot define an exact scripted action sequence"):
        CampaignSpecLoader.load_from_yaml(yaml_content)
