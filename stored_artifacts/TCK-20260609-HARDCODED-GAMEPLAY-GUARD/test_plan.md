---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-HARDCODED-GAMEPLAY-GUARD
artifact_type: test_plan
tags: [hardcoded, gameplay, guard]
---


# Test Plan

5 architecture tests in tests/architecture/test_no_new_hardcoded_gameplay_truth.py, all pass.

| Test | Validates |
|---|---|
| test_migration_map_exists | migration_map.yaml file exists |
| test_no_new_hardcoded_gameplay_ids_without_migration_map_entry | main gate — no unmapped new IDs |
| test_scan_finds_expected_fallback_families | smoke: scan detects all 6 families |
| test_scan_finds_known_fallback_ids | smoke: specific IDs detected correctly |
| test_known_baseline_stale_guard | stale baseline: remove from KNOWN_HARDCODED_BASELINE if now in migration_map |
