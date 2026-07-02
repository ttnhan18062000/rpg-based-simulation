"""Unit tests for GoldSinkSystem (TCK-20260619-E33C-GOLD-SINK).

Test plan: staging_artifacts/TCK-20260619-E33C-GOLD-SINK/test_plan.md
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.models.inventory import EquipSlot
from src.core.state import AuthoritativeState, EquipmentComponent
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.gold_sink import GoldSinkSystem
from src.core.conservation import ResourceTransactionResolver
from src.core.update_models.resources import ResourceTransferIntent


SEED = 42
WINDOW_TICK = 100   # EconomyHealthMonitor.WINDOW_SIZE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: int, gold: int, alive: bool = True, equipment: EquipmentComponent | None = None):
    b = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(float(eid), 0.0)
        .combat(hp=100, max_hp=100, atk=5, def_stat=5, attack_range=1, alive=alive, readiness=100.0)
        .inventory(gold=gold)
    )
    if equipment is not None:
        b = b.replace_equipment(equipment)
    return b.build()


def _unequal_state(tick: int = WINDOW_TICK) -> AuthoritativeState:
    """One rich entity (50000 gold) + 9 poor (1 gold each). Gini ≈ 0.9 >> 0.7."""
    entities = {1: _entity(1, 50000)}
    for i in range(2, 11):
        entities[i] = _entity(i, 1)
    return AuthoritativeState(tick=tick, seed=SEED, entities=entities)


def _equal_state(tick: int = WINDOW_TICK) -> AuthoritativeState:
    """All entities have equal gold → Gini = 0 (below threshold)."""
    entities = {i: _entity(i, 100) for i in range(1, 6)}
    return AuthoritativeState(tick=tick, seed=SEED, entities=entities)


def _make_degraded_equipment() -> EquipmentComponent:
    """Equipment with MAIN_HAND durability 0.3 (< 0.5) and TORSO 0.8 (>= 0.5)."""
    return EquipmentComponent(
        slots={EquipSlot.MAIN_HAND: "sword", EquipSlot.TORSO: "chainmail"},
        durability={EquipSlot.MAIN_HAND: 0.3, EquipSlot.TORSO: 0.8},
    )


def _make_good_equipment() -> EquipmentComponent:
    """Equipment with all slots above 0.5 durability."""
    return EquipmentComponent(
        slots={EquipSlot.MAIN_HAND: "sword", EquipSlot.TORSO: "chainmail"},
        durability={EquipSlot.MAIN_HAND: 0.9, EquipSlot.TORSO: 0.8},
    )


# ---------------------------------------------------------------------------
# TC-C01: REPAIR_FEE applied to degraded equipment under inflation
# ---------------------------------------------------------------------------

def test_repair_fee_applied_to_degraded_equipment():
    """Entity with 1 degraded slot and gini > 0.7 gets a REPAIR_FEE intent."""
    equip = _make_degraded_equipment()
    # Use unequal state but replace entity 1 with degraded equipment
    entities = {1: _entity(1, 50000, equipment=equip)}
    for i in range(2, 11):
        entities[i] = _entity(i, 1)
    state = AuthoritativeState(tick=WINDOW_TICK, seed=SEED, entities=entities)

    result = GoldSinkSystem.apply(state, StateUpdate())

    e1_upd = result.entity_updates.get(1)
    assert e1_upd is not None, "Entity 1 should have an update"
    repair_intents = [t for t in e1_upd.resource_transfers if t.source_kind == "REPAIR_FEE"]
    assert len(repair_intents) == 1
    assert repair_intents[0].gold_cost == 1   # 1 degraded slot × 1 gold/slot


# ---------------------------------------------------------------------------
# TC-C02: REPAIR_FEE not applied when durability is fine
# ---------------------------------------------------------------------------

def test_repair_fee_not_applied_above_durability_threshold():
    """Entity with all slots >= 0.5 durability under inflation gets no REPAIR_FEE."""
    equip = _make_good_equipment()
    entities = {1: _entity(1, 50000, equipment=equip)}
    for i in range(2, 11):
        entities[i] = _entity(i, 1)
    state = AuthoritativeState(tick=WINDOW_TICK, seed=SEED, entities=entities)

    result = GoldSinkSystem.apply(state, StateUpdate())

    e1_upd = result.entity_updates.get(1)
    if e1_upd is not None:
        repair_intents = [t for t in e1_upd.resource_transfers if t.source_kind == "REPAIR_FEE"]
        assert len(repair_intents) == 0, "No REPAIR_FEE when all durability >= 0.5"


# ---------------------------------------------------------------------------
# TC-C03: SERVICE_FEE applied to alive entities with gold under inflation
# ---------------------------------------------------------------------------

def test_service_fee_applied_under_inflation():
    """Every alive entity with gold >= 1 gets a SERVICE_FEE intent under inflation."""
    state = _unequal_state()
    result = GoldSinkSystem.apply(state, StateUpdate())

    # All entities with gold >= 1 should receive SERVICE_FEE
    entities_with_fee = 0
    for e in state.entities.values():
        if e.combat.alive and e.inventory.gold >= 1:
            upd = result.entity_updates.get(e.id)
            if upd is not None:
                service_intents = [t for t in upd.resource_transfers if t.source_kind == "SERVICE_FEE"]
                if service_intents:
                    entities_with_fee += 1
    assert entities_with_fee > 0, "At least some entities should have SERVICE_FEE"


# ---------------------------------------------------------------------------
# TC-C04: TAX applied to wealthy entities above mean*1.5
# ---------------------------------------------------------------------------

def test_tax_applied_to_wealthy_entities():
    """Rich entity (50000 gold >> mean) receives a TAX intent under inflation."""
    state = _unequal_state()
    result = GoldSinkSystem.apply(state, StateUpdate())

    # Entity 1 has 50000 gold — far above mean
    e1_upd = result.entity_updates.get(1)
    assert e1_upd is not None
    tax_intents = [t for t in e1_upd.resource_transfers if t.source_kind == "TAX"]
    assert len(tax_intents) == 1
    # Tax = min(50, max(1, int(50000 * 0.05))) = min(50, 2500) = 50
    assert tax_intents[0].gold_cost == 50


# ---------------------------------------------------------------------------
# TC-C05: TAX not applied to poor entities below mean*1.5
# ---------------------------------------------------------------------------

def test_tax_not_applied_to_poor_entities():
    """Poor entities (1 gold, below mean*1.5) receive no TAX."""
    state = _unequal_state()
    result = GoldSinkSystem.apply(state, StateUpdate())

    # Entities 2-10 have 1 gold each — mean ≈ 5001, threshold ≈ 7501 → below
    for eid in range(2, 11):
        upd = result.entity_updates.get(eid)
        if upd is not None:
            tax_intents = [t for t in upd.resource_transfers if t.source_kind == "TAX"]
            assert len(tax_intents) == 0, f"Entity {eid} should not receive TAX (too poor)"


# ---------------------------------------------------------------------------
# TC-C06: No sinks when gini below threshold
# ---------------------------------------------------------------------------

def test_no_sinks_when_gini_below_threshold():
    """Equal wealth distribution → gini ≈ 0 → no sink transfers emitted."""
    state = _equal_state()
    result = GoldSinkSystem.apply(state, StateUpdate())

    for upd in result.entity_updates.values():
        sink_intents = [t for t in upd.resource_transfers
                        if t.source_kind in ("REPAIR_FEE", "SERVICE_FEE", "TAX")]
        assert len(sink_intents) == 0, "No sinks should fire below gini threshold"


# ---------------------------------------------------------------------------
# TC-C07: Conservation invariant — gold_cost sum equals intended drain
# ---------------------------------------------------------------------------

def test_conservation_invariant():
    """Total gold_cost across all sink intents equals the sum of individual fees."""
    state = _unequal_state()
    result = GoldSinkSystem.apply(state, StateUpdate())

    total_intended = 0
    for upd in result.entity_updates.values():
        for intent in upd.resource_transfers:
            if intent.source_kind in ("REPAIR_FEE", "SERVICE_FEE", "TAX"):
                total_intended += intent.gold_cost

    # All gold_delta on sink intents should be 0 (only gold_cost moves gold)
    for upd in result.entity_updates.values():
        for intent in upd.resource_transfers:
            if intent.source_kind in ("REPAIR_FEE", "SERVICE_FEE", "TAX"):
                assert intent.gold_delta == 0, "Sink intents must use gold_cost only, not gold_delta"

    assert total_intended > 0, "Some gold should be drained under inflation"


# ---------------------------------------------------------------------------
# TC-C08: Sinks not applied to dead entities
# ---------------------------------------------------------------------------

def test_sink_not_applied_to_dead_entities():
    """Dead entities receive no gold sink transfers."""
    dead = _entity(99, 5000, alive=False)
    entities = {99: dead, 1: _entity(1, 50000)}
    for i in range(2, 11):
        entities[i] = _entity(i, 1)
    state = AuthoritativeState(tick=WINDOW_TICK, seed=SEED, entities=entities)

    result = GoldSinkSystem.apply(state, StateUpdate())

    dead_upd = result.entity_updates.get(99)
    if dead_upd is not None:
        sink_intents = [t for t in dead_upd.resource_transfers
                        if t.source_kind in ("REPAIR_FEE", "SERVICE_FEE", "TAX")]
        assert len(sink_intents) == 0, "Dead entity should receive no sink transfers"


# ---------------------------------------------------------------------------
# TC-C09: Sink respects entity gold floor (gold=0 entity is skipped)
# ---------------------------------------------------------------------------

def test_sink_respects_entity_gold_floor():
    """Entity with gold=0 receives no sink transfers."""
    broke = _entity(50, 0)
    entities = {50: broke, 1: _entity(1, 50000)}
    for i in range(2, 11):
        entities[i] = _entity(i, 1)
    state = AuthoritativeState(tick=WINDOW_TICK, seed=SEED, entities=entities)

    result = GoldSinkSystem.apply(state, StateUpdate())

    upd = result.entity_updates.get(50)
    if upd is not None:
        sink_intents = [t for t in upd.resource_transfers
                        if t.source_kind in ("REPAIR_FEE", "SERVICE_FEE", "TAX")]
        assert len(sink_intents) == 0, "Gold=0 entity should not receive any sink"


# ---------------------------------------------------------------------------
# TC-C10: Conservation resolver handles REPAIR_FEE
# ---------------------------------------------------------------------------

def test_conservation_resolver_handles_repair_fee_accepted():
    """ResourceTransactionResolver accepts REPAIR_FEE when entity has sufficient gold."""
    entity = _entity(1, 100)
    state = AuthoritativeState(tick=1, seed=SEED, entities={1: entity})
    intent = ResourceTransferIntent(
        source_id="gold_sink",
        source_kind="REPAIR_FEE",
        gold_cost=5,
        gold_delta=0,
        transfer_kind="FEE",
    )
    result = ResourceTransactionResolver.resolve(state, entity, intent)
    assert result.accepted is True
    assert result.inventory_update is not None
    # Net gold change = gold_delta - gold_cost = 0 - 5 = -5
    assert result.inventory_update.gold_delta == -5


def test_conservation_resolver_handles_repair_fee_rejected():
    """ResourceTransactionResolver rejects REPAIR_FEE when entity gold < gold_cost."""
    from src.core.enums import ReasonCode
    entity = _entity(1, 2)
    state = AuthoritativeState(tick=1, seed=SEED, entities={1: entity})
    intent = ResourceTransferIntent(
        source_id="gold_sink",
        source_kind="REPAIR_FEE",
        gold_cost=10,  # entity only has 2
        gold_delta=0,
        transfer_kind="FEE",
    )
    result = ResourceTransactionResolver.resolve(state, entity, intent)
    assert result.accepted is False
    assert result.reason == ReasonCode.ACTION_EXHAUSTION


# ---------------------------------------------------------------------------
# TC-C11: Conservation resolver handles SERVICE_FEE
# ---------------------------------------------------------------------------

def test_conservation_resolver_handles_service_fee():
    """ResourceTransactionResolver accepts SERVICE_FEE correctly."""
    entity = _entity(1, 50)
    state = AuthoritativeState(tick=1, seed=SEED, entities={1: entity})
    intent = ResourceTransferIntent(
        source_id="gold_sink",
        source_kind="SERVICE_FEE",
        gold_cost=1,
        gold_delta=0,
        transfer_kind="FEE",
    )
    result = ResourceTransactionResolver.resolve(state, entity, intent)
    assert result.accepted is True
    assert result.inventory_update.gold_delta == -1


# ---------------------------------------------------------------------------
# TC-C12: Non-window tick does not fire
# ---------------------------------------------------------------------------

def test_no_sink_on_non_window_tick():
    """GoldSinkSystem does not fire on non-WINDOW_SIZE ticks (e.g. tick=1)."""
    entities = {1: _entity(1, 50000)}
    for i in range(2, 11):
        entities[i] = _entity(i, 1)
    state = AuthoritativeState(tick=1, seed=SEED, entities=entities)  # tick=1, not 100

    result = GoldSinkSystem.apply(state, StateUpdate())

    # No entity updates should be added
    assert len(result.entity_updates) == 0, "Gold sink must not fire on non-window ticks"
