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
    WarehouseHealthStatus,
    BehaviorMetricWindowRecord,
    BehaviorEventRecord,
    BehaviorEpisodeRecord,
    EntityBehaviorScorecardRecord,
    RunBehaviorScorecardRecord,
    BehaviorFindingRecord,
    BehaviorInsightRecord,
    CohortBehaviorReportRecord,
    RunBehaviorComparisonRecord
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

    def query_behavior_events(self, filters: Dict[str, Any]) -> List[BehaviorEventRecord]:
        return []

    def query_behavior_episodes(self, filters: Dict[str, Any]) -> List[BehaviorEpisodeRecord]:
        return []

    def query_behavior_metric_windows(self, filters: Dict[str, Any]) -> List[BehaviorMetricWindowRecord]:
        return []

    def query_entity_behavior_scorecards(self, filters: Dict[str, Any]) -> List[EntityBehaviorScorecardRecord]:
        return []

    def query_run_behavior_scorecards(self, filters: Dict[str, Any]) -> List[RunBehaviorScorecardRecord]:
        return []

    def query_behavior_findings(self, filters: Dict[str, Any]) -> List[BehaviorFindingRecord]:
        return []

    def query_behavior_insights(self, filters: Dict[str, Any]) -> List[BehaviorInsightRecord]:
        return []

    def query_cohort_behavior_reports(self, filters: Dict[str, Any]) -> List[CohortBehaviorReportRecord]:
        return []

    def query_run_behavior_comparisons(self, filters: Dict[str, Any]) -> List[RunBehaviorComparisonRecord]:
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
            "metrics": 0,
            "behavior_metrics": 0
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

            # 7. Map behavior metric windows if available
            run_dir = os.path.join(self.run_repo.base_dir, run_id)
            behavior_metrics_path = os.path.join(run_dir, "behavior_metric_windows.jsonl")
            if os.path.exists(behavior_metrics_path):
                from src.observability.warehouse.models import BehaviorMetricWindowRecord
                with open(behavior_metrics_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        m_dict = json.loads(line)
                        BehaviorMetricWindowRecord(
                            run_id=run_id,
                            window_start_tick=m_dict.get("window_start_tick", 0),
                            window_end_tick=m_dict.get("window_end_tick", 0),
                            behavior_counts_json=json.dumps(m_dict.get("behavior_counts", {})),
                            route_family_counts_json=json.dumps(m_dict.get("route_family_counts", {})),
                            episode_counts_json=json.dumps(m_dict.get("episode_counts", {})),
                            episode_outcomes_json=json.dumps(m_dict.get("episode_outcomes", {})),
                            failure_counts_json=json.dumps(m_dict.get("failure_counts", {})),
                            adaptation_counts_json=json.dumps(m_dict.get("adaptation_counts", {})),
                            entity_activity_counts_json=json.dumps(m_dict.get("entity_activity_counts", {})),
                            schema_version=m_dict.get("schema_version", 1)
                        )
                        records_count["behavior_metrics"] = records_count.get("behavior_metrics", 0) + 1

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

    def query_behavior_events(self, filters: Dict[str, Any]) -> List[BehaviorEventRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "behavior_events")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    if "entity_id" in filters and d.get("entity_id") != filters["entity_id"]:
                        continue
                    if "category" in filters and d.get("category") != filters["category"]:
                        continue
                    records.append(BehaviorEventRecord(
                        run_id=run_id,
                        tick=d.get("tick", 0),
                        event_id=d.get("event_id", ""),
                        entity_id=d.get("entity_id", ""),
                        category=d.get("category", ""),
                        family=d.get("family", ""),
                        action=d.get("action", ""),
                        subject_type=d.get("subject_type", ""),
                        subject_id=d.get("subject_id"),
                        success=d.get("success", True),
                        metadata_json=json.dumps(d.get("metadata", {}))
                    ))
                except Exception:
                    continue
        records.sort(key=lambda x: x.tick)
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_behavior_episodes(self, filters: Dict[str, Any]) -> List[BehaviorEpisodeRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "behavior_episodes")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    if "entity_id" in filters and d.get("entity_id") != filters["entity_id"]:
                        continue
                    if "category" in filters and d.get("category") != filters["category"]:
                        continue
                    records.append(BehaviorEpisodeRecord(
                        run_id=run_id,
                        episode_id=d.get("episode_id", ""),
                        entity_id=d.get("entity_id", ""),
                        category=d.get("category", ""),
                        start_tick=d.get("start_tick", 0),
                        end_tick=d.get("end_tick", 0),
                        duration_ticks=d.get("duration_ticks", 0),
                        outcome=d.get("outcome", ""),
                        event_count=d.get("event_count", 0),
                        events_json=json.dumps(d.get("events", []))
                    ))
                except Exception:
                    continue
        records.sort(key=lambda x: x.start_tick)
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_behavior_metric_windows(self, filters: Dict[str, Any]) -> List[BehaviorMetricWindowRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "behavior_metric_windows")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    records.append(BehaviorMetricWindowRecord(
                        run_id=run_id,
                        window_start_tick=d.get("window_start_tick", 0),
                        window_end_tick=d.get("window_end_tick", 0),
                        behavior_counts_json=json.dumps(d.get("behavior_counts", {})),
                        route_family_counts_json=json.dumps(d.get("route_family_counts", {})),
                        episode_counts_json=json.dumps(d.get("episode_counts", {})),
                        episode_outcomes_json=json.dumps(d.get("episode_outcomes", {})),
                        failure_counts_json=json.dumps(d.get("failure_counts", {})),
                        adaptation_counts_json=json.dumps(d.get("adaptation_counts", {})),
                        entity_activity_counts_json=json.dumps(d.get("entity_activity_counts", {})),
                        schema_version=d.get("schema_version", 1)
                    ))
                except Exception:
                    continue
        records.sort(key=lambda x: x.window_start_tick)
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_entity_behavior_scorecards(self, filters: Dict[str, Any]) -> List[EntityBehaviorScorecardRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "entity_behavior_scorecards")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    if "entity_id" in filters and d.get("entity_id") != filters["entity_id"]:
                        continue
                    records.append(EntityBehaviorScorecardRecord(
                        run_id=run_id,
                        entity_id=d.get("entity_id", ""),
                        total_events=d.get("total_events", 0),
                        category_counts_json=json.dumps(d.get("category_counts", {})),
                        family_counts_json=json.dumps(d.get("family_counts", {})),
                        episode_counts_json=json.dumps(d.get("episode_counts", {})),
                        episode_outcomes_json=json.dumps(d.get("episode_outcomes", {})),
                        total_failures=d.get("total_failures", 0),
                        total_adaptations=d.get("total_adaptations", 0),
                        failure_loop_count=d.get("failure_loop_count", 0),
                        adaptation_proof_count=d.get("adaptation_proof_count", 0),
                        suspicion_score=d.get("suspicion_score", 0.0),
                        verdict=d.get("verdict", "INCONCLUSIVE")
                    ))
                except Exception:
                    continue
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_run_behavior_scorecards(self, filters: Dict[str, Any]) -> List[RunBehaviorScorecardRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "run_behavior_scorecard")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return [RunBehaviorScorecardRecord(
                run_id=run_id,
                total_events=d.get("total_events", 0),
                total_episodes=d.get("total_episodes", 0),
                total_failures=d.get("total_failures", 0),
                total_adaptations=d.get("total_adaptations", 0),
                entity_count=d.get("entity_count", 0),
                verdict_distribution_json=json.dumps(d.get("verdict_distribution", {})),
                category_counts_json=json.dumps(d.get("category_counts", {})),
                family_counts_json=json.dumps(d.get("family_counts", {}))
            )]
        except Exception:
            return []

    def query_behavior_findings(self, filters: Dict[str, Any]) -> List[BehaviorFindingRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "behavior_findings")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    if "entity_id" in filters and d.get("entity_id") != filters["entity_id"]:
                        continue
                    records.append(BehaviorFindingRecord(
                        run_id=run_id,
                        finding_id=d.get("finding_id", ""),
                        entity_id=d.get("entity_id", ""),
                        pattern_type=d.get("pattern_type", ""),
                        tick=d.get("tick", 0),
                        severity=d.get("severity", "INFO"),
                        evidence_json=json.dumps(d.get("evidence", {}))
                    ))
                except Exception:
                    continue
        records.sort(key=lambda x: x.tick)
        offset = int(filters.get("offset", 0))
        limit = int(filters.get("limit", 50))
        return records[offset:offset+limit]

    def query_behavior_insights(self, filters: Dict[str, Any]) -> List[BehaviorInsightRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "behavior_insights")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # If it's a list:
            if isinstance(data, list):
                records = []
                for d in data:
                    records.append(BehaviorInsightRecord(
                        run_id=run_id,
                        insight_id=d.get("insight_id", ""),
                        insight_type=d.get("insight_type", ""),
                        title=d.get("title", ""),
                        evidence_json=json.dumps(d.get("evidence", {})),
                        recommendation=d.get("recommendation", ""),
                        severity=d.get("severity", "INFO")
                    ))
                return records
            # Otherwise single dict:
            return [BehaviorInsightRecord(
                run_id=run_id,
                insight_id=data.get("insight_id", ""),
                insight_type=data.get("insight_type", ""),
                title=data.get("title", ""),
                evidence_json=json.dumps(data.get("evidence", {})),
                recommendation=data.get("recommendation", ""),
                severity=data.get("severity", "INFO")
            )]
        except Exception:
            return []

    def query_cohort_behavior_reports(self, filters: Dict[str, Any]) -> List[CohortBehaviorReportRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "cohort_behavior_report")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            # Wrap in list
            return [CohortBehaviorReportRecord(
                run_id=run_id,
                cohort_name=d.get("cohort_name", "all"),
                entities_json=json.dumps(d.get("entities", [])),
                metrics_json=json.dumps(d.get("metrics", {}))
            )]
        except Exception:
            return []

    def query_run_behavior_comparisons(self, filters: Dict[str, Any]) -> List[RunBehaviorComparisonRecord]:
        run_id = filters.get("run_id")
        if not run_id:
            return []
        try:
            path = self.run_repo.resolve_path(run_id, "run_behavior_comparison")
        except Exception:
            return []
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return [RunBehaviorComparisonRecord(
                run_id=run_id,
                baseline_run_id=d.get("baseline_run_id", ""),
                episode_success_rate_delta=d.get("episode_success_rate_delta", 0.0),
                consecutive_failures_delta=d.get("consecutive_failures_delta", 0.0),
                event_volume_delta=d.get("event_volume_delta", 0.0),
                verdict=d.get("verdict", "NO_CHANGE"),
                reason=d.get("reason", "")
            )]
        except Exception:
            return []

    def health(self) -> WarehouseHealthStatus:
        return WarehouseHealthStatus(connected=True, latency_ms=0.5)

    def close(self) -> None:
        pass
