"""Pure summary maths for the load-test runner: Locust CSV parsing, spread across repeats, saturation rule.

No I/O besides reading the CSV paths it is given, so it is testable from fixed fixtures.
The saturation rule is documented in tools/loadtest/README.md; keep the two in step.
"""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

# Saturation (README "Saturation rule"). Throughput that stops growing while p95 climbs marks the knee; the resource is then attributed.
KNEE_MAX_RPS_GAIN = 0.10      # throughput gain over the previous step below this ...
KNEE_MIN_P95_RISE = 0.50      # ... while p95 rises by at least this
HOST_CPU_PCT = 90.0           # vmstat us+sy
BACKEND_NEAR_MAX = 0.90       # backend CPU within 10 % of its maximum over all steps
MEMORY_FRACTION = 0.90        # backend memory / its mem_limit (flag, not a verdict)
ERROR_RATE = 0.01             # 5xx or 429 share of requests (flag)
HOST_BASELINE_LIMIT_KB_S = 1024.0   # swap or disk above the idle baseline by more than 1 MB/s (flag)
PER_KEY_REFILL_PER_S = 3.0    # src/api/admission_control.py _BUCKET_REFILL_PER_SECOND
CEILING_WARN_FRACTION = 0.5


def classify_failure(status_code: int) -> str | None:
    """Failure message for a response status, None when the response is a success."""
    if status_code == 429:
        return "admission_429"
    if status_code >= 500:
        return f"server_5xx_{status_code}"
    if status_code >= 400:
        return f"http_{status_code}"
    return None


@dataclass(frozen=True)
class StepStats:
    requests: int
    failures: int
    rps: float
    p50: float
    p95: float
    p99: float


def parse_stats_csv(path: Path) -> StepStats:
    """The ``Aggregated`` row of a Locust ``<prefix>_stats.csv``."""
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["Name"] == "Aggregated":
                return StepStats(
                    requests=int(row["Request Count"]),
                    failures=int(row["Failure Count"]),
                    rps=float(row["Requests/s"]),
                    p50=float(row["50%"]),
                    p95=float(row["95%"]),
                    p99=float(row["99%"]),
                )
    raise ValueError(f"no Aggregated row in {path}")


def parse_failures_csv(path: Path) -> dict[str, int]:
    """Failure counts by category from ``<prefix>_failures.csv`` (messages set by locustfile.classify_failure).

    Categories: ``admission_429``, ``server_5xx`` (any 5xx), ``http_other`` (other 4xx), ``transport``
    (Locust's own connection errors, i.e. anything not produced by classify_failure).
    """
    counts = {"admission_429": 0, "server_5xx": 0, "http_other": 0, "transport": 0}
    if not path.exists():
        return counts
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            error, occurrences = row["Error"], int(row["Occurrences"])
            # Locust writes a catch_response failure as "CatchResponseError('<message>')", so match the message anywhere.
            if "admission_429" in error:
                counts["admission_429"] += occurrences
            elif "server_5xx_" in error:
                counts["server_5xx"] += occurrences
            elif "'http_" in error:
                counts["http_other"] += occurrences
            else:
                counts["transport"] += occurrences
    return counts


def spread(values: Sequence[float]) -> dict[str, float]:
    """Median and min-max across repeats."""
    if not values:
        raise ValueError("spread() needs at least one value")
    return {"median": statistics.median(values), "min": min(values), "max": max(values)}


def aggregate_repeats(repeats: Sequence[StepStats]) -> dict[str, dict[str, float]]:
    return {
        "rps": spread([r.rps for r in repeats]),
        "p50": spread([r.p50 for r in repeats]),
        "p95": spread([r.p95 for r in repeats]),
        "p99": spread([r.p99 for r in repeats]),
    }


def error_rates(requests: int, failures: Mapping[str, int]) -> dict[str, float]:
    if requests <= 0:
        return {key: 0.0 for key in failures}
    return {key: count / requests for key, count in failures.items()}


def pool_ceiling_rps(pool_size: int) -> float:
    """Requests/s the key pool carries before per-key 429s start (keys rotate round-robin per request)."""
    return PER_KEY_REFILL_PER_S * pool_size


def ceiling_warning(rps: float, pool_size: int) -> bool:
    """True when a step's throughput is above 50 % of the pool ceiling (the step is too close to measuring the key limit)."""
    return rps > CEILING_WARN_FRACTION * pool_ceiling_rps(pool_size)


def above_baseline(step_mean_kb_s: float, baseline_mean_kb_s: float) -> tuple[float, bool]:
    """(step minus idle baseline, flagged) for host swap or disk, in KB/s; flagged when more than 1 MB/s above baseline."""
    delta = step_mean_kb_s - baseline_mean_kb_s
    return delta, delta > HOST_BASELINE_LIMIT_KB_S


@dataclass(frozen=True)
class StepView:
    """What the saturation verdict needs from one user step (medians/means over repeats)."""

    users: int
    rps: float
    p95: float
    backend_cpu_pct: float
    host_cpu_pct: float
    run_queue: float


@dataclass(frozen=True)
class Saturation:
    users: int          # the step at which throughput stopped growing
    resource: str       # host_cpu | backend_process | unattributed
    branch: str         # which rule branch fired, in words


