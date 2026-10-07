"""
Per-kind biological need rates (SURV-05, owner decision row 22).

What a body requires comes from what kind of body it is. A subject's hunger and sleep-debt
accumulation follow its kind's declared need profile (``data/content/living/need_profiles.yaml``):
a kind whose profile declares ``hunger: none`` never becomes hungry, and kinds whose profiles
differ build their needs at different rates. The base rates are the constants
``ApplyPath`` used to apply to every subject (hunger 0.1, sleep debt 0.05 per biological tick), so
a ``medium`` need reproduces the old behavior exactly.

Source of the profile, most specific first:
1. ``identity.properties["need_profile_id"]`` (an explicitly assigned profile).
2. The subject's species' catalog ``need_profile`` (``identity.properties["species_id"]``).
3. The ordinary person's profile (``humanoid_survival``) when the subject is a person (a civil
   role).
4. Otherwise the subject has no declared kind: a content defect to report (SURV-05), never a
   guess. Its accumulation is left at the base rates (unchanged behavior), and it is listed by
   :func:`undeclared_need_kinds` for the assembly integrity check.

This module only reads. Rates are derived, not stored, so no durable state is added.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.core.enums import EntityRole
from src.engine import behavior_consumers

BASE_HUNGER_RATE = 0.1
BASE_SLEEP_DEBT_RATE = 0.05

# Qualitative need level -> multiple of the base rate. ``medium`` is the pre-SURV-05 constant.
NEED_LEVEL_RATE_SCALE: Dict[str, float] = {"none": 0.0, "low": 0.5, "medium": 1.0, "high": 1.5}

PERSON_FALLBACK_PROFILE_ID = "humanoid_survival"
_PERSON_ROLES = frozenset({
    int(EntityRole.HERO), int(EntityRole.SHOPKEEPER), int(EntityRole.CITIZEN),
    int(EntityRole.WORKER), int(EntityRole.GUARD),
})

# (need_profile_id, species_id, role) -> (hunger_rate, sleep_debt_rate)
_RATES_CACHE: Dict[Tuple[Optional[str], Optional[str], int], Tuple[float, float]] = {}
_CACHE_CATALOG_ID: Optional[int] = None

_BASE_RATES = (BASE_HUNGER_RATE, BASE_SLEEP_DEBT_RATE)


def _catalog() -> Any:
    if behavior_consumers._catalog is None:
        behavior_consumers._auto_init()
    return behavior_consumers._catalog


def profile_id_for(props: Dict[str, Any], role: int, catalog: Any) -> Optional[str]:
    """The need profile id that governs a subject, or None when it has no declared kind."""
    explicit = props.get("need_profile_id")
    if explicit:
        return str(explicit)
    species_id = props.get("species_id")
    if species_id:
        species = catalog.get_species(species_id)
        if species is not None and species.need_profile:
            return str(species.need_profile)
        return None
    return PERSON_FALLBACK_PROFILE_ID if int(role) in _PERSON_ROLES else None


def _rate(needs: Dict[str, str], key: str, base: float) -> float:
    return base * NEED_LEVEL_RATE_SCALE.get(needs.get(key, "none"), 1.0)


def need_rates(entity: Any) -> Tuple[float, float]:
    """(hunger_rate, sleep_debt_rate) per biological tick for this subject."""
    global _CACHE_CATALOG_ID
    catalog = _catalog()
    if _CACHE_CATALOG_ID != id(catalog):
        _RATES_CACHE.clear()
        _CACHE_CATALOG_ID = id(catalog)
    ident = entity.identity
    props = ident.properties or {}
    key = (props.get("need_profile_id"), props.get("species_id"), int(ident.role))
    rates = _RATES_CACHE.get(key)
    if rates is None:
        profile_id = profile_id_for(props, ident.role, catalog)
        profile = catalog.get_need_profile(profile_id) if profile_id else None
        if profile is None:
            rates = _BASE_RATES
        else:
            rates = (_rate(profile.needs, "hunger", BASE_HUNGER_RATE),
                     _rate(profile.needs, "sleep", BASE_SLEEP_DEBT_RATE))
        _RATES_CACHE[key] = rates
    return rates


def undeclared_need_kinds(state: Any, catalog: Any) -> Dict[Tuple[Optional[str], int], int]:
    """Subjects with no declared kind (SURV-05 content defects), counted per (species_id, role)."""
    out: Dict[Tuple[Optional[str], int], int] = {}
    for entity in state.entities.values():
        props = entity.identity.properties or {}
        profile_id = profile_id_for(props, entity.identity.role, catalog)
        if profile_id is None or catalog.get_need_profile(profile_id) is None:
            key = (props.get("species_id"), int(entity.identity.role))
            out[key] = out.get(key, 0) + 1
    return out
