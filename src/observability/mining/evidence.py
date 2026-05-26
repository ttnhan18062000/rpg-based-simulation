# Compliance IDs: OBS-PH9-M54
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EvidencePackBuilder:
    """Aggregates highly compressed, context-isolated telemetry excerpts and reproduction parameters for debugging."""
    
    @classmethod
    def build_evidence_pack(cls, experiment_id: str, candidate_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        
        # Load backlog to find candidate spec
        backlog_path = os.path.join(experiment_dir, "engineering_backlog.json")
        if not os.path.exists(backlog_path):
            raise FileNotFoundError(f"Engineering backlog not found at: {backlog_path}")
            
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog = json.load(f)
            
        candidate = None
        for item in backlog.get("backlog_items", []):
            if item["candidate_id"] == candidate_id:
                candidate = item
                break
                
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found in backlog.")
            
        # Create candidate evidence directory
        evidence_dir = os.path.join(experiment_dir, "evidence_packs", candidate_id)
        os.makedirs(evidence_dir, exist_ok=True)
        
        # Locate representative runs and seeds
        affected_runs = []
        affected_seeds = []
        
        # Parse datasets to find runs experiencing this specific anomaly
        dataset_dir = os.path.join(experiment_dir, "dataset")
        anomalies_json = os.path.join(dataset_dir, "anomalies.json")
        
        trigger_ticks = {}
        
        if os.path.exists(anomalies_json):
            try:
                with open(anomalies_json, "r", encoding="utf-8") as f:
                    anomalies = json.load(f)
                    for a in anomalies:
                        # Check matches
                        match = False
                        if "anomaly_pattern" in candidate_id:
                            target_rule = candidate_id.replace("anomaly_pattern_", "")
                            match = a.get("rule_id") == target_rule
                        else:
                            match = str(a.get("seed")) in candidate_id
                            
                        if match:
                            r_id = a["run_id"]
                            seed = a["seed"]
                            tick = a.get("tick", 0)
                            if r_id not in affected_runs:
                                affected_runs.append(r_id)
                                trigger_ticks[r_id] = tick
                            if seed not in affected_seeds:
                                affected_seeds.append(seed)
            except Exception as e:
                logger.warning(f"Error filtering anomalies for evidence builder: {e}")
                
        # Fill manifest values
        candidate["affected_runs"] = affected_runs
        candidate["affected_seeds"] = affected_seeds
        if affected_seeds:
            candidate["reproduction_seed"] = affected_seeds[0]
            
        # Select best representative runs (up to 3 worst runs)
        rep_runs = affected_runs[:3]
        
        # Extract excerpts of metric windows & event logs around anomaly ticks
        events_excerpt = []
        metrics_excerpt = []
        
        for r_id in rep_runs:
            run_dir = os.path.join(experiment_dir, "runs", r_id)
            trigger_tick = trigger_ticks.get(r_id, 1000)
            
            # Slice metrics around trigger tick (-500 to +500 ticks)
            metrics_file = os.path.join(run_dir, "metric_windows.jsonl")
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            m = json.loads(line)
                            tick = m.get("tick", 0)
                            if trigger_tick - 500 <= tick <= trigger_tick + 500:
                                metrics_excerpt.append(m)
                except Exception:
                    pass
                    
            # Slice simulation events around trigger tick (-200 to +200 ticks)
            events_file = os.path.join(run_dir, "simulation_events.jsonl")
            if os.path.exists(events_file):
                try:
                    with open(events_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            e = json.loads(line)
                            tick = e.get("tick", 0)
                            if trigger_tick - 200 <= tick <= trigger_tick + 200:
                                events_excerpt.append(e)
                except Exception:
                    pass
                    
        # Collect matched anomalies to extract their entity_ids and trigger ticks
        matched_anomalies = []
        if os.path.exists(anomalies_json):
            try:
                with open(anomalies_json, "r", encoding="utf-8") as f:
                    anomalies = json.load(f)
                    for a in anomalies:
                        match = False
                        if "anomaly_pattern" in candidate_id:
                            target_rule = candidate_id.replace("anomaly_pattern_", "")
                            match = a.get("rule_id") == target_rule
                        else:
                            match = str(a.get("seed")) in candidate_id
                        
                        if match:
                            matched_anomalies.append(a)
            except Exception as e:
                logger.warning(f"Error filtering anomalies for matching: {e}")

        # Identify representative target entity
        target_eid = None
        for a in matched_anomalies:
            if a.get("entity_id") is not None:
                target_eid = a.get("entity_id")
                break

        # Collect cognition evidence for representative runs
        cognition_summary_manifest = {
            "top_affected_entities": [],
            "current_projects": {},
            "unresolved_blockers_count": 0,
            "known_leads_count": 0,
            "project_switch_count": 0,
            "detour_count": 0,
            "overload_count": 0,
            "graph_diff_summary": {}
        }

        # We will loop through the representative runs to gather the actual cognition files and output them
        for r_id in rep_runs:
            run_dir = os.path.join(experiment_dir, "runs", r_id)
            trigger_tick = trigger_ticks.get(r_id, 1000)
            
            # Load files
            snapshots_file = os.path.join(run_dir, "cognition_graph_snapshots.jsonl")
            diffs_file = os.path.join(run_dir, "cognition_graph_diffs.jsonl")
            features_file = os.path.join(run_dir, "cognition_features.jsonl")
            patterns_file = os.path.join(run_dir, "cognition_patterns.json")

            snaps = []
            if os.path.exists(snapshots_file):
                try:
                    with open(snapshots_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                snaps.append(json.loads(line))
                except Exception:
                    pass

            diffs = []
            if os.path.exists(diffs_file):
                try:
                    with open(diffs_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                diffs.append(json.loads(line))
                except Exception:
                    pass

            feats = []
            if os.path.exists(features_file):
                try:
                    with open(features_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                feats.append(json.loads(line))
                except Exception:
                    pass

            patterns = []
            if os.path.exists(patterns_file):
                try:
                    with open(patterns_file, "r", encoding="utf-8") as f:
                        patterns = json.load(f)
                except Exception:
                    pass

            # Write before/after/diff/feature/pattern summaries for target_eid
            if target_eid is not None:
                # Find before snapshot (tick <= trigger_tick)
                before_snap = None
                for snap in reversed(snaps):
                    if snap.get("entity_id") == target_eid and snap.get("tick", 0) <= trigger_tick:
                        before_snap = snap
                        break
                
                # Find after snapshot (tick > trigger_tick or closest >= trigger_tick)
                after_snap = None
                for snap in snaps:
                    if snap.get("entity_id") == target_eid and snap.get("tick", 0) > trigger_tick:
                        after_snap = snap
                        break
                if not after_snap and snaps:
                    # fallback to latest snap for target_eid
                    for snap in reversed(snaps):
                        if snap.get("entity_id") == target_eid:
                            after_snap = snap
                            break

                # Find diff
                matched_diff = None
                for d in diffs:
                    if d.get("entity_id") == target_eid and d.get("tick", 0) == (after_snap.get("tick") if after_snap else -1):
                        matched_diff = d
                        break

                # Target features
                target_feats = [f for f in feats if f.get("entity_id") == target_eid]
                # Target patterns
                target_patterns = [p for p in patterns if p.get("entity_id") == target_eid]

                if before_snap:
                    with open(os.path.join(evidence_dir, "cognition_snapshot_before.json"), "w", encoding="utf-8") as f:
                        json.dump(before_snap, f, indent=2)
                if after_snap:
                    with open(os.path.join(evidence_dir, "cognition_snapshot_after.json"), "w", encoding="utf-8") as f:
                        json.dump(after_snap, f, indent=2)
                if matched_diff:
                    with open(os.path.join(evidence_dir, "cognition_diff.json"), "w", encoding="utf-8") as f:
                        json.dump(matched_diff, f, indent=2)
                
                with open(os.path.join(evidence_dir, "cognition_feature_summary.json"), "w", encoding="utf-8") as f:
                    json.dump(target_feats, f, indent=2)
                with open(os.path.join(evidence_dir, "cognition_pattern_summary.json"), "w", encoding="utf-8") as f:
                    json.dump(target_patterns, f, indent=2)

            # Build affected_entities_cognition_summary.json across all entities
            affected_summary = {}
            for snap in snaps:
                eid = snap.get("entity_id")
                tick = snap.get("tick")
                if eid not in affected_summary or tick > affected_summary[eid]["tick"]:
                    nodes = snap.get("nodes", [])
                    blockers_cnt = sum(1 for n in nodes if n.get("kind") == "blocker")
                    leads_cnt = sum(1 for n in nodes if n.get("kind") == "lead")
                    concerns_cnt = sum(1 for n in nodes if n.get("kind") == "concern")
                    
                    affected_summary[eid] = {
                        "entity_id": eid,
                        "tick": tick,
                        "current_project": snap.get("current_project_id"),
                        "current_objective": snap.get("current_objective_id"),
                        "blocker_count": blockers_cnt,
                        "lead_count": leads_cnt,
                        "concern_count": concerns_cnt,
                        "overload_source": snap.get("overload_source")
                    }

            with open(os.path.join(evidence_dir, "affected_entities_cognition_summary.json"), "w", encoding="utf-8") as f:
                json.dump(list(affected_summary.values()), f, indent=2)

            # Aggregate into the compressed cognition_summary manifest
            unique_eids = list(affected_summary.keys())
            cognition_summary_manifest["top_affected_entities"].extend(unique_eids[:5])
            for eid, summary in affected_summary.items():
                if summary["current_project"]:
                    cognition_summary_manifest["current_projects"][str(eid)] = {
                        "project": summary["current_project"],
                        "objective": summary["current_objective"]
                    }
                cognition_summary_manifest["unresolved_blockers_count"] += summary["blocker_count"]
                cognition_summary_manifest["known_leads_count"] += summary["lead_count"]
                if summary["overload_source"]:
                    cognition_summary_manifest["overload_count"] += 1

            # Project switch count, detour count, diff summary
            project_switch_count = 0
            detour_count = 0
            added_nodes_tot = 0
            removed_nodes_tot = 0
            for d in diffs:
                if d.get("current_project_changed"):
                    project_switch_count += 1
                detour_count += d.get("detour_delta_count", 0)
                added_nodes_tot += len(d.get("added_nodes", []))
                removed_nodes_tot += len(d.get("removed_nodes", []))

            cognition_summary_manifest["project_switch_count"] += project_switch_count
            cognition_summary_manifest["detour_count"] += detour_count
            cognition_summary_manifest["graph_diff_summary"] = {
                "added_nodes_count": added_nodes_tot,
                "removed_nodes_count": removed_nodes_tot
            }

        # Write files
        with open(os.path.join(evidence_dir, "affected_runs.json"), "w", encoding="utf-8") as f:
            json.dump(affected_runs, f, indent=2)
            
        with open(os.path.join(evidence_dir, "affected_seeds.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(str(s) for s in affected_seeds))
            
        with open(os.path.join(evidence_dir, "metric_windows_excerpt.jsonl"), "w", encoding="utf-8") as f:
            for m in metrics_excerpt[:100]:  # Cap at 100 entries to prevent LLM overflow
                f.write(json.dumps(m) + "\n")
                
        with open(os.path.join(evidence_dir, "events_excerpt.jsonl"), "w", encoding="utf-8") as f:
            for e in events_excerpt[:100]:  # Cap at 100 entries to prevent LLM overflow
                f.write(json.dumps(e) + "\n")
                
        # Write reproduction instructions
        rep_command = f"pytest tests/integration/test_mining_experiment_flow.py -k \"reproduce\""
        if affected_seeds:
            rep_command = f"rpg-observe sweep --scenario {candidate.get('scenario_name', 'RESOURCE_ECONOMY_10')} --seeds {affected_seeds[0]} --ticks {candidate.get('ticks', 1000)}"
            
        repro_md = f"""# Reproduction Playbook

To reproduce this specific diagnostic candidate, execute the following CLI command in your virtual environment:

```bash
{rep_command}
```

---
*Generated by Phase 9 Evidence Pack Builder on {datetime.now(timezone.utc).isoformat()}*
"""
        with open(os.path.join(evidence_dir, "reproduction_commands.md"), "w", encoding="utf-8") as f:
            f.write(repro_md)
            
        # Write final pack JSON
        pack_manifest = {
            "candidate_id": candidate_id,
            "title": candidate["title"],
            "priority": candidate["priority"],
            "category": candidate["category"],
            "evidence_directory": evidence_dir,
            "reproduction_command": rep_command,
            "excerpts": {
                "events_count": len(events_excerpt),
                "metrics_count": len(metrics_excerpt)
            },
            "cognition_summary": cognition_summary_manifest,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        with open(os.path.join(evidence_dir, "evidence_pack.json"), "w", encoding="utf-8") as f:
            json.dump(pack_manifest, f, indent=2)
            
        return pack_manifest
