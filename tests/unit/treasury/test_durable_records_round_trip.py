"""The new durable records survive the places state is written down: the canonical hash and checkpoint data, and the presenter view (EXCH-02)."""
from __future__ import annotations

from dataclasses import replace

from src.api.presenters.state_presenter import StatePresenter
from src.core.models.world_records import CorpseState, OwedRecord
from src.core.state import AuthoritativeState, ItemStack, RegionState
from src.engine.checkpoint import CanonicalStateHasher


def _state(**kw):
    return AuthoritativeState(tick=3, seed=1, **kw)


def test_a_bodys_coin_is_part_of_the_state_hash_and_the_checkpoint_data():
    body = CorpseState(id=9, original_entity_id=1, position=(1.0, 1.0), items=[ItemStack("wood", 1)], decay_tick=50, gold=7)
    richer = replace(body, gold=8)
    assert CanonicalStateHasher.get_hash(_state(corpses={9: body})) != CanonicalStateHasher.get_hash(_state(corpses={9: richer}))
    assert CanonicalStateHasher.to_canonical_data(_state(corpses={9: body}))["corpses"]["9"]["gold"] == 7


def test_an_owed_debt_is_part_of_the_state_hash_and_the_checkpoint_data():
    debt = OwedRecord(id="owed:q:1", creditor_id=1, debtor_faction=0, amount=30, posted_tick=2)
    assert CanonicalStateHasher.get_hash(_state(owed={debt.id: debt})) != CanonicalStateHasher.get_hash(_state())
    assert CanonicalStateHasher.to_canonical_data(_state(owed={debt.id: debt}))["owed"][debt.id]["amount"] == 30


def test_a_regions_tax_share_is_part_of_the_state_hash_and_the_region_view():
    taxed = RegionState(id="r", name="R", bounds=(0, 0, 5, 5), owner_faction_id=0, tax_share=0.1)
    free = replace(taxed, tax_share=0.0)
    assert CanonicalStateHasher.get_hash(_state(regions={"r": taxed})) != CanonicalStateHasher.get_hash(_state(regions={"r": free}))
    assert StatePresenter.present_region(taxed)["tax_share"] == 0.1


def test_the_full_view_shows_bodies_and_debts():
    body = CorpseState(id=9, original_entity_id=1, position=(1.0, 1.0), items=[], decay_tick=50, gold=7)
    debt = OwedRecord(id="owed:q:1", creditor_id=1, debtor_faction=0, amount=30, posted_tick=2)
    view = StatePresenter.present_full(_state(corpses={9: body}, owed={debt.id: debt}))
    assert view["corpses"][0]["gold"] == 7 and view["owed"][0]["amount"] == 30 and view["owed"][0]["creditor_id"] == 1
