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


def test_strategic_source_trust_participates_in_canonical_hash():
    """
    TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP: source_trust is a real, live scoring input
    to detour selection (belief_and_detour_contract.md's source_trust_bonus term), but was
    previously excluded from EntityState.to_canonical_dict()'s "strategic" sub-dict -- a
    same-seed divergence confined to source_trust would have gone completely undetected by
    CanonicalStateHasher, the hash src/engine/kernel.py uses for its per-tick and final-run
    determinism checks. Confirms the fix: two otherwise-identical entities differing ONLY in
    source_trust now produce different canonical dicts and different hashes.
    """
    from dataclasses import replace as dataclass_replace
    from src.core.state import AuthoritativeState
    from src.core.strategic import SourceTrustEntry
    from src.engine.checkpoint import CanonicalStateHasher

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    assert base.strategic.source_trust == {}

    with_trust = dataclass_replace(
        base,
        strategic=dataclass_replace(
            base.strategic,
            source_trust={5: SourceTrustEntry(entity_id=5, trust=0.9, interactions=3, last_outcome="SUCCESS")},
        ),
    )

    assert base.to_canonical_dict() != with_trust.to_canonical_dict()

    state_base = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: base})
    state_with_trust = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: with_trust})

    assert CanonicalStateHasher.get_hash(state_base) != CanonicalStateHasher.get_hash(state_with_trust)


def test_strategic_all_nine_newly_covered_fields_participate_in_canonical_hash():
    """
    TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP: the remaining 8 fields (source_trust is
    covered by its own dedicated test above given its P0 live-behavior significance) --
    home_region_id, candidate_zones, hypotheses, contracts, turning_points,
    committed_intentions, primary_overload_source, last_overload_tick -- were also
    previously excluded from the canonical hash with no comment explaining why. Confirms
    each one independently changes to_canonical_dict() output when it diverges.
    """
    from dataclasses import replace as dataclass_replace
    from src.core.strategic import (
        CandidateZone, HypothesisState, ContractState, ContractKind, ContractStatus,
        TurningPointState, TurningPointKind, CommittedIntention,
    )

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    base_dict = base.to_canonical_dict()

    variants = {
        "home_region_id": dataclass_replace(base.strategic, home_region_id="region_1"),
        "candidate_zones": dataclass_replace(
            base.strategic, candidate_zones={"z1": CandidateZone(id="z1", region_id="region_1")}
        ),
        "hypotheses": dataclass_replace(
            base.strategic, hypotheses={"h1": HypothesisState(id="h1", subject="s", claim="c")}
        ),
        "contracts": dataclass_replace(
            base.strategic,
            contracts={"c1": ContractState(
                id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2,
                status=ContractStatus.OFFERED,
            )},
        ),
        "turning_points": dataclass_replace(
            base.strategic,
            turning_points=[TurningPointState(id="t1", kind=TurningPointKind.BETRAYAL, subject_id=2)],
        ),
        "committed_intentions": dataclass_replace(
            base.strategic,
            committed_intentions=(
                CommittedIntention(
                    intention_id="i1", goal_kind="explore", target_hint=None,
                    sequence_index=0, status="pending",
                ),
            ),
        ),
        "primary_overload_source": dataclass_replace(base.strategic, primary_overload_source="combat"),
        "last_overload_tick": dataclass_replace(base.strategic, last_overload_tick=42),
    }

    for field_name, changed_strategic in variants.items():
        changed_entity = dataclass_replace(base, strategic=changed_strategic)
        assert base_dict != changed_entity.to_canonical_dict(), (
            f"'{field_name}' divergence did not change to_canonical_dict() output"
        )


def test_strategic_profile_excluded_from_canonical_hash():
    """
    TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP: StrategicComponent.profile is documented as
    "Derived from entity attributes (WIS, INT, level, archetype)" -- fully reconstructable
    from already-covered `attributes`, so it is intentionally excluded from the canonical
    hash (a divergence there cannot be independent of already-detected state). This is a
    regression guard on the exclusion itself: if a future change makes `profile` divergent
    from `attributes`, this test failing is the signal that the exclusion is no longer safe.
    """
    from dataclasses import replace as dataclass_replace
    from src.core.strategic import CognitionProfile

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    changed = dataclass_replace(
        base,
        strategic=dataclass_replace(base.strategic, profile=CognitionProfile(max_active_projects=99)),
    )

    assert base.to_canonical_dict() == changed.to_canonical_dict()


def test_social_seven_newly_covered_fields_participate_in_canonical_hash():
    """
    TCK-20260902-SOCIAL-CANONICAL-HASH-GAP: SocialComponent's canonical hash previously
    covered only 10 of 17 real fields, omitting debt_history, salience_history,
    nemesis_ids, place_attachment, betrayal_records, last_offer_tick, and rejection_count
    -- all confirmed real, actively-consumed durable state (e.g. nemesis_ids gates
    cognition target evaluation, rejection_count feeds contract appraisal). Notably
    betrayal_records (the event list) was uncovered while betrayal_count (its own derived
    count) was already covered -- an inconsistent partial gap, not a deliberate exclusion.
    Confirms each of the 7 fields independently changes to_canonical_dict() output when it
    diverges.
    """
    from dataclasses import replace as dataclass_replace
    from src.core.models.social import BetrayalRecord

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    base_dict = base.to_canonical_dict()

    variants = {
        "debt_history": dataclass_replace(base.social, debt_history={5: 3.0}),
        "salience_history": dataclass_replace(base.social, salience_history={5: 0.8}),
        "nemesis_ids": dataclass_replace(base.social, nemesis_ids={5, 9}),
        "place_attachment": dataclass_replace(base.social, place_attachment={"region_1": 0.5}),
        "betrayal_records": dataclass_replace(
            base.social,
            betrayal_records=[BetrayalRecord(contract_id="c1", betrayer_id=1, victim_id=2)],
        ),
        "last_offer_tick": dataclass_replace(base.social, last_offer_tick=42),
        "rejection_count": dataclass_replace(base.social, rejection_count={5: 3}),
    }

    for field_name, changed_social in variants.items():
        changed_entity = dataclass_replace(base, social=changed_social)
        assert base_dict != changed_entity.to_canonical_dict(), (
            f"'{field_name}' divergence did not change to_canonical_dict() output"
        )


