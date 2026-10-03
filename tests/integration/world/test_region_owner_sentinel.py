"""Region-owner unowned-sentinel decoding.

TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW.

`WorldUpdate.owner_faction_id_set=None` already means "no change", so a liberation
signals clear-to-unowned with the in-band `NO_OWNER_SENTINEL` (-1). Nothing decoded it,
so -1 was persisted as a region's durable `owner_faction_id`, where `Faction`-keyed
lookups raise KeyError (Faction has values 0-3 only).
"""
from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, NO_OWNER_SENTINEL, decode_owner_faction_id_set
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, EntityRole, PassiveDeathCause
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.engine.pipeline import AuthoritativeApplyPipeline


def _invader_region_with_dying_monster(tick, influence=46.0):
    """A MONSTER_HORDE-owned region one monster death away from liberation (+50).

    The death is staged as a passive cause rather than a raw CombatUpdate:
    TrustBoundaryPhase strips the latter, so a CombatUpdate-driven death never reaches
    resolve_lifecycle through refine().
    """
    region = RegionState(
        id="forest", name="Grim Forest", bounds=(0, 0, 100, 100),
        influence=influence, owner_faction_id=Faction.MONSTER_HORDE,
    )
    monster = (
        V2EntityBuilder(1).kind("monster").location(50, 50)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .combat(hp=10, alive=True).build()
    )
    monster = replace(monster, lifecycle=replace(
        monster.lifecycle,
        passive_death_cause=PassiveDeathCause.STARVATION,
        passive_death_cause_tick=tick,
    ))
    return region, monster


def test_decode_owner_faction_id_set_maps_sentinel_but_preserves_hero_guild():
    """HERO_GUILD is int 0, so the decoder must not conflate it with the sentinel."""
    assert decode_owner_faction_id_set(NO_OWNER_SENTINEL) is None
    assert decode_owner_faction_id_set(None) is None
    assert decode_owner_faction_id_set(Faction.HERO_GUILD) == Faction.HERO_GUILD
    assert decode_owner_faction_id_set(Faction.MONSTER_HORDE) == Faction.MONSTER_HORDE


def test_liberation_clears_owner_to_none_not_raw_sentinel():
    """A liberation persists owner_faction_id=None, never the raw -1 sentinel.

    Logic ID: WORLD-107 (Sovereignty shift)
    """
    region, monster = _invader_region_with_dying_monster(tick=5)
    state = AuthoritativeState(tick=5, seed=42, entities={1: monster},
                              regions={"forest": region})

    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())
    final = ApplyPath.apply_generation(state, refined, next_tick=6)

    owner = final.regions["forest"].owner_faction_id
    assert owner != NO_OWNER_SENTINEL, (
        f"raw sentinel persisted as durable owner_faction_id: {owner!r}"
    )
    assert owner is None, f"expected unowned after liberation, got {owner!r}"


def test_liberated_region_survives_a_later_tax_tick_without_keyerror():
    """A region liberated on one tick must not crash the pipeline on a LATER tax tick.

    Two ticks are required to reach the crash. On the liberating tick, taxation still
    sees the old valid owner, so the bad value is only persisted at apply. It is the
    NEXT tax tick that reads it: town_resolution guards taxation with
    `owner_faction_id is not None`, which -1 satisfies, then indexes a Faction-keyed
    dict -> KeyError(-1). Faction has values 0-3 only.
    Logic ID: TOWN-138 (Regional Taxation)
    """
    cadence = SystemCadence(town_resolution=50)  # tax every 100 ticks
    region, monster = _invader_region_with_dying_monster(tick=100)
    taxable = (
        V2EntityBuilder(2).kind("peasant").location(51, 51)
        .identity(role=EntityRole.HERO, faction=Faction.NEUTRAL)
        .inventory(gold=100).combat(hp=10, alive=True).build()
    )
    state = AuthoritativeState(
        tick=100, seed=42, entities={1: monster, 2: taxable},
        regions={"forest": region},
        global_resources={"faction_hero_guild_gold": 0.0},
    )

    # Tick 100: the liberation itself. Taxation here still sees MONSTER_HORDE, so this
    # tick cannot crash. Deliberately NOT asserted on -- the persisted-value invariant is
    # test_liberation_clears_owner_to_none_not_raw_sentinel's job. Asserting it here would
    # short-circuit before tick 200 and this test would never exercise the crash at all.
    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate(), cadence=cadence)
    mid = ApplyPath.apply_generation(state, refined, next_tick=101, cadence=cadence)

    # Tick 200: the next tax tick now READS the persisted owner. Pre-fix this raised
    # KeyError(-1) out of town_resolution's faction_keys lookup.
    mid = replace(mid, tick=200)
    refined_2 = AuthoritativeApplyPipeline.refine(mid, StateUpdate(), cadence=cadence)
    final = ApplyPath.apply_generation(mid, refined_2, next_tick=201, cadence=cadence)

    # The region is legitimately re-conquered to HERO_GUILD here: it is now unowned with
    # influence >= +50, so world_dynamics' unconditional sweep claims it. That is correct
    # and not what this test guards. The invariant is that the owner is never the raw
    # sentinel and that reaching a tax tick does not raise.
    owner = final.regions["forest"].owner_faction_id
    assert owner != NO_OWNER_SENTINEL, f"sentinel survived into tick 200: {owner!r}"
    assert owner is None or owner in set(Faction), f"owner is not a valid faction: {owner!r}"
