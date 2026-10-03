# Test Plan — TCK-20260619-E51-CHRONICLE

## Unit Tests — `tests/unit/chronicle/test_chronicle_compiler.py`

```python
def test_significance_scoring_ranks_death_above_harvesting():
    # entity_death significance > routine harvest significance
    death_entry = NarrativeLedgerEntry(event_type="entity_death", significance=0.5, ...)
    harvest_entry = NarrativeLedgerEntry(event_type="harvest", significance=0.1, ...)
    assert EventSignificanceScorer.score(death_entry) > EventSignificanceScorer.score(harvest_entry)

def test_hero_death_scores_higher_than_commoner_death():
    # HERO payload → 0.8; non-HERO → 0.5
    hero_death = NarrativeLedgerEntry(event_type="entity_death", payload={"entity_role": "HERO"}, ...)
    assert EventSignificanceScorer.score(hero_death) >= 0.8

def test_event_grouping_produces_incident_clusters():
    # 15 events within 50-tick windows → ≥2 incidents
    events = [make_entry(tick=i*10) for i in range(15)]
    hierarchy = ChronicleGrouper().group(events)
    assert len(hierarchy.incidents) >= 2

def test_chronicle_hierarchy_contains_all_four_levels():
    # After grouping: ChronicleHierarchy has events, incidents, episodes, eras
    hierarchy = ChronicleGrouper().group(make_entries(50))
    assert hierarchy.eras and hierarchy.episodes and hierarchy.incidents

def test_milestone_naming_deterministic():
    # Same entry → same name every call
    entry = make_entry(event_type="entity_death", subject_id=42)
    assert ChronicleNamer.name_milestone(entry, {42: "Aldric"}) == "The Death of Aldric"
```

## Integration Tests — `tests/integration/scenarios/test_campaign_chronicle.py`

```python
@pytest.mark.slow
def test_chronicle_md_contains_three_milestones():
    # Run 3-episode campaign; run ChronicleCompiler; assert ≥3 named milestones in Chronicle.md

@pytest.mark.slow
def test_chronicle_md_readable_without_prior_context():
    # All named entities have at least one description sentence in Chronicle.md

@pytest.mark.slow
def test_chronicle_json_matches_structured_schema():
    # chronicle.json validates against expected schema (campaign_id, eras[], episodes[], incidents[])
```

## API Tests — `tests/api/test_chronicle_api.py`

```python
def test_chronicle_rest_endpoint_returns_structured_json():
    # GET /api/v1/chronicle/{campaign_id} → 200 with eras array

def test_era_summary_endpoint_returns_milestone_names():
    # GET /api/v1/chronicle/{campaign_id}/eras/era_1/summary → named_milestones non-empty
```

## Parity Coverage
- `docs/parity_ledger/social_narrative.yaml`: add chronicle event compression entries as `verified`
