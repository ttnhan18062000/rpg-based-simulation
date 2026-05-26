# Compliance IDs: OBS-PH9-M50
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RunFeatureExtractor:
    """Extracts run-level features from individual simulation output folders."""
    
    @classmethod
    def extract_features(cls, run_dir: str, spec_data: Dict[str, Any]) -> Dict[str, Any]:
        run_id = spec_data.get("run_id")
        seed = spec_data.get("seed", 0)
        repeat_index = spec_data.get("repeat_index", 0)
        scenario_name = spec_data.get("scenario", "")
        scenario_type = spec_data.get("scenario_type", "")
        
        # Load run manifest
        status = "FAILED"
        ticks_completed = spec_data.get("ticks", 0)
        manifest_file = os.path.join(run_dir, "run_manifest.json")
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    status = manifest_data.get("status", "FAILED")
                    ticks_completed = manifest_data.get("ticks_completed", ticks_completed)
            except Exception as e:
                logger.warning(f"Error reading run_manifest.json for {run_id}: {e}")
                
        # Defaults
        health_score = 100.0
        critical_count = 0
        warning_count = 0
        hard_law_violation_count = 0
        anomaly_count = 0
        stuck_anomaly_count = 0
        quest_stall_count = 0
        economy_freeze_count = 0
        governor_degraded_count = 0
        tick_compute_ms_p95 = 0.0
        memory_rss_bytes_max = 0
        event_count = 0
        dropped_event_count = 0
        top_anomaly_rule = None
        top_domain = None
        worst_tick_range_start = None
        worst_tick_range_end = None
        
        # Load run report
        report_file = os.path.join(run_dir, "run_report.json")
        if os.path.exists(report_file):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    health_score = report_data.get("health_score", 100.0)
                    critical_count = report_data.get("critical_count", 0)
                    warning_count = report_data.get("warning_count", 0)
                    hard_law_violation_count = report_data.get("hard_law_violation_count", 0)
                    anomaly_count = report_data.get("anomaly_count", 0)
                    dropped_event_count = report_data.get("dropped_event_count", 0)
            except Exception as e:
                logger.warning(f"Error reading run_report.json for {run_id}: {e}")
                
        # Parse anomalies
        anomalies_file = os.path.join(run_dir, "anomalies.json")
        rule_counts = {}
        domain_counts = {}
        if os.path.exists(anomalies_file):
            try:
                with open(anomalies_file, "r", encoding="utf-8") as f:
                    anomalies = json.load(f)
                    for a in anomalies:
                        rule_id = a.get("rule_id", "unknown")
                        domain = a.get("domain", "unknown")
                        rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                        
                        # Stuck count
                        if "stuck" in rule_id.lower() or "stall" in rule_id.lower():
                            stuck_anomaly_count += 1
                        # Quest stall count
                        if "quest" in rule_id.lower() and "stall" in rule_id.lower():
                            quest_stall_count += 1
                        # Economy freeze count
                        if "econ" in rule_id.lower() and "freeze" in rule_id.lower():
                            economy_freeze_count += 1
                        # Governor degradation count
                        if "gov" in rule_id.lower() and "degrad" in rule_id.lower():
                            governor_degraded_count += 1
                            
                # Determine top rule and top domain
                if rule_counts:
                    top_anomaly_rule = max(rule_counts, key=rule_counts.get)
                if domain_counts:
                    top_domain = max(domain_counts, key=domain_counts.get)
            except Exception as e:
                logger.warning(f"Error parsing anomalies.json for {run_id}: {e}")
                
        # Parse metrics for p95 latency & memory
        metrics_file = os.path.join(run_dir, "metric_windows.jsonl")
        latencies = []
        memories = []
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        m = json.loads(line)
                        lat = m.get("tick_compute_ms_p95") or m.get("latency_p95") or m.get("tick_compute_ms")
                        mem = m.get("memory_rss_bytes_max") or m.get("memory_rss") or m.get("rss")
                        if lat is not None:
                            latencies.append(float(lat))
                        if mem is not None:
                            memories.append(int(mem))
                if latencies:
                    latencies.sort()
                    p95_idx = int(len(latencies) * 0.95)
                    tick_compute_ms_p95 = latencies[min(p95_idx, len(latencies) - 1)]
                if memories:
                    memory_rss_bytes_max = max(memories)
            except Exception as e:
                logger.warning(f"Error parsing metric_windows.jsonl for {run_id}: {e}")
                
        # Parse event count
        events_file = os.path.join(run_dir, "simulation_events.jsonl")
        if os.path.exists(events_file):
            try:
                with open(events_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            event_count += 1
            except Exception as e:
                logger.warning(f"Error counting simulation_events.jsonl for {run_id}: {e}")
                
        # Locate worst tick range
        # Worst range is defined as the tick window containing the highest density of anomalies
        anomaly_tick_density = {}
        if os.path.exists(anomalies_file):
            try:
                with open(anomalies_file, "r", encoding="utf-8") as f:
                    anomalies = json.load(f)
                    for a in anomalies:
                        tick = a.get("tick")
                        if tick is not None:
                            # Group by 100-tick windows
                            bucket = (tick // 100) * 100
                            anomaly_tick_density[bucket] = anomaly_tick_density.get(bucket, 0) + 1
                if anomaly_tick_density:
                    worst_bucket = max(anomaly_tick_density, key=anomaly_tick_density.get)
                    worst_tick_range_start = worst_bucket
                    worst_tick_range_end = worst_bucket + 99
            except Exception:
                pass
                
        return {
            "run_id": run_id,
            "seed": seed,
            "repeat_index": repeat_index,
            "scenario_name": scenario_name,
            "scenario_type": scenario_type,
            "status": status,
            "ticks_completed": ticks_completed,
            "health_score": health_score,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "hard_law_violation_count": hard_law_violation_count,
            "anomaly_count": anomaly_count,
            "stuck_anomaly_count": stuck_anomaly_count,
            "quest_stall_count": quest_stall_count,
            "economy_freeze_count": economy_freeze_count,
            "governor_degraded_count": governor_degraded_count,
            "tick_compute_ms_p95": tick_compute_ms_p95,
            "memory_rss_bytes_max": memory_rss_bytes_max,
            "event_count": event_count,
            "dropped_event_count": dropped_event_count,
            "top_anomaly_rule": top_anomaly_rule,
            "top_domain": top_domain,
            "worst_tick_range_start": worst_tick_range_start,
            "worst_tick_range_end": worst_tick_range_end
        }


class MiningDatasetBuilder:
    """Builds a queryable structured dataset from individual simulation run output folders."""
    
    @classmethod
    def build_dataset(cls, experiment_id: str, base_dir: str = "data/mining_experiments") -> Dict[str, Any]:
        experiment_dir = os.path.abspath(os.path.join(base_dir, experiment_id))
        manifest_file = os.path.join(experiment_dir, "experiment_manifest.json")
        if not os.path.exists(manifest_file):
            raise FileNotFoundError(f"Experiment manifest not found at: {manifest_file}")
            
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        run_ids = manifest.get("run_ids", [])
        
        # Load run matrix specifications
        matrix_specs = {}
        matrix_file = os.path.join(experiment_dir, "run_matrix.jsonl")
        if os.path.exists(matrix_file):
            try:
                with open(matrix_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        spec = json.loads(line)
                        matrix_specs[spec["run_id"]] = spec
            except Exception as e:
                logger.warning(f"Failed parsing run_matrix.jsonl: {e}")
                
        runs_table = []
        features_table = []
        anomalies_table = []
        hard_law_violations_table = []
        
        valid_run_count = 0
        missing_run_count = 0
        
        for run_id in run_ids:
            run_dir = os.path.join(experiment_dir, "runs", run_id)
            spec_data = matrix_specs.get(run_id, {"run_id": run_id})
            
            if not os.path.exists(run_dir):
                missing_run_count += 1
                runs_table.append({
                    "run_id": run_id,
                    "seed": spec_data.get("seed", 0),
                    "status": "MISSING_ARTIFACTS",
                    "ticks_completed": 0,
                    "health_score": 0.0
                })
                continue
                
            valid_run_count += 1
            
            # Extract features
            features = RunFeatureExtractor.extract_features(run_dir, spec_data)
            features_table.append(features)
            
            # Extract basic run overview
            runs_table.append({
                "run_id": run_id,
                "seed": features["seed"],
                "repeat_index": features["repeat_index"],
                "scenario_name": features["scenario_name"],
                "scenario_type": features["scenario_type"],
                "status": features["status"],
                "ticks_completed": features["ticks_completed"],
                "health_score": features["health_score"]
            })
            
            # Extract granular anomalies table
            anomalies_file = os.path.join(run_dir, "anomalies.json")
            if os.path.exists(anomalies_file):
                try:
                    with open(anomalies_file, "r", encoding="utf-8") as f:
                        anomalies = json.load(f)
                        for a in anomalies:
                            anomalies_table.append({
                                "run_id": run_id,
                                "seed": features["seed"],
                                "rule_id": a.get("rule_id"),
                                "severity": a.get("severity"),
                                "domain": a.get("domain"),
                                "tick": a.get("tick"),
                                "message": a.get("message")
                            })
                except Exception as e:
                    logger.warning(f"Failed extracting anomalies for {run_id}: {e}")
                    
            # Extract hard law violations table
            violations_file = os.path.join(run_dir, "hard_law_violations.jsonl")
            if os.path.exists(violations_file):
                try:
                    with open(violations_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            v = json.loads(line)
                            hard_law_violations_table.append({
                                "run_id": run_id,
                                "seed": features["seed"],
                                "law_id": v.get("law_id"),
                                "tick": v.get("tick"),
                                "message": v.get("message")
                            })
                except Exception as e:
                    logger.warning(f"Failed extracting violations for {run_id}: {e}")
                    
        # 3. Save tables to dataset folder
        dataset_dir = os.path.join(experiment_dir, "dataset")
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Save JSON tables
        tables_data = {
            "runs": runs_table,
            "run_features": features_table,
            "anomalies": anomalies_table,
            "hard_law_violations": hard_law_violations_table
        }
        
        for name, data in tables_data.items():
            json_path = os.path.join(dataset_dir, f"{name}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        # Optional: Save Parquet tables if pandas/pyarrow are present
        table_files = {
            "runs": "runs.json",
            "run_features": "run_features.json",
            "anomalies": "anomalies.json",
            "hard_law_violations": "hard_law_violations.json"
        }
        
        try:
            import pandas as pd
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            for name, data in tables_data.items():
                parquet_filename = f"{name}.parquet"
                parquet_path = os.path.join(dataset_dir, parquet_filename)
                df = pd.DataFrame(data)
                df.to_parquet(parquet_path, index=False)
                table_files[name] = parquet_filename
            logger.info("Successfully wrote dataset tables as Parquet archives.")
        except ImportError:
            logger.info("pyarrow/pandas absent; saved dataset tables as robust JSON structures.")
            
        # Write dataset manifest
        manifest_data = {
            "experiment_id": experiment_id,
            "source_run_count": len(run_ids),
            "valid_run_count": valid_run_count,
            "missing_run_count": missing_run_count,
            "table_files": table_files,
            "record_counts": {name: len(data) for name, data in tables_data.items()},
            "schema_version": "mining_dataset_v1",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        with open(os.path.join(dataset_dir, "dataset_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            
        return manifest_data


class DatasetQueryService:
    """Relational SQL query broker providing unified access across DuckDB Parquet and JSON tables."""
    
    def __init__(self, dataset_dir: str):
        self.dataset_dir = os.path.abspath(dataset_dir)
        self.manifest_path = os.path.join(self.dataset_dir, "dataset_manifest.json")
        
        try:
            import duckdb
            self.duckdb = duckdb
            self.duckdb_enabled = True
        except ImportError:
            self.duckdb_enabled = False
            
    def query(self, sql: str) -> List[Dict[str, Any]]:
        if not self.duckdb_enabled:
            # Simple Python-based query fallback for in-memory tables when duckdb is absent
            return self._python_fallback_query(sql)
            
        conn = self.duckdb.connect(database=":memory:")
        try:
            # Pre-register Parquet views if they exist, otherwise fallback to JSON
            manifest_data = {}
            if os.path.exists(self.manifest_path):
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    
            table_files = manifest_data.get("table_files", {})
            for table_name in ["runs", "run_features", "anomalies", "hard_law_violations"]:
                filename = table_files.get(table_name, f"{table_name}.json")
                file_path = os.path.join(self.dataset_dir, filename)
                if os.path.exists(file_path):
                    if filename.endswith(".parquet"):
                        conn.execute(f"CREATE VIEW {table_name} AS SELECT * FROM '{file_path}'")
                    else:
                        conn.execute(f"CREATE VIEW {table_name} AS SELECT * FROM read_json_auto('{file_path}')")
                        
            relation = conn.execute(sql)
            columns = [desc[0] for desc in relation.description]
            rows = relation.fetchall()
            
            results = []
            for row in rows:
                row_dict = {}
                for col_name, val in zip(columns, row):
                    if hasattr(val, "item"):
                        val = val.item()
                    row_dict[col_name] = val
                results.append(row_dict)
            return results
        finally:
            conn.close()
            
    def _python_fallback_query(self, sql: str) -> List[Dict[str, Any]]:
        sql_lower = sql.lower()
        
        # Load tables on-demand
        def load_table(name: str) -> List[Dict[str, Any]]:
            path = os.path.join(self.dataset_dir, f"{name}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
            
        if "from run_features" in sql_lower:
            data = load_table("run_features")
            data.sort(key=lambda x: (x.get("health_score", 100.0), -x.get("hard_law_violation_count", 0), -x.get("anomaly_count", 0)))
            return data[:10]
            
        elif "from anomalies" in sql_lower:
            anoms = load_table("anomalies")
            if "group by domain" in sql_lower:
                # Domain Clusters query
                counts = {}
                affected_runs = {}
                for row in anoms:
                    dom = row.get("domain", "unknown")
                    counts[dom] = counts.get(dom, 0) + 1
                    affected_runs.setdefault(dom, set()).add(row.get("run_id"))
                results = []
                for dom in counts:
                    results.append({
                        "domain": dom,
                        "anomaly_count": counts[dom],
                        "affected_runs": len(affected_runs[dom])
                    })
                results.sort(key=lambda x: x["anomaly_count"], reverse=True)
                return results
                
            elif "group by tick_bucket" in sql_lower or "tick / 1000" in sql_lower:
                # Temporal Patterns query
                counts = {}
                for row in anoms:
                    tick = row.get("tick", 0)
                    bucket = (tick // 1000) * 1000
                    counts[bucket] = counts.get(bucket, 0) + 1
                results = []
                for bucket in counts:
                    results.append({
                        "tick_bucket": bucket,
                        "anomaly_count": counts[bucket]
                    })
                results.sort(key=lambda x: x["anomaly_count"], reverse=True)
                return results[:10]
                
            elif "message like" in sql_lower:
                # Hotspots query
                counts = {}
                for row in anoms:
                    msg = row.get("message", "")
                    if "entity" in msg.lower() or "node" in msg.lower() or "region" in msg.lower():
                        counts[msg] = counts.get(msg, 0) + 1
                results = []
                for msg in counts:
                    results.append({
                        "message": msg,
                        "count": counts[msg]
                    })
                results.sort(key=lambda x: x["count"], reverse=True)
                return results[:10]
                
            else:
                # Recurring Anomalies query
                # GROUP BY rule_id, severity, domain
                counts = {}
                affected_runs = {}
                severities = {}
                domains = {}
                
                for row in anoms:
                    r_id = row.get("rule_id", "unknown")
                    counts[r_id] = counts.get(r_id, 0) + 1
                    affected_runs.setdefault(r_id, set()).add(row.get("run_id"))
                    severities[r_id] = row.get("severity", "warning")
                    domains[r_id] = row.get("domain", "unknown")
                    
                results = []
                for r_id in counts:
                    results.append({
                        "rule_id": r_id,
                        "severity": severities[r_id],
                        "domain": domains[r_id],
                        "occurrence_count": counts[r_id],
                        "affected_runs": len(affected_runs[r_id])
                    })
                results.sort(key=lambda x: x["occurrence_count"], reverse=True)
                return results
                
        elif "from hard_law_violations" in sql_lower:
            return load_table("hard_law_violations")
            
        logger.warning(f"Complexity fallback triggered: returning empty array for direct custom sql query: {sql}")
        return []

