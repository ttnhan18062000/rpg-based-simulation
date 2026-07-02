"""
src/systems/social_systems/consequence_events.py
───────────────────────────────────────────────────────────────────────────────
Social Memory Consequence Event Evaluator — Epic 4.3E
(TCK-20260619-E43E-CONSEQUENCE-EVENTS)

Pure function: evaluate_social_consequence() reads cross-episode social memory
records from CampaignState and returns SimulationEvent instances when the
encounter triggers one of the three consequence event kinds:

  LEGENDARY_ARRIVAL      — entity faction_reputation["default"] >= 0.9
  KNOWN_TRAITOR_SPOTTED  — entity flagged in faction_social_memories hostility >= 0.5
  OLD_DEBT_COLLECTED     — entity has a positive relationship_score >= 0.5 with a
                           known entity in the faction's prior social memory

Design constraints (mirrors social_memory.py):
  - MUST NOT import from src.engine or src.core.state at module level.
  - EntityState and CampaignState are duck-typed at runtime.
  - Pure function — no IO, no durable state mutation.
  - Returns a list[SimulationEvent] — callers decide whether to emit/persist.
  - Deterministic: threshold comparisons only, no randomness.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.observability.events import (
    KNOWN_TRAITOR_SPOTTED,  # noqa: F401 — re-exported for callers
    LEGENDARY_ARRIVAL,       # noqa: F401 — re-exported for callers
    OLD_DEBT_COLLECTED,      # noqa: F401 — re-exported for callers
    KnownTraitorSpottedEvent,
    LegendaryArrivalEvent,
    OldDebtCollectedEvent,
    SimulationEvent,
)

if TYPE_CHECKING:
    pass  # EntityState / CampaignState duck-typed at runtime


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

#: Minimum faction_reputation["default"] for LEGENDARY_ARRIVAL to fire.
LEGENDARY_REP_THRESHOLD: float = 0.9

#: Minimum entity_hostility score (0.0–1.0) for KNOWN_TRAITOR_SPOTTED to fire.
TRAITOR_HOSTILITY_THRESHOLD: float = 0.5

#: Minimum relationship_score for OLD_DEBT_COLLECTED to fire.
OLD_DEBT_SCORE_THRESHOLD: float = 0.5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_social_consequence(
    entity: "object",
    faction_id: str,
    campaign_state: "object",
    tick: int = 0,
) -> List[SimulationEvent]:
    """Evaluate which cross-episode consequence events fire for an entity encounter.

    Called at the start of a social encounter when an entity enters or interacts
    with a faction context. Reads cross-episode social memory from campaign_state
    without mutating any live state.

    Parameters
    ----------
    entity : EntityState (duck-typed)
        The entity entering the faction's territory or triggering an encounter.
        Accessed as ``entity.id`` and ``entity.social.public_reputation``.
    faction_id : str
        The faction whose territory/context the entity has entered.
    campaign_state : CampaignState (duck-typed)
        Current campaign state. Accessed via
        ``campaign_state.faction_social_memories`` and
        ``campaign_state.social_memories``.
    tick : int
        Current simulation tick (used for event construction). Default 0.

    Returns
    -------
    List[SimulationEvent]
        Zero or more consequence events. Ordered: traitor → legendary → debt.
        Never None; always a list.

    Determinism
    -----------
    The function is fully deterministic: all branches depend only on threshold
    comparisons on input data. No randomness, no side effects.

    Architecture
    ------------
    This is a read-only query over CampaignState. The returned events are
    *proposals* — callers are responsible for emitting them via the authoritative
    pipeline. This function never mutates entity, campaign_state, or any registry.
    """
    events: List[SimulationEvent] = []

    entity_id: int = entity.id  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 1. KNOWN_TRAITOR_SPOTTED — faction holds a high-hostility grudge
    # ------------------------------------------------------------------
    faction_mem = getattr(campaign_state, "faction_social_memories", {}).get(faction_id)
    if faction_mem is not None:
        hostility = faction_mem.entity_hostility.get(entity_id, 0.0)
        episode_of_offense = faction_mem.episode_of_offense.get(entity_id, 0)
        if hostility >= TRAITOR_HOSTILITY_THRESHOLD:
            events.append(
                KnownTraitorSpottedEvent(
                    tick=tick,
                    entity_id=entity_id,
                    faction_id=faction_id,
                    hostility_score=hostility,
                    episode_of_offense=episode_of_offense,
                    payload={
                        "faction_id": faction_id,
                        "hostility_score": hostility,
                        "episode_of_offense": episode_of_offense,
                    },
                )
            )

    # ------------------------------------------------------------------
    # 2. LEGENDARY_ARRIVAL — entity has outstanding cross-episode reputation
    # ------------------------------------------------------------------
    social_memories = getattr(campaign_state, "social_memories", {})
    social_record = social_memories.get(entity_id)

    if social_record is not None:
        rep = social_record.faction_reputation.get("default", 0.0)
        if rep >= LEGENDARY_REP_THRESHOLD:
            events.append(
                LegendaryArrivalEvent(
                    tick=tick,
                    entity_id=entity_id,
                    faction_id=faction_id,
                    payload={
                        "faction_id": faction_id,
                        "reputation": rep,
                    },
                )
            )

    # ------------------------------------------------------------------
    # 3. OLD_DEBT_COLLECTED — entity has a significant positive bond with a
    #    known entity (first qualifying bond only, for determinism)
    # ------------------------------------------------------------------
    if social_record is not None:
        # Iterate in sorted key order for determinism
        for other_id, score in sorted(social_record.relationship_scores.items()):
            if score >= OLD_DEBT_SCORE_THRESHOLD:
                events.append(
                    OldDebtCollectedEvent(
                        tick=tick,
                        entity_id=entity_id,
                        faction_id=faction_id,
                        debtor_id=other_id,
                        relationship_score=score,
                        payload={
                            "faction_id": faction_id,
                            "debtor_id": other_id,
                            "relationship_score": score,
                        },
                    )
                )
                break  # one OLD_DEBT_COLLECTED per encounter (first qualifying)

    return events
