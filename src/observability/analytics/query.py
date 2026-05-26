# Compliance IDs: OBS-058, OBS-059, OBS-060
from __future__ import annotations

import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DuckDBQueryService:
    """Analytical service powered by in-process DuckDB executing SQL queries directly over Parquet data tables."""

    def __init__(self, dataset_dir: str):
        self.dataset_dir = os.path.abspath(dataset_dir)
        self.manifest_path = os.path.join(self.dataset_dir, "dataset_manifest.json")
        
        try:
            import duckdb
            self.duckdb = duckdb
            self.enabled = True
        except ImportError:
            self.enabled = False

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise ImportError(
                "Optional dependency 'duckdb' is required to execute local analytics queries. "
                "Please ensure duckdb is installed in the current virtual environment."
            )

    def _resolve_table_path(self, table_name: str) -> str:
        # Load from manifest or standard filename fallback
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    tables = manifest.get("table_files") or {}
                    if table_name in tables:
                        return os.path.join(self.dataset_dir, tables[table_name])
            except Exception as e:
                logger.warning(f"Failed parsing dataset_manifest.json: {e}")

        # Fallback to standard parquet filename
        return os.path.join(self.dataset_dir, f"{table_name}.parquet")

    def execute_predefined_query(self, query_name: str) -> List[Dict[str, Any]]:
        self._ensure_enabled()
        
        query_name = query_name.lower()
        
        runs_path = self._resolve_table_path("runs")
        anomalies_path = self._resolve_table_path("anomalies")

        if query_name == "worst-runs":
            if not os.path.exists(runs_path):
                raise FileNotFoundError(f"Runs table not found at: {runs_path}")
            
            sql = f"""
                SELECT 
                    run_id, 
                    seed, 
                    health_score, 
                    status, 
                    critical_count, 
                    warning_count 
                FROM '{runs_path}' 
                ORDER BY health_score ASC, critical_count DESC
            """
            
        elif query_name == "anomaly-summary":
            if not os.path.exists(anomalies_path):
                raise FileNotFoundError(f"Anomalies table not found at: {anomalies_path}")
            
            sql = f"""
                SELECT 
                    rule_id, 
                    severity, 
                    COUNT(*) as count 
                FROM '{anomalies_path}' 
                GROUP BY rule_id, severity 
                ORDER BY count DESC
            """
            
        else:
            raise ValueError(
                f"Unsupported predefined query '{query_name}'. "
                f"Available queries: 'worst-runs', 'anomaly-summary'"
            )

        logger.info(f"Executing query '{query_name}' using DuckDB...")
        
        # Connect to an in-memory DuckDB instance
        conn = self.duckdb.connect(database=":memory:")
        try:
            relation = conn.execute(sql)
            columns = [desc[0] for desc in relation.description]
            rows = relation.fetchall()
            
            # Map columns to values for JSON-safe results
            results = []
            for row in rows:
                row_dict = {}
                for col_name, val in zip(columns, row):
                    # duckdb can return custom decimal or numpy types, convert to std float/int/str
                    if hasattr(val, "item"): # numpy types
                        val = val.item()
                    row_dict[col_name] = val
                results.append(row_dict)
                
            return results
        finally:
            conn.close()
