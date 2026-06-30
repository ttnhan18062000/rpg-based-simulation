# Test Plan — TCK-20260619-E53-FACTION-DIPLOMACY

Test plan is per-child-epic. Each child epic writes its own test files at implementation time.

## Phase A — Faction as Agent

```python
# tests/unit/faction/test_faction_state.py
def test_faction_state_constructs_and_serializes():
    # FactionState(faction_id="iron_guild", territory=("region_1",), ...) → canonical dict

def test_faction_decision_phase_produces_directive():
    # FactionDecisionPhase with mocked world state → ≥1 FactionDirective output

def test_faction_tension_increases_on_resource_depletion():
    # Inject RESOURCE_DEPLETED event in faction territory
    # Assert FactionState.tension_level increases

def test_guard_entity_patrol_routes_boosted_near_contested_border():
    # GUARD entity near contested region; FactionDirective=DEFEND
    # Assert patrol route urgency +2.0
```

## Phase B — Diplomacy

```python
# tests/unit/faction/test_diplomacy.py
def test_diplomatic_state_transitions_valid():
    # NEUTRAL→TENSE→HOSTILE→WAR→NEUTRAL transition is valid
    # NEUTRAL→WAR direct transition is invalid

def test_alliance_reduces_shared_territory_threat():
    # Two factions ALLIED; shared border region threat_score decreases

def test_treaty_flows_through_narrative_ledger():
    # TreatyOffer accepted → NarrativeLedgerEntry(event_type="ALLIANCE_FORMED") emitted
```

## Phase C — Territorial Conflict

```python
# tests/integration/scenarios/test_faction_campaign.py
@pytest.mark.slow
def test_war_declared_and_territory_transferred():
    # 3-episode campaign, 3 factions; assert war_declared → siege → territory_transferred

@pytest.mark.slow
def test_war_exhaustion_ends_conflict():
    # Long war; assert both factions' military_strength < 0.3 → peace transition

@pytest.mark.slow
def test_chronicle_names_the_war():
    # After E53D+E51 integration: ChronicleCompiler names the war
```

## Phase D — History Integration

```python
def test_faction_war_declared_event_in_narrative_ledger():
    # WAR_DECLARED event present in NarrativeLedger with significance ≥ 0.9

def test_grand_strategy_doc_archived():
    # docs/archive/grand_strategy_v1.md exists; docs/systems/grand_strategy.md does NOT
```

## Parity Coverage
- `docs/parity_ledger/world_dynamics.yaml`: faction/political entries as `verified`
- `docs/parity_ledger/substrate.yaml`: FactionState persistence entries as `verified`
