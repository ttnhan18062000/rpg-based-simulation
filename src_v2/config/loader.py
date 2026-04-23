from __future__ import annotations
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src_v2.config.profiles import RuntimeProfile, HardwareClass

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Law: The engine must support configuration precedence: 
    CLI > Env > YAML > Defaults. (Phase 10 Requirement)
    """

    @staticmethod
    def load_profile(
        profile_name: str = "cli_default",
        config_path: Optional[str] = None,
        env_prefix: str = "RPG_",
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> RuntimeProfile:
        """
        Loads a RuntimeProfile with full precedence resolution.
        """
        # 1. Base Defaults (Hardcoded for "cli_default")
        # In a real system, these might come from a internal registry of known profiles.
        base_data = {
            "name": profile_name,
            "hardware_class": HardwareClass.CLASS_B,
            "max_ram_mb": 1024,
            "max_cpu_percent": 80.0,
            "max_worker_count": 4,
            "max_queue_depth": 100,
            "max_replay_buffer_kb": 4096,
            "max_observability_budget_percent": 10.0,
            "max_tick_budget_ms": 50.0
        }

        # 2. YAML Config
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    yaml_data = yaml.safe_load(f)
                    if yaml_data and "profiles" in yaml_data:
                        profile_data = yaml_data["profiles"].get(profile_name, {})
                        base_data.update(profile_data)
            except Exception as e:
                logger.warning(f"Failed to load YAML config from {config_path}: {e}")

        # 3. Environment Variables (e.g. RPG_MAX_WORKER_COUNT=8)
        for field in RuntimeProfile.model_fields:
            env_key = f"{env_prefix}{field.upper()}"
            if env_key in os.environ:
                val = os.environ[env_key]
                # Basic type conversion
                field_type = RuntimeProfile.model_fields[field].annotation
                try:
                    if field_type == int:
                        base_data[field] = int(val)
                    elif field_type == float:
                        base_data[field] = float(val)
                    elif field_type == bool:
                        base_data[field] = val.lower() in ("true", "1", "yes")
                    elif issubclass(field_type, str): # Handle HardwareClass Enum
                        base_data[field] = val
                except ValueError:
                    logger.warning(f"Invalid environment value for {env_key}: {val}")

        # Special case: BROKER_DISABLED=1
        if os.environ.get("BROKER_DISABLED") == "1":
            logger.info("BROKER_DISABLED=1 detected. Forcing max_worker_count=0.")
            base_data["max_worker_count"] = 0

        # Special case: TELEMETRY_DISABLED=1
        if os.environ.get("TELEMETRY_DISABLED") == "1":
            logger.info("TELEMETRY_DISABLED=1 detected. Disabling observability budget.")
            base_data["max_observability_budget_percent"] = 0.0

        # 4. CLI Overrides
        if cli_overrides:
            base_data.update({k: v for k, v in cli_overrides.items() if v is not None})

        return RuntimeProfile(**base_data)
