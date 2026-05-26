# Compliance IDs: OBS-050, OBS-051, OBS-052, OBS-053
from __future__ import annotations

import os
import uuid
import time
import json
import shutil
import logging
from typing import Dict, List, Optional, Any, Type, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic schemas for Export jobs & manifests
class ExportJob(BaseModel):
    export_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    source_run_id: Optional[str] = None
    source_sweep_id: Optional[str] = None
    source_path: str
    output_path: str
    format: Literal["jsonl", "parquet"]
    artifact_types: List[str]
    created_at: float = Field(default_factory=time.time)
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"] = "PENDING"
    errors: List[str] = Field(default_factory=list)

class ExportManifest(BaseModel):
    export_id: str
    source_run_id: Optional[str] = None
    source_sweep_id: Optional[str] = None
    format: str
    artifact_types: List[str]
    output_files: Dict[str, str] = Field(default_factory=dict)
    record_counts: Dict[str, int] = Field(default_factory=dict)
    skipped_artifacts: List[str] = Field(default_factory=list)
    schema_version: str = "export_manifest_v1"
    created_at: float = Field(default_factory=time.time)
    status: str = "COMPLETED"

class ArtifactExporter:
    """Base interface for specialized storage format exporters."""
    
    def export_run(
        self,
        run_id: str,
        source_dir: str,
        dest_dir: str,
        artifact_types: List[str]
    ) -> tuple[Dict[str, str], Dict[str, int], List[str]]:
        """
        Exports a single simulation run.
        Returns: (output_files, record_counts, skipped_artifacts)
        """
        raise NotImplementedError

    def export_sweep(
        self,
        sweep_id: str,
        source_dir: str,
        dest_dir: str,
        artifact_types: List[str]
    ) -> tuple[Dict[str, str], Dict[str, int], List[str]]:
        """
        Exports an entire scenario sweep of runs.
        Returns: (output_files, record_counts, skipped_artifacts)
        """
        raise NotImplementedError


