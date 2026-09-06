"""Idea 22 (Relationship Roles) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

CORRECTION, found during Investigate: a repeated-grudge sequence (>= 3.0) does NOT write
`SocialBond.role` (`RelationshipRole`: NEUTRAL/FRIEND/RIVAL) -- confirmed via grep that
`BondUpdate.role_set` (src/core/updates.py:284) has ZERO real production writers anywhere in
`src/`. The real, live classification mechanism at the grudge>=3.0 threshold is
`SocialMemoryService.check_nemesis_promotion()` (src/systems/social_systems/memory.py:38-50),
which promotes the offending entity id into `SocialComponent.nemesis_ids` -- a structurally
different field than `SocialBond.role`. This test exercises the real, live mechanism instead of
the ticket's own incorrect `SocialBond.role` framing.
"""
from __future__ import annotations

from src.core.models.social import SocialComponent
from src.core.state import EntityState
from src.systems.social_systems.memory import SocialMemoryService


def test_repeated_grudge_at_or_above_3_promotes_to_nemesis():
    social = SocialComponent(grudge_history={7: 3.0}, nemesis_ids=())
    entity = EntityState(id=1, kind="citizen", social=social)

    update = SocialMemoryService.check_nemesis_promotion(entity)

    assert update is not None, "grudge >= 3.0 must produce a real nemesis-promotion update"
    assert 7 in update.nemesis_promotion


def test_grudge_below_3_does_not_promote_to_nemesis():
    social = SocialComponent(grudge_history={7: 2.9}, nemesis_ids=())
    entity = EntityState(id=1, kind="citizen", social=social)

    update = SocialMemoryService.check_nemesis_promotion(entity)

    assert update is None, "grudge below 3.0 must not promote a nemesis (regression guard)"


def test_already_promoted_nemesis_is_not_re_promoted():
    social = SocialComponent(grudge_history={7: 4.0}, nemesis_ids=(7,))
    entity = EntityState(id=1, kind="citizen", social=social)

    update = SocialMemoryService.check_nemesis_promotion(entity)

    assert update is None, "an existing nemesis_ids entry must not be re-promoted"
