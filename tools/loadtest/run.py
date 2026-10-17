"""Run the Locust API scenario at fixed user steps and record the method with the numbers.

Per step and repeat: Locust CSVs, a USE sample file (docker stats of the backend container, vmstat, the Locust
process's own CPU). Per run: manifest.json (commit, image digests, host, engine state, observability on/off, fleet
state) and summary.json plus a printed table. Locust runs on the host, outside the backend container, and shares the
host's vCPUs with it; its own CPU is sampled for that reason. The numbers of a smoke run are not a measurement.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from tools.loadtest import summary
from tools.loadtest.keys import DEFAULT_KEYS_FILE, load_keys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_OUT = HERE / "runs"


def sh(*cmd: str, timeout: float = 20.0) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def backend_container() -> str:
    ids = sh("docker", "compose", "ps", "-q", "backend").splitlines()
    return ids[0] if ids else ""


def get_json(url: str, key: str | None) -> dict | None:
    request = urllib.request.Request(url, headers={"X-API-Key": key} if key else {})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read())
    except Exception:  # noqa: BLE001 -- engine state is best effort, never fails the run
        return None


def build_manifest(host: str, key: str | None, args: argparse.Namespace) -> dict:
    container = backend_container()
    services = sh("docker", "compose", "ps", "--services").split()
    return {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "is_measurement": not args.smoke,
        "commit": sh("git", "rev-parse", "HEAD"),
        "dirty": bool(sh("git", "status", "--porcelain")),
        "image_digests": {
            "backend_image_id": sh("docker", "inspect", "--format", "{{.Image}}", container) if container else "",
            "backend_repo_digest": sh("docker", "inspect", "--format", "{{.Config.Image}}", container) if container else "",
        },
        "host": {
            "nproc": int(sh("nproc") or 0),
            "lscpu": sh("lscpu"),
            "free_m": sh("free", "-m"),
            "virtualization": sh("systemd-detect-virt") or "unknown",
        },
        "engine_state": get_json(f"{host}/api/v1/observability/live/status", key),
        "observability_profile_on": "prometheus" in services,
        "compose_services_running": services,
        "fleet": {"uptime": sh("uptime"), "claude_processes": int(sh("pgrep", "-fc", "claude") or 0)},
        "settings": {k: v for k, v in vars(args).items() if k not in {"keys_file"}},
    }


class UseSampler(threading.Thread):
    """Samples backend container and host USE signals until stopped; ``peaks()`` summarises them."""

    def __init__(self, container: str, locust_pid: int, interval: float) -> None:
        super().__init__(daemon=True)
        self.container, self.locust_pid, self.interval = container, locust_pid, interval
        self.stop_event = threading.Event()
        self.rows: list[dict] = []
        self._vmstat = subprocess.Popen(["vmstat", "1"], stdout=subprocess.PIPE, text=True)

    def run(self) -> None:
        while not self.stop_event.wait(self.interval):
            row: dict = {"t": time.time()}
            if self.container:
                raw = sh("docker", "stats", "--no-stream", "--format", "{{json .}}", self.container, timeout=15)
                try:
                    stats = json.loads(raw)
                    row["backend_cpu_pct"] = float(stats["CPUPerc"].rstrip("%"))
                    row["backend_mem_mb"] = _to_mb(stats["MemUsage"].split("/")[0])
                    row["net_io"], row["block_io"] = stats["NetIO"], stats["BlockIO"]
                except (ValueError, KeyError):
                    pass
            row["locust_cpu_pct"] = float(sh("ps", "-o", "%cpu=", "-p", str(self.locust_pid)) or 0)
            self.rows.append(row)

    def finish(self) -> list[dict]:
        self.stop_event.set()
        self._vmstat.terminate()
        vm_rows = []
        for line in (self._vmstat.stdout.read() or "").splitlines():
            parts = line.split()
            if len(parts) >= 17 and parts[0].isdigit():
                vm_rows.append({"run_queue": int(parts[0]), "swap_kb_s": int(parts[6]) + int(parts[7]),
                                "bi": int(parts[8]), "bo": int(parts[9]), "host_cpu_pct": int(parts[12]) + int(parts[13])})
        return [{"source": "docker", **r} for r in self.rows] + [{"source": "vmstat", **r} for r in vm_rows]


def _to_mb(text: str) -> float:
    match = re.match(r"\s*([\d.]+)\s*([KMG]i?B)", text)
    if not match:
        return 0.0
    return float(match.group(1)) * {"KB": 1 / 1024, "KiB": 1 / 1024, "MB": 1, "MiB": 1, "GB": 1024, "GiB": 1024}[match.group(2)]


def peak_use(rows: list[dict]) -> dict[str, float]:
    keys = ("backend_cpu_pct", "backend_mem_mb", "locust_cpu_pct", "host_cpu_pct", "run_queue", "swap_kb_s", "bi", "bo")
    return {k: max((r[k] for r in rows if k in r), default=0.0) for k in keys}


def run_locust(users: int, seconds: int, csv_prefix: Path | None, host: str, env: dict) -> subprocess.Popen:
    cmd = [sys.executable, "-m", "locust", "-f", str(HERE / "locustfile.py"), "--headless", "-u", str(users),
           "-r", str(users), "-t", f"{seconds}s", "--host", host, "--only-summary"]
    if csv_prefix:
        cmd += ["--csv", str(csv_prefix)]
    return subprocess.Popen(cmd, env=env, cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="http://localhost:8000")
    ap.add_argument("--users", default="10,25,50,100,200", help="comma-separated user steps")
    ap.add_argument("--duration", type=int, default=60, help="seconds per step after warm-up")
    ap.add_argument("--warmup", type=int, default=15, help="unrecorded warm-up seconds before each step")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--sample-interval", type=float, default=2.0)
    ap.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_FILE)
    ap.add_argument("--single-key", action="store_true", help="all users share key 0 (shows the per-key limit)")
    ap.add_argument("--mem-limit-mb", type=float, default=1024.0, help="backend mem_limit in compose.yaml")
    ap.add_argument("--label", default="run")
    ap.add_argument("--smoke", action="store_true", help="label the numbers as a smoke run, not a measurement")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    keys = load_keys(args.keys_file)
    steps = [int(u) for u in args.users.split(",")]
    if not keys:
        print(f"no keys in {args.keys_file}; run tools/loadtest/keys.py", file=sys.stderr)
        return 2
    if not args.single_key and max(steps) > len(keys):
        print(f"warning: {max(steps)} users but only {len(keys)} keys; keys will be shared", file=sys.stderr)
    out = args.out / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True)
    env = {**os.environ, "LOADTEST_KEYS_FILE": str(args.keys_file), "PYTHONPATH": str(REPO)}
    if args.single_key:
        env["LOADTEST_SINGLE_KEY"] = "1"
    manifest = build_manifest(args.host, keys[0], args)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    container = backend_container()
    nproc = manifest["host"]["nproc"] or 1

    per_step: dict[int, dict] = {}
    for users in steps:
        repeats, uses, rates_all = [], [], []
        for repeat in range(args.repeats):
            if args.warmup:
                run_locust(users, args.warmup, None, args.host, env).wait()
            prefix = out / f"step{users}_r{repeat}"
            proc = run_locust(users, args.duration, prefix, args.host, env)
            sampler = UseSampler(container, proc.pid, args.sample_interval)
            sampler.start()
            proc.wait()
            rows = sampler.finish()
            (out / f"step{users}_r{repeat}_use.json").write_text(json.dumps(rows))
            stats = summary.parse_stats_csv(Path(f"{prefix}_stats.csv"))
            failures = summary.parse_failures_csv(Path(f"{prefix}_failures.csv"))
            repeats.append(stats)
            uses.append(peak_use(rows))
            rates_all.append(summary.error_rates(stats.requests, failures))
        per_step[users] = {
            "spread": summary.aggregate_repeats(repeats),
            "peak_use": {k: max(u[k] for u in uses) for k in uses[0]},
            "error_rates": {k: max(r[k] for r in rates_all) for k in rates_all[0]},
        }

    first = summary.first_saturation(
        ((u, d["peak_use"], d["error_rates"]) for u, d in per_step.items()), nproc=nproc, mem_limit_mb=args.mem_limit_mb)
    result = {"is_measurement": not args.smoke, "steps": per_step,
              "first_saturation": {"users": first[0], "resource": first[1], "value": first[2]} if first else None}
    (out / "summary.json").write_text(json.dumps(result, indent=2))
    print(("SMOKE RUN -- not a measurement\n" if args.smoke else "") + f"{'users':>5} {'req/s med (min-max)':>24} {'p50':>6} {'p95':>6} {'p99':>6} {'429':>6} {'5xx':>6}")
    for users, d in per_step.items():
        s = d["spread"]
        print(f"{users:>5} {s['rps']['median']:>10.1f} ({s['rps']['min']:.1f}-{s['rps']['max']:.1f}) {s['p50']['median']:>6.0f} "
              f"{s['p95']['median']:>6.0f} {s['p99']['median']:>6.0f} {d['error_rates']['admission_429']:>6.1%} {d['error_rates']['server_5xx']:>6.1%}")
    print("first saturated:", f"{first[1]} at {first[0]} users (value {first[2]:.1f})" if first else "none within the tested steps")
    print(f"Locust peak CPU shares the {nproc} vCPUs with the backend: see *_use.json (locust_cpu_pct). Output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
