"""Idea 36/40 (Clan) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

No registered corpus world carries real `ClanState` content (`orc_clan_territory.yaml` defines
only `factions: ["orc_clan"]`, a naming coincidence, not the ClanState mechanic -- re-confirmed,
same finding as this M9 batch's own immediately-prior sibling ticket,
CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS). Unit-tier hand-seeded content is idiomatic here per
`corpus_tier_taxonomy.md`.

CORRECTION, found during Investigate: the real party-defection trigger
(`PartyLifecycleService.check_defection()` via `GroupPhase.resolve()`) only degrades
`ClanState.clan_reputation` (confirmed by the M9 sibling ticket above) -- it does NOT remove the
defector from `ClanState.member_entity_ids`. Membership removal is a real, separate, correctly-
implemented pure function, `ClanLifecycleService.process_leave()`
(src/systems/social_systems/clan_lifecycle.py:52-75), but it has ZERO real production callers
today (confirmed via grep) -- a disclosed "built, not yet wired" gap, matching this session's
now-repeated pattern, not something this ticket fixes. This test proves the real membership-count
setup and the real, correct (but not-yet-live-triggered) `process_leave()` mechanics directly.
"""
from __future__ import annotations

from src.core.state import AuthoritativeState, ClanState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.systems.social_systems.clan_lifecycle import ClanLifecycleService


def _two_clans_of_four() -> AuthoritativeState:
    clans = {
        "clan_a": ClanState(clan_id="clan_a", name="Clan A", member_entity_ids=(1, 2, 3, 4), clan_reputation=1.0),
        "clan_b": ClanState(clan_id="clan_b", name="Clan B", member_entity_ids=(5, 6, 7, 8), clan_reputation=1.0),
    }
    return AuthoritativeState(tick=0, seed=1, clans=clans)


def test_two_clans_of_four_members_each():
    state = _two_clans_of_four()
    assert len(state.clans["clan_a"].member_entity_ids) == 4
    assert len(state.clans["clan_b"].member_entity_ids) == 4
    assert set(state.clans["clan_a"].member_entity_ids).isdisjoint(state.clans["clan_b"].member_entity_ids)


def test_process_leave_removes_exactly_one_member_through_the_real_apply_path():
    state = _two_clans_of_four()

    update, event = ClanLifecycleService.process_leave(clan_id="clan_a", entity_id=2, tick=1)
    final_state = ApplyPath.apply_partial(state, StateUpdate(clan_updates=[update]))

    final_clan_a = final_state.clans["clan_a"]
    assert final_clan_a.member_entity_ids == (1, 3, 4), (
        "process_leave must remove exactly entity_id 2 and leave the other 3 members intact"
    )
    assert event.clan_id == "clan_a"
    assert event.entity_id == 2
