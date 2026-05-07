"""
Phase 3 — Resource / Reward Transaction Completion Tests

Proves that:
1. Combat loot/gold reward cannot partially disappear
2. Multiple transfers in one tick support all-or-nothing (grouped) semantics
3. Failed reward is either queued, rejected, or explicitly partial with reason
4. Transaction rejection records reason in IntentResult
5. No source mutation occurs without destination success
6. Quest reward delivery and status are atomic
"""
import pytest
from dataclasses import replace, field
from src.core.state import (
    AuthoritativeState, EntityState, InventoryComponent, ItemStack,
    ResourceNodeState, GroundItemState, CorpseState, IntentResult,
    IdentityComponent, InteractionComponent
)
from src.core.updates import (
    StateUpdate, EntityUpdate, ResourceTransferIntent, InventoryUpdate,
    IdentityUpdate, QuestUpdate
)
from src.core.conservation import ResourceTransactionResolver, TransactionResult
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def base_state():
    """Minimal authoritative state for conservation tests."""
    return AuthoritativeState(tick=10, seed=42)

@pytest.fixture
def entity_with_inventory(base_state):
    """Entity with a 2-slot inventory containing 50 gold, enough weight for 2 items."""
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0, 0)
               .inventory(gold=50, max_slots=2, max_weight=100.0)
              .build())
    return replace(base_state, entities={1: entity})

@pytest.fixture
def entity_full_inventory(base_state):
    """Entity with completely full inventory (2/2 slots)."""
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0, 0)
              .inventory(gold=50, items=[ItemStack("wood", 1), ItemStack("herb", 1)], max_slots=2)
              .build())
    return replace(base_state, entities={1: entity})


# ─── 1. Combat Loot Atomicity (Direct Resolver) ─────────────────────────────

class TestCombatRewardAtomicity:
    """Combat rewards (gold + XP) must not partially disappear.
    Tested at the resolver level since combat intents are generated 
    by authoritative systems inside the pipeline."""

    def test_combat_reward_gold_and_xp_are_atomic(self, entity_with_inventory):
        """COMBAT source_kind produces both gold and XP as a single accepted transfer."""
        state = entity_with_inventory
        intent = ResourceTransferIntent(
            source_id=99,
            source_kind="COMBAT",
            gold_delta=100,
            xp_reward=250,
            transfer_kind="REWARD"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is True
        assert result.inventory_update.gold_delta == 100
        assert result.identity_update.evolution_points_delta == 250

    def test_combat_reward_with_items_respects_capacity(self, entity_full_inventory):
        """Gold/XP rewards (no slot usage) always succeed even with full inventory."""
        state = entity_full_inventory
        intent = ResourceTransferIntent(
            source_id=99,
            source_kind="COMBAT",
            gold_delta=200,
            xp_reward=500,
            transfer_kind="REWARD"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is True
        assert result.inventory_update.gold_delta == 200
        assert result.identity_update.evolution_points_delta == 500

    def test_quest_reward_resolver_is_atomic(self, entity_with_inventory):
        """QUEST source_kind produces gold + XP as a single accepted transfer."""
        state = entity_with_inventory
        intent = ResourceTransferIntent(
            source_id="q1",
            source_kind="QUEST",
            gold_delta=100,
            xp_reward=200,
            transfer_kind="QUEST_REWARD"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is True
        assert result.inventory_update.gold_delta == 100
        assert result.identity_update.evolution_points_delta == 200


# ─── 2. Grouped Transfer Rollback ────────────────────────────────────────────

class TestGroupedTransferRollback:
    """Grouped resource transfers roll back atomically if any required member fails.
    Uses HARVEST/PICKUP transfer kinds that pass through the pipeline gate."""

    def test_grouped_harvests_all_succeed(self, entity_with_inventory):
        """Two grouped harvests that both succeed produce combined results."""
        state = entity_with_inventory
        node1 = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=5, max_charges=5,
            required_ticks=1
        )
        node2 = ResourceNodeState(
            id=102, kind="HERB_NODE", position=(2, 0),
            yields_item="herb", remaining_charges=5, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node1, 102: node2})

        group_id = "harvest_bundle_1"
        transfers = [
            ResourceTransferIntent(
                source_id=101, source_kind="NODE",
                items_add=[ItemStack("iron_ore", 1)],
                transfer_kind="HARVEST",
                group_id=group_id, is_group_required=True
            ),
            ResourceTransferIntent(
                source_id=102, source_kind="NODE",
                items_add=[ItemStack("herb", 1)],
                transfer_kind="HARVEST",
                group_id=group_id, is_group_required=True
            ),
        ]

        update = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=transfers)
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        # Both succeeded: entity should have iron_ore and herb
        items = {i.item_id for i in final_state.entities[1].inventory.items}
        assert "iron_ore" in items
        assert "herb" in items

    def test_grouped_transfers_rollback_on_required_failure(self, entity_with_inventory):
        """If a required grouped intent fails, ALL intents in the group roll back."""
        state = entity_with_inventory

        # Node 101 is valid, Node 102 is depleted
        node1 = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=5, max_charges=5,
            required_ticks=1
        )
        node2 = ResourceNodeState(
            id=102, kind="HERB_NODE", position=(2, 0),
            yields_item="herb", remaining_charges=0, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node1, 102: node2})

        group_id = "harvest_bundle_1"
        transfers = [
            ResourceTransferIntent(
                source_id=101, source_kind="NODE",
                items_add=[ItemStack("iron_ore", 1)],
                transfer_kind="HARVEST",
                group_id=group_id, is_group_required=True
            ),
            ResourceTransferIntent(
                source_id=102, source_kind="NODE",
                items_add=[ItemStack("herb", 1)],
                transfer_kind="HARVEST",
                group_id=group_id, is_group_required=True
            ),
        ]

        update = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=transfers)
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        # Rollback: NO items should have been added
        assert len(final_state.entities[1].inventory.items) == 0
        # Node 101 should NOT be depleted (rollback preserved charges)
        assert final_state.resource_nodes[101].remaining_charges == 5

    def test_independent_transfers_allow_partial_success(self, entity_with_inventory):
        """Transfers without a group_id are independent — one can fail while another succeeds."""
        state = entity_with_inventory

        node1 = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=5, max_charges=5,
            required_ticks=1
        )
        node2 = ResourceNodeState(
            id=102, kind="HERB_NODE", position=(2, 0),
            yields_item="herb", remaining_charges=0, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node1, 102: node2})

        transfers = [
            # Independent intent 1: valid harvest (succeeds)
            ResourceTransferIntent(
                source_id=101, source_kind="NODE",
                items_add=[ItemStack("iron_ore", 1)],
                transfer_kind="HARVEST",
                group_id=None  # Independent
            ),
            # Independent intent 2: DEPLETED node (fails)
            ResourceTransferIntent(
                source_id=102, source_kind="NODE",
                items_add=[ItemStack("herb", 1)],
                transfer_kind="HARVEST",
                group_id=None  # Independent
            ),
        ]

        update = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1, resource_transfers=transfers)
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        # First succeeded: iron_ore added
        items = {i.item_id for i in final_state.entities[1].inventory.items}
        assert "iron_ore" in items
        # Second failed: no herb
        assert "herb" not in items


