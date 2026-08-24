#!/usr/bin/env python3
"""Standalone measurement harness for TCK-20260821-LIVE-MAP-PERF-VALIDATION.

Measures the byte size of the live-map WebSocket entity-delta broadcast
(`/api/v1/ws`) at a given entity count, in both JSON and msgpack wire
encodings, over two buckets:

- `steady_state`: real per-tick delta messages captured live from a running
  server, exactly what production traffic sends.
- `full_scan`: a synthetic, harness-computed "what would a full-state
  broadcast weigh" estimate (see "Full-scan finding" below for why this is
  NOT a live WS capture).

One known gap this script routes around without touching production code
(see staging_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/investigation.md):
`python3 -m src serve --entities N` silently ignores `--entities`
(`src/cli/entry.py::_run_serve` never reads `args.entities`). This script
never shells out to `-m src serve`; its own `--internal-serve` mode
replicates `_run_serve`'s boot sequence but monkeypatches the
`V2EngineManager` symbol inside `src.api.server`'s module namespace (only in
this subprocess's own process memory) so the FastAPI lifespan's
`V2EngineManager(profile)` call picks up a custom `entities_count`/`seed`.
This patch is applied only inside this script's own subprocess, to module
globals of a fresh Python interpreter it started -- never to any file under
src/ or frontend/src/.

Full-scan finding (discovered during Implement, corrects plan.md Step 1
point 7's assumption): plan.md expected a dedicated
`Kernel(..., flags={"force_full_scan": True})` boot to make the live WS
delta's `changed` list include every entity, citing
`src/engine/pipeline.py`'s "Phase 17 Law" (a method named
`AuthoritativeApplyPipeline._refresh_dirty_set`). Verified against source
during Implement: `_refresh_dirty_set` is defined but never called anywhere
in the codebase (confirmed by a full-repo grep for its name -- zero call
sites). `force_full_scan=True` genuinely does widen phase-level entity
iteration (`src/core/dirty.py::get_relevant_entity_ids` returns every entity
as a phase's candidate set) and does force every phase to run
(`PhaseDependencyGraph.should_run_phase`'s override), but the DirtySet that
actually reaches the WS broadcast is built exclusively by
`DirtySetBuilder.mark_from_update()`, called several times through
`refine()` (pipeline.py lines 261, 296, 314, 329, 352) -- which only marks
entities that produced a real `EntityUpdate` this tick, regardless of
`force_full_scan`. So no live WS message with an all-entities `changed` list
is obtainable today via any documented mechanism (neither investigation.md's
originally-assumed `tick % 20` heartbeat, nor plan.md's corrected
`force_full_scan` flag). This is reported as a genuine engine-behavior
finding (AC4), not fixed here (fixing `_refresh_dirty_set`'s dead wiring
would be a `src/engine/pipeline.py` change, barred by this ticket's Out of
Scope). In its place, `full_scan` is computed synthetically and in-process,
by building the same entity population `V2EngineManager._build()` would
(via a real `V2EngineManager(profile, entities_count=N)` construction, no
server/HTTP/WS involved) and passing every alive entity through the exact
same `StatePresenter.present_entity_slim` + `jsonable_encoder` +
`json.dumps`/`msgpack.packb` code path the real WS handler uses
(`src/api/ws/stream.py::stream_ws`) -- giving an honest, code-path-faithful
"what a full broadcast would cost" estimate, clearly labeled as
harness-synthesized rather than a captured live message. This also removes
the need for a second server subprocess, a welcome resource-safety
simplification given this sandbox's tight memory budget.

Auth: reuses the exact `RPG_API_KEY_HASHES` env var + `X-API-Key` header
pattern already proven end-to-end in tests/api/test_ws_protocol.py and
tickets/done/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md.

Must run under the repo's pydantic-capable interpreter:
    .venv/bin/python3 tools/perf/live_map_ws_payload_measure.py --entities 500

Resource guards (see plan.md Open Question 2): a pre-flight `free -m`
available-memory check gates any run at >=2000 entities (the CLASS_B-scale
attempt); an in-flight guard polls `free -m` every `--guard-every` samples in
the steady-state run and aborts cleanly (process-group kill, partial results
recorded) if available memory drops below `--guard-floor-mb`.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import secrets
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

# Must run first, before any `import src...` anywhere in this process (driver
# or --internal-serve subprocess): when this file is invoked as a script
# (not `python3 -c`), sys.path[0] is this file's own directory
# (tools/perf/), not the repo root or cwd. Without this insert, `import src`
# falls through to this venv's editable-install finder
# (site-packages/__editable__.rpg_based_simulation-*.pth), which resolves to
# the MAIN CHECKOUT's src/ (a different git worktree), not this worktree's
# own, possibly-diverged src/ -- confirmed live during Implement (the main
# checkout's src/api/presenters/state_presenter.py lacks
# present_entity_slim, a method this worktree's branch added).
sys.path.insert(0, str(REPO_ROOT))

_CLIENT_ID = "live-map-perf-validation"


def _raw_key_and_hash() -> tuple[str, str]:
    raw = f"{_CLIENT_ID}-{secrets.token_hex(8)}"
    return raw, hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _available_mb() -> Optional[int]:
    """Parses `free -m`'s `Mem:` line `available` column. Returns None (never
    raises) if `free` is unavailable or the output shape is unexpected --
    a guard check that can't itself crash the harness it's protecting."""
    try:
        out = subprocess.run(
            ["free", "-m"], capture_output=True, text=True, check=True, timeout=5
        ).stdout
        for line in out.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                return int(parts[6])
    except Exception:
        return None
    return None


def _percentiles(values: List[int]) -> Dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "p50": None, "p95": None, "p99": None}
    s = sorted(values)
    n = len(s)

    def pct(p: float) -> float:
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        return float(s[idx])

    return {
        "count": n,
        "min": float(s[0]),
        "max": float(s[-1]),
        "mean": float(statistics.mean(s)),
        "p50": pct(0.50),
        "p95": pct(0.95),
        "p99": pct(0.99),
    }


def _kill_process_group(proc: "subprocess.Popen[bytes]", grace: float = 3.0) -> None:
    """Kills the whole process group `proc` was launched with
    (`start_new_session=True`), not just its own PID -- uvicorn and its
    reload/worker machinery can spawn children that a plain
    `Popen.terminate()` on the parent alone would leave running and still
    holding memory, defeating the resource guard's purpose."""
    if proc.poll() is not None:
        return
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + grace
    while time.time() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.1)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Internal server-boot mode -- runs in its own subprocess (start_new_session)
