---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP
artifact_type: test_plan
tags: [determinism]
---

# Test Plan — TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP

## New tests
- `test_navigation_eleven_newly_covered_fields_participate_in_canonical_hash` — per-field divergence
  sweep, mirrors `test_strategic_all_nine_newly_covered_fields_participate_in_canonical_hash` and
  `test_social_seven_newly_covered_fields_participate_in_canonical_hash`. Confirms each of the 11 newly
  added fields independently changes `to_canonical_dict()` output when it diverges.
- `test_navigation_region_id_participates_in_canonical_hash_end_to_end` — mirrors
  `test_social_nemesis_ids_participates_in_canonical_hash_end_to_end`. Confirms the fix propagates all
  the way to `CanonicalStateHasher.get_hash()`, the real consumer `src/engine/kernel.py` uses for its
  per-tick and final-run determinism checks — not just `to_canonical_dict()` in isolation.

## Regression scope
- `pytest tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/ -m "not slow"`
- `pytest tests/integration/kernel/test_determinism_suite.py tests/integration/kernel/test_checkpoint_reproducibility.py tests/integration/kernel/test_replay_fidelity.py -m "not slow"`

## Result
Both new tests pass. Full regression sweep: 564 passed, 2 skipped (pre-existing, unrelated), 0 failed.
Integration determinism/checkpoint/replay suites: 15 passed, 0 failed.
