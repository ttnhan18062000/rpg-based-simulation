"""The faction treasury is one typed account per region-owner bucket (EXCH-02, src/core/treasury.py)."""
from __future__ import annotations

import pytest

from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent
from src.core.treasury import (
    TreasuryTransfer, apply_transfer, balance, can_pay, treasury_coin, treasury_key, treasury_keys, total_coin,
)
from tests.helpers.scenario import compile_world


def test_there_is_one_key_per_bucket_and_it_keeps_the_existing_name():
    assert treasury_key(Faction.HERO_GUILD) == "faction_hero_guild_gold"
    assert treasury_key(int(Faction.MONSTER_HORDE)) == "faction_monster_horde_gold"
    assert treasury_keys() == {"faction_hero_guild_gold", "faction_monster_horde_gold", "faction_town_council_gold", "faction_neutral_gold"}


def test_a_balance_counts_what_this_tick_already_accepted():
    resources = {treasury_key(Faction.HERO_GUILD): 100.0}
    pending = {treasury_key(Faction.HERO_GUILD): -70.0}
    assert balance(resources, Faction.HERO_GUILD) == 100.0
    assert balance(resources, Faction.HERO_GUILD, pending) == 30.0
    assert can_pay(resources, Faction.HERO_GUILD, 30.0, pending)
    assert not can_pay(resources, Faction.HERO_GUILD, 31.0, pending)  # a second debit in the same tick cannot overspend
    assert not can_pay(resources, Faction.MONSTER_HORDE, 1.0)          # a treasury nobody funded pays nothing


def test_a_transfer_folds_into_the_resource_update_shape():
    out = apply_transfer({}, TreasuryTransfer(int(Faction.HERO_GUILD), -5.0))
    out = apply_transfer(out, TreasuryTransfer(int(Faction.HERO_GUILD), 2.0))
    assert out == {"faction_hero_guild_gold": -3.0}


def test_total_coin_counts_purses_buildings_and_treasuries():
    state = AuthoritativeState(tick=0, seed=1, global_resources={treasury_key(Faction.HERO_GUILD): 10.0, "iron_ore": 99.0},
                               buildings={1: BuildingState(id=1, kind="inn", position=(0, 0), functional=True, inventory=InventoryComponent(gold=7))})
    assert treasury_coin(state.global_resources) == 10.0   # a resource that is not a treasury is not coin
    assert total_coin(state) == 17.0


@pytest.mark.parametrize("world", ["frontier_living_world", "crowded_frontier", "urban_political"])
def test_a_compiled_world_has_the_four_bucket_vaults_and_no_orphan_faction_keys(world):
    state = compile_world(world)
    faction_keys = {k for k in state.global_resources if k.startswith("faction_") and k.endswith("_gold")}
    assert faction_keys <= treasury_keys(), f"orphan vault keys no phase reads: {sorted(faction_keys - treasury_keys())}"
    assert treasury_key(Faction.HERO_GUILD) in faction_keys


def test_a_bucket_starts_with_every_member_factions_declared_gold_once():
    from src.worldbuilding.compiler import get_faction_enum
    from src.worldbuilding.repository import WorldRepository
    spec, ctx = WorldRepository("data/worlds").load_world_with_context("crowded_frontier")
    declared: dict[int, float] = {}
    for f in spec.factions:
        gold = ctx.factions[f.id].starting_gold if f.id in ctx.factions else 1000.0
        bucket = int(get_faction_enum(f.id, context=ctx))
        declared[bucket] = declared.get(bucket, 0.0) + gold
    state = compile_world("crowded_frontier")
    assert {treasury_key(b): g for b, g in declared.items()} == {k: state.global_resources[k] for k in treasury_keys() if k in state.global_resources}
