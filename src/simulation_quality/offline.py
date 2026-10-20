"""SimQ scores a run offline, from the run's lossless ``simulation_events.jsonl`` (decision 80 C).

The live stream (in-process queue or broker) sheds events under pressure, so a score taken from it depends on host speed. ``EventRecorder`` writes every event that
passed its mode filter to ``simulation_events.jsonl`` (TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER). This module replays that file, in file order,
through a fresh :class:`QualityHub`; the live feed stays display-only. Calibration, the long-run observation and the compare tools score through here.

* A run directory without the file is refused (:class:`RunNotReplayable`), never scored as an empty run.
* The report is a function of the file and the weights only: ``generated_at`` is the fixed marker :data:`OFFLINE_GENERATED_AT` (the live report carries the wall clock), so the
  same run directory gives a byte-identical ``quality_report.json`` on any host and under any load.
* Per-type event counts of the replayed file are an output (:attr:`ReplayResult.event_counts_by_type`), keyed by the type in the file, before SimQ's own vocabulary translation.
* A run that is not recorded host-independent (the manifest's ``signals_zeroed``) can be refused by the caller (``require_host_independent=True``); the sidecar that records it
  beside the report is written by the tool (``tools/simq_score_run.py``, ``calibrate_simq``), which also owns the compare refusals.
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional

from src.observability.events import ObservabilityEventEnvelope

logger = logging.getLogger(__name__)

EVENTS_FILE = "simulation_events.jsonl"
OFFLINE_GENERATED_AT = "offline-replay"


class RunNotReplayable(ValueError):
    """The run directory cannot be scored offline (no lossless event file, scoring switched off, or not recorded host-independent)."""


@dataclass
class ReplayResult:
    event_count: int = 0
    skipped_lines: int = 0
    event_counts_by_type: Dict[str, int] = field(default_factory=dict)


def events_path(run_dir: str | os.PathLike) -> str:
    return os.path.join(os.fspath(run_dir), EVENTS_FILE)


def require_replayable(run_dir: str | os.PathLike) -> str:
    """The path of ``run_dir``'s lossless event file; raise :class:`RunNotReplayable` when there is none."""
    path = events_path(run_dir)
    if not os.path.isfile(path):
        raise RunNotReplayable(f"{os.fspath(run_dir)}: no {EVENTS_FILE}; SimQ scores a run only from its lossless event file, so the run is refused")
    return path


def iter_envelopes(path: str) -> Iterator[Optional[ObservabilityEventEnvelope]]:
    """One item per non-blank line of ``path``: the envelope, or ``None`` for a line that is not a valid event (the caller counts it)."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                data["related_entity_ids"] = tuple(data.get("related_entity_ids") or ())
                yield ObservabilityEventEnvelope(**data)
            except Exception as exc:  # noqa: BLE001 - a corrupt line is counted and skipped, as the calibration replay always did
                logger.debug("Skipped JSONL event: %s", exc)
                yield None


def replay_run_dir(run_dir: str | os.PathLike, hub: Any) -> ReplayResult:
    """Replay ``run_dir``'s lossless event file through ``hub`` in file order; counts per original event type are in the result."""
    path = require_replayable(run_dir)
    counts: Counter[str] = Counter()
    result = ReplayResult()
    for envelope in iter_envelopes(path):
        if envelope is None:
            result.skipped_lines += 1
            continue
        counts[envelope.event_type] += 1
        hub.on_envelope(envelope)
        result.event_count += 1
    result.event_counts_by_type = dict(sorted(counts.items()))
    return result


def build_hub(weights: Any, out_dir: str | os.PathLike, run_id: str) -> tuple[Any, Any]:
    """A fresh hub with every scorer and a persistence that writes ``quality_scores.jsonl`` into ``out_dir``; returns ``(hub, persistence)``."""
    from src.simulation_quality.persistence import QualityPersistence
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.scorers import build_all_scorers

    persistence = QualityPersistence(os.fspath(out_dir))
    return QualityHub(build_all_scorers(weights), weights, persistence, run_id=run_id), persistence


def _require_recorded_host_independent(run_dir: str | os.PathLike) -> None:
    """Refuse a run whose own manifest does not record ``signals_zeroed`` as True (the same rule the compare tools apply)."""
    from pathlib import Path

    from src.observability.reporting.artifact_repository import RunArtifactRepository
    from src.observability.reporting.run_determinism import NonAuditRunError, require_host_independent_runs

    path = Path(os.fspath(run_dir))
    try:
        manifest = json.loads(Path(RunArtifactRepository(base_dir=str(path.parent)).resolve_path(path.name, "manifest")).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    try:
        require_host_independent_runs({path.name: manifest if isinstance(manifest, dict) else {}})
    except NonAuditRunError as exc:
        raise RunNotReplayable(str(exc)) from exc


def score_run_dir(
    run_dir: str | os.PathLike,
    weights: Any,
    out_dir: str | os.PathLike,
    run_id: Optional[str] = None,
    require_host_independent: bool = False,
):
    """Score ``run_dir`` offline: replay, build the report, write ``quality_report.json`` and ``quality_scores.jsonl`` into ``out_dir``; return ``(report, ReplayResult)``."""
    if os.environ.get("QUALITY_SCORING_DISABLED") == "1":
        raise RunNotReplayable("QUALITY_SCORING_DISABLED=1: the hub would score nothing; unset it to score a run offline")
    require_replayable(run_dir)
    if require_host_independent:
        _require_recorded_host_independent(run_dir)
    hub, persistence = build_hub(weights, out_dir, run_id or os.path.basename(os.path.normpath(os.fspath(run_dir))))
    try:
        result = replay_run_dir(run_dir, hub)
        report = hub.get_quality_report(generated_at=OFFLINE_GENERATED_AT)
        persistence.write_report(report)
    finally:
        persistence.shutdown()
    return report, result
