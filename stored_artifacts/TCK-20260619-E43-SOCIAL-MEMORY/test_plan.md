# Test Plan — TCK-20260619-E43-SOCIAL-MEMORY

## Unit Tests — `tests/unit/social/test_social_memory.py`

```python
def test_social_memory_record_serializes_to_campaign_state():
    # SocialMemoryExporter.export(entity, episode=1) → SocialMemoryRecord
    # Assert round-trips through CampaignState JSON serialization correctly

def test_betrayal_decay_slower_than_cooperation():
    # SocialMemoryRecord with relationship_scores={entity_1: -3.0 (grudge), entity_2: 2.0 (friend)}
    # Apply SocialMemoryDecay 3 times (3 episodes)
    # Assert abs(relationship_scores[entity_1]) > abs(relationship_scores[entity_2])

def test_faction_hostility_persists_after_key_member_death():
    # FactionSocialMemory with entity_hostility={entity_id: 4.0}
    # Mark entity as dead (entity not in alive entities)
    # Assert faction_hostility still contains entity_hostility[entity_id] in next episode

def test_social_memory_importer_applies_decay_before_applying():
    # SocialMemoryRecord from episode 1 with relationship_score=2.0
    # Importer applies to episode 2 entity
    # Assert applied score = 2.0 * (1 - 0.40) = 1.2 (friendship decay applied)

def test_known_traitor_event_fires_on_encounter_threshold():
    # FactionSocialMemory.entity_hostility[entity_id] = 5.0 (betrayal)
    # Entity enters faction territory
    # Assert KNOWN_TRAITOR_SPOTTED event emitted
```

## Integration Tests — `tests/integration/scenarios/test_social_memory.py`

```python
@pytest.mark.slow
def test_reputation_transfer_across_episodes():
    # 2-episode campaign; entity completes quest for Faction A in ep1
    # Assert starting faction_reputation with Faction A NPCs in ep2 > neutral baseline

@pytest.mark.slow
def test_known_traitor_event_fires_on_encounter():
    # Entity betrayed Faction B in ep1
    # Encounter Faction B NPC in ep2
    # Assert KNOWN_TRAITOR_SPOTTED event in simulation_events.jsonl

@pytest.mark.slow
def test_faction_memory_survives_episode_without_member_npcs():
    # All Faction A members die in ep1; new NPCs spawned in ep2
    # Entity that wronged Faction A enters territory
    # Assert faction hostility response fires (collective memory persists)
```

## Parity Coverage
- Update `docs/parity_ledger/social_narrative.yaml`: cross_episode_reputation, faction_collective_hostility, relationship_decay
