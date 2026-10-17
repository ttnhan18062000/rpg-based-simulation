"""Run the Locust API scenario at fixed user steps and record the method with the numbers.

Per run: a 30 s idle baseline (host swap and disk), then per step and repeat the Locust CSVs and a USE sample file
(docker stats of EVERY container in the compose project, vmstat, the Locust process's own CPU). manifest.json holds the
commit, the image id, the host, the engine state (read with a key that is not in the pool, before any load), the
observability profile on/off and the fleet state; summary.json and a printed table hold the results. Locust runs on
the host, outside the backend container, and shares the host's vCPUs with it; its own CPU is sampled for that reason.
The numbers of a smoke run are not a measurement.
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
from tools.loadtest.keys import DEFAULT_KEYS_FILE, DEFAULT_STATUS_KEY_FILE, load_keys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_OUT = HERE / "runs"


def sh(*cmd: str, timeout: float = 20.0) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def project_containers() -> list[str]:
    """Container ids of every service of the compose project (all profiles that are up)."""
    return sh("docker", "compose", "ps", "-q").splitlines()


def container_of(service: str) -> str:
    ids = sh("docker", "compose", "ps", "-q", service).splitlines()
    return ids[0] if ids else ""


def get_json(url: str, key: str | None) -> dict | None:
    request = urllib.request.Request(url, headers={"X-API-Key": key} if key else {})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read())
    except Exception:  # noqa: BLE001 -- engine state is best effort, never fails the run
        return None


def build_manifest(host: str, status_key: str | None, args: argparse.Namespace, pool_size: int) -> dict:
    container = container_of("backend")
    services = sh("docker", "compose", "ps", "--services").split()
    image_id = sh("docker", "inspect", "--format", "{{.Image}}", container) if container else ""
    repo_digests = json.loads(sh("docker", "inspect", "--format", "{{json .RepoDigests}}", image_id) or "null") if image_id else None
    images: dict = {"backend_image_id": image_id}
    if repo_digests:  # only a pulled image has a digest; a locally built one has none
        images["backend_repo_digests"] = repo_digests
    return {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "is_measurement": not args.smoke,
        "commit": sh("git", "rev-parse", "HEAD"),
        "dirty": bool(sh("git", "status", "--porcelain")),
        "images": images,
        "host": {
            "nproc": int(sh("nproc") or 0),
            "lscpu": sh("lscpu"),
            "free_m": sh("free", "-m"),
            "virtualization": sh("systemd-detect-virt") or "unknown",
        },
        "engine_state": get_json(f"{host}/api/v1/observability/live/status", status_key),
        "engine_state_key": "dedicated status key, not in the pool" if status_key else "none (no status key file)",
        "key_pool_size": pool_size,
        "pool_ceiling_rps": summary.pool_ceiling_rps(pool_size),
        "observability_profile_on": "prometheus" in services,
        "compose_services_running": services,
        "fleet": {"uptime": sh("uptime"), "claude_processes": int(sh("pgrep", "-fc", "claude") or 0)},
        "settings": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items() if k not in {"keys_file", "status_key_file"}},
    }


def _to_mb(text: str) -> float:
    match = re.match(r"\s*([\d.]+)\s*([KMG]i?B)", text)
    if not match:
        return 0.0
    return float(match.group(1)) * {"KB": 1 / 1024, "KiB": 1 / 1024, "MB": 1, "MiB": 1, "GB": 1024, "GiB": 1024}[match.group(2)]


class UseSampler(threading.Thread):
    """Samples every project container (docker stats), the host (vmstat) and a process's CPU until finished."""

    def __init__(self, containers: list[str], pid: int | None, interval: float) -> None:
        super().__init__(daemon=True)
        self.containers, self.pid, self.interval = containers, pid, interval
        self.stop_event = threading.Event()
        self.rows: list[dict] = []
        self._vmstat = subprocess.Popen(["vmstat", "1"], stdout=subprocess.PIPE, text=True)

    def run(self) -> None:
        while not self.stop_event.wait(self.interval):
            row: dict = {"t": time.time(), "containers": {}}
            if self.containers:
                for line in sh("docker", "stats", "--no-stream", "--format", "{{json .}}", *self.containers, timeout=30).splitlines():
                    try:
                        stats = json.loads(line)
                        row["containers"][stats["Name"]] = {
                            "cpu_pct": float(stats["CPUPerc"].rstrip("%")), "mem_mb": _to_mb(stats["MemUsage"].split("/")[0]),
                            "net_io": stats["NetIO"], "block_io": stats["BlockIO"]}
                    except (ValueError, KeyError):
                        continue
            if self.pid:
                row["locust_cpu_pct"] = float(sh("ps", "-o", "%cpu=", "-p", str(self.pid)) or 0)
            self.rows.append(row)

    def finish(self) -> dict:
        self.stop_event.set()
        self._vmstat.terminate()
        vm_rows = []
        for line in (self._vmstat.stdout.read() or "").splitlines():
            parts = line.split()
            if len(parts) >= 17 and parts[0].isdigit():
                vm_rows.append({"run_queue": int(parts[0]), "swap_kb_s": int(parts[6]) + int(parts[7]),
                                "disk_kb_s": int(parts[8]) + int(parts[9]), "host_cpu_pct": int(parts[12]) + int(parts[13])})
        return {"docker": self.rows, "vmstat": vm_rows}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def digest_use(samples: dict, backend_name: str) -> dict:
    """Peaks and means of one sampled window: backend, every container, host, and Locust's own CPU."""
    docker, vm = samples["docker"], samples["vmstat"]
    per_container: dict[str, dict[str, float]] = {}
    for row in docker:
        for name, c in row["containers"].items():
            peak = per_container.setdefault(name, {"cpu_pct_peak": 0.0, "mem_mb_peak": 0.0})
            peak["cpu_pct_peak"] = max(peak["cpu_pct_peak"], c["cpu_pct"])
            peak["mem_mb_peak"] = max(peak["mem_mb_peak"], c["mem_mb"])
    backend = per_container.get(backend_name, {})
    return {
        "backend_cpu_pct": backend.get("cpu_pct_peak", 0.0), "backend_mem_mb": backend.get("mem_mb_peak", 0.0),
        "locust_cpu_pct": max((r.get("locust_cpu_pct", 0.0) for r in docker), default=0.0),
        "host_cpu_pct": max((r["host_cpu_pct"] for r in vm), default=0.0), "run_queue": max((r["run_queue"] for r in vm), default=0.0),
        "swap_kb_s_mean": _mean([r["swap_kb_s"] for r in vm]), "disk_kb_s_mean": _mean([r["disk_kb_s"] for r in vm]),
        "containers": per_container,
    }


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
    ap.add_argument("--baseline-seconds", type=int, default=30, help="idle window before step 1 for the host swap/disk baseline")
    ap.add_argument("--sample-interval", type=float, default=2.0)
    ap.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_FILE)
    ap.add_argument("--status-key-file", type=Path, default=DEFAULT_STATUS_KEY_FILE)
    ap.add_argument("--single-key", action="store_true", help="all requests use key 0 (shows the per-key limit)")
    ap.add_argument("--mem-limit-mb", type=float, default=1024.0, help="backend mem_limit in compose.yaml")
    ap.add_argument("--label", default="run")
    ap.add_argument("--smoke", action="store_true", help="label the numbers as a smoke run, not a measurement")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    keys = load_keys(args.keys_file)
    status_key = (load_keys(args.status_key_file) or [None])[0] if args.status_key_file.exists() else None
    steps = [int(u) for u in args.users.split(",")]
    if not keys:
        print(f"no keys in {args.keys_file}; run tools/loadtest/keys.py", file=sys.stderr)
        return 2
    ceiling = summary.pool_ceiling_rps(1 if args.single_key else len(keys))
    print(f"key pool: {len(keys)} keys{' (single-key mode: 1 key)' if args.single_key else ''}; ceiling {ceiling:.0f} req/s "
          f"before per-key 429s (3/s per key); steps above {ceiling * summary.CEILING_WARN_FRACTION:.0f} req/s are flagged", file=sys.stderr)
    out = args.out / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True)
    env = {**os.environ, "LOADTEST_KEYS_FILE": str(args.keys_file), "PYTHONPATH": str(REPO)}
    if args.single_key:
        env["LOADTEST_SINGLE_KEY"] = "1"
    manifest = build_manifest(args.host, status_key, args, 1 if args.single_key else len(keys))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    containers = project_containers()
    backend_name = sh("docker", "inspect", "--format", "{{.Name}}", container_of("backend")).lstrip("/")
    nproc = manifest["host"]["nproc"] or 1

    # Idle baseline for host-wide swap and disk (other sessions move these), taken before any load.
    baseline_sampler = UseSampler(containers, None, args.sample_interval)
    baseline_sampler.start()
    time.sleep(args.baseline_seconds)
    baseline = digest_use(baseline_sampler.finish(), backend_name)
    (out / "baseline_use.json").write_text(json.dumps(baseline))

    per_step: dict[int, dict] = {}
    for users in steps:
        repeats, uses, rates_all = [], [], []
        for repeat in range(args.repeats):
            if args.warmup:
                run_locust(users, args.warmup, None, args.host, env).wait()
            prefix = out / f"step{users}_r{repeat}"
            proc = run_locust(users, args.duration, prefix, args.host, env)
            sampler = UseSampler(containers, proc.pid, args.sample_interval)
            sampler.start()
            proc.wait()
            samples = sampler.finish()
            (out / f"step{users}_r{repeat}_use.json").write_text(json.dumps(samples))
            stats = summary.parse_stats_csv(Path(f"{prefix}_stats.csv"))
            failures = summary.parse_failures_csv(Path(f"{prefix}_failures.csv"))
            repeats.append(stats)
            uses.append(digest_use(samples, backend_name))
            rates_all.append(summary.error_rates(stats.requests, failures))
        agg = summary.aggregate_repeats(repeats)
        containers_peak: dict[str, dict[str, float]] = {}
        for u in uses:
            for name, c in u["containers"].items():
                peak = containers_peak.setdefault(name, {"cpu_pct_peak": 0.0, "mem_mb_peak": 0.0})
                peak["cpu_pct_peak"] = max(peak["cpu_pct_peak"], c["cpu_pct_peak"])
                peak["mem_mb_peak"] = max(peak["mem_mb_peak"], c["mem_mb_peak"])
        peak_use = {k: max(u[k] for u in uses) for k in ("backend_cpu_pct", "backend_mem_mb", "locust_cpu_pct", "host_cpu_pct", "run_queue")}
        swap_delta, _ = summary.above_baseline(_mean([u["swap_kb_s_mean"] for u in uses]), baseline["swap_kb_s_mean"])
        disk_delta, _ = summary.above_baseline(_mean([u["disk_kb_s_mean"] for u in uses]), baseline["disk_kb_s_mean"])
        rates = {k: max(r[k] for r in rates_all) for k in rates_all[0]}
        per_step[users] = {
            "spread": agg, "peak_use": peak_use, "containers_peak": containers_peak, "error_rates": rates,
            "swap_delta_kb_s": swap_delta, "disk_delta_kb_s": disk_delta,
            "ceiling_warning": summary.ceiling_warning(agg["rps"]["median"], 1 if args.single_key else len(keys)),
            "flags": summary.step_flags(backend_mem_mb=peak_use["backend_mem_mb"], mem_limit_mb=args.mem_limit_mb, rates=rates,
                                        swap_delta_kb_s=swap_delta, disk_delta_kb_s=disk_delta),
        }

    sat = summary.find_saturation(
        [summary.StepView(u, d["spread"]["rps"]["median"], d["spread"]["p95"]["median"], d["peak_use"]["backend_cpu_pct"],
                          d["peak_use"]["host_cpu_pct"], d["peak_use"]["run_queue"]) for u, d in per_step.items()], nproc=nproc)
    result = {"is_measurement": not args.smoke, "pool_ceiling_rps": ceiling, "baseline": {k: v for k, v in baseline.items() if k != "containers"},
              "steps": per_step,
              "saturation": {"users": sat.users, "resource": sat.resource, "branch": sat.branch} if sat else None}
    (out / "summary.json").write_text(json.dumps(result, indent=2))
    print(("SMOKE RUN -- not a measurement\n" if args.smoke else "") + f"pool ceiling {ceiling:.0f} req/s")
    print(f"{'users':>5} {'req/s med (min-max)':>24} {'p50':>6} {'p95':>6} {'p99':>6} {'429':>6} {'5xx':>6}  flags")
    for users, d in per_step.items():
        s = d["spread"]
        flags = list(d["flags"]) + (["near_pool_ceiling"] if d["ceiling_warning"] else [])
        print(f"{users:>5} {s['rps']['median']:>10.1f} ({s['rps']['min']:.1f}-{s['rps']['max']:.1f}) {s['p50']['median']:>6.0f} "
              f"{s['p95']['median']:>6.0f} {s['p99']['median']:>6.0f} {d['error_rates']['admission_429']:>6.1%} "
              f"{d['error_rates']['server_5xx']:>6.1%}  {','.join(flags)}")
    print("saturation (throughput gain < 10 % while p95 rises >= 50 %):",
          f"{sat.resource} at {sat.users} users ({sat.branch})" if sat else "no knee within the tested steps")
    names = sorted({n for d in per_step.values() for n in d["containers_peak"]})
    print("peak per container (CPU % of one core / memory MiB), max over steps:")
    for name in names:
        cpu = max(d["containers_peak"].get(name, {}).get("cpu_pct_peak", 0.0) for d in per_step.values())
        mem = max(d["containers_peak"].get(name, {}).get("mem_mb_peak", 0.0) for d in per_step.values())
        print(f"  {name:<40} {cpu:>7.1f} {mem:>8.0f}")
    print(f"Locust shares the {nproc} vCPUs with the backend; its own peak CPU is in summary.json. Output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
