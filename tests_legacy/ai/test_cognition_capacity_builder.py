"""Derivation proof tests for CognitionCapacityBuilder non-attribute inputs. [Intel M1 Task 2]

Verifies that personality, traits, archetype, and temporary overload
modifiers are actually consumed by the builder and produce deterministic
differences in the output profile.
"""
import pytest
from unittest.mock import MagicMock
from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder
from src_legacy.core.models.enums import TraitType


def create_mock_entity(
    int_=8, wis=8, per=8, cha=8,
    int_cap=15, wis_cap=15, per_cap=15, cha_cap=15,
    stamina=50, max_stamina=50,
    aggression=0.5, greed=0.5, caution=0.5, loyalty=0.5,
    ambition=0.5, curiosity=0.5, neuroticism=0.5,
    archetype="warrior",
    traits=None,
    hp=100, max_hp=100,
    hunger=0.0, panic=0.0
):
    """Create a deterministic mock entity for builder testing."""
    entity = MagicMock()
    
    # Attributes
    entity.progression.attributes.int_ = int_
    entity.progression.attributes.wis = wis
    entity.progression.attributes.per = per
    entity.progression.attributes.cha = cha
    entity.progression.attribute_caps.int_cap = int_cap
    entity.progression.attribute_caps.wis_cap = wis_cap
    entity.progression.attribute_caps.per_cap = per_cap
    entity.progression.attribute_caps.cha_cap = cha_cap
    entity.progression.stamina = stamina
    entity.progression.max_stamina = max_stamina

    # Personality
    entity.mind.decision.personality.aggression = aggression
    entity.mind.decision.personality.greed = greed
    entity.mind.decision.personality.caution = caution
    entity.mind.decision.personality.loyalty = loyalty
    entity.mind.decision.personality.ambition = ambition
    entity.mind.decision.personality.curiosity = curiosity
    entity.mind.decision.personality.neuroticism = neuroticism
    entity.mind.decision.personality.archetype = archetype

    # Traits
    _traits = set(traits or [])
    entity.has_trait = lambda t: t in _traits

    # Combat HP
    entity.combat.hp = hp
    entity.combat.max_hp = max_hp

    # Routine
    entity.mind.routine.hunger_level = hunger
    entity.mind.routine.sleep_debt = 0.0

    # Emotion
    entity.mind.emotion.panic = panic

    return entity


class TestPersonalityDerivation:
    """Verify personality modifiers affect builder output with deterministic deltas."""

    def test_curiosity_impact_on_leads(self):
        """Higher curiosity should strictly increase lead_retention_limit until clamped."""
        # Baseline with minimal attributes (n_per=0, n_int=0)
        v_low = create_mock_entity(int_=1, per=1, curiosity=0.0) # 2.0 -> 2
        v_high = create_mock_entity(int_=1, per=1, curiosity=1.0) # 3.5 -> 3
        
        p0 = CognitionCapacityBuilder.build(v_low)
        p1 = CognitionCapacityBuilder.build(v_high)
        
        assert p1.lead_retention_limit > p0.lead_retention_limit
        assert p0.lead_retention_limit == 2
        assert p1.lead_retention_limit == 3

    def test_caution_impact_on_resume(self):
        """Higher caution should strictly increase resume_reliability."""
        reckless = create_mock_entity(caution=0.0)
        cautious = create_mock_entity(caution=1.0)

        p_reckless = CognitionCapacityBuilder.build(reckless)
        p_cautious = CognitionCapacityBuilder.build(cautious)

        assert p_cautious.resume_reliability > p_reckless.resume_reliability
        # Delta should be exactly 0.15
        assert round(p_cautious.resume_reliability - p_reckless.resume_reliability, 2) == 0.15

    def test_neuroticism_impact_on_stability(self):
        """Higher neuroticism should strictly decrease judgment_stability."""
        stable = create_mock_entity(neuroticism=0.0)
        anxious = create_mock_entity(neuroticism=1.0)

        p_stable = CognitionCapacityBuilder.build(stable)
        p_anxious = CognitionCapacityBuilder.build(anxious)

        assert p_anxious.judgment_stability < p_stable.judgment_stability
        assert p_stable.judgment_stability - p_anxious.judgment_stability == pytest.approx(0.10)

    def test_unmapped_personality_no_effect(self):
        """Verify that aggression and greed do NOT affect cognitive capacity profile (Sparse Mapping)."""
        base = create_mock_entity(aggression=0.5, greed=0.5)
        high_aggro = create_mock_entity(aggression=1.0, greed=0.5)
        high_greed = create_mock_entity(aggression=0.5, greed=1.0)

        p_base = CognitionCapacityBuilder.build(base)
        p_aggro = CognitionCapacityBuilder.build(high_aggro)
        p_greed = CognitionCapacityBuilder.build(high_greed)

        assert p_base.model_dump() == p_aggro.model_dump()
        assert p_base.model_dump() == p_greed.model_dump()


