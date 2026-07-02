# Test Plan — TCK-20260619-E43D-FACTION-MEMORY

## Test file
`tests/unit/social/test_social_memory.py` (extend existing file)

## Required test (AC)
- `test_faction_hostility_persists_after_key_member_death` — verifies that `FactionSocialMemory` survives even when the offending entities have no live `SocialMemoryRecord` (models the "all members dead" scenario).

## Additional tests

### FactionSocialMemory construction
- `test_faction_social_memory_default_empty` — constructs with defaults; empty dicts.
- `test_faction_social_memory_is_immutable` — frozen dataclass rejects mutation.
- `test_faction_social_memory_round_trip` — to_dict/from_dict JSON round-trip.
- `test_faction_social_memory_int_keys_as_str_in_dict` — entity_hostility and episode_of_offense keys are str in serialized form.
- `test_faction_social_memory_sorted_keys` — to_dict keys are deterministically sorted.

### FactionSocialMemoryExporter
- `test_exporter_builds_from_betrayal_events` — betrayal events → entity_hostility populated.
- `test_exporter_builds_from_attack_events` — attack events → entity_hostility populated.
- `test_exporter_ignores_non_offense_events` — "helped", "traded" events → no entry.
- `test_exporter_max_hostility_on_multiple_events` — duplicate events for same entity → max hostility.
- `test_exporter_records_episode_of_offense` — episode index captured per entity.

### CampaignState integration
- `test_campaign_state_faction_social_memories_default_empty` — new CampaignState has empty dict.
- `test_campaign_state_round_trip_with_faction_memory` — CampaignState.to_dict/from_dict preserves faction_social_memories.

## Run command
```bash
pytest tests/unit/social/test_social_memory.py -x -v -m "not slow"
```
