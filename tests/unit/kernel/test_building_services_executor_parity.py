"""Building services land when their action executes (``building_services.py``), under either executor: the same staged REST, EAT and SELL
actions give the same services from ``LocalSequentialExecutor`` (the state) and ``ConcurrentExecutionAdapter`` (a ``WorkerPacket``), and the
building is only ever READ for its position and kind and its purse snapshot; its coin and stock move through the typed transfer."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, ItemStack
from src.core.work import WorkClass, WorkItem
from src.engine.executor import ConcurrentExecutionAdapter, LocalSequentialExecutor
from src.engine.worker_manager import WorkerManager
from src.platform.rng import DeterministicRNG
from tests.unit.kernel.test_executor_parity import make_profile


def _staged():
    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=100))
    shop = BuildingState(id=11, kind="shop", position=(20.0, 5.0), functional=True, inventory=InventoryComponent(gold=250))
    def worker(eid, pos, gold, items=()):
        e = V2EntityBuilder(eid).kind("worker").properties({"species_id": "human"}).location(*pos).inventory(gold=gold).social(public_reputation=0.0).build()
        return replace(e, inventory=replace(e.inventory, items=list(items)))
    entities = {1: worker(1, (5.0, 6.0), 50), 2: worker(2, (5.0, 4.0), 50), 3: worker(3, (20.0, 6.0), 0, [ItemStack("wood", 4)])}
    return AuthoritativeState(tick=11, seed=42, entities=entities, buildings={10: inn, 11: shop})  # tick 11: off every town cadence


def _items():
    payloads = {1: {"action": "EAT", "target_id": 10}, 2: {"action": "REST", "target_id": 10}, 3: {"action": "SELL", "target_id": 11}}
    return [WorkItem(work_id=f"11:{eid}:ENTITY_ACT", owner_id=eid, work_kind="ENTITY_ACT", work_class=WorkClass.CRITICAL,
                     payload=payload, priority=eid) for eid, payload in payloads.items()]


def _normal(results):
    out = {}
    for r in results:
        if r.entity_id == 0:
            continue
        transfers = [(t.source_kind, t.source_id, t.transfer_kind, t.gold_delta, tuple((s.item_id, s.quantity) for s in t.items_remove)) for t in r.update.resource_transfers]
        out[r.entity_id] = (r.update.readiness_delta, transfers)
    return out


def test_eat_rest_and_sell_land_with_their_action_and_identically_under_both_executors():
    state, rng, profile = _staged(), DeterministicRNG(42), make_profile()
    local = _normal(LocalSequentialExecutor().execute(_items(), state, rng, profile))
    workers = WorkerManager(max_workers=1)
    try:
        concurrent = _normal(ConcurrentExecutionAdapter(workers).execute(_items(), _staged(), DeterministicRNG(42), profile))  # a fresh state: freezing one whose buildings cached their canonical form is not what is under test
    finally:
        workers.shutdown()
    assert local == concurrent
    assert [t[2] for t in local[1][1]] == ["EAT"] and local[1][1][0][1] == 10  # the meal is bought from the inn building (its purse is credited)
    assert [t[2] for t in local[2][1]] == ["REST"]  # a bed
    assert [t[0] for t in local[3][1]] == ["SHOP_SELL"] and local[3][1][0][4] == (("wood", 4),)


def test_deep_freeze_handles_a_dataclass_with_a_cache_field_that_is_not_an_init_argument():
    """The concurrent adapter freezes ``state.buildings``; ``BuildingState`` has an init=False ``_canonical_cache`` and a list inventory, so
    ``replace(obj, **fields)`` used to raise TypeError and no state with a building could run under the concurrent executor."""
    from src.core.immutability import deep_freeze
    frozen = deep_freeze(_staged().buildings)
    assert isinstance(frozen[10].inventory.items, tuple) and frozen[10].inventory.gold == 100
