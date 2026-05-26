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
    DEBUG = "DEBUG"
    CERTIFICATION = "CERTIFICATION"
    LONG_RUN = "LONG_RUN"


class ObservabilityConfig:
    """
    Thread-safe global manager for resolving the active simulation observability mode.
    Precedence: Direct override -> Environment variable -> Default (LIGHT)
    """
    _override_mode: Optional[ObservabilityMode] = None
    _lock = threading.Lock()

    @classmethod
    def set_override_mode(cls, mode: Optional[ObservabilityMode]) -> None:
        """Sets a programmatic override mode, e.g. for specific tests."""
        with cls._lock:
            cls._override_mode = mode

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



