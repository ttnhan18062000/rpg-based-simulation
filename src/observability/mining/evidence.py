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
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        with open(os.path.join(evidence_dir, "evidence_pack.json"), "w", encoding="utf-8") as f:
            json.dump(pack_manifest, f, indent=2)
            
        return pack_manifest
