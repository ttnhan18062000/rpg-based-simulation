# Test Plan - Phase 28 (Perspective/relation usage and legacy-safe migration)

We will verify both clean perspective projections and fallback compatibility behaviors.

## Unit Testing

Add a new test suite to `tests/unit/content_semantics/test_semantics.py` containing the following tests:
1. `test_relation_projection_clean`:
   - Hero Guild perspective projects Goblin Warband as `"enemy"`.
   - Hero Guild perspective projects Merchant League as `"neutral"`.
   - Hero Guild perspective projects Wild Beast Pack as `"threat"` (contextual threat).
   - Wild Beast Pack perspective projects Town Council as `"intruder"` when context has `intruding=True`.
2. `test_relation_projection_fallback`:
   - Verify projection falls back to legacy bucket hostility check if clean data (perspective + relationships) is missing.
3. `test_is_hostile_compat`:
   - Verify `is_hostile_compat` behaves exactly like `is_hostile` for legacy queries when clean data is missing.
   - Verify `is_hostile_compat` uses clean projection when data exists (e.g. wild beast pack is not hostile by default, but is hostile when context indicates combat engagement or intrusion).

## Regression Testing

Run the entire suite of unit tests to verify nothing else is broken:
- `pytest tests/unit/content_semantics/test_semantics.py`
- `pytest tests/arena/`
