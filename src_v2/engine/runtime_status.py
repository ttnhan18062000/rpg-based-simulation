from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import List, Optional
from src_v2.core.governance import RuntimeMode, PressureSignals


@dataclass
class RuntimeStatus:
    """
    Operational control state for the simulation engine.
    M5 Law: This state is isolated from AuthoritativeState and does not 
    contaminate simulation hashes.
    """
    current_mode: RuntimeMode = RuntimeMode.NORMAL
    
    # Stability tracking
    mode_dwell_ticks: int = 0
    
    # Bounded signal history (Step 5 tightening)
    # Stores the last 100 sets of pressure signals.
    signal_history: deque[PressureSignals] = field(
        default_factory=lambda: deque(maxlen=100)
    )

    def record_signals(self, signals: PressureSignals) -> None:
        """Append fresh signals to the bounded operational history."""
        self.signal_history.append(signals)

    def increment_dwell(self) -> None:
        """Track how long we've stayed in the current mode."""
        self.mode_dwell_ticks += 1

    def reset_dwell(self, new_mode: RuntimeMode) -> None:
        """Reset counters when a transition occurs."""
        self.current_mode = new_mode
        self.mode_dwell_ticks = 0
