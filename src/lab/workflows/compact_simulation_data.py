import json
import logging
from pathlib import Path
from typing import Optional, Any

from src.lab.results import CompactSimulationDataResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.request import WorkflowRequest
from src.lab.store import LabResultStore
from src.lab.schema import LabRunManifest
from src.lab.workflows._path_safety import safe_path_resolution

logger = logging.getLogger(__name__)

class CompactSimulationDataWorkflow:
    """
    M99 Workflow: Converts heavy raw simulation run folders and child reports
    into token-efficient compact summaries, issue indexes, and metric digests
    ready for deep metamorphic balance investigations.
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

    def run(self, session_id: str, request: WorkflowRequest) -> CompactSimulationDataResult:
        logger.info(f"Running CompactSimulationDataWorkflow for session '{session_id}'")

        # 1. Access lab session
        manifest = self.session_store.load_session(session_id)
        # Transition session to REGISTRATION stage as files belong under registration/
        manifest.current_stage = "REGISTRATION"
        self.session_store.save_session(manifest)

        reg_dir = self.session_store.get_stage_dir(session_id, "REGISTRATION")
        reg_dir.mkdir(parents=True, exist_ok=True)

        # 2. Resolve target run directory path
        if request.mode == "specific":
            lab_run_path_str = request.specific_inputs.get("lab_run_path")
            if not lab_run_path_str:
                raise ValueError("lab_run_path must be supplied in specific mode.")
            top_n = request.specific_inputs.get("top_n", 5)
            focus_domains = request.specific_inputs.get("focus_domains", ["resource", "movement", "strategy", "combat", "kernel"])
        else:
            # Generic mode: load from registration/actual_lab_run_path.txt
            run_path_file = reg_dir / "actual_lab_run_path.txt"
            if not run_path_file.is_file():
                err_msg = "No registered lab run path found. Register simulation results first."
                return {"status": "BLOCKED", "reason": err_msg}
            lab_run_path_str = run_path_file.read_text(encoding="utf-8").strip()
            top_n = 5
            focus_domains = ["resource", "movement", "strategy", "combat", "kernel"]

        # Prevent traversal escapes
        resolved_run_path = safe_path_resolution(self.workspace_root, lab_run_path_str)

        # 3. Check and load sweep manifest
        manifest_file = resolved_run_path / "lab_run_manifest.json"
        if not resolved_run_path.is_dir() or not manifest_file.is_file():
            err_msg = f"Target run directory or manifest not found: {lab_run_path_str}"
            return {"status": "BLOCKED", "reason": err_msg}

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                run_manifest_data = json.load(f)
            run_manifest = LabRunManifest(**run_manifest_data)
        except Exception as e:
            return {"status": "BLOCKED", "reason": f"Malformed or unparseable run manifest: {e}"}

        # 4. Scan and load child run summaries
        child_reports = []
        runs_dir = resolved_run_path / "runs"
        if runs_dir.is_dir():
            for child_dir in sorted(runs_dir.iterdir(), key=lambda x: x.name):
                if child_dir.is_dir():
                    report_path = child_dir / "run_report.json"
                    if report_path.is_file():
                        try:
                            with open(report_path, "r", encoding="utf-8") as f:
                                child_reports.append((child_dir.name, json.load(f)))
                        except Exception as e:
                            logger.warning(f"Failed to load run report in {child_dir.name}: {e}")

        if not child_reports:
            return {"status": "BLOCKED", "reason": "No child run reports found to compact."}

        # 5. Process anomaly rollups for issue index and entity hotspots
        all_anomalies = []
        rule_execution_stats = {}  # rule_name -> {status_counts: {status: count}, total_anomalies: int}

        for run_id, report in child_reports:
            # Gather anomalies
            anomalies = report.get("anomalies", [])
            for an in anomalies:
                # Add run reference
                an_copy = dict(an)
                an_copy["run_id"] = run_id
                all_anomalies.append(an_copy)

            # Gather rule execution signals
            for rule in report.get("rule_execution", []):
                rule_id = rule.get("rule_id")
                status = rule.get("status", "UNKNOWN")
                rule_stat = rule_execution_stats.setdefault(rule_id, {"status_counts": {}, "total_anomalies": 0})
                rule_stat["status_counts"][status] = rule_stat["status_counts"].get(status, 0) + 1

        # 6. Group issues (Issue Index)
        grouped_issues = {}
        for an in all_anomalies:
            rule_name = an.get("rule_name", "UnknownRule")
            severity = an.get("severity", "WARNING")
            entity_id = an.get("entity_id")
            tick = an.get("tick_detected", 0)
            msg = an.get("message", "")
            run_id = an.get("run_id")

            issue = grouped_issues.setdefault(rule_name, {
                "rule_name": rule_name,
                "severity": severity,
                "count": 0,
                "tick_range": [tick, tick],
                "affected_entities": set(),
                "affected_runs": set(),
                "evidence_samples": set()
            })

            issue["count"] += 1
            # Maintain highest severity observed
            severity_order = {"CRITICAL": 3, "ERROR": 2, "WARNING": 1, "INFO": 0}
            current_sev_rank = severity_order.get(issue["severity"], 0)
            new_sev_rank = severity_order.get(severity, 0)
            if new_sev_rank > current_sev_rank:
                issue["severity"] = severity

            # Tick range
            issue["tick_range"][0] = min(issue["tick_range"][0], tick)
            issue["tick_range"][1] = max(issue["tick_range"][1], tick)

            if entity_id is not None:
                issue["affected_entities"].add(int(entity_id))
            if run_id:
                issue["affected_runs"].add(run_id)
            if msg:
                issue["evidence_samples"].add(msg)

        # Finalize and sort issues by count descending
        issue_index_list = []
        for name, data in grouped_issues.items():
            issue_index_list.append({
                "rule_name": name,
                "severity": data["severity"],
                "count": data["count"],
                "tick_range": data["tick_range"],
                "affected_entities": sorted(list(data["affected_entities"])),
                "affected_runs": sorted(list(data["affected_runs"])),
                "short_evidence_summaries": sorted(list(data["evidence_samples"]))[:top_n]
            })
        issue_index_list.sort(key=lambda x: x["count"], reverse=True)
        # Apply top_n slice for the final written index
        issue_index_final = issue_index_list[:top_n]

        # 7. Formulate child run summary (Evidence Pack Index)
        evidence_pack_list = []
        for run_id, report in child_reports:
            anomalies = report.get("anomalies", [])
            anomaly_counts = {}
            has_crit = False
            for an in anomalies:
                r_name = an.get("rule_name", "UnknownRule")
                anomaly_counts[r_name] = anomaly_counts.get(r_name, 0) + 1
                if an.get("severity") == "CRITICAL":
                    has_crit = True

            h_score = report.get("health_score", 100.0)
            err_cnt = report.get("errors_count", report.get("error_count", 0))
            crit_cnt = report.get("critical_count", report.get("hard_law_violation_count", 0))

            # Simple COMPLETE vs FAILED status based on error flags
            status_val = "FAILED" if err_cnt > 0 or report.get("metadata", {}).get("status") == "FAILED" else "COMPLETE"

            evidence_pack_list.append({
                "run_id": run_id,
                "status": status_val,
                "health_score": h_score,
                "anomaly_counts": anomaly_counts,
                "total_anomalies": len(anomalies),
                "has_critical_violations": has_crit or crit_cnt > 0,
                "report_file_path": f"runs/{run_id}/run_report.json"
            })

        # 8. Build Metric Digest
        h_scores = [p["health_score"] for p in evidence_pack_list]
        avg_health = sum(h_scores) / len(h_scores) if h_scores else 100.0
        min_health = min(h_scores) if h_scores else 100.0
        max_health = max(h_scores) if h_scores else 100.0

        total_crit = sum(r.get("critical_count", r.get("hard_law_violation_count", 0)) for _, r in child_reports)
        total_warn = sum(r.get("warnings_count", r.get("warning_count", 0)) for _, r in child_reports)
        total_err = sum(r.get("errors_count", r.get("error_count", 0)) for _, r in child_reports)

        max_tick = 0
        for an in all_anomalies:
            max_tick = max(max_tick, an.get("tick_detected", 0))
        for _, r in child_reports:
            # Try to grab final ticks from rules or metadata if present
            max_tick = max(max_tick, r.get("metadata", {}).get("final_tick", 0))

        metric_digest = {
            "avg_health_score": avg_health,
            "min_health_score": min_health,
            "max_health_score": max_health,
            "total_criticals": total_crit,
            "total_warnings": total_warn,
            "total_errors": total_err,
            "tick_max": max_tick
        }

        # 9. Build Entity Hotspot Index
        grouped_entities = {}
        for an in all_anomalies:
            eid = an.get("entity_id")
            if eid is not None:
                eid_int = int(eid)
                rule_name = an.get("rule_name", "UnknownRule")
                run_id = an.get("run_id")

                ent = grouped_entities.setdefault(eid_int, {
                    "entity_id": eid_int,
                    "anomaly_count": 0,
                    "issue_types": set(),
                    "affected_runs": set()
                })
                ent["anomaly_count"] += 1
                ent["issue_types"].add(rule_name)
                ent["affected_runs"].add(run_id)

        entity_hotspots_list = []
        for eid, data in grouped_entities.items():
            entity_hotspots_list.append({
                "entity_id": eid,
                "anomaly_count": data["anomaly_count"],
                "issue_types": sorted(list(data["issue_types"])),
                "affected_runs": sorted(list(data["affected_runs"]))
            })
        entity_hotspots_list.sort(key=lambda x: x["anomaly_count"], reverse=True)
        entity_hotspots_final = entity_hotspots_list[:top_n]

        # 10. Build Signal Coverage Report
        gameplay_domain_rules = {
            "kernel": ["HardLawViolationRule", "HardLawViolationLive", "GovernorDegradedLive", "EventDropRateHigh"],
            "movement": ["NavigationStuckRule", "NavigationStuckLive"],
            "strategy": ["QuestStalledRule"],
            "combat": ["CombatNeverEndsRule"],
            "resource": ["ResourceNodeCrowdingRule"]
        }

        def get_domain_for_rule(rule_name: str) -> str:
            for domain, rules in gameplay_domain_rules.items():
                if rule_name in rules:
                    return domain
            r_lower = rule_name.lower()
            if "hardlaw" in r_lower:
                return "kernel"
            if "navigation" in r_lower or "stuck" in r_lower:
                return "movement"
            if "quest" in r_lower:
                return "strategy"
            if "combat" in r_lower:
                return "combat"
            if "resource" in r_lower or "node" in r_lower:
                return "resource"
            return "kernel"

        signal_coverage_map = {}
        # Initialise standard domains
        standard_domains = ["kernel", "movement", "strategy", "combat", "resource"]
        for dom in standard_domains:
            signal_coverage_map[dom] = {
                "domain": dom,
                "total_anomalies": 0,
                "covered": False,
                "focus_status": "NONE",
                "rules_triggered": set()
            }

        # Fill with actual signals
        for an in all_anomalies:
            r_name = an.get("rule_name", "UnknownRule")
            dom = get_domain_for_rule(r_name)
            cov = signal_coverage_map.setdefault(dom, {
                "domain": dom,
                "total_anomalies": 0,
                "covered": False,
                "focus_status": "NONE",
                "rules_triggered": set()
            })
            cov["total_anomalies"] += 1
            cov["covered"] = True
            cov["rules_triggered"].add(r_name)

        # Check coverage from rule executions even if 0 anomalies were triggered!
        for rule_id, stats in rule_execution_stats.items():
            dom = get_domain_for_rule(rule_id)
            cov = signal_coverage_map.setdefault(dom, {
                "domain": dom,
                "total_anomalies": 0,
                "covered": False,
                "focus_status": "NONE",
                "rules_triggered": set()
            })
            cov["covered"] = True

        # Process focus statuses
        for dom, cov in signal_coverage_map.items():
            cov["rules_triggered"] = sorted(list(cov["rules_triggered"]))
            if dom in focus_domains:
                if cov["total_anomalies"] > 0:
                    cov["focus_status"] = "HIGH_FOCUS"
                else:
                    cov["focus_status"] = "FOCUS"
            else:
                cov["focus_status"] = "NONE"

        signal_coverage_final = sorted(list(signal_coverage_map.values()), key=lambda x: x["domain"])

        # 11. Formulate final Compact Summary
        focused_summary_list = [c for c in signal_coverage_final if c["domain"] in focus_domains]

        compact_summary = {
            "lab_run_id": run_manifest.lab_run_id,
            "session_id": session_id,
            "world_id": run_manifest.world_id,
            "scenario_id": run_manifest.scenario_id,
            "experiment_id": run_manifest.experiment_id,
            "summary_stats": {
                "run_count": len(evidence_pack_list),
                "completed_run_count": sum(1 for p in evidence_pack_list if p["status"] == "COMPLETE"),
                "failed_run_count": sum(1 for p in evidence_pack_list if p["status"] == "FAILED"),
                "total_anomalies": len(all_anomalies),
                "average_health_score": avg_health
            },
            "top_issues": issue_index_final,
            "top_entity_hotspots": entity_hotspots_final,
            "focused_domains_summary": focused_summary_list
        }

        # 12. Write JSON outputs
        with open(reg_dir / "compact_summary.json", "w", encoding="utf-8") as f:
            json.dump(compact_summary, f, indent=2)
        with open(reg_dir / "issue_index.json", "w", encoding="utf-8") as f:
            json.dump(issue_index_final, f, indent=2)
        with open(reg_dir / "evidence_pack_index.json", "w", encoding="utf-8") as f:
            json.dump(evidence_pack_list, f, indent=2)
        with open(reg_dir / "metric_digest.json", "w", encoding="utf-8") as f:
            json.dump(metric_digest, f, indent=2)
        with open(reg_dir / "entity_hotspots.json", "w", encoding="utf-8") as f:
            json.dump(entity_hotspots_final, f, indent=2)
        with open(reg_dir / "signal_coverage.json", "w", encoding="utf-8") as f:
            json.dump(signal_coverage_final, f, indent=2)

        # 13. Render beautifully formatted Markdown Report (compact_summary.md)
        summary_md = self._format_compact_summary_md(session_id, compact_summary, metric_digest, signal_coverage_final)
        (reg_dir / "compact_summary.md").write_text(summary_md, encoding="utf-8")

        return {
            "status": "READY",
            "report_path": str(reg_dir / "compact_summary.md")
        }

    def _format_compact_summary_md(self, session_id: str, summary: dict[str, Any], digest: dict[str, Any], coverage: list[dict[str, Any]]) -> str:
        """Formats premium compact summary overview markdown."""
        stats = summary["summary_stats"]

        # Format issue rows
        issue_rows = []
        for issue in summary["top_issues"]:
            range_str = f"Ticks {issue['tick_range'][0]}-{issue['tick_range'][1]}"
            entities_str = ", ".join(str(e) for e in issue["affected_entities"][:5])
            if len(issue["affected_entities"]) > 5:
                entities_str += "..."
            issue_rows.append(
                f"| `{issue['rule_name']}` | **{issue['severity']}** | {issue['count']} | {range_str} | Entities: {entities_str or 'None'} |"
            )
        issues_table = "\n".join(issue_rows) if issue_rows else "| *No issue anomalies detected* | | | | |"

        # Format hotspot rows
        hotspot_rows = []
        for hot in summary["top_entity_hotspots"]:
            rules_str = ", ".join(hot["issue_types"])
            hotspot_rows.append(
                f"| **Entity {hot['entity_id']}** | {hot['anomaly_count']} | {rules_str} |"
            )
        hotspot_table = "\n".join(hotspot_rows) if hotspot_rows else "| *No entity hotspots recorded* | | |"

        # Format coverage rows
        coverage_rows = []
        for cov in coverage:
            status_tag = "✅ COVERED" if cov["covered"] else "❌ UNCOVERED"
            focus_tag = f"`{cov['focus_status']}`"
            rules_str = ", ".join(cov["rules_triggered"]) or "None"
            coverage_rows.append(
                f"| {cov['domain'].upper()} | {status_tag} | {focus_tag} | {cov['total_anomalies']} | {rules_str} |"
            )
        coverage_table = "\n".join(coverage_rows)

        return f"""# Compact Simulation Sweep Diagnostic Summary

