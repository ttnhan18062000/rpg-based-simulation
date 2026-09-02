import pytest

from src.core.builder import V2EntityBuilder
from src.core.classes import CLASS_TIER_REGISTRY
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.apply import ApplyPath


def make_warrior_entity(entity_id: int, *, class_id: str = "WARRIOR"):
    """
    Build a WARRIOR-classed hero with default (unbonused) attributes, matching
    tests/unit/core/test_class_registry.py::make_class_entity's explicit-setup style.
    """
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
            class_id=class_id,
        )
        .combat(
            hp=150,
            max_hp=150,
            atk=15,
            def_stat=10,
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .build()
    )


def test_class_tier_registry_has_branching_options():
    """
    Verify CLASS_TIER_REGISTRY defines >=2 mutually-exclusive next-tier options
    per base class, not a single linear chain like EvolutionSystem._get_evolved_kind.

    Fraud this catches:
        - registry collapses to a single hardcoded destination per base class
        - two tier options accidentally share the same tier_id
    """
    assert len(CLASS_TIER_REGISTRY["WARRIOR"]) >= 2
    assert len(CLASS_TIER_REGISTRY["MAGE"]) >= 2

    all_tier_ids = [opt.tier_id for options in CLASS_TIER_REGISTRY.values() for opt in options]
    assert len(all_tier_ids) == len(set(all_tier_ids))

    for base_class, options in CLASS_TIER_REGISTRY.items():
        assert len(options) >= 2, f"{base_class} must offer >=2 mutually-exclusive tier options"


def test_class_id_set_applies_via_identity_patch():
    """
    Verify IdentityUpdate.class_id_set authoritatively mutates class_id via the
    real apply path, mirroring test_goblin_evolution's kind_set apply-path pattern.

    Fraud this catches:
        - class_id_set is accepted by IdentityUpdate but never reaches IdentityPatch.apply()
        - is_noop()/merge() omit the new field, silently breaking update merging
    """
    assert IdentityUpdate(class_id_set=None).is_noop() is True
    assert IdentityUpdate(class_id_set="WARRIOR_CHAMPION").is_noop() is False

    base = IdentityUpdate(class_id_set="WARRIOR_CHAMPION")
    merged = base.merge(IdentityUpdate(class_id_set="WARRIOR_GUARDIAN"))
    assert merged.class_id_set == "WARRIOR_GUARDIAN"

    entity = make_warrior_entity(1)
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                identity=IdentityUpdate(class_id_set="WARRIOR_CHAMPION"),
            )
        }
    )

    new_state = ApplyPath.apply_generation(state, state_upd)
    new_entity = new_state.entities[1]

    assert new_entity.identity.class_id == "WARRIOR_CHAMPION"


def test_branch_selection_diverges_class_id():
    """
    Verify two entities with identical starting class/attributes but different
    branch-selection inputs diverge in class_id and combat stats, mirroring
    test_goblin_evolution's "identical starting state, diverging input" pattern.

    Fraud this catches:
        - both branch choices silently resolve to the same class_id
        - tier attribute_bonuses are not observable in derived combat stats
    """
    entity_a = make_warrior_entity(1)
    entity_b = make_warrior_entity(2)
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity_a, 2: entity_b})

    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, identity=IdentityUpdate(class_id_set="WARRIOR_CHAMPION")),
            2: EntityUpdate(entity_id=2, identity=IdentityUpdate(class_id_set="WARRIOR_GUARDIAN")),
        }
    )

    new_state = ApplyPath.apply_generation(state, state_upd)
    champion = new_state.entities[1]
    guardian = new_state.entities[2]

    assert champion.identity.class_id == "WARRIOR_CHAMPION"
    assert guardian.identity.class_id == "WARRIOR_GUARDIAN"
    assert champion.identity.class_id != guardian.identity.class_id
    assert champion.identity.class_id != "WARRIOR"
    assert guardian.identity.class_id != "WARRIOR"

    # WARRIOR_CHAMPION is offense-leaning (strength/vitality); WARRIOR_GUARDIAN is
    # defense-leaning (vitality/endurance) - the derived stats must reflect that split.
    assert champion.combat.atk > guardian.combat.atk
    assert guardian.combat.max_hp > champion.combat.max_hp


def test_tier_bonus_survives_subsequent_stats_dirty_event():
    """
    Verify a tier's attribute-derived combat bonus is not silently wiped by the
    next unrelated stats_dirty recompute (regression guard for the pre-existing
    get_effective_stats() base-stat-sourcing gap - see plan.md Anti-Drift Notes).

    Fraud this catches:
        - tier bonuses implemented as one-time CombatUpdate deltas that get
          overwritten by the next stats_dirty event instead of being re-derived
          live from the durable class_id every time
    """
    entity = make_warrior_entity(1)
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    branch_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, identity=IdentityUpdate(class_id_set="WARRIOR_CHAMPION")),
        }
    )
    state_after_branch = ApplyPath.apply_generation(state, branch_upd)
    branched_entity = state_after_branch.entities[1]
    bonused_atk = branched_entity.combat.atk
    bonused_max_hp = branched_entity.combat.max_hp

    unrelated_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, identity=IdentityUpdate(learned_skills=["power_strike"])),
        }
    )
    state_after_unrelated = ApplyPath.apply_generation(state_after_branch, unrelated_upd)
    final_entity = state_after_unrelated.entities[1]

    assert final_entity.identity.class_id == "WARRIOR_CHAMPION"
    assert final_entity.combat.atk == bonused_atk
    assert final_entity.combat.max_hp == bonused_max_hp