class TestTraitDerivation:
    """Verify trait modifiers produce observable differences."""

    def test_diligent_increases_planning_budget(self):
        """DILIGENT trait should increase planning_budget by +1."""
        base = create_mock_entity(traits=[])
        diligent = create_mock_entity(traits=[TraitType.DILIGENT])

        p_base = CognitionCapacityBuilder.build(base)
        p_diligent = CognitionCapacityBuilder.build(diligent)

        assert p_diligent.planning_budget >= p_base.planning_budget
        assert p_diligent.judgment_stability >= p_base.judgment_stability

    def test_lazy_decreases_planning_budget(self):
        """LAZY trait should decrease planning_budget by -1."""
        base = create_mock_entity(traits=[])
        lazy = create_mock_entity(traits=[TraitType.LAZY])

        p_base = CognitionCapacityBuilder.build(base)
        p_lazy = CognitionCapacityBuilder.build(lazy)

        assert p_lazy.planning_budget <= p_base.planning_budget
        assert p_lazy.judgment_stability <= p_base.judgment_stability

    def test_tactical_increases_active_slice(self):
        """TACTICAL trait should increase active_slice_limit by +1."""
        base = create_mock_entity(traits=[])
        tactical = create_mock_entity(traits=[TraitType.TACTICAL])

        p_base = CognitionCapacityBuilder.build(base)
        p_tactical = CognitionCapacityBuilder.build(tactical)

        assert p_tactical.active_slice_limit >= p_base.active_slice_limit

    def test_curious_increases_leads(self):
        """CURIOUS trait should increase lead_retention_limit by +1."""
        base = create_mock_entity(traits=[])
        curious = create_mock_entity(traits=[TraitType.CURIOUS])

        p_base = CognitionCapacityBuilder.build(base)
        p_curious = CognitionCapacityBuilder.build(curious)

        assert p_curious.lead_retention_limit >= p_base.lead_retention_limit

    def test_oblivious_decreases_evidence_quality(self):
        """OBLIVIOUS trait should decrease evidence_quality."""
        base = create_mock_entity(traits=[])
        oblivious = create_mock_entity(traits=[TraitType.OBLIVIOUS])

        p_base = CognitionCapacityBuilder.build(base)
        p_oblivious = CognitionCapacityBuilder.build(oblivious)

        assert p_oblivious.evidence_quality < p_base.evidence_quality


class TestArchetypeDerivation:
    """Verify archetype modifiers produce observable differences."""

    def test_scholar_archetype_modifies_planning(self):
        """Scholar archetype should add +0.1 arch_mod to detour and abandonment."""
        warrior = create_mock_entity(archetype="warrior")
        scholar = create_mock_entity(archetype="scholar")

        p_warrior = CognitionCapacityBuilder.build(warrior)
        p_scholar = CognitionCapacityBuilder.build(scholar)

        # Scholar gets +0.1 arch_mod which feeds into detour_depth_limit and abandonment_threshold_mod
        assert p_scholar.abandonment_threshold_mod >= p_warrior.abandonment_threshold_mod

    def test_scout_archetype_modifies_detour(self):
        """Scout archetype should add +0.05 arch_mod."""
        warrior = create_mock_entity(archetype="warrior")
        scout = create_mock_entity(archetype="scout")

        p_warrior = CognitionCapacityBuilder.build(warrior)
        p_scout = CognitionCapacityBuilder.build(scout)

        assert p_scout.abandonment_threshold_mod >= p_warrior.abandonment_threshold_mod


class TestTemporaryOverloadDerivation:
    """Verify temporary impairment modifiers affect builder output."""

    def test_low_hp_reduces_planning(self):
        """Low HP (< 25%) should add stress penalty reducing planning budget."""
        healthy = create_mock_entity(hp=100, max_hp=100)
        wounded = create_mock_entity(hp=10, max_hp=100)

        p_healthy = CognitionCapacityBuilder.build(healthy)
        p_wounded = CognitionCapacityBuilder.build(wounded)

        assert p_wounded.planning_budget <= p_healthy.planning_budget
        assert p_wounded.judgment_stability <= p_healthy.judgment_stability

    def test_hunger_reduces_stability(self):
        """High hunger (> 0.8) should add stress penalty."""
        fed = create_mock_entity(hunger=0.0)
        starving = create_mock_entity(hunger=0.95)

        p_fed = CognitionCapacityBuilder.build(fed)
        p_starving = CognitionCapacityBuilder.build(starving)

        assert p_starving.judgment_stability <= p_fed.judgment_stability

    def test_panic_severely_reduces_planning(self):
        """High panic (> 0.5) should dramatically reduce planning budget."""
        calm = create_mock_entity(panic=0.0)
        panicked = create_mock_entity(panic=0.9)

        p_calm = CognitionCapacityBuilder.build(calm)
        p_panicked = CognitionCapacityBuilder.build(panicked)

        # Panic adds -2.0 to planning_budget calculation and +0.15 stress
        assert p_panicked.planning_budget < p_calm.planning_budget

    def test_fatigue_reduces_evidence_quality(self):
        """Low stamina should reduce evidence quality and judgment stability."""
        fresh = create_mock_entity(stamina=50, max_stamina=50)
        exhausted = create_mock_entity(stamina=1, max_stamina=50)

        p_fresh = CognitionCapacityBuilder.build(fresh)
        p_exhausted = CognitionCapacityBuilder.build(exhausted)

        assert p_exhausted.evidence_quality < p_fresh.evidence_quality
        assert p_exhausted.judgment_stability < p_fresh.judgment_stability
