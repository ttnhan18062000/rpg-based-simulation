"""
src/domains/combat_engagement/memory_store.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

The single, sanctioned write path into `CognitionModel.memory.combat.opponent_stats`
(docs/mechanics/04_strategic_cognition.md Sec 13.6).

Eviction is by salience, never oldest-first -- copying causal memory's own policy
(`src/domains/memory/phase.py`'s `entries.pop(0)`) would be wrong here and would break this
feature's own three-phase acceptance scenario (engage -> withdraw -> engage-again-once-stronger):
an observer that meets a dozen other creatures after its one frightening encounter would forget the
frightening one before it ever grew strong enough to matter.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from src.core.cognition import CombatMemory
from src.domains.combat_engagement.schema import OpponentModel

# "An entity remembers a handful of things it has met recently or been hurt by, and genuinely
# forgets the rest" (Sec 13.6) -- a small bound, not a performance-tuned number. An unbounded
# per-individual-per-observer collection is O(n^2) durable state and does not scale.
MAX_OPPONENT_MODELS_PER_ENTITY = 8


def compute_salience(prior: Optional[OpponentModel], updated_estimated_power: float, outcome_severity: float = 0.0) -> float:
    """
    Salience rises with the magnitude of surprise (how wrong the prior estimate turned out to be,
    once corrected -- already computed at the moment an estimate updates, so this is a stored
    score, not a new calculation) and with the severity of the outcome (a near-death encounter is
    more salient than a routine win).

    `outcome_severity` is 0.0 for a passive-observation-only update (no combat occurred) and rises
    toward 1.0 for a real fight outcome (e.g. a near-death survival) -- callers own thresholding
    that severity, this function only combines it with observed surprise.
    """
    prior_power = prior.estimated_power if prior is not None else updated_estimated_power
    surprise = abs(updated_estimated_power - prior_power) / max(1.0, abs(prior_power))
    return round(min(1.0, surprise) * 0.6 + min(1.0, max(0.0, outcome_severity)) * 0.4, 4)


def store_opponent_model(combat_memory: CombatMemory, model: OpponentModel) -> CombatMemory:
    """
    Upsert `model` into `combat_memory.opponent_stats`, keyed by `model.subject_key`.

    Updating an existing `subject_key` never grows the collection. Inserting a genuinely new key
    while already at `MAX_OPPONENT_MODELS_PER_ENTITY` evicts the entry with the lowest `salience`
    first -- never the oldest (`last_updated_tick`).
    """
    stats = dict(combat_memory.opponent_stats)
    is_new_key = model.subject_key not in stats

    if is_new_key and len(stats) >= MAX_OPPONENT_MODELS_PER_ENTITY:
        lowest_key = min(stats, key=lambda k: stats[k].salience)
        del stats[lowest_key]

    stats[model.subject_key] = model
    return replace(combat_memory, opponent_stats=stats)
