from __future__ import annotations

from dataclasses import dataclass
from src_legacy.core.governance import RuntimeMode


@dataclass(frozen=True, slots=True)
class GovernorPolicy:
    """
    Explicit decisions emitted by the Resource Governor for system consumption.
    M5 Law: Subsystems respond to these flags, not to raw pressure enums.
    """
    allow_opportunistic: bool = True
    allow_non_authoritative_periodic: bool = True
    diagnostic_verbosity: str = "FULL"  # "FULL", "MINIMAL", "ERROR", "MUTED"
    metrics_detail: str = "HIGH"        # "HIGH", "LOW", "MUTED"
    
    # M8 Adaptive Concurrency
    concurrency_limit: float = 1.0     # 0.0 to 1.0 multiplier of active pool
    
    # M6 Replay Policy
    replay_allowed: bool = True
    replay_richness: str = "FULL"       # "FULL", "MINIMAL", "OFF"
    allow_subsystem_traces: bool = True

    @classmethod
    def from_mode(cls, mode: RuntimeMode) -> GovernorPolicy:
        """
        Policy Waterfall according to Milestone 5/6 Degradation Matrix.
        """
        if mode == RuntimeMode.NORMAL:
            return cls(
                allow_opportunistic=True,
                allow_non_authoritative_periodic=True,
                diagnostic_verbosity="FULL",
                metrics_detail="HIGH",
                concurrency_limit=1.0,
                replay_allowed=True,
                replay_richness="FULL",
                allow_subsystem_traces=True
            )
        
        if mode == RuntimeMode.CONSTRAINED:
            return cls(
                allow_opportunistic=True,
                allow_non_authoritative_periodic=True,
                diagnostic_verbosity="MINIMAL",
                metrics_detail="HIGH",
                concurrency_limit=1.0,
                replay_allowed=True,
                replay_richness="FULL",
                allow_subsystem_traces=False # Drop internal traces first
            )
            
        if mode == RuntimeMode.DEGRADED:
            return cls(
                allow_opportunistic=False,
                allow_non_authoritative_periodic=True,
                diagnostic_verbosity="ERROR",
                metrics_detail="LOW",
                concurrency_limit=0.5,
                replay_allowed=True,
                replay_richness="MINIMAL",
                allow_subsystem_traces=False
            )
            
        if mode == RuntimeMode.SURVIVAL:
            return cls(
                allow_opportunistic=False,
                allow_non_authoritative_periodic=False,
                diagnostic_verbosity="MUTED",
                metrics_detail="MUTED",
                concurrency_limit=0.25,
                replay_allowed=False,
                replay_richness="OFF",
                allow_subsystem_traces=False
            )
            
        return cls()
