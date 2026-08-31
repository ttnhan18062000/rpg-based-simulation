"""TCK-20260824-WOUND-HEALING-DECISION -- proves, at the authoritative-state/producer level,
that wounds are permanent in production: a real, non-mocked Kernel.tick_once() loop inflicts a
real wound through the real combat-resolution path, and across the whole run no wound ever
transitions healed=False -> True and no ScarState is ever added.

Deliberately does NOT assert on emitted events (wound_sustained/wound_healed/scar_gained) --
src/observability/event_extractor.py:280-281,302-303 has a separate, independently-discovered
bug (isinstance(x, list) instead of isinstance(x, (list, tuple)), tracked by
TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND) that silently drops ALL wound/scar
event extraction once state is committed as a tuple by the real apply path (which it always is,
confirmed by the isinstance(wounds, tuple) assertion below). Relying on events here would make
this test's pass/fail depend on an unrelated bug being fixed first. This test instead reads
kernel.state.entities[...].combat.wounds/.scars directly -- the real, frozen, authoritative state
-- which is unaffected by that bug.
"""
from dataclasses import replace

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, EntityRole
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

TICKS = 40
SEED = 42


def _make_combatant(eid, pos, faction_id, faction_enum, atk, hp=100, def_stat=1):
    return (
        V2EntityBuilder(eid)
        .kind("actor")
        .location(*pos)
        .identity(faction=faction_enum, role=EntityRole.HERO, properties={"faction_id": faction_id})
        .combat(hp=hp, max_hp=hp, atk=atk, def_stat=def_stat, attack_range=2, readiness=100.0, alive=True)
        .lifecycle(active=True)
        .build()
    )


def test_wound_healed_and_scar_gained_have_zero_production_producers():
    """Real Kernel.tick_once() loop, real combat path, real authoritative state.

    - Attacker (hero_guild) vs. defender (goblin_warband), hostile factions, adjacent,
      ENABLE_COMBAT_ENGAGEMENT ON. Attacker ATK (80) vs. defender max_hp (100) is tuned so a real
      hit clears the 25%-max-HP wound threshold (src/engine/combat.py:607,
      `damage > defender.combat.max_hp * 0.25`).
    - Deterministic at seed 42: a real wound is genuinely inflicted at tick 9 (confirmed directly,
      reproducibly, via the exact fixture below) -- proving combat/wounding is live in this test,
      not just theoretically gated on.
    - Across the entire run: no wound ever transitions healed=False -> True, and no ScarState is
      ever added to any entity -- proving zero production producers exist for
      `WoundUpdate.wounds_heal`/`scars_add`, independent of ENABLE_COMBAT_ENGAGEMENT's gate state.
    """
    attacker = _make_combatant(1, (1.0, 1.0), "hero_guild", Faction.HERO_GUILD, atk=80, hp=100, def_stat=1)
    defender = _make_combatant(2, (2.0, 1.0), "goblin_warband", Faction.MONSTER_HORDE, atk=1, hp=100, def_stat=1)

    state = AuthoritativeState(tick=0, seed=SEED, entities={1: attacker, 2: defender})
    state = replace(state, feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"})

    rng = DeterministicRNG(SEED)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True, "no_replay": True})

    saw_a_wound = False
    any_wound_ever_healed = False
    any_scar_ever_added = False

    try:
        for _ in range(TICKS):
            kernel.tick_once()
            for eid in (1, 2):
                entity = kernel.state.entities.get(eid)
                if entity is None:
                    continue

                wounds = entity.combat.wounds
                scars = entity.combat.scars

                # The real, authoritative apply path (WoundPatch.apply, src/engine/patches.py)
                # always commits these fields as tuples -- assert this holds so this test is
                # genuinely exercising the same real state shape event_extractor.py's bug
                # silently mishandles, not a hand-constructed list bypassing it.
                assert isinstance(wounds, tuple)
                assert isinstance(scars, tuple)

                if wounds:
                    saw_a_wound = True
                    if any(w.healed for w in wounds):
                        any_wound_ever_healed = True
                if scars:
                    any_scar_ever_added = True
    finally:
        kernel.shutdown()

    assert saw_a_wound, (
        "no wound was ever inflicted across the run -- fixture/threshold drifted, this test can "
        "no longer distinguish 'combat produces wounds but never heals them' from 'combat never "
        "produced anything at all'"
    )
    assert not any_wound_ever_healed, (
        "a wound transitioned healed=False -> True in production state -- this would mean a "
        "healing producer now exists and the wound-permanence decision "
        "(TCK-20260824-WOUND-HEALING-DECISION) needs to be revisited, not silently invalidated"
    )
    assert not any_scar_ever_added, (
        "a ScarState was added to production state -- this would mean a scar-formation producer "
        "now exists and the wound-permanence decision needs to be revisited, not silently "
        "invalidated"
    )
