# Investigation — TCK-20260619-E43C-DECAY

## Topic
Relationship decay mechanics for cross-episode social memory.

## Prerequisite Status
- TCK-20260619-E43B-EXPORT-IMPORT: DONE (in `tickets/done/`)
- `SocialMemoryRecord`, `SocialMemoryExporter`, `SocialMemoryImporter` all exist in
  `src/domains/campaigns/social_memory.py`.

## Current State of `social_memory.py`

### Data model (E43A)
- `InteractionRecord` — frozen dataclass, immutable, JSON round-trip.
- `SocialMemoryRecord` — frozen dataclass with fields:
  - `entity_id: int`
  - `interaction_history: Tuple[InteractionRecord, ...]`
  - `relationship_scores: Dict[int, float]` — positive = friendly, negative = hostile
  - `faction_reputation: Dict[str, float]`
  - `last_betrayal_tick: Optional[int]` — already reserved for E43C
  - `last_cooperation_tick: Optional[int]` — already reserved for E43C

### Export/Import (E43B)
- `SocialMemoryExporter.export()` — pure read from `EntityState.social`, produces
  `SocialMemoryRecord`, wired into `CampaignOrchestrator._advance_state()`.
- `SocialMemoryImporter.apply()` — merges `relationship_scores` into `entity.social.trust_history`
  additively, seeds `public_reputation` from `faction_reputation["default"]`, returns
  new `EntityState` via `dc_replace`. No in-place mutation.
  - **NOTE in docstring**: "Decay (E43C) is applied to the record before this importer is called;
    E43B receives the record as-is (no decay at this tier)."
  - The importer already anticipates receiving a pre-decayed record; E43C calls
    `apply_decay(record)` before calling `SocialMemoryImporter.apply()`.

### Where Decay is Called
The ticket scope says: call `SocialMemoryDecay.apply_decay(record)` inside
`SocialMemoryImporter.apply()` before applying scores. This means the importer
itself calls decay, making it transparent to callers (CampaignOrchestrator does
not need to change).

## Decay Formula Analysis

```
friendship score × (1 - FRIENDSHIP_DECAY)  per episode
grudge score    × (1 - GRUDGE_DECAY)        per episode
```

Constants:
- `FRIENDSHIP_DECAY = 0.40`  → score multiplied by 0.60 each episode
- `GRUDGE_DECAY     = 0.10`  → score multiplied by 0.90 each episode

AC verification (from ticket):
- friendship after 3 decays: `2.0 × 0.6^3 = 2.0 × 0.216 = 0.432` ... wait, ticket says `0.216`.
  Re-reading: `2.0 × 0.6^3 = 0.432`. However ticket says "2.0×0.6^3" == 0.216 ×.
  Actually: `0.6^3 = 0.216`, so `2.0 × 0.6^3 = 0.432`.
  The ticket AC reads "friendship at 0.216 (2.0×0.6^3)". This seems to intend a
  starting value of 1.0: `1.0 × 0.6^3 = 0.216`. The parenthetical is the formula
  pattern, not the literal multiplication. Test will use starting value = 1.0 for
  friendship.
- grudge after 3 decays: `abs(-1.0) × 0.9^3 = 0.729`. Starting value = -1.0,
  result = `-1.0 × 0.9 × 0.9 × 0.9 = -0.729`. Abs value is 0.729. The test
  checks the absolute decay amount.

## Determinism Check
- `apply_decay` is pure function: no randomness, no side effects.
- Uses `round(..., 4)` for bounded float precision — deterministic.
- Input is an immutable frozen dataclass; output is a new frozen dataclass via `replace`.
- Score sign (`< 0`) determines decay branch — fully deterministic.

## Architecture Constraints Satisfied
- No raw domain models from APIs (no API involvement).
- Durable state via typed records: `SocialMemoryRecord` is the typed carrier.
- `replace(record, ...)` (which is `dataclasses.replace` aliased as `dc_replace`)
  already imported in the file — no new imports needed at top.
- No mutation of live state.

## Files to Change
1. `src/domains/campaigns/social_memory.py` — add `SocialMemoryDecay` class,
   call `apply_decay` inside `SocialMemoryImporter.apply()`.
2. `tests/unit/social/test_social_memory.py` — add decay tests.
3. `docs/parity_ledger/social_narrative.yaml` — add `SOC-CROSS-EP-003`.

## No Conflicts Found
- No other ticket touches `SocialMemoryDecay` or `apply_decay`.
- E43D (faction memory) is parallel and touches different fields.
- `replace` (`dc_replace`) is already imported at top of `social_memory.py`.
