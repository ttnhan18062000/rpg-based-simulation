"""
src/domains/culture/settlement_personality.py
───────────────────────────────────────────────────────────────────────────────
SettlementPersonalityService — the first non-Campaign-mode-episode-machinery
read-side consumer of Culture Drift (idea 61).

Pure and stateless: wraps the already-certified
CulturalBiasApplicator.compute_culture_delta over a canonical tag set to
produce a named settlement-personality signal. No new formulas, no new
threshold — CULTURE_ACTIVATION_THRESHOLD and compute_culture_delta are
reused unchanged from src.domains.culture.applicator (WORLD-CULT-002/003
stay untouched).

MUST NOT import from src.engine, src.core.state, or
src.domains.campaigns.orchestrator — matches CultureState's own module-doc
constraint (src/domains/culture/model.py:8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from src.domains.culture.applicator import (
    CULTURE_ACTIVATION_THRESHOLD,
    CulturalBiasApplicator,
)

if TYPE_CHECKING:
    from src.domains.culture.model import CultureState

# The full union of tags CulturalBiasApplicator's axis rules key off of
# (src/domains/culture/applicator.py:31-36) — reusing this set (not inventing
# a new one) keeps this service's output traceable 1:1 to already-verified
# axis→tag rules.
CANONICAL_TAGS: Tuple[str, ...] = (
    "caution", "recovery", "flee", "pride", "combat",
    "aggressive", "loyalty", "party", "survival",
)

_AXIS_TRAIT_NAMES: Dict[str, str] = {
    "fatalism": "fatalistic",
    "hero_veneration": "hero_venerating",
    "resource_scarcity_memory": "scarcity_scarred",
    "faction_conflict_exposure": "conflict_hardened",
}


@dataclass(frozen=True, slots=True)
class SettlementPersonalityDescriptor:
    """Shaped, named settlement-personality signal derived from a CultureState.

    Never bare None — the "no culture data" case is represented by a neutral
    descriptor (empty traits, all-zero tag_deltas), not a null value, so
    callers never need a null-check branch.
    """

    traits: Tuple[str, ...] = ()
    tag_deltas: Dict[str, float] = field(default_factory=dict)

    @property
    def is_neutral(self) -> bool:
        return not self.traits


class SettlementPersonalityService:
    """Pure translation from CultureState to a named personality signal."""

    @staticmethod
    def describe(culture: Optional["CultureState"]) -> SettlementPersonalityDescriptor:
        """Return the settlement-personality signal for a region's culture.

        Parameters
        ----------
        culture:
            Regional CultureState snapshot, or None if no culture data has
            been derived for the region yet (the default for every one of
            the 21 corpus worlds today).

        Returns
        -------
        SettlementPersonalityDescriptor
            Always a descriptor object, never None. `culture=None` and an
            all-default CultureState() both produce the neutral descriptor
            (traits=(), all-0.0 tag_deltas), since compute_culture_delta
            already returns 0.0 when every axis is <= CULTURE_ACTIVATION_THRESHOLD.
        """
        if culture is None:
            return SettlementPersonalityDescriptor()

        traits = tuple(
            trait_name
            for axis_name, trait_name in _AXIS_TRAIT_NAMES.items()
            if getattr(culture, axis_name) > CULTURE_ACTIVATION_THRESHOLD
        )
        tag_deltas = {
            tag: CulturalBiasApplicator.compute_culture_delta(culture, [tag])
            for tag in CANONICAL_TAGS
        }
        return SettlementPersonalityDescriptor(traits=traits, tag_deltas=tag_deltas)
