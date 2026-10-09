"""A bed, a meal and a sale land with their action, on whatever tick the decision was made (``building_services.py``); the cadence-gated town
phase attaches none, so a service is never delivered twice; a hunger project that visited a shop ends once nothing is left to sell."""
import pytest

from src.core.state import ItemStack
from src.core.strategic import GoalKind
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.domain.action_router import ActionRouter
from src.engine.town_resolution import TownResolutionSystem
from src.engine.building_arrival import finished_visit
from tests.unit.world.test_sell_is_a_chosen_act import _world


@pytest.mark.parametrize("tick", [1, 3, 7, 11, 13, 17])
def test_the_sale_lands_on_any_tick_not_only_on_the_town_cadence(tick):
    from dataclasses import replace
    state, ent, shop = _world([ItemStack("wood", 4)])
    state = replace(state, tick=tick)
    out = ActionRouter.execute_action(ent, {"action": "SELL", "target_id": 10}, tick, None, state)[1]
    assert [t.source_kind for t in out.resource_transfers] == ["SHOP_SELL"]


@pytest.mark.parametrize("tick", [1, 10, 20, 30])
def test_the_town_phase_attaches_no_service_so_none_is_delivered_twice(tick):
    from dataclasses import replace
    state, ent, shop = _world([ItemStack("wood", 4)])
    state = replace(state, tick=tick)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=TaskUpdate(
        work_kind_set="ENTITY_ACT", payload_set={"action": "SELL", "target_id": 10}))})
    out = TownResolutionSystem.resolve(state, update).entity_updates.get(1)
    assert out is None or not out.resource_transfers


def _hunger_project(target):
    objective = ObjectiveState(id="hunger_10", kind=ObjectiveKind.REACH_LOCATION, target=str(target), target_position=(5.0, 5.0),
                               status=ObjectiveStatus.ACTIVE)
    return ProjectState(id="proj_hunger_1", kind=GoalKind.HUNGER, status=ProjectStatus.ACTIVE,
                        score=100.0, objectives=[objective], active_objective_id=objective.id)


def test_a_shop_visit_stays_open_while_a_sale_remains_and_ends_when_nothing_is_left_to_sell():
    from dataclasses import replace
    state, ent, shop = _world([ItemStack("wood", 4)])
    project = _hunger_project(10)
    assert finished_visit(state, ent, project, shop) is None  # still something to sell
    empty = replace(ent, inventory=replace(ent.inventory, items=[]))
    done = finished_visit(state, empty, project, shop).strategic
    assert done.projects_add_or_update[0].status == ProjectStatus.COMPLETED and done.current_project_id_set == ""
    assert done.projects_add_or_update[0].objectives[0].status == ObjectiveStatus.RESOLVED


def test_the_tactical_arrival_at_a_shop_sells_first_and_ends_the_visit_when_nothing_remains():
    from dataclasses import replace
    from src.engine.tactical import TacticalDecisionSystem
    state, ent, shop = _world([ItemStack("wood", 4)])
    project = _hunger_project(10)
    strategic = replace(ent.strategic, projects={project.id: project}, current_project_id=project.id, current_objective_id="hunger_10")
    holder = replace(ent, strategic=strategic)
    state = replace(state, entities={1: holder})
    sells = TacticalDecisionSystem.evaluate_entity_intent(state, holder)
    assert sells.task.payload_set["action"] == "SELL"
    empty = replace(holder, inventory=replace(holder.inventory, items=[]))
    ends = TacticalDecisionSystem.evaluate_entity_intent(replace(state, entities={1: empty}), empty)
    assert ends.strategic.current_project_id_set == "" and ends.task is None


@pytest.mark.parametrize("kind,action", [("inn", "EAT"), ("inn", "REST"), ("home", "REST")])
@pytest.mark.parametrize("gold", [50, 3, 0])
def test_every_building_service_payment_is_credited_to_the_building_that_served_it(kind, action, gold):
    """EXCH-02: the payer's debit equals the building's credit for every TOWN_SERVICE a building serves (what was actually paid when the
    subject holds less than the price: the charge is clamped at what it holds); no coin vanishes."""
    from dataclasses import replace

    from src.core.conservation import ResourceTransactionResolver
    state, ent, shop = _world([])
    building = replace(shop, kind=kind)
    state = replace(state, buildings={10: building})
    ent = replace(ent, inventory=replace(ent.inventory, gold=gold))
    update = ActionRouter.execute_action(ent, {"action": action, "target_id": 10}, state.tick, None, state)[1]
    (charge,) = [t for t in update.resource_transfers if t.source_kind == "TOWN_SERVICE"]
    result = ResourceTransactionResolver.resolve(state, ent, charge, reservations={})
    assert result.accepted
    paid = min(gold, -charge.gold_delta)  # the inventory clamp at 0 means a broke subject pays only what it holds
    if paid == 0:
        assert result.building_update is None  # nothing was paid, nothing to credit
        return
    assert charge.source_id == 10 and result.building_update.building_id == 10
    assert result.building_update.inventory.gold_delta == paid  # the building's credit is what the payer actually paid
    assert result.inventory_update.gold_delta == charge.gold_delta  # the payer's debit (apply clamps it at what it holds)


@pytest.mark.parametrize("gold", [50, 4, 0])
def test_a_repair_at_the_blacksmith_in_reach_is_credited_to_that_blacksmith(gold):
    from dataclasses import replace

    from src.core.conservation import ResourceTransactionResolver
    state, ent, shop = _world([])
    smith = replace(shop, kind="blacksmith")
    state = replace(state, buildings={10: smith})
    ent = replace(ent, inventory=replace(ent.inventory, gold=gold), equipment=replace(ent.equipment, durability={"weapon": 60.0}),
                   combat=replace(ent.combat, readiness=100.0))
    update = ActionRouter.execute_action(ent, {"action": "REPAIR"}, state.tick, None, state)[1]
    (charge,) = [t for t in update.resource_transfers if t.source_kind == "TOWN_SERVICE"]
    assert charge.source_id == 10  # the payee is the blacksmith in reach, not an unnamed "BLACKSMITH"
    result = ResourceTransactionResolver.resolve(state, ent, charge, reservations={})
    if gold < charge.gold_cost:
        assert not result.accepted  # an unaffordable repair is refused, no coin moves
        return
    debit = min(gold, charge.gold_cost - charge.gold_delta)
    assert result.accepted
    if debit == 0:
        assert result.building_update is None
    else:
        assert result.building_update.inventory.gold_delta == debit  # the payee's credit equals what the payer was debited


@pytest.mark.parametrize("gold", [0, 3, 50])
def test_a_hungry_subject_at_the_inn_eats_whatever_it_holds_while_free_meals_stand(gold):
    """Owner decision 44: free meals stay on, so the arrival dispatch at an inn is a meal for every subject, broke ones included (an earlier
    cut dispatched a shift of work to a broke subject, which fed no one: wildlife ever-ate fell from 2.6 to 0.4 per run)."""
    from dataclasses import replace

    from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
    from src.engine.building_arrival import building_arrival_update
    state, ent, shop = _world([], gold=gold)
    inn = replace(shop, kind="inn")
    state = replace(state, buildings={10: inn})
    ent = replace(ent, biological=replace(ent.biological, hunger=70.0))
    project = _hunger_project(10)
    assert building_arrival_update(state, ent, project, 10).task.payload_set["action"] == "EAT"
