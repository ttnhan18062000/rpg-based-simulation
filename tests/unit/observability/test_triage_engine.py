import pytest
from src.observability.anomaly.rules_engine import AnomalyRecord
from src.observability.anomaly.triage import TriageEngine, AnomalyCluster, InvestigationHint

def test_triage_clustering_logic():
    anomalies = [
        AnomalyRecord(
            rule_id="NavigationStuckBasic",
            severity="WARNING",
            domain="movement",
            message="Entity 1 stuck",
            tick_start=10,
            tick_end=20,
            affected_entity_ids=[1],
            affected_region_ids=["region_a"],
            suggested_causes=["Tile block"]
        ),
        AnomalyRecord(
            rule_id="NavigationStuckBasic",
            severity="WARNING",
            domain="movement",
            message="Entity 2 stuck",
            tick_start=15,
            tick_end=25,
            affected_entity_ids=[2],
            affected_region_ids=["region_a"],
            suggested_causes=["Crowding"]
        ),
        # Different region -> should not merge
        AnomalyRecord(
            rule_id="NavigationStuckBasic",
            severity="WARNING",
            domain="movement",
            message="Entity 3 stuck",
            tick_start=15,
            tick_end=25,
            affected_entity_ids=[3],
            affected_region_ids=["region_b"],
            suggested_causes=["Tile block"]
        ),
        # Different severity -> should not merge
        AnomalyRecord(
            rule_id="NavigationStuckBasic",
            severity="ERROR",
            domain="movement",
            message="Entity 4 stuck critically",
            tick_start=15,
            tick_end=25,
            affected_entity_ids=[4],
            affected_region_ids=["region_a"],
            suggested_causes=["Tile block"]
        ),
        # Non-overlapping tick -> should not merge
        AnomalyRecord(
            rule_id="NavigationStuckBasic",
            severity="WARNING",
            domain="movement",
            message="Entity 5 stuck later",
            tick_start=100,
            tick_end=110,
            affected_entity_ids=[5],
            affected_region_ids=["region_a"],
            suggested_causes=["Tile block"]
        ),
    ]

    clusters = TriageEngine.cluster_anomalies(anomalies)

    # We expect:
    # 1. Cluster with ERROR, NavigationStuckBasic, region_a (Entity 4) (highest severity first)
    # 2. Cluster with WARNING, NavigationStuckBasic, region_a, ticks 10-25 (Entities 1 and 2 merged)
    # 3. Cluster with WARNING, NavigationStuckBasic, region_b, ticks 15-25 (Entity 3)
    # 4. Cluster with WARNING, NavigationStuckBasic, region_a, ticks 100-110 (Entity 5)
    
    assert len(clusters) == 4
    
    # 1st cluster should be the ERROR one (severity sorting)
    assert clusters[0].severity == "ERROR"
    assert clusters[0].affected_entity_ids == [4]
    
    # Check the merged cluster
    merged_cluster = next(c for c in clusters if c.severity == "WARNING" and len(c.affected_entity_ids) == 2)
    assert merged_cluster.region_id == "region_a"
    assert merged_cluster.tick_start == 10
    assert merged_cluster.tick_end == 25
    assert set(merged_cluster.affected_entity_ids) == {1, 2}
    assert "Tile block" in merged_cluster.suggested_causes
    assert "Crowding" in merged_cluster.suggested_causes
    assert len(merged_cluster.anomalies) == 2

def test_investigation_hints():
    hints = InvestigationHint.get_hints("NavigationStuckBasic")
    assert len(hints) > 0
    assert any("pathfinding" in h.lower() for h in hints)

    fallback_hints = InvestigationHint.get_hints("UnknownRuleName")
    assert len(fallback_hints) == 1
    assert "Analyze corresponding" in fallback_hints[0]
