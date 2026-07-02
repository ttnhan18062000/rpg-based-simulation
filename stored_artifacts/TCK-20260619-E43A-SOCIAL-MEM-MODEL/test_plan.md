# Test Plan — TCK-20260619-E43A-SOCIAL-MEM-MODEL

## Scope

Unit tests for `SocialMemoryRecord` and `InteractionRecord` construction,
serialization, and deserialization. No live engine state needed.

## Test File

`tests/unit/social/test_social_memory.py`

## Test Cases

### Normal flow

- `test_interaction_record_constructs` — basic field construction, all fields
  set, no defaults needed.
- `test_social_memory_record_default_empty` — SocialMemoryRecord with only
  entity_id, verify empty collections for interaction_history /
  relationship_scores / faction_reputation and None for optional ticks.
- `test_social_memory_record_serializes_to_campaign_state` (ticket AC) — full
  round-trip: build a SocialMemoryRecord with multiple InteractionRecords,
  call `to_dict()`, call `from_dict()` on the result, assert equality.

### Edge cases

- `test_interaction_record_optional_fields_none` — both `other_entity_id` and
  `faction_id` are None; verify to_dict() emits null and from_dict() restores
  None.
- `test_social_memory_record_empty_round_trip` — entity with no interactions
  round-trips cleanly.
- `test_social_memory_record_entity_id_key_round_trip` — relationship_scores
  keyed by int entity_id; keys survive JSON str-conversion round-trip.

### Regression / determinism

- `test_to_dict_keys_sorted` — `relationship_scores` and `faction_reputation`
  dict keys appear in sorted order in `to_dict()` output (matches CampaignState
  determinism convention).

## Run Command

```bash
pytest tests/unit/social/test_social_memory.py -x -v
```
