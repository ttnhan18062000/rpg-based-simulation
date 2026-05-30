from __future__ import annotations
import os
import threading
from enum import Enum
from typing import Optional


class ObservabilityMode(str, Enum):
    """
    Observability operational modes for the RPG Simulation Engine.
    """
    OFF = "OFF"
    LIGHT = "LIGHT"
    NORMAL = "NORMAL"
    FULL = "FULL"
    RESEARCH = "RESEARCH"
    DEBUG = "DEBUG"
    CERTIFICATION = "CERTIFICATION"
    LONG_RUN = "LONG_RUN"


class ObservabilityConfig:
    """
    Thread-safe global manager for resolving the active simulation observability mode.
    Precedence: Direct override -> Environment variable -> Default (LIGHT)
    """
    _override_mode: Optional[ObservabilityMode] = None
    _override_flags: dict[str, bool] = {}
    _lock = threading.Lock()

    _DEFAULT_FLAG_MAPPINGS = {
        ObservabilityMode.OFF: {
            "OBS_RUNTIME_PROFILING": False,
            "OBS_RAW_EVENTS": False,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": False,
            "OBS_ENTITY_TIMELINE": False,
            "OBS_BEHAVIOR_NORMALIZATION": False,
            "OBS_BEHAVIOR_TIMELINE": False,
            "OBS_BEHAVIOR_EPISODES": False,
            "OBS_BEHAVIOR_METRICS": False,
            "OBS_BEHAVIOR_PATTERNS": False,
            "OBS_BEHAVIOR_SCORECARDS": False,
            "OBS_COHORT_ANALYSIS": False,
            "OBS_RUN_COMPARISON": False,
            "OBS_INSIGHT_GENERATION": False,
            "OBS_WAREHOUSE_INGEST": False,
            "OBS_DASHBOARD_EXPORT": False,
        },
        ObservabilityMode.LIGHT: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": False,
            "OBS_BEHAVIOR_TIMELINE": False,
            "OBS_BEHAVIOR_EPISODES": False,
            "OBS_BEHAVIOR_METRICS": False,
            "OBS_BEHAVIOR_PATTERNS": False,
            "OBS_BEHAVIOR_SCORECARDS": False,
            "OBS_COHORT_ANALYSIS": False,
            "OBS_RUN_COMPARISON": False,
            "OBS_INSIGHT_GENERATION": False,
            "OBS_WAREHOUSE_INGEST": False,
            "OBS_DASHBOARD_EXPORT": False,
        },
        ObservabilityMode.NORMAL: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": True,
            "OBS_BEHAVIOR_TIMELINE": True,
            "OBS_BEHAVIOR_EPISODES": False,
            "OBS_BEHAVIOR_METRICS": True,
            "OBS_BEHAVIOR_PATTERNS": False,
            "OBS_BEHAVIOR_SCORECARDS": False,
            "OBS_COHORT_ANALYSIS": False,
            "OBS_RUN_COMPARISON": False,
            "OBS_INSIGHT_GENERATION": False,
            "OBS_WAREHOUSE_INGEST": True,
            "OBS_DASHBOARD_EXPORT": False,
        },
        ObservabilityMode.FULL: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": True,
            "OBS_BEHAVIOR_TIMELINE": True,
            "OBS_BEHAVIOR_EPISODES": True,
            "OBS_BEHAVIOR_METRICS": True,
            "OBS_BEHAVIOR_PATTERNS": True,
            "OBS_BEHAVIOR_SCORECARDS": True,
            "OBS_COHORT_ANALYSIS": True,
            "OBS_RUN_COMPARISON": False,
            "OBS_INSIGHT_GENERATION": True,
            "OBS_WAREHOUSE_INGEST": True,
            "OBS_DASHBOARD_EXPORT": False,
        },
        ObservabilityMode.RESEARCH: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": True,
            "OBS_BEHAVIOR_TIMELINE": True,
            "OBS_BEHAVIOR_EPISODES": True,
            "OBS_BEHAVIOR_METRICS": True,
            "OBS_BEHAVIOR_PATTERNS": True,
            "OBS_BEHAVIOR_SCORECARDS": True,
            "OBS_COHORT_ANALYSIS": True,
            "OBS_RUN_COMPARISON": True,
            "OBS_INSIGHT_GENERATION": True,
            "OBS_WAREHOUSE_INGEST": True,
            "OBS_DASHBOARD_EXPORT": False,
        },
        ObservabilityMode.DEBUG: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": True,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": True,
            "OBS_BEHAVIOR_TIMELINE": True,
            "OBS_BEHAVIOR_EPISODES": True,
            "OBS_BEHAVIOR_METRICS": True,
            "OBS_BEHAVIOR_PATTERNS": True,
            "OBS_BEHAVIOR_SCORECARDS": True,
            "OBS_COHORT_ANALYSIS": True,
            "OBS_RUN_COMPARISON": True,
            "OBS_INSIGHT_GENERATION": True,
            "OBS_WAREHOUSE_INGEST": True,
            "OBS_DASHBOARD_EXPORT": True,
        },
        ObservabilityMode.CERTIFICATION: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": True,
            "OBS_BEHAVIOR_TIMELINE": True,
            "OBS_BEHAVIOR_EPISODES": False,
            "OBS_BEHAVIOR_METRICS": True,
            "OBS_BEHAVIOR_PATTERNS": False,
            "OBS_BEHAVIOR_SCORECARDS": False,
            "OBS_COHORT_ANALYSIS": False,
            "OBS_RUN_COMPARISON": False,
            "OBS_INSIGHT_GENERATION": False,
            "OBS_WAREHOUSE_INGEST": True,
            "OBS_DASHBOARD_EXPORT": False,
        },
        ObservabilityMode.LONG_RUN: {
            "OBS_RUNTIME_PROFILING": True,
            "OBS_RAW_EVENTS": True,
            "OBS_LIVE_STREAM": False,
            "OBS_EVENT_RECORDER": True,
            "OBS_ENTITY_TIMELINE": True,
            "OBS_BEHAVIOR_NORMALIZATION": True,
            "OBS_BEHAVIOR_TIMELINE": True,
            "OBS_BEHAVIOR_EPISODES": False,
            "OBS_BEHAVIOR_METRICS": True,
            "OBS_BEHAVIOR_PATTERNS": False,
            "OBS_BEHAVIOR_SCORECARDS": False,
            "OBS_COHORT_ANALYSIS": False,
            "OBS_RUN_COMPARISON": False,
            "OBS_INSIGHT_GENERATION": False,
            "OBS_WAREHOUSE_INGEST": True,
            "OBS_DASHBOARD_EXPORT": False,
        },
    }

    @classmethod
    def set_override_mode(cls, mode: Optional[ObservabilityMode]) -> None:
        """Sets a programmatic override mode, e.g. for specific tests."""
        with cls._lock:
            cls._override_mode = mode

    @classmethod
    def set_flag_override(cls, flag_name: str, value: Optional[bool]) -> None:
        """Programmatically override a specific observability flag thread-safely."""
        with cls._lock:
            if value is None:
                cls._override_flags.pop(flag_name, None)
            else:
                cls._override_flags[flag_name] = value

    @classmethod
    def clear_all_overrides(cls) -> None:
        """Clear all mode and flag programmatic overrides thread-safely."""
        with cls._lock:
            cls._override_mode = None
            cls._override_flags.clear()

    @classmethod
    def get_flag(cls, flag_name: str) -> bool:
        """Resolves an individual feature flag's active boolean status thread-safely."""
        # 1. Programmatic direct flag override
        with cls._lock:
            if flag_name in cls._override_flags:
                return cls._override_flags[flag_name]

        # 2. Env variable check for the exact flag or common prefixes
        for env_key in (flag_name, f"SIM_{flag_name}", f"RPG_{flag_name}"):
            env_val = os.environ.get(env_key)
            if env_val is not None:
                return env_val.strip().lower() in ("true", "1", "yes", "on")

        # 3. Active Mode mapping resolution
        mode = cls.get_mode()
        mapping = cls._DEFAULT_FLAG_MAPPINGS.get(mode, cls._DEFAULT_FLAG_MAPPINGS[ObservabilityMode.LIGHT])
        return mapping.get(flag_name, False)

    @classmethod
    def is_runtime_profiling_enabled(cls) -> bool:
        return cls.get_flag("OBS_RUNTIME_PROFILING")

    @classmethod
    def is_raw_events_enabled(cls) -> bool:
        return cls.get_flag("OBS_RAW_EVENTS")

    @classmethod
    def is_live_stream_enabled(cls) -> bool:
        return cls.get_flag("OBS_LIVE_STREAM")

    @classmethod
    def is_event_recorder_enabled(cls) -> bool:
        return cls.get_flag("OBS_EVENT_RECORDER")

    @classmethod
    def is_entity_timeline_enabled(cls) -> bool:
        return cls.get_flag("OBS_ENTITY_TIMELINE")

    @classmethod
    def is_behavior_normalization_enabled(cls) -> bool:
        return cls.get_flag("OBS_BEHAVIOR_NORMALIZATION")

    @classmethod
    def is_behavior_timeline_enabled(cls) -> bool:
        return cls.get_flag("OBS_BEHAVIOR_TIMELINE")

    @classmethod
    def is_behavior_episodes_enabled(cls) -> bool:
        return cls.get_flag("OBS_BEHAVIOR_EPISODES")

    @classmethod
    def is_behavior_metrics_enabled(cls) -> bool:
        return cls.get_flag("OBS_BEHAVIOR_METRICS")

    @classmethod
    def is_behavior_patterns_enabled(cls) -> bool:
        return cls.get_flag("OBS_BEHAVIOR_PATTERNS")

    @classmethod
    def is_behavior_scorecards_enabled(cls) -> bool:
        return cls.get_flag("OBS_BEHAVIOR_SCORECARDS")

    @classmethod
    def is_cohort_analysis_enabled(cls) -> bool:
        return cls.get_flag("OBS_COHORT_ANALYSIS")

    @classmethod
    def is_run_comparison_enabled(cls) -> bool:
        return cls.get_flag("OBS_RUN_COMPARISON")

    @classmethod
    def is_insight_generation_enabled(cls) -> bool:
        return cls.get_flag("OBS_INSIGHT_GENERATION")

    @classmethod
    def is_warehouse_ingest_enabled(cls) -> bool:
        return cls.get_flag("OBS_WAREHOUSE_INGEST")

    @classmethod
    def is_dashboard_export_enabled(cls) -> bool:
        return cls.get_flag("OBS_DASHBOARD_EXPORT")

    @classmethod
    def get_mode(cls) -> ObservabilityMode:
        """Resolves the current active observability mode with precedence."""
        with cls._lock:
            if cls._override_mode is not None:
                return cls._override_mode

        # Precedence: Env variable -> Default
        env_val = os.environ.get("SIM_OBS_MODE") or os.environ.get("RPG_OBS_MODE")
        if env_val:
            try:
                return ObservabilityMode(env_val.strip().upper())
            except ValueError:
                pass

        return ObservabilityMode.LIGHT

    @classmethod
    def get_deployment_profile(cls) -> str:
        """Resolves the active deployment profile (local-dev, production, scale-test)."""
        return os.environ.get("SIM_DEPLOYMENT_PROFILE") or os.environ.get("RPG_DEPLOYMENT_PROFILE") or "local-dev"

    @classmethod
    def get_stream_backend(cls) -> str:
        """Resolves the event stream backend from env or active deployment profile default."""
        val = os.environ.get("SIM_STREAM_BACKEND") or os.environ.get("RPG_STREAM_BACKEND")
        if val:
            return val
        profile = cls.get_deployment_profile().lower().strip()
        if profile == "production":
            return "redis"
        elif profile == "scale-test":
            return "null"
        return "in_process"

    @classmethod
    def get_redis_url(cls) -> str:
        """Resolves the Redis connection string from env, defaulting to default local."""
        return os.environ.get("SIM_REDIS_URL") or os.environ.get("RPG_REDIS_URL") or "redis://localhost:6379/0"

    @classmethod
    def get_stream_name(cls) -> str:
        """Resolves the target stream key name from env, defaulting to 'simulation:events'."""
        return os.environ.get("SIM_STREAM_NAME") or os.environ.get("RPG_STREAM_NAME") or "simulation:events"

    @classmethod
    def get_max_queue_size(cls) -> int:
        """Resolves maximum event cap size from env or active deployment profile default."""
        val = os.environ.get("SIM_MAX_QUEUE_SIZE") or os.environ.get("RPG_MAX_QUEUE_SIZE")
        if val:
            try:
                return int(val)
            except ValueError:
                pass
        profile = cls.get_deployment_profile().lower().strip()
        if profile == "production":
            return 5000
        elif profile == "scale-test":
            return 0
        return 1000

    @classmethod
    def get_warehouse_backend(cls) -> str:
        """Resolves the event warehouse backend from env or active deployment profile default."""
        val = os.environ.get("SIM_WAREHOUSE_BACKEND") or os.environ.get("RPG_WAREHOUSE_BACKEND")
        if val:
            return val
        profile = cls.get_deployment_profile().lower().strip()
        if profile == "scale-test":
            return "null"
        return "local"

    @classmethod
    def get_clickhouse_host(cls) -> str:
        """Resolves ClickHouse server host address."""
        return os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_HOST") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_HOST") or "localhost"

    @classmethod
    def get_clickhouse_port(cls) -> int:
        """Resolves ClickHouse server HTTP port."""
        val = os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_PORT") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_PORT")
        if val:
            try:
                return int(val)
            except ValueError:
                pass
        return 8123

    @classmethod
    def get_clickhouse_database(cls) -> str:
        """Resolves ClickHouse target database name."""
        return os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_DATABASE") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_DATABASE") or "default"

    @classmethod
    def get_clickhouse_username(cls) -> str:
        """Resolves ClickHouse database login username."""
        return os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_USERNAME") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_USERNAME") or "default"

    @classmethod
    def get_clickhouse_password(cls) -> str:
        """Resolves ClickHouse database login password."""
        return os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_PASSWORD") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_PASSWORD") or ""

    @classmethod
    def get_clickhouse_secure(cls) -> bool:
        """Resolves whether to establish secure SSL connections to ClickHouse."""
        val = os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_SECURE") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_SECURE")
        if val:
            return str(val).lower().strip() in ("true", "1", "yes")
        return False

    @classmethod
    def get_clickhouse_batch_size(cls) -> int:
        """Resolves batch chunk sizing for telemetry insertions."""
        val = os.environ.get("SIM_WAREHOUSE_CLICKHOUSE_BATCH_SIZE") or os.environ.get("RPG_WAREHOUSE_CLICKHOUSE_BATCH_SIZE")
        if val:
            try:
                return int(val)
            except ValueError:
                pass
        return 1000



