from src.domains.campaigns.schema import EntityArcReport
from src.domains.campaigns.diversity import RouteDiversityAnalyzer


def test_route_diversity_counts_multiple_route_families():
    reports = [
        EntityArcReport(1, ("cautious_growth",), (), (), ()),
        EntityArcReport(2, ("craft_growth",), (), (), ()),
        EntityArcReport(3, ("information_growth",), (), (), ()),
    ]
    analyzer = RouteDiversityAnalyzer()
    res = analyzer.analyze(tuple(reports), 3)
    assert res.unique_route_families_used == 3
    assert res.route_family_distribution["cautious_growth"] == 1
    assert res.identical_behavior_collapse is False


def test_identical_behavior_collapse_is_flagged():
    reports = [
        EntityArcReport(1, ("cautious_growth",), (), (), ()),
        EntityArcReport(2, ("cautious_growth",), (), (), ()),
        EntityArcReport(3, ("cautious_growth",), (), (), ()),
    ]
    analyzer = RouteDiversityAnalyzer()
    res = analyzer.analyze(tuple(reports), 3)
    assert res.identical_behavior_collapse is True


def test_stagnant_entity_ratio_is_reported():
    reports = [
        EntityArcReport(1, ("stagnant",), (), (), ()),
        EntityArcReport(2, ("cautious_growth",), (), (), ()),
    ]
    analyzer = RouteDiversityAnalyzer()
    res = analyzer.analyze(tuple(reports), 2)
    assert res.stagnant_entity_ratio == 0.5
