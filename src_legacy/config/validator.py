from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from pydantic import ValidationError

if TYPE_CHECKING:
    from src_legacy.config.profiles import RuntimeProfile

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
        if profile.max_observability_budget_percent >= 50.0:
            raise ConfigValidationError(
                f"Observability budget ({profile.max_observability_budget_percent}%) "
                "is excessively high (>=50%). This threatens simulation stability."
            )

        # 2. Performance Envelope Sanity
        if profile.max_tick_budget_ms < 1.0:
             raise ConfigValidationError(
                f"Tick budget {profile.max_tick_budget_ms}ms is sub-millisecond. "
                "The engine does not certify sub-ms deterministic stability."
            )

        # 3. Logic Consistency (impossible combinations)
        if profile.max_replay_buffer_kb > 0 and profile.max_ram_mb <= 32:
             raise ConfigValidationError(
                f"Profile defines a replay buffer ({profile.max_replay_buffer_kb}KB) "
                f"but has insufficient RAM allowance ({profile.max_ram_mb}MB). "
                "Minimum 32MB RAM required for any replay-enabled profile."
            )

        # 4. Hardware Realism (M7/C: Warning only)
        # Feasibility pre-checks based on class. Reserved for M9 certification.
        if "CLASS_C" in str(profile.hardware_class) and profile.max_tick_budget_ms < 5.0:
            logger.warning(
                "ALERT: Aggressive tick budget (%.1fms) on Class C hardware. "
                "Feasibility not certified until M9.", profile.max_tick_budget_ms
            )

    @staticmethod
    def validate_flags(flags: dict, profile: Optional[RuntimeProfile] = None) -> None:
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

        # Contradictory Flag/Profile Logic (Milestone C)
        if flags.get("SURVIVAL_ONLY") and flags.get("REPLAY_ENABLED"):
             raise ConfigValidationError(
                "Contradictory Flags: SURVIVAL_ONLY and REPLAY_ENABLED are mutually exclusive. "
                "Survival modes must prioritize authoritative CPU over observational trace."
            )
        
        if profile and flags.get("REPLAY_ENABLED") and profile.max_replay_buffer_kb == 0:
            raise ConfigValidationError(
                "Contradictory Config: REPLAY_ENABLED flag set, but profile has 0KB replay buffer."
            )