# ─── 3. Rejection Reason Recording ──────────────────────────────────────────

class TestTransactionRejectionReasons:
    """Failed transactions must record explicit reasons."""

    def test_depleted_node_records_reason(self, entity_with_inventory):
        state = entity_with_inventory
        node = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=0, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node})

        intent = ResourceTransferIntent(
            source_id=101, source_kind="NODE",
            items_add=[ItemStack("iron_ore", 1)],
            transfer_kind="HARVEST"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is False
        assert result.reason == "SOURCE_DEPLETED"

    def test_full_inventory_records_reason(self, entity_full_inventory):
        state = entity_full_inventory
        node = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=5, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node})

        intent = ResourceTransferIntent(
            source_id=101, source_kind="NODE",
            items_add=[ItemStack("iron_ore", 1)],
            transfer_kind="HARVEST"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is False
        assert result.reason == "INVENTORY_FULL"

    def test_insufficient_gold_records_reason(self, entity_with_inventory):
        state = entity_with_inventory
        # Entity has 50 gold, trying to buy something for 100
        intent = ResourceTransferIntent(
            source_id=301, source_kind="SHOP_BUY",
            items_add=[ItemStack("healing_potion", 1)],
            gold_cost=100,
            transfer_kind="BUY"
        )
        # Add a building to the state so we pass the target check
        from src.core.state import BuildingState, InventoryComponent
        shop = BuildingState(
            id=301, kind="shop", position=(0, 0),
            inventory=InventoryComponent(items=[ItemStack("healing_potion", 1)])
        )
        state = replace(state, buildings={301: shop})
        
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is False
        assert result.reason == "INSUFFICIENT_GOLD"

    def test_missing_corpse_records_reason(self, entity_with_inventory):
        """Missing corpse source records SOURCE_MISSING."""
        state = entity_with_inventory
        intent = ResourceTransferIntent(
            source_id=999, source_kind="CORPSE",
            items_add=[ItemStack("iron_ore", 1)],
            transfer_kind="LOOT"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is False
        assert result.reason == "SOURCE_MISSING"

    def test_unknown_source_kind_records_reason(self, entity_with_inventory):
        state = entity_with_inventory
        intent = ResourceTransferIntent(
            source_id="void", source_kind="INVALID_SOURCE",
            transfer_kind="UNKNOWN"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is False
        assert result.reason == "UNKNOWN_SOURCE_KIND"

    def test_intent_results_propagate_through_pipeline(self, entity_with_inventory):
        """IntentResult objects appear on the refined EntityUpdate after pipeline processing."""
        state = entity_with_inventory
        node = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=0, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node})

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[ResourceTransferIntent(
                    source_id=101, source_kind="NODE",
                    items_add=[ItemStack("iron_ore", 1)],
                    transfer_kind="HARVEST",
                    transaction_id="txn_harvest_101"
                )]
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        ent_upd = refined.entity_updates[1]

        # Intent results should be populated
        # RPG-RES-201: Standard reason propagation
        assert len(ent_upd.intent_results) == 1
        ir = ent_upd.intent_results[0]
        assert ir.accepted is False
        assert ir.reason == "SOURCE_DEPLETED"
        assert ir.transaction_id == "txn_harvest_101"
        assert ir.source_kind == "NODE"


# ─── 4. Source Mutation Conservation ─────────────────────────────────────────

class TestSourceMutationConservation:
    """No source mutation (node depletion, ground item removal, corpse removal)
    occurs without successful destination receipt."""

    def test_node_not_depleted_on_full_inventory(self, entity_full_inventory):
        """Law: Node charges must not decrease if item cannot be added to inventory."""
        state = entity_full_inventory
        node = ResourceNodeState(
            id=101, kind="IRON_NODE", position=(1, 0),
            yields_item="iron_ore", remaining_charges=5, max_charges=5,
            required_ticks=1
        )
        state = replace(state, resource_nodes={101: node})

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[ResourceTransferIntent(
                    source_id=101, source_kind="NODE",
                    items_add=[ItemStack("iron_ore", 1)],
                    transfer_kind="HARVEST"
                )]
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        assert final_state.resource_nodes[101].remaining_charges == 5

    def test_ground_item_not_removed_on_full_inventory(self, entity_full_inventory):
        """Law: Ground item must persist if pickup fails."""
        state = entity_full_inventory
        ground_item = GroundItemState(id=201, item_id="iron_ore", quantity=1, position=(0, 0))
        state = replace(state, ground_items={201: ground_item})

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[ResourceTransferIntent(
                    source_id=201, source_kind="GROUND_ITEM",
                    items_add=[ItemStack("iron_ore", 1)],
                    transfer_kind="PICKUP"
                )]
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        assert 201 in final_state.ground_items

    def test_corpse_not_removed_on_full_inventory(self, entity_full_inventory):
        """Law: Corpse must persist if loot fails."""
        state = entity_full_inventory
        corpse = CorpseState(
            id=301, original_entity_id=99, position=(0, 0),
            items=[ItemStack("iron_ore", 1)], decay_tick=100
        )
        state = replace(state, corpses={301: corpse})

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[ResourceTransferIntent(
                    source_id=301, source_kind="CORPSE",
                    items_add=[ItemStack("iron_ore", 1)],
                    transfer_kind="LOOT"
                )]
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        assert 301 in final_state.corpses

    def test_crafting_materials_not_consumed_on_full_inventory(self, entity_full_inventory):
        """Law: Crafting materials must not be consumed if product cannot be added.
        RPG-RES-200: Capacity enforcement must account for removals.
        """
        state = entity_full_inventory

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[ResourceTransferIntent(
                    source_id="forge",
                    source_kind="CRAFTING",
                    items_add=[ItemStack("steel_sword", 2)],
                    items_remove=[ItemStack("wood", 1)],
                    gold_cost=30,
                    transfer_kind="CRAFT"
                )]
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        # Gold and items should be unchanged
        assert final_state.entities[1].inventory.gold == 50
        assert any(i.item_id == "wood" for i in final_state.entities[1].inventory.items)

    def test_shop_gold_not_spent_if_inventory_full(self, entity_full_inventory):
        """Law: Gold is not deducted if purchased item cannot be stored."""
        state = entity_full_inventory

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                resource_transfers=[ResourceTransferIntent(
                    source_id="shop_1",
                    source_kind="SHOP_BUY",
                    items_add=[ItemStack("healing_potion", 1)],
                    gold_cost=30,
                    transfer_kind="BUY"
                )]
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        final_state = ApplyPath.apply_generation(state, refined)

        # Gold should be unchanged
        assert final_state.entities[1].inventory.gold == 50
        assert not any(i.item_id == "healing_potion" for i in final_state.entities[1].inventory.items)


# ─── 5. Quest Reward Status Atomicity ────────────────────────────────────────

class TestQuestRewardAtomicity:
    """Quest status REWARDED must only be set after successful reward delivery.
    Tested at the resolver level since quest reward intents are generated 
    by authoritative QuestResolutionSystem inside the pipeline."""

    def test_quest_reward_accepted_at_resolver(self, entity_with_inventory):
        """QUEST source_kind produces accepted result for gold+XP (no slots needed)."""
        from src.core.quests import QuestStatus
        state = entity_with_inventory

        intent = ResourceTransferIntent(
            source_id="q1",
            source_kind="QUEST",
            gold_delta=100,
            xp_reward=200,
            transfer_kind="QUEST_REWARD"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is True
        assert result.inventory_update.gold_delta == 100
        assert result.identity_update.evolution_points_delta == 200

    def test_quest_reward_with_item_rejected_on_full_inventory(self, entity_full_inventory):
        """When inventory is full, quest item reward is rejected."""
        state = entity_full_inventory

        intent = ResourceTransferIntent(
            source_id="q1",
            source_kind="QUEST",
            items_add=[ItemStack("legendary_sword", 1)],
            gold_delta=100,
            xp_reward=200,
            transfer_kind="QUEST_REWARD"
        )
        result = ResourceTransactionResolver.resolve(state, state.entities[1], intent)

        assert result.accepted is False
        assert result.reason == "INVENTORY_FULL"

    def test_pipeline_strips_worker_quest_status(self, entity_with_inventory):
        """Pipeline gate strips status_set from worker-submitted QuestUpdate."""
        from src.core.quests import QuestStatus
        state = entity_with_inventory

        update = StateUpdate(entity_updates={
            1: EntityUpdate(
                entity_id=1,
                quest=QuestUpdate(quest_id="q1", status_set=QuestStatus.REWARDED)
            )
        })

        refined = AuthoritativeApplyPipeline.refine(state, update)
        quest_upd = refined.entity_updates[1].quest
        assert quest_upd is not None
        assert quest_upd.status_set is None  # Stripped by gate

    def test_quest_reward_retry_after_freeing_inventory(self, base_state):
        """
        Verify that a quest in REWARD_PENDING state re-emits its reward intent
        every tick until it succeeds (e.g. after inventory is freed).
        """
        from src.core.quests import QuestStatus, QuestState, RewardState
        from src.core.inventory import InventoryComponent, ItemStack
        from src.core.state import StrategicComponent
        
        state = base_state
        # Entity with full inventory
        quest_obj = QuestState(
            id="q1", kind="quest", quest_status=QuestStatus.REWARD_PENDING,
            reward=RewardState(gold=100, xp=50, items=["herb"])
        )
        from src.core.builder import V2EntityBuilder
        e = (V2EntityBuilder(1)
             .kind("HERO")
             .location(0, 0)
             .inventory(gold=50, items=[ItemStack("wood", 1)], max_slots=1)
             .combat(readiness=100.0)
             .strategic(projects={"q1": quest_obj})
             .build())
        state = replace(state, entities={1: e})
        
        # 1. Tick 1: Try to resolve. Should fail because inventory is full.
        # Emit an empty worker update to trigger quest system
        raw_update = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1, quest=QuestUpdate(quest_id="q1"))
        })
        
        # Refine (runs QuestExecutionSystem which emits the intent)
        refined = AuthoritativeApplyPipeline.refine(state, raw_update)
        
        # Check that it stayed in REWARD_PENDING
        upd = refined.entity_updates.get(1)
        assert upd.quest is not None
        assert upd.quest.status_set == QuestStatus.REWARD_PENDING
        
        # Apply the update to get new state
        new_state = ApplyPath.apply_generation(state, refined)
        final_quest = new_state.entities[1].strategic.projects["q1"]
        assert final_quest.quest_status == QuestStatus.REWARD_PENDING
        
        # 2. Tick 2: Free inventory space, then try again
        e_ready = replace(new_state.entities[1],
            inventory=InventoryComponent(max_slots=1, items=[], gold=50)
        )
        state_ready = replace(new_state, entities={1: e_ready}, tick=11)
        
        raw_update_2 = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1, quest=QuestUpdate(quest_id="q1"))
        })
        refined_2 = AuthoritativeApplyPipeline.refine(state_ready, raw_update_2)
        
        # Should now be REWARDED
        upd_2 = refined_2.entity_updates.get(1)
        assert upd_2.quest.status_set == QuestStatus.REWARDED
        
        # Apply and verify final state
        final_state = ApplyPath.apply_generation(state_ready, refined_2)
        final_quest_2 = final_state.entities[1].strategic.projects["q1"]
        assert final_quest_2.quest_status == QuestStatus.REWARDED
        assert any(item.item_id == "herb" for item in final_state.entities[1].inventory.items)
