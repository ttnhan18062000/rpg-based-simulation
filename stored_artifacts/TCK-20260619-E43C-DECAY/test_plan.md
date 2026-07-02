# Test Plan — TCK-20260619-E43C-DECAY

## Scope
Unit tests for `SocialMemoryDecay.apply_decay()` and integration of decay into
`SocialMemoryImporter.apply()`.

## Test File
`tests/unit/social/test_social_memory.py` — appended to existing file.

## Test Cases

### 1. `test_decay_friendship_reduces_score`
- Input: `relationship_scores = {5: 1.0}` (positive friendship)
- One decay application
- Expected: `1.0 × (1 - 0.40) = 0.6`

### 2. `test_decay_grudge_reduces_score_slower`
- Input: `relationship_scores = {5: -1.0}` (grudge)
- One decay application
- Expected: `-1.0 × (1 - 0.10) = -0.9`

### 3. `test_betrayal_decay_slower_than_cooperation` (Ticket AC)
- Input: `relationship_scores = {5: 1.0, 6: -1.0}`
- Three decay applications
- Friendship: `1.0 × 0.6^3 = 0.216` (rounded to 4 dp)
- Grudge: `-1.0 × 0.9^3 = -0.729` (rounded to 4 dp)

### 4. `test_decay_faction_reputation`
- Input: `faction_reputation = {"guild": 0.8}`
- One decay application
- Expected: `round(0.8 × 0.6, 4) = 0.48`

### 5. `test_decay_zero_score_stays_zero`
- Input: `relationship_scores = {5: 0.0}`
- Expected: `0.0 × 0.6 = 0.0` (zero stays zero)

### 6. `test_decay_returns_new_record`
- Verify `apply_decay` returns a different object (frozen, new via `replace`)
- Original record unchanged

### 7. `test_importer_applies_decay_before_merge`
- Build entity with empty trust, record with `relationship_scores = {5: 1.0}`
- Call `SocialMemoryImporter.apply(entity, record)`
- Verify result has `trust_history[5] ≈ 0.6` (decay applied before merge)

### 8. `test_decay_preserves_empty_scores`
- `relationship_scores = {}`, `faction_reputation = {}` → no keys → returns same
  empty dicts (no errors)

## Run Command
```bash
pytest tests/unit/social/test_social_memory.py -x -v
```

## Acceptance Criteria
- All new tests pass
- `test_betrayal_decay_slower_than_cooperation` passes (ticket-named AC)
- All pre-existing tests in the file continue to pass
