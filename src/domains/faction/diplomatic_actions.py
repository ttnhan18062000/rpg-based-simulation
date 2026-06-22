"""DiplomaticActionHandler — pure function dispatcher for diplomatic action types (E53Bb).

All handlers are read-only with respect to FactionState. They return FactionUpdate
records; durable mutation happens exclusively through the authoritative apply-path.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from src.core.state import FactionState
    from src.engine.faction_decision import FactionDirective

from src.core.enums import DiplomaticState
from src.core.updates import FactionUpdate


def handle(
    action: FactionDirective,
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    """Dispatch a diplomatic action and return the resulting FactionUpdate list.

    Pure function — no side effects. All returned updates are applied through
    the authoritative pipeline; this function never mutates factions directly.

    Args:
        action:   A diplomatic FactionDirective subtype (TreatyOffer, TradeAgreement, etc.).
        factions: Current faction map (read-only).

    Returns:
        List of FactionUpdate records (may be empty for no-op actions).
    """
    from src.engine.faction_decision import (
        TreatyOffer, TradeAgreement, NonAggressionPact, AllianceProposal, Betrayal
    )

    if isinstance(action, TreatyOffer):
        return _handle_treaty_offer(action, factions)
    if isinstance(action, TradeAgreement):
        return _handle_trade_agreement(action, factions)
    if isinstance(action, NonAggressionPact):
        return _handle_non_aggression_pact(action, factions)
    if isinstance(action, AllianceProposal):
        return _handle_alliance_proposal(action, factions)
    if isinstance(action, Betrayal):
        return _handle_betrayal(action, factions)
    return []


def _handle_treaty_offer(
    action: TreatyOffer,
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    if not action.accepted:
        return []
    return [
        FactionUpdate(
            faction_id=action.from_faction,
            diplomatic_relations_set={action.to_faction: DiplomaticState.NEUTRAL},
            tension_delta=-0.1,
        ),
        FactionUpdate(
            faction_id=action.to_faction,
            diplomatic_relations_set={action.from_faction: DiplomaticState.NEUTRAL},
            tension_delta=-0.1,
        ),
    ]


def _handle_trade_agreement(
    action: TradeAgreement,
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    return [
        FactionUpdate(
            faction_id=action.from_faction,
            diplomatic_relations_set={action.to_faction: DiplomaticState.NEUTRAL},
            tension_delta=-0.15,
        ),
        FactionUpdate(
            faction_id=action.to_faction,
            diplomatic_relations_set={action.from_faction: DiplomaticState.NEUTRAL},
            tension_delta=-0.15,
        ),
    ]


def _handle_non_aggression_pact(
    action: NonAggressionPact,
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    return [
        FactionUpdate(
            faction_id=action.from_faction,
            diplomatic_relations_set={action.to_faction: DiplomaticState.NEUTRAL},
        ),
        FactionUpdate(
            faction_id=action.to_faction,
            diplomatic_relations_set={action.from_faction: DiplomaticState.NEUTRAL},
        ),
    ]


def _handle_alliance_proposal(
    action: AllianceProposal,
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    target_fs = factions.get(action.to_faction)
    target_strength = target_fs.military_strength if target_fs is not None else 1.0

    if action.proposer_strength >= target_strength * 2.0:
        # Proposer dominates: to_faction becomes VASSAL of from_faction
        return [
            FactionUpdate(
                faction_id=action.from_faction,
                diplomatic_relations_set={action.to_faction: DiplomaticState.ALLIED},
            ),
            FactionUpdate(
                faction_id=action.to_faction,
                diplomatic_relations_set={action.from_faction: DiplomaticState.VASSAL},
            ),
        ]
    return [
        FactionUpdate(
            faction_id=action.from_faction,
            diplomatic_relations_set={action.to_faction: DiplomaticState.ALLIED},
        ),
        FactionUpdate(
            faction_id=action.to_faction,
            diplomatic_relations_set={action.from_faction: DiplomaticState.ALLIED},
        ),
    ]


def _handle_betrayal(
    action: Betrayal,
    factions: Dict[str, FactionState],
) -> List[FactionUpdate]:
    from_fs = factions.get(action.from_faction)
    if from_fs is None:
        return []
    current = from_fs.diplomatic_relations.get(action.to_faction)
    if current != DiplomaticState.ALLIED:
        return []
    return [
        FactionUpdate(
            faction_id=action.from_faction,
            diplomatic_relations_set={action.to_faction: DiplomaticState.HOSTILE},
        ),
        FactionUpdate(
            faction_id=action.to_faction,
            diplomatic_relations_set={action.from_faction: DiplomaticState.HOSTILE},
            tension_delta=0.3,
        ),
    ]
