---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE28-PERSPECTIVE-RELATION-MIGRATION
artifact_type: investigation
tags: [phase28, perspective, relation, migration]
---

# Phase 28 Investigation

## Relationship Semantics Service and Combat targeting

In the codebase, `FactionSemanticsService.is_hostile_compat` implements relation projection lookup:
- It checks if the source faction has perspective or relationship data.
- If missing, it falls back to standard `is_hostile` and logs to debug: `"Falling back to legacy hostility semantics for..."`
- If present, it projects relation and yields `True` for `enemy`, `threat` (contextually), and `intruder` (contextually).

Currently, `TacticalDecisionSystem` filters hostiles as follows:
```python
        hostiles = [
            n for n in neighbors 
            if n.identity.faction != entity.identity.faction and n.combat.alive
        ]
```
And `LegalityServiceV2` checks friendly fire as follows:
```python
        # 3. Faction Validity (Friendly Fire Law)
        if attacker.identity.faction == target.identity.faction:
            return False, ReasonCode.FRIENDLY_FIRE_ILLEGAL
```

By changing these checks to use `is_hostile_compat` when a catalog repository or service registry is available, we can:
- Query relationship projection logic at runtime.
- Determine target suitability based on dynamic perspectives and active-data context (combat engagement, distance, intrusion).
- Maintain legacy enum fallback when relationships are missing.
