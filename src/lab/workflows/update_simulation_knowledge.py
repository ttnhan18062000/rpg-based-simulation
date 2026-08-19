import hashlib
import json
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

from src.lab.results import UpdateSimulationKnowledgeResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.audit import LabAuditTrail
from src.lab.workflows._path_safety import safe_path_resolution

logger = logging.getLogger(__name__)

class UpdateSimulationKnowledgeWorkflow:
    """
    M102 Workflow: Store approved insights, known issues, rule updates, and decisions.
    Requires explicit user approval before execution.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()

        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        self.knowledge_root = self.workspace_root / "data" / "lab_knowledge"

    def run(self, session_id: str, request: WorkflowRequest) -> UpdateSimulationKnowledgeResult:
        logger.info(f"Running UpdateSimulationKnowledgeWorkflow for session '{session_id}'")
        from src.lab.audit import LabAuditTrail
        trail = LabAuditTrail(self.workspace_root)

        trail.log_event(session_id, "workflow_started", {
            "workflow": "UpdateSimulationKnowledge",
            "mode": request.mode
        })

        # 1. Access session and confirm stage
        manifest = self.session_store.load_session(session_id)

        # 2. Strict User Approval Verification
        # Check approval in specific_inputs
        inputs = request.specific_inputs or {}
        approved_by = inputs.get("approved_by")
        approval_recorded = inputs.get("approval_recorded", False)

        trail.log_event(session_id, "approval_required", {
            "workflow": "UpdateSimulationKnowledge",
            "required_stage": "ENHANCEMENT"
        })

        if not approved_by and not approval_recorded:
            trail.log_event(session_id, "blocked_action", {
                "reason": "Missing user approval credentials",
                "action": "Sync knowledge updates"
            })
            raise ValueError("Explicit user approval is required to update the simulation knowledge base.")

        # Record approval in audit log
        trail.log_event(session_id, "approval_recorded", {
            "approved_by": approved_by,
            "recorded": True
        })

        # Transition session to KNOWLEDGE_UPDATE stage
        manifest.current_stage = "KNOWLEDGE_UPDATE"
        self.session_store.save_session(manifest)

        # 3. Setup global knowledge base directories
        insights_dir = self.knowledge_root / "insights"
        issues_dir = self.knowledge_root / "known_issues"
        rules_dir = self.knowledge_root / "rules"
        principles_dir = self.knowledge_root / "principles"
        decisions_dir = self.knowledge_root / "decisions"

        for d in (insights_dir, issues_dir, rules_dir, principles_dir, decisions_dir):
            d.mkdir(parents=True, exist_ok=True)

        # 4. Ingest and Process Approved Items
        enhance_dir = self.session_store.get_stage_dir(session_id, "ENHANCEMENT")

        # Determine targets based on mode
        approved_insights = []
        approved_patches = []
        decision_note = inputs.get("decision_note", "No decision note provided.")

        if request.mode == "specific":
            # Specific approved files
            insight_paths = inputs.get("approved_insights", [])
            patch_paths = inputs.get("approved_patches", [])

            for path_str in insight_paths:
                resolved_path = safe_path_resolution(enhance_dir, path_str)
                if resolved_path.is_file():
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        approved_insights.append(json.load(f))

            for path_str in patch_paths:
                resolved_path = safe_path_resolution(enhance_dir, path_str)
                if resolved_path.is_file():
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        approved_patches.append(yaml.safe_load(f))
        else:
            # Generic mode: Ingest from latest enhancement results
            insight_file = enhance_dir / "insight_candidates.json"
            if insight_file.is_file():
                with open(insight_file, "r", encoding="utf-8") as f:
                    candidates = json.load(f)
                    approved_insights.extend(candidates)

            proposed_patches_dir = enhance_dir / "proposed_patches"
            if proposed_patches_dir.is_dir():
                for p_file in proposed_patches_dir.glob("*.yaml"):
                    with open(p_file, "r", encoding="utf-8") as f:
                        approved_patches.append(yaml.safe_load(f))

        # 5. Block unapproved rulebook/principles updates (Anti-misdirection rule)
        # Verify if request triggers rules/principles updates without approval
        has_rule_update = any(p.get("target_type") in ("ObservabilityRules", "ScenarioSpec", "WorldSpec") for p in approved_patches)
        if has_rule_update and not approved_by:
            raise ValueError("Workflow cannot update rules/principles without a valid approval marker.")

        # 6. Store Insights & Check Duplicates
        stored_insights = []
        insight_paths = []
        file_hashes: Dict[str, str] = {}
        for ins in approved_insights:
            insight_id = ins.get("insight_id", "INSIGHT-GENERIC")
            target_file = insights_dir / f"{insight_id.lower()}.json"

            if target_file.is_file():
                raise ValueError(f"Duplicate insight registration detected: {insight_id}")

            insight_record = {
                "insight_id": insight_id,
                "type": ins.get("type", "OBSERVABILITY_GAP"),
                "title": ins.get("title", ins.get("observation", "Generic insight")),
                "source_lab_run": ins.get("source_lab_run", session_id),
                "source_report": ins.get("source_report", ""),
                "evidence_refs": ins.get("evidence_refs", ins.get("evidence", [])),
                "status": "APPROVED",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            insight_json = json.dumps(insight_record, indent=2)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(insight_json)
            stored_insights.append(insight_record)
            relative_path = f"insights/{insight_id.lower()}.json"
            insight_paths.append(relative_path)
            file_hashes[relative_path] = hashlib.sha256(insight_json.encode("utf-8")).hexdigest()

        # 7. Store Known Issues
        stored_patches = []
        issue_paths = []
        rule_paths = []
        for patch in approved_patches:
            patch_id = patch.get("patch_id", "PATCH-GENERIC")
            if patch.get("target_type") == "KnownIssues":
                issue_file = issues_dir / f"{patch_id.lower()}.json"
                issue_record = {
                    "issue_id": patch_id,
                    "target_file": patch.get("target_file", ""),
                    "reason": patch.get("reason", ""),
                    "evidence_refs": patch.get("evidence", []),
                    "status": "STORED"
                }
                issue_json = json.dumps(issue_record, indent=2)
                with open(issue_file, "w", encoding="utf-8") as f:
                    f.write(issue_json)
                stored_patches.append(issue_record)
                relative_path = f"known_issues/{patch_id.lower()}.json"
                issue_paths.append(relative_path)
                file_hashes[relative_path] = hashlib.sha256(issue_json.encode("utf-8")).hexdigest()
            elif patch.get("target_type") in ("ScenarioSpec", "WorldSpec"):
                # Simulates rulebook updates
                rule_file = rules_dir / f"{patch_id.lower()}.json"
                rule_record = {
                    "patch_id": patch_id,
                    "target_type": patch.get("target_type"),
                    "version": "1.0.0",
                    "evidence_refs": patch.get("evidence", [])
                }
                rule_json = json.dumps(rule_record, indent=2)
                with open(rule_file, "w", encoding="utf-8") as f:
                    f.write(rule_json)
                stored_patches.append(rule_record)
                relative_path = f"rules/{patch_id.lower()}.json"
                rule_paths.append(relative_path)
                file_hashes[relative_path] = hashlib.sha256(rule_json.encode("utf-8")).hexdigest()

        # 8. Append Decision Log (JSON Lines)
        decision_file = decisions_dir / "decision_log.jsonl"
        log_entry = {
            "session_id": session_id,
            "decision_note": decision_note,
            "approved_by": approved_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(decision_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        # 9. Format Markdown Report
        report_md = self._format_knowledge_report_md(session_id, stored_insights, stored_patches, decision_note)
        report_path = enhance_dir / "knowledge_update_report.md"
        report_path.write_text(report_md, encoding="utf-8")

        # 10. Audit Logging
        synced_count = len(stored_insights) + len(stored_patches)
        sync_status = "SYNCED" if synced_count > 0 else "NO_INSIGHTS"

        trail.log_event(session_id, "files_read", {
            "files": ["insight_candidates.json", "proposed_patches/*"]
        })
        trail.log_event(session_id, "files_written", {
            "files": [str(report_path), "decisions/decision_log.jsonl"] + insight_paths + issue_paths + rule_paths,
            "file_hashes": file_hashes,
        })
        trail.log_event(session_id, "knowledge_sync_result", {
            "status": sync_status,
            "synced_insights": len(stored_insights),
            "synced_patches": len(stored_patches),
            "decision_log_entry": log_entry,
        })
        trail.log_event(session_id, "workflow_completed", {
            "workflow": "UpdateSimulationKnowledge",
            "status": sync_status,
        })

        return {
            "status": sync_status,
            "report_path": str(report_path),
            "synced_count": synced_count,
        }

    def _format_knowledge_report_md(self, session_id: str, insights: list, patches: list, note: str) -> str:
        """Formats the knowledge base sync report."""
        ins_rows = [f"| `{i['insight_id']}` | {i['title']} | Evidence Count: {len(i['evidence_refs'])} |" for i in insights]
        ins_table = "\n".join(ins_rows) if ins_rows else "| *No insights recorded* | | |"

        pat_rows = [f"| `{p.get('issue_id', p.get('patch_id'))}` | {p.get('reason', p.get('target_type'))} | Stored |" for p in patches]
        pat_table = "\n".join(pat_rows) if pat_rows else "| *No issue patches synchronized* | | |"

        return f"""# Simulation Knowledge Base Synchronization Report

Global knowledge synchronization details for session `{session_id}`.

---

## 1. Executive Summary
Strategic insights and approved declarative corrections have been safely synchronized into the global knowledge store.

---

## 2. Decision Log Entry
> **Decision Note**: {note}

---

## 3. Registered Insights
| Insight ID | Title / Observation | Evidence Refs Status |
| :--- | :--- | :--- |
{ins_table}

---

## 4. Synchronized Known Issues & Rules
| Patch / Issue ID | Core Context / Target | Sync Status |
| :--- | :--- | :--- |
{pat_table}
"""
