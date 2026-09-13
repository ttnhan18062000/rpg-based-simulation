"""
src/domains/combat_engagement/power.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

True power, apparent power, power-gap-driven observation uncertainty, and deterministic
observation noise -- docs/mechanics/04_strategic_cognition.md Sec 13.2/13.3/13.9.

Everything here is pure arithmetic on already-stable inputs. No RNG object anywhere, per Sec
13.9's determinism law: same seed/tick/observer/observed -> same estimate, always.
"""

from __future__ import annotations

import hashlib
import math

from src.core.state import EntityState

# D-11 (docs/plans/deferred_tuning_decisions_register.md): first-pass, evidence-backed coefficients.
# atk + def_stat*0.5 reuses CapabilityEstimateService's own base_power sub-expression (Sec 6.12);
# max_hp*0.1 is scaled so its raw 35-150 range does not swamp the 4.5-28 atk/def term. Weights are
# awaiting real-run calibration, not a re-derivation target for this ticket.
TRUE_POWER_DEF_WEIGHT = 0.5
TRUE_POWER_MAX_HP_WEIGHT = 0.1

# apparent_power()'s condition curve -- lifted unchanged from OpponentPerceptionService.estimate()'s
# own pre-existing hp_ratio adjustment (perception.py), just named and extracted per Sec 13.2.
_APPARENT_POWER_CRITICAL_HP_RATIO = 0.3
_APPARENT_POWER_CRITICAL_MULTIPLIER = 0.6
_APPARENT_POWER_WOUNDED_HP_RATIO = 0.7
_APPARENT_POWER_WOUNDED_MULTIPLIER = 0.85

# gap_uncertainty()'s curve constants -- a first pass on shape, not a tuned final answer (matches
# D-11's own precedent of recording evidence-backed axes now, weights later).
UNCERTAINTY_FLOOR = 0.05
UNCERTAINTY_CEILING = 0.6
_GAP_SHARPNESS_BASE = 0.05
_PERCEPTION_SCALE_MAX = 99.0  # docs/mechanics/01_entity_anatomy.md Sec 1: PER scale is 1-99.

# deterministic_observation_noise()'s output range and how much it can perturb an estimate at
# maximum uncertainty.
NOISE_MAGNITUDE_AT_MAX_UNCERTAINTY = 0.3


def true_power(entity: EntityState) -> float:
    """
    An entity's own real, static combat strength (Sec 13.2). Computed identically for both sides
    of a comparison. `evolution_level` is deliberately excluded, not merely unweighted -- levelling
    grants Attribute Points that already feed atk/def_stat/max_hp's own derived-stat formulas
    (docs/mechanics/01_entity_anatomy.md), so including it again would double-count the same
    progression.
    """
    combat = entity.combat
    return combat.atk + combat.def_stat * TRUE_POWER_DEF_WEIGHT + combat.max_hp * TRUE_POWER_MAX_HP_WEIGHT


def apparent_power(entity: EntityState) -> float:
    """
    `true_power(entity)` adjusted for the entity's current condition (Sec 13.2) -- an identity
    with respect to deception today; a future deception mechanism changes only this function's own
    body, nothing downstream of it.
    """
    tp = true_power(entity)
    max_hp = max(1, entity.combat.max_hp)
    hp_ratio = entity.combat.hp / max_hp

    if hp_ratio < _APPARENT_POWER_CRITICAL_HP_RATIO:
        return tp * _APPARENT_POWER_CRITICAL_MULTIPLIER
    if hp_ratio < _APPARENT_POWER_WOUNDED_HP_RATIO:
        return tp * _APPARENT_POWER_WOUNDED_MULTIPLIER
    return tp


def deterministic_observation_noise(seed: int, tick: int, observer_id: int, observed_id: int) -> float:
    """
    A pure function of `(seed, tick, observer_id, observed_id)` mapped into `[-1.0, 1.0)` -- the
    same seed/tick/observer/observed always produces the same value, following
    `_hash_point_in_bounds()`'s own precedent (src/worldassembly/resolver.py:947): a stable key
    hashed via hashlib.sha256, never a call into DeterministicRNG or any other seeded-but-stateful
    generator (Sec 13.9).
    """
    key = f"{seed}:{tick}:{observer_id}:{observed_id}"
    digest = hashlib.sha256(key.encode()).digest()
    unit_interval = int.from_bytes(digest[:8], "big") / float(2 ** 64)
    return unit_interval * 2.0 - 1.0


def gap_uncertainty(gap: float, perception: float) -> float:
    """
    Observation error driven by the power gap, not the observer alone (Sec 13.3): confident at
    extremes, maximally uncertain exactly at parity (`gap == 0`) -- the point of the design, not a
    side effect to smooth away. A higher `Perception (PER)` observer needs a smaller gap before its
    estimate sharpens (a larger `perception` value decays uncertainty faster as `gap` grows).
    """
    perception_factor = max(0.0, min(1.0, perception / _PERCEPTION_SCALE_MAX))
    sharpness = _GAP_SHARPNESS_BASE * (1.0 + perception_factor)
    decay = math.exp(-abs(gap) * sharpness)
    return UNCERTAINTY_FLOOR + (UNCERTAINTY_CEILING - UNCERTAINTY_FLOOR) * decay
