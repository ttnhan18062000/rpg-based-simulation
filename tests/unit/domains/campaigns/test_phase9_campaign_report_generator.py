import os
from src.domains.campaigns.schema import (
    CampaignResult,
    CampaignScorecard,
    RouteDiversityReport,
    EntityArcReport
)
from src.domains.campaigns.reports import CampaignReportGenerator


def test_report_generator_writes_markdown_and_json():
    scorecard = CampaignScorecard("pass", "pass", "pass", "pass", "pass", "pass", "pass", 10, 0.8, 0.0, 0, "pass")
    diversity = RouteDiversityReport(3, {"cautious_growth": 3}, {}, 0.0, 0.0, False)
    entity_reports = [
        EntityArcReport(1, ("cautious_growth",), (), (), ("e1",))
    ]
    result = CampaignResult(
        campaign_id="first_30_days_adventurers",
        final_state=None,
        entity_arc_reports=tuple(entity_reports),
        world_arc_reports=(),
        forbidden_behaviors=(),
        route_diversity=diversity,
        semantic_scorecard=scorecard,
        performance_summary={"campaign_ticks": 100, "entity_count": 3}
    )
    generator = CampaignReportGenerator()
    out = generator.write_reports(result, "tests/scratch/campaign_reports")
    
    assert os.path.exists(out["markdown"])
    assert os.path.exists(out["json"])
    
    # Read and assert content sections exist
    with open(out["markdown"], "r") as f:
        md = f.read()
        assert "Campaign Semantic Evaluation" in md
        assert "first_30_days_adventurers" in md
        assert "Route Diversity Distribution" in md
