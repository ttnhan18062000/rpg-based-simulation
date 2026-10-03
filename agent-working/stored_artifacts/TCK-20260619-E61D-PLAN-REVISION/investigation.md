# Investigation — TCK-20260619-E61D-PLAN-REVISION

## Context Search Results

- `search_docs`: NarrativeLedgerEntry schema in state.py (7 fields including entry_id); orchestrator._build_initial_state() is the episode-start hook.
- Parity: no `_prepare_next_episode()` method exists — must add logic to `_build_initial_state()`.

## Key Findings

1. `InteractionRecord.other_entity_id: Optional[int]` — the entity this interaction was with.
2. `SocialMemoryRecord.relationship_scores: Dict[int, float]` — positive score = friendly/mentor.
3. `SocialMemoryRecord.interaction_history: Tuple[InteractionRecord, ...]`.
4. "Mentor" = any entity with positive relationship_score in SocialMemoryRecord.relationship_scores.
5. No HERO role in EntityCarryForward → generate plans for all alive entities without one (document simplification).
6. `persistent_entities` at `_build_initial_state()` time contains all entity carry-forwards from prior episode (both alive and dead); dead mentor detection checks `.alive == False`.
7. Deferred import of `PlanRevisionService` in `_build_initial_state()` avoids any circular import.

## Architecture Boundary

`plan_revision.py` is a service (not a data model) — can import from `state.py` and `social_memory.py`. No circular imports.
