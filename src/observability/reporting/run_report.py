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
            "hard_law_violation_count": hard_law_violations_count,
            "hard_law_violations_count": hard_law_violations_count,
            "critical_count": hard_law_violations_count,
            "errors_count": errors_count,
            "error_count": errors_count,
            "warnings_count": warnings_count,
            "warning_count": warnings_count,
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

        # Load cognition artifacts securely
        cognition_summary = {
            "available": False,
            "patterns": [],
            "features": [],
            "snapshots": [],
            "diffs": []
        }
        
        patterns_path = os.path.join(run_dir, "cognition_patterns.json")
        features_path = os.path.join(run_dir, "cognition_features.jsonl")
        snapshots_path = os.path.join(run_dir, "cognition_graph_snapshots.jsonl")
        diffs_path = os.path.join(run_dir, "cognition_graph_diffs.jsonl")

        if os.path.exists(patterns_path):
            try:
                with open(patterns_path, "r", encoding="utf-8") as f:
                    cognition_summary["patterns"] = json.load(f)
                    cognition_summary["available"] = True
            except Exception as e:
                logger.error(f"Failed loading cognition_patterns.json: {e}")
        
        if os.path.exists(features_path):
            try:
                feats = []
                with open(features_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            feats.append(json.loads(line))
                cognition_summary["features"] = feats
                cognition_summary["available"] = True
            except Exception as e:
                logger.error(f"Failed loading cognition_features.jsonl: {e}")

        if os.path.exists(snapshots_path):
            try:
                snaps = []
                with open(snapshots_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            snaps.append(json.loads(line))
                cognition_summary["snapshots"] = snaps
                cognition_summary["available"] = True
            except Exception as e:
                logger.error(f"Failed loading cognition_graph_snapshots.jsonl: {e}")

        if os.path.exists(diffs_path):
            try:
                dfs = []
                with open(diffs_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            dfs.append(json.loads(line))
                cognition_summary["diffs"] = dfs
                cognition_summary["available"] = True
            except Exception as e:
                logger.error(f"Failed loading cognition_graph_diffs.jsonl: {e}")

        # Resolve provenance info for each anomaly
        from src.observability.reporting.artifact_repository import RunArtifactRepository
        from src.observability.warehouse.provenance_lookup import ProvenanceLookupService

        base_dir = os.path.dirname(run_dir) or "."
        repo = RunArtifactRepository(base_dir=base_dir)
        lookup_service = ProvenanceLookupService(run_repo=repo)
        run_id = os.path.basename(run_dir)

        by_module = {}
        by_profile = {}
        by_faction = {}

        for a in anomalies:
            entity_ids = []
            region_ids = []
            resource_ids = []

            # Extract from anomaly record / dict representation
            if "affected_entity_ids" in a and a["affected_entity_ids"]:
                entity_ids.extend([str(eid) for eid in a["affected_entity_ids"]])
            elif a.get("entity_id") is not None:
                entity_ids.append(str(a["entity_id"]))

            ctx = a.get("context", {})
            if isinstance(ctx, dict):
                # Check for structured evidence
                if "affected_ids" in ctx:
                    aff = ctx["affected_ids"]
                    if isinstance(aff, dict):
                        entity_ids.extend([str(eid) for eid in aff.get("entities", []) if eid is not None])
                        region_ids.extend([str(rid) for rid in aff.get("regions", []) if rid is not None])
                        resource_ids.extend([str(rid) for rid in aff.get("resources", []) if rid is not None])
                elif "evidence" in ctx and isinstance(ctx["evidence"], dict):
                    aff = ctx["evidence"].get("affected_ids", {})
                    if isinstance(aff, dict):
                        entity_ids.extend([str(eid) for eid in aff.get("entities", []) if eid is not None])
                        region_ids.extend([str(rid) for rid in aff.get("regions", []) if rid is not None])
                        resource_ids.extend([str(rid) for rid in aff.get("resources", []) if rid is not None])
                
                # Check directly in context
                for r_id in ctx.get("affected_region_ids", []):
                    if r_id is not None:
                        region_ids.append(str(r_id))
                for r_id in ctx.get("affected_resource_ids", []):
                    if r_id is not None:
                        resource_ids.append(str(r_id))

            entity_ids = list(set(entity_ids))
            region_ids = list(set(region_ids))
            resource_ids = list(set(resource_ids))

            # Resolve origins
            a_modules = set()
            a_profiles = set()
            a_factions = set()

            for eid in entity_ids:
                origin = lookup_service.get_entity_origin(run_id, eid)
                if origin:
                    if origin.get("source_module"):
                        a_modules.add(origin["source_module"])
                    prof = origin.get("profiles", {})
                    if isinstance(prof, dict):
                        role = prof.get("role") or prof.get("building_type") or prof.get("resource_type")
                        if role:
                            a_profiles.add(role)
                        fact = prof.get("faction")
                        if fact:
                            a_factions.add(fact)

            for rid in region_ids:
                origin = lookup_service.get_region_origin(run_id, rid)
                if origin:
                    if origin.get("source_module"):
                        a_modules.add(origin["source_module"])
                    prof = origin.get("profiles", {})
                    if isinstance(prof, dict):
                        reg_type = prof.get("region_type")
                        if reg_type:
                            a_profiles.add(reg_type)

            for rid in resource_ids:
                try:
                    num_id = int(rid)
                except ValueError:
                    num_id = None

                if num_id is not None and num_id >= 20000:
                    origin = lookup_service.get_building_origin(run_id, rid)
                else:
                    origin = lookup_service.get_resource_origin(run_id, rid)
                    if not origin:
                        origin = lookup_service.get_building_origin(run_id, rid)

                if origin:
                    if origin.get("source_module"):
                        a_modules.add(origin["source_module"])
                    prof = origin.get("profiles", {})
                    if isinstance(prof, dict):
                        val = prof.get("resource_type") or prof.get("building_type")
                        if val:
                            a_profiles.add(val)

            # Ensure default unknown is handled
            if not a_modules:
                a_modules.add("unknown")
            if not a_profiles:
                a_profiles.add("unknown")
            if not a_factions:
                a_factions.add("unknown")

            a["provenance"] = {
                "source_modules": list(a_modules),
                "profiles": list(a_profiles),
                "factions": list(a_factions)
            }

            for m in a_modules:
                by_module.setdefault(m, []).append(a)
            for p in a_profiles:
                by_profile.setdefault(p, []).append(a)
            for f in a_factions:
                by_faction.setdefault(f, []).append(a)

        provenance_grouping = {
            "by_module": {m: [{"rule_name": an.get("rule_name"), "severity": an.get("severity"), "message": an.get("message"), "tick": an.get("tick_detected")} for an in list_an] for m, list_an in by_module.items()},
            "by_profile": {p: [{"rule_name": an.get("rule_name"), "severity": an.get("severity"), "message": an.get("message"), "tick": an.get("tick_detected")} for an in list_an] for p, list_an in by_profile.items()},
            "by_faction": {f: [{"rule_name": an.get("rule_name"), "severity": an.get("severity"), "message": an.get("message"), "tick": an.get("tick_detected")} for an in list_an] for f, list_an in by_faction.items()}
        }

        report_data = {
            "metadata": metadata,
            "anomalies": anomalies,
            "provenance_grouping": provenance_grouping,
            "flagged_timelines": flagged_timelines,
            "rule_execution": serialized_rule_results,
            "anomaly_clusters": serialized_clusters,
            "health_score": health_score,
            "critical_count": hard_law_violations_count,
            "warning_count": warnings_count,
            "hard_law_violation_count": hard_law_violations_count,
            "hard_law_violations_count": hard_law_violations_count,
            "errors_count": errors_count,
            "error_count": errors_count,
            "warnings_count": warnings_count,
            "total_anomalies_count": len(anomalies),
            "cognition": cognition_summary
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

            # Render Strategic Cognition Evidence
            cognition = data.get("cognition", {})
            f.write("## 🧠 Strategic Cognition Evidence\n\n")
            if not cognition or not cognition.get("available", False):
                f.write("> Strategic cognition data is missing or unavailable for this run.\n\n")
            else:
                snaps = cognition.get("snapshots", [])
                diffs = cognition.get("diffs", [])
                features = cognition.get("features", [])
                patterns = cognition.get("patterns", [])

                # Get latest snapshot per entity
                latest_snaps = {}
                for snap in snaps:
                    eid = snap.get("entity_id")
                    tick = snap.get("tick")
                    if eid not in latest_snaps or tick > latest_snaps[eid]["tick"]:
                        latest_snaps[eid] = snap

                if not latest_snaps:
                    f.write("> No active cognition snapshots recorded in this run.\n\n")
                else:
                    for eid, snap in latest_snaps.items():
                        f.write(f"### Entity `{eid}` Strategic Status (Tick `{snap['tick']}`)\n\n")
                        f.write(f"- **Current Project**: `{snap.get('current_project_id') or 'None'}`\n")
                        f.write(f"- **Current Objective**: `{snap.get('current_objective_id') or 'None'}`\n")
                        f.write(f"- **Primary Overload Source**: `{snap.get('overload_source') or 'None'}`\n\n")

                        # Extract nodes
                        nodes = snap.get("nodes", [])
                        
                        blockers = [n for n in nodes if n.get("kind") == "blocker"]
                        leads = [n for n in nodes if n.get("kind") == "lead"]
                        concerns = [n for n in nodes if n.get("kind") == "concern"]
                        hypotheses = [n for n in nodes if n.get("kind") == "hypothesis"]

                        # Blockers
                        f.write("#### Active Blockers\n")
                        if not blockers:
                            f.write("- *None*\n")
                        for b in blockers:
                            label = b.get("label", "")
                            meta = b.get("metadata", {})
                            sev = meta.get("severity", "unknown")
                            res = "Resolved" if meta.get("resolved") else "Active"
                            f.write(f"- `{b['node_id']}`: {label} (Severity: `{sev}`, Status: `{res}`)\n")
                        f.write("\n")

                        # Leads
                        f.write("#### Known Leads\n")
                        if not leads:
                            f.write("- *None*\n")
                        for l in leads:
                            label = l.get("label", "")
                            meta = l.get("metadata", {})
                            cert = meta.get("certainty", "unknown")
                            tst = "Tested" if meta.get("tested") else "Untested"
                            f.write(f"- `{l['node_id']}`: {label} (Certainty: `{cert}`, Status: `{tst}`)\n")
                        f.write("\n")

                        # Concerns
                        f.write("#### Concerns\n")
                        if not concerns:
                            f.write("- *None*\n")
                        for c in concerns:
                            label = c.get("label", "")
                            meta = c.get("metadata", {})
                            urg = meta.get("urgency", 0)
                            f.write(f"- `{c['node_id']}`: {label} (Urgency: `{urg}`)\n")
                        f.write("\n")

                        # Hypotheses
                        f.write("#### Hypotheses\n")
                        if not hypotheses:
                            f.write("- *None*\n")
                        for h in hypotheses:
                            label = h.get("label", "")
                            meta = h.get("metadata", {})
                            conf = meta.get("confidence", 0.0)
                            f.write(f"- `{h['node_id']}`: {label} (Confidence: `{conf}`)\n")
                        f.write("\n")

                # Recent cognition changes
                f.write("### Recent Strategic Cognition Changes\n\n")
                if not diffs:
                    f.write("- *No strategic cognition changes recorded.*\n\n")
                else:
                    for d in diffs[-10:]: # last 10 diffs
                        eid = d.get("entity_id")
                        tick = d.get("tick")
                        reason = d.get("reason", "unknown")
                        f.write(f"- **Tick {tick} (Entity {eid})** [{reason}]:\n")
                        f.write(f"  - Added nodes: `{d.get('added_nodes', [])}`\n")
                        f.write(f"  - Removed nodes: `{d.get('removed_nodes', [])}`\n")
                        if d.get("current_project_changed"):
                            f.write(f"  - Project changed to: `{d.get('current_project_id')}`\n")
                        if d.get("current_objective_changed"):
                            f.write(f"  - Objective changed to: `{d.get('current_objective_id')}`\n")
                    f.write("\n")

                # Potential cognition patterns
                f.write("### Potential Cognition Patterns\n\n")
                if not patterns:
                    f.write("- *No strategic cognition failure patterns identified.*\n\n")
                else:
                    for p in patterns:
                        eid = p.get("entity_id")
                        ptype = p.get("pattern_type", "unknown")
                        sev = p.get("severity", "WARNING")
                        desc = p.get("description", "")
                        tick = p.get("tick_detected")
                        f.write(f"- `{ptype}` ({sev}) on Entity `{eid}` at Tick `{tick}`: {desc}\n")
                    f.write("\n")

            # Provenance grouping section
            f.write("## 🌐 Provenance Source Grouping\n\n")
            if not anomalies:
                f.write("🟢 **No anomalies detected. All provenance sources (modules, profiles, factions) are verified and clean.**\n\n")
            else:
                f.write("This section groups detected anomalies and violations by their compile-time source module, profile, and faction based on resolved world assembly provenance metadata.\n\n")
                
                # Reconstruct groups from anomalies list
                by_module = {}
                by_profile = {}
                by_faction = {}
                for a in anomalies:
                    prov = a.get("provenance", {})
                    for m in prov.get("source_modules", ["unknown"]):
                        by_module.setdefault(m, []).append(a)
                    for p in prov.get("profiles", ["unknown"]):
                        by_profile.setdefault(p, []).append(a)
                    for fac in prov.get("factions", ["unknown"]):
                        by_faction.setdefault(fac, []).append(a)
                        
                f.write("### 📦 By Source Module\n\n")
                f.write("| Source Module | Severity | Rule ID | Message (Tick) |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for m, list_an in sorted(by_module.items()):
                    for a in list_an:
                        f.write(f"| `{m}` | `{a.get('severity', 'WARNING')}` | `{a.get('rule_name', '')}` | {a.get('message', '')} (Tick `{a.get('tick_detected', 0)}`) |\n")
                f.write("\n")
                
                f.write("### 👤 By Profile / Role\n\n")
                f.write("| Profile | Severity | Rule ID | Message (Tick) |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for p, list_an in sorted(by_profile.items()):
                    for a in list_an:
                        f.write(f"| `{p}` | `{a.get('severity', 'WARNING')}` | `{a.get('rule_name', '')}` | {a.get('message', '')} (Tick `{a.get('tick_detected', 0)}`) |\n")
                f.write("\n")
                
                f.write("### 🛡️ By Faction\n\n")
                f.write("| Faction | Severity | Rule ID | Message (Tick) |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                for fact, list_an in sorted(by_faction.items()):
                    for a in list_an:
                        f.write(f"| `{fact}` | `{a.get('severity', 'WARNING')}` | `{a.get('rule_name', '')}` | {a.get('message', '')} (Tick `{a.get('tick_detected', 0)}`) |\n")
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
