"""TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE (AC #3) — next-tick-boundary legality
semantics for a faction mutation.

AuthoritativeApplyPipeline.refine() runs "action_routing" (src/engine/pipeline.py:297) --
where LegalityServiceV2.verify_attack_legality() is evaluated -- strictly before "groups"
(src/engine/pipeline.py:402), where PartyLifecycleService.check_defection()'s
IdentityUpdate(faction_set=...) trigger lives. Both phases read the same frozen `state`
argument, so a same-tick defection cannot retroactively change a legality decision this same
tick's "action_routing" phase already made against the pre-defection faction: the new faction
only becomes visible to legality reads starting with the next tick's (or, as proven directly
here, the post-apply state's) "action_routing" pass. See docs/world/affiliation_mutation.md.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState, GroupRecord
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.engine.legality import LegalityServiceV2
from src.systems.social_systems.party_lifecycle import PartyLifecycleService


def _entity(eid, faction, pos):
    entity = (
        V2EntityBuilder(eid)
        .kind("hero")
        .identity(faction=faction)
        .combat(hp=100, max_hp=100, attack_range=1, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    return replace(entity, navigation=replace(entity.navigation, position=pos))


def test_faction_change_mid_tick_legality_semantics():
    attacker = _entity(1, Faction.HERO_GUILD, pos=(10, 10))
    defector = _entity(2, Faction.MONSTER_HORDE, pos=(10, 11))  # Manhattan dist 1, melee range

    state = AuthoritativeState(tick=1, seed=1, entities={1: attacker, 2: defector})

    # Same-tick "action_routing" read (src/engine/pipeline.py:297): hostile factions, legal.
    legal_before, reason_before = LegalityServiceV2.verify_attack_legality(attacker, defector, state)
    assert legal_before is True
    assert reason_before == ReasonCode.LEGAL

    # Same-tick "groups" phase (src/engine/pipeline.py:402) produces a real defection trigger.
    group = GroupRecord(
        id=1, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0),
        grievance_log=("g1", "g2", "g3"),
    )
    _, _, entity_update = PartyLifecycleService.check_defection(group, defector, tick=1)
    assert entity_update.identity.faction_set == Faction.NEUTRAL

    # The frozen `state` handed to "action_routing" is unaffected by "groups"'s mutation this
    # same tick -- re-checking against it still resolves against the pre-defection faction.
    legal_same_tick, reason_same_tick = LegalityServiceV2.verify_attack_legality(
        attacker, state.entities[2], state
    )
    assert legal_same_tick is True
    assert reason_same_tick == ReasonCode.LEGAL

    # Only the applied (next-tick-boundary) state reflects the new faction.
    update = StateUpdate(entity_updates={2: entity_update})
    next_state = ApplyPath.apply_partial(state, update)
    assert next_state.entities[2].identity.faction == Faction.NEUTRAL

    legal_after, reason_after = LegalityServiceV2.verify_attack_legality(
        attacker, next_state.entities[2], next_state
    )
    assert legal_after is False
    assert reason_after == ReasonCode.FRIENDLY_FIRE_ILLEGAL
