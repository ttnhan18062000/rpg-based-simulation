# Compliance IDs: OBS-055, OBS-056, OBS-057
from __future__ import annotations

import os
import uuid
import time
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DatasetManifest(BaseModel):
    dataset_id: str
    source_sweep_id: str
    table_files: Dict[str, str] = Field(default_factory=dict)
    record_counts: Dict[str, int] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class AnalyticsDatasetBuilder:
    """Consolidates scenario sweep artifacts and individual run data into a local Parquet dataset."""

    def __init__(self, base_analytics_dir: str = "data/analytics"):
        self.base_analytics_dir = os.path.abspath(base_analytics_dir)
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            self.pa = pa
            self.pq = pq
            self.enabled = True
        except ImportError:
            self.enabled = False

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise ImportError(
                "Optional dependency 'pyarrow' is required to compile Parquet datasets. "
                "Please verify pyarrow is installed in the current environment."
            )

    def build_dataset(self, sweep_id: str, source_sweep_dir: str, dataset_id: Optional[str] = None) -> DatasetManifest:
        self._ensure_enabled()
        if not dataset_id:
            dataset_id = f"ds_{sweep_id}_{uuid.uuid4().hex[:8]}"

        dest_dir = os.path.join(self.base_analytics_dir, dataset_id)
        os.makedirs(dest_dir, exist_ok=True)

        logger.info(f"Building analytics dataset '{dataset_id}' from sweep '{sweep_id}'...")

        # PyArrow Schemas
        run_schema = self.pa.schema([
            ("run_id", self.pa.string()),
            ("sweep_id", self.pa.string()),
            ("scenario_name", self.pa.string()),
            ("scenario_type", self.pa.string()),
            ("seed", self.pa.int64()),
            ("status", self.pa.string()),
            ("ticks_completed", self.pa.int64()),
            ("health_score", self.pa.float64()),
            ("critical_count", self.pa.int64()),
            ("warning_count", self.pa.int64()),
            ("started_at", self.pa.string()),
            ("ended_at", self.pa.string()),
        ])

        metrics_schema = self.pa.schema([
            ("run_id", self.pa.string()),
            ("window_start_tick", self.pa.int64()),
            ("window_end_tick", self.pa.int64()),
            ("tick_compute_ms_avg", self.pa.float64()),
            ("tick_compute_ms_p95", self.pa.float64()),
            ("memory_rss_bytes_avg", self.pa.float64()),
            ("memory_rss_bytes_max", self.pa.float64()),
            ("alive_entities_avg", self.pa.float64()),
            ("gold_total_avg", self.pa.float64()),
            ("event_count", self.pa.int64()),
            ("hard_law_violation_count", self.pa.int64()),
        ])

        anomaly_schema = self.pa.schema([
            ("run_id", self.pa.string()),
            ("rule_id", self.pa.string()),
            ("severity", self.pa.string()),
            ("domain", self.pa.string()),
            ("tick_start", self.pa.int64()),
            ("tick_end", self.pa.int64()),
            ("affected_entity_count", self.pa.int64()),
            ("message", self.pa.string()),
        ])

        event_schema = self.pa.schema([
            ("run_id", self.pa.string()),
            ("tick", self.pa.int64()),
            ("event_type", self.pa.string()),
            ("event_category", self.pa.string()),
            ("severity", self.pa.string()),
            ("entity_id", self.pa.int64()),
            ("region_id", self.pa.string()),
            ("quest_id", self.pa.string()),
            ("message", self.pa.string()),
            ("payload_json", self.pa.string()),
        ])

        # Tables columns accumulators
        runs_cols: Dict[str, List[Any]] = {n: [] for n in run_schema.names}
        metrics_cols: Dict[str, List[Any]] = {n: [] for n in metrics_schema.names}
        anomalies_cols: Dict[str, List[Any]] = {n: [] for n in anomaly_schema.names}
        events_cols: Dict[str, List[Any]] = {n: [] for n in event_schema.names}

        # 1. Read runs inside this sweep
        runs_dir = os.path.join(source_sweep_dir, "runs")
        run_ids = []
        if os.path.exists(runs_dir):
            run_ids = [d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))]

        # Let's also parse the sweep run_index if it exists
        index_path = os.path.join(source_sweep_dir, "run_index.jsonl")
        index_data: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            d = json.loads(line)
                            if "run_id" in d:
                                index_data[d["run_id"]] = d
            except Exception as e:
                logger.warning(f"Failed parsing run_index.jsonl: {e}")

        # Iterate runs
        for rid in run_ids:
            run_path = os.path.join(runs_dir, rid)
            manifest_path = os.path.join(run_path, "run_manifest.json")
            
            # Load basic info
            scenario_name = ""
            scenario_type = ""
            seed = 0
            status = "COMPLETED"
            ticks = 0
            started = ""
            ended = ""
            health = 100.0
            crit = 0
            warn = 0

            # Override with index details if available
            if rid in index_data:
                idx_row = index_data[rid]
                scenario_name = idx_row.get("scenario_name") or ""
                scenario_type = idx_row.get("scenario_type") or ""
                seed = idx_row.get("seed") or 0
                status = idx_row.get("status") or "COMPLETED"
                ticks = idx_row.get("ticks_completed") or 0
                health = idx_row.get("health_score") or 100.0
                crit = idx_row.get("critical_count") or 0
                warn = idx_row.get("warning_count") or 0

            # Read manifest directly
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                        scenario_name = m_data.get("scenario_name") or scenario_name
                        scenario_type = m_data.get("scenario_type") or scenario_type
                        seed = m_data.get("seed") or seed
                        status = m_data.get("status") or status
                        ticks = m_data.get("ticks_completed") or ticks
                        started = m_data.get("started_at") or started
                        ended = m_data.get("ended_at") or ended
                        
                        # Populate health summary metrics if in manifest
                        if "health_score" in m_data:
                            health = m_data["health_score"]
                        if "critical_count" in m_data:
                            crit = m_data["critical_count"]
                        if "warning_count" in m_data:
                            warn = m_data["warning_count"]
                except Exception as e:
                    logger.warning(f"Error parsing run_manifest.json for {rid}: {e}")

            # Append run row
            runs_cols["run_id"].append(rid)
            runs_cols["sweep_id"].append(sweep_id)
            runs_cols["scenario_name"].append(scenario_name)
            runs_cols["scenario_type"].append(scenario_type)
            runs_cols["seed"].append(seed)
            runs_cols["status"].append(status)
            runs_cols["ticks_completed"].append(ticks)
            runs_cols["health_score"].append(health)
            runs_cols["critical_count"].append(crit)
            runs_cols["warning_count"].append(warn)
            runs_cols["started_at"].append(started)
            runs_cols["ended_at"].append(ended)

            # 2. Parse metric windows
            metrics_path = os.path.join(run_path, "metric_windows.jsonl")
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            d = json.loads(line)
                            metrics_cols["run_id"].append(rid)
                            metrics_cols["window_start_tick"].append(int(d.get("window_start_tick") or 0))
                            metrics_cols["window_end_tick"].append(int(d.get("window_end_tick") or 0))
                            metrics_cols["tick_compute_ms_avg"].append(float(d.get("tick_compute_ms_avg") or 0.0))
                            metrics_cols["tick_compute_ms_p95"].append(float(d.get("tick_compute_ms_p95") or 0.0))
                            metrics_cols["memory_rss_bytes_avg"].append(float(d.get("memory_rss_bytes_avg") or 0.0))
                            metrics_cols["memory_rss_bytes_max"].append(float(d.get("memory_rss_bytes_max") or 0.0))
                            metrics_cols["alive_entities_avg"].append(float(d.get("alive_entities_avg") or 0.0))
                            metrics_cols["gold_total_avg"].append(float(d.get("gold_total_avg") or 0.0))
                            metrics_cols["event_count"].append(int(d.get("event_count") or 0))
                            metrics_cols["hard_law_violation_count"].append(int(d.get("hard_law_violation_count") or 0))
                except Exception as e:
                    logger.warning(f"Error parsing metric windows for {rid}: {e}")

            # 3. Parse anomalies
            anomalies_path = os.path.join(run_path, "anomalies.json")
            if os.path.exists(anomalies_path):
                try:
                    with open(anomalies_path, "r", encoding="utf-8") as f:
                        a_data = json.load(f)
                        if not isinstance(a_data, list):
                            a_data = [a_data]
                        for a in a_data:
                            ctx = a.get("context") or {}
                            anomalies_cols["run_id"].append(rid)
                            anomalies_cols["rule_id"].append(str(a.get("rule_name") or ""))
                            anomalies_cols["severity"].append(str(a.get("severity") or "WARNING"))
                            anomalies_cols["domain"].append(str(ctx.get("domain") or "simulation"))
                            anomalies_cols["tick_start"].append(int(a.get("tick_detected") or 0))
                            anomalies_cols["tick_end"].append(int(a.get("tick_detected") or 0))
                            
                            ent = a.get("entity_id")
                            anomalies_cols["affected_entity_count"].append(1 if ent is not None else 0)
                            anomalies_cols["message"].append(str(a.get("message") or ""))
                except Exception as e:
                    logger.warning(f"Error parsing anomalies for {rid}: {e}")

            # 4. Parse simulation events
            events_path = os.path.join(run_path, "simulation_events.jsonl")
            if os.path.exists(events_path):
                try:
                    with open(events_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            d = json.loads(line)
                            events_cols["run_id"].append(rid)
                            events_cols["tick"].append(int(d.get("tick") or 0))
                            events_cols["event_type"].append(str(d.get("event_type") or ""))
                            events_cols["event_category"].append(str(d.get("event_category") or ""))
                            events_cols["severity"].append(str(d.get("severity") or "INFO"))
                            
                            ent_id = d.get("entity_id")
                            events_cols["entity_id"].append(int(ent_id) if ent_id is not None else None)
                            
                            events_cols["region_id"].append(d.get("region_id"))
                            events_cols["quest_id"].append(d.get("quest_id"))
                            events_cols["message"].append(str(d.get("message") or ""))
                            
                            payload = d.get("payload") or {}
                            events_cols["payload_json"].append(json.dumps(payload))
                except Exception as e:
                    logger.warning(f"Error parsing events for {rid}: {e}")

        # Compile and save Parquet files
        table_files = {}
        record_counts = {}

        # Save runs
        runs_path = os.path.join(dest_dir, "runs.parquet")
        runs_table = self.pa.Table.from_pydict(runs_cols, schema=run_schema)
        self.pq.write_table(runs_table, runs_path)
        table_files["runs"] = os.path.relpath(runs_path, dest_dir)
        record_counts["runs"] = len(runs_cols["run_id"])

        # Save metrics
        metrics_path = os.path.join(dest_dir, "metric_windows.parquet")
        metrics_table = self.pa.Table.from_pydict(metrics_cols, schema=metrics_schema)
        self.pq.write_table(metrics_table, metrics_path)
        table_files["metric_windows"] = os.path.relpath(metrics_path, dest_dir)
        record_counts["metric_windows"] = len(metrics_cols["run_id"])

        # Save anomalies
        anomalies_path = os.path.join(dest_dir, "anomalies.parquet")
        anomalies_table = self.pa.Table.from_pydict(anomalies_cols, schema=anomaly_schema)
        self.pq.write_table(anomalies_table, anomalies_path)
        table_files["anomalies"] = os.path.relpath(anomalies_path, dest_dir)
        record_counts["anomalies"] = len(anomalies_cols["run_id"])

        # Save events
        events_path = os.path.join(dest_dir, "simulation_events.parquet")
        events_table = self.pa.Table.from_pydict(events_cols, schema=event_schema)
        self.pq.write_table(events_table, events_path)
        table_files["simulation_events"] = os.path.relpath(events_path, dest_dir)
        record_counts["simulation_events"] = len(events_cols["run_id"])

        # Save manifest
        manifest = DatasetManifest(
            dataset_id=dataset_id,
            source_sweep_id=sweep_id,
            table_files=table_files,
            record_counts=record_counts
        )

        manifest_path = os.path.join(dest_dir, "dataset_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        logger.info(f"Successfully compiled analytics dataset '{dataset_id}' with {record_counts['runs']} runs!")
        return manifest
