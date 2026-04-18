from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from pydantic import ValidationError

if TYPE_CHECKING:
    from src_v2.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when a starting configuration violates the engine contract."""
    pass


class ProfileValidator:
    """
    Law: The engine must validate runtime configuration and profile 
    compatibility at startup. (M7 Rule 5)
    """

    @staticmethod
    def validate_profile(profile: RuntimeProfile) -> None:
        """
        Verify that a profile is internally consistent and within 
        declared resource laws.
        """
        # 1. Budget consistency
        # Replay + Observability + Buffer overhead should not consume 
        # the entire performance envelope.
        if profile.max_observability_budget_percent >= 50.0:
            raise ConfigValidationError(
                f"Observability budget ({profile.max_observability_budget_percent}%) "
                "is excessively high (>=50%). This threatens simulation stability."
            )

        # 2. Logic Consistency (impossible combinations)
        if profile.max_replay_buffer_kb > 0 and profile.max_ram_mb <= 16:
             raise ConfigValidationError(
                "Profile defines a replay buffer but has extremely low RAM allowance (<=16MB). "
                "This is an inconsistent configuration."
            )

        # 3. Hardware Realism (M7: Warning only)
        # Empirical feasibility pre-checks based on class.
        if "CLASS_C" in str(profile.hardware_class) and profile.max_tick_budget_ms < 5.0:
            logger.warning(
                "ALERT: Aggressive tick budget (%.1fms) on Class C hardware. "
                "Feasibility not certified until M9.", profile.max_tick_budget_ms
            )

    @staticmethod
    def validate_flags(flags: dict) -> None:
        """
        Verify that operational flags are safe and do not bypass 
        authoritative semantics. (M7 Rule 8/Control Matrix)
        """
        forbidden_flags = ["FORCE_NORMAL", "BYPASS_GOVERNOR", "DISABLE_RESOURCE_CEILINGS"]
        
        for flag in forbidden_flags:
            if flags.get(flag):
                raise ConfigValidationError(
                    f"Operational flag '{flag}' is FORBIDDEN. "
                    "Flags must remain subordinate to the resource contract."
                )
