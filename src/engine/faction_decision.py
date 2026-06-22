"""FactionDecisionPhase — read-only domain phase that emits transient FactionDirective structs.
FactionAwarenessService — reads recent world events and produces FactionUpdate tension deltas.

Runs inside AuthoritativeApplyPipeline.refine() before adventure_decision (E53Ac).
Directives are NEVER persisted in AuthoritativeState — they are transient per-tick scratch
consumed within the same refine() call by E53Ac (directive propagation).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Sequence

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.engine.policy import GovernorPolicy

# Directive kind constants live in faction_constants to avoid circular imports
# with scoring.py (which also imports these).
from src.engine.faction_constants import DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST
from src.domains.world_emergence.schema import WorldEventCategory, WorldEvent
from src.core.updates import FactionUpdate


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
# Diplomatic action subtypes of FactionDirective (E53Bb)
# All new fields carry defaults so subclass __init__ ordering is valid.
# Callers always supply from_faction/to_faction/terms as keyword args.
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TreatyOffer(FactionDirective):
    """Proposed treaty between factions. Handler is a no-op if accepted=False."""
    from_faction: str = ""
    to_faction: str = ""
    terms: str = ""         # "non_aggression" | "trade" | "alliance" | "vassal"
    accepted: bool = False


@dataclass(frozen=True, slots=True)
class TradeAgreement(FactionDirective):
    """Confirmed trade agreement → both factions NEUTRAL, tension -0.15."""
    from_faction: str = ""
    to_faction: str = ""


@dataclass(frozen=True, slots=True)
class NonAggressionPact(FactionDirective):
    """Non-aggression pact → both factions NEUTRAL, no tension change."""
    from_faction: str = ""
    to_faction: str = ""


@dataclass(frozen=True, slots=True)
class AllianceProposal(FactionDirective):
    """Alliance or vassal proposal.

    If proposer_strength >= target_strength * 2.0: target becomes VASSAL.
    Otherwise: both become ALLIED.
    """
    from_faction: str = ""
    to_faction: str = ""
    proposer_strength: float = 1.0


@dataclass(frozen=True, slots=True)
class Betrayal(FactionDirective):
    """Break an ALLIED relation. Guard: only valid when current relation is ALLIED.

    Result: both factions set to HOSTILE; betrayed faction receives tension_delta +0.3.
    Returns empty list if current relation is not ALLIED.
    """
    from_faction: str = ""
    to_faction: str = ""


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


# ---------------------------------------------------------------------------
# FactionAwarenessService — tension updates from world events
# ---------------------------------------------------------------------------
class FactionAwarenessService:
    """Observes recent WorldEvents and produces FactionUpdate tension deltas.

    Uses ``state.recent_world_events`` which contains the PREVIOUS tick's event
    window (inherent one-tick lag — state is frozen at tick entry, same as all
    WorldEmergencePhase signal propagation).

    Cap (min 0.0, max 1.0) is enforced by the authoritative apply-path, not here.
    """

    @staticmethod
    def compute_tension_updates(
        state: AuthoritativeState,
        recent_events: Sequence[WorldEvent],
    ) -> list[FactionUpdate]:
        """Return one FactionUpdate(tension_delta=+0.1) per faction per RESOURCE_DEPLETED event
        that occurred in that faction's territory.

        Args:
            state:         Current authoritative world state (read-only).
            recent_events: Bounded window of recent WorldEvents from state.

        Returns:
            List of FactionUpdate records (may be empty).
        """
        updates: list[FactionUpdate] = []
        for event in recent_events:
            if event.category != WorldEventCategory.RESOURCE_DEPLETED:
                continue
            if event.region_id is None:
                continue
            for faction_id, fs in state.factions.items():
                if event.region_id in fs.territory:
                    updates.append(FactionUpdate(faction_id=faction_id, tension_delta=0.1))
        return updates
