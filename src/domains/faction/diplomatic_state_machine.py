"""DiplomaticStateMachine — pure tension/threshold-driven diplomatic state transitions (E53Bc).

No imports from src.engine — depends only on src.core and src.domains.faction.

Transition priority (single-step per pair per call):
  1. WAR → NEUTRAL      both military_strength < 0.3 (exhaustion)
  2. HOSTILE → WAR      aggressor military_strength > defender * 1.2
  3. TENSE → HOSTILE    pair_tension > 0.7 OR shared territory
  4. NEUTRAL → TENSE    pair_tension > 0.4

ALLIED and VASSAL are terminal — suppressed from threshold transitions.
Pair tension proxy: max(a.tension_level, b.tension_level).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from src.core.state import FactionState

from src.core.enums import DiplomaticState
from src.core.updates import FactionUpdate


def compute_transitions(factions: Dict[str, FactionState]) -> List[FactionUpdate]:
    """Evaluate all faction pairs and return FactionUpdate list for required transitions.

    Pairs are iterated in lexicographic order (a < b) to produce deterministic output.
    At most one transition fires per pair per call (single-step enforcement).

    Args:
        factions: Current faction map (read-only).

    Returns:
        List of FactionUpdate records encoding the required relation transitions.
    """
    updates: List[FactionUpdate] = []
    faction_ids = sorted(factions.keys())

    for i, fid_a in enumerate(faction_ids):
        for fid_b in faction_ids[i + 1:]:
            fa = factions[fid_a]
            fb = factions[fid_b]

            current_ab = fa.diplomatic_relations.get(fid_b, DiplomaticState.NEUTRAL)

            # ALLIED and VASSAL are terminal — no tension-driven transitions
            if current_ab in (DiplomaticState.ALLIED, DiplomaticState.VASSAL):
                continue

            pair_tension = max(fa.tension_level, fb.tension_level)
            shared_territory = bool(set(fa.territory) & set(fb.territory))

            if current_ab == DiplomaticState.WAR:
                if fa.military_strength < 0.3 and fb.military_strength < 0.3:
                    updates.extend([
                        FactionUpdate(faction_id=fid_a, diplomatic_relations_set={fid_b: DiplomaticState.NEUTRAL}),
                        FactionUpdate(faction_id=fid_b, diplomatic_relations_set={fid_a: DiplomaticState.NEUTRAL}),
                    ])

            elif current_ab == DiplomaticState.HOSTILE:
                if fa.military_strength > fb.military_strength * 1.2 or fb.military_strength > fa.military_strength * 1.2:
                    updates.extend([
                        FactionUpdate(faction_id=fid_a, diplomatic_relations_set={fid_b: DiplomaticState.WAR}),
                        FactionUpdate(faction_id=fid_b, diplomatic_relations_set={fid_a: DiplomaticState.WAR}),
                    ])

            elif current_ab == DiplomaticState.TENSE:
                if pair_tension > 0.7 or shared_territory:
                    updates.extend([
                        FactionUpdate(faction_id=fid_a, diplomatic_relations_set={fid_b: DiplomaticState.HOSTILE}),
                        FactionUpdate(faction_id=fid_b, diplomatic_relations_set={fid_a: DiplomaticState.HOSTILE}),
                    ])

            elif current_ab == DiplomaticState.NEUTRAL:
                if pair_tension > 0.4:
                    updates.extend([
                        FactionUpdate(faction_id=fid_a, diplomatic_relations_set={fid_b: DiplomaticState.TENSE}),
                        FactionUpdate(faction_id=fid_b, diplomatic_relations_set={fid_a: DiplomaticState.TENSE}),
                    ])

    return updates


def events_from_transitions(
    transition_updates: List[FactionUpdate],
    alliance_updates: List[FactionUpdate],
    prior_factions: Dict[str, "FactionState"],
    tick: int,
) -> list:
    """Build WorldEvent list from transition and alliance update batches (E53Bd).

    Deduplicates by pair — emits exactly one WorldEvent per faction pair per call.
    subject format: ":".join(sorted([fid_a, fid_b])) for narrative ledger dedup.

    Faction IDs go in WorldEvent.subject (payload is Dict[str, float], not Any).

    Args:
        transition_updates: FactionUpdates from compute_transitions().
        alliance_updates:   FactionUpdates from DiplomaticActionHandler alliance path.
        prior_factions:     Faction map BEFORE updates applied (for WAR→NEUTRAL detection).
        tick:               Current simulation tick.

    Returns:
        List of WorldEvent objects (no src.engine imports required).
    """
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

    events: list = []
    seen_pairs: set = set()

    for upd in transition_updates:
        for other_fid, new_state in upd.diplomatic_relations_set.items():
            pair = frozenset([upd.faction_id, other_fid])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            subject = ":".join(sorted([upd.faction_id, other_fid]))

            if new_state == DiplomaticState.WAR:
                events.append(WorldEvent(
                    category=WorldEventCategory.FACTION_WAR_DECLARED,
                    tick=tick,
                    subject=subject,
                ))
            elif new_state == DiplomaticState.NEUTRAL:
                # Only a peace treaty if the prior relation was WAR
                prior_fs = prior_factions.get(upd.faction_id)
                if prior_fs is not None:
                    prior_rel = prior_fs.diplomatic_relations.get(
                        other_fid, DiplomaticState.NEUTRAL
                    )
                    if prior_rel == DiplomaticState.WAR:
                        events.append(WorldEvent(
                            category=WorldEventCategory.FACTION_PEACE_TREATY,
                            tick=tick,
                            subject=subject,
                        ))

    seen_alliance_pairs: set = set()
    for upd in alliance_updates:
        for other_fid, new_state in upd.diplomatic_relations_set.items():
            if new_state == DiplomaticState.ALLIED:
                pair = frozenset([upd.faction_id, other_fid])
                if pair in seen_alliance_pairs:
                    continue
                seen_alliance_pairs.add(pair)
                subject = ":".join(sorted([upd.faction_id, other_fid]))
                events.append(WorldEvent(
                    category=WorldEventCategory.FACTION_ALLIANCE_FORMED,
                    tick=tick,
                    subject=subject,
                ))

    return events


def compute_common_enemy_pairs(
    factions: Dict[str, FactionState],
) -> List[Tuple[str, str, float]]:
    """Return (fid_a, fid_b, proposer_strength) for pairs that share a common hostile enemy.

    Used by the pipeline to generate AllianceProposal directives without requiring
    this module to import from src.engine. One proposal per pair per tick.

    Args:
        factions: Current faction map (read-only).

    Returns:
        List of (fid_a, fid_b, proposer_strength) tuples where fid_a < fid_b lexicographically.
    """
    results: List[Tuple[str, str, float]] = []
    faction_ids = sorted(factions.keys())
    _hostile_states = (DiplomaticState.HOSTILE, DiplomaticState.WAR)

    for i, fid_a in enumerate(faction_ids):
        for fid_b in faction_ids[i + 1:]:
            current_ab = factions[fid_a].diplomatic_relations.get(fid_b, DiplomaticState.NEUTRAL)
            if current_ab in (DiplomaticState.ALLIED, DiplomaticState.VASSAL):
                continue
            for fid_c in faction_ids:
                if fid_c == fid_a or fid_c == fid_b:
                    continue
                a_toward_c = factions[fid_a].diplomatic_relations.get(fid_c, DiplomaticState.NEUTRAL)
                b_toward_c = factions[fid_b].diplomatic_relations.get(fid_c, DiplomaticState.NEUTRAL)
                if a_toward_c in _hostile_states and b_toward_c in _hostile_states:
                    results.append((fid_a, fid_b, factions[fid_a].military_strength))
                    break  # one proposal per pair per tick

    return results
