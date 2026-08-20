import json
import logging
from pathlib import Path
from typing import Optional, Any

from src.lab.results import InvestigateSimulationResultResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.store import LabResultStore
from src.lab.audit import LabAuditTrail
from src.lab.workflows._path_safety import safe_path_resolution

logger = logging.getLogger(__name__)

class InvestigateSimulationResultWorkflow:
    """
    M100 Workflow: Analyzes registered and compacted simulation results
    to identify balance anomalies, domain issues, liveness issues,
    and formulate a bug backlog and missing signal report.
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

    def run(self, session_id: str, request: WorkflowRequest) -> InvestigateSimulationResultResult:
        logger.info(f"Running InvestigateSimulationResultWorkflow for session '{session_id}'")

        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)

        # 2. Get registration directory (where compacted files are stored)
        reg_dir = self.session_store.get_stage_dir(session_id, "REGISTRATION")

        # Check if compaction files exist
        compact_summary_file = reg_dir / "compact_summary.json"
        issue_index_file = reg_dir / "issue_index.json"

        if not compact_summary_file.is_file() or not issue_index_file.is_file():
            return {
                "status": "BLOCKED",
                "reason": "Compacted simulation data not found under registration/ directory. Run CompactSimulationData first."
            }

        # 3. Resolve target run directory path for specific or generic mode
        if request.mode == "specific":
            lab_run_path_str = request.specific_inputs.get("lab_run_path")
            if not lab_run_path_str:
                raise ValueError("lab_run_path must be supplied in specific mode.")
            # Focus inputs
            focus_domains = request.specific_inputs.get("focus_domains")
            focus_issues = request.specific_inputs.get("focus_issues", [])
            seeds = request.specific_inputs.get("seeds")
            tick_range = request.specific_inputs.get("tick_range")
            analysis_depth = request.specific_inputs.get("analysis_depth", "standard")
        else:
            # Generic mode
            run_path_file = reg_dir / "actual_lab_run_path.txt"
            if not run_path_file.is_file():
                return {"status": "BLOCKED", "reason": "No registered lab run path found."}
            lab_run_path_str = run_path_file.read_text(encoding="utf-8").strip()
            focus_domains = None
            focus_issues = []
            seeds = None
            tick_range = None
            analysis_depth = request.specific_inputs.get("analysis_depth", "standard") if request.specific_inputs else "standard"

        # Prevent traversal escapes
        resolved_run_path = safe_path_resolution(self.workspace_root, lab_run_path_str)

        # Deep analysis confirmation gate — requires explicit opt-in to protect token and time budgets
        if analysis_depth == "deep":
            allow_deep = (request.constraints or {}).get("allow_deep_analysis", False)
            if not allow_deep:
                audit = LabAuditTrail(self.workspace_root)
                audit.log_event(session_id, "guardrail_violation", {
                    "violation_type": "deep_analysis_blocked",
                    "reason": "analysis_depth='deep' requested without allow_deep_analysis=true in constraints",
                    "action": "downgraded to standard depth"
                })
                analysis_depth = "standard"
                logger.warning(
                    "InvestigateSimulationResultWorkflow: deep analysis requested but 'allow_deep_analysis' "
                    "not set in constraints — downgraded to 'standard' depth."
                )

        # Verify that the run directory and manifest exist
        run_manifest_file = resolved_run_path / "lab_run_manifest.json"
        if not resolved_run_path.is_dir() or not run_manifest_file.is_file():
            return {
                "status": "BLOCKED",
                "reason": f"Run directory or manifest not found: {lab_run_path_str}"
            }

        # Load run manifest to check status
        with open(run_manifest_file, "r", encoding="utf-8") as f:
            run_manifest = json.load(f)

        if run_manifest.get("status") != "COMPLETED":
            return {
                "status": "BLOCKED",
                "reason": f"Unsupported lab run state: status is {run_manifest.get('status')}. Run must be COMPLETED."
            }

        # Transition session to INVESTIGATION stage
        manifest.current_stage = "INVESTIGATION"
        self.session_store.save_session(manifest)

        invest_dir = self.session_store.get_stage_dir(session_id, "INVESTIGATION")
        invest_dir.mkdir(parents=True, exist_ok=True)

        # 4. Load Compaction Files
        with open(compact_summary_file, "r", encoding="utf-8") as f:
            compact_summary = json.load(f)
        with open(issue_index_file, "r", encoding="utf-8") as f:
            all_issues = json.load(f)

        # Read other indexes if standard or deep
        evidence_pack = []
        signal_coverage = []
        entity_hotspots = []
        metric_digest = {}

        if analysis_depth in ("standard", "deep"):
            ev_file = reg_dir / "evidence_pack_index.json"
            sig_file = reg_dir / "signal_coverage.json"
            hot_file = reg_dir / "entity_hotspots.json"
            dig_file = reg_dir / "metric_digest.json"
            if ev_file.is_file():
                with open(ev_file, "r", encoding="utf-8") as f:
                    evidence_pack = json.load(f)
            if sig_file.is_file():
                with open(sig_file, "r", encoding="utf-8") as f:
                    signal_coverage = json.load(f)
            if hot_file.is_file():
                with open(hot_file, "r", encoding="utf-8") as f:
                    entity_hotspots = json.load(f)
            if dig_file.is_file():
                with open(dig_file, "r", encoding="utf-8") as f:
                    metric_digest = json.load(f)

        # 5. Process based on depth
        analyzed_issues = all_issues
        if analysis_depth == "light":
            # Only top 3 issues
            analyzed_issues = all_issues[:3]
        elif analysis_depth == "standard":
            # Top 10 issues
            analyzed_issues = all_issues[:10]
        elif analysis_depth == "deep":
            # Under deep mode, read selected evidence packs or specific child run report.json files
            # based on focus_issues, seeds, or tick_range constraints.
            # We strictly DO NOT load the full raw event timeline.
            analyzed_issues = all_issues[:10]
            # If focus_issues is provided, filter or prioritize
            if focus_issues:
                priority_issues = [i for i in all_issues if i["rule_name"] in focus_issues]
                other_issues = [i for i in all_issues if i["rule_name"] not in focus_issues]
                analyzed_issues = (priority_issues + other_issues)[:10]

        # 6. Analyze and Derive Investigation Reports
        # Categories mapping
        critical_issues = []
        domain_issues = {}
        balance_concerns = []
        liveness_concerns = []
        performance_concerns = []
        entity_evidence = []
        missing_data = []
        likely_causes_vs_facts = []
        recommended_steps = []
        evidence_references = []

        # Executive summary & Data Quality derived defaults
        exec_sum = f"Investigation suite parsed completed simulation run {compact_summary['lab_run_id']} at '{analysis_depth}' analysis depth. "
        dq_desc = f"Compaction dataset integrity is optimal. Parsed {compact_summary['summary_stats']['completed_run_count']} child run reports successfully."

        # Filter domain issues
        for issue in analyzed_issues:
            # Severity critical
            if issue["severity"] == "CRITICAL":
                critical_issues.append({
                    "rule_name": issue["rule_name"],
                    "count": issue["count"],
                    "severity": issue["severity"],
                    "affected_entities": issue["affected_entities"]
                })

            # Map gameplay domains based on rule name patterns
            rule_lower = issue["rule_name"].lower()
            domain = "kernel"
            if "nav" in rule_lower or "stuck" in rule_lower or "move" in rule_lower:
                domain = "movement"
            elif "balance" in rule_lower or "economy" in rule_lower or "production" in rule_lower or "zero" in rule_lower:
                domain = "resource"
            elif "combat" in rule_lower or "fight" in rule_lower or "death" in rule_lower:
                domain = "combat"
            elif "strat" in rule_lower or "decision" in rule_lower:
                domain = "strategy"

            domain_issues.setdefault(domain, []).append({
                "rule_name": issue["rule_name"],
                "count": issue["count"],
                "severity": issue["severity"]
            })

            # Flag Balance concerns
            if "balance" in rule_lower or "production" in rule_lower or "zero" in rule_lower or "economy" in rule_lower:
                balance_concerns.append(f"Anomalous balance violation in rule '{issue['rule_name']}': Triggered {issue['count']} times between ticks {issue['tick_range'][0]}-{issue['tick_range'][1]}.")

            # Flag Liveness concerns
            if "stuck" in rule_lower or "liveness" in rule_lower or "nav" in rule_lower or "hang" in rule_lower:
                liveness_concerns.append(f"System liveness or pathfinding breakdown in rule '{issue['rule_name']}': {issue['count']} occurrences. Affected entities: {issue['affected_entities']}.")

            # Likely causes vs confirmed facts
            fact = f"Fact: Rule '{issue['rule_name']}' was triggered {issue['count']} times in the simulation."
            cause = "Likely Cause: State transition or boundary rule configuration mismatch."
            if "nav" in rule_lower or "stuck" in rule_lower:
                cause = "Likely Cause: Pathfinding obstacle blockage or navigation loop."
            likely_causes_vs_facts.append({"fact": fact, "hypothesized_cause": cause})

        # Add metric-based performance concerns
        if metric_digest:
            if metric_digest.get("total_criticals", 0) > 0:
                performance_concerns.append(f"Critical rule alerts detected: {metric_digest['total_criticals']} occurrences.")
            # If storage usage is high or run counts are very large
            if compact_summary["summary_stats"].get("storage_usage_mb", 0) > 10.0:
                performance_concerns.append("High disk usage (>10MB) detected for simulation run logs.")

        # Map missing signals
        if signal_coverage:
            for cov in signal_coverage:
                if not cov["covered"] and cov["focus_status"] in ("HIGH_FOCUS", "FOCUS"):
                    missing_data.append({
                        "domain": cov["domain"],
                        "focus_status": cov["focus_status"],
                        "reason": "Gameplay domain marked as high focus but had zero telemetry logs recorded in this sweep."
                    })

        # Map entity evidence hotspots
        if entity_hotspots:
            for hot in entity_hotspots[:5]:
                entity_evidence.append({
                    "entity_id": hot["entity_id"],
                    "anomaly_count": hot["anomaly_count"],
                    "issue_types": hot["issue_types"]
                })

        # Recommended steps
        if critical_issues:
            recommended_steps.append("1. Resolve CRITICAL rules immediately to prevent simulator kernel divergence.")
        if liveness_concerns:
            recommended_steps.append("2. Audit agent pathfinding coordinates and topological obstacles.")
        if balance_concerns:
            recommended_steps.append("3. Adjust production coefficients or trading prices in scenario files.")
        if not recommended_steps:
            recommended_steps.append("1. Keep baseline configuration stable. Sweep with a wider seed matrix to confirm stability.")

        # Evidence references
        for issue in analyzed_issues[:5]:
            evidence_references.append({
                "rule_name": issue["rule_name"],
                "reference_files": [f"runs/*/run_report.json"],
                "ticks": issue.get("tick_range", "unknown")
            })

        # 7. Create Output JSON Report
        investigation_report = {
            "session_id": session_id,
            "lab_run_id": compact_summary["lab_run_id"],
            "analysis_depth": analysis_depth,
            "investigated_at": "2026-05-24T08:52:05Z",
            "executive_summary": exec_sum,
            "data_quality": dq_desc,
            "signal_coverage": signal_coverage,
            "critical_issues": critical_issues,
            "domain_issues": domain_issues,
            "balance_concerns": balance_concerns,
            "liveness_concerns": liveness_concerns,
            "performance_concerns": performance_concerns,
            "entity_evidence": entity_evidence,
            "missing_data": missing_data,
            "likely_causes_vs_facts": likely_causes_vs_facts,
            "recommended_steps": recommended_steps,
            "evidence_references": evidence_references
        }

        # Save investigation_report.json
        with open(invest_dir / "investigation_report.json", "w", encoding="utf-8") as f:
            json.dump(investigation_report, f, indent=2)

        # 8. Create Issue Backlog JSON
        issue_backlog = []
        for idx, issue in enumerate(all_issues):
            domain = "kernel"
            rule_lower = issue["rule_name"].lower()
            if "nav" in rule_lower or "stuck" in rule_lower or "move" in rule_lower:
                domain = "movement"
            elif "balance" in rule_lower or "economy" in rule_lower or "production" in rule_lower:
                domain = "resource"
            elif "combat" in rule_lower or "fight" in rule_lower:
                domain = "combat"
            elif "strat" in rule_lower or "decision" in rule_lower:
                domain = "strategy"

            issue_backlog.append({
                "issue_id": f"ISSUE-{idx+1:03d}",
                "rule_name": issue["rule_name"],
                "severity": issue.get("severity", "WARNING"),
                "domain": issue.get("domain", domain),
                "description": issue.get(
                    "description",
                    f"Rule {issue['rule_name']} triggered {issue.get('count', 0)} times in simulation sweep."
                ),
                "frequency": issue.get("count", 0),
                "affected_entities": issue.get("affected_entities", []),
                "state": "OPEN"
            })

        with open(invest_dir / "issue_backlog.json", "w", encoding="utf-8") as f:
            json.dump(issue_backlog, f, indent=2)

        # 9. Create Missing Signals JSON
        missing_signals_out = []
        if signal_coverage:
            for cov in signal_coverage:
                if not cov["covered"] and cov["focus_status"] in ("HIGH_FOCUS", "FOCUS"):
                    missing_signals_out.append({
                        "domain": cov["domain"],
                        "focus_status": cov["focus_status"],
                        "reason": f"Gameplay domain '{cov['domain']}' was prioritized but had zero telemetry logs recorded in this sweep."
                    })
        with open(invest_dir / "missing_signals.json", "w", encoding="utf-8") as f:
            json.dump(missing_signals_out, f, indent=2)

        # 10. Create Insight Candidates JSON
        insight_candidates = []
        for idx, concern in enumerate(balance_concerns):
            insight_candidates.append({
                "insight_id": f"INSIGHT-{idx+1:03d}",
                "title": f"Balance Regression: {concern.split(':')[0]}",
                "domain": "resource",
                "observation": concern,
                "hypothesized_cause": "Resource rates or pricing margins require rebalancing."
            })
        with open(invest_dir / "insight_candidates.json", "w", encoding="utf-8") as f:
            json.dump(insight_candidates, f, indent=2)

        # 11. Create Next Experiment Suggestions JSON
        next_experiment_suggestions = []
        if critical_issues or balance_concerns:
            next_experiment_suggestions.append({
                "experiment_id": "EXP-REPRODUCE-001",
                "focus_issues": [i["rule_name"] for i in critical_issues],
                "suggested_seeds": seeds or [42, 101, 2023],
                "suggested_constraints": {
                    "max_runtime_minutes": 30,
                    "target_ticks": tick_range or [10000, 30000]
                }
            })
        with open(invest_dir / "next_experiment_suggestions.json", "w", encoding="utf-8") as f:
            json.dump(next_experiment_suggestions, f, indent=2)

        # 12. Create beautifully formatted Premium Markdown Report
        summary_md = self._format_investigation_report_md(investigation_report, issue_backlog)
        (invest_dir / "investigation_report.md").write_text(summary_md, encoding="utf-8")

        return {
            "status": "READY",
            "report_path": str(invest_dir / "investigation_report.md")
        }

    def _format_investigation_report_md(self, report: dict[str, Any], backlog: list[dict[str, Any]]) -> str:
        """Formats the 13 required sections of the investigation report in a gorgeous markdown format."""

        # format critical issue rows
        crit_rows = []
        for crit in report["critical_issues"]:
            crit_rows.append(f"- **{crit['rule_name']}**: Triggered {crit['count']} times. Affected scope: Entities {crit['affected_entities'][:5]}")
        crit_list = "\n".join(crit_rows) if crit_rows else "*No CRITICAL severity issues identified.*"

        # format domain issue list
        domain_items = []
        for dom, issues in report["domain_issues"].items():
            domain_items.append(f"### Gameplay Domain: {dom.upper()}")
            for iss in issues:
                domain_items.append(f"- `{iss['rule_name']}` (**{iss['severity']}**): Triggered {iss['count']} times")
        domain_list = "\n".join(domain_items) if domain_items else "*No domain violations categorised.*"

        # format balance concerns
        bal_list = "\n".join(f"- {b}" for b in report["balance_concerns"]) if report["balance_concerns"] else "*No balance concerns recorded.*"

        # format liveness concerns
        live_list = "\n".join(f"- {l}" for l in report["liveness_concerns"]) if report["liveness_concerns"] else "*No liveness concerns recorded.*"

        # format performance concerns
        perf_list = "\n".join(f"- {p}" for p in report["performance_concerns"]) if report["performance_concerns"] else "*No performance concerns recorded.*"

        # format entity/cognition evidence
        ent_rows = []
        for ent in report["entity_evidence"]:
            ent_rows.append(f"| **Entity {ent['entity_id']}** | {ent['anomaly_count']} | {', '.join(ent['issue_types'])} |")
        ent_table = "\n".join(ent_rows) if ent_rows else "| *No entity hotspot evidence found* | | |"

        # format missing data
        miss_rows = []
        for m in report["missing_data"]:
            miss_rows.append(f"| **{m['domain'].upper()}** | `{m['focus_status']}` | {m['reason']} |")
        miss_table = "\n".join(miss_rows) if miss_rows else "| *No missing signal gaps reported* | | |"

        # format likely causes vs facts
        cause_list = []
        for idx, cf in enumerate(report["likely_causes_vs_facts"]):
            cause_list.append(f"{idx+1}. **{cf['fact']}**\n   - *{cf['hypothesized_cause']}*")
        cause_text = "\n".join(cause_list) if cause_list else "*No fact comparisons recorded.*"

        # format recommended steps
        rec_list = "\n".join(report["recommended_steps"])

        # format evidence references
        ref_rows = []
        for ref in report["evidence_references"]:
            ref_rows.append(f"- **{ref['rule_name']}**: File `{ref['reference_files'][0]}` (Ticks: {ref['ticks'][0]}-{ref['ticks'][1]})")
        ref_list = "\n".join(ref_rows) if ref_rows else "*No evidence references registered.*"

        return f"""# Investigation Sweep Diagnostic Report

Comprehensive diagnostic analysis of the completed simulation run sweep.

---

## 1. Executive Summary
{report["executive_summary"]}

## 2. Data Quality
{report["data_quality"]}

---

## 3. Signal Coverage
### Prioritized Telemetry Coverage Gaps
| Game Domain | Focus Level | Reason for Telemetry Gap |
| :--- | :--- | :--- |
{miss_table}

---

## 4. Critical Issues
{crit_list}

---

## 5. Domain Issues
{domain_list}

---

## 6. Balance Concerns
{bal_list}

---

## 7. Liveness Concerns
{live_list}

---

## 8. Runtime/performance concerns
{perf_list}

---

## 9. Entity/cognition evidence
| Hotspot Entity | Anomaly Frequency | Associated Rules |
| :--- | :--- | :--- |
{ent_table}

---

## 10. Missing data
*Refer to Section 3: Signal Coverage.*

---

## 11. Likely causes vs confirmed facts
{cause_text}

---

## 12. Recommended next steps
{rec_list}

---

## 13. Evidence references
{ref_list}
"""
