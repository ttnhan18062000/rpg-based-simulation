---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME
artifact_type: plan
tags: [content, observability]
---

# Plan — TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME

1. `src/content/schema.py`: `FactionDefinition.common_races` → `common_species`.
2. `data/content/social/factions.yaml`: rename all 16 `common_races:` entries →
   `common_species:` (key-only, zero value changes).
3. `tests/unit/content/test_layered_catalog.py`: fixture kwarg fix (`common_races` →
   `common_species`).
4. `src/observability/event_shapers.py`: rename the deferred `combat_engagement_started`/`ended`
   event output key `"race_id"` → `"species_id"` (confirmed zero downstream consumers first);
   update its docstring's "role/faction/race" → "role/faction/species".
5. `tests/unit/observability/test_event_shapers.py`: matching assertion fix
   (`snap["race_id"]` → `snap["species_id"]`).
6. Re-confirm (via direct grep, not the epic's now-stale scan) that `src/engine/{kernel,cognition,
   replay_manager}.py`, `src/observability/{event_recorder,alerts/sinks}.py`,
   `src/quests/generator.py`, `src/api/ws/stream.py`, `src/content_semantics/personality.py`,
   `data/content/entities/entity_archetypes.yaml`, `data/content/social/personality_bias.yaml` need
   no further change (all already closed by child 1, or never functionally coupled).
7. Fix 2 leftover terminology-accuracy comments found via full grep sweep:
   `src/engine/cognition.py`, `tests/unit/content_semantics/test_semantics.py`.
8. Run scoped tests, then a full non-slow `tests/unit/`+`tests/integration/` sweep to confirm no
   regression.
