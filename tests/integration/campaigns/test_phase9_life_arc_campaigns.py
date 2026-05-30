from src.domains.campaigns.schema import CampaignEvent
from src.domains.campaigns.spec import CampaignSpecLoader
from src.domains.campaigns.runner import CampaignRunner


def test_scenario_life_arc_campaigns():
    yaml_content = """
campaign_id: full_simulation_scenario_campaign
seed: 777
ticks: 20
world_pack: phase1_adventure_seed
actors:
  count: 4
  start_region: hometown
  start_level: 1
  class_distribution:
    warrior: 2
    ranger: 2
  trait_distribution:
    brave: 0.5
    cautious: 0.5
initial_world_pressures:
  - dangerous_wilds
expected_arc_families:
  - cautious_growth
  - craft_growth
forbidden_behavior:
  - action_after_death
"""
    spec = CampaignSpecLoader.load_from_yaml(yaml_content)

    # Let's inject semantic events that reflect:
    # Actor 1: craft_growth
    # Actor 2: cautious_growth with an avoidance behavior proof (combat loss -> avoid danger)
    # Actor 3: failed_adventurer (combat loss -> died)
    # Actor 4: stagnant (scout only)
    injected_events = [
        # Actor 1: craft growth
        CampaignEvent("e1_1", 2, 1, "progression", "recipe_learned", {"recipe": "wooden_shield"}),
        CampaignEvent("e1_2", 8, 1, "progression", "item_crafted", {"item": "wooden_shield"}),

        # Actor 2: cautious growth + avoidance learning
        CampaignEvent("e2_1", 3, 2, "combat", "combat_loss", {"target": "shadow_beast"}),
        CampaignEvent("e2_2", 12, 2, "movement", "avoided_danger", {"reason": "avoid_shadow_beast"}),
        CampaignEvent("e2_3", 14, 2, "quest", "quest_completed", {"quest_type": "inn_visit", "difficulty": "easy"}),
        CampaignEvent("e2_4", 15, 2, "movement", "scout_location", {}),
        CampaignEvent("e2_5", 16, 2, "movement", "scout_location", {}),

        # Actor 3: failed adventurer
        CampaignEvent("e3_1", 4, 3, "combat", "combat_loss", {}),
        CampaignEvent("e3_2", 15, 3, "lifecycle", "died", {}),

        # Actor 4: stagnant
        CampaignEvent("e4_1", 5, 4, "movement", "scout_location", {}),
    ]

    runner = CampaignRunner()
    result = runner.run(spec, injected_events=injected_events)

    # Assert correct entities classified
    entity_arcs = {r.entity_id: r.arc_types for r in result.entity_arc_reports}
    assert "craft_growth" in entity_arcs[1]
    assert "cautious_growth" in entity_arcs[2]
    assert "failed_adventurer" in entity_arcs[3]
    assert "stagnant" in entity_arcs[4]

    # Route diversity assertions
    assert result.route_diversity.unique_route_families_used >= 3
    assert result.route_diversity.identical_behavior_collapse is False

    # Scorecard assertions
    assert result.semantic_scorecard.verdict in ("pass", "fail")
    assert result.semantic_scorecard.behavior_change_proofs >= 1


def test_scenario_detects_forbidden_behaviors():
    yaml_content = """
campaign_id: forbidden_behavior_detection_campaign
seed: 123
ticks: 10
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

    # Actor 1 performs action after death!
    injected_events = [
        CampaignEvent("e1", 2, 1, "lifecycle", "died", {}),
        CampaignEvent("e2", 5, 1, "movement", "scout_location", {}),
    ]

    runner = CampaignRunner()
    result = runner.run(spec, injected_events=injected_events)

    # Assert forbidden behavior detected
    assert len(result.forbidden_behaviors) == 1
    assert result.forbidden_behaviors[0].rule_violated == "action_after_death"
    assert result.forbidden_behaviors[0].entity_id == 1

    # Scorecard should fail because of forbidden behavior
    assert result.semantic_scorecard.verdict == "fail"
    assert result.semantic_scorecard.forbidden_behavior_count == 1
