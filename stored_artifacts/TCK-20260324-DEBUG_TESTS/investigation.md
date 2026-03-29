# Investigation: WorldLoop Test Failures

## Summary of Failures

| Test Case | Error | Root Cause |
|-----------|-------|------------|
| `test_appraisal_phase_triggers_panic_on_low_hp` | `TypeError: '>=' (actually <)` | `actor.stats.hp_ratio` is a `MagicMock`, comparing to `float` fails. |
| `test_perception_tracks_position_history` | `AttributeError: return_value` | `brain._faction_reg.is_hostile` access issue on `MagicMock`. |
| `test_appraisal_detects_stuck` | `TypeError: '>='` | `actor.mind.pos_history` identical check or `age_ticks` comparison. |
| `test_breakthrough_applies_bonus` | `TypeError: '>'` | `stats.atk` or traits comparison involving `MagicMock`. |
| `test_aging_and_death` | `AttributeError` | `is_hostile` mocking issue on `FactionRegistry`. |
| `test_generate_quest_*` | `UnboundLocalError` | `target_pos` scope issue in `generate_quest`. |

## Detailed Analysis

### 1. TypeError (Mock Comparisons)
In many AI tests, `actor = MagicMock()` is used. In `AIBrain._appraisal_phase`, properties like `hp_ratio` are accessed. Since they aren't explicitly mocked with a return value, they return a `MagicMock`, which cannot be compared to floats/ints in Python 3.
- **Fix**: Explicitly set `actor.stats.hp_ratio.return_value = 0.5` or similar.

### 2. AttributeError (FactionRegistry)
`brain._faction_reg.is_hostile.return_value = False` fails if `is_hostile` is somehow not being treated as a mockable attribute. Since `FactionRegistry` has `__slots__`, `MagicMock` might be behaving unexpectedly if the mock attempts to spec the class.
- **Fix**: Ensure `brain._faction_reg` is a plain `MagicMock` or properly spec'd.

### 3. UnboundLocalError: target_pos
In `src/core/quests.py`, `target_pos` is initialized at line 248, but used at 355.
Wait! I found it! Look at the code I viewed:
```python
248:     target_pos = None
...
296:     if template.quest_type == QuestType.LIBERATE and world:
...
303:             target_pos = target_region.center
...
339:     if template.quest_type == QuestType.EXPLORE:
...
342:         target_pos = Vector2(tx, ty)
```
If `template.quest_type` is `HUNT`, both `if` blocks are skipped. `target_pos` *should* be `None`.
**Wait!** Is there a `target_pos` assignment in a DIFFERENT branch that I missed?
Or maybe `target_pos` is used WITHOUT initialization in a branch?

### 4. 51 Skipped Tests
My local run shows 0 skips. The user sees 51. This suggests some features (like Redis or Calamity system) are missing in the user's environment, or they are running with `pytest -m "not slow"`.
- **Action**: Check `pyproject.toml` for markers.
