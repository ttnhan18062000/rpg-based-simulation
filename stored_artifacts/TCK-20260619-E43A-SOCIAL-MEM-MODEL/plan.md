# Plan — TCK-20260619-E43A-SOCIAL-MEM-MODEL

## Approach

Create a new pure data-model file `src/domains/campaigns/social_memory.py`
following the exact conventions of `src/domains/campaigns/state.py`:
- `dataclass(frozen=True)` for all sub-records (no `slots=True`; not used in
  existing campaign records)
- `to_dict()` / `from_dict()` pair on every class
- No imports from `src.engine` or `src.core.state`
- `from __future__ import annotations` for forward references
- `Dict`, `Tuple`, `Optional` from `typing` (existing files use this style)

Add tests in `tests/unit/social/test_social_memory.py`.

## Files

| Action | Path |
|--------|------|
| New    | `src/domains/campaigns/social_memory.py` |
| New    | `tests/unit/social/test_social_memory.py` |

## Record Design

### InteractionRecord
- `episode: int` — which episode this happened in
- `tick: int` — which tick within that episode
- `kind: str` — one of: "helped", "betrayed", "traded", "fought_alongside",
  "conflict"
- `other_entity_id: Optional[int]` — None for faction-only events
- `faction_id: Optional[str]` — None for direct entity-only events
- `magnitude: float` — 0.0–1.0

### SocialMemoryRecord
- `entity_id: int`
- `interaction_history: Tuple[InteractionRecord, ...]` — ordered log
- `relationship_scores: Dict[int, float]` — entity_id → net score (positive
  = friendly, negative = hostile). Used by E43B importer.
- `faction_reputation: Dict[str, float]` — faction_id → reputation score
- `last_betrayal_tick: Optional[int]` — most recent betrayal tick (for
  grudge half-life decay in E43C)
- `last_cooperation_tick: Optional[int]` — most recent cooperation tick

## Serialization Convention

- `Dict[int, float]` keys: `str(k)` in `to_dict()`, `int(k)` in `from_dict()`
- `Tuple[InteractionRecord, ...]`: list of dicts in `to_dict()`, converted via
  `tuple(InteractionRecord.from_dict(r) for r in ...)`
- `Optional[int]`/`Optional[str]`: stored as-is (JSON null when None)
- Dict key ordering: `sorted()` for determinism

## Review Gate

- All state is typed and immutable (frozen dataclasses)
- No live engine state imported
- No raw domain models exposed
- Deterministic dict key ordering
