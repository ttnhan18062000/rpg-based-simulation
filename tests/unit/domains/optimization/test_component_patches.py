# Compliance IDs: PERF-015
import pytest
from unittest.mock import MagicMock
from src.core.updates import EntityUpdate, CombatUpdate, NavigationUpdate, AttributeUpdate, IdentityUpdate, WoundUpdate, StatusEffectUpdate, InteractionUpdate
from src.core.state import EntityState, CombatComponent, NavigationComponent, AttributeComponent, IdentityComponent, LifeStage, StatusEffectState, InteractionComponent
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.engine.patches import (
    extract_patches, CombatPatch, NavigationPatch, AttributePatch, IdentityPatch, WoundPatch, KindPatch,
    SelfModelPatch, StatusEffectPatch, InteractionPatch
)

def test_patch_noop_detection():
    # Test KindPatch
    kp_noop = KindPatch(entity_id=1, kind_set=None)
    assert kp_noop.is_noop() is True
    kp_active = KindPatch(entity_id=1, kind_set="Goblin")
    assert kp_active.is_noop() is False

    # Test CombatPatch
    cp_noop = CombatPatch(entity_id=1, combat=None, readiness_delta=0.0)
    assert cp_noop.is_noop() is True
    cp_active = CombatPatch(entity_id=1, combat=CombatUpdate(hp_delta=-10), readiness_delta=0.0)
    assert cp_active.is_noop() is False

def test_patch_merging():
    cp1 = CombatPatch(entity_id=1, combat=CombatUpdate(hp_delta=-10, atk_delta=2), readiness_delta=10.0)
    cp2 = CombatPatch(entity_id=1, combat=CombatUpdate(hp_delta=-5, def_delta=1), readiness_delta=-5.0)
    
    merged = cp1.merge(cp2)
    assert merged.combat.hp_delta == -15
    assert merged.combat.atk_delta == 2
    assert merged.combat.def_delta == 1
    assert merged.readiness_delta == 5.0

def test_order_sensitivity():
    # Verify extract_patches maintains correct dependency order
    update = EntityUpdate(
        entity_id=1,
        kind_set="Orc",
        attributes=AttributeUpdate(strength_delta=5),
        combat=CombatUpdate(hp_delta=-15),
        identity=IdentityUpdate(role_set="Warrior")
    )
    patches = extract_patches(1, update)
    patch_types = [type(p) for p in patches]
    
    # Kind and Identity must come before Combat and Attributes
    assert KindPatch in patch_types
    assert IdentityPatch in patch_types
    assert CombatPatch in patch_types
    assert AttributePatch in patch_types
    
    kind_idx = patch_types.index(KindPatch)
    id_idx = patch_types.index(IdentityPatch)
    com_idx = patch_types.index(CombatPatch)
    att_idx = patch_types.index(AttributePatch)
    
    # Kind and Identity precede Combat
    assert kind_idx < com_idx
    assert id_idx < com_idx


# ─────────────────────────────────────────────────────────────────────────────
# SelfModelPatch (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B supplementary fix)
# ─────────────────────────────────────────────────────────────────────────────

def test_identity_patch_apply_sets_life_stage():
    """TCK-20260824-LIFE-STAGE-TRANSITIONS: life_stage_set must reach IdentityComponent.life_stage
    through IdentityPatch.apply()'s replace() branch -- not silently dropped as new_id.life_stage
    (the OLD value) would be if that call omitted the life_stage kwarg. property_updates={} and
    intent_results=[] left empty makes the _fast_replace_identity guard condition trivially false
    regardless, so this test is unambiguous about which apply() branch actually ran."""
    entity = EntityState(id=1, kind="HERO", identity=IdentityComponent(life_stage=LifeStage.ADULT))
    identity_patch = IdentityPatch(entity_id=1, identity=IdentityUpdate(life_stage_set=LifeStage.ELDER))

    changes = {}
    identity_patch.apply(entity, changes)

    assert changes["identity"].life_stage == LifeStage.ELDER


