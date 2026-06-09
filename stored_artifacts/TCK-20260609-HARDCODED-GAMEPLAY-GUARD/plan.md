---
ticket: TCK-20260609-HARDCODED-GAMEPLAY-GUARD
phase: plan
---

# Plan

## New file: tests/architecture/test_no_new_hardcoded_gameplay_truth.py

Gate: for each dict-literal gameplay ID in src/, check if it's in migration_map.yaml OR KNOWN_HARDCODED_BASELINE. Fail on any ID in neither set.

KNOWN_HARDCODED_BASELINE: frozenset of (legacy_id, legacy_family) tuples for pre-existing content not yet tracked in migration_map. 29 entries. Stale-baseline guard fires if any baseline entry gains a migration_map entry.

Scan: regex `^\s+"([\w_]+)"\s*:\s*(Item|Resource|Enemy|Recipe|Service|Region)Def\s*\(` on all src/**/*.py files.

5 tests: migration_map_exists, no_new_ids, smoke-families, smoke-ids, stale_baseline_guard.