class JSONLArtifactExporter(ArtifactExporter):
    """Exporter for keeping files in their raw JSON/JSONL representation."""

    def _copy_or_skip(
        self,
        src_path: str,
        dest_path: str,
        key: str,
        output_files: Dict[str, str],
        record_counts: Dict[str, int],
        skipped_artifacts: List[str],
        is_jsonl: bool = True
    ) -> None:
        if not os.path.exists(src_path):
            skipped_artifacts.append(key)
            return

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        
        # Determine record count
        count = 0
        try:
            if is_jsonl:
                with open(src_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            count += 1
            else:
                with open(src_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else 1
        except Exception:
            count = 1

        output_files[key] = os.path.relpath(dest_path, os.path.dirname(dest_path))
        record_counts[key] = count

    def export_run(
        self,
        run_id: str,
        source_dir: str,
        dest_dir: str,
        artifact_types: List[str]
    ) -> tuple[Dict[str, str], Dict[str, int], List[str]]:
        output_files = {}
        record_counts = {}
        skipped_artifacts = []

        mappings = {
            "simulation_events": ("simulation_events.jsonl", True),
            "metric_windows": ("metric_windows.jsonl", True),
            "hard_law_violations": ("hard_law_violations.jsonl", True),
            "anomalies": ("anomalies.json", False),
            "run_manifest": ("run_manifest.json", False),
            "run_report_json": ("run_report.json", False),
        }

        for atype in artifact_types:
            if atype not in mappings:
                skipped_artifacts.append(atype)
                continue
            fname, is_jsonl = mappings[atype]
            src = os.path.join(source_dir, fname)
            dest = os.path.join(dest_dir, fname)
            self._copy_or_skip(src, dest, atype, output_files, record_counts, skipped_artifacts, is_jsonl)

        return output_files, record_counts, skipped_artifacts

    def export_sweep(
        self,
        sweep_id: str,
        source_dir: str,
        dest_dir: str,
        artifact_types: List[str]
    ) -> tuple[Dict[str, str], Dict[str, int], List[str]]:
        output_files = {}
        record_counts = {}
        skipped_artifacts = []

        # Sweep-level files
        sweep_mappings = {
            "run_index": ("run_index.jsonl", True),
            "sweep_summary": ("sweep_summary.json", False),
            "baseline": ("baseline.json", False),
        }

        for atype in artifact_types:
            if atype in sweep_mappings:
                fname, is_jsonl = sweep_mappings[atype]
                src = os.path.join(source_dir, fname)
                dest = os.path.join(dest_dir, fname)
                self._copy_or_skip(src, dest, atype, output_files, record_counts, skipped_artifacts, is_jsonl)

        # Export individual runs inside the sweep
        runs_dir = os.path.join(source_dir, "runs")
        if os.path.exists(runs_dir):
            for rid in os.listdir(runs_dir):
                run_src = os.path.join(runs_dir, rid)
                if os.path.isdir(run_src):
                    run_dest = os.path.join(dest_dir, "runs", rid)
                    o_files, r_counts, skipped = self.export_run(rid, run_src, run_dest, artifact_types)
                    for k, val in o_files.items():
                        output_files[f"runs/{rid}/{k}"] = os.path.join("runs", rid, val)
                        record_counts[f"runs/{rid}/{k}"] = r_counts[k]
                    skipped_artifacts.extend([f"runs/{rid}/{s}" for s in skipped])

        return output_files, record_counts, skipped_artifacts


class ParquetArtifactExporter(ArtifactExporter):
    """Exporter for packing simulation and sweep events into typing-strict Parquet files using PyArrow."""

    def __init__(self) -> None:
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
                "Optional dependency 'pyarrow' is required for exporting to Parquet format. "
                "Please make sure pyarrow is installed in the current environment."
            )

    def _convert_events_to_parquet(self, src_path: str, dest_path: str) -> int:
        self._ensure_enabled()
        import json
        
        # Build schemas matching the database normalization specifications
        schema = self.pa.schema([
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

        cols: Dict[str, List[Any]] = {name: [] for name in schema.names}
        count = 0

        with open(src_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                
                cols["run_id"].append(str(data.get("run_id") or ""))
                cols["tick"].append(int(data.get("tick") or 0))
                cols["event_type"].append(str(data.get("event_type") or ""))
                cols["event_category"].append(str(data.get("event_category") or ""))
                cols["severity"].append(str(data.get("severity") or "INFO"))
                
                ent_id = data.get("entity_id")
                cols["entity_id"].append(int(ent_id) if ent_id is not None else None)
                
                cols["region_id"].append(data.get("region_id"))
                cols["quest_id"].append(data.get("quest_id"))
                cols["message"].append(str(data.get("message") or ""))
                
                payload = data.get("payload") or {}
                cols["payload_json"].append(json.dumps(payload))
                count += 1

        if count > 0:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            table = self.pa.Table.from_pydict(cols, schema=schema)
            self.pq.write_table(table, dest_path)
            
        return count

    def _convert_metric_windows_to_parquet(self, src_path: str, dest_path: str) -> int:
        self._ensure_enabled()
        import json
        
        schema = self.pa.schema([
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

        cols: Dict[str, List[Any]] = {name: [] for name in schema.names}
        count = 0

        with open(src_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                
                cols["run_id"].append(str(data.get("run_id") or ""))
                cols["window_start_tick"].append(int(data.get("window_start_tick") or 0))
                cols["window_end_tick"].append(int(data.get("window_end_tick") or 0))
                cols["tick_compute_ms_avg"].append(float(data.get("tick_compute_ms_avg") or 0.0))
                cols["tick_compute_ms_p95"].append(float(data.get("tick_compute_ms_p95") or 0.0))
                cols["memory_rss_bytes_avg"].append(float(data.get("memory_rss_bytes_avg") or 0.0))
                cols["memory_rss_bytes_max"].append(float(data.get("memory_rss_bytes_max") or 0.0))
                cols["alive_entities_avg"].append(float(data.get("alive_entities_avg") or 0.0))
                cols["gold_total_avg"].append(float(data.get("gold_total_avg") or 0.0))
                cols["event_count"].append(int(data.get("event_count") or 0))
                cols["hard_law_violation_count"].append(int(data.get("hard_law_violation_count") or 0))
                count += 1

        if count > 0:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            table = self.pa.Table.from_pydict(cols, schema=schema)
            self.pq.write_table(table, dest_path)
            
        return count

    def _convert_anomalies_to_parquet(self, src_path: str, dest_path: str) -> int:
        self._ensure_enabled()
        import json
        
        schema = self.pa.schema([
            ("run_id", self.pa.string()),
            ("rule_id", self.pa.string()),
            ("severity", self.pa.string()),
            ("domain", self.pa.string()),
            ("tick_start", self.pa.int64()),
            ("tick_end", self.pa.int64()),
            ("affected_entity_count", self.pa.int64()),
            ("message", self.pa.string()),
        ])

        cols: Dict[str, List[Any]] = {name: [] for name in schema.names}
        count = 0

        with open(src_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]
                
            for item in data:
                # Find run_id
                ctx = item.get("context") or {}
                rid = ctx.get("run_id") or ""
                
                cols["run_id"].append(str(rid))
                cols["rule_id"].append(str(item.get("rule_name") or ""))
                cols["severity"].append(str(item.get("severity") or "WARNING"))
                cols["domain"].append(str(ctx.get("domain") or "simulation"))
                cols["tick_start"].append(int(item.get("tick_detected") or 0))
                cols["tick_end"].append(int(item.get("tick_detected") or 0))
                
                ent = item.get("entity_id")
                cols["affected_entity_count"].append(1 if ent is not None else 0)
                cols["message"].append(str(item.get("message") or ""))
                count += 1

        if count > 0:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            table = self.pa.Table.from_pydict(cols, schema=schema)
            self.pq.write_table(table, dest_path)
            
        return count

    def _convert_violations_to_parquet(self, src_path: str, dest_path: str) -> int:
        self._ensure_enabled()
        import json
        
        schema = self.pa.schema([
            ("run_id", self.pa.string()),
            ("tick", self.pa.int64()),
            ("law_id", self.pa.string()),
            ("severity", self.pa.string()),
            ("message", self.pa.string()),
        ])

        cols: Dict[str, List[Any]] = {name: [] for name in schema.names}
        count = 0

        with open(src_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                
                cols["run_id"].append(str(data.get("run_id") or ""))
                cols["tick"].append(int(data.get("tick") or 0))
                cols["law_id"].append(str(data.get("event_type") or "InvariantViolation"))
                cols["severity"].append(str(data.get("severity") or "CRITICAL"))
                cols["message"].append(str(data.get("message") or ""))
                count += 1

        if count > 0:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            table = self.pa.Table.from_pydict(cols, schema=schema)
            self.pq.write_table(table, dest_path)
            
        return count

    def _convert_run_manifest_to_parquet(self, src_path: str, dest_path: str) -> int:
        self._ensure_enabled()
        import json
        
        schema = self.pa.schema([
            ("run_id", self.pa.string()),
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

        cols: Dict[str, List[Any]] = {name: [] for name in schema.names}

        with open(src_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        cols["run_id"].append(str(data.get("run_id") or ""))
        cols["scenario_name"].append(str(data.get("scenario_name") or ""))
        cols["scenario_type"].append(str(data.get("scenario_type") or ""))
        cols["seed"].append(int(data.get("seed") or 0))
        cols["status"].append(str(data.get("status") or "CREATED"))
        cols["ticks_completed"].append(int(data.get("ticks_completed") or 0))
        
        cols["health_score"].append(100.0)
        cols["critical_count"].append(0)
        cols["warning_count"].append(0)
        
        cols["started_at"].append(str(data.get("started_at") or ""))
        cols["ended_at"].append(str(data.get("ended_at") or ""))

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        table = self.pa.Table.from_pydict(cols, schema=schema)
        self.pq.write_table(table, dest_path)
        return 1

    def _convert_run_index_to_parquet(self, src_path: str, dest_path: str) -> int:
        self._ensure_enabled()
        import json
        
        schema = self.pa.schema([
            ("sweep_id", self.pa.string()),
            ("run_id", self.pa.string()),
            ("seed", self.pa.int64()),
            ("scenario_name", self.pa.string()),
            ("scenario_type", self.pa.string()),
            ("status", self.pa.string()),
            ("ticks_completed", self.pa.int64()),
            ("health_score", self.pa.float64()),
            ("critical_count", self.pa.int64()),
            ("warning_count", self.pa.int64()),
            ("hard_law_violation_count", self.pa.int64()),
        ])

        cols: Dict[str, List[Any]] = {name: [] for name in schema.names}
        count = 0

        with open(src_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                
                cols["sweep_id"].append(str(data.get("sweep_id") or ""))
                cols["run_id"].append(str(data.get("run_id") or ""))
                cols["seed"].append(int(data.get("seed") or 0))
                cols["scenario_name"].append(str(data.get("scenario_name") or ""))
                cols["scenario_type"].append(str(data.get("scenario_type") or ""))
                cols["status"].append(str(data.get("status") or "COMPLETED"))
                cols["ticks_completed"].append(int(data.get("ticks_completed") or 0))
                cols["health_score"].append(float(data.get("health_score") or 0.0))
                cols["critical_count"].append(int(data.get("critical_count") or 0))
                cols["warning_count"].append(int(data.get("warning_count") or 0))
                cols["hard_law_violation_count"].append(int(data.get("hard_law_violation_count") or 0))
                count += 1

        if count > 0:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            table = self.pa.Table.from_pydict(cols, schema=schema)
            self.pq.write_table(table, dest_path)
            
        return count

    def export_run(
        self,
        run_id: str,
        source_dir: str,
        dest_dir: str,
        artifact_types: List[str]
    ) -> tuple[Dict[str, str], Dict[str, int], List[str]]:
        if not self.enabled:
            logger.warning("pyarrow is not installed in the environment. Falling back to JSONL format for export.")
            jsonl_exporter = JSONLArtifactExporter()
            return jsonl_exporter.export_run(run_id, source_dir, dest_dir, artifact_types)

        self._ensure_enabled()
        
        output_files = {}
        record_counts = {}
        skipped_artifacts = []

        mappings = {
            "simulation_events": ("simulation_events.jsonl", "simulation_events.parquet", self._convert_events_to_parquet),
            "metric_windows": ("metric_windows.jsonl", "metric_windows.parquet", self._convert_metric_windows_to_parquet),
            "hard_law_violations": ("hard_law_violations.jsonl", "hard_law_violations.parquet", self._convert_violations_to_parquet),
            "anomalies": ("anomalies.json", "anomalies.parquet", self._convert_anomalies_to_parquet),
            "run_manifest": ("run_manifest.json", "run_manifest.parquet", self._convert_run_manifest_to_parquet),
        }

        for atype in artifact_types:
            if atype not in mappings:
                skipped_artifacts.append(atype)
                continue
            
            src_fname, dest_fname, convert_func = mappings[atype]
            src = os.path.join(source_dir, src_fname)
            dest = os.path.join(dest_dir, dest_fname)

            if not os.path.exists(src):
                skipped_artifacts.append(atype)
                continue

            try:
                count = convert_func(src, dest)
                output_files[atype] = os.path.relpath(dest, os.path.dirname(dest))
                record_counts[atype] = count
            except Exception as e:
                logger.error(f"Failed exporting run artifact '{atype}' to Parquet: {e}")
                skipped_artifacts.append(atype)

        return output_files, record_counts, skipped_artifacts

    def export_sweep(
        self,
        sweep_id: str,
        source_dir: str,
        dest_dir: str,
        artifact_types: List[str]
    ) -> tuple[Dict[str, str], Dict[str, int], List[str]]:
        if not self.enabled:
            logger.warning("pyarrow is not installed in the environment. Falling back to JSONL format for export.")
            jsonl_exporter = JSONLArtifactExporter()
            return jsonl_exporter.export_sweep(sweep_id, source_dir, dest_dir, artifact_types)

        self._ensure_enabled()

        output_files = {}
        record_counts = {}
        skipped_artifacts = []

        # Sweep-level files
        sweep_mappings = {
            "run_index": ("run_index.jsonl", "run_index.parquet", self._convert_run_index_to_parquet),
        }

        for atype in artifact_types:
            if atype in sweep_mappings:
                src_fname, dest_fname, convert_func = sweep_mappings[atype]
                src = os.path.join(source_dir, src_fname)
                dest = os.path.join(dest_dir, dest_fname)

                if not os.path.exists(src):
                    skipped_artifacts.append(atype)
                    continue

                try:
                    count = convert_func(src, dest)
                    output_files[atype] = os.path.relpath(dest, os.path.dirname(dest))
                    record_counts[atype] = count
                except Exception as e:
                    logger.error(f"Failed exporting sweep artifact '{atype}' to Parquet: {e}")
                    skipped_artifacts.append(atype)

        # Export individual runs inside the sweep
        runs_dir = os.path.join(source_dir, "runs")
        if os.path.exists(runs_dir):
            for rid in os.listdir(runs_dir):
                run_src = os.path.join(runs_dir, rid)
                if os.path.isdir(run_src):
                    run_dest = os.path.join(dest_dir, "runs", rid)
                    o_files, r_counts, skipped = self.export_run(rid, run_src, run_dest, artifact_types)
                    for k, val in o_files.items():
                        output_files[f"runs/{rid}/{k}"] = os.path.join("runs", rid, val)
                        record_counts[f"runs/{rid}/{k}"] = r_counts[k]
                    skipped_artifacts.extend([f"runs/{rid}/{s}" for s in skipped])

        return output_files, record_counts, skipped_artifacts


# Registry logic
_EXPORTERS: Dict[str, Type[ArtifactExporter]] = {
    "jsonl": JSONLArtifactExporter,
    "parquet": ParquetArtifactExporter,
}

def register_exporter(format_name: str, exporter_class: Type[ArtifactExporter]) -> None:
    _EXPORTERS[format_name.lower()] = exporter_class

def get_exporter(format_name: str) -> ArtifactExporter:
    fmt = format_name.lower()
    if fmt not in _EXPORTERS:
        raise ValueError(f"Unsupported export format: {format_name}. Supported formats: {list(_EXPORTERS.keys())}")
    return _EXPORTERS[fmt]()


class ExportManager:
    """Manages the full lifecycle of an export job."""

    def __init__(self, base_export_dir: str = "data/exports"):
        self.base_export_dir = os.path.abspath(base_export_dir)

    def execute_job(self, job: ExportJob) -> ExportManifest:
        job.status = "RUNNING"
        manifest_path = os.path.join(self.base_export_dir, job.export_id, "export_manifest.json")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)

        try:
            exporter = get_exporter(job.format)
            
            if job.source_run_id:
                o_files, r_counts, skipped = exporter.export_run(
                    run_id=job.source_run_id,
                    source_dir=job.source_path,
                    dest_dir=job.output_path,
                    artifact_types=job.artifact_types
                )
                manifest = ExportManifest(
                    export_id=job.export_id,
                    source_run_id=job.source_run_id,
                    format=job.format,
                    artifact_types=job.artifact_types,
                    output_files=o_files,
                    record_counts=r_counts,
                    skipped_artifacts=skipped,
                    status="COMPLETED"
                )
            elif job.source_sweep_id:
                o_files, r_counts, skipped = exporter.export_sweep(
                    sweep_id=job.source_sweep_id,
                    source_dir=job.source_path,
                    dest_dir=job.output_path,
                    artifact_types=job.artifact_types
                )
                manifest = ExportManifest(
                    export_id=job.export_id,
                    source_sweep_id=job.source_sweep_id,
                    format=job.format,
                    artifact_types=job.artifact_types,
                    output_files=o_files,
                    record_counts=r_counts,
                    skipped_artifacts=skipped,
                    status="COMPLETED"
                )
            else:
                raise ValueError("Either source_run_id or source_sweep_id must be specified.")

            # Write manifest JSON
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(manifest.model_dump_json(indent=2))

            job.status = "COMPLETED"
            return manifest

        except Exception as e:
            job.status = "FAILED"
            job.errors.append(str(e))
            logger.error(f"Export Job {job.export_id} failed: {e}")
            
            manifest = ExportManifest(
                export_id=job.export_id,
                source_run_id=job.source_run_id,
                source_sweep_id=job.source_sweep_id,
                format=job.format,
                artifact_types=job.artifact_types,
                skipped_artifacts=job.artifact_types,
                status="FAILED"
            )
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(manifest.model_dump_json(indent=2))
            raise