def test_attribute_patch_apply_clamps_to_documented_range():
    """TCK-20260902-ATTRIBUTE-CLAMP-WIRING-GAP: AttributePatch.apply must clamp to the documented
    [1, ATTRIBUTE_CAP=99] range via enforce_attribute_caps -- not the old ad hoc 100-only-upper-bound
    logic that had no lower bound at all. Proves the fix is reachable through the real apply() path,
    not just enforce_attribute_caps() called in isolation (already covered separately)."""
    entity = EntityState(id=1, kind="HERO", attributes=AttributeComponent(strength=95, agility=3))
    patch = AttributePatch(entity_id=1, attributes=AttributeUpdate(strength_delta=20, agility_delta=-10))

    changes = {}
    patch.apply(entity, changes)

    # Too-high case: 95 + 20 = 115 -> must clamp to 99 (documented ATTRIBUTE_CAP), not the old buggy 100
    assert changes["attributes"].strength == 99
    # Negative case: 3 + (-10) = -7 -> must clamp to 1 (the old code applied no floor at all)
    assert changes["attributes"].agility == 1


def test_attribute_patch_apply_within_range_unaffected():
    """Deltas that stay within [1, 99] must pass through unchanged -- the clamp fix must not
    perturb the normal, in-range case."""
    entity = EntityState(id=1, kind="HERO", attributes=AttributeComponent(strength=10, agility=10))
    patch = AttributePatch(entity_id=1, attributes=AttributeUpdate(strength_delta=5, agility_delta=-3))

    changes = {}
    patch.apply(entity, changes)

    assert changes["attributes"].strength == 15
    assert changes["attributes"].agility == 7


def test_self_model_patch_noop_detection():
    smp_noop = SelfModelPatch(entity_id=1, self_model_bundle_set=None)
    assert smp_noop.is_noop() is True

    bundle = SelfModelBundle(knowledge=KnowledgeModelComponent(
        unknowns={"coal_ore": UnknownFact(subject="coal_ore", reason="need_material")}
    ))
    smp_active = SelfModelPatch(entity_id=1, self_model_bundle_set=bundle)
    assert smp_active.is_noop() is False


def test_self_model_patch_merge_prefers_other():
    bundle_a = SelfModelBundle(knowledge=KnowledgeModelComponent(
        unknowns={"coal_ore": UnknownFact(subject="coal_ore", reason="need_material")}
    ))
    bundle_b = SelfModelBundle(knowledge=KnowledgeModelComponent(
        unknowns={"iron_ore": UnknownFact(subject="iron_ore", reason="need_material")}
    ))

    smp1 = SelfModelPatch(entity_id=1, self_model_bundle_set=bundle_a)
    smp2 = SelfModelPatch(entity_id=1, self_model_bundle_set=bundle_b)

    merged = smp1.merge(smp2)
    assert merged.self_model_bundle_set is bundle_b  # last-write-wins

    # other.is_noop() (None) -> self's bundle preserved
    smp_noop_other = SelfModelPatch(entity_id=1, self_model_bundle_set=None)
    merged_preserve = smp1.merge(smp_noop_other)
    assert merged_preserve.self_model_bundle_set is bundle_a


def test_self_model_patch_apply_sets_changes_key():
    entity = EntityState(id=1, kind="hero")
    bundle = SelfModelBundle(knowledge=KnowledgeModelComponent(
        unknowns={"coal_ore": UnknownFact(subject="coal_ore", reason="need_material")}
    ))
    smp = SelfModelPatch(entity_id=1, self_model_bundle_set=bundle)

    changes = {}
    smp.apply(entity, changes)
    assert changes["self_model"] is bundle  # identity, not just equality


def test_self_model_patch_apply_noop_leaves_changes_untouched():
    entity = EntityState(id=1, kind="hero")
    smp = SelfModelPatch(entity_id=1, self_model_bundle_set=None)

    changes = {}
    smp.apply(entity, changes)
    assert "self_model" not in changes


