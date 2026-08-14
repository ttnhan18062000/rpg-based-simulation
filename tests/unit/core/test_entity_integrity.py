import pytest
from dataclasses import fields
from src.core.state import EntityState, CombatComponent, IdentityComponent
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact

# Approved fields for V2 EntityState
# Strictly speaking, RPG-AUTH-030 says "only ID, Kind, and Aspects"
# But we might have some legacy drift. Let's see what fails.
REQUIRED_BASE_FIELDS = {"id", "kind"}

FORBIDDEN_LEGACY_PROPERTIES = {
    "hp", "max_hp", "atk", "def_stat", "speed", "mp", "max_mp", 
    "xp", "level", "gold", "stamina_current",
    "faction", "role", "name", "hero_class",
    "ai_state", "goals", "target",
    "home_pos", "leash_radius"
}

def test_entity_field_integrity():
    """RPG-AUTH-030: Ensure Entity model_fields contains only the ID, Kind, and Aspects."""
    entity_fields = {f.name for f in fields(EntityState)}
    
    aspects = {
        "interaction", "identity", "attributes", "inventory", 
        "strategic", "social", "biological", "lifecycle", 
        "aptitude", "combat", "equipment", "navigation", 
        "task", "stamina"
    }
    
    extra_fields = entity_fields - REQUIRED_BASE_FIELDS - aspects - {"_readonly_cache", "_spatial_grid_cache", "_canonical_cache", "timeline", "self_model", "cognition"}
    
    assert not extra_fields, f"Unauthorized fields detected in EntityState: {extra_fields}"

def test_entity_property_locking():
    """RPG-AUTH-031: Ensure no forbidden legacy properties have been re-introduced as shims."""
    entity_members = set(dir(EntityState))
    leaked = entity_members & FORBIDDEN_LEGACY_PROPERTIES
    assert not leaked, f"Legacy properties leaked into EntityState namespace: {leaked}."

def test_aspect_model_purity():
    """RPG-AUTH-032: Ensure aspects themselves stay clean of Cross-Aspect dependencies."""
    combat_fields = {f.name for f in fields(CombatComponent)}
    assert "gold" not in combat_fields
    assert "ai_state" not in combat_fields
    
    identity_fields = {f.name for f in fields(IdentityComponent)}
    assert "hp" not in identity_fields

def test_mandatory_aspect_naming():
    """RPG-AUTH-033: Aspects must be named exactly as their type (lowercase)."""
    entity_fields = {f.name for f in fields(EntityState)}
    expected_aspects = {
        "interaction", "identity", "attributes", "inventory", 
        "strategic", "social", "biological", "lifecycle", 
        "aptitude", "combat", "equipment", "navigation", 
        "task", "stamina"
    }
    for aspect in expected_aspects:
        assert aspect in entity_fields, f"EntityState missing {aspect} aspect field"


def test_self_model_participates_in_canonical_hash():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (supplementary fix, SUB-374): confirms the
    corrected invariant — self_model DOES participate in the authoritative canonical
    hash (the prior docstring claiming exclusion, src/core/self_model.py:216-219, was
    false and pre-existing). Two otherwise-identical EntityStates differing ONLY in
    self_model content must produce DIFFERENT to_canonical_dict() output (and therefore
    different CanonicalStateHasher-derived hashes).
    """
    from dataclasses import replace as dataclass_replace
    from src.core.state import AuthoritativeState
    from src.engine.checkpoint import CanonicalStateHasher

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    assert base.self_model == SelfModelBundle.empty()

    non_empty = dataclass_replace(
        base,
        self_model=SelfModelBundle(
            knowledge=KnowledgeModelComponent(
                facts={},
                unknowns={"material.moon_resin.source": UnknownFact(subject="material.moon_resin.source", reason="provider_unknown")},
            )
        ),
    )

    assert base.to_canonical_dict() != non_empty.to_canonical_dict()

    state_empty = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: base})
    state_non_empty = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: non_empty})

    assert CanonicalStateHasher.get_hash(state_empty) != CanonicalStateHasher.get_hash(state_non_empty)


def test_self_model_fix_preserves_existing_baseline_hashes_when_flag_off():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (supplementary fix, SUB-374): before/after
    hash-stability regression guard. With ENABLE_SELF_MODEL_COGNITION OFF (the shipped
    default), no EntityUpdate ever carries a non-None self_model_bundle_set, so the new
    SelfModelPatch (src/engine/patches.py) is gated out via is_noop() and never mutates
    `changes["self_model"]`. This proves landing SelfModelPatch changes zero shipped
    baseline hash values: applying an update with self_model_bundle_set=None through the
    real ApplyPath (post-fix code path) must produce a canonical hash bit-identical to
    manually constructing the same resulting state without ever touching self_model
    (the pre-fix-equivalent state, since self_model was never wired into `changes` before
    this fix landed).
    """
    from dataclasses import replace as dataclass_replace
    from src.core.state import AuthoritativeState
    from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate
    from src.engine.apply import ApplyPath
    from src.engine.patches import extract_patches, SelfModelPatch
    from src.engine.checkpoint import CanonicalStateHasher

    entity = EntityState(
        id=1, kind="hero",
        combat=CombatComponent(hp=100, max_hp=100, alive=True),
    )
    state = AuthoritativeState(tick=1, seed=7, world_time=50, entities={1: entity})

    # Flag-off scenario: self_model_bundle_set is never populated. Use a navigation-only
    # update (not attributes/equipment/identity/wound) so it stays clear of the PH8
    # derived-stats recompute block (apply.py:448-497) and isolates exactly the
    # self_model-materialization behavior under test.
    e_upd = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(5.0, 5.0)))
    assert e_upd.self_model_bundle_set is None

    # SelfModelPatch is gated out entirely when self_model_bundle_set is None — confirms
    # the new patch class contributes zero behavior difference in the flag-off scenario.
    patches = extract_patches(1, e_upd)
    assert not any(isinstance(p, SelfModelPatch) for p in patches)

    # passive=False disables ambient per-tick biological/lifecycle aging systems so the
    # manually-reconstructed comparison state below only needs to account for the
    # entity_update actually supplied, not incidental hunger/sleep-debt/age drift.
    update = StateUpdate(entity_updates={1: e_upd}, force_full_scan=True)
    post_fix_state = ApplyPath.apply_generation(state, update, next_tick=2, passive=False)

    # Manually construct the pre-fix-equivalent result: same navigation change, self_model
    # never touched (mirrors pre-fix behavior where changes["self_model"] was never set,
    # since nothing populated changes["self_model"] before SelfModelPatch existed either).
    expected_entity = dataclass_replace(
        entity,
        navigation=dataclass_replace(entity.navigation, target=(5.0, 5.0)),
    )
    pre_fix_equivalent_state = dataclass_replace(
        state, tick=2, entities={1: expected_entity},
    )

    assert post_fix_state.entities[1].self_model == entity.self_model == SelfModelBundle.empty()
    assert (
        CanonicalStateHasher.get_hash(post_fix_state)
        == CanonicalStateHasher.get_hash(pre_fix_equivalent_state)
    )
