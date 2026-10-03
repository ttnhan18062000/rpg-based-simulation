# Test Plan — TCK-20260619-E43B-EXPORT-IMPORT

## Scope

Covers: SocialMemoryExporter, SocialMemoryImporter, CampaignState.social_memories,
orchestrator hook wiring.

## Unit Tests (tests/unit/social/test_social_memory.py)

| Test | What it verifies |
|---|---|
| test_exporter_produces_record_from_entity_state | Exporter reads trust_history + public_reputation; produces correct SocialMemoryRecord |
| test_exporter_empty_social_state | Entity with no social history → empty relationship_scores, default faction_reputation |
| test_importer_applies_trust_history | Trust history from record merged additively into entity social |
| test_importer_applies_reputation | public_reputation seeded from record's "default" faction_reputation key |
| test_importer_no_default_reputation_leaves_original | Missing "default" key → public_reputation unchanged |
| test_importer_additive_merge_trust | Existing trust + carried trust = sum (not overwrite) |
| test_importer_returns_new_entity_state | Original EntityState is not mutated; new instance returned |

## Integration Tests (tests/integration/scenarios/test_social_memory.py)

| Test | Marker | What it verifies |
|---|---|---|
| test_reputation_transfer_across_episodes | @slow | After ep0: social_memories populated. ep1 entity has trust_history seeded from ep0 record. AC from ticket. |

## Parity Ledger Updates

- `docs/parity_ledger/social_narrative.yaml`: update SOC-CROSS-EP-001 status from
  `missing` → `verified`; add `SOC-CROSS-EP-002` for exporter/importer wiring.

## Run Command

```bash
pytest tests/unit/social/test_social_memory.py tests/integration/scenarios/test_social_memory.py -x -v -m "not slow or slow"
```

Scoped command (slow test optional):
```bash
pytest tests/unit/social/test_social_memory.py -x -v
pytest tests/integration/scenarios/test_social_memory.py -x -v -m slow
```
