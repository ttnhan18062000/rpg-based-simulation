---
status: historical
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43B-EXPORT-IMPORT
phase: done
date: 2026-06-20
tags: [social-memory, exporter, importer, campaign-orchestrator, phase-4]
---

# TCK-20260619-E43B-EXPORT-IMPORT

## Title
Epic 4.3B · SocialMemoryExporter + Importer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Wires `SocialMemoryRecord` into `CampaignOrchestrator._advance_state()` as pre/post-episode hooks. Exporter serializes at episode end; importer applies at episode start.

**Requires:** TCK-20260619-E43A-SOCIAL-MEM-MODEL

## Scope

In `src/domains/campaigns/social_memory.py`, add:

```python
class SocialMemoryExporter:
    @staticmethod
    def export(entity: EntityState, episode: int) -> SocialMemoryRecord:
        """Read entity's current social state and produce a SocialMemoryRecord."""
        return SocialMemoryRecord(
            entity_id=entity.id,
            relationship_scores=dict(entity.social.relationship_scores),
            faction_reputation=dict(entity.social.faction_reputation),
            # interaction_history populated from recent social events
        )

class SocialMemoryImporter:
    @staticmethod
    def apply(entity_update: EntityUpdate, record: SocialMemoryRecord, decayed: SocialMemoryRecord) -> EntityUpdate:
        """Merge decayed social memory into entity's initial state for new episode."""
        # Apply faction_reputation deltas — do NOT reset existing; merge additively
        ...
```

Wire both hooks into `CampaignOrchestrator._advance_state()` (in `src/domains/campaigns/orchestrator.py` from E32C):
- After episode end: `SocialMemoryExporter.export()` for all alive entities → store in `CampaignState.social_memories: Dict[int, SocialMemoryRecord]`
- Before episode start: `SocialMemoryImporter.apply()` for each entity using decayed record

Add `social_memories: Dict[int, SocialMemoryRecord] = field(default_factory=dict)` to `CampaignState` (E32B).

## Acceptance Criteria
- Reputation from ep1 quest completion is present (with decay) in ep2 entity initial state
- `test_reputation_transfer_across_episodes` passes

## Related Tickets
- TCK-20260619-E43-SOCIAL-MEMORY (parent epic)
- TCK-20260619-E43A-SOCIAL-MEM-MODEL (required)
- TCK-20260619-E43C-DECAY (blocked on this)
- TCK-20260619-E32C-ORCHESTRATOR (CampaignOrchestrator — add_advance_state hook)

## Related Code Areas
- `src/domains/campaigns/social_memory.py` (Exporter/Importer classes)
- `src/domains/campaigns/orchestrator.py` (wire hooks)
- `src/domains/campaigns/state.py` (add social_memories to CampaignState)

## Test Summary
```bash
pytest tests/integration/scenarios/test_social_memory.py::test_reputation_transfer_across_episodes -x -v -m slow
```
## Files Changed
- `src/domains/campaigns/social_memory.py` — Added SocialMemoryExporter and SocialMemoryImporter classes; added TYPE_CHECKING import guard for EntityState; added dc_replace import.
- `src/domains/campaigns/state.py` — Added `social_memories: Dict[int, SocialMemoryRecord]` field to CampaignState; added to_dict/from_dict serialization with str/int key conversion; imported SocialMemoryRecord.
- `src/domains/campaigns/orchestrator.py` — Imported SocialMemoryExporter/Importer; added `_extract_social_memories()` method; wired export into `_advance_state()`; wired import into `_build_initial_state()`.
- `tests/unit/social/test_social_memory.py` — Extended with 8 new unit tests covering Exporter and Importer (19 total, all pass).
- `tests/integration/scenarios/test_social_memory.py` — New file; 2 @slow integration tests (all pass).
- `docs/parity_ledger/social_narrative.yaml` — Added SOC-CROSS-EP-002 entry (verified).

## Completion Summary
SocialMemoryExporter and SocialMemoryImporter implemented in
`src/domains/campaigns/social_memory.py`. Exporter reads trust_history and
public_reputation from EntityState at episode end; Importer applies them
additively to EntityState at episode start. CampaignState extended with
`social_memories: Dict[int, SocialMemoryRecord]` field (serialized with
str/int key conversion). Both hooks wired into CampaignOrchestrator.
19 unit tests and 2 integration tests pass. Parity ledger SOC-CROSS-EP-002
added. Unblocks E43C (decay).