This report delivers a token-efficient, quantitative scorecard of the manual simulation sweep results.

## Staging Registry
- **Lab Session**: `{session_id}`
- **Sweep Run ID**: `{summary["lab_run_id"]}`
- **Average Health Score**: `{stats["average_health_score"]:.2f} / 100.0`

> [!NOTE]
> All raw timelines and massive event logs have been successfully filtered out to ensure a lightweight footprint for downstream reasoning.

---

## Configuration Map
- **World ID**: `{summary["world_id"]}`
- **Scenario ID**: `{summary["scenario_id"]}`
- **Experiment ID**: `{summary["experiment_id"]}`

## Quantitative Digest
- **Sweep Size**: `{stats["run_count"]} runs` (Completed: `{stats["completed_run_count"]}`, Failed: `{stats["failed_run_count"]}`)
- **Total Anomaly Events**: `{stats["total_anomalies"]}`
- **Aggregated Health Distribution**: Min: `{digest["min_health_score"]:.2f}`, Max: `{digest["max_health_score"]:.2f}`
- **Categorized Violations**: Criticals: `{digest["total_criticals"]}`, Errors: `{digest["total_errors"]}`, Warnings: `{digest["total_warnings"]}`
- **Max Timeline Tick**: `{digest["tick_max"]} ticks`

---

## Gameplay Domain Coverage
| Gameplay Domain | Diagnostic Status | Focus Level | Anomalies | Triggered Laws/Rules |
| :--- | :--- | :--- | :--- | :--- |
{coverage_table}

---

## Top Issue Index
| Law / Rule Triggered | Severity | Total Anomalies | Detection Range | Affected Scope Summary |
| :--- | :--- | :--- | :--- | :--- |
{issues_table}

---

## Top Entity Hotspots
| Affected Entity | Trigger Frequency | Triggered Rule Types |
| :--- | :--- | :--- |
{hotspot_table}

---

## Next Steps
To run post-analysis, metamorphic balance reviews, and print diagnostic reports, trigger the Investigation workflow:
```bash
rpg-workflow-investigate --session-id "{session_id}"
```
"""
