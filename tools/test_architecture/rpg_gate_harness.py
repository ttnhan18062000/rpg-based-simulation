"""The rpg gate harness: every (world, seed) runs in a fresh, fully pinned Python process and yields one metric document.

TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS (child 3 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). Two findings of 2026-10-09 shape it:
process-global state leaks between tests in one process (the strict xfail, the CONFLICT-04 xdist red), and tests are governor-mode-sensitive. So
no two runs share a process, and every pin is explicit.

Layers (this module orchestrates, ``rpg_gate_run`` is the child process):

* Child ``python -m tools.test_architecture.rpg_gate_run run``: compiles the world (``WorldRepository.load_world_with_context`` then
  ``WorldCompiler.compile``), builds a ``Kernel`` with ``PinnedNormalGovernor``, ``LocalSequentialExecutor``, ``flags={"audit_mode": True,
  "no_frame_pacing": True}`` and ``max_tick_budget_ms=1e9``, runs the ticks, shuts the kernel down (which flushes the recorded events), calls the metrics
  module with a ``RunArtifacts`` (world, seed, ticks, sha, final state, run directory holding the typed event stream) and writes the document. ``... pool`` calls the module's ``pool`` for one world.
* :func:`run_matrix` here starts one child per (world, seed) with a bounded worker count. A crashed, timed-out or malformed run becomes a ``no-data``
  document carrying the error; the others still complete. After all seeds of a world are done, a fresh process pools them; a world with any
  ``no-data`` seed gets a ``no-data`` pooled document, never a partial pool. The harness never reads ``counts``.

The metrics module (rpg's, planned at ``src.observability.rpg_gate_metrics``; named by ``module`` or ``module:attr`` on the command line) provides
``compute(run_artifacts) -> document or list[metric]`` and ``pool(docs) -> list[metric]`` following the ``rpg-gate-metrics/v1`` contract in the epic ticket.
The harness keeps only the metrics and writes the document header itself.

Document (``rpg-gate-metrics/v1``): ``{"schema", "status": "ok"|"no-data", "world", "seed", "ticks", "sha", "harness_hash", "metrics": [...], "reason"?, "error"?}``.
A ``no-data`` document carries ``reason``: ``run_error`` (an exception in the simulation, world compile or ticks; with ``exception_type``; an rpg defect),
``metric_error`` (an exception in rpg's ``compute`` or ``pool``), ``harness_error`` (a timeout, a bad document, a child that never started) or
``seed_no_data`` (the pool was skipped because a seed has no data).
It is written with sorted keys and carries no time or path, so the same (SHA, world, seed) gives byte-identical bytes. Wall time and peak memory go
to a sidecar ``<doc>.cost.json`` and ``matrix.json``, never into the document.

Harness hash (:func:`harness_hash`): sha256 over the harness sources, the pin settings, the config bytes and the metrics module's name and source
(read from disk, never imported; ``src/`` simulation code is deliberately not hashed); every document records it, and baseline staleness
compares it.

``tools/`` imports ``tests.helpers.kernel_pinning`` on purpose: the pinned governor is the one shared copy, and a guard in ``tests/architecture/`` forbids local copies.

Run directories: each child's ``Kernel`` gets ``run_id = rpg-gate-<world>-s<seed>-<sha8>-<invocation token>`` (the token keeps two invocations on one SHA apart) so it writes ``data/runs/<run_id>``; the harness removes exactly
that directory afterwards unless ``keep_runs`` is set (CLAUDE.md: clean only the run data this session wrote, by id).

CLI (``--metrics-module`` defaults to :data:`DEFAULT_METRICS_MODULE`)::

    python -m tools.test_architecture.rpg_gate_harness --config FILE [--metrics-module MOD[:ATTR]] --out DIR [--workers N] [--sha SHA] [--keep-runs] [--timeout S]
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from tools.test_architecture.rpg_gate_baseline import GateConfig, load_config

SCHEMA = "rpg-gate-metrics/v1"
OK, NO_DATA = "ok", "no-data"
RUNS_DIR = Path("data/runs")
RUN_MODULE = "tools.test_architecture.rpg_gate_run"
# The ONE place rpg's metric module is named (planned home); swapping the stub for it is this line.
DEFAULT_METRICS_MODULE = "src.observability.rpg_gate_metrics"
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT_S = 3600.0

PIN_SETTINGS: Dict[str, Any] = {
    "governor": "PinnedNormalGovernor",
    "executor": "LocalSequentialExecutor",
    "flags": {"audit_mode": True, "no_frame_pacing": True},
    "profile": "PROD_SMALL with max_tick_budget_ms=1e9",
    "world_loader": "WorldRepository.load_world_with_context + WorldCompiler.compile",
    "metrics_module": "named and hashed per invocation (see harness_hash)",
}

_HARNESS_SOURCES = (
    "tools/test_architecture/rpg_gate_harness.py",
    "tools/test_architecture/rpg_gate_run.py",
    "tests/helpers/kernel_pinning.py",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _module_source(spec: str, root: Path) -> bytes:
    """The source of the metrics module ``spec`` (``module`` or ``module:attr``), found on disk under ``root`` without importing anything.
    A module that is not there yet (rpg's, before it lands) hashes as a fixed marker, so its arrival changes the hash."""
    relative = Path(*spec.partition(":")[0].split("."))
    for candidate in (root / relative.with_suffix(".py"), root / relative / "__init__.py"):
        if candidate.is_file():
            return candidate.read_bytes()
    return b"<metrics module not found>"


def harness_hash(config_path: Path, root: Optional[Path] = None, metrics_module: str = "") -> str:
    """A stable hash of the harness code, the pin settings, the config and the metrics module's source; any change to one of them changes it.

    The metrics module is hashed so that a changed metric definition makes every older baseline stale. Simulation code under ``src/`` is deliberately not
    hashed: a behaviour change there is what the gate exists to detect.
    """
    root = root or repo_root()
    digest = hashlib.sha256()
    digest.update(metrics_module.encode())
    digest.update(_module_source(metrics_module, root) if metrics_module else b"")
    for rel in _HARNESS_SOURCES:
        digest.update(rel.encode())
        digest.update((root / rel).read_bytes())
    digest.update(json.dumps(PIN_SETTINGS, sort_keys=True).encode())
    digest.update(Path(config_path).read_bytes())
    return digest.hexdigest()


def run_id_for(world: str, seed: int, sha: str, token: str = "") -> str:
    """``token`` is per invocation, so two invocations on the same SHA never share a run directory."""
    return f"rpg-gate-{world}-s{seed}-{sha[:8]}" + (f"-{token}" if token else "")


def doc_name(world: str, seed: Optional[int]) -> str:
    return f"{world}__s{seed}.json" if seed is not None else f"{world}__pooled.json"


def dump_doc(doc: Dict[str, Any]) -> str:
    return json.dumps(doc, sort_keys=True, indent=2) + "\n"


HARNESS_ERROR, SEED_NO_DATA = "harness_error", "seed_no_data"


def no_data_doc(world: str, seed: Optional[int], ticks: int, sha: str, hhash: str, error: str, reason: str = HARNESS_ERROR) -> Dict[str, Any]:
    """A ``no-data`` document. ``reason`` is ``run_error`` / ``metric_error`` (written by the child, which knows the phase) or ``harness_error`` (a timeout, a bad
    document, a child that never started) or ``seed_no_data`` (a pool that was skipped because a seed has no data)."""
    doc: Dict[str, Any] = {"schema": SCHEMA, "status": NO_DATA, "reason": reason, "world": world, "ticks": ticks, "sha": sha, "harness_hash": hhash, "metrics": [], "error": error}
    if seed is not None:
        doc["seed"] = seed
    return doc


@dataclass(frozen=True)
class RunCost:
    wall_seconds: float
    peak_rss_mb: Optional[float]


def _child_env() -> Dict[str, str]:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    root = str(repo_root())
    env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _call_child(args: Sequence[str], timeout_s: float) -> Optional[str]:
    """Run a child; return ``None`` on success or a one-line error."""
    try:
        done = subprocess.run([sys.executable, "-m", RUN_MODULE, *args], cwd=repo_root(), env=_child_env(), capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return f"timed out after {timeout_s:g}s"
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).strip().splitlines()
        return f"exit {done.returncode}: {tail[-1] if tail else 'no output'}"
    return None


def _read_ok_doc(path: Path) -> Optional[str]:
    """``None`` when ``path`` holds a usable ok document, else the reason it does not."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"no readable document ({exc.__class__.__name__})"
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not isinstance(doc.get("metrics"), list):
        return "document does not follow rpg-gate-metrics/v1"
    return None


def run_one(world: str, seed: int, config: GateConfig, out_dir: Path, *, metrics_module: str, sha: str, hhash: str, keep_runs: bool, timeout_s: float, token: str = "") -> Path:
    """Run one (world, seed) in a fresh process; the result file is always written (a ``no-data`` document on any failure)."""
    target = out_dir / doc_name(world, seed)
    run_id = run_id_for(world, seed, sha, token)
    started = time.monotonic()
    error = _call_child(
        ["run", "--world", world, "--seed", str(seed), "--ticks", str(config.ticks), "--metrics-module", metrics_module, "--sha", sha,
         "--harness-hash", hhash, "--run-id", run_id, "--out", str(target)],
        timeout_s,
    )
    if error is None:
        error = _read_ok_doc(target)
    if error is not None:
        target.write_text(dump_doc(no_data_doc(world, seed, config.ticks, sha, hhash, error)), encoding="utf-8")
    if not keep_runs:
        shutil.rmtree(repo_root() / RUNS_DIR / run_id, ignore_errors=True)  # exactly this run's directory, by id
    cost_path = target.with_name(target.name + ".cost.json")
    peak = None
    try:
        peak = json.loads(cost_path.read_text()).get("peak_rss_mb")
    except (OSError, json.JSONDecodeError):
        pass
    cost_path.write_text(json.dumps({"wall_seconds": round(time.monotonic() - started, 3), "peak_rss_mb": peak}, sort_keys=True) + "\n", encoding="utf-8")
    return target


def pool_world(world: str, seed_paths: Sequence[Path], config: GateConfig, out_dir: Path, *, metrics_module: str, sha: str, hhash: str, timeout_s: float) -> Path:
    """Pool one world's per-seed documents in a fresh process; any ``no-data`` seed makes the pooled document ``no-data``."""
    target = out_dir / doc_name(world, None)
    bad = [p.name for p in seed_paths if json.loads(p.read_text(encoding="utf-8")).get("status") != OK]
    error: Optional[str] = f"no pool: seed document(s) without data: {', '.join(bad)}" if bad else None
    if error is not None:
        target.write_text(dump_doc(no_data_doc(world, None, config.ticks, sha, hhash, error, SEED_NO_DATA)), encoding="utf-8")
        return target
    if error is None:
        error = _call_child(
            ["pool", "--world", world, "--ticks", str(config.ticks), "--metrics-module", metrics_module, "--sha", sha, "--harness-hash", hhash,
             "--out", str(target), "--docs", *[str(p) for p in seed_paths]],
            timeout_s,
        )
    if error is None:
        error = _read_ok_doc(target)
    if error is not None:
        target.write_text(dump_doc(no_data_doc(world, None, config.ticks, sha, hhash, error)), encoding="utf-8")
    return target


def run_matrix(
    config: GateConfig,
    config_path: Path,
    out_dir: Path,
    *,
    metrics_module: str,
    sha: str,
    workers: int = DEFAULT_WORKERS,
    keep_runs: bool = False,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> Dict[str, Any]:
    """Run every (world, seed), pool each world, write ``matrix.json`` and return it. One failing run never stops the others."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    hhash = harness_hash(config_path, metrics_module=metrics_module)
    token = f"{os.getpid()}-{int(time.time()) % 100000}"
    jobs = [(w, s) for w in config.worlds for s in config.seeds]
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            (w, s): pool.submit(run_one, w, s, config, out_dir, metrics_module=metrics_module, sha=sha, hhash=hhash, keep_runs=keep_runs, timeout_s=timeout_s, token=token)
            for w, s in jobs
        }
        seed_paths = {key: fut.result() for key, fut in futures.items()}
    pooled = {
        w: pool_world(w, [seed_paths[(w, s)] for s in config.seeds], config, out_dir, metrics_module=metrics_module, sha=sha, hhash=hhash, timeout_s=timeout_s)
        for w in config.worlds
    }
    runs: List[Dict[str, Any]] = []
    for (w, s), path in seed_paths.items():
        doc = json.loads(path.read_text(encoding="utf-8"))
        cost = json.loads(path.with_name(path.name + ".cost.json").read_text())
        runs.append({"world": w, "seed": s, "status": doc["status"], "file": path.name, **cost, **({"error": doc["error"]} if "error" in doc else {})})
    matrix = {
        "schema": "rpg-gate-matrix/v1",
        "sha": sha,
        "harness_hash": hhash,
        "wall_seconds": round(time.monotonic() - started, 3),
        "workers": workers,
        "runs": runs,
        "pooled": {w: {"file": p.name, "status": json.loads(p.read_text(encoding="utf-8"))["status"]} for w, p in pooled.items()},
    }
    (out_dir / "matrix.json").write_text(json.dumps(matrix, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return matrix


def _git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root(), capture_output=True, text=True, check=True).stdout.strip()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--metrics-module", default=DEFAULT_METRICS_MODULE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--sha")
    parser.add_argument("--only-world", action="append", default=[], help="run only this world of the config (repeatable); a CI shard runs one world")
    parser.add_argument("--keep-runs", action="store_true")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.only_world:
        unknown = [w for w in args.only_world if w not in config.worlds]
        if unknown:
            parser.error(f"--only-world not in the config: {unknown}")
        config = dataclasses.replace(config, worlds=tuple(w for w in config.worlds if w in args.only_world))
    matrix = run_matrix(config, args.config, args.out, metrics_module=args.metrics_module, sha=args.sha or _git_head(),
                        workers=args.workers, keep_runs=args.keep_runs, timeout_s=args.timeout)
    bad = [r for r in matrix["runs"] if r["status"] != OK]
    print(f"{len(matrix['runs']) - len(bad)}/{len(matrix['runs'])} runs ok in {matrix['wall_seconds']}s; matrix: {args.out / 'matrix.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