# ---------------------------------------------------------------------------

def _run_internal_serve(args: argparse.Namespace) -> None:
    import functools

    os.environ["RPG_API_KEY_HASHES"] = f"{_CLIENT_ID}:{args.api_key_hash}"

    import src.api.server as server_module
    from src.api.engine_manager import V2EngineManager as RealV2EngineManager
    from src.config.loader import ConfigLoader
    from src.logging.formatter import setup_v2_logging

    setup_v2_logging(level="ERROR", json_format=False)

    # Only this subprocess's own module namespace is patched -- never
    # src/api/server.py itself. See module docstring point 1.
    server_module.V2EngineManager = functools.partial(
        RealV2EngineManager, entities_count=args.entities, seed=args.seed
    )

    profile = ConfigLoader.load_profile(profile_name="cli_default", cli_overrides={})
    app = server_module.create_v2_app(profile)

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="error")


def _compute_synthetic_full_scan(entities: int, seed: int) -> Dict[str, Any]:
    """In-process, no-server estimate of "what a full-state WS broadcast
    would weigh" -- see module docstring's "Full-scan finding" for why no
    live WS message with an all-entities `changed` list is obtainable today.
    Uses the same entity-population logic (`V2EngineManager._build()`) and
    the same per-entity presenter/serialization code the real WS handler
    uses (`StatePresenter.present_entity_slim`, `jsonable_encoder`,
    `json.dumps`/`msgpack.packb` -- src/api/ws/stream.py::stream_ws)."""
    import msgpack
    from fastapi.encoders import jsonable_encoder

    from src.api.engine_manager import V2EngineManager
    from src.api.presenters.state_presenter import StatePresenter
    from src.config.loader import ConfigLoader

    profile = ConfigLoader.load_profile(profile_name="cli_default", cli_overrides={})
    manager = V2EngineManager(profile, entities_count=entities, seed=seed)
    state = manager.kernel.state

    changed = [
        StatePresenter.present_entity_slim(e)
        for e in state.entities.values()
        if e.combat.alive
    ]
    payload = {
        "tick": state.tick,
        "changed": changed,
        "removed": [],
        "events": [],
        "snapshot_as_of_tick": state.tick,
        "region_id": None,
    }
    encoded = jsonable_encoder(payload)
    json_byte_len = len(json.dumps(encoded).encode("utf-8"))
    msgpack_byte_len = len(msgpack.packb(encoded))

    return {
        "method": "synthetic in-process construction -- NOT a live WS capture, "
                  "see module docstring's Full-scan finding",
        "entity_count": len(changed),
        "json_bytes": json_byte_len,
        "msgpack_bytes": msgpack_byte_len,
    }


