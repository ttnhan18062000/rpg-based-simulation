from __future__ import annotations
import os
import json
import logging
import time
from typing import Any, Dict, List, Optional
from src.core.lifecycle import ShutdownResult
from src.observability.entity_timeline import EntityTimelineStore

logger = logging.getLogger(__name__)

class RunReportGenerator:
    """Aggregates diagnostics, computes deterministic health scores, and generates simulation run reports."""
    @staticmethod
    def generate(
        run_dir: str,
        shutdown_result: Optional[Any] = None,
        timeline_store: Optional[EntityTimelineStore] = None
    ) -> Dict[str, Any]:
        """Orchestrates post-run report generation, saving run_report.md and run_report.json."""
        # Ensure run directory exists
        os.makedirs(run_dir, exist_ok=True)

        # 1. Load anomalies
        anomalies: List[Dict[str, Any]] = []
        anomalies_path = os.path.join(run_dir, "anomalies.json")
        if os.path.exists(anomalies_path):
            try:
                with open(anomalies_path, "r", encoding="utf-8") as f:
                    anomalies = json.load(f)
            except Exception as e:
                logger.error(f"Failed loading anomalies.json: {e}")

        # 2. Compute Health Score
        health_score = 100.0
        hard_law_violations_count = 0
        errors_count = 0
        warnings_count = 0

        for a in anomalies:
            severity = a.get("severity", "WARNING")
            rule_name = a.get("rule_name", "")
            if severity == "CRITICAL" or rule_name == "HardLawViolationRule":
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

        report_data = {
            "metadata": metadata,
            "anomalies": anomalies,
            "flagged_timelines": flagged_timelines
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

            f.write("## ⚠️ Top Anomaly Breakdowns\n\n")
            if not anomalies:
                f.write("> Zero anomalies triggered during this run.\n\n")
            else:
                for idx, a in enumerate(anomalies[:5], 1):
                    emoji = "🟥" if a.get("severity") == "CRITICAL" else "🟧" if a.get("severity") == "ERROR" else "🟨"
                    f.write(f"### {idx}. {emoji} {a.get('rule_name')} (Tick `{a.get('tick_detected')}`)\n")
                    f.write(f"- **Message**: {a.get('message')}\n")
                    f.write(f"- **Entity ID**: `{a.get('entity_id')}`\n")
                    if a.get("context"):
                        f.write("- **Telemetric context**:\n")
                        f.write("  ```json\n")
                        f.write(json.dumps(a.get("context"), indent=2) + "\n")
                        f.write("  ```\n")
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
                        # Translate category / severity for easy display
                        cat = str(ev.get("event_category", "")).upper()
                        ev_type = str(ev.get("event_type", ""))
                        msg = str(ev.get("message", ""))
                        f.write(f"| `{ev.get('tick')}` | **{cat}** | `{ev_type}` | {msg} |\n")
                    f.write("\n")
