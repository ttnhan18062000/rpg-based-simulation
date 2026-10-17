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

# Saturation thresholds (README "Saturation rule"). Order is the tie-break within one step.
BACKEND_CPU_PCT = 90.0       # docker stats CPU %; 100 % is one core, the backend is one process
HOST_CPU_PCT = 90.0          # vmstat us+sy
MEMORY_FRACTION = 0.90       # backend memory / its mem_limit
ERROR_RATE = 0.01            # 5xx or 429 share of requests
RESOURCE_ORDER = ("backend_cpu", "host_cpu", "run_queue", "memory", "swap", "admission_429", "server_5xx")


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


def saturated_resources(
    use: Mapping[str, float], *, nproc: int, mem_limit_mb: float, rates: Mapping[str, float]
) -> list[tuple[str, float]]:
    """Resources over their threshold in one step, in RESOURCE_ORDER.

    ``use`` keys (peak over the step): backend_cpu_pct, host_cpu_pct, run_queue, backend_mem_mb, swap_kb_s.
    """
    checks = {
        "backend_cpu": (use.get("backend_cpu_pct", 0.0), lambda v: v >= BACKEND_CPU_PCT),
        "host_cpu": (use.get("host_cpu_pct", 0.0), lambda v: v >= HOST_CPU_PCT),
        "run_queue": (use.get("run_queue", 0.0), lambda v: v > nproc),
        "memory": (use.get("backend_mem_mb", 0.0), lambda v: v >= MEMORY_FRACTION * mem_limit_mb),
        "swap": (use.get("swap_kb_s", 0.0), lambda v: v > 0),
        "admission_429": (rates.get("admission_429", 0.0), lambda v: v >= ERROR_RATE),
        "server_5xx": (rates.get("server_5xx", 0.0), lambda v: v >= ERROR_RATE),
    }
    return [(name, checks[name][0]) for name in RESOURCE_ORDER if checks[name][1](checks[name][0])]


def first_saturation(
    steps: Iterable[tuple[int, Mapping[str, float], Mapping[str, float]]], *, nproc: int, mem_limit_mb: float
) -> tuple[int, str, float] | None:
    """(users, resource, value) for the lowest user step with any saturated resource, else None.

    ``steps`` is (users, peak USE values, error rates); steps are checked in ascending user order and the
    first resource in RESOURCE_ORDER wins a tie within a step.
    """
    for users, use, rates in sorted(steps, key=lambda s: s[0]):
        hits = saturated_resources(use, nproc=nproc, mem_limit_mb=mem_limit_mb, rates=rates)
        if hits:
            return users, hits[0][0], hits[0][1]
    return None
