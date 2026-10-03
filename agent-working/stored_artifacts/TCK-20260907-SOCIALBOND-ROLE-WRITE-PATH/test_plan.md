---
status: active
layer: core
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH
date: 2026-09-07
---

# Test Plan: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH

## New Tests (`tests/unit/social/test_relationships.py`)
1. `test_sustained_positive_sentiment_derives_role_to_friend` — real `sentiment_delta` crossing 0.8
   through `process_update()` derives `FRIEND`.
2. `test_sustained_negative_sentiment_derives_role_to_rival` — mirror-negative, crossing -0.8.
3. `test_mid_band_sentiment_change_does_not_derive_a_role` — a real, non-extreme `sentiment_delta`
   leaves `role` at its `NEUTRAL` default (not a tautology).
4. `test_derived_friend_role_is_not_demoted_by_a_later_mid_band_sentiment_update` — regression guard:
   a prior FRIEND derivation is not reset to NEUTRAL by a later mid-band sentiment change.
5. `test_extreme_negative_sentiment_can_flip_an_existing_friend_role_to_rival` — an existing FRIEND can
   flip to RIVAL on a real, extreme reversal (not one-way-only like nemesis promotion).
6. `test_explicit_role_set_overrides_a_contradicting_derived_sentiment` — `role_set` still wins even
   when it contradicts what sentiment alone would derive.
7. `test_zero_sentiment_delta_bond_update_does_not_touch_role` — re-asserts the pre-existing
   `test_process_update_role_set_none_preserves_existing_role` guarantee directly against the new
   derivation code path.

## Regression
- `tests/unit/social/test_relationships.py` — full file, including the 2 pre-existing role tests,
  unmodified.
- `tests/architecture/test_social_write_paths.py` — the authoritative-write-path architecture guard.
- `tests/unit/social/`, `tests/unit/domains/campaigns/`, `tests/integration/campaigns/` — broader
  social-adjacent sweep.

## Commands
```
pytest tests/unit/social/test_relationships.py -v
pytest tests/architecture/test_social_write_paths.py -q
pytest tests/unit/social/ tests/unit/domains/campaigns/ tests/integration/campaigns/ -q
```

## Verification (non-pytest)
- `grep -rn "place_attachment_delta=" src/` / `grep -rn "check_nemesis_promotion" src/` — confirm the
  disclosed-but-unfixed adjacent dormancy finding (zero real callers) before writing the Chapter 07 §3
  correction.
- `python3 tools/parity_index.py build && health` — confirm `SOC-248` lands clean.
