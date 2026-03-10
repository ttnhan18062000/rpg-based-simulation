"""Prometheus metrics definitions for the RPG engine."""

from prometheus_client import Counter, Gauge, Histogram

# --- HTTP Metrics ---

API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# --- Engine Metrics ---

SIM_TICK_DURATION = Histogram(
    "sim_tick_duration_seconds",
    "Time spent computing simulation ticks",
    ["phase"], # e.g. "scheduling", "resolve", "subsystems", "cleanup", "total"
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

ACTIVE_ENTITIES = Gauge(
    "sim_active_entities",
    "Number of alive entities currently in the world"
)

TOTAL_SPAWNS = Counter(
    "sim_total_spawns",
    "Total entities spawned since boot"
)

TOTAL_DEATHS = Counter(
    "sim_total_deaths",
    "Total entities died since boot"
)
