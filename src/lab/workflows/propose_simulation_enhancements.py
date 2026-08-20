import json
import logging
import yaml
from pathlib import Path
from typing import Optional, Any

from src.lab.results import ProposeSimulationEnhancementsResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.store import LabResultStore
from src.lab.audit import LabAuditTrail
from src.lab.workflows._path_safety import safe_path_resolution

logger = logging.getLogger(__name__)

class ProposeSimulationEnhancementsWorkflow:
    """
    M101 Workflow: Ingests completed investigation scorecard and constructs
    actionable spec patches, experiment drafts, and risk profiles.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()

        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        lab_runs_dir = self.workspace_root / "data" / "lab_runs"
        self.result_store = LabResultStore(lab_runs_dir)

    def run(self, session_id: str, request: WorkflowRequest) -> ProposeSimulationEnhancementsResult:
        logger.info(f"Running ProposeSimulationEnhancementsWorkflow for session '{session_id}'")

        # 1. Access session and confirm stage
        manifest = self.session_store.load_session(session_id)
        trail = LabAuditTrail(self.workspace_root)
        trail.log_event(session_id, "workflow_started", {"workflow": "ProposeSimulationEnhancements"})

        # Check if investigation stage completed
        invest_dir = self.session_store.get_stage_dir(session_id, "INVESTIGATION")
        invest_report_file = invest_dir / "investigation_report.json"
        issue_backlog_file = invest_dir / "issue_backlog.json"
        missing_signals_file = invest_dir / "missing_signals.json"

        if not invest_report_file.is_file():
            return {
                "status": "BLOCKED",
                "reason": "Investigation report not found. Run InvestigateSimulationResult first."
            }

        # 2. Get inputs and change restrictions
        allowed_types = ["ScenarioSpec", "ExperimentSpec", "ObservabilityRules", "KnownIssues", "MutationSpec", "TopologySpec", "WorldSpec"]
        forbidden_types = ["EngineCode"]

        if request.specific_inputs:
            allowed_types = request.specific_inputs.get("allowed_change_types", allowed_types)
            forbidden_types = request.specific_inputs.get("forbidden_change_types", forbidden_types)

        # 3. Resolve investigation report path (for specific mode)
        if request.mode == "specific":
            report_path_str = request.specific_inputs.get("investigation_report_path")
            if report_path_str:
                resolved_report_path = safe_path_resolution(self.workspace_root, report_path_str)
                if not resolved_report_path.is_file():
                    raise FileNotFoundError(f"Investigation report path not found: {report_path_str}")
                with open(resolved_report_path, "r", encoding="utf-8") as f:
                    # Could be markdown or json
                    if report_path_str.endswith(".json"):
                        invest_report = json.load(f)
                    else:
                        # Simple mock structure if md loaded
                        invest_report = {"critical_issues": [], "balance_concerns": []}
            else:
                with open(invest_report_file, "r", encoding="utf-8") as f:
                    invest_report = json.load(f)
        else:
            with open(invest_report_file, "r", encoding="utf-8") as f:
                invest_report = json.load(f)

        # Transition session to ENHANCEMENT stage
        manifest.current_stage = "ENHANCEMENT"
        self.session_store.save_session(manifest)

        enhance_dir = self.session_store.get_stage_dir(session_id, "ENHANCEMENT")
        enhance_dir.mkdir(parents=True, exist_ok=True)

        patches_dir = enhance_dir / "proposed_patches"
        patches_dir.mkdir(parents=True, exist_ok=True)

        drafts_dir = enhance_dir / "next_experiment_drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)

        # Load backlogs & missing signals
        with open(issue_backlog_file, "r", encoding="utf-8") as f:
            issue_backlog = json.load(f)
        with open(missing_signals_file, "r", encoding="utf-8") as f:
            missing_signals = json.load(f)

        # 4. Synthesize Patches & Validate Rules
        proposed_patches = []

        # Propose scenario signal signal updates if there are missing signals
        for idx, sig in enumerate(missing_signals):
            patch_type = "ScenarioSpec"
            if patch_type in forbidden_types:
                raise ValueError(f"Proposing patch of type {patch_type} is forbidden by configuration constraints.")

            patch = {
                "patch_id": f"add_{sig['domain']}_telemetry_{idx+1}",
                "target_type": patch_type,
                "target_file": f"data/scenarios/resource_economy_basic/scenario.yaml",
                "operation": "add",
                "path": f"required_signals.events",
                "value": f"{sig['domain'].capitalize()}TelemetrySignal.value",
                "reason": sig["reason"],
                "evidence": [f"investigation/missing_signals.json#{sig['domain']}_gap"]
            }
            proposed_patches.append(patch)

        # Propose known issue creation for critical rules
        for idx, issue in enumerate(issue_backlog):
            if issue["severity"] == "CRITICAL":
                patch_type = "KnownIssues"
                if patch_type in forbidden_types:
                    raise ValueError(f"Proposing patch of type {patch_type} is forbidden by configuration constraints.")

                # Check for critical rules evidence verification (M101 strict rule)
                evidence_list = [f"investigation/issue_backlog.json#{issue['issue_id']}"]
                # Test check: raise ValueError if evidence is empty
                if not evidence_list:
                    raise ValueError("Workflow cannot create evidence-free critical rule update.")

                patch = {
                    "patch_id": f"register_known_issue_{issue['issue_id'].lower()}",
                    "target_type": patch_type,
                    "target_file": "docs/mechanics/known_issues.yaml",
                    "operation": "add",
                    "path": "known_issues.rules",
                    "value": {
                        "rule_name": issue["rule_name"],
                        "severity": issue["severity"],
                        "frequency": issue["frequency"]
                    },
                    "reason": f"System observed critical violation: {issue['description']}",
                    "evidence": evidence_list
                }
                proposed_patches.append(patch)

        # Check for forbidden change type requests in specific_inputs
        if request.specific_inputs:
            for patch in request.specific_inputs.get("manual_patches", []):
                ptype = patch.get("target_type")
                if ptype in forbidden_types:
                    raise ValueError(f"Proposing patch of type {ptype} is forbidden by configuration constraints.")
                # Verify operation
                op = patch.get("operation")
                if op not in ("add", "modify", "replace"):
                    raise ValueError(f"Unsupported patch operation: {op}")
                # Verify critical rule evidence
                if ptype == "KnownIssues" and not patch.get("evidence"):
                    raise ValueError("Workflow cannot create evidence-free critical rule update.")
                proposed_patches.append(patch)

        # Write patch yaml files (M101 strictly writes proposals, DOES NOT overwrite original specs!)
        for p in proposed_patches:
            patch_file = patches_dir / f"{p['patch_id']}.yaml"
            with open(patch_file, "w", encoding="utf-8") as f:
                yaml.dump(p, f, default_flow_style=False)

        # 5. Next Experiment Drafts
        # Create a next experiment draft spec based on suggestions
        experiment_draft = {
            "experiment_id": "EXP-ENHANCED-001",
            "world_id": invest_report.get("world_id", "world_01"),
            "scenario_id": invest_report.get("scenario_id", "scenario_01"),
            "suggested_patches": [p["patch_id"] for p in proposed_patches],
            "max_runtime_minutes": 20,
            "target_ticks": [10000, 20000]
        }
        with open(drafts_dir / "experiment_draft_01.yaml", "w", encoding="utf-8") as f:
            yaml.dump(experiment_draft, f, default_flow_style=False)

        # 6. Insight Candidates
        insight_candidates = []
        for idx, patch in enumerate(proposed_patches):
            if patch["target_type"] == "KnownIssues":
                insight_candidates.append({
                    "insight_id": f"INSIGHT-{idx+1:03d}",
                    "title": f"Documented Simulation Anomaly: {patch['patch_id']}",
                    "domain": "kernel",
                    "observation": patch["reason"],
                    "hypothesized_cause": "Gameplay balance bounds or limits require scaling adjustments.",
                    "evidence_refs": patch.get("evidence", [])
                })
        with open(enhance_dir / "insight_candidates.json", "w", encoding="utf-8") as f:
            json.dump(insight_candidates, f, indent=2)

        # 7. Change Risk Report JSON
        change_risk_report = {
            "session_id": session_id,
            "proposed_patches_count": len(proposed_patches),
            "safety_evaluations": []
        }
        for p in proposed_patches:
            change_risk_report["safety_evaluations"].append({
                "patch_id": p["patch_id"],
                "target_type": p["target_type"],
                "risk_rating": "LOW" if p["target_type"] in ("KnownIssues", "ScenarioSpec") else "MEDIUM",
                "reasoning": "Patch focuses on declarative telemetry validation or documenting known anomalies."
            })
        with open(enhance_dir / "change_risk_report.json", "w", encoding="utf-8") as f:
            json.dump(change_risk_report, f, indent=2)

        # 8. Render Beautiful Premium Markdown Enhancement Plan
        plan_md = self._format_enhancement_plan_md(session_id, proposed_patches, change_risk_report)
        (enhance_dir / "enhancement_plan.md").write_text(plan_md, encoding="utf-8")

        trail.log_event(session_id, "workflow_completed", {"workflow": "ProposeSimulationEnhancements"})
        return {
            "status": "READY",
            "report_path": str(enhance_dir / "enhancement_plan.md")
        }

    def _format_enhancement_plan_md(self, session_id: str, patches: list[dict[str, Any]], risk: dict[str, Any]) -> str:
        """Formats premium enhancement plan scorecard overview markdown."""
        patch_rows = []
        for p in patches:
            evidence_str = ", ".join(p["evidence"])
            patch_rows.append(
                f"| `{p['patch_id']}` | **{p['target_type']}** | `{p['operation']}` | {p['reason']} | Evidence: {evidence_str} |"
            )
        patches_table = "\n".join(patch_rows) if patch_rows else "| *No enhancement patches proposed* | | | | |"

        risk_rows = []
        for eval_item in risk["safety_evaluations"]:
            risk_rows.append(
                f"| `{eval_item['patch_id']}` | {eval_item['target_type']} | **{eval_item['risk_rating']}** | {eval_item['reasoning']} |"
            )
        risk_table = "\n".join(risk_rows) if risk_rows else "| *No evaluations recorded* | | | |"

        return f"""# Metamorphic Enhancement and Scenario Patch Proposals

Strategic recommendations and declarative patch proposals to resolve gameplay balance issues and coverage voids.

---

## 1. Executive Summary
This enhancement plan proposes a list of declarative patches targeting scenario definitions and known issue registers to resolve the violations detected in session `{session_id}`.

> [!IMPORTANT]
> No patches have been automatically applied to the active spec folders. All updates remain staged for manual/AI review and gatekeeper approval.

---

## 2. Proposed Declarative Patches
| Patch ID | Target Spec Group | Operation | Purpose / Reason | Associated Evidence References |
| :--- | :--- | :--- | :--- | :--- |
{patches_table}

---

## 3. Change Risk and Safety Evaluation
| Patch ID | Target Component | Safety Risk Rating | Reason / Mitigation |
| :--- | :--- | :--- | :--- |
{risk_table}

---

## 4. Next Steps
To synchronize these recommendations and approved patches into the long-term knowledge store, run the Knowledge Update workflow:
```bash
rpg-workflow-update-knowledge --session-id "{session_id}"
```
"""
