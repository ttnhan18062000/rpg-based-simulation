"""Coming of Age archetype-choice roll (idea 34, TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE).

Computes a genuinely weighted (not fixed-priority) distribution over the civilian occupation
roles {SHOPKEEPER, WORKER, GUARD} and draws from it via the seeded DeterministicRNG service.
This is the mirror-opposite design choice from OccupationChangeGoalScorer
(src/ai/goals/occupation_change_scorer.py), which is a fixed-priority first-fit selector with
zero variance by construction -- reusing that pattern here would collapse every same-tick,
same-region child to the identical occupation, which is the exact convergence bug this
mechanism's metamorphic test (tests/unit/strategic/test_coming_of_age_archetype_choice.py)
exists to prevent. See staging_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/plan.md
Decisions 1-5 for the full design rationale.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from src.core.enums import Domain, EntityRole
from src.platform.rng import DeterministicRNG

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, PersonalityComponent

# Independent tuple literal -- deliberately not imported from
# OccupationChangeGoalScorer._CANDIDATE_ROLES (src/ai/goals/occupation_change_scorer.py), since
# that name is underscore-prefixed/module-private by convention. Must be kept in sync by hand if
# that scorer's own candidate set ever changes.
_CANDIDATE_ROLES: Tuple[int, ...] = (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)

# role -> PersonalityComponent field, mirroring PersonalityService.get_goal_modifiers()'s own
# greed->"trade" / industry->"harvesting"/"crafting" / bravery->"combat" mappings
# (src/ai/personality.py), applied here to a categorical draw instead of goal utility.
_PERSONALITY_ATTR = {
    EntityRole.SHOPKEEPER: "greed",
    EntityRole.WORKER: "industry",
    EntityRole.GUARD: "bravery",
}

BASE_WEIGHT = 1.0
PERSONALITY_COEFF = 1.0
PARENTAL_COEFF = 1.0
DEFAULT_REGIONAL_COEFF = 1.0
# Guarantees every role keeps strictly nonzero draw probability regardless of how skewed the
# other three terms get -- a structural never-fully-collapses guard supporting AC3.
WEIGHT_FLOOR = 0.05


def _personality_weight(role: int, personality: "PersonalityComponent") -> float:
    return getattr(personality, _PERSONALITY_ATTR[role])


def _parental_weight(role: int, entity: "EntityState", state: "AuthoritativeState") -> float:
    """Count how many of the entity's resolvable, active parents currently hold this role.

    Missing (None id), dead-and-removed (state.entities.get() is None), or deactivated
    (lifecycle.active is False) parents contribute nothing -- a flat, role-neutral 0.0, never a
    crash and never a fallback favoring any single role.
    """
    total = 0.0
    for parent_id in (entity.lifecycle.parent_a_entity_id, entity.lifecycle.parent_b_entity_id):
        if parent_id is None:
            continue
        parent = state.entities.get(parent_id)
        if parent is None or not parent.lifecycle.active:
            continue
        if parent.identity.role == role:
            total += 1.0
    return total


def _regional_need_weight(role: int, entity: "EntityState", state: "AuthoritativeState") -> float:
    """Read-only reuse of OccupationChangeGoalScorer's own region/tally logic as the
    regional-need INPUT signal, not a duplicate of its selection behavior."""
    from src.engine.legality import LegalityServiceV2
    from src.world.occupation_config import BASE_OCCUPATION_DENSITY, MIN_OCCUPATION_SLOTS

    region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
    if region is None:
        return 0.0

    live_count = 0
    for other in state.entities.values():
        if not other.combat.alive or other.identity.role != role:
            continue
        other_region = LegalityServiceV2.get_region_for_position(other.navigation.position, state)
        if other_region is not None and other_region.id == region.id:
            live_count += 1

    xmin, ymin, xmax, ymax = region.bounds
    area = (xmax - xmin) * (ymax - ymin)
    target_count = max(MIN_OCCUPATION_SLOTS, int((area / 10000.0) * BASE_OCCUPATION_DENSITY[role]))
    return max(0.0, float(target_count - live_count))


def compute_role_weights(
    entity: "EntityState",
    state: "AuthoritativeState",
    *,
    personality_coeff: float = PERSONALITY_COEFF,
    parental_coeff: float = PARENTAL_COEFF,
    regional_coeff: float = DEFAULT_REGIONAL_COEFF,
) -> List[float]:
    """Pure (no RNG) weight vector over _CANDIDATE_ROLES. Coefficients are exposed as keyword
    overrides so the metamorphic test can sweep regional_coeff independently while holding
    personality_coeff/parental_coeff fixed."""
    personality = entity.identity.personality
    weights: List[float] = []
    for role in _CANDIDATE_ROLES:
        weight = (
            BASE_WEIGHT
            + personality_coeff * _personality_weight(role, personality)
            + parental_coeff * _parental_weight(role, entity, state)
            + regional_coeff * _regional_need_weight(role, entity, state)
        )
        weights.append(max(WEIGHT_FLOOR, weight))
    return weights


def is_excluded_no_birth_record(entity: "EntityState") -> bool:
    """True only when birth_tick, parent_a_entity_id, and parent_b_entity_id are all still at
    their construction defaults simultaneously -- a compound check, not birth_tick==0 alone.

    birth_tick==0 alone is unsafe: HumanoidReproductionService.process_reproduction() has no
    explicit tick>0 guard, so a real Humanoid-path child can be born at tick 0 with non-None
    parent ids (two same-kind adults near each other at world genesis). This compound check
    correctly treats that case as "has a birth record" (parent ids are non-None), while excluding
    a hypothetical construction-default CHILD with no .birth_record() call at all.

    Forward-compatibility caveat: this is not provably safe against a hypothetical future
    reproduction path with neither an accumulation gate nor tracked parent ids. No such path
    exists in the live codebase today -- both current CHILD-construction call sites
    (spawn_natural_creature_offspring, spawn_humanoid_offspring in
    src/systems/world_systems/generator.py) unconditionally chain into .birth_record(...).
    """
    return (
        entity.lifecycle.birth_tick == 0
        and entity.lifecycle.parent_a_entity_id is None
        and entity.lifecycle.parent_b_entity_id is None
    )


def choose_archetype(entity: "EntityState", state: "AuthoritativeState") -> int:
    """Seeded, order-independent weighted draw over _CANDIDATE_ROLES. Never Python's unseeded
    random module -- keyed by (Domain.STRATEGIC, state.tick, entity.id) so a re-run with
    identical state/seed reproduces byte-identical role_set outcomes regardless of
    state.entities dict iteration order."""
    rng = DeterministicRNG(state.seed)
    weights = compute_role_weights(entity, state)
    result = rng.weighted_choice(
        Domain.STRATEGIC, state.tick, entity.id, list(_CANDIDATE_ROLES), weights
    )
    return int(result)
