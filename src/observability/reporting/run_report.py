from __future__ import annotations
import os
import json
import logging
import time
from typing import Any, Dict, List, Optional
from src.core.lifecycle import ShutdownResult
from src.observability.entity_timeline import EntityTimelineStore
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.observability.anomaly.rules_engine import RuleResult
    from src.observability.anomaly.triage import AnomalyCluster

logger = logging.getLogger(__name__)

class RunReportGenerator:
    """Aggregates diagnostics, computes deterministic health scores, and generates simulation run reports."""
    @staticmethod
    def generate(
        run_dir: str,
        shutdown_result: Optional[Any] = None,
        timeline_store: Optional[EntityTimelineStore] = None,
        rule_results: Optional[List[RuleResult]] = None,
        clusters: Optional[List[AnomalyCluster]] = None,
        anomalies: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrates post-run report generation, saving run_report.md and run_report.json."""
        # Ensure run directory exists
        os.makedirs(run_dir, exist_ok=True)

        # 1. Load or extract anomalies
        combined_anomalies: List[Dict[str, Any]] = []

        if anomalies is not None:
            for a in anomalies:
                if isinstance(a, dict):
                    combined_anomalies.append(a)
                else:
                    combined_anomalies.append({
                        "rule_name": getattr(a, "rule_name", ""),
                        "severity": getattr(a, "severity", "WARNING"),
                        "tick_detected": getattr(a, "tick_detected", 0),
                        "message": getattr(a, "message", ""),
                        "entity_id": getattr(a, "entity_id", None),
                        "context": getattr(a, "context", {})
                    })

        if rule_results is not None:
            for r in rule_results:
                if r.anomalies:
                    for a in r.anomalies:
                        norm_msg = a.message.lower().replace("hard law violation detected:", "").replace("invariant violation logged:", "").strip()
                        exists = any(
                            existing.get("tick_detected") == a.tick_start and
                            existing.get("entity_id") == (a.affected_entity_ids[0] if a.affected_entity_ids else None) and
                            existing.get("message", "").lower().replace("hard law violation detected:", "").replace("invariant violation logged:", "").strip() == norm_msg
                            for existing in combined_anomalies
                        )
                        if not exists:
                            combined_anomalies.append({
                                "rule_name": r.rule_id,
                                "severity": a.severity,
                                "tick_detected": a.tick_start,
                                "message": a.message,
                                "entity_id": a.affected_entity_ids[0] if a.affected_entity_ids else None,
                                "context": a.evidence
                            })

        if not combined_anomalies and rule_results is None:
            anomalies_path = os.path.join(run_dir, "anomalies.json")
            if os.path.exists(anomalies_path):
                try:
                    with open(anomalies_path, "r", encoding="utf-8") as f:
                        combined_anomalies = json.load(f)
                except Exception as e:
                    logger.error(f"Failed loading anomalies.json: {e}")

        anomalies = combined_anomalies

        # 2. Compute Health Score
        health_score = 100.0
        hard_law_violations_count = 0
        errors_count = 0
        warnings_count = 0

        for a in anomalies:
            severity = a.get("severity", "WARNING")
            rule_name = a.get("rule_name", "")
            if severity == "CRITICAL" or rule_name == "HardLawViolationRule" or rule_name == "HardLawViolationDetected":
                health_score -= 40.0
                hard_law_violations_count += 1
            elif severity == "ERROR":
                health_score -= 15.0
                errors_count += 1
            else:
                health_score -= 5.0
                warnings_count += 1

        health_score = max(0.0, health_score)

        # 3. Compile Metadata
        final_tick = shutdown_result.final_tick if shutdown_result else -1
        final_hash = shutdown_result.final_hash if shutdown_result else "UNKNOWN"
        overall_outcome = str(shutdown_result.overall_outcome) if shutdown_result else "UNKNOWN"

        metadata = {
            "run_id": os.path.basename(run_dir),
            "generated_at": time.time(),
            "final_tick": final_tick,
            "final_hash": final_hash,
            "overall_outcome": overall_outcome,
            "health_score": health_score,
            "hard_law_violations_count": hard_law_violations_count,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "total_anomalies_count": len(anomalies)
        }

        # 4. Fetch Flagged Entity Timelines
        flagged_entity_ids = list(set([
            a.get("entity_id") for a in anomalies if a.get("entity_id") is not None
        ]))
        
        flagged_timelines = {}
        if timeline_store:
            # Load from in-memory external timeline store
            flagged_timelines = timeline_store.get_flagged_timelines(flagged_entity_ids)
        else:
            # Reconstruct from JSONL event log if timeline store is not available
            events_path = os.path.join(run_dir, "simulation_events.jsonl")
            if os.path.exists(events_path):
                try:
                    with open(events_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                ev_data = json.loads(line)
                                eid = ev_data.get("entity_id")
                                if eid in flagged_entity_ids:
                                    flagged_timelines.setdefault(eid, []).append(ev_data)
                except Exception as e:
                    logger.error(f"Failed reconstructing timelines from JSONL: {e}")

        # Keep only the last 15 events for each entity timeline in the report to prevent bloat
        for eid in flagged_timelines:
            flagged_timelines[eid] = flagged_timelines[eid][-15:]

        # Serialize rule results and clusters if present
        serialized_rule_results = []
        if rule_results:
            for r in rule_results:
                serialized_rule_results.append({
                    "rule_id": r.rule_id,
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "anomalies_count": len(r.anomalies) if r.anomalies else 0
                })

        serialized_clusters = []
        if clusters:
            for c in clusters:
                serialized_clusters.append({
                    "cluster_id": c.cluster_id,
                    "rule_id": c.rule_id,
                    "severity": c.severity,
                    "region_id": c.region_id,
                    "resource_id": c.resource_id,
                    "quest_id": c.quest_id,
                    "affected_entity_ids": c.affected_entity_ids,
                    "tick_start": c.tick_start,
                    "tick_end": c.tick_end,
                    "evidence_samples": c.evidence_samples,
                    "suggested_causes": c.suggested_causes,
                    "anomalies_count": len(c.anomalies)
                })

        report_data = {
            "metadata": metadata,
            "anomalies": anomalies,
            "flagged_timelines": flagged_timelines,
            "rule_execution": serialized_rule_results,
            "anomaly_clusters": serialized_clusters
        }

        # Save run_report.json
        json_report_path = os.path.join(run_dir, "run_report.json")
        try:
            with open(json_report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Saved run_report.json to {json_report_path}")
        except Exception as e:
            logger.error(f"Failed to save run_report.json: {e}")

        # Save run_report.md
        md_report_path = os.path.join(run_dir, "run_report.md")
        try:
            RunReportGenerator.write_markdown_report(md_report_path, report_data)
            logger.info(f"Saved run_report.md to {md_report_path}")
        except Exception as e:
            logger.error(f"Failed to save run_report.md: {e}")

        return report_data

    @staticmethod
    def write_markdown_report(filepath: str, data: Dict[str, Any]) -> None:
        """Writes a beautifully styled Markdown report for executive review and continuous integration."""
        meta = data["metadata"]
        anomalies = data["anomalies"]
        timelines = data["flagged_timelines"]
        rules = data.get("rule_execution", [])
        clusters = data.get("anomaly_clusters", [])

        # Health score badge selection
        score = meta["health_score"]
        if score >= 90:
            badge = "🟢 **HEALTHY**"
            alert = "> [!NOTE]\n> **Simulation run is highly healthy.** Excellent stability and agent behaviors."
        elif score >= 60:
            badge = "🟡 **DEGRADED**"
            alert = "> [!WARNING]\n> **Simulation run degraded.** System behavior is stable, but multiple anomalies require review."
        else:
            badge = "🔴 **CRITICAL CRASH / MALFUNCTION**"
            alert = "> [!CAUTION]\n> **Critical failure or severe regression.** Hard law violations or massive anomaly rates detected."

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Simulation Run Observatory Report — {meta['run_id']}\n\n")
            f.write(f"{alert}\n\n")
            
            f.write("## Executive Scorecard\n\n")
            f.write(f"- **Deterministic Health Score**: `{score}/100` ({badge})\n")
            f.write(f"- **Final Simulation Tick**: `{meta['final_tick']}`\n")
            f.write(f"- **Authoritative State Hash**: `{meta['final_hash']}`\n")
            f.write(f"- **Lifecycle Outcome**: `{meta['overall_outcome']}`\n\n")

            f.write("## Triage Metrics Dashboard\n\n")
            f.write("| Telemetry Signal | Count | Status |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| 🟥 Hard Law Violations | {meta['hard_law_violations_count']} | {'🔴 ACTION REQUIRED' if meta['hard_law_violations_count'] > 0 else '🟢 PASS'} |\n")
            f.write(f"| 🟧 Behavioral Errors | {meta['errors_count']} | {'🔴 REFACTOR NEEDED' if meta['errors_count'] > 0 else '🟢 PASS'} |\n")
            f.write(f"| 🟨 Diagnostic Warnings | {meta['warnings_count']} | {'🟡 MONITORING' if meta['warnings_count'] > 0 else '🟢 PASS'} |\n\n")

            # Rule Execution Table
            if rules:
                f.write("## 📋 Rule Engine Execution Summary\n\n")
                f.write("| Rule ID | Status | Anomalies Triggered |\n")
                f.write("| :--- | :--- | :--- |\n")
                for r in rules:
                    status_str = r["status"]
                    if status_str == "PASSED":
                        status_badge = "🟢 PASSED"
                    elif status_str == "FAILED":
                        status_badge = "🔴 FAILED"
                    elif status_str == "SKIPPED_MISSING_SIGNAL":
                        status_badge = "⚪ SKIPPED (MISSING SIGNAL)"
                    elif status_str == "SKIPPED_SCENARIO_TYPE":
                        status_badge = "⚪ SKIPPED (SCENARIO TYPE)"
                    else:
                        status_badge = f"⚪ SKIPPED ({status_str})"
                    f.write(f"| `{r['rule_id']}` | {status_badge} | `{r['anomalies_count']}` |\n")
                f.write("\n")

            f.write("## 🔍 Actionable Triage & Investigation Guide\n\n")
            if not anomalies:
                f.write("🟢 **Triage Clear**: No action needed. System meets all stability and behavioral criteria.\n\n")
            else:
                f.write("### Recommended Actions:\n")
                if meta['hard_law_violations_count'] > 0:
                    f.write("1. 🟥 **Fix Hard Law Violations**: Critical invariants were breached. Check the isolation scope of the respective systems immediately.\n")
                if meta['errors_count'] > 0:
                    f.write("2. 🟧 **Fix Navigation or Combat Stall Loops**: Agents are stuck in place or engaged in endless combat. Verify pathfinding obstacles and combat termination criteria.\n")
                if meta['warnings_count'] > 0:
                    f.write("3. 🟨 **Analyze Quest Stalls & Node Crowding**: Quests are taking too long or too many agents gather at resource nodes. Optimize spawning density and target choice.\n\n")

            # Upgraded Report V2 Clustered Anomaly Details
            f.write("## ⚠️ Top Anomaly Breakdowns & Clustered Details (Report V2)\n\n")
            
            if not anomalies and not clusters:
                f.write("> Zero anomalies triggered during this run.\n\n")
            else:
                if anomalies:
                    f.write("### Raw Anomaly Logs:\n")
                    for a in anomalies:
                        f.write(f"- {a.get('message', '')} (Tick `{a.get('tick_detected', 0)}`, Severity: `{a.get('severity', '')}`)\n")
                    f.write("\n")

                if clusters:
                    f.write("### Spacetime Clustered Anomalies:\n")
                    for idx, c in enumerate(clusters, 1):
                        emoji = "🟥" if c["severity"] == "CRITICAL" else "🟧" if c["severity"] == "ERROR" else "🟨"
                        f.write(f"#### {idx}. {emoji} {c['rule_id']} — {c['severity']}\n")
                        f.write(f"- **Cluster ID**: `{c['cluster_id']}`\n")
                        f.write(f"- **Spacetime Span**: Ticks `{c['tick_start']} - {c['tick_end']}`\n")
                        
                        context_items = []
                        if c.get("region_id"):
                            context_items.append(f"Region: `{c['region_id']}`")
                        if c.get("resource_id"):
                            context_items.append(f"Resource: `{c['resource_id']}`")
                        if c.get("quest_id"):
                            context_items.append(f"Quest: `{c['quest_id']}`")
                        
                        if context_items:
                            f.write(f"- **Context**: {', '.join(context_items)}\n")
                        
                        if c.get("affected_entity_ids"):
                            f.write(f"- **Affected Entity IDs**: `{c['affected_entity_ids']}`\n")
                        
                        # Suggested Causes
                        if c.get("suggested_causes"):
                            f.write("- **Primary Suggested Causes**:\n")
                            for cause in c["suggested_causes"]:
                                f.write(f"  - {cause}\n")

                        # Troubleshooting hints
                        from src.observability.anomaly.triage import InvestigationHint
                        hints = InvestigationHint.get_hints(c["rule_id"])
                        f.write("- **Troubleshooting Hints**:\n")
                        for hint in hints:
                            f.write(f"  - {hint}\n")

                        # Collapsible Evidence
                        if c.get("evidence_samples"):
                            f.write("- **Evidence Payload Context**:\n")
                            f.write("  <details>\n")
                            f.write(f"  <summary>View Evidence Payloads (Matches: {len(c['evidence_samples'])})</summary>\n\n")
                            f.write("  ```json\n")
                            f.write(json.dumps(c["evidence_samples"], indent=2) + "\n")
                            f.write("  ```\n")
                            f.write("  </details>\n")
                        f.write("\n")

            f.write("## 📜 Diagnostic Entity Timelines\n\n")
            if not timelines:
                f.write("> No active entity timelines flagged for investigation.\n\n")
            else:
                for eid, events in timelines.items():
                    f.write(f"### Entity `{eid}` Timeline History\n\n")
                    f.write("| Tick | Category | Event Type | Diagnostic Message |\n")
                    f.write("| :--- | :--- | :--- | :--- |\n")
                    for ev in events:
                        cat = str(ev.get("event_category", "")).upper()
                        ev_type = str(ev.get("event_type", ""))
                        msg = str(ev.get("message", ""))
                        f.write(f"| `{ev.get('tick')}` | **{cat}** | `{ev_type}` | {msg} |\n")
                    f.write("\n")
