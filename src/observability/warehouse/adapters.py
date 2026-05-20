from __future__ import annotations
import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.observability.warehouse.base import WarehouseAdapter
from src.observability.warehouse.models import (
    RunRecord,
    SweepRecord,
    EventRecord,
    MetricWindowRecord,
    AnomalyRecord,
    HardLawViolationRecord,
    BaselineRecord,
    ComparisonRecord,
    WarehouseIngestionResult,
    WarehouseHealthStatus
)
from src.observability.warehouse.registry import WarehouseSchemaRegistry
from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.observability.reporting.run_set_repository import RunSetArtifactRepository

class NullWarehouseAdapter(WarehouseAdapter):
    """No-op adapter that silently drops ingestions and queries."""

    def ingest_run(self, run_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        return WarehouseIngestionResult(
            ingestion_id=str(uuid.uuid4()),
            run_id=run_id,
            status="DRY_RUN" if dry_run else "COMPLETED",
            records_ingested={"runs": 1},
            duration_ms=0.0
        )

    def ingest_sweep(self, sweep_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        return WarehouseIngestionResult(
            ingestion_id=str(uuid.uuid4()),
            sweep_id=sweep_id,
            status="DRY_RUN" if dry_run else "COMPLETED",
            records_ingested={"sweeps": 1},
            duration_ms=0.0
        )

    def query_runs(self, filters: Dict[str, Any]) -> List[RunRecord]:
        return []

    def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
        return []

    def query_anomalies(self, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        return []

    def query_metric_windows(self, filters: Dict[str, Any]) -> List[MetricWindowRecord]:
        return []

    def query_violations(self, filters: Dict[str, Any]) -> List[HardLawViolationRecord]:
        return []

    def health(self) -> WarehouseHealthStatus:
        return WarehouseHealthStatus(connected=True, latency_ms=0.0)

    def close(self) -> None:
        pass


class LocalWarehouseAdapter(WarehouseAdapter):
    """
    Local repository adapter designed for dry-run ingestion pipelines.
    Parses local JSON/JSONL runs and sweep directories, translates them into the concrete Pydantic database models,
    validates schema version constraints, and returns diagnostic metrics.
    """

    def __init__(
        self,
        run_repo: Optional[RunArtifactRepository] = None,
        sweep_repo: Optional[RunSetArtifactRepository] = None
    ):
        self.run_repo = run_repo or RunArtifactRepository()
        self.sweep_repo = sweep_repo or RunSetArtifactRepository()

    def ingest_run(self, run_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        start_time = time.perf_counter()
        ingestion_id = str(uuid.uuid4())
        records_count = {
            "runs": 0,
            "events": 0,
            "anomalies": 0,
            "violations": 0,
            "metrics": 0
        }
        errors = []

        try:
            # 1. Load run manifest
            manifest_path = self.run_repo.resolve_path(run_id, "manifest")
            if not os.path.exists(manifest_path):
                raise FileNotFoundError(f"Run manifest path not found: {manifest_path}")

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_dict = json.load(f)

            # 2. Validate artifact schema version
            WarehouseSchemaRegistry.validate_manifest(manifest_dict)

            # 3. Map to RunRecord
            run_rec = RunRecord(
                run_id=run_id,
                scenario_name=manifest_dict.get("scenario_name", "unknown"),
                scenario_type=manifest_dict.get("scenario_type", "unknown"),
                seed=manifest_dict.get("seed", 0),
                status=manifest_dict.get("status", "UNKNOWN"),
                ticks_completed=manifest_dict.get("ticks_completed", 0),
                health_score=manifest_dict.get("health_score", 100.0) if "health_score" in manifest_dict else 100.0,
                started_at=manifest_dict.get("started_at", ""),
                ended_at=manifest_dict.get("ended_at"),
                manifest_json=json.dumps(manifest_dict)
            )
            records_count["runs"] += 1

            # 4. Map events if available
            events_path = self.run_repo.resolve_path(run_id, "events")
            if os.path.exists(events_path):
                with open(events_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        event_dict = json.loads(line)
                        payload = event_dict.get("payload", {})
                        
                        # Extract event timestamps or default
                        created_at = event_dict.get("timestamp") or datetime.utcnow().isoformat()
                        
                        EventRecord(
                            run_id=run_id,
                            tick=event_dict.get("tick", 0),
                            event_type=event_dict.get("event_type", "unknown"),
                            event_category=event_dict.get("event_category", "unknown"),
                            severity=event_dict.get("severity", "INFO"),
                            entity_id=event_dict.get("entity_id"),
                            region_id=event_dict.get("region_id"),
                            quest_id=event_dict.get("quest_id"),
                            faction_id=event_dict.get("faction_id"),
                            message=event_dict.get("message", ""),
                            payload_json=json.dumps(payload),
                            created_at=created_at
                        )
                        records_count["events"] += 1

            # 5. Map violations if available
            violations_path = self.run_repo.resolve_path(run_id, "violations")
            if os.path.exists(violations_path):
                with open(violations_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        violation_dict = json.loads(line)
                        HardLawViolationRecord(
                            run_id=run_id,
                            tick=violation_dict.get("tick", 0),
                            violation_type=violation_dict.get("violation_type", "unknown"),
                            severity=violation_dict.get("severity", "CRITICAL"),
                            actor_id=violation_dict.get("actor_id"),
                            target_id=violation_dict.get("target_id"),
                            message=violation_dict.get("message", ""),
                            evidence_json=json.dumps(violation_dict.get("evidence", {}))
                        )
                        records_count["violations"] += 1

            # 6. Map anomalies if available
            anomalies_path = self.run_repo.resolve_path(run_id, "anomalies")
            if os.path.exists(anomalies_path):
                with open(anomalies_path, "r", encoding="utf-8") as f:
                    anomalies_list = json.load(f)
                    for anomaly_dict in anomalies_list:
                        AnomalyRecord(
                            run_id=run_id,
                            rule_id=anomaly_dict.get("rule_id", "unknown"),
                            severity=anomaly_dict.get("severity", "WARNING"),
                            domain=anomaly_dict.get("domain", "general"),
                            tick_start=anomaly_dict.get("tick_start", 0),
                            tick_end=anomaly_dict.get("tick_end", 0),
                            affected_entity_count=anomaly_dict.get("affected_entity_count", 0),
                            message=anomaly_dict.get("message", ""),
                            evidence_json=json.dumps(anomaly_dict.get("evidence", {}))
                        )
                        records_count["anomalies"] += 1

        except Exception as e:
            errors.append(str(e))
            status = "FAILED"
        else:
            status = "DRY_RUN" if dry_run else "COMPLETED"

        duration = (time.perf_counter() - start_time) * 1000.0
        return WarehouseIngestionResult(
            ingestion_id=ingestion_id,
            run_id=run_id,
            status=status,
            records_ingested=records_count,
            errors=errors,
            duration_ms=duration
        )

    def ingest_sweep(self, sweep_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        start_time = time.perf_counter()
        ingestion_id = str(uuid.uuid4())
        records_count = {
            "sweeps": 0,
            "runs": 0
        }
        errors = []

        try:
            # 1. Load run set manifest
            manifest_path = self.sweep_repo.resolve_path(sweep_id, "manifest")
            if not os.path.exists(manifest_path):
                raise FileNotFoundError(f"Sweep manifest path not found: {manifest_path}")

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_dict = json.load(f)

            # 2. Load sweep summary
            summary_path = self.sweep_repo.resolve_path(sweep_id, "summary")
            if not os.path.exists(summary_path):
                raise FileNotFoundError(f"Sweep summary path not found: {summary_path}")

            with open(summary_path, "r", encoding="utf-8") as f:
                summary_dict = json.load(f)

            # 3. Map to SweepRecord
            SweepRecord(
                sweep_id=sweep_id,
                scenario_name=summary_dict.get("scenario_name", "unknown"),
                scenario_type=summary_dict.get("scenario_type", "unknown"),
                total_runs=summary_dict.get("total_runs", 0),
                completed_runs=summary_dict.get("completed_runs", 0),
                failed_runs=summary_dict.get("failed_runs", 0),
                average_health_score=summary_dict.get("average_health_score", 100.0),
                created_at=datetime.utcnow().isoformat(),
                summary_json=json.dumps(summary_dict)
            )
            records_count["sweeps"] += 1

            # 4. Ingest children run indices
            run_indices = self.sweep_repo.read_run_index(sweep_id)
            for record in run_indices:
                # We can dry-run ingest each child run if the directory exists
                child_res = self.ingest_run(record.run_id, dry_run=True)
                if child_res.status == "FAILED":
                    errors.extend(child_res.errors)
                else:
                    records_count["runs"] += 1

        except Exception as e:
            errors.append(str(e))
            status = "FAILED"
        else:
            status = "DRY_RUN" if dry_run else "COMPLETED"

        duration = (time.perf_counter() - start_time) * 1000.0
        return WarehouseIngestionResult(
            ingestion_id=ingestion_id,
            sweep_id=sweep_id,
            status=status,
            records_ingested=records_count,
            errors=errors,
            duration_ms=duration
        )

    def query_runs(self, filters: Dict[str, Any]) -> List[RunRecord]:
        # Scans base_dir for run manifest summaries
        runs_dict = self.run_repo.list_runs()
        records = []
        for run_id, manifest in runs_dict.items():
            # Apply filters
            if "scenario_name" in filters and manifest.scenario_name != filters["scenario_name"]:
                continue
            if "status" in filters and manifest.status != filters["status"]:
                continue
            
            # Retrieve health_score from run_report.json if present
            health_score = 100.0
            try:
                report_path = self.run_repo.resolve_path(run_id, "report_json")
                if os.path.exists(report_path):
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                        health_score = report_data.get("metadata", {}).get("health_score", 100.0)
            except Exception:
                pass

            # Map manifest to RunRecord
            run_rec = RunRecord(
                run_id=run_id,
                scenario_name=manifest.scenario_name,
                scenario_type=manifest.scenario_type,
                seed=manifest.seed,
                status=manifest.status,
                ticks_completed=manifest.ticks_completed,
                health_score=health_score,
                started_at=manifest.started_at,
                ended_at=manifest.ended_at,
                manifest_json=manifest.model_dump_json()
            )
            records.append(run_rec)

        # Sort
        if "sort" in filters:
            if filters["sort"] == "health_score_asc":
                records.sort(key=lambda x: x.health_score)
            elif filters["sort"] == "health_score_desc":
                records.sort(key=lambda x: x.health_score, reverse=True)
            else:
                records.sort(key=lambda x: x.run_id, reverse=True)
        else:
            records.sort(key=lambda x: x.run_id, reverse=True)

        # Paginate
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        
        # Protect against path traversal using sanitize_id
        from src.observability.reporting.history_query import sanitize_id
        try:
            run_id = sanitize_id(run_id)
        except ValueError:
            return []

        events_path = self.run_repo.resolve_path(run_id, "events")
        if not os.path.exists(events_path):
            return []

        records = []
        with open(events_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event_dict = json.loads(line)
                    # Apply filters
                    if "entity_id" in filters and event_dict.get("entity_id") is not None:
                        if str(event_dict.get("entity_id")) != str(filters["entity_id"]):
                            continue
                    if "tick_start" in filters and event_dict.get("tick", 0) < int(filters["tick_start"]):
                        continue
                    if "tick_end" in filters and event_dict.get("tick", 0) > int(filters["tick_end"]):
                        continue
                    if "severity" in filters and event_dict.get("severity") != filters["severity"]:
                        continue

                    payload = event_dict.get("payload", {})
                    created_at = event_dict.get("timestamp") or datetime.utcnow().isoformat()
                    if isinstance(created_at, (int, float)):
                        created_at = datetime.fromtimestamp(created_at).isoformat()

                    rec = EventRecord(
                        run_id=run_id,
                        tick=event_dict.get("tick", 0),
                        event_type=event_dict.get("event_type", "unknown"),
                        event_category=event_dict.get("event_category", "unknown"),
                        severity=event_dict.get("severity", "INFO"),
                        entity_id=event_dict.get("entity_id"),
                        region_id=event_dict.get("region_id"),
                        quest_id=event_dict.get("quest_id"),
                        faction_id=event_dict.get("faction_id"),
                        message=event_dict.get("message", ""),
                        payload_json=json.dumps(payload),
                        created_at=created_at
                    )
                    records.append(rec)
                except Exception:
                    continue

        records.sort(key=lambda x: x.tick)
        
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_anomalies(self, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []

        from src.observability.reporting.history_query import sanitize_id
        try:
            run_id = sanitize_id(run_id)
        except ValueError:
            return []

        anomalies_path = self.run_repo.resolve_path(run_id, "anomalies")
        if not os.path.exists(anomalies_path):
            return []

        records = []
        with open(anomalies_path, "r", encoding="utf-8") as f:
            try:
                anomalies_list = json.load(f)
                for anomaly_dict in anomalies_list:
                    # Apply filters
                    if "rule_id" in filters and anomaly_dict.get("rule_id") != filters["rule_id"]:
                        continue
                    
                    rec = AnomalyRecord(
                        run_id=run_id,
                        rule_id=anomaly_dict.get("rule_id", "unknown"),
                        severity=anomaly_dict.get("severity", "WARNING"),
                        domain=anomaly_dict.get("domain", "general"),
                        tick_start=anomaly_dict.get("tick_start", 0),
                        tick_end=anomaly_dict.get("tick_end", 0),
                        affected_entity_count=anomaly_dict.get("affected_entity_count", 0),
                        message=anomaly_dict.get("message", ""),
                        evidence_json=json.dumps(anomaly_dict.get("evidence", {}))
                    )
                    records.append(rec)
            except Exception:
                pass

        records.sort(key=lambda x: x.tick_start)

        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_metric_windows(self, filters: Dict[str, Any]) -> List[MetricWindowRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []

        from src.observability.reporting.history_query import sanitize_id
        try:
            run_id = sanitize_id(run_id)
        except ValueError:
            return []

        run_dir = os.path.join(self.run_repo.base_dir, run_id)
        metrics_path = os.path.join(run_dir, "metric_windows.jsonl")
        if not os.path.exists(metrics_path):
            return []

        records = []
        with open(metrics_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    m_dict = json.loads(line)
                    rec = MetricWindowRecord(
                        run_id=run_id,
                        window_start_tick=m_dict.get("window_start_tick", 0),
                        window_end_tick=m_dict.get("window_end_tick", 0),
                        tick_compute_ms_avg=m_dict.get("tick_compute_ms_avg", 0.0),
                        tick_compute_ms_p95=m_dict.get("tick_compute_ms_p95", 0.0),
                        memory_rss_bytes_avg=m_dict.get("memory_rss_bytes_avg", 0.0),
                        memory_rss_bytes_max=m_dict.get("memory_rss_bytes_max", 0.0),
                        alive_entities_avg=m_dict.get("alive_entities_avg", 0.0),
                        gold_total_avg=m_dict.get("gold_total_avg", 0.0),
                        event_count=m_dict.get("event_count", 0),
                        hard_law_violation_count=m_dict.get("hard_law_violation_count", 0),
                        metrics_json=json.dumps(m_dict)
                    )
                    records.append(rec)
                except Exception:
                    continue

        records.sort(key=lambda x: x.window_start_tick)

        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_violations(self, filters: Dict[str, Any]) -> List[HardLawViolationRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []

        from src.observability.reporting.history_query import sanitize_id
        try:
            run_id = sanitize_id(run_id)
        except ValueError:
            return []

        violations_path = self.run_repo.resolve_path(run_id, "violations")
        if not os.path.exists(violations_path):
            return []

        records = []
        with open(violations_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    v_dict = json.loads(line)
                    # Apply filters
                    if "violation_type" in filters and v_dict.get("violation_type") != filters["violation_type"]:
                        continue

                    rec = HardLawViolationRecord(
                        run_id=run_id,
                        tick=v_dict.get("tick", 0),
                        violation_type=v_dict.get("violation_type", "unknown"),
                        severity=v_dict.get("severity", "CRITICAL"),
                        actor_id=v_dict.get("actor_id"),
                        target_id=v_dict.get("target_id"),
                        message=v_dict.get("message", ""),
                        evidence_json=json.dumps(v_dict.get("evidence", {}))
                    )
                    records.append(rec)
                except Exception:
                    continue

        records.sort(key=lambda x: x.tick)

        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def health(self) -> WarehouseHealthStatus:
        return WarehouseHealthStatus(connected=True, latency_ms=0.5)

    def close(self) -> None:
        pass
