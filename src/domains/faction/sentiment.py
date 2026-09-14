"""FactionSentimentService — faction-to-faction sentiment derived from real entity interaction.

No imports from src.engine — depends only on src.core and src.content_semantics, matching
diplomatic_state_machine.py's own constraint.

TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION: a real, continuous pre-war tension
producer that doesn't require war -- or even territory -- to exist first. Full design:
docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md §3.2.
"""
from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

from src.core.updates import FactionUpdate, StateUpdate
from src.content_semantics.faction import get_faction_id_str

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState


class FactionSentimentService:
    """Derives faction-to-faction sentiment/tension from real entity interactions.

    Reuses the single real choke point every entity-level interaction system already writes
    through -- SocialBondUpdate (combat.py, contracts.py, appraisal.py) -- rather than adding
    faction-awareness to any of those three systems. Zero changes needed there.
    """

    # Provisional, not a design decision -- dampens one entity-level interaction so it doesn't
    # swing faction-wide standing as hard as it swings the two entities' own bond. Uniform
    # (not per-entity): importance weighting was investigated and cut from this build, see
    # the design proposal §3.2.4.
    FACTION_SCALE_FACTOR: float = 0.1

    # Reuses CalamityPressurePropagator's own real cadence constant (src/world/calamity.py,
    # SEASONAL_PROPAGATION_INTERVAL) rather than inventing a new tick interval -- the closest
    # real precedent for "a periodic, slow-moving world-level drift."
    DECAY_INTERVAL: int = 500
    # Ticks since last_interaction_tick before a pair is considered stale enough to decay.
    DECAY_STALENESS_THRESHOLD: int = 1000
    # Fraction of the current sentiment retained per decay interval past staleness. New
    # mechanism -- no live precedent found for a similarly-shaped directed value (design
    # proposal §3.2.5); this value is a placeholder, not a proposed final one.
    DECAY_FACTOR: float = 0.9

    @staticmethod
    def derive_from_bond_updates(state: "AuthoritativeState", update: StateUpdate) -> List[FactionUpdate]:
        """Scan this tick's already-produced SocialBondUpdates and derive cross-faction
        sentiment + tension consequences.

        Symmetric per pair (mirrors contracts.py's own bidirectional SocialBondUpdate
        emission): both factions record the interaction toward each other. Negative sentiment
        swings additionally raise `pairwise_tension_delta` for that specific rival only (feeding
        DiplomaticStateMachine.compute_transitions()'s pair_tension read); positive swings do
        not lower it here -- peace-making is already a distinct, deliberate action
        (diplomatic_actions.py), not an automatic side-effect of ordinary friendly interaction.

        Deliberately targets `pairwise_tension_delta`, not the ambient `tension_delta` -- a
        faction's fight with one specific rival must not read as tension with every other
        faction it has never met (TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION: this
        was confirmed live as the actual cause of a single HOSTILE pair cascading into blanket
        HOSTILE, then blanket ALLIED among the rest of a 15-faction world, in one tick).
        """
        faction_updates: List[FactionUpdate] = []
        if not state.factions:
            return faction_updates

        for source_entity_id, entity_update in update.entity_updates.items():
            if entity_update.social is None or not entity_update.social.bond_updates:
                continue
            source_entity = state.entities.get(source_entity_id)
            if source_entity is None:
                continue
            source_faction = get_faction_id_str(source_entity)

            for bond_update in entity_update.social.bond_updates:
                if bond_update.sentiment_delta == 0.0 and bond_update.familiarity_delta == 0.0:
                    continue
                target_entity = state.entities.get(bond_update.target_id)
                if target_entity is None:
                    continue
                target_faction = get_faction_id_str(target_entity)
                if source_faction == target_faction:
                    continue  # same-faction interaction; nothing to derive at faction scope

                scale = FactionSentimentService.FACTION_SCALE_FACTOR
                scaled_sentiment = bond_update.sentiment_delta * scale
                scaled_familiarity = bond_update.familiarity_delta * scale
                tension_bump = max(0.0, -scaled_sentiment)  # only hostile swings raise tension

                for a, b in ((source_faction, target_faction), (target_faction, source_faction)):
                    faction_updates.append(FactionUpdate(
                        faction_id=a,
                        faction_sentiment_delta={b: scaled_sentiment},
                        faction_familiarity_delta={b: scaled_familiarity},
                        pairwise_tension_delta={b: tension_bump} if tension_bump else {},
                    ))

        return faction_updates

    @staticmethod
    def decay_stale_sentiments(state: "AuthoritativeState") -> List[FactionUpdate]:
        """Periodic decay toward neutral for faction pairs that haven't interacted recently.

        Uses `faction_sentiment_decay_set` (an absolute value), not `faction_sentiment_delta`
        -- decay must not itself count as a real interaction, or it would reset the very
        staleness clock it's checking and never re-fire for that pair.
        """
        if state.tick % FactionSentimentService.DECAY_INTERVAL != 0:
            return []

        updates: List[FactionUpdate] = []
        for fid, fs in state.factions.items():
            decayed: Dict[str, float] = {}
            for target_fid, fsent in fs.faction_sentiments.items():
                if fsent.sentiment == 0.0:
                    continue
                if state.tick - fsent.last_interaction_tick <= FactionSentimentService.DECAY_STALENESS_THRESHOLD:
                    continue
                decayed[target_fid] = fsent.sentiment * FactionSentimentService.DECAY_FACTOR
            if decayed:
                updates.append(FactionUpdate(faction_id=fid, faction_sentiment_decay_set=decayed))
        return updates
