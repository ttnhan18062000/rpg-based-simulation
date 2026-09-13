"""
src/domains/combat_engagement/learning_outcome.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

The single, sanctioned place the real CombatUpdate.outcome_kind -> CombatLearning.learn() outcome
mapping lives (docs/mechanics/04_strategic_cognition.md Sec 13.5a). Scattering this translation
across each real resolver call site is how a second, divergent mapping appears later.

Classification is per-participant, keyed on that participant's OWN role and OWN post-exchange HP
ratio -- never a single shared outcome for both sides. Both classify_* functions read only their
own participant's already-resolved, real fields; neither reads the other's in-progress result, so
applying both in either order produces identical results (Sec 13.5a's own determinism/order-
independence requirement).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional, Tuple

from src.core.combat_constants import NEAR_DEATH_HP_RATIO
from src.core.cognition import CognitionModel
from src.core.state import EntityState
from src.domains.combat_engagement.learning import CombatLearning
from src.domains.combat_engagement.memory_store import compute_salience, store_opponent_model
from src.domains.combat_engagement.schema import OpponentModel

# outcome_kind values where the DEFENDER died in some form -- the ATTACKER won, the DEFENDER lost.
# SURVIVE (defender lived) and REJECTED (nothing happened) are deliberately absent: both are
# inconclusive for combat-learning purposes (Sec 13.5a) -- manufacturing confidence from an
# unresolved fight, or from an attack that never legally happened, would corrupt the estimate.
_DEFEATED_OUTCOME_KINDS = ("KILL", "DEFEAT", "PERMADEATH", "REBIRTH")

# Salience severities per classification -- a near-death correction and a real loss are both
# highly salient (Sec 13.6: "a near-death encounter is more salient than a routine win"); an easy
# win is real signal but milder.
_SEVERITY_NEAR_DEATH = 1.0
_SEVERITY_LOST = 0.8
_SEVERITY_WON_EASY = 0.3


def classify_defender_outcome(outcome_kind: str) -> Optional[str]:
    """What the DEFENDER learns about the ATTACKER from this exchange."""
    if outcome_kind in _DEFEATED_OUTCOME_KINDS:
        return "LOST"
    return None


def classify_attacker_outcome(outcome_kind: str, attacker_hp_ratio: float) -> Optional[str]:
    """
    What the ATTACKER learns about the DEFENDER from this exchange. `attacker_hp_ratio` is the
    attacker's OWN current hp/max_hp -- not touched by this exchange's own CombatUpdate (only the
    defender's combat component is, per src/engine/combat.py's real resolvers), so it already
    reflects whatever damage this attacker has accumulated across the real, ongoing multi-tick
    fight this exchange concludes.
    """
    if outcome_kind in _DEFEATED_OUTCOME_KINDS:
        return "NEAR_DEATH" if attacker_hp_ratio < NEAR_DEATH_HP_RATIO else "WON_EASY"
    return None


_SEVERITY_BY_OUTCOME = {
    "NEAR_DEATH": _SEVERITY_NEAR_DEATH,
    "LOST": _SEVERITY_LOST,
    "WON_EASY": _SEVERITY_WON_EASY,
}


def _apply_single_learning(
    cognition: CognitionModel,
    opponent_id: int,
    learning_outcome: str,
    observed_damage: float,
    tick: int,
) -> CognitionModel:
    """Apply one CombatLearning.learn() call against a cognition model, return the updated one."""
    subject_key = f"entity.{opponent_id}"
    prior_memory = cognition.memory.combat.opponent_stats.get(subject_key)

    updated_model = CombatLearning.learn(
        memory=prior_memory,
        subject_key=subject_key,
        outcome=learning_outcome,
        observed_damage=observed_damage,
        observed_skills=(),
        tick=tick,
    )
    severity = _SEVERITY_BY_OUTCOME.get(learning_outcome, 0.0)
    updated_model = replace(
        updated_model,
        salience=compute_salience(prior_memory, updated_model.estimated_power, outcome_severity=severity),
    )

    new_combat_memory = store_opponent_model(cognition.memory.combat, updated_model)
    new_memory = replace(cognition.memory, combat=new_combat_memory)
    return replace(cognition, memory=new_memory)


def _learn_and_store(
    learner: EntityState,
    opponent_id: int,
    learning_outcome: str,
    observed_damage: float,
    tick: int,
) -> CognitionModel:
    """Apply one participant's own CombatLearning.learn() call and return their updated CognitionModel."""
    return _apply_single_learning(learner.cognition, opponent_id, learning_outcome, observed_damage, tick)


def apply_combat_learning(
    attacker: EntityState,
    defender: EntityState,
    outcome_kind: str,
    damage_taken: float,
    tick: int,
) -> Tuple[Optional[CognitionModel], Optional[CognitionModel]]:
    """
    Classify and apply combat learning for both real participants of one resolved exchange.
    Returns `(new_attacker_cognition, new_defender_cognition)` -- either may be `None` if that
    participant's own outcome was inconclusive (Sec 13.5a: SURVIVE/REJECTED teach nothing).
    """
    attacker_hp_ratio = attacker.combat.hp / max(1, attacker.combat.max_hp)

    attacker_outcome = classify_attacker_outcome(outcome_kind, attacker_hp_ratio)
    defender_outcome = classify_defender_outcome(outcome_kind)

    new_attacker_cognition = (
        _learn_and_store(attacker, defender.id, attacker_outcome, damage_taken, tick)
        if attacker_outcome is not None else None
    )
    new_defender_cognition = (
        _learn_and_store(defender, attacker.id, defender_outcome, damage_taken, tick)
        if defender_outcome is not None else None
    )

    return new_attacker_cognition, new_defender_cognition


def apply_fled_learning(
    fleeing_entity: EntityState,
    evaded_hostile_ids: Tuple[int, ...],
    tick: int,
) -> Optional[CognitionModel]:
    """
    Sec 13.5a FLED: the real producer is src/engine/movement.py's own
    combat_escape="EVASIVE_SUCCESS" property update (a separate real call site from
    src/engine/combat.py's resolvers, so this is never reached via apply_combat_learning() above).
    The fleeing entity learns a weak "FLED" correction about each real hostile it evaded this tick
    -- Sec 13.5a's own worked scenario requires this: "the entity that flees a fight it is losing
    is precisely the one that must remember why it fled."

    Deliberately one-sided: the reciprocal (each evaded hostile learning about the fleeing entity)
    is NOT written here. Unlike the attacker/defender case above, an evaded opportunity attack
    produces no CombatUpdate at all (skip_oa is true precisely because it never resolved) -- there
    is no real outcome for a hostile's own post-exchange HP ratio to classify, so a hostile-side
    write here would have no real signal backing it.
    """
    if not evaded_hostile_ids:
        return None
    cognition = fleeing_entity.cognition
    for hostile_id in evaded_hostile_ids:
        cognition = _apply_single_learning(cognition, hostile_id, "FLED", observed_damage=0.0, tick=tick)
    return cognition
