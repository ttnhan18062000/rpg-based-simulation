# Plan — TCK-20260619-E61A-PLAN-MODEL

## Approach

Follow the `SocialMemoryRecord` pattern exactly:
- New file `src/domains/campaigns/progression_plan.py` with 4 frozen dataclasses
- `to_dict()` / `from_dict()` on each; sorted dict keys; `.get()` for backward compat
- Import `ProgressionPlan` in `state.py`; add field; extend `to_dict()` and `from_dict()`

## Files to Create/Modify

1. **NEW** `src/domains/campaigns/progression_plan.py` — 4 dataclasses
2. **MODIFY** `src/domains/campaigns/state.py` — add field + serialization
3. **NEW** `tests/unit/campaigns/test_progression_plan.py` — 4 tests per spec
4. **MODIFY** `docs/parity_ledger/progression.yaml` — add PROG-110

## Serialization Key Decisions

- `progression_plans` → str keys in JSON (`str(k)`), int keys in Python (`int(k)`)
- Tuples serialized as lists in JSON, reconstructed as tuples via `tuple(...)` in `from_dict()`
- All leaf dict keys sorted for determinism

## No Risks

This is a pure data model addition with no engine or pipeline changes.