# ---------------------------------------------------------------------------
# Driver mode -- spawns the internal-serve subprocess, drives a real WS client
# ---------------------------------------------------------------------------

def _spawn_server(
    entities: int, seed: int, port: int, api_key_hash: str
) -> "subprocess.Popen[bytes]":
    cmd = [
        sys.executable, str(Path(__file__).resolve()),
        "--internal-serve",
        "--entities", str(entities),
        "--seed", str(seed),
        "--port", str(port),
        "--api-key-hash", api_key_hash,
    ]
    return subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def _wait_for_server(port: int, timeout: float = 30.0) -> bool:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status in (200, 503):
                    return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False


async def _collect_ws_run(
    port: int,
    raw_key: str,
    fmt: str,
    warmup_ticks: int,
    sample_target: int,
    max_wall_seconds: float,
    guard_every: int,
    guard_floor_mb: int,
) -> Dict[str, Any]:
    """Connects once, discards the initial handshake payload (minimal-summary
    shape, not a delta -- see manager.get_state()/stream.py), waits for the
    engine to report tick >= warmup_ticks on a received delta message, then
    records the byte length of every subsequent delta message until
    sample_target is reached or the wall-clock/memory guard trips."""
    import websockets

    samples: List[int] = []
    aborted = False
    abort_reason: Optional[str] = None
    warmup_tick_reached: Optional[int] = None
    start = time.time()

    uri = f"ws://127.0.0.1:{port}/api/v1/ws"
    async with websockets.connect(uri, additional_headers={"X-API-Key": raw_key}) as ws:
        await ws.send(json.dumps({"type": "handshake", "format": fmt}))
        await ws.recv()  # initial minimal-summary payload -- not sampled

        while len(samples) < sample_target:
            if time.time() - start > max_wall_seconds:
                aborted = True
                abort_reason = f"wall-clock budget ({max_wall_seconds}s) exceeded at {len(samples)} samples"
                break

            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
            except asyncio.TimeoutError:
                aborted = True
                abort_reason = f"no message received within 10s at {len(samples)} samples"
                break

            if fmt == "msgpack":
                import msgpack
                decoded = msgpack.unpackb(raw)
                byte_len = len(raw)
            else:
                decoded = json.loads(raw)
                byte_len = len(raw.encode("utf-8")) if isinstance(raw, str) else len(raw)

            msg_tick = decoded.get("tick", 0) if isinstance(decoded, dict) else 0

            if warmup_tick_reached is None:
                if msg_tick < warmup_ticks:
                    continue
                warmup_tick_reached = msg_tick

            samples.append(byte_len)

            if guard_every > 0 and len(samples) % guard_every == 0:
                avail = _available_mb()
                if avail is not None and avail < guard_floor_mb:
                    aborted = True
                    abort_reason = (
                        f"memory guard tripped: {avail}MB available < "
                        f"{guard_floor_mb}MB floor, at {len(samples)} samples"
                    )
                    break

    stats = _percentiles(samples)
    stats["aborted"] = aborted
    stats["abort_reason"] = abort_reason
    stats["warmup_ticks_target"] = warmup_ticks
    stats["warmup_tick_reached"] = warmup_tick_reached
    stats["wall_seconds"] = round(time.time() - start, 2)
    return stats


