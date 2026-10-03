# Test Plan — TCK-20260619-E41-PARTY-LOOP

## Unit Tests — `tests/unit/social/test_party_lifecycle.py`

```python
def test_party_formation_requires_compatibility_threshold():
    # Two entities with incompatible personalities/classes (low sociability + prior grudge)
    # Assert no GroupRecord formed when compatibility score < threshold

def test_fair_share_protocol_distributes_by_contribution():
    # Known contribution: entity_a=0.7, entity_b=0.3, reward=100
    # Assert shares[entity_a]=70, shares[entity_b]=30

def test_betrayal_desertion_fires_on_high_grievance():
    # Inject grievance_score=4.0 (above threshold 3.0)
    # Assert `betrayal_desertion` SimulationEvent emitted and reputation_delta=-2.0

def test_escort_target_route_scores_above_survival():
    # Designate entity B as ESCORT_TARGET in GroupRecord
    # Assert entity A's PROTECT_TARGET route urgency > entity A's OWN_SURVIVAL route urgency

def test_leadership_election_picks_highest_sociability():
    # Leader sociability=0.3, member sociability=0.8 (diff=0.5 > threshold 0.2)
    # Assert GroupUpdate.new_leader_id = member.id after LEADERSHIP_CHECK_INTERVAL ticks

def test_class_synergy_bonus_applied_to_combat_routes():
    # WARRIOR + MAGE in party
    # Assert combat_route_score *= 1.15 in AdventureRouteScorer
```

## Integration Tests — `tests/integration/scenarios/test_party_lifecycle.py`

```python
@pytest.mark.slow
def test_party_survives_two_quests():
    # 600-tick urban_political run with HERO entities
    # Assert: party forms, completes ≥2 quests, ≥1 NarrativeLedger party entry

@pytest.mark.slow
def test_party_dissolves_gracefully_after_quest_completion():
    # Group forms, quest completes, reward distributed
    # Assert dissolution_tick is set and no orphaned group entry remains

@pytest.mark.slow
def test_defection_and_reputation_penalty_in_run():
    # Run until betrayal_desertion event fires
    # Assert departing entity has reduced faction reputation
```

## Parity Coverage
- Update `docs/parity_ledger/social_narrative.yaml`: party_lifecycle_sustained, reward_split, escort_behavior, defection
