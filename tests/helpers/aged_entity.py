"""An entity as it looks after a long life: many finished quests, resolved blockers, closed contracts and items carrying properties.

Used to prove the entity read model does not grow with world age (TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL):
the live part is constant while the terminal records pile up.
"""
from __future__ import annotations

from typing import Any, Dict

from src.core.builder import V2EntityBuilder
from src.core.models.quests import QuestKind, QuestState, QuestStatus, RewardState
from src.core.state import EntityState, ItemStack
from src.core.strategic import (
    BlockerKind,
    BlockerState,
    ContractKind,
    ContractState,
    ContractStatus,
    ProjectKind,
    ProjectStatus,
)


def aged_entity(entity_id: int = 1, terminal_quests: int = 0, resolved_blockers: int = 0, closed_contracts: int = 0, live_quests: int = 2,
                unresolved_blockers: int = 2, open_contracts: int = 1, item_properties: int = 0) -> EntityState:
    """One entity with a constant live core and ``terminal_*`` finished records."""
    projects: Dict[str, Any] = {}
    for i in range(live_quests):
        projects[f"q_live_{i}"] = QuestState(id=f"q_live_{i}", kind=ProjectKind.QUEST, status=ProjectStatus.ACTIVE, created_tick=10_000 + i, quest_kind=QuestKind.HUNT,
                                             quest_status=QuestStatus.ACTIVE, goal_value=5.0, current_value=1.0, name=f"live {i}", reward=RewardState(xp=5, gold=3, items=["x"]))
    for i in range(terminal_quests):
        projects[f"q_done_{i}"] = QuestState(id=f"q_done_{i}", kind=ProjectKind.QUEST, status=ProjectStatus.COMPLETED if i % 2 else ProjectStatus.ABANDONED, created_tick=i,
                                             quest_kind=QuestKind.GATHER, quest_status=QuestStatus.COMPLETED, goal_value=5.0, current_value=5.0, name=f"finished quest {i}",
                                             reward=RewardState(xp=10 + i, gold=7, items=["iron_ore", "bread"]))
    blockers: Dict[str, BlockerState] = {}
    for i in range(unresolved_blockers):
        blockers[f"b_open_{i}"] = BlockerState(id=f"b_open_{i}", kind=BlockerKind.MATERIAL, subject=f"ore_{i}", severity=0.5, resolved=False)
    for i in range(resolved_blockers):
        blockers[f"b_done_{i}"] = BlockerState(id=f"b_done_{i}", kind=BlockerKind.MATERIAL, subject=f"ore_done_{i}", severity=0.3, resolved=True)
    contracts: Dict[str, ContractState] = {}
    for i in range(open_contracts):
        contracts[f"c_open_{i}"] = ContractState(id=f"c_open_{i}", kind=ContractKind.PROTECTION, source_id=entity_id, target_id=entity_id + 1, status=ContractStatus.ACTIVE, created_tick=10_000 + i)
    for i in range(closed_contracts):
        contracts[f"c_done_{i}"] = ContractState(id=f"c_done_{i}", kind=ContractKind.LOAN, source_id=entity_id, target_id=entity_id + 1,
                                                 status=ContractStatus.FULFILLED if i % 2 else ContractStatus.EXPIRED, created_tick=i)
    items = [ItemStack(item_id="sword", quantity=1, properties={f"k{j}": "v" * 40 for j in range(item_properties)})] if item_properties else [ItemStack(item_id="bread", quantity=2)]
    return V2EntityBuilder(entity_id).kind("worker").location(5.0, 5.0).inventory(items=items, gold=50).strategic(projects=projects, blockers=blockers, contracts=contracts).build()
