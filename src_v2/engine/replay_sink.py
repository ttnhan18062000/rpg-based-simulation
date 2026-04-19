from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from src_v2.core.diagnostic import TraceEvent


@dataclass(frozen=True)
class SinkMetrics:
    """Operational metrics for the persistence sink."""
    bytes_written: int = 0
    chunks_persisted: int = 0
    quota_used_bytes: int = 0
    last_write_ms: float = 0.0


class ReplaySink:
    """
    Persistence adapter for simulation replay data.
    M6 Law: Replay IO must be structured, compact, and non-authoritative.
    Note: Falling back to compacted JSON due to environment constraints.
    """

    def __init__(self, run_dir: Path):
        self._run_dir = run_dir
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._metrics = SinkMetrics()

    def persist_chunk(self, chunk_id: int, events: List[TraceEvent]) -> bool:
        """
        Write a batch of events to a durable chunk file.
        Using compact JSON for portability in this environment.
        """
        try:
            filename = f"chunk_{chunk_id:04d}.json"
            filepath = self._run_dir / filename
            
            # Serialize events to compact JSON (no whitespace)
            data = [asdict(e) for e in events]
            json_data = json.dumps(data, separators=(',', ':'))
            encoded_data = json_data.encode('utf-8')
            
            with open(filepath, "wb") as f:
                f.write(encoded_data)
            
            # Update metrics
            self._metrics = SinkMetrics(
                bytes_written=self._metrics.bytes_written + len(encoded_data),
                chunks_persisted=self._metrics.chunks_persisted + 1,
                quota_used_bytes=self._metrics.quota_used_bytes + len(encoded_data)
            )
            return True
            
        except Exception:
            # M6 Law: Non-authoritative fallback
            return False

    def write_manifest(self, manifest_data: Dict[str, Any]) -> bool:
        """
        Write the run metadata index atomically.
        M7 Law: Write to temp then rename to ensure integrity.
        """
        try:
            manifest_path = self._run_dir / "manifest.json"
            temp_path = self._run_dir / "manifest.json.tmp"
            
            with open(temp_path, "w") as f:
                json.dump(manifest_data, f, indent=2)
            
            # Atomic rename (POSIX property)
            os.replace(temp_path, manifest_path)
            return True
        except Exception:
            return False

    def check_quota(self, max_bytes: int) -> bool:
        """
        Simulated quota check.
        M6 Law: Replay must be pressure-aware.
        """
        return self._metrics.quota_used_bytes < max_bytes

    @property
    def metrics(self) -> SinkMetrics:
        return self._metrics
