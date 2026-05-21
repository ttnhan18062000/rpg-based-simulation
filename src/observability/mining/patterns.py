# Compliance IDs: OBS-PH9-M52
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.observability.mining.dataset import DatasetQueryService

logger = logging.getLogger(__name__)


class PatternMiningEngine:
    """Mines multi-run simulation datasets to extract recurring patterns, temporal failure windows, and hotspots."""
    
    @classmethod
    def mine_patterns(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        dataset_dir = os.path.join(experiment_dir, "dataset")
        
        query_service = DatasetQueryService(dataset_dir)
        
        # 1. Outlier Detection: Find runs with lowest health or highest anomaly count
        outliers = []
        try:
            sql = """
                SELECT run_id, seed, health_score, anomaly_count, hard_law_violation_count 
                FROM run_features 
                ORDER BY health_score ASC, hard_law_violation_count DESC, anomaly_count DESC
                LIMIT 10
            """
            outliers = query_service.query(sql)
        except Exception as e:
            logger.warning(f"Outlier SQL extraction failed: {e}")
            
        # 2. Recurring Anomalies: Rank rules across runs
        recurring_anomalies = []
        try:
            sql = """
                SELECT rule_id, severity, domain, COUNT(*) as occurrence_count, COUNT(DISTINCT run_id) as affected_runs
                FROM anomalies 
                GROUP BY rule_id, severity, domain
                ORDER BY occurrence_count DESC
            """
            recurring_anomalies = query_service.query(sql)
        except Exception as e:
            logger.warning(f"Recurring anomaly SQL extraction failed: {e}")
            
        # 3. Domain Clusters: Anomalies segregated by category
        domain_clusters = []
        try:
            sql = """
                SELECT domain, COUNT(*) as anomaly_count, COUNT(DISTINCT run_id) as affected_runs
                FROM anomalies 
                GROUP BY domain
                ORDER BY anomaly_count DESC
            """
            domain_clusters = query_service.query(sql)
        except Exception as e:
            logger.warning(f"Domain SQL extraction failed: {e}")
            
        # 4. Temporal Patterns: Find common tick ranges when failures begin
        temporal_patterns = []
        try:
            # Group by 1000-tick intervals
            sql = """
                SELECT ((tick / 1000) * 1000) as tick_bucket, COUNT(*) as anomaly_count
                FROM anomalies 
                GROUP BY tick_bucket
                ORDER BY anomaly_count DESC
                LIMIT 10
            """
            temporal_patterns = query_service.query(sql)
        except Exception as e:
            logger.warning(f"Temporal SQL extraction failed: {e}")
            
        # 5. Hotspots: Common entities or targets associated with anomalies
        hotspots = []
        try:
            # Parse messages for mentions of region or node IDs
            # Simple extraction for entity hotspots
            sql = """
                SELECT message, COUNT(*) as count 
                FROM anomalies 
                WHERE message LIKE '%entity%' OR message LIKE '%node%' OR message LIKE '%region%'
                GROUP BY message
                ORDER BY count DESC
                LIMIT 10
            """
            hotspots = query_service.query(sql)
        except Exception as e:
            logger.warning(f"Hotspot SQL extraction failed: {e}")
            
        report = {
            "experiment_id": experiment_id,
            "outlier_runs": outliers,
            "recurring_anomalies": recurring_anomalies,
            "domain_clusters": domain_clusters,
            "temporal_patterns": temporal_patterns,
            "hotspots": hotspots,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save JSON
        report_path = os.path.join(experiment_dir, "pattern_mining_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        # Write Markdown
        cls._write_markdown_report(report, os.path.join(experiment_dir, "pattern_mining_report.md"))
        
        return report
        
    @classmethod
    def _write_markdown_report(cls, report: Dict[str, Any], path: str) -> None:
        md = f"""# Cross-Run Pattern Mining Report

**Experiment ID**: `{report["experiment_id"]}`
**Timestamp**: `{report["created_at"]}`

---

## 1. Outlier Runs (Worst Performing Seeds)
"""
        for o in report["outlier_runs"][:5]:
            md += f"*   `{o['run_id']}` (Seed: {o['seed']}): **Health Score: {o['health_score']:.1f}** | Anomaly Count: {o['anomaly_count']} | Law Violations: {o['hard_law_violation_count']}\n"
            
        md += "\n## 2. Recurring Anomaly Rankings\n"
        for a in report["recurring_anomalies"][:5]:
            md += f"*   `{a['rule_id']}` ({a['domain']}): Occurred **{a['occurrence_count']}** times across **{a['affected_runs']}** runs.\n"
            
        md += "\n## 3. Subsystem Domain Distribution\n"
        for d in report["domain_clusters"]:
            md += f"*   **{d['domain']}**: {d['anomaly_count']} anomalies across {d['affected_runs']} runs.\n"
            
        md += "\n## 4. Temporal Congestion Windows\n"
        for t in report["temporal_patterns"][:5]:
            md += f"*   **Tick Bucket {t['tick_bucket']} - {t['tick_bucket'] + 999}**: {t['anomaly_count']} anomalies triggered.\n"
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
