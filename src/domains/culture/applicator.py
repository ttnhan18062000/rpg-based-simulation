"""
src/domains/culture/applicator.py
───────────────────────────────────────────────────────────────────────────────
CulturalBiasApplicator — translates a CultureState into an additive tag-level
bias delta layered onto AdventureRouteScorer.score()'s personality_bias (E62C,
re-wired by TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE — the original
MotivationBiasService this docstring referred to was confirmed dead and deleted,
TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT).

The overlay is transient (per scoring call) and never stored in durable state.
It does not modify MotivationModel on the entity.

Axis → tag → delta rules:
  fatalism > THRESHOLD         → +fatalism*0.4 for {caution, recovery, flee}
                               → -fatalism*0.3 for {pride, combat, aggressive}
  hero_veneration > THRESHOLD  → +hero_veneration*0.4 for {loyalty, party, combat}
  resource_scarcity_memory > THRESHOLD → +scarcity*0.4 for {survival, recovery, caution}
  faction_conflict_exposure > THRESHOLD → +conflict*0.3 for {caution}
                               → -conflict*0.2 for {loyalty}

Final delta is bounded: max(-0.5, min(1.0, delta))
CULTURE_ACTIVATION_THRESHOLD = 0.3 — axes below this produce no effect.
"""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domains.culture.model import CultureState

CULTURE_ACTIVATION_THRESHOLD: float = 0.3

_FATALISM_POSITIVE = frozenset({"caution", "recovery", "flee"})
_FATALISM_NEGATIVE = frozenset({"pride", "combat", "aggressive"})
_HERO_POSITIVE = frozenset({"loyalty", "party", "combat"})
_SCARCITY_POSITIVE = frozenset({"survival", "recovery", "caution"})
_CONFLICT_POSITIVE = frozenset({"caution"})
_CONFLICT_NEGATIVE = frozenset({"loyalty"})


class CulturalBiasApplicator:
    """Compute additive culture delta for a given set of route tags.

    Stateless — all logic in compute_culture_delta().
    """

    @staticmethod
    def compute_culture_delta(
        culture: "CultureState",
        tags: Iterable[str],
    ) -> float:
        """Return additive delta to add to AdventureRouteScorer.score()'s personality_bias.

        Parameters
        ----------
        culture:
            Regional CultureState snapshot.
        tags:
            Route tags being scored (e.g. ["caution", "recovery"]).

        Returns
        -------
        float
            Bounded additive delta in [-0.5, 1.0]. Zero when all axes are 0.0
            or no relevant tags are present.
        """
        tags_set = set(tags)
        delta = 0.0

        if culture.fatalism > CULTURE_ACTIVATION_THRESHOLD:
            f = culture.fatalism
            for tag in tags_set & _FATALISM_POSITIVE:
                delta += f * 0.4
            for tag in tags_set & _FATALISM_NEGATIVE:
                delta -= f * 0.3

        if culture.hero_veneration > CULTURE_ACTIVATION_THRESHOLD:
            h = culture.hero_veneration
            for tag in tags_set & _HERO_POSITIVE:
                delta += h * 0.4

        if culture.resource_scarcity_memory > CULTURE_ACTIVATION_THRESHOLD:
            s = culture.resource_scarcity_memory
            for tag in tags_set & _SCARCITY_POSITIVE:
                delta += s * 0.4

        if culture.faction_conflict_exposure > CULTURE_ACTIVATION_THRESHOLD:
            c = culture.faction_conflict_exposure
            for tag in tags_set & _CONFLICT_POSITIVE:
                delta += c * 0.3
            for tag in tags_set & _CONFLICT_NEGATIVE:
                delta -= c * 0.2

        return max(-0.5, min(1.0, delta))
