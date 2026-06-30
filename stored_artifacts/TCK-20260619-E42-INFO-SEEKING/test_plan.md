# Test Plan — TCK-20260619-E42-INFO-SEEKING

## Unit Tests — `tests/unit/cognition/test_information_seeking.py`

```python
def test_unknown_fact_generates_seeking_project():
    # UnknownFact with priority=0.7 and no seeking_project_id
    # Assert InformationNeedDetector generates ProjectState(kind=INFORMATION_SEEKING)

def test_paid_transaction_transfers_gold_and_lead():
    # Known entity gold=100; InformationProvider reliability=0.9; cost=10
    # Assert ResourceTransferIntent(gold_delta=-10) emitted; LeadState with EXACT certainty received

def test_lead_staleness_decay_reduces_confidence():
    # KnowledgeFact recorded_tick=0; current_tick=5000
    # Assert certainty < 0.5 (DECAY_RATE=0.0001 → certainty * (1 - 5000*0.0001) = 0.5)

def test_person_and_concept_lead_types_accepted():
    # LeadState(kind=LeadKind.PERSON, ...) and LeadState(kind=LeadKind.CONCEPT, ...)
    # Assert no validation error; both valid LeadKind values

def test_belief_contradiction_fires_on_depleted_lead():
    # Entity executes location lead pointing to depleted ResourceNodeState
    # Assert "belief_contradiction" SimulationEvent emitted
    # Assert InformationProviderState.reliability_score -= 0.1

def test_information_provider_registered_in_authoritative_state():
    # Build state with InformationProvider entity
    # Assert state.information_providers[entity_id].archetype == MERCHANT
```

## Integration Tests — `tests/integration/scenarios/test_information_seeking.py`

```python
@pytest.mark.slow
def test_full_seeking_cycle_in_600_tick_run():
    # 600-tick run with InformationProvider entity
    # Assert event sequence: information_need_identified → information_transaction → lead_received

@pytest.mark.slow
def test_belief_contradiction_on_stale_lead():
    # Inject stale coordinate lead pointing to depleted node
    # Entity navigates to location; assert belief_contradiction event
    # Assert retry seeking project generated

@pytest.mark.slow
def test_person_lead_routes_entity_to_provider():
    # Entity has UnknownFact about faction tension; generates PERSON_LEAD to GUILD_MASTER
    # Assert entity path goes through GUILD_MASTER entity position
```

## Parity Coverage
- Update `docs/parity_ledger/strategic_cognition.yaml`: information_seeking, paid_leads, lead_contradiction
