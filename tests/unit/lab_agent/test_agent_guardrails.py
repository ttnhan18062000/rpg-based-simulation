"""
Unit tests for M104 — Token, Time, and Storage Guardrails
Tests: test_agent_guardrails.py

Validates:
- Context pack respects max_evidence_packs limit
- Raw logs are blocked by default (raw_logs_allowed=False)
- Raw logs are allowed when explicitly enabled
- Deep analysis requires explicit allow_deep_analysis=True in constraints
- Oversized experiment creates warning/block outcomes
- Storage estimates are included in readiness report
- Guardrail violations are recorded in audit log
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore
from src.lab.context import ContextPackBuilder, RawLogAccessError
from src.lab.audit import LabAuditTrail
from src.lab.workflows import (
    PrepareSimulationExecutionWorkflow,
    InvestigateSimulationResultWorkflow,
    GenerateSimulationSetupWorkflow,
    safe_path_resolution,
)


# ──────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────

@pytest.fixture
def mock_workspace(tmp_path: Path) -> Path:
    """Fully populated workspace with sessions, draft specs, and registration data."""
    # Docs
    docs_dir = tmp_path / "docs" / "mechanics"
    docs_dir.mkdir(parents=True)
    (docs_dir / "worldbuilding_rules.md").write_text("Rule 1: Balance resources.", encoding="utf-8")
    (docs_dir / "testing_principles.md").write_text("Principle 1: Deterministic seeds.", encoding="utf-8")
    (docs_dir / "investigation_rules.md").write_text("Rule: Check for anomalies.", encoding="utf-8")

    known_issues = [
        {"id": "ISS-001", "title": "Economy Inflation", "description": "Gold stacks", "domain": "economy", "tags": ["economy"]},
        {"id": "ISS-002", "title": "Pathing Bug", "description": "Workers stuck", "domain": "movement", "tags": ["movement"]},
        {"id": "ISS-003", "title": "Housing Crisis", "description": "No beds", "domain": "housing", "tags": ["housing"]},
    ]
    with open(docs_dir / "known_issues.json", "w", encoding="utf-8") as f:
        json.dump(known_issues, f)

    # Data dirs
    data_dir = tmp_path / "data"
    for d in ["worlds", "scenarios", "experiments", "runs", "issues"]:
        (data_dir / d).mkdir(parents=True)

    with open(data_dir / "worlds" / "world_index.json", "w") as f:
        json.dump({"world_valley": {}}, f)
    with open(data_dir / "scenarios" / "scenario_index.json", "w") as f:
        json.dump({"scen_1": {}}, f)
    with open(data_dir / "experiments" / "experiment_index.json", "w") as f:
        json.dump({"exp_1": {}}, f)
    with open(data_dir / "runs" / "historical_setups.json", "w") as f:
        json.dump([{"run_id": "old_1"}, {"run_id": "old_2"}, {"run_id": "old_3"}], f)
    with open(data_dir / "issues" / "issue_index.json", "w") as f:
        json.dump({}, f)
    with open(data_dir / "issues" / "signal_coverage.json", "w") as f:
        json.dump({}, f)

    # Lab sessions
    sessions_dir = data_dir / "lab_sessions"
    store = LabSessionStore(sessions_dir)
    store.create_session("session_g1")

    session_dir = store.resolve_session_dir("session_g1")

    # Build registration data with 4 run evidence packs
    reg_dir = session_dir / "registration"
    reg_dir.mkdir(parents=True, exist_ok=True)

    with open(reg_dir / "lab_summary.json", "w") as f:
        json.dump({"completed_run_count": 4, "failed_run_count": 0, "status": "GREEN"}, f)
    with open(reg_dir / "missing_signals.json", "w") as f:
        json.dump([], f)

    for i in range(1, 5):
        run_dir = reg_dir / "runs" / f"run_00{i}"
        run_dir.mkdir(parents=True, exist_ok=True)
        with open(run_dir / "run_report.json", "w") as f:
            json.dump({"run_id": f"run_00{i}", "score": 90.0 + i}, f)
        # Each run also has a heavy raw log file
        (run_dir / "simulation_events.jsonl").write_text(
            '{"tick": 1, "event": "unit_move"}\n' * 200, encoding="utf-8"
        )

    return tmp_path


@pytest.fixture
def builder(mock_workspace: Path) -> ContextPackBuilder:
    return ContextPackBuilder(mock_workspace)


# ──────────────────────────────────────────────────────
# Tests: Context Pack Limits
# ──────────────────────────────────────────────────────

class TestContextPackLimits:
    def test_max_evidence_packs_is_respected(self, builder: ContextPackBuilder):
        """Context pack must load at most max_evidence_packs evidence scorecards."""
        request = WorkflowRequest(workflow="InvestigateSimulationResult", mode="generic", user_goal="investigate")
        pack = builder.build_investigation_pack("session_g1", request, limits={"max_evidence_packs": 2})
        assert len(pack["top_n_evidence_packs"]) == 2

    def test_max_known_issues_is_respected(self, builder: ContextPackBuilder, mock_workspace: Path):
        """Generation pack must truncate known issues to max_known_issues."""
        request = WorkflowRequest(workflow="GenerateSimulationSetup", mode="generic", user_goal="test anything")
        pack = builder.build_generation_pack("session_g1", request, limits={"max_known_issues": 2})
        # The workspace has 3 issues, but none match "test anything" in tags/domain
        # So known_issues should be <= 2 if any filter hits
        assert len(pack["known_issues"]) <= 2

    def test_max_previous_runs_is_respected(self, builder: ContextPackBuilder):
        """Generation pack must truncate historical setups to max_previous_runs."""
        request = WorkflowRequest(workflow="GenerateSimulationSetup", mode="generic", user_goal="stress test")
        pack = builder.build_generation_pack("session_g1", request, limits={"max_previous_runs": 1})
        assert len(pack["similar_previous_setups"]) == 1

    def test_default_evidence_packs_limit_is_three(self, builder: ContextPackBuilder):
        """Default max_evidence_packs is 3 — should not load all 4 run packs by default."""
        request = WorkflowRequest(workflow="InvestigateSimulationResult", mode="generic", user_goal="investigate")
        pack = builder.build_investigation_pack("session_g1", request)  # no limits override
        assert len(pack["top_n_evidence_packs"]) == 3


# ──────────────────────────────────────────────────────
# Tests: Raw Log Access Guardrail
# ──────────────────────────────────────────────────────

class TestRawLogGuardrail:
    def test_raw_logs_excluded_by_default(self, builder: ContextPackBuilder):
        """By default (raw_logs_allowed=False), simulation_events.jsonl must not appear in the pack."""
        request = WorkflowRequest(workflow="InvestigateSimulationResult", mode="generic", user_goal="investigate")
        pack = builder.build_investigation_pack("session_g1", request)
        pack_str = json.dumps(pack)
        assert "simulation_events.jsonl" not in pack_str
        assert "unit_move" not in pack_str

    def test_raw_logs_flag_is_captured_in_pack(self, builder: ContextPackBuilder):
        """raw_logs_allowed flag must be reflected in the returned context pack."""
        request = WorkflowRequest(workflow="InvestigateSimulationResult", mode="generic", user_goal="investigate")
        pack_default = builder.build_investigation_pack("session_g1", request)
        assert pack_default["raw_logs_allowed"] is False
        assert pack_default["limits"]["raw_logs_allowed"] is False

    def test_raw_logs_flag_true_is_preserved(self, builder: ContextPackBuilder):
        """When raw_logs_allowed=True is set, the flag must be reflected in the pack."""
        request = WorkflowRequest(workflow="InvestigateSimulationResult", mode="generic", user_goal="investigate")
        pack = builder.build_investigation_pack("session_g1", request, limits={"raw_logs_allowed": True})
        assert pack["raw_logs_allowed"] is True

    def test_generation_pack_raw_logs_allowed_false_by_default(self, builder: ContextPackBuilder):
        """Generation context pack must also default raw_logs_allowed to False."""
        request = WorkflowRequest(workflow="GenerateSimulationSetup", mode="generic", user_goal="setup")
        pack = builder.build_generation_pack("session_g1", request)
        assert pack["raw_logs_allowed"] is False


# ──────────────────────────────────────────────────────
# Tests: Deep Analysis Confirmation Gate
# ──────────────────────────────────────────────────────

class TestDeepAnalysisGate:
    def _build_minimal_workspace(self, tmp_path: Path) -> tuple[Path, LabSessionStore]:
        """Build a minimal workspace with compacted data so investigation can run."""
        # Build required directory structure
        for d in ["worlds", "scenarios", "experiments", "runs", "issues"]:
            (tmp_path / "data" / d).mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "mechanics").mkdir(parents=True, exist_ok=True)
        for fname, content in [
            ("worldbuilding_rules.md", "Rule: Balance resources."),
            ("testing_principles.md", "Principle: Deterministic seeds."),
            ("investigation_rules.md", "Rule: Check anomalies."),
        ]:
            (tmp_path / "docs" / "mechanics" / fname).write_text(content, encoding="utf-8")
        import json as _json
        for fname, data in [
            ("data/worlds/world_index.json", {}),
            ("data/scenarios/scenario_index.json", {}),
            ("data/experiments/experiment_index.json", {}),
            ("docs/mechanics/known_issues.json", []),
            ("data/issues/issue_index.json", {}),
            ("data/issues/signal_coverage.json", {}),
        ]:
            with open(tmp_path / fname, "w") as f:
                _json.dump(data, f)

        data_dir = tmp_path / "data"
        sessions_dir = data_dir / "lab_sessions"
        store = LabSessionStore(sessions_dir)
        store.create_session("sess_deep")

        # Generate draft specs using the workflow so YAML is schema-compliant
        gen_req = WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="generic",
            user_goal="verification run for deep analysis gate test",
            constraints={"budget_profile": "local_dev"}
        )
        GenerateSimulationSetupWorkflow(workspace_root=tmp_path).run("sess_deep", gen_req)

        session_dir = store.resolve_session_dir("sess_deep")
        reg_dir = session_dir / "registration"
        reg_dir.mkdir(parents=True, exist_ok=True)

        # Create compact summary and issue index required by investigation workflow
        with open(reg_dir / "compact_summary.json", "w") as f:
            _json.dump({
                "lab_run_id": "run_deep_01",
                "total_runs": 2,
                "run_count": 2,
                "total_ticks": 200,
                "avg_health_score": 88.5,
                "status": "COMPLETED",
                "compacted_at": "2026-01-01",
                "summary_stats": {
                    "completed_run_count": 2,
                    "failed_run_count": 0,
                    "avg_health_score": 88.5,
                    "top_anomalies": {"EconInflation": 2}
                }
            }, f)
        with open(reg_dir / "issue_index.json", "w") as f:
            _json.dump([{
                "rule_name": "EconCheck",
                "severity": "WARNING",
                "domain": "economy",
                "description": "Economy inflation detected",
                "count": 3
            }], f)

        # Create run path reference
        lab_runs_dir = data_dir / "lab_runs" / "run_deep_01"
        lab_runs_dir.mkdir(parents=True, exist_ok=True)
        with open(lab_runs_dir / "lab_run_manifest.json", "w") as f:
            _json.dump({"status": "COMPLETED", "lab_run_id": "run_deep_01"}, f)
        (reg_dir / "actual_lab_run_path.txt").write_text(
            "data/lab_runs/run_deep_01", encoding="utf-8"
        )

        return tmp_path, store

    def test_deep_analysis_without_flag_is_downgraded(self, tmp_path: Path):
        """If analysis_depth=deep is requested but allow_deep_analysis not in constraints,
        it must be silently downgraded to standard and log a guardrail_violation event."""
        workspace, store = self._build_minimal_workspace(tmp_path)

        request = WorkflowRequest(
            workflow="InvestigateSimulationResult",
            mode="specific",
            user_goal="investigate",
            specific_inputs={
                "lab_run_path": "data/lab_runs/run_deep_01",
                "analysis_depth": "deep"
            },
            constraints={}  # No allow_deep_analysis
        )

        workflow = InvestigateSimulationResultWorkflow(workspace_root=workspace)
        result = workflow.run("sess_deep", request)

        # Workflow must succeed (not blocked)
        assert result["status"] != "BLOCKED" or "analysis_depth" not in result.get("reason", "")

        # Guardrail violation must be in audit log
        trail = LabAuditTrail(workspace)
        events = trail.read_log("sess_deep")
        violation_events = [e for e in events if e["event_type"] == "guardrail_violation"]
        deep_blocks = [e for e in violation_events if e["details"].get("violation_type") == "deep_analysis_blocked"]
        assert len(deep_blocks) >= 1
        assert deep_blocks[0]["details"]["action"] == "downgraded to standard depth"

    def test_deep_analysis_with_flag_is_permitted(self, tmp_path: Path):
        """If analysis_depth=deep is requested with allow_deep_analysis=True in constraints,
        no guardrail violation should be logged."""
        workspace, store = self._build_minimal_workspace(tmp_path)

        request = WorkflowRequest(
            workflow="InvestigateSimulationResult",
            mode="specific",
            user_goal="investigate",
            specific_inputs={
                "lab_run_path": "data/lab_runs/run_deep_01",
                "analysis_depth": "deep"
            },
            constraints={"allow_deep_analysis": True}
        )

        workflow = InvestigateSimulationResultWorkflow(workspace_root=workspace)
        workflow.run("sess_deep", request)

        trail = LabAuditTrail(workspace)
        events = trail.read_log("sess_deep")
        deep_blocks = [
            e for e in events
            if e["event_type"] == "guardrail_violation"
            and e["details"].get("violation_type") == "deep_analysis_blocked"
        ]
        # No deep analysis blocks should be present
        assert len(deep_blocks) == 0


# ──────────────────────────────────────────────────────
# Tests: Storage Estimate in Readiness Report
# ──────────────────────────────────────────────────────

class TestStorageEstimateInReadinessReport:
    def _build_prep_workspace(self, tmp_path: Path) -> Path:
        """Build workspace with valid draft specs using GenerateSimulationSetupWorkflow."""
        for d in ["worlds", "scenarios", "experiments", "runs", "issues"]:
            (tmp_path / "data" / d).mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "mechanics").mkdir(parents=True, exist_ok=True)
        for fname, content in [
            ("worldbuilding_rules.md", "Rule: Balance resources."),
            ("testing_principles.md", "Principle: Deterministic seeds."),
        ]:
            (tmp_path / "docs" / "mechanics" / fname).write_text(content, encoding="utf-8")
        for fname, data in [
            ("data/worlds/world_index.json", {}),
            ("data/scenarios/scenario_index.json", {}),
            ("data/experiments/experiment_index.json", {}),
        ]:
            with open(tmp_path / fname, "w") as f:
                json.dump(data, f)

        sessions_dir = tmp_path / "data" / "lab_sessions"
        store = LabSessionStore(sessions_dir)
        store.create_session("sess_prep")

        # Generate compliant draft specs
        gen_req = WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="generic",
            user_goal="standard verification run",
            constraints={"budget_profile": "local_dev"}
        )
        GenerateSimulationSetupWorkflow(workspace_root=tmp_path).run("sess_prep", gen_req)
        return tmp_path

    def test_readiness_report_includes_storage_estimate(self, tmp_path: Path):
        """execution_readiness_report.json must include storage_estimate with all required keys."""
        workspace = self._build_prep_workspace(tmp_path)

        request = WorkflowRequest(
            workflow="PrepareSimulationExecution",
            mode="generic",
            user_goal="prepare run",
            constraints={"budget_profile": "local_dev"}
        )

        workflow = PrepareSimulationExecutionWorkflow(workspace_root=workspace)
        result = workflow.run("sess_prep", request)

        assert result["status"] == "READY"

        # Verify the readiness JSON has storage_estimate
        support_dir = workflow.session_store.get_stage_dir("sess_prep", "EXECUTION_SUPPORT")
        report_path = support_dir / "execution_readiness_report.json"
        assert report_path.is_file()

        with open(report_path, "r") as f:
            report = json.load(f)

        assert "storage_estimate" in report
        est = report["storage_estimate"]
        for key in ["run_count", "total_ticks", "expected_entity_count", "expected_event_volume",
                    "expected_artifact_mb", "expected_runtime_minutes"]:
            assert key in est, f"Missing estimate key: {key}"
        # Sanity: run_count should be a positive integer
        assert est["run_count"] >= 1
        assert est["total_ticks"] >= 1


# ──────────────────────────────────────────────────────
# Tests: Guardrail Violations Recorded in Audit Log
# ──────────────────────────────────────────────────────

class TestGuardrailViolationsInAuditLog:
    def _make_oversized_prep_workspace(self, tmp_path: Path) -> Path:
        """Build workspace with a CI-limit-violating experiment spec."""
        for d in ["worlds", "scenarios", "experiments", "runs", "issues"]:
            (tmp_path / "data" / d).mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "mechanics").mkdir(parents=True, exist_ok=True)
        for fname, content in [
            ("worldbuilding_rules.md", "Rule: Balance resources."),
            ("testing_principles.md", "Principle: Deterministic seeds."),
        ]:
            (tmp_path / "docs" / "mechanics" / fname).write_text(content, encoding="utf-8")
        for fname, data in [
            ("data/worlds/world_index.json", {}),
            ("data/scenarios/scenario_index.json", {}),
            ("data/experiments/experiment_index.json", {}),
        ]:
            with open(tmp_path / fname, "w") as f:
                json.dump(data, f)

        sessions_dir = tmp_path / "data" / "lab_sessions"
        store = LabSessionStore(sessions_dir)
        store.create_session("sess_ci")

        # Generate baseline specs using workflow (schema-compliant)
        gen_req = WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="generic",
            user_goal="stress test oversized sweep",
            constraints={"budget_profile": "local_dev"}
        )
        GenerateSimulationSetupWorkflow(workspace_root=tmp_path).run("sess_ci", gen_req)

        # Now override the experiment.yaml with an oversized one (25 seeds)
        gen_dir = store.get_stage_dir("sess_ci", "GENERATION")
        draft_dir = gen_dir / "draft_specs"
        # Load existing experiment to find the scenario/world IDs
        import yaml as _yaml
        with open(draft_dir / "experiment.yaml") as f:
            exp_data = _yaml.safe_load(f)
        with open(draft_dir / "scenario.yaml") as f:
            sc_data = _yaml.safe_load(f)

        # Overwrite with 25 seeds (CI limit is 20)
        exp_data["run"]["seeds"] = list(range(1, 26))
        exp_data["run"]["ticks"] = 300
        with open(draft_dir / "experiment.yaml", "w") as f:
            _yaml.dump(exp_data, f)

        return tmp_path

    def test_oversized_experiment_is_blocked_on_ci_profile(self, tmp_path: Path):
        """An oversized experiment on CI profile must be blocked and return BLOCKED status."""
        workspace = self._make_oversized_prep_workspace(tmp_path)
        request = WorkflowRequest(
            workflow="PrepareSimulationExecution",
            mode="generic",
            user_goal="prepare run",
            constraints={"budget_profile": "CI"}
        )
        workflow = PrepareSimulationExecutionWorkflow(workspace_root=workspace)
        result = workflow.run("sess_ci", request)
        assert result["status"] == "BLOCKED"
        assert "budget" in result["reason"].lower() or "CI" in result["reason"]

    def test_guardrail_block_is_recorded_in_audit_log(self, tmp_path: Path):
        """When a budget BLOCK occurs on CI, a guardrail_violation audit event must be written."""
        workspace = self._make_oversized_prep_workspace(tmp_path)
        request = WorkflowRequest(
            workflow="PrepareSimulationExecution",
            mode="generic",
            user_goal="prepare run",
            constraints={"budget_profile": "CI"}
        )
        workflow = PrepareSimulationExecutionWorkflow(workspace_root=workspace)
        workflow.run("sess_ci", request)

        trail = LabAuditTrail(workspace)
        events = trail.read_log("sess_ci")
        violations = [e for e in events if e["event_type"] == "guardrail_violation"]
        blocks = [e for e in violations if e["details"].get("violation_type") == "budget_blocked"]
        assert len(blocks) >= 1
        assert "blocked_reasons" in blocks[0]["details"]

    def test_oversized_experiment_creates_warning_on_local_profile(self, tmp_path: Path):
        """An experiment with 60 runs on local_dev profile triggers a warning in the budget report."""
        # Setup workspace
        for d in ["worlds", "scenarios", "experiments", "runs", "issues"]:
            (tmp_path / "data" / d).mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "mechanics").mkdir(parents=True, exist_ok=True)
        for fname, content in [
            ("worldbuilding_rules.md", "Rule: Balance resources."),
            ("testing_principles.md", "Principle: Deterministic seeds."),
        ]:
            (tmp_path / "docs" / "mechanics" / fname).write_text(content, encoding="utf-8")
        for fname, data in [
            ("data/worlds/world_index.json", {}),
            ("data/scenarios/scenario_index.json", {}),
            ("data/experiments/experiment_index.json", {}),
        ]:
            with open(tmp_path / fname, "w") as f:
                json.dump(data, f)

        sessions_dir = tmp_path / "data" / "lab_sessions"
        store = LabSessionStore(sessions_dir)
        store.create_session("sess_warn")

        # Generate compliant baseline specs
        gen_req = WorkflowRequest(
            workflow="GenerateSimulationSetup",
            mode="generic",
            user_goal="many seeds sweep test",
            constraints={"budget_profile": "local_dev"}
        )
        GenerateSimulationSetupWorkflow(workspace_root=tmp_path).run("sess_warn", gen_req)

        # Override experiment.yaml with 60 seeds to trigger a warning
        gen_dir = store.get_stage_dir("sess_warn", "GENERATION")
        draft_dir = gen_dir / "draft_specs"
        import yaml as _yaml
        with open(draft_dir / "experiment.yaml") as f:
            exp_data = _yaml.safe_load(f)
        exp_data["run"]["seeds"] = list(range(1, 61))  # 60 seeds > typical warning threshold
        exp_data["run"]["ticks"] = 10
        with open(draft_dir / "experiment.yaml", "w") as f:
            _yaml.dump(exp_data, f)

        request = WorkflowRequest(
            workflow="PrepareSimulationExecution",
            mode="generic",
            user_goal="prepare run",
            constraints={"budget_profile": "local_dev"}
        )
        workflow = PrepareSimulationExecutionWorkflow(workspace_root=tmp_path)
        result = workflow.run("sess_warn", request)

        # Should not be fully blocked on local_dev, but budget_report should have warnings
        support_dir = workflow.session_store.get_stage_dir("sess_warn", "EXECUTION_SUPPORT")
        budget_report_path = support_dir / "budget_report.json"
        assert budget_report_path.is_file(), f"Budget report not found. Result: {result}"
        with open(budget_report_path) as f:
            budget_report = json.load(f)

        # With 60 runs the check returns WARNING or OK (local_dev won't block at 60)
        assert budget_report["status"] in ("WARNING", "OK"), \
            f"Expected WARNING or OK status, got: {budget_report['status']}"
        # Audit log should have a budget_warning violation event
        trail = LabAuditTrail(tmp_path)
        events = trail.read_log("sess_warn")
        warnings = [
            e for e in events
            if e["event_type"] == "guardrail_violation"
            and e["details"].get("violation_type") == "budget_warning"
        ]
        assert len(warnings) >= 1, \
            f"Expected budget_warning guardrail event in audit log. Events: {[e['event_type'] for e in events]}"
