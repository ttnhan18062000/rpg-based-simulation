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

SIM_WORLD_DIFFICULTY_MULT = Gauge(
    "sim_world_difficulty_mult",
    "Current global stat multiplier based on world age"
)

SIM_TOP_HERO_LEVEL = Gauge(
    "sim_top_hero_level",
    "Current highest hero level in the world"
)

SIM_TOP_HERO_GOLD = Gauge(
    "sim_top_hero_gold",
    "Current highest gold amount held by a single hero"
)

# --- Combat Metrics ---

SIM_COMBAT_EVENTS = Counter(
    "sim_combat_events_total",
    "Total combat events emitted",
    ["attacker_faction", "defender_faction"]
)

SIM_SKILL_EVENTS = Counter(
    "sim_skill_events_total",
    "Total skill usage events emitted",
    ["attacker_faction", "skill_name"]
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

SIM_WORKER_HEALTH = Gauge(
    "sim_worker_health",
    "Health status of AI workers (1=OK, 0=Busy/Error)",
    ["worker_id", "state"] # state: "idle", "busy", "error"
)

# --- Infrastructure Metrics ---

SIM_REDIS_LATENCY = Histogram(
    "sim_redis_latency_seconds",
    "Latency of Redis operations by type",
    ["op"], # e.g. "publish", "get_state", "set_snapshot"
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
)

SIM_REDIS_PUBLISH_DURATION = Histogram(
    "sim_redis_publish_seconds",
    "Time to publish state delta to Redis stream",
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.05]
)

SIM_KAFKA_PUBLISH_DURATION = Histogram(
    "sim_kafka_publish_seconds",
    "Time to publish snapshot/events to Kafka",
    ["type"],
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

# --- Simulation Depth Metrics ---

SIM_FACTION_POPULATION = Gauge(
    "sim_faction_population",
    "Current headcount per faction",
    ["faction"]
)

SIM_ENTITY_LEVEL_DISTRIBUTION = Gauge(
    "sim_entity_level_distribution",
    "Number of entities at each level bracket",
    ["kind", "level_bracket"] # e.g. "1-10", "11-20", etc.
)

SIM_HERO_CLASS_TOTAL = Gauge(
    "sim_hero_class_total",
    "Total heroes in each class and tier",
    ["hero_class", "tier"]
)

SIM_GOLD_CIRCULATION_TOTAL = Gauge(
    "sim_gold_circulation_total",
    "Total gold held by all entities in a faction",
    ["faction"]
)

SIM_BUILDING_DURABILITY_PERCENT = Gauge(
    "sim_building_durability_percent",
    "Health of town infrastructure (0-100)",
    ["building_id"]
)

SIM_QUEST_STATUS_TOTAL = Counter(
    "sim_quest_status_total",
    "Tracking GATHER/HUNT/EXPLORE success/failure rates",
    ["type", "status"] # e.g. "hunt", "completed"
)

SIM_ITEMS_CRAFTED_TOTAL = Counter(
    "sim_items_crafted_total",
    "Tracking blacksmith activity and gear quality",
    ["item_id", "tier"]
)

SIM_SHOP_TRANSACTIONS_TOTAL = Counter(
    "sim_shop_transactions_total",
    "Tracking general store buy/sell volume",
    ["type", "item_id"] # type: "buy" or "sell"
)

SIM_CALAMITY_ACTIVE = Gauge(
    "sim_calamity_active",
    "1 if a world boss is active, 0 otherwise",
    ["region_id"]
)

# --- Admin & Diagnostic Metrics ---

SIM_ERRORS_TOTAL = Counter(
    "sim_errors_total",
    "Caught exceptions in world loop, AI, or networking",
    ["exception_type", "component"]
)

SIM_INVALID_ACTIONS_TOTAL = Counter(
    "sim_invalid_actions_total",
    "Actions proposed by AI that failed validation",
    ["action_type", "reason"]
)

SIM_STATE_TRANSITION_FAILURES = Counter(
    "sim_state_transition_failures_total",
    "Failures in AI state logic transitions",
    ["from_state", "to_state"]
)

# --- Strategic Metrics [PHASE 6] ---

SIM_STRATEGIC_PROJECT_STATUS = Counter(
    "sim_strategic_project_status_total",
    "Tracking strategic project lifecycle transitions",
    ["kind", "status"] # kind: quest, exploration, etc. status: started, completed, abandoned
)

SIM_STRATEGIC_PRESSURE_CONCERNS = Gauge(
    "sim_strategic_pressure_concerns",
    "Tracking active strategic pressures (concerns) across the population",
    ["kind"] # kind: threat, opportunity, obligation
)

SIM_STRATEGIC_WORLD_OPPORTUNITIES = Gauge(
    "sim_strategic_world_opportunities",
    "Number of active shared world opportunities"
)

SIM_STRATEGIC_CONTRACT_BREACHES = Counter(
    "sim_strategic_contract_breaches_total",
    "Tracking social contract violations",
    ["contract_kind", "reason"]
)
