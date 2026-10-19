"""Produce the ``rows.jsonl`` that ``simq_reanchor`` reads: every anchor key run twice in its own process under ``--audit-mode``, one row per run.

TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT. Before this tool the rows came from a driver that lived in one session's scratch directory. This is the
committed, repeatable producer. It decides nothing: whether a pair is an anchor is ``simq_reanchor``'s call (it refuses a run that is not recorded as audit_mode).

Row shape (one JSON object per line; pinned by ``tests/unit/tools/test_simq_audit_rows.py``)::

    {"key": run_key, "rep": 1|2, "exit": returncode, "wall_s": seconds, "run_id": the engine run id or None,
     "audit_mode": bool|None, "signals_zeroed": bool|None,
     "pillars": {PILLAR: {"grade", "norm", "raw", "events"[, "status", "min_events"]}}, "overall": [grade, score] | None}

``audit_mode`` and ``signals_zeroed`` are copied from the run's own ``run_manifest.json`` (read BEFORE the run directory is deleted; see ``simq_run_record``), never from this
tool's ``--audit-mode`` flag. Absent or null in the manifest (or no manifest) is ``None``: not recorded. ``status`` and ``min_events`` are copied only when the report carries them.

Each run's ``data/runs/<id>`` directory is removed by its exact id through ``done_checker_static.delete_data_run_paths`` (never a glob, never a sweep); only run ids this tool
created are named.

CLI::

    python -m tools.test_architecture.simq_audit_rows --fixture tests/simulation_quality/fixtures/grade_anchors.json --out OUTDIR [--workers 4] [--key KEY ...]

Writes ``OUTDIR/<key>__audit<rep>/{quality_report.json,stdout.txt}`` and ``OUTDIR/rows.jsonl``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from tools.gate_checks.done_checker_static import delete_data_run_paths
from tools.test_architecture.simq_run_record import read_run_determinism

REPS = (1, 2)
_RUN_DIR = re.compile(r"JSONL at: (data/runs/[^\s]+)")


def run_id_from_stdout(stdout: str) -> Optional[str]:
    match = _RUN_DIR.search(stdout)
    return Path(match.group(1)).name if match else None


def build_row(key: str, rep: int, returncode: int, wall_s: float, run_id: Optional[str], determinism: Mapping[str, Any], report: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """The row of one run. ``pillars`` and ``overall`` stay empty when the run did not complete (the consumer refuses an incomplete run)."""
    row: Dict[str, Any] = {
        "key": key, "rep": rep, "exit": returncode, "wall_s": round(wall_s, 1), "run_id": run_id,
        "audit_mode": determinism.get("audit_mode"), "signals_zeroed": determinism.get("signals_zeroed"), "pillars": {}, "overall": None,
    }
    if returncode == 0 and report is not None:
        for name, pillar in report["pillars"].items():
            entry = {"grade": pillar["grade"], "norm": pillar["normalized_score"], "raw": pillar["raw_score"], "events": pillar["event_count"]}
            for extra in ("status", "min_events"):
                if extra in pillar:
                    entry[extra] = pillar[extra]
            row["pillars"][name] = entry
        row["overall"] = [report["overall_grade"], report["overall_score"]]
    return row


def collect_row(
    key: str, rep: int, returncode: int, stdout: str, wall_s: float, out_dir: Path, runs_dir: Path = Path("data/runs"), proof_dir: Path = Path("reports/release_proof"),
) -> Dict[str, Any]:
    """Read one finished run, then delete its run directory by exact id. The manifest is read first; the directory is gone afterwards."""
    run_id = run_id_from_stdout(stdout)
    determinism = read_run_determinism(Path(runs_dir) / run_id) if run_id else {"audit_mode": None, "signals_zeroed": None}
    report_path = Path(out_dir) / "quality_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if returncode == 0 and report_path.exists() else None
    row = build_row(key, rep, returncode, wall_s, run_id, determinism, report)
    if run_id and (Path(runs_dir) / run_id).exists():
        delete_data_run_paths([run_id], runs_dir=runs_dir, proof_dir=proof_dir)
    return row


def _run_one(job: Tuple[str, int], out: Path) -> Dict[str, Any]:
    from tools.evaluate_simq import _parse_run_key, _resolve_world_name  # noqa: PLC0415  (imported lazily: it pulls the engine)

    key, rep = job
    run_out = out / f"{key}__audit{rep}"
    run_out.mkdir(parents=True, exist_ok=True)
    profile, seed, ticks = _parse_run_key(key)
    world = _resolve_world_name(profile)
    started = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "tools.calibrate_simq", "--name", world, "--profile", profile, "--seed", str(seed), "--ticks", str(ticks), "--output", str(run_out), "--audit-mode"],
        capture_output=True, text=True,
    )
    (run_out / "stdout.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return collect_row(key, rep, proc.returncode, proc.stdout, time.time() - started, run_out)


def produce(keys: Sequence[str], out: Path, workers: int = 4) -> List[Dict[str, Any]]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(key, rep) for key in keys for rep in REPS]
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(lambda job: _run_one(job, out), jobs))
    (out / "rows.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return rows


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", type=Path, required=True, help="grade_anchors.json (its keys are the runs)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--key", action="append", help="run only this anchor key (repeatable); default: every key in the fixture")
    args = parser.parse_args(argv)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    keys = args.key or [k for k in fixture if not k.startswith("_")]
    unknown = [k for k in keys if k not in fixture]
    if unknown:
        print(f"unknown anchor key(s): {unknown}", file=sys.stderr)
        return 2
    rows = produce(keys, args.out, args.workers)
    failed = [r for r in rows if r["exit"] != 0]
    print(f"{len(rows)} runs, {len(failed)} failed; rows at {args.out / 'rows.jsonl'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
