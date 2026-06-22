"""FactionDecisionPhase — read-only domain phase that emits transient FactionDirective structs.

Runs cadenced inside AuthoritativeApplyPipeline.refine() (E53Ab).
Directives are NEVER persisted in AuthoritativeState — they are transient per-tick scratch
consumed within the same refine() call by E53Ac (directive propagation).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.engine.policy import GovernorPolicy

# ---------------------------------------------------------------------------
# Directive kind constants (plain strings — NOT IntEnum, to keep E53B/C extensible)
# ---------------------------------------------------------------------------
DEFEND_BORDER: str = "DEFEND_BORDER"
TRADE_ROUTE: str = "TRADE_ROUTE"
COMMISSION_QUEST: str = "COMMISSION_QUEST"


# ---------------------------------------------------------------------------
# FactionDirective — frozen, slotted transient value object
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class FactionDirective:
    """Represents a faction-level strategic intention for one decision tick.

    Transient — never written to AuthoritativeState or StateUpdate.
    Re-derived each cadence tick by FactionDecisionPhase.execute().
    """

    faction_id: str
    directive_kind: str  # "DEFEND_BORDER" | "TRADE_ROUTE" | "COMMISSION_QUEST"
    target_faction: Optional[str] = None
    target_region: Optional[str] = None
    priority: float = 1.0
    created_tick: int = 0


# ---------------------------------------------------------------------------
# FactionDecisionPhase — stateless domain phase
# ---------------------------------------------------------------------------
class FactionDecisionPhase:
    """Read-only phase: reads state.factions, emits list[FactionDirective].

    Decision rules (evaluated per faction):
      - DEFEND_BORDER:    tension_level > 0.5  AND territory non-empty
      - TRADE_ROUTE:      military_strength > 0.7  AND tension_level < 0.3
        (mutually exclusive with DEFEND_BORDER via if/elif)
      - COMMISSION_QUEST: territory non-empty (unconditional; priority = tension_level)

    The ``policy`` parameter is accepted for E53B/C compatibility but is unused in E53Ab.
    """

    @staticmethod
    def execute(
        state: AuthoritativeState,
        policy: GovernorPolicy | None = None,
    ) -> list[FactionDirective]:
        """Produce transient FactionDirective list for the current tick.

        Args:
            state:  Current authoritative world state.
            policy: Governor policy (reserved for E53B/C; unused in E53Ab).

        Returns:
            List of FactionDirective objects (may be empty if state.factions is empty).
        """
        directives: list[FactionDirective] = []

        for faction_id, fs in state.factions.items():
            # --- Primary branch: DEFEND_BORDER vs TRADE_ROUTE (mutually exclusive) ---
            if fs.tension_level > 0.5 and len(fs.territory) > 0:
                directives.append(
                    FactionDirective(
                        faction_id=faction_id,
                        directive_kind=DEFEND_BORDER,
                        priority=fs.tension_level,
                        created_tick=state.tick,
                    )
                )
            elif fs.military_strength > 0.7 and fs.tension_level < 0.3:
                directives.append(
                    FactionDirective(
                        faction_id=faction_id,
                        directive_kind=TRADE_ROUTE,
                        priority=1.0,
                        created_tick=state.tick,
                    )
                )

            # --- Unconditional secondary: COMMISSION_QUEST when territory non-empty ---
            if len(fs.territory) > 0:
                directives.append(
                    FactionDirective(
                        faction_id=faction_id,
                        directive_kind=COMMISSION_QUEST,
                        priority=fs.tension_level,
                        created_tick=state.tick,
                    )
                )

        return directives
