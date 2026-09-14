"""
tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py

Phase 4 — OpponentPerceptionService unit tests.
Verifies subjective opponent estimation and uncertainty propagation.

TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: rewritten against the power-gap-driven law
(docs/mechanics/04_strategic_cognition.md Sec 13.2/13.3) -- the prior version of this file hardcoded
assertions against the disproven `target_lvl * 20.0` power term and the flat `perception < 4`
uncertainty threshold this ticket replaces. `evolution_level`/`level=` is no longer a real input to
the power estimate at all (Sec 13.2: deliberately excluded, double-counts via Attribute Points) --
real power gaps are built here via atk/def_stat/max_hp directly.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, EquipmentComponent, AuthoritativeState
from src.core.models.inventory import ItemStack, EquipSlot
from src.domains.combat_engagement.perception import OpponentPerceptionService
from src.domains.combat_engagement.schema import OpponentModel
from src.domains.combat_engagement.power import true_power


def _entity(e_id, perception=5, hp=100, max_hp=100, atk=10, def_stat=2, weapon_slot=None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=atk, def_stat=def_stat))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    b.attributes(perception=perception)

    if weapon_slot:
        from src.core.state import ReadOnlyDict
        slots = ReadOnlyDict({EquipSlot.MAIN_HAND: "iron_sword"})
        durability = ReadOnlyDict({EquipSlot.MAIN_HAND: 100.0})
        b.replace_equipment(EquipmentComponent(slots=slots, durability=durability))

    return b.build()


def _state(entities, tick=1, seed=42) -> AuthoritativeState:
    return AuthoritativeState(entities={e.id: e for e in entities}, tick=tick, seed=seed)


def test_evenly_matched_pair_has_maximal_uncertainty():
    """Sec 13.3's own point of the design: uncertainty is highest exactly where the gap is zero."""
    actor = _entity(1, perception=5, atk=10, def_stat=2, max_hp=100)
    target = _entity(2, perception=5, atk=10, def_stat=2, max_hp=100)
    state = _state([actor, target])

    est = OpponentPerceptionService.estimate(actor, target, memory=None, state=state)

    assert est.uncertainty >= 0.5
    assert est.confidence <= 0.6


def test_large_power_gap_produces_confident_estimate():
    """A far stronger target is judged confidently -- the far end of the gap curve."""
    actor = _entity(1, perception=5, atk=10, def_stat=2, max_hp=100)
    target = _entity(2, perception=5, atk=80, def_stat=40, max_hp=300)  # true_power ~130
    state = _state([actor, target])

    est = OpponentPerceptionService.estimate(actor, target, memory=None, state=state)

    assert est.uncertainty < 0.3
    assert est.confidence > 0.6


def test_estimated_power_tracks_apparent_power_not_level():
    """evolution_level no longer feeds the estimate at all -- real combat stats do."""
    actor = _entity(1, perception=5)
    target = _entity(2, perception=5, atk=20, def_stat=8, max_hp=150)
    state = _state([actor, target])

    est = OpponentPerceptionService.estimate(actor, target, memory=None, state=state)

    expected_true_power = true_power(target)
    # Noise term perturbs the estimate deterministically -- must stay within the documented
    # noise envelope of true_power, not equal it exactly.
    assert abs(est.estimated_power - expected_true_power) <= expected_true_power * 0.5


def test_known_enemy_memory_reduces_uncertainty():
    actor = _entity(1, perception=5, atk=10, def_stat=2, max_hp=100)
    target = _entity(2, perception=5, atk=10, def_stat=2, max_hp=100)  # zero-gap pair
    state = _state([actor, target])

    est_without_memory = OpponentPerceptionService.estimate(actor, target, memory=None, state=state)

    mem = OpponentModel(
        subject_key="entity.2",
        estimated_power=42.0,
        uncertainty=0.1,
        confidence=0.9,
    )
    est_with_memory = OpponentPerceptionService.estimate(actor, target, memory=mem, state=state)

    # Memory must reduce uncertainty and increase confidence relative to no memory at all.
    assert est_with_memory.uncertainty < est_without_memory.uncertainty
    assert est_with_memory.confidence > est_without_memory.confidence
    assert "entity.2" in est_with_memory.memory_used


def test_visible_better_equipment_increases_estimate():
    actor = _entity(1, perception=5)
    target_unarmed = _entity(2)
    target_armed = _entity(3, weapon_slot="iron_sword")
    state = _state([actor, target_unarmed, target_armed])

    est_unarmed = OpponentPerceptionService.estimate(actor, target_unarmed, state=state)
    est_armed = OpponentPerceptionService.estimate(actor, target_armed, state=state)

    assert est_armed.estimated_power > est_unarmed.estimated_power
    assert "armed" in est_armed.visible_signals


def test_low_perception_sharpens_slower_at_a_real_gap():
    """
    Sec 13.3: a higher-PER observer needs a smaller gap before its estimate sharpens. At exact
    parity (gap=0) uncertainty is maximal for everyone regardless of PER -- the old flat-threshold
    test's premise (perception matters even at zero gap) no longer holds under the gap-driven law,
    since nobody can distinguish a perfectly even match no matter how sharp-eyed. The real
    perception effect only shows up once there IS a gap to resolve.
    """
    actor_blind = _entity(1, perception=2, atk=10, def_stat=2, max_hp=100)
    actor_sharp = _entity(2, perception=99, atk=10, def_stat=2, max_hp=100)
    target = _entity(3, perception=5, atk=30, def_stat=10, max_hp=150)  # a real, nonzero gap
    state = _state([actor_blind, actor_sharp, target])

    est_blind = OpponentPerceptionService.estimate(actor_blind, target, state=state)
    est_sharp = OpponentPerceptionService.estimate(actor_sharp, target, state=state)

    assert est_blind.uncertainty > est_sharp.uncertainty
    assert "poor_perception" in est_blind.unknown_factors


def test_dead_intel_variable_is_gone():
    """
    TCK-20260913 disclosed defect (Sec 13.3): `attrs.intelligence` was read into a local `intel`
    variable never subsequently used anywhere in estimate(). Confirmed fixed via source inspection
    -- INT is a declared future consideration-weighting seam (Sec 13.4), not an estimation-accuracy
    input today.
    """
    import inspect
    from src.domains.combat_engagement import perception as perception_module

    source = inspect.getsource(perception_module.OpponentPerceptionService.estimate)
    assert "intelligence" not in source
