# Compliance IDs: OBS-PH9-M49, OBS-PH9-M50, OBS-PH9-M51, OBS-PH9-M52, OBS-PH9-M53, OBS-PH9-M54, OBS-PH9-M55, OBS-PH9-M56, OBS-PH9-M57
from __future__ import annotations

import os
import json
import shutil
import tempfile
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.observability.mining.controller import (
    MiningExperimentConfig,
    MiningRunMatrixBuilder,
    MiningExperimentController,
    MiningExperimentManifest
)
from src.observability.mining.dataset import (
    RunFeatureExtractor,
    MiningDatasetBuilder,
    DatasetQueryService
)
from src.observability.mining.auditor import (
    DataCompletenessAuditor,
    DeterminismAuditor
)
from src.observability.mining.patterns import PatternMiningEngine
from src.observability.mining.priority import PriorityScorer, EngineeringBacklogGenerator
from src.observability.mining.evidence import EvidencePackBuilder
from src.observability.mining.orchestrator import AIAgentInvestigationRunner, AgentOutputValidator
from src.observability.mining.recommender import NextExperimentRecommender
from src.observability.mining.workflow import MiningReviewWorkflow, MiningQualityGate


@pytest.fixture
def temp_experiment_workspace():
    """Sets up a temporary directory mocking an completed simulation mining experiment."""
    temp_dir = tempfile.mkdtemp()
    
    # 1. Create subfolders
    runs_dir = os.path.join(temp_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    
    # Create 3 run directories (run_1: completed, run_2: completed same seed repeat, run_3: failed or different seed)
    run_ids = ["run_exp_1_seed_42_rep_0", "run_exp_1_seed_42_rep_1", "run_exp_1_seed_99"]
    seeds = [42, 42, 99]
    reps = [0, 1, 0]
    
    for r_id, seed, rep in zip(run_ids, seeds, reps):
        r_dir = os.path.join(runs_dir, r_id)
        os.makedirs(r_dir, exist_ok=True)
        
        # Write run_manifest.json
        state_hash = "hash_42_a" if r_id == "run_exp_1_seed_42_rep_0" else ("hash_42_b" if r_id == "run_exp_1_seed_42_rep_1" else "hash_99")
        status = "COMPLETED"
        manifest_data = {
            "run_id": r_id,
            "seed": seed,
            "status": status,
            "ticks_completed": 100,
            "final_state_hash": state_hash,
            "schema_version": "run_manifest_v1"
        }
        with open(os.path.join(r_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            
        # Write run_report.json
        report_data = {
            "run_id": r_id,
            "health_score": 95.0 if seed == 42 else 55.0,
            "critical_count": 0 if seed == 42 else 2,
            "warning_count": 1 if seed == 42 else 5,
            "hard_law_violation_count": 0 if seed == 42 else 1,
            "anomaly_count": 1 if seed == 42 else 7,
            "dropped_event_count": 0
        }
        with open(os.path.join(r_dir, "run_report.json"), "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
            
        # Write anomalies.json
        anomalies_data = [
            {
                "rule_id": "STUCK_NAVIGATION" if seed == 42 else "QUEST_STALLED",
                "severity": "warning" if seed == 42 else "critical",
                "domain": "movement" if seed == 42 else "quest",
                "tick": 50 if seed == 42 else 30,
                "message": f"Entity stuck at node 123" if seed == 42 else "Quest stalled at blacksmith step"
            }
        ]
        with open(os.path.join(r_dir, "anomalies.json"), "w", encoding="utf-8") as f:
            json.dump(anomalies_data, f, indent=2)
            
        # Write simulation_events.jsonl (with divergence at tick 50)
        with open(os.path.join(r_dir, "simulation_events.jsonl"), "w", encoding="utf-8") as f:
            # Event 1 (identical)
            f.write(json.dumps({"tick": 10, "event_type": "TICK_START", "payload": {}}) + "\n")
            # Event 2 (divergent for seed 42 repeat runs)
            p_val = "val_a" if r_id == "run_exp_1_seed_42_rep_0" else ("val_b" if r_id == "run_exp_1_seed_42_rep_1" else "val_c")
            f.write(json.dumps({"tick": 50, "event_type": "MOVEMENT", "payload": {"coord": p_val}}) + "\n")
            
        # Write metric_windows.jsonl
        with open(os.path.join(r_dir, "metric_windows.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"tick": 50, "tick_compute_ms": 1.5, "memory_rss": 2048}) + "\n")
            
    # 2. Write experiment_manifest.json
    manifest_data = {
        "experiment_id": "exp_test_1",
        "experiment_type": "same_seed_repeat",
        "scenario_name": "RESOURCE_ECONOMY_10",
        "seed_count": 2,
        "repeat_count": 2,
        "run_count": 3,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETED",
        "run_ids": run_ids
    }
    with open(os.path.join(temp_dir, "experiment_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
        
    # 3. Write run_matrix.jsonl
    with open(os.path.join(temp_dir, "run_matrix.jsonl"), "w", encoding="utf-8") as f:
        for r_id, seed, rep in zip(run_ids, seeds, reps):
            spec = {
                "run_id": r_id,
                "scenario": "RESOURCE_ECONOMY_10",
                "seed": seed,
                "repeat_index": rep,
                "engine_version": "v2",
                "balance_profile": "cli_default",
                "observability_profile": "production",
                "ticks": 100
            }
            f.write(json.dumps(spec) + "\n")
            
    yield temp_dir
    
    shutil.rmtree(temp_dir)


def test_mining_config_validation():
    """Verify config validation limits and field validation logic."""
    config = MiningExperimentConfig(
        experiment_id="exp_test_val",
        experiment_type="same_seed_repeat",
        scenario_name="RESOURCE_ECONOMY_10",
        scenario_type="test",
        seeds=[42],
        ticks=100
    )
    assert config.experiment_id == "exp_test_val"
    assert config.ticks == 100
    
    with pytest.raises(ValueError, match="seeds list cannot be empty"):
        MiningExperimentConfig(
            experiment_type="same_seed_repeat",
            scenario_name="RESOURCE_ECONOMY_10",
            scenario_type="test",
            seeds=[],
            ticks=100
        )
        
    with pytest.raises(ValueError, match="ticks must be positive"):
        MiningExperimentConfig(
            experiment_type="same_seed_repeat",
            scenario_name="RESOURCE_ECONOMY_10",
            scenario_type="test",
            seeds=[42],
            ticks=-5
        )


def test_matrix_builder_generates_matrix():
    """Verify MiningRunMatrixBuilder correctly segregates sweeps and repeat parameters."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = MiningExperimentConfig(
            experiment_id="exp_matrix_test",
            experiment_type="same_seed_repeat",
            scenario_name="RESOURCE_ECONOMY_10",
            scenario_type="test",
            seeds=[42],
            repeat_count=3,
            ticks=100
        )
        specs = MiningRunMatrixBuilder.build_matrix(config, tmp_dir)
        
        assert len(specs) == 3
        assert specs[0].run_id == "run_exp_matrix_test_seed_42_rep_0"
        assert specs[1].run_id == "run_exp_matrix_test_seed_42_rep_1"
        assert specs[2].run_id == "run_exp_matrix_test_seed_42_rep_2"
        assert os.path.exists(os.path.join(tmp_dir, "run_matrix.jsonl"))


def test_dataset_builder_compiles_data(temp_experiment_workspace):
    """Verify MiningDatasetBuilder constructs unified relational tables."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    manifest_data = MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    
    dataset_dir = os.path.join(exp_dir, "dataset")
    assert os.path.exists(os.path.join(dataset_dir, "dataset_manifest.json"))
    assert os.path.exists(os.path.join(dataset_dir, "runs.json"))
    assert os.path.exists(os.path.join(dataset_dir, "run_features.json"))
    assert os.path.exists(os.path.join(dataset_dir, "anomalies.json"))
    assert os.path.exists(os.path.join(dataset_dir, "hard_law_violations.json"))
    
    assert manifest_data["record_counts"]["runs"] == 3
    assert manifest_data["record_counts"]["anomalies"] == 3


def test_query_service_executes_queries(temp_experiment_workspace):
    """Verify relational querying performs filtering and ordering across JSON tables."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    
    dataset_dir = os.path.join(exp_dir, "dataset")
    query_service = DatasetQueryService(dataset_dir)
    
    # Test fallback or standard query
    sql = "SELECT run_id, seed, health_score FROM run_features ORDER BY health_score ASC"
    res = query_service.query(sql)
    
    assert len(res) > 0
    # Worst run should be first (seed 99 has health score 55.0)
    assert res[0]["seed"] == 99


def test_data_completeness_auditor(temp_experiment_workspace):
    """Verify DataCompletenessAuditor classifies run health and telemetry coverage."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    report = DataCompletenessAuditor.audit_completeness(exp_id, base_dir=parent_dir)
    
    assert report["total_runs"] == 3
    assert report["valid_run_count"] == 3
    assert report["quality_score"] == 100.0
    assert report["runs_classification"]["run_exp_1_seed_42_rep_0"] == "VALID_FOR_MINING"


def test_determinism_auditor_finds_divergence(temp_experiment_workspace):
    """Verify DeterminismAuditor identifies state divergence and highlights exact coordinates."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    report = DeterminismAuditor.audit_determinism(exp_id, base_dir=parent_dir)
    
    assert report["verdict"] == "CONFIRMED_NONDETERMINISM"
    assert len(report["determinism_failures"]) == 1
    
    failure = report["determinism_failures"][0]
    assert failure["seed"] == 42
    # Divergence was mapped in temp workspace at tick 50
    assert failure["earliest_divergence_tick"] == 50


def test_pattern_mining_engine(temp_experiment_workspace):
    """Verify PatternMiningEngine segregates anomalies by gameplay domain."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    report = PatternMiningEngine.mine_patterns(exp_id, base_dir=parent_dir)
    
    assert len(report["outlier_runs"]) > 0
    assert len(report["recurring_anomalies"]) > 0
    
    # Check that STUCK_NAVIGATION or QUEST_STALLED rule ranks are populated
    rules = [r["rule_id"] for r in report["recurring_anomalies"]]
    assert "STUCK_NAVIGATION" in rules or "QUEST_STALLED" in rules


def test_priority_scorer_and_backlog(temp_experiment_workspace):
    """Verify priority scoring calculates ranks correctly and compiles suggestion plays."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    # 1. Build dataset
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    # 2. Mine patterns
    PatternMiningEngine.mine_patterns(exp_id, base_dir=parent_dir)
    # 3. Audit determinism
    DeterminismAuditor.audit_determinism(exp_id, base_dir=parent_dir)
    
    backlog = EngineeringBacklogGenerator.generate_backlog(exp_id, base_dir=parent_dir)
    
    assert len(backlog["backlog_items"]) > 0
    # The determinism failure should rank first as P0
    assert backlog["backlog_items"][0]["priority"] == "P0"
    assert "reproduction_seed" in backlog["backlog_items"][0]


def test_evidence_pack_builder(temp_experiment_workspace):
    """Verify EvidencePackBuilder isolates and extracts telemetry slices."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    PatternMiningEngine.mine_patterns(exp_id, base_dir=parent_dir)
    DeterminismAuditor.audit_determinism(exp_id, base_dir=parent_dir)
    EngineeringBacklogGenerator.generate_backlog(exp_id, base_dir=parent_dir)
    
    # Get the determinism failure candidate ID
    candidate_id = "det_fail_seed_42"
    pack = EvidencePackBuilder.build_evidence_pack(exp_id, candidate_id, base_dir=parent_dir)
    
    evidence_dir = os.path.join(exp_dir, "evidence_packs", candidate_id)
    assert os.path.exists(evidence_dir)
    assert os.path.exists(os.path.join(evidence_dir, "evidence_pack.json"))
    assert os.path.exists(os.path.join(evidence_dir, "metric_windows_excerpt.jsonl"))
    assert os.path.exists(os.path.join(evidence_dir, "events_excerpt.jsonl"))
    assert os.path.exists(os.path.join(evidence_dir, "reproduction_commands.md"))


def test_ai_agent_investigation_orchestrator(temp_experiment_workspace):
    """Verify AIAgentInvestigationRunner handles schema validity gates."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    PatternMiningEngine.mine_patterns(exp_id, base_dir=parent_dir)
    DeterminismAuditor.audit_determinism(exp_id, base_dir=parent_dir)
    EngineeringBacklogGenerator.generate_backlog(exp_id, base_dir=parent_dir)
    
    candidate_id = "det_fail_seed_42"
    EvidencePackBuilder.build_evidence_pack(exp_id, candidate_id, base_dir=parent_dir)
    
    findings = AIAgentInvestigationRunner.run_investigation(exp_id, candidate_id, base_dir=parent_dir)
    
    assert findings["candidate_id"] == candidate_id
    assert findings["verdict"] == "CONFIRMED_NONDETERMINISM"
    assert findings["confidence"] == 1.0
    
    evidence_dir = os.path.join(exp_dir, "evidence_packs", candidate_id)
    assert os.path.exists(os.path.join(evidence_dir, "agent_findings.json"))
    assert os.path.exists(os.path.join(evidence_dir, "agent_investigation_report.md"))


def test_next_experiment_recommender(temp_experiment_workspace):
    """Verify NextExperimentRecommender identifies gaps and configures follow-ups."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    PatternMiningEngine.mine_patterns(exp_id, base_dir=parent_dir)
    DeterminismAuditor.audit_determinism(exp_id, base_dir=parent_dir)
    EngineeringBacklogGenerator.generate_backlog(exp_id, base_dir=parent_dir)
    
    recs = NextExperimentRecommender.recommend_next(exp_id, base_dir=parent_dir)
    
    assert len(recs["recommended_experiments"]) > 0
    # Should recommend follow-up experiment for seed 42 same_seed_repeat
    assert recs["recommended_experiments"][0]["experiment_type"] == "same_seed_repeat"


def test_review_workflow_and_quality_gate(temp_experiment_workspace):
    """Verify MiningReviewWorkflow applies human labels and MiningQualityGate evaluates CI outcomes."""
    exp_dir = temp_experiment_workspace
    exp_id = os.path.basename(exp_dir)
    parent_dir = os.path.dirname(exp_dir)
    
    # Setup backlog
    MiningDatasetBuilder.build_dataset(exp_id, base_dir=parent_dir)
    PatternMiningEngine.mine_patterns(exp_id, base_dir=parent_dir)
    DeterminismAuditor.audit_determinism(exp_id, base_dir=parent_dir)
    EngineeringBacklogGenerator.generate_backlog(exp_id, base_dir=parent_dir)
    
    # 1. Test workflow labeling
    candidate_id = "det_fail_seed_42"
    backlog = MiningReviewWorkflow.apply_review_label(exp_id, candidate_id, "ACCEPTED_FOR_INVESTIGATION", reviewer="john_doe", base_dir=parent_dir)
    
    item = [x for x in backlog["backlog_items"] if x["candidate_id"] == candidate_id][0]
    assert item["review_status"] == "ACCEPTED_FOR_INVESTIGATION"
    assert item["reviewed_by"] == "john_doe"
    
    # 2. Test Quality Gate (should FAIL because of confirmed nondeterminism)
    gate = MiningQualityGate.evaluate_gate(exp_id, base_dir=parent_dir)
    assert gate["verdict"] == "FAIL"
    assert len(gate["failure_reasons"]) > 0
