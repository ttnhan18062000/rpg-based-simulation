"""Idea 39 (Affiliation Change) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

`IdentityUpdate.faction_set` (M6, TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE) is the real,
authoritative faction-mutation primitive. `src/systems/social_systems/relationships.py` (the sole
authoritative SocialBond write path) has zero references to `identity.faction`/`faction_set`
(confirmed via grep) -- a faction change never touches any SocialBond, so old-faction bonds do not
auto-degrade, exactly as this ticket's own text expects.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.models.social import SocialBond
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.apply import ApplyPath


def test_faction_change_does_not_auto_degrade_existing_social_bonds():
    entity = (
        V2EntityBuilder(1)
        .location(0.0, 0.0)
        .identity(faction=Faction.TOWN_COUNCIL)
        .social(bonds={2: SocialBond(target_id=2, sentiment=0.7, familiarity=0.8)})
        .build()
    )
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    update = StateUpdate(entity_updates={1: EntityUpdate(
        entity_id=1, identity=IdentityUpdate(faction_set=Faction.NEUTRAL),
    )})
    final_state = ApplyPath.apply_partial(state, update)

    final_entity = final_state.entities[1]
    assert final_entity.identity.faction == Faction.NEUTRAL, "faction must actually change"
    bond = final_entity.social.bonds[2]
    assert bond.sentiment == 0.7, "existing bond sentiment must be untouched by a faction change"
    assert bond.familiarity == 0.8, "existing bond familiarity must be untouched by a faction change"
