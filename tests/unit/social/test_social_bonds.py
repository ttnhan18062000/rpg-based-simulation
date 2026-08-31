# tests/social/test_social_bonds.py
import json
from dataclasses import asdict

import pytest
from src.core.state import EntityState, SocialComponent, IdentityComponent, SocialBond
from src.core.models.social import RelationshipRole
from src.core.updates import SocialUpdate, SocialBondUpdate
from src.systems.social_systems.appraisal import SocialAppraisalSystem
from src.systems.social_systems.relationships import RelationshipService

def create_mock_social_entity(eid, cha=5):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("HERO")
        .location(0, 0)
        .attributes(charisma=cha)
        .combat(alive=True)
        .build())

@pytest.mark.v2_contract
@pytest.mark.differential
def test_social_bond_learning():
    """
    Verifies that update_familiarity produces a first-class bond record.
    Logic ID: SOC-195 (Familiarity changes through interaction evidence)
    Logic ID: SOC-196 (Trust/sentiment changes through interaction evidence)
    """
    hero = create_mock_social_entity(1, cha=10) # High charisma
    subject_id = 2
    
    # 1. First interaction
    update = SocialAppraisalSystem.update_familiarity(hero, subject_id, interaction_quality=1.0, current_tick=100, cha_modifier=2.0)
    
    assert len(update.bond_updates) == 1
    b_upd = update.bond_updates[0]
    assert b_upd.target_id == subject_id
    assert b_upd.familiarity_delta == 0.1 # 0.05 * 2.0
    assert b_upd.sentiment_delta == 0.1 # 1.0 * 0.1
    
    # 2. Apply Update
    new_social = RelationshipService.process_update(hero.social, update)
    assert subject_id in new_social.bonds
    bond = new_social.bonds[subject_id]
    assert bond.familiarity == 0.1
    assert bond.sentiment == 0.1
    assert bond.last_interaction_tick == 100
    
    # 3. Second interaction (Hostile)
    from dataclasses import replace
    hero_v2 = replace(hero, social=new_social)
    update_v2 = SocialAppraisalSystem.update_familiarity(hero_v2, subject_id, interaction_quality=-1.0, current_tick=200, cha_modifier=2.0)
    
    new_social_v2 = RelationshipService.process_update(hero_v2.social, update_v2)
    bond_v2 = new_social_v2.bonds[subject_id]
    assert bond_v2.familiarity == 0.2
    assert bond_v2.sentiment == 0.0 # 0.1 + (-1.0 * 0.1)
    assert bond_v2.last_interaction_tick == 200

def test_social_bond_role_defaults_to_neutral():
    """
    A SocialBond constructed without specifying role continues to canonicalize
    identically to today. Logic ID: SOC-247.
    """
    bond = SocialBond(target_id=2, familiarity=0.5, sentiment=0.3)
    assert bond.role == RelationshipRole.NEUTRAL


def test_social_bond_role_canonical_dict_serializes_as_plain_string():
    """
    RelationshipRole is a str subclass, so the canonical dict (asdict()'s shape,
    matching AuthoritativeState.to_canonical_dict()'s bonds serialization at
    src/core/state.py) round-trips through json.dumps as a plain string, exactly
    as PartyRole already does elsewhere. Logic ID: SOC-247.
    """
    bond = SocialBond(target_id=2, role=RelationshipRole.FRIEND)
    canonical = asdict(bond)
    assert canonical["role"] == "friend"
    round_tripped = json.loads(json.dumps(canonical))
    assert round_tripped["role"] == "friend"
    assert type(round_tripped["role"]) is str


if __name__ == "__main__":
    test_social_bond_learning()
