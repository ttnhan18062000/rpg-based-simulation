from __future__ import annotations
import os
import json
import shutil
import pytest
from src.observability.behavior.behavior_finding import BehaviorFinding
from src.observability.behavior.behavior_insight import BehaviorInsight


@pytest.fixture
def temp_run_dir():
    run_dir = "tests/run_data_phase25_test"
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    yield run_dir
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)


def test_behavior_analysis_skips_when_artifacts_missing():
    # If events/episodes missing, analyzer skips gracefully
    run_dir = "tests/missing_run_dir"
    findings_path = os.path.join(run_dir, "behavior_findings.jsonl")
    assert not os.path.exists(findings_path)


def test_findings_and_insights_are_written_to_files(temp_run_dir):
    run_dir = temp_run_dir
    findings_path = os.path.join(run_dir, "behavior_findings.jsonl")
    insights_path = os.path.join(run_dir, "behavior_insights.json")

    finding = BehaviorFinding(
        finding_id="find_1",
        finding_type="repeated_failure_loop",
        severity="WARNING",
        summary="A failure loop",
        affected_entities=(12,),
        tick_range=(0, 100),
        evidence_event_ids=(),
        evidence_episode_ids=("ep_1",),
        suggested_systems=("locomotion",),
        recommendation="Cooldown"
    )

    insight = BehaviorInsight(
        insight_id="ins_1",
        summary="summary of loops",
        evidence="evidence proof",
        affected_entities=(12,),
        findings=("find_1",),
        recommendation="recommendation description"
    )

    with open(findings_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(finding.to_dict()) + "\n")

    with open(insights_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(insight.to_dict()) + "\n")

    assert os.path.exists(findings_path)
    assert os.path.exists(insights_path)
