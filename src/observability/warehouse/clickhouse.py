from __future__ import annotations
import os
import json
import uuid
import time
import hashlib
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
from src.observability.config import ObservabilityConfig

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None


def calculate_checksum(data_dict: Dict[str, Any]) -> str:
    """Computes a deterministic hash of the manifest dictionary for ingestion idempotency checks."""
    serialized = json.dumps(data_dict, sort_keys=True)
    return hashlib.md5(serialized.encode("utf-8")).hexdigest()


class ClickHouseSchemaManager:
    """Responsible for creating database schemas and tables on target ClickHouse instances."""

    def __init__(self, client: Any):
        self.client = client

    def init_schema(self, database: str = "default") -> None:
        """Runs CREATE TABLE DDL commands to declare optimized telemetry analytics tables."""
        if not self.client:
            raise ConnectionError("ClickHouse client not initialized.")

        # Create database if custom database configured
        if database and database != "default":
            self.client.command(f"CREATE DATABASE IF NOT EXISTS {database}")

        self.client.command("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id String,
            scenario_name String,
            scenario_type String,
            seed UInt32,
            status String,
            ticks_completed UInt32,
            health_score Float32,
            started_at String,
            ended_at Nullable(String),
            schema_version String,
            checksum String,
            manifest_json String,
            resolved_world_path Nullable(String),
            compile_context_path Nullable(String),
            provenance_manifest_path Nullable(String),
            assembly_report_path Nullable(String),
            validation_report_path Nullable(String),
            compile_report_path Nullable(String),
            runtime_content_source Nullable(String),
            catalog_fingerprint Nullable(String),
            module_fingerprints Nullable(String),
            state_hash Nullable(String)
        ) ENGINE = MergeTree()
        ORDER BY (run_id)
        """)

        self.client.command("""
        CREATE TABLE IF NOT EXISTS sweeps (
            sweep_id String,
            scenario_name String,
            scenario_type String,
            total_runs UInt32,
            completed_runs UInt32,
            failed_runs UInt32,
            average_health_score Float32,
            created_at String,
            schema_version String,
            summary_json String
        ) ENGINE = MergeTree()
        ORDER BY (sweep_id)
        """)

        self.client.command("""
        CREATE TABLE IF NOT EXISTS simulation_events (
            run_id String,
            tick UInt32,
            event_type String,
            event_category String,
            severity String,
            entity_id Nullable(String),
            region_id Nullable(String),
            quest_id Nullable(String),
            faction_id Nullable(String),
            message String,
            payload_json String,
            created_at String
        ) ENGINE = MergeTree()
        ORDER BY (run_id, tick, event_type)
        """)

        self.client.command("""
        CREATE TABLE IF NOT EXISTS metric_windows (
            run_id String,
            window_start_tick UInt32,
            window_end_tick UInt32,
            tick_compute_ms_avg Float32,
            tick_compute_ms_p95 Float32,
            memory_rss_bytes_avg Float32,
            memory_rss_bytes_max Float32,
            alive_entities_avg Float32,
            gold_total_avg Float32,
            event_count UInt32,
            hard_law_violation_count UInt32,
            metrics_json String
        ) ENGINE = MergeTree()
        ORDER BY (run_id, window_start_tick)
        """)

        self.client.command("""
        CREATE TABLE IF NOT EXISTS anomalies (
            run_id String,
            rule_id String,
            severity String,
            domain String,
            tick_start UInt32,
            tick_end UInt32,
            affected_entity_count UInt32,
            message String,
            evidence_json String
        ) ENGINE = MergeTree()
        ORDER BY (run_id, rule_id)
        """)

        self.client.command("""
        CREATE TABLE IF NOT EXISTS hard_law_violations (
            run_id String,
            tick UInt32,
            violation_type String,
            severity String,
            actor_id Nullable(String),
            target_id Nullable(String),
            message String,
            evidence_json String
        ) ENGINE = MergeTree()
        ORDER BY (run_id, tick, violation_type)
        """)


class ClickHouseWarehouseAdapter(WarehouseAdapter):
    """
    High-volume analytical event warehouse adapter using ClickHouse.
    Allows hot-swapping backend engine and supports query and batch insertion optimizations.
    """

    def __init__(
        self,
        run_repo: Optional[RunArtifactRepository] = None,
        sweep_repo: Optional[RunSetArtifactRepository] = None
    ):
        if clickhouse_connect is None:
            raise ImportError(
                "The 'clickhouse-connect' package is required for ClickHouseWarehouseAdapter but is not installed."
            )

        self.run_repo = run_repo or RunArtifactRepository()
        self.sweep_repo = sweep_repo or RunSetArtifactRepository()

        self.host = ObservabilityConfig.get_clickhouse_host()
        self.port = ObservabilityConfig.get_clickhouse_port()
        self.database = ObservabilityConfig.get_clickhouse_database()
        self.username = ObservabilityConfig.get_clickhouse_username()
        self.password = ObservabilityConfig.get_clickhouse_password()
        self.secure = ObservabilityConfig.get_clickhouse_secure()
        self.batch_size = ObservabilityConfig.get_clickhouse_batch_size()

        self.client = None
        self._conn_error = None

        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
                secure=self.secure
            )
        except Exception as e:
            # Self-healing: if target database doesn't exist, connect to default and create it
            if "UNKNOWN_DATABASE" in str(e) or "code: 81" in str(e):
                try:
                    self.client = clickhouse_connect.get_client(
                        host=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        database="default",
                        secure=self.secure
                    )
                    if self.database:
                        self.client.command(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                        # Switch current client context to the new database
                        self.client.command(f"USE {self.database}")
                except Exception as inner_e:
                    self._conn_error = str(inner_e)
            else:
                self._conn_error = str(e)

    def health(self) -> WarehouseHealthStatus:
        if not self.client:
            return WarehouseHealthStatus(connected=False, latency_ms=0.0, error=self._conn_error or "Not connected")
        start = time.perf_counter()
        try:
            self.client.ping()
            latency = (time.perf_counter() - start) * 1000.0
            return WarehouseHealthStatus(connected=True, latency_ms=latency)
        except Exception as e:
            return WarehouseHealthStatus(connected=False, latency_ms=0.0, error=str(e))

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def init_schema(self) -> None:
        if not self.client:
            raise ConnectionError(f"Cannot initialize schema: clickhouse not connected. Error: {self._conn_error}")
        
        # Safe database bootstrapping using default connection context
        try:
            temp_client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database="default",
                secure=self.secure
            )
            if self.database and self.database != "default":
                temp_client.command(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            temp_client.close()
        except Exception as e:
            # Fallback or pass if default database setup fails
            pass

        # Reconnect main client under target database context to ensure HTTP headers align
        try:
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
                secure=self.secure
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to target database after bootstrapping: {e}")

        manager = ClickHouseSchemaManager(self.client)
        manager.init_schema(self.database)

    def ingest_run(self, run_id: str, dry_run: bool = False, force: bool = False) -> WarehouseIngestionResult:
        if not self.client and not dry_run:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

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
            run_repo = self.run_repo
            manifest_path = run_repo.resolve_path(run_id, "manifest")
            if not os.path.exists(manifest_path):
                raise FileNotFoundError(f"Run manifest path not found: {manifest_path}")

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_dict = json.load(f)

            # 2. Validate artifact schema version
            WarehouseSchemaRegistry.validate_manifest(manifest_dict)

            # Compute manifest checksum
            checksum = calculate_checksum(manifest_dict)

            # 3. Check for existing run (Idempotency)
            if not dry_run:
                existing = self.client.query("SELECT checksum FROM runs WHERE run_id = %(run_id)s", {"run_id": run_id}).result_rows
                if existing:
                    existing_checksum = existing[0][0]
                    if existing_checksum == checksum:
                        duration = (time.perf_counter() - start_time) * 1000.0
                        return WarehouseIngestionResult(
                            ingestion_id=ingestion_id,
                            run_id=run_id,
                            status="SKIPPED",
                            records_ingested=records_count,
                            errors=[],
                            duration_ms=duration
                        )
                    else:
                        if not force:
                            raise ValueError(
                                f"Run {run_id} already exists with different checksum. Re-run with force=True to overwrite."
                            )
                        else:
                            # Delete existing records for this run across all tables
                            self.client.command(f"ALTER TABLE runs DELETE WHERE run_id = '{run_id}'")
                            self.client.command(f"ALTER TABLE simulation_events DELETE WHERE run_id = '{run_id}'")
                            self.client.command(f"ALTER TABLE metric_windows DELETE WHERE run_id = '{run_id}'")
                            self.client.command(f"ALTER TABLE anomalies DELETE WHERE run_id = '{run_id}'")
                            self.client.command(f"ALTER TABLE hard_law_violations DELETE WHERE run_id = '{run_id}'")

            # 4. Map to RunRecord
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
                manifest_json=json.dumps(manifest_dict),
                resolved_world_path=manifest_dict.get("resolved_world_path"),
                compile_context_path=manifest_dict.get("compile_context_path"),
                provenance_manifest_path=manifest_dict.get("provenance_manifest_path"),
                assembly_report_path=manifest_dict.get("assembly_report_path"),
                validation_report_path=manifest_dict.get("validation_report_path"),
                compile_report_path=manifest_dict.get("compile_report_path"),
                runtime_content_source=manifest_dict.get("runtime_content_source"),
                catalog_fingerprint=manifest_dict.get("catalog_fingerprint"),
                module_fingerprints=manifest_dict.get("module_fingerprints"),
                state_hash=manifest_dict.get("state_hash")
            )

            if not dry_run:
                module_fingerprints_str = (
                    json.dumps(run_rec.module_fingerprints)
                    if run_rec.module_fingerprints is not None
                    else None
                )
                self.client.insert("runs", [[
                    run_rec.run_id,
                    run_rec.scenario_name,
                    run_rec.scenario_type,
                    run_rec.seed,
                    run_rec.status,
                    run_rec.ticks_completed,
                    run_rec.health_score,
                    run_rec.started_at,
                    run_rec.ended_at,
                    run_rec.schema_version,
                    checksum,
                    run_rec.manifest_json,
                    run_rec.resolved_world_path,
                    run_rec.compile_context_path,
                    run_rec.provenance_manifest_path,
                    run_rec.assembly_report_path,
                    run_rec.validation_report_path,
                    run_rec.compile_report_path,
                    run_rec.runtime_content_source,
                    run_rec.catalog_fingerprint,
                    module_fingerprints_str,
                    run_rec.state_hash
                ]], column_names=[
                    "run_id", "scenario_name", "scenario_type", "seed", "status",
                    "ticks_completed", "health_score", "started_at", "ended_at",
                    "schema_version", "checksum", "manifest_json",
                    "resolved_world_path", "compile_context_path", "provenance_manifest_path", "assembly_report_path",
                    "validation_report_path", "compile_report_path", "runtime_content_source", "catalog_fingerprint",
                    "module_fingerprints", "state_hash"
                ])
            records_count["runs"] += 1

            # 5. Map events if available
            events_path = run_repo.resolve_path(run_id, "events")
            if os.path.exists(events_path):
                events_to_insert = []
                with open(events_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        event_dict = json.loads(line)
                        payload = event_dict.get("payload", {})
                        created_at = event_dict.get("timestamp") or datetime.utcnow().isoformat()

                        ev = EventRecord(
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
                        events_to_insert.append([
                            ev.run_id, ev.tick, ev.event_type, ev.event_category,
                            ev.severity, ev.entity_id, ev.region_id, ev.quest_id,
                            ev.faction_id, ev.message, ev.payload_json, ev.created_at
                        ])

                if events_to_insert and not dry_run:
                    for i in range(0, len(events_to_insert), self.batch_size):
                        chunk = events_to_insert[i:i + self.batch_size]
                        self.client.insert("simulation_events", chunk, column_names=[
                            "run_id", "tick", "event_type", "event_category",
                            "severity", "entity_id", "region_id", "quest_id",
                            "faction_id", "message", "payload_json", "created_at"
                        ])
                records_count["events"] = len(events_to_insert)

            # 6. Map violations if available
            violations_path = run_repo.resolve_path(run_id, "violations")
            if os.path.exists(violations_path):
                violations_to_insert = []
                with open(violations_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        violation_dict = json.loads(line)
                        v = HardLawViolationRecord(
                            run_id=run_id,
                            tick=violation_dict.get("tick", 0),
                            violation_type=violation_dict.get("violation_type", "unknown"),
                            severity=violation_dict.get("severity", "CRITICAL"),
                            actor_id=violation_dict.get("actor_id"),
                            target_id=violation_dict.get("target_id"),
                            message=violation_dict.get("message", ""),
                            evidence_json=json.dumps(violation_dict.get("evidence", {}))
                        )
                        violations_to_insert.append([
                            v.run_id, v.tick, v.violation_type, v.severity,
                            v.actor_id, v.target_id, v.message, v.evidence_json
                        ])

                if violations_to_insert and not dry_run:
                    for i in range(0, len(violations_to_insert), self.batch_size):
                        chunk = violations_to_insert[i:i + self.batch_size]
                        self.client.insert("hard_law_violations", chunk, column_names=[
                            "run_id", "tick", "violation_type", "severity",
                            "actor_id", "target_id", "message", "evidence_json"
                        ])
                records_count["violations"] = len(violations_to_insert)

            # 7. Map anomalies if available
            anomalies_path = run_repo.resolve_path(run_id, "anomalies")
            if os.path.exists(anomalies_path):
                anomalies_to_insert = []
                with open(anomalies_path, "r", encoding="utf-8") as f:
                    anomalies_list = json.load(f)
                    for anomaly_dict in anomalies_list:
                        a = AnomalyRecord(
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
                        anomalies_to_insert.append([
                            a.run_id, a.rule_id, a.severity, a.domain,
                            a.tick_start, a.tick_end, a.affected_entity_count,
                            a.message, a.evidence_json
                        ])

                if anomalies_to_insert and not dry_run:
                    self.client.insert("anomalies", anomalies_to_insert, column_names=[
                        "run_id", "rule_id", "severity", "domain",
                        "tick_start", "tick_end", "affected_entity_count",
                        "message", "evidence_json"
                    ])
                records_count["anomalies"] = len(anomalies_to_insert)

            # 8. Map metrics if available
            metrics_path = os.path.join(run_repo.base_dir, run_id, "metric_windows.jsonl")
            if os.path.exists(metrics_path):
                metrics_to_insert = []
                with open(metrics_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        metric_window = json.loads(line)

                        m = MetricWindowRecord(
                            run_id=run_id,
                            window_start_tick=metric_window.get("window_start_tick", 0),
                            window_end_tick=metric_window.get("window_end_tick", 0),
                            tick_compute_ms_avg=metric_window.get("tick_compute_ms_avg", 0.0),
                            tick_compute_ms_p95=metric_window.get("tick_compute_ms_p95", 0.0),
                            memory_rss_bytes_avg=metric_window.get("memory_rss_bytes_avg", 0.0),
                            memory_rss_bytes_max=metric_window.get("memory_rss_bytes_max", 0.0),
                            alive_entities_avg=metric_window.get("alive_entities_avg", 0.0),
                            gold_total_avg=metric_window.get("gold_total_avg", 0.0),
                            event_count=metric_window.get("event_count", 0),
                            hard_law_violation_count=metric_window.get("hard_law_violation_count", 0),
                            metrics_json=json.dumps(metric_window.get("metrics", {}))
                        )
                        metrics_to_insert.append([
                            m.run_id, m.window_start_tick, m.window_end_tick,
                            m.tick_compute_ms_avg, m.tick_compute_ms_p95,
                            m.memory_rss_bytes_avg, m.memory_rss_bytes_max,
                            m.alive_entities_avg, m.gold_total_avg,
                            m.event_count, m.hard_law_violation_count, m.metrics_json
                        ])

                if metrics_to_insert and not dry_run:
                    self.client.insert("metric_windows", metrics_to_insert, column_names=[
                        "run_id", "window_start_tick", "window_end_tick",
                        "tick_compute_ms_avg", "tick_compute_ms_p95",
                        "memory_rss_bytes_avg", "memory_rss_bytes_max",
                        "alive_entities_avg", "gold_total_avg",
                        "event_count", "hard_law_violation_count", "metrics_json"
                    ])
                records_count["metrics"] = len(metrics_to_insert)

        except ValueError as e:
            raise e
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
        if not self.client and not dry_run:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

        start_time = time.perf_counter()
        ingestion_id = str(uuid.uuid4())
        records_count = {
            "sweeps": 0,
            "runs": 0
        }
        errors = []

        try:
            # 1. Load run set manifest
            sweep_repo = self.sweep_repo
            manifest_path = sweep_repo.resolve_path(sweep_id, "manifest")
            if not os.path.exists(manifest_path):
                raise FileNotFoundError(f"Sweep manifest path not found: {manifest_path}")

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_dict = json.load(f)

            # 2. Load sweep summary
            summary_path = sweep_repo.resolve_path(sweep_id, "summary")
            if not os.path.exists(summary_path):
                raise FileNotFoundError(f"Sweep summary path not found: {summary_path}")

            with open(summary_path, "r", encoding="utf-8") as f:
                summary_dict = json.load(f)

            # 3. Check for existing sweep
            if not dry_run:
                existing = self.client.query("SELECT sweep_id FROM sweeps WHERE sweep_id = %(sweep_id)s", {"sweep_id": sweep_id}).result_rows
                if existing:
                    if not force:
                        raise ValueError(
                            f"Sweep {sweep_id} already exists. Re-run with force=True to overwrite."
                        )
                    else:
                        self.client.command(f"ALTER TABLE sweeps DELETE WHERE sweep_id = '{sweep_id}'")

            # 4. Map to SweepRecord
            sweep_rec = SweepRecord(
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

            if not dry_run:
                self.client.insert("sweeps", [[
                    sweep_rec.sweep_id,
                    sweep_rec.scenario_name,
                    sweep_rec.scenario_type,
                    sweep_rec.total_runs,
                    sweep_rec.completed_runs,
                    sweep_rec.failed_runs,
                    sweep_rec.average_health_score,
                    sweep_rec.created_at,
                    sweep_rec.schema_version,
                    sweep_rec.summary_json
                ]], column_names=[
                    "sweep_id", "scenario_name", "scenario_type", "total_runs",
                    "completed_runs", "failed_runs", "average_health_score",
                    "created_at", "schema_version", "summary_json"
                ])
            records_count["sweeps"] += 1

            # 5. Ingest children runs
            run_indices = sweep_repo.read_run_index(sweep_id)
            for record in run_indices:
                child_res = self.ingest_run(record.run_id, dry_run=dry_run, force=force)
                if child_res.status == "FAILED":
                    errors.extend(child_res.errors)
                else:
                    records_count["runs"] += 1

        except ValueError as e:
            raise e
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
        if not self.client:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

        query = "SELECT * FROM runs"
        conditions = []
        params = {}

        if "scenario_name" in filters:
            conditions.append("scenario_name = %(scenario_name)s")
            params["scenario_name"] = filters["scenario_name"]
        if "status" in filters:
            conditions.append("status = %(status)s")
            params["status"] = filters["status"]

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if "sort" in filters:
            if filters["sort"] == "health_score_asc":
                query += " ORDER BY health_score ASC"
            elif filters["sort"] == "health_score_desc":
                query += " ORDER BY health_score DESC"
        else:
            query += " ORDER BY run_id DESC"

        if "limit" in filters:
            query += " LIMIT %(limit)s"
            params["limit"] = int(filters["limit"])

        res = self.client.query(query, params)
        records = []
        for row in res.named_results():
            if "module_fingerprints" in row and isinstance(row["module_fingerprints"], str):
                try:
                    row["module_fingerprints"] = json.loads(row["module_fingerprints"])
                except Exception:
                    row["module_fingerprints"] = None
            records.append(RunRecord(**row))
        return records

    def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
        if not self.client:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

        query = "SELECT * FROM simulation_events"
        conditions = []
        params = {}

        if "run_id" in filters:
            conditions.append("run_id = %(run_id)s")
            params["run_id"] = filters["run_id"]
        if "entity_id" in filters:
            conditions.append("entity_id = %(entity_id)s")
            params["entity_id"] = filters["entity_id"]
        if "tick_start" in filters:
            conditions.append("tick >= %(tick_start)s")
            params["tick_start"] = int(filters["tick_start"])
        if "tick_end" in filters:
            conditions.append("tick <= %(tick_end)s")
            params["tick_end"] = int(filters["tick_end"])
        if "severity" in filters:
            conditions.append("severity = %(severity)s")
            params["severity"] = filters["severity"]

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY tick ASC"

        if "limit" in filters:
            query += " LIMIT %(limit)s"
            params["limit"] = int(filters["limit"])

        res = self.client.query(query, params)
        records = []
        for row in res.named_results():
            records.append(EventRecord(**row))
        return records

    def query_anomalies(self, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        if not self.client:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

        query = "SELECT * FROM anomalies"
        conditions = []
        params = {}

        if "run_id" in filters:
            conditions.append("run_id = %(run_id)s")
            params["run_id"] = filters["run_id"]
        if "rule_id" in filters:
            conditions.append("rule_id = %(rule_id)s")
            params["rule_id"] = filters["rule_id"]

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY tick_start ASC"

        if "limit" in filters:
            query += " LIMIT %(limit)s"
            params["limit"] = int(filters["limit"])

        res = self.client.query(query, params)
        records = []
        for row in res.named_results():
            records.append(AnomalyRecord(**row))
        return records

    def query_metric_windows(self, filters: Dict[str, Any]) -> List[MetricWindowRecord]:
        if not self.client:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

        query = "SELECT * FROM metric_windows"
        conditions = []
        params = {}

        if "run_id" in filters:
            conditions.append("run_id = %(run_id)s")
            params["run_id"] = filters["run_id"]

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY window_start_tick ASC"

        if "limit" in filters:
            query += " LIMIT %(limit)s"
            params["limit"] = int(filters["limit"])

        res = self.client.query(query, params)
        records = []
        for row in res.named_results():
            records.append(MetricWindowRecord(**row))
        return records

    def query_violations(self, filters: Dict[str, Any]) -> List[HardLawViolationRecord]:
        if not self.client:
            raise ConnectionError(f"ClickHouse client not connected: {self._conn_error}")

        query = "SELECT * FROM hard_law_violations"
        conditions = []
        params = {}

        if "run_id" in filters:
            conditions.append("run_id = %(run_id)s")
            params["run_id"] = filters["run_id"]
        if "violation_type" in filters:
            conditions.append("violation_type = %(violation_type)s")
            params["violation_type"] = filters["violation_type"]

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY tick ASC"

        if "limit" in filters:
            query += " LIMIT %(limit)s"
            params["limit"] = int(filters["limit"])

        res = self.client.query(query, params)
        records = []
        for row in res.named_results():
            records.append(HardLawViolationRecord(**row))
        return records

    def query_behavior_events(self, filters: Dict[str, Any]) -> List[BehaviorEventRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM behavior_events"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if "entity_id" in filters:
                conditions.append("entity_id = %(entity_id)s")
                params["entity_id"] = filters["entity_id"]
            if "category" in filters:
                conditions.append("category = %(category)s")
                params["category"] = filters["category"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY tick ASC"
            if "limit" in filters:
                query += " LIMIT %(limit)s"
                params["limit"] = int(filters["limit"])
            res = self.client.query(query, params)
            return [BehaviorEventRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_behavior_episodes(self, filters: Dict[str, Any]) -> List[BehaviorEpisodeRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM behavior_episodes"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if "entity_id" in filters:
                conditions.append("entity_id = %(entity_id)s")
                params["entity_id"] = filters["entity_id"]
            if "category" in filters:
                conditions.append("category = %(category)s")
                params["category"] = filters["category"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY start_tick ASC"
            if "limit" in filters:
                query += " LIMIT %(limit)s"
                params["limit"] = int(filters["limit"])
            res = self.client.query(query, params)
            return [BehaviorEpisodeRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_behavior_metric_windows(self, filters: Dict[str, Any]) -> List[BehaviorMetricWindowRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM behavior_metric_windows"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY window_start_tick ASC"
            if "limit" in filters:
                query += " LIMIT %(limit)s"
                params["limit"] = int(filters["limit"])
            res = self.client.query(query, params)
            return [BehaviorMetricWindowRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_entity_behavior_scorecards(self, filters: Dict[str, Any]) -> List[EntityBehaviorScorecardRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM entity_behavior_scorecards"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if "entity_id" in filters:
                conditions.append("entity_id = %(entity_id)s")
                params["entity_id"] = filters["entity_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            if "limit" in filters:
                query += " LIMIT %(limit)s"
                params["limit"] = int(filters["limit"])
            res = self.client.query(query, params)
            return [EntityBehaviorScorecardRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_run_behavior_scorecards(self, filters: Dict[str, Any]) -> List[RunBehaviorScorecardRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM run_behavior_scorecards"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            res = self.client.query(query, params)
            return [RunBehaviorScorecardRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_behavior_findings(self, filters: Dict[str, Any]) -> List[BehaviorFindingRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM behavior_findings"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if "entity_id" in filters:
                conditions.append("entity_id = %(entity_id)s")
                params["entity_id"] = filters["entity_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY tick ASC"
            if "limit" in filters:
                query += " LIMIT %(limit)s"
                params["limit"] = int(filters["limit"])
            res = self.client.query(query, params)
            return [BehaviorFindingRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_behavior_insights(self, filters: Dict[str, Any]) -> List[BehaviorInsightRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM behavior_insights"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            res = self.client.query(query, params)
            return [BehaviorInsightRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_cohort_behavior_reports(self, filters: Dict[str, Any]) -> List[CohortBehaviorReportRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM cohort_reports"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            res = self.client.query(query, params)
            return [CohortBehaviorReportRecord(**row) for row in res.named_results()]
        except Exception:
            return []

    def query_run_behavior_comparisons(self, filters: Dict[str, Any]) -> List[RunBehaviorComparisonRecord]:
        if not self.client:
            return []
        try:
            query = "SELECT * FROM behavior_comparisons"
            conditions = []
            params = {}
            if "run_id" in filters:
                conditions.append("run_id = %(run_id)s")
                params["run_id"] = filters["run_id"]
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            res = self.client.query(query, params)
            return [RunBehaviorComparisonRecord(**row) for row in res.named_results()]
        except Exception:
            return []

