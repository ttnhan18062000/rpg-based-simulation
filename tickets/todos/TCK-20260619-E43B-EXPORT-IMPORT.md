---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43B-EXPORT-IMPORT
phase: open
date: 2026-06-20
tags: [social-memory, exporter, importer, campaign-orchestrator, phase-4]
---

# TCK-20260619-E43B-EXPORT-IMPORT

## Title
Epic 4.3B · SocialMemoryExporter + Importer

## Status
OPEN

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
_To be filled on completion._
## Completion Summary
_To be filled on completion._
