"""What a SimQ run's own manifest says about host independence, and the sidecar that carries it next to the run's quality report.

TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT. rpg's ``RunManifest`` records ``audit_mode`` and ``signals_zeroed`` (booleans; absent in an older
manifest). Nothing here infers either one from a flag, a file name or the caller's own arguments: they are copied from ``run_manifest.json``, and anything that is not
a boolean (absent, null, a string) is ``None``, which every comparison tool reads as "not recorded" and refuses.

* :func:`read_run_determinism` reads one run directory's manifest (the file name comes from ``RunArtifactRepository.resolve_path``, never hard-coded here).
* :func:`write_sidecar` writes ``quality_report.run_determinism.json`` into a calibration directory: ``{"run_id", "audit_mode", "signals_zeroed"}``. ``calibrate_simq``
  calls it for the same run whose report it writes, so the sidecar can never describe a different run than the report beside it.
* :func:`load_sidecar` reads it back; a missing or unreadable sidecar is ``None`` (a stale calibration directory from before this record), which the comparison refuses.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from src.observability.reporting.artifact_repository import RunArtifactRepository

SIDECAR_NAME = "quality_report.run_determinism.json"
FIELDS = ("audit_mode", "signals_zeroed")


def _bool_or_none(value: Any) -> Optional[bool]:
    return value if isinstance(value, bool) else None


def read_run_determinism(run_dir: str | os.PathLike) -> Dict[str, Any]:
    """``{"run_id", "audit_mode", "signals_zeroed"}`` from ``<run_dir>``'s run manifest; a missing or unreadable manifest gives ``None`` for both fields."""
    run_dir = Path(run_dir)
    manifest_path = RunArtifactRepository(base_dir=str(run_dir.parent)).resolve_path(run_dir.name, "manifest")
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    if not isinstance(manifest, dict):
        manifest = {}
    return {"run_id": run_dir.name, **{field: _bool_or_none(manifest.get(field)) for field in FIELDS}}


def write_sidecar(cal_dir: str | os.PathLike, run_dir: str | os.PathLike) -> Dict[str, Any]:
    """Write the sidecar for ``run_dir`` into ``cal_dir`` and return what it holds."""
    record = read_run_determinism(run_dir)
    Path(cal_dir, SIDECAR_NAME).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def load_sidecar(cal_dir: str | os.PathLike) -> Optional[Dict[str, Any]]:
    """The sidecar of a calibration directory, or ``None`` when there is none (or it is not a JSON object)."""
    try:
        record = json.loads(Path(cal_dir, SIDECAR_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None