async def _run_steady_state_bucket(
    port: int,
    raw_key: str,
    warmup_ticks: int,
    sample_target: int,
    msgpack_sample_target: int,
    max_wall_seconds: float,
    guard_every: int,
    guard_floor_mb: int,
) -> Dict[str, Any]:
    json_stats = await _collect_ws_run(
        port, raw_key, "json", warmup_ticks, sample_target,
        max_wall_seconds, guard_every, guard_floor_mb,
    )
    msgpack_stats = await _collect_ws_run(
        port, raw_key, "msgpack", warmup_ticks=0, sample_target=msgpack_sample_target,
        max_wall_seconds=max(30.0, max_wall_seconds / 4), guard_every=guard_every,
        guard_floor_mb=guard_floor_mb,
    )
    return {"json_bytes": json_stats, "msgpack_bytes": msgpack_stats}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entities", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=str,
                         default=str(REPO_ROOT / "staging_artifacts" / "TCK-20260821-LIVE-MAP-PERF-VALIDATION" / "raw"))
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--warmup-ticks", type=int, default=100)
    parser.add_argument("--sample-ticks", type=int, default=1000)
    parser.add_argument("--msgpack-samples", type=int, default=50)
    parser.add_argument("--max-wall-seconds", type=float, default=240.0)
    parser.add_argument("--guard-every", type=int, default=50)
    parser.add_argument("--guard-floor-mb", type=int, default=300)
    parser.add_argument("--preflight-entities-threshold", type=int, default=2000)
    parser.add_argument("--preflight-required-mb", type=int, default=2500)

    # Internal server-boot mode (hidden from the ticket's public surface --
    # this process re-invokes itself with these flags, see _spawn_server).
    parser.add_argument("--internal-serve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--api-key-hash", type=str, default=None, help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.internal_serve:
        _run_internal_serve(args)
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / f"ws_payload_{args.entities}.json"
    aborted_path = out_dir / f"ws_payload_{args.entities}_ABORTED.json"

    if args.entities >= args.preflight_entities_threshold:
        avail = _available_mb()
        if avail is None or avail < args.preflight_required_mb:
            marker = {
                "entities": args.entities,
                "seed": args.seed,
                "attempted": False,
                "reason": "pre-flight memory check failed",
                "available_mb": avail,
                "required_mb": args.preflight_required_mb,
                "timestamp": time.time(),
            }
            _write_json(aborted_path, marker)
            print(f"NOT ATTEMPTED -- pre-flight memory check failed: "
                  f"{avail}MB available < {args.preflight_required_mb}MB required. "
                  f"Wrote {aborted_path}")
            return 0

    raw_key, key_hash = _raw_key_and_hash()

    result: Dict[str, Any] = {
        "entities": args.entities,
        "seed": args.seed,
        "attempted": True,
        "started_at": time.time(),
        "steady_state": None,
        "full_scan": None,
    }
    top_level_aborted = False

    async def _drive() -> None:
        nonlocal top_level_aborted

        # --- Steady-state run: real per-tick delta messages, live server ---
        server = _spawn_server(args.entities, args.seed, args.port, key_hash)
        try:
            ready = await _wait_for_server(args.port)
            if not ready:
                result["steady_state"] = {"aborted": True, "abort_reason": "server did not become healthy within timeout"}
                top_level_aborted = True
                return
            result["steady_state"] = await _run_steady_state_bucket(
                args.port, raw_key, args.warmup_ticks, args.sample_ticks, args.msgpack_samples,
                args.max_wall_seconds, args.guard_every, args.guard_floor_mb,
            )
            if result["steady_state"]["json_bytes"].get("aborted") or result["steady_state"]["msgpack_bytes"].get("aborted"):
                top_level_aborted = True
        finally:
            _kill_process_group(server)

    asyncio.run(_drive())

    # --- Full-scan bucket: synthetic, in-process, no server -- see module
    # docstring's "Full-scan finding" for why no live capture is possible.
    result["full_scan"] = _compute_synthetic_full_scan(args.entities, args.seed)

    result["finished_at"] = time.time()
    result["aborted"] = top_level_aborted

    dest = aborted_path if top_level_aborted else result_path
    _write_json(dest, result)
    print(f"Wrote {dest} (aborted={top_level_aborted})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
