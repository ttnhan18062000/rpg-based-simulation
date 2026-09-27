---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality]
---

# Test Plan — TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION

New file `tests/tools/test_monitoring_shard_paths.py`:

1. `test_shard_paths_finds_bare_canonical_only`
2. `test_shard_paths_finds_per_identifier_only`
3. `test_shard_paths_finds_both_shapes_combined`
4. `test_shard_paths_empty_when_neither_exists`
5. `test_per_identifier_shard_paths_excludes_bare_canonical`
6. `test_double_glob_idiom_appears_in_exactly_one_module` (AC5's static guard) — scans `tools/`
   and `src/` (excluding `tests/`) for the two-line double-glob shape; asserts exactly one hit,
   inside `monitoring_shard_paths.py`.

Existing suites re-run unmodified per migrated file (AC2/AC4):
`test_done_checker_static.py`, `test_agent_replay_codex_monitoring_shards.py` (or equivalent),
`test_bash_command_mix.py`, `test_generate_retro.py`, `test_validate_agent_monitoring.py`,
`test_agent_monitoring_manifest.py`, `test_agent_ops_dashboard_ingest.py`, `test_record_events.py`,
`test_verify_referential_integrity.py`, `test_monitoring_consolidation.py`.

Full `tests/tools/` regression after all ten migrations land.