def find_saturation(steps: Sequence[StepView], *, nproc: int) -> Saturation | None:
    """The first step where throughput gains < 10 % over the previous step while p95 rises >= 50 %, then the resource.

    Attribution at that step: host CPU >= 90 % or run queue > nproc -> host_cpu; else backend CPU within 10 % of its
    maximum over all steps -> backend_process (GIL/engine contention); else unattributed. None when there is no knee.
    """
    ordered = sorted(steps, key=lambda s: s.users)
    backend_max = max((s.backend_cpu_pct for s in ordered), default=0.0)
    for previous, step in zip(ordered, ordered[1:]):
        gain = (step.rps - previous.rps) / previous.rps if previous.rps > 0 else 0.0
        rise = (step.p95 - previous.p95) / previous.p95 if previous.p95 > 0 else 0.0
        if gain < KNEE_MAX_RPS_GAIN and rise >= KNEE_MIN_P95_RISE:
            if step.host_cpu_pct >= HOST_CPU_PCT:
                return Saturation(step.users, "host_cpu", f"host CPU {step.host_cpu_pct:.0f} % >= {HOST_CPU_PCT:.0f} %")
            if step.run_queue > nproc:
                return Saturation(step.users, "host_cpu", f"run queue {step.run_queue:.0f} > {nproc} vCPUs")
            if backend_max > 0 and step.backend_cpu_pct >= BACKEND_NEAR_MAX * backend_max:
                return Saturation(step.users, "backend_process",
                                  f"backend CPU {step.backend_cpu_pct:.0f} % within 10 % of its maximum {backend_max:.0f} %")
            return Saturation(step.users, "unattributed", "host CPU, run queue and backend CPU all below their branch limits")
    return None


def step_flags(*, backend_mem_mb: float, mem_limit_mb: float, rates: Mapping[str, float],
               swap_delta_kb_s: float, disk_delta_kb_s: float) -> list[str]:
    """Context flags for one step (not saturation verdicts)."""
    flags = []
    if backend_mem_mb >= MEMORY_FRACTION * mem_limit_mb:
        flags.append("memory_near_limit")
    if rates.get("admission_429", 0.0) >= ERROR_RATE:
        flags.append("admission_429")
    if rates.get("server_5xx", 0.0) >= ERROR_RATE:
        flags.append("server_5xx")
    if swap_delta_kb_s > HOST_BASELINE_LIMIT_KB_S:
        flags.append("host_swap")
    if disk_delta_kb_s > HOST_BASELINE_LIMIT_KB_S:
        flags.append("host_disk")
    return flags


# --- engine state per step (the engine shares the backend process and its GIL) ---------------------------------------------

ENGINE_FIELDS = ("status", "current_tick", "governor_mode", "health_state", "observability_mode", "elapsed_seconds")


def engine_reading(payload: Mapping | None, taken_at: float) -> dict | None:
    """The fields of one /api/v1/observability/live/status reading, plus the wall time it was taken. None if there is no payload."""
    if not isinstance(payload, Mapping):
        return None
    reading = {name: payload.get(name) for name in ENGINE_FIELDS}
    reading["taken_at"] = taken_at
    return reading


def ticks_per_second(start: Mapping | None, end: Mapping | None) -> float | None:
    """Engine ticks per second between two readings. Uses the engine's own elapsed_seconds when both readings carry it, else the wall
    time of the readings. None when a reading or tick is missing, the tick went backwards (engine restarted) or no time passed."""
    if not start or not end:
        return None
    first, last = start.get("current_tick"), end.get("current_tick")
    if not isinstance(first, (int, float)) or not isinstance(last, (int, float)) or last < first:
        return None
    seconds = None
    if isinstance(start.get("elapsed_seconds"), (int, float)) and isinstance(end.get("elapsed_seconds"), (int, float)):
        seconds = end["elapsed_seconds"] - start["elapsed_seconds"]
    if seconds is None or seconds <= 0:
        seconds = end["taken_at"] - start["taken_at"]
    return (last - first) / seconds if seconds > 0 else None


def aggregate_engine(windows: Sequence[tuple[Mapping | None, Mapping | None]]) -> dict:
    """One step's engine summary from its (start, end) readings, one pair per repeat: ticks/s per repeat and the modes seen."""
    rates = [ticks_per_second(a, b) for a, b in windows]
    readings = [r for pair in windows for r in pair if r]
    return {
        "ticks_per_s": [None if r is None else round(r, 2) for r in rates],
        "ticks_per_s_median": round(statistics.median(valid), 2) if (valid := [r for r in rates if r is not None]) else None,
        "start": windows[0][0] if windows else None,
        "end": windows[-1][1] if windows else None,
        "governor_modes": sorted({r["governor_mode"] for r in readings if r.get("governor_mode")}),
        "health_states": sorted({r["health_state"] for r in readings if r.get("health_state")}),
        "observability_modes": sorted({r["observability_mode"] for r in readings if r.get("observability_mode")}),
    }


def format_engine_row(users: int, engine: Mapping) -> str:
    """One row of the per-step engine table: users, ticks/s median, then governor / health / observability mode (n/a when unread)."""
    tps = engine.get("ticks_per_s_median")
    modes = (", ".join(engine.get(key) or ["n/a"]) for key in ("governor_modes", "health_states", "observability_modes"))
    return f"{users:>5} {'n/a' if tps is None else f'{tps:.1f}':>8} ticks/s  " + " / ".join(modes)
