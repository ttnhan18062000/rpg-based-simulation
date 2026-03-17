"""Prometheus metrics definitions for the RPG engine."""

from prometheus_client import Counter, Gauge, Histogram, Info

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

SIM_CURRENT_TICK = Gauge(
    "sim_current_tick",
    "Current simulation tick number"
)

SIM_TICKS_PER_SECOND = Gauge(
    "sim_ticks_per_second",
    "Actual simulation throughput in ticks per second"
)

# --- Combat Metrics ---

SIM_COMBAT_EVENTS = Counter(
    "sim_combat_events_total",
    "Total combat events emitted"
)

SIM_SKILL_EVENTS = Counter(
    "sim_skill_events_total",
    "Total skill usage events emitted"
)

# --- Worker & Queue Metrics ---

SIM_WORKER_DISPATCH_DURATION = Histogram(
    "sim_worker_dispatch_seconds",
    "Time to dispatch and collect AI decisions from workers",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

SIM_WORKER_ENTITIES_DISPATCHED = Counter(
    "sim_worker_entities_dispatched_total",
    "Total entities dispatched to AI workers"
)

SIM_ACTION_QUEUE_DEPTH = Gauge(
    "sim_action_queue_depth",
    "Current number of pending actions in the queue"
)

# --- Infrastructure Metrics ---

SIM_REDIS_PUBLISH_DURATION = Histogram(
    "sim_redis_publish_seconds",
    "Time to publish state delta to Redis stream",
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.05]
)

SIM_KAFKA_PUBLISH_DURATION = Histogram(
    "sim_kafka_publish_seconds",
    "Time to publish snapshot/events to Kafka",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
)

# --- Process Resource Metrics ---

PROCESS_CPU_PERCENT = Gauge(
    "process_cpu_percent",
    "Backend Python process CPU usage percentage"
)

PROCESS_MEMORY_RSS = Gauge(
    "process_memory_rss_bytes",
    "Backend Python process resident set size in bytes"
)

PROCESS_MEMORY_VMS = Gauge(
    "process_memory_vms_bytes",
    "Backend Python process virtual memory size in bytes"
)

PROCESS_THREAD_COUNT = Gauge(
    "process_thread_count",
    "Number of threads in the backend process"
)
