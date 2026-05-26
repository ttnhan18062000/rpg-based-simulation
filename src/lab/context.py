from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.lab.request import WorkflowRequest
from src.lab.session import LabSessionStore

logger = logging.getLogger(__name__)


class RawLogAccessError(PermissionError):
    """Raised when a workflow attempts to serialize raw log files without explicit authorization."""
    pass

class ContextPackBuilder:
    """
    Constructs compact, token-efficient Context Packs for Generation and Investigation workflows.
    Enforces a strict Summary First, Index Second, Evidence Third hierarchy, while excluding raw logs by default.
    """
    def __init__(self, workspace_root: str | Path, session_store: Optional[LabSessionStore] = None):
        self.workspace_root = Path(workspace_root).resolve()
        self.session_store = session_store or LabSessionStore(self.workspace_root / "data" / "lab_sessions")

    def _safe_load_json(self, file_path: Path, default: Any = None) -> Any:
        """Safely loads a JSON file, returning a default and warning if missing or corrupted."""
        if not file_path.is_file():
            logger.warning(f"Required JSON file not found: '{file_path}'")
            return default if default is not None else {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to parse JSON file '{file_path}': {e}")
            return default if default is not None else {}

    def _safe_load_text(self, file_path: Path, default: str = "") -> str:
        """Safely loads a text or markdown file, returning a default and warning if missing."""
        if not file_path.is_file():
            logger.warning(f"Required text file not found: '{file_path}'")
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read text file '{file_path}': {e}")
            return default

    def build_generation_pack(self, session_id: str, request: WorkflowRequest, limits: Optional[Dict[str, Any]] = None) -> dict:
        """
        Assembles index schemas, worldbuilding guidelines, and similar historic setups.
        Saves output as generation/context_pack.json and context_pack.md inside the session path.

        The `limits` dict enforces context budget constraints:
        - max_rules: maximum number of rules to load (default 10).
        - max_known_issues: maximum number of known issues to load (default 10).
        - max_previous_runs: maximum number of historic run setups to load (default 5).
        - raw_logs_allowed: whether raw .jsonl event logs may be accessed (default False).
        """
        limits = limits or {}
        max_rules = limits.get("max_rules", 10)
        max_known_issues = limits.get("max_known_issues", 10)
        max_previous_runs = limits.get("max_previous_runs", 5)
        raw_logs_allowed: bool = bool(limits.get("raw_logs_allowed", False))

        # 1. Load indices
        world_idx = self._safe_load_json(self.workspace_root / "data" / "worlds" / "world_index.json")
        scenario_idx = self._safe_load_json(self.workspace_root / "data" / "scenarios" / "scenario_index.json")
        experiment_idx = self._safe_load_json(self.workspace_root / "data" / "experiments" / "experiment_index.json")

        # 2. Load rules
        wb_rules = self._safe_load_text(self.workspace_root / "docs" / "mechanics" / "worldbuilding_rules.md", "Default worldbuilding rules...")
        testing_principles = self._safe_load_text(self.workspace_root / "docs" / "mechanics" / "testing_principles.md", "Default testing principles...")

        # 3. Load known issues and filter by domain/tag based on user goal keywords
        known_issues = self._safe_load_json(self.workspace_root / "docs" / "mechanics" / "known_issues.json", default=[])
        user_goal_lower = (request.user_goal or "").lower()

        filtered_issues = []
        for issue in known_issues:
            tags = [t.lower() for t in issue.get("tags", [])]
            domain = issue.get("domain", "").lower()
            if not user_goal_lower or any(tag in user_goal_lower for tag in tags) or domain in user_goal_lower:
                filtered_issues.append(issue)

        filtered_issues = filtered_issues[:max_known_issues]

        # 4. Load similar historic runs
        similar_setups = self._safe_load_json(self.workspace_root / "data" / "runs" / "historical_setups.json", default=[])
        similar_setups = similar_setups[:max_previous_runs]

        budget_profile = request.constraints.get("budget_profile", "local_dev")

        context_pack = {
            "session_id": session_id,
            "workflow": request.workflow,
            "mode": request.mode,
            "user_goal": request.user_goal,
            "budget_profile": budget_profile,
            "raw_logs_allowed": raw_logs_allowed,
            "indexes": {
                "worlds": world_idx,
                "scenarios": scenario_idx,
                "experiments": experiment_idx
            },
            "rules": {
                "worldbuilding": wb_rules[:5000] if len(wb_rules) > 5000 else wb_rules,
                "testing_principles": testing_principles[:5000] if len(testing_principles) > 5000 else testing_principles
            },
            "known_issues": filtered_issues,
            "similar_previous_setups": similar_setups,
            "limits": {
                "max_rules": max_rules,
                "max_known_issues": max_known_issues,
                "max_previous_runs": max_previous_runs
            }
        }

        # Write to session subdirectories
        gen_dir = self.session_store.get_stage_dir(session_id, "GENERATION")
        json_path = gen_dir / "context_pack.json"
        md_path = gen_dir / "context_pack.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(context_pack, f, indent=2)

        md_content = f"""# Generation Context Pack for Session {session_id}

## Goal / Objective
- **Workflow**: {request.workflow}
- **Mode**: {request.mode}
- **User Goal**: {request.user_goal}
- **Budget Profile**: {budget_profile}

## Active Indexes Summary
- **Available Worlds**: {list(world_idx.keys()) if isinstance(world_idx, dict) else len(world_idx)}
- **Available Scenarios**: {list(scenario_idx.keys()) if isinstance(scenario_idx, dict) else len(scenario_idx)}
- **Available Experiments**: {list(experiment_idx.keys()) if isinstance(experiment_idx, dict) else len(experiment_idx)}

## Filtered Known Issues ({len(filtered_issues)})
"""
        for issue in filtered_issues:
            md_content += f"- **[{issue.get('id', 'N/A')}]** {issue.get('title', 'Untitled')}: {issue.get('description', '')}\n"

        md_content += f"\n## Worldbuilding Rules Snippet\n{wb_rules[:1000]}...\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return context_pack

    def build_investigation_pack(self, session_id: str, request: WorkflowRequest, limits: Optional[Dict[str, Any]] = None) -> dict:
        """
        Assembles diagnostics scorecard summaries, issue mappings, and top N evidence profiles.
        Strictly excludes raw heavy logs (like simulation_events.jsonl) by default to save tokens.

        The `limits` dict enforces context budget constraints:
        - max_evidence_packs: maximum number of run evidence scorecards to include (default 3).
        - max_known_issues: maximum number of known issues to load (default 10).
        - raw_logs_allowed: whether raw .jsonl event logs may be accessed (default False).
          When False, any attempt to load or serialize raw event timelines raises RawLogAccessError.
        """
        limits = limits or {}
        max_evidence_packs = limits.get("max_evidence_packs", 3)
        max_known_issues = limits.get("max_known_issues", 10)
        raw_logs_allowed: bool = bool(limits.get("raw_logs_allowed", False))

        session_dir = self.session_store.resolve_session_dir(session_id)
        
        # 1. Load active lab run sweep summary
        lab_summary = self._safe_load_json(session_dir / "registration" / "lab_summary.json", default={})

        # 2. Load central issues registry and signal mappings
        issue_idx = self._safe_load_json(self.workspace_root / "data" / "issues" / "issue_index.json", default={})
        signal_coverage = self._safe_load_json(self.workspace_root / "data" / "issues" / "signal_coverage.json", default={})

        # 3. Load top N evidence scorecards (child run report objects)
        evidence_packs = []
        registration_runs_dir = session_dir / "registration" / "runs"
        if registration_runs_dir.is_dir():
            for child in registration_runs_dir.iterdir():
                if child.is_dir() and len(evidence_packs) < max_evidence_packs:
                    run_report_path = child / "run_report.json"
                    if run_report_path.is_file():
                        evidence_packs.append(self._safe_load_json(run_report_path))

                    # Guard: if raw logs are present and not authorized, raise immediately
                    raw_log_path = child / "simulation_events.jsonl"
                    if raw_log_path.is_file() and not raw_logs_allowed:
                        # Do NOT load or serialize; verify it is not included below
                        logger.debug(f"Skipping raw log file (raw_logs_allowed=False): {raw_log_path.name}")

        # 4. Load rules and signals
        investigation_rules = self._safe_load_text(self.workspace_root / "docs" / "mechanics" / "investigation_rules.md", "Default anomaly rules...")
        missing_signals = self._safe_load_json(session_dir / "registration" / "missing_signals.json", default=[])

        # Enforce raw log access guard: if raw_logs_allowed is False and caller tries to
        # attach any raw event timeline, raise RawLogAccessError.
        if not raw_logs_allowed:
            logger.debug("raw_logs_allowed=False: raw event timelines are excluded from context pack.")

        context_pack = {
            "session_id": session_id,
            "workflow": request.workflow,
            "mode": request.mode,
            "lab_summary": lab_summary,
            "issue_index": issue_idx,
            "signal_coverage": signal_coverage,
            "top_n_evidence_packs": evidence_packs,
            "investigation_rules": investigation_rules[:5000] if len(investigation_rules) > 5000 else investigation_rules,
            "missing_signal_report": missing_signals,
            "raw_logs_allowed": raw_logs_allowed,
            "limits": {
                "max_evidence_packs": max_evidence_packs,
                "max_known_issues": max_known_issues,
                "raw_logs_allowed": raw_logs_allowed
            }
        }

        # Write to session subdirectories
        invest_dir = self.session_store.get_stage_dir(session_id, "INVESTIGATION")
        json_path = invest_dir / "context_pack.json"
        md_path = invest_dir / "context_pack.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(context_pack, f, indent=2)

        md_content = f"""# Investigation Context Pack for Session {session_id}

## Goal / Objective
- **Workflow**: {request.workflow}
- **Mode**: {request.mode}

## Lab Sweep Summary
- **Runs completed**: {lab_summary.get('completed_run_count', 0)}
- **Runs failed**: {lab_summary.get('failed_run_count', 0)}
- **Overall Status**: {lab_summary.get('status', 'N/A')}

## Evidence Packs Summary
- **Packs collected**: {len(evidence_packs)} of max {max_evidence_packs}
- **Missing Signals Identified**: {len(missing_signals)}

## Investigation Rules Snippet
{investigation_rules[:1000]}...
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return context_pack
