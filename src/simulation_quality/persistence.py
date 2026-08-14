from __future__ import annotations
import json
import logging
import os
from typing import Optional

from src.simulation_quality.score_record import ScoreRecord
from src.simulation_quality.quality_report import QualityReport
from src.simulation_quality.run_health import RunHealthRecord

logger = logging.getLogger(__name__)


class QualityPersistence:
    """Non-blocking file writer for quality score records and reports."""

    def __init__(self, run_dir: str) -> None:
        self._run_dir = run_dir
        self._file_handle = None
        try:
            os.makedirs(run_dir, exist_ok=True)
            jsonl_path = os.path.join(run_dir, "quality_scores.jsonl")
            self._file_handle = open(jsonl_path, "a", encoding="utf-8")
        except Exception as exc:
            logger.error("QualityPersistence: failed to open quality_scores.jsonl: %s", exc)

    def write(self, record: ScoreRecord) -> None:
        if self._file_handle is None:
            return
        try:
            data = {
                "tick": record.tick,
                "event_id": record.event_id,
                "pillar": record.pillar.value,
                "delta": record.delta,
                "reason": record.reason,
                "event_type": record.event_type,
                "entity_id": record.entity_id,
                "region_id": record.region_id,
                "tags": list(record.tags),
            }
            self._file_handle.write(json.dumps(data) + "\n")
            self._file_handle.flush()
        except Exception as exc:
            logger.warning("QualityPersistence.write: failed to write record: %s", exc)

    def write_report(self, report: QualityReport) -> None:
        tmp_path = os.path.join(self._run_dir, "quality_report.json.tmp")
        final_path = os.path.join(self._run_dir, "quality_report.json")
        try:
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(report.to_dict(), fh, indent=2)
            os.rename(tmp_path, final_path)
        except Exception as exc:
            logger.warning("QualityPersistence.write_report: failed to write report: %s", exc)

    @staticmethod
    def write_run_health(run_dir: str, record: RunHealthRecord) -> None:
        """Write a RunHealthRecord sidecar next to quality_report.json in run_dir.

        Static (not an instance method touching self._file_handle) because callers
        such as calibrate_simq.py's _run_engine() need to persist this record before
        a full QualityPersistence instance for run_dir exists — instantiating one
        just for this write would open a second, never-closed quality_scores.jsonl
        handle in the same directory.
        """
        tmp_path = os.path.join(run_dir, "quality_report.run_health.json.tmp")
        final_path = os.path.join(run_dir, "quality_report.run_health.json")
        try:
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(record.to_dict(), fh, indent=2)
            os.rename(tmp_path, final_path)
        except Exception as exc:
            logger.warning("QualityPersistence.write_run_health: failed to write record: %s", exc)

    def shutdown(self) -> None:
        if self._file_handle is not None:
            try:
                self._file_handle.flush()
                self._file_handle.close()
            except Exception as exc:
                logger.warning("QualityPersistence.shutdown: error closing file: %s", exc)
            finally:
                self._file_handle = None