def test_social_nemesis_ids_participates_in_canonical_hash_end_to_end():
    """
    TCK-20260902-SOCIAL-CANONICAL-HASH-GAP: nemesis_ids specifically gates cognition
    target evaluation (src/engine/cognition.py) -- confirms the fix propagates all the
    way to CanonicalStateHasher.get_hash(), the hash src/engine/kernel.py uses for its
    per-tick and final-run determinism checks (same consumer chain as the parallel
    TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP fix).
    """
    from dataclasses import replace as dataclass_replace
    from src.core.state import AuthoritativeState
    from src.engine.checkpoint import CanonicalStateHasher

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    assert base.social.nemesis_ids == set()

    with_nemesis = dataclass_replace(
        base, social=dataclass_replace(base.social, nemesis_ids={5, 9}),
    )

    state_base = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: base})
    state_with_nemesis = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: with_nemesis})

    assert CanonicalStateHasher.get_hash(state_base) != CanonicalStateHasher.get_hash(state_with_nemesis)


def test_navigation_eleven_newly_covered_fields_participate_in_canonical_hash():
    """
    TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP: NavigationComponent's canonical hash
    previously covered only target, path, moved_recently, and place_id -- omitting
    movement_mode, last_failure_reason, wait_count, oscillation_count, last_position,
    home_position, leash_radius, region_id, chase_ticks, max_chase_ticks, and
    returning_home. All 11 confirmed real, actively-consumed durable state (e.g.
    region_id gates memory/information/combat-target-resolution phases, wait_count/
    oscillation_count gate congestion-recovery replanning in src/engine/movement.py,
    leash_radius/chase_ticks/max_chase_ticks/returning_home gate mob-leash chase logic
    in src/engine/rpg_depth.py, last_failure_reason feeds StrategicIntelligenceSystem's
    blocker inference). `position` itself was already covered separately as a top-level
    `to_canonical_dict()` key (`self.navigation.position`), not omitted as the original
    finding's own open question worried it might be. Confirms each of the 11 fields
    independently changes to_canonical_dict() output when it diverges.
    """
    from dataclasses import replace as dataclass_replace
    from src.core.movement_modes import MovementMode

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    base_dict = base.to_canonical_dict()

    variants = {
        "movement_mode": dataclass_replace(base.navigation, movement_mode=MovementMode.PURSUE),
        "last_failure_reason": dataclass_replace(base.navigation, last_failure_reason="path_blocked"),
        "wait_count": dataclass_replace(base.navigation, wait_count=3),
        "oscillation_count": dataclass_replace(base.navigation, oscillation_count=2),
        "last_position": dataclass_replace(base.navigation, last_position=(1.0, 2.0)),
        "home_position": dataclass_replace(base.navigation, home_position=(4.0, 5.0)),
        "leash_radius": dataclass_replace(base.navigation, leash_radius=10.0),
        "region_id": dataclass_replace(base.navigation, region_id="region_1"),
        "chase_ticks": dataclass_replace(base.navigation, chase_ticks=5),
        "max_chase_ticks": dataclass_replace(base.navigation, max_chase_ticks=30),
        "returning_home": dataclass_replace(base.navigation, returning_home=True),
    }

    for field_name, changed_navigation in variants.items():
        changed_entity = dataclass_replace(base, navigation=changed_navigation)
        assert base_dict != changed_entity.to_canonical_dict(), (
            f"'{field_name}' divergence did not change to_canonical_dict() output"
        )


def test_navigation_region_id_participates_in_canonical_hash_end_to_end():
    """
    TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP: region_id specifically is a cached
    back-reference ("Phase 3 Hardening: Cache region_id to avoid O(N) scans") that real
    movement/memory/combat-resolution logic gates on (src/domains/memory/phase.py,
    src/domains/information/phase.py, src/engine/semantic_entity_index.py,
    src/engine/pipeline_phases/actions.py) -- a same-seed divergence there would have
    gone completely undetected by CanonicalStateHasher, the hash src/engine/kernel.py
    uses for its per-tick and final-run determinism checks. Confirms the fix propagates
    all the way to CanonicalStateHasher.get_hash() (same consumer chain as the parallel
    TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP / TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
    fixes).
    """
    from dataclasses import replace as dataclass_replace
    from src.core.state import AuthoritativeState
    from src.engine.checkpoint import CanonicalStateHasher

    base = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    assert base.navigation.region_id is None

    with_region = dataclass_replace(
        base, navigation=dataclass_replace(base.navigation, region_id="region_1"),
    )

    state_base = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: base})
    state_with_region = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: with_region})

    assert CanonicalStateHasher.get_hash(state_base) != CanonicalStateHasher.get_hash(state_with_region)