def test_extract_patches_includes_self_model_patch():
    bundle = SelfModelBundle(knowledge=KnowledgeModelComponent(
        unknowns={"coal_ore": UnknownFact(subject="coal_ore", reason="need_material")}
    ))
    update = EntityUpdate(
        entity_id=1,
        kind_set="Orc",
        attributes=AttributeUpdate(strength_delta=5),
        combat=CombatUpdate(hp_delta=-15),
        identity=IdentityUpdate(role_set="Warrior"),
        self_model_bundle_set=bundle,
    )
    patches = extract_patches(1, update)
    patch_types = [type(p) for p in patches]

    assert SelfModelPatch in patch_types
    smp = next(p for p in patches if isinstance(p, SelfModelPatch))
    assert smp.self_model_bundle_set is bundle


def test_extract_patches_omits_self_model_patch_when_unset():
    update = EntityUpdate(entity_id=1, kind_set="Orc")
    patches = extract_patches(1, update)
    assert not any(isinstance(p, SelfModelPatch) for p in patches)


# ─────────────────────────────────────────────────────────────────────────────
# StatusEffectPatch / InteractionPatch.kind (TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION)
# ─────────────────────────────────────────────────────────────────────────────

def test_status_effect_patch_noop_detection():
    sep_noop = StatusEffectPatch(entity_id=1, status_effect_update=None)
    assert sep_noop.is_noop() is True
    sep_active = StatusEffectPatch(entity_id=1, status_effect_update=StatusEffectUpdate(
        effects_add=[StatusEffectState(kind="frozen")]
    ))
    assert sep_active.is_noop() is False


def test_status_effect_patch_apply_adds_effect():
    entity = EntityState(id=1, kind="hero")
    patch = StatusEffectPatch(entity_id=1, status_effect_update=StatusEffectUpdate(
        effects_add=[StatusEffectState(kind="frozen", source="test_fixture", magnitude=1.0, expires_tick=50)]
    ))

    changes = {}
    patch.apply(entity, changes)

    assert [s.kind for s in changes["combat"].status_effects] == ["frozen"]


def test_status_effect_patch_apply_removes_effect_by_kind():
    entity = EntityState(id=1, kind="hero", combat=CombatComponent(
        status_effects=[StatusEffectState(kind="frozen"), StatusEffectState(kind="stunned")]
    ))
    patch = StatusEffectPatch(entity_id=1, status_effect_update=StatusEffectUpdate(
        effects_remove=["frozen"]
    ))

    changes = {}
    patch.apply(entity, changes)

    assert [s.kind for s in changes["combat"].status_effects] == ["stunned"]


def test_status_effect_patch_merge():
    sep1 = StatusEffectPatch(entity_id=1, status_effect_update=StatusEffectUpdate(
        effects_add=[StatusEffectState(kind="frozen")]
    ))
    sep2 = StatusEffectPatch(entity_id=1, status_effect_update=StatusEffectUpdate(
        effects_remove=["stunned"]
    ))

    merged = sep1.merge(sep2)
    assert [s.kind for s in merged.status_effect_update.effects_add] == ["frozen"]
    assert merged.status_effect_update.effects_remove == ["stunned"]


def test_extract_patches_includes_status_effect_patch():
    update = EntityUpdate(
        entity_id=1,
        status_effect_update=StatusEffectUpdate(effects_add=[StatusEffectState(kind="frozen")])
    )
    patches = extract_patches(1, update)
    assert any(isinstance(p, StatusEffectPatch) for p in patches)


def test_interaction_patch_apply_sets_kind():
    entity = EntityState(id=1, kind="hero", interaction=InteractionComponent(target_node_id=101, progress=0))
    patch = InteractionPatch(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0, kind="harvest"))

    changes = {}
    patch.apply(entity, changes)

    assert changes["interaction"].kind == "harvest"
    assert changes["interaction"].progress == 1.0


def test_interaction_patch_apply_reset_clears_kind():
    """Explicit behavior change from the old identity.properties dict-storage shape:
    reset=True replaces the whole InteractionComponent, so `kind` clears on reset --
    unlike the old dict-based interaction_kind, which was merge-only and never cleared."""
    entity = EntityState(id=1, kind="hero", interaction=InteractionComponent(
        target_node_id=101, progress=9, kind="harvest"
    ))
    patch = InteractionPatch(entity_id=1, interaction=InteractionUpdate(reset=True))

    changes = {}
    patch.apply(entity, changes)

    assert changes["interaction"].kind is None
    assert changes["interaction"].target_node_id is None
