"""TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY: a way is open iff the inn would actually deliver the service now (AGENCY-03,
SURV-07 row 27). One admission function (``service_admission.admits``) is read by the service and by every "open" test; the payment law is one
constant. The ATOMIC law is exercised here by patching that constant; main keeps CLAMP."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.ways import WayKind, ways_in_reach
from src.ai.goals.scorers import EatScorer, SleepScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.engine import service_admission
from src.engine.appraisal import can_use_inn_meal
from src.engine.building_services import service_building, service_delta
from src.engine.domain.core_actions import eat_update
from src.engine.service_admission import PaymentLaw, admits
from src.engine.service_prices import EAT_PRICE_GOLD, REST_PRICE_GOLD

PRICES = {"EAT": EAT_PRICE_GOLD, "REST": REST_PRICE_GOLD}
GOLDS = (0, 1, EAT_PRICE_GOLD - 1, EAT_PRICE_GOLD, EAT_PRICE_GOLD + 1, REST_PRICE_GOLD - 1, REST_PRICE_GOLD, REST_PRICE_GOLD + 7)
TICKET = "TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT"


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _world(species_id="human", gold=20, kind="inn", at=(5.0, 5.0), **bio):
    ent = V2EntityBuilder(1).kind("worker").properties({"species_id": species_id}).location(*at).inventory(gold=gold).build()
    ent = replace(ent, biological=replace(ent.biological, **bio))
    buildings = {10: BuildingState(id=10, kind=kind, position=(5.0, 5.0), functional=True)}
    state = AuthoritativeState(tick=1, seed=1, world_time=1000, entities={1: ent}, town_tiles={(5, 5)}, building_tiles={(5, 5): kind}, buildings=buildings)
    return state, ent


def _law(monkeypatch, law):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", law)


def test_main_keeps_the_clamp_law():
    assert service_admission.SERVICE_PAYMENT_LAW is PaymentLaw.CLAMP


@pytest.mark.parametrize("law", list(PaymentLaw))
@pytest.mark.parametrize("action", ["EAT", "REST"])
@pytest.mark.parametrize("gold", GOLDS)
def test_admission_equals_what_the_service_really_delivers_for_a_coin_keeping_subject(monkeypatch, law, action, gold):
    _law(monkeypatch, law)
    state, ent = _world(gold=gold, hunger=60.0, sleep_debt=60.0)
    delivered = service_delta(state, ent, action, 1) is not None
    assert admits(ent, action) is delivered
    assert delivered is (law is PaymentLaw.CLAMP or gold >= PRICES[action])


@pytest.mark.parametrize("law", list(PaymentLaw))
@pytest.mark.parametrize("action", ["EAT", "REST"])
@pytest.mark.parametrize("gold", GOLDS)
def test_gold_is_never_debited_without_the_service_in_the_same_update(monkeypatch, law, action, gold):
    """Under CLAMP partial payment is the law; what must never happen is gold leaving a subject with no delivery (the N1 t587 shape)."""
    _law(monkeypatch, law)
    state, ent = _world(gold=gold)
    delta = service_delta(state, ent, action, 1)
    if delta is None:
        return  # nothing delivered and nothing charged: no transfer exists to debit
    charge = delta.resource_transfers[0]
    assert charge.gold_delta < 0 or charge.gold_cost > 0
    if action == "EAT":
        assert delta.biological is not None and delta.biological.hunger_delta < 0
    else:
        assert delta.readiness_delta > 0


def test_a_diet_without_prepared_food_is_not_admitted_to_the_meal_whatever_it_holds():
    _, plant_eater = _world("small_plant_eater", gold=100)
    assert not can_use_inn_meal(plant_eater) and not admits(plant_eater, "EAT")
    _, person = _world("human", gold=0)
    assert can_use_inn_meal(person) and admits(person, "EAT")


def test_the_action_side_diet_gate_agrees_with_the_admission_diet_branch():
    for species in ("human", "small_plant_eater", "wolf"):
        _, ent = _world(species, gold=100)
        fed = eat_update(ent, 1).biological is not None
        assert fed is admits(ent, "EAT", PaymentLaw.CLAMP)


@pytest.mark.parametrize("law", list(PaymentLaw))
@pytest.mark.parametrize("gold", (0, EAT_PRICE_GOLD - 1, EAT_PRICE_GOLD))
def test_ways_in_reach_and_the_eat_scorer_agree_with_the_service_on_the_inn_meal(monkeypatch, law, gold):
    _law(monkeypatch, law)
    state, ent = _world(gold=gold, at=(2.0, 5.0), hunger=60.0)
    inn_open = WayKind.INN_MEAL in ways_in_reach(ent, state)
    on_the_inn_tile = replace(ent, navigation=replace(ent.navigation, position=(5.0, 5.0)))
    assert inn_open is admits(ent, "EAT") is (service_delta(state, on_the_inn_tile, "EAT", 1) is not None)
    score = EatScorer().score(ent, state)
    assert (score.target_id == "10") is inn_open


@pytest.mark.parametrize("law,walks", [(PaymentLaw.CLAMP, True), (PaymentLaw.ATOMIC, False)])
def test_a_broke_tired_subject_is_offered_the_inn_bed_iff_rest_would_deliver_it(monkeypatch, law, walks):
    """f400 (TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR): live on main (CLAMP: it walks to the bed); under the atomic law (D73) it rests in place."""
    _law(monkeypatch, law)
    state, ent = _world(gold=0, at=(2.0, 5.0), sleep_debt=60.0)
    score = SleepScorer().score(ent, state)
    on_the_inn_tile = replace(ent, navigation=replace(ent.navigation, position=(5.0, 5.0)))
    assert (score.target_id == "10") is walks is (service_delta(state, on_the_inn_tile, "REST", 1) is not None)
    if not walks:
        assert score.target_pos is None


def test_known_gap_admission_ignores_keeps_coin_while_the_service_refuses_a_non_coin_subject():
    """Pinned, not xfail (designer ruling A, 2026-10-29): ``admits`` is True for a non-coin subject that ``service_building`` refuses. Tracked in
    %s; when that ticket puts keeps_coin into admission this test is rewritten to assert agreement."""  % TICKET
    state, ent = _world("small_plant_eater", gold=100)
    assert admits(ent, "REST") is True
    assert service_building(state, ent, "REST") is None
