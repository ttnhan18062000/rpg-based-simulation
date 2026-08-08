---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY
artifact_type: test_plan
tags: [ai, observability, process-improvement]
---

# Test Plan — TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY

New tests in `tests/tools/test_parity_index.py` (extending the existing suite), all using
`tmp_path`-scoped scratch DB/ledger fixtures — never the real repo `docs/parity_ledger/` or
`parity-index/parity.db`.

1. `test_check_staleness_not_built_when_db_missing` — no DB file at the given path; assert
   `status == "NOT_BUILT"`.
2. `test_check_staleness_fresh_immediately_after_build` — build into a scratch DB from a scratch
   ledger dir, then check staleness against the same live ledger dir; assert `status == "FRESH"`
   and `db_hash == live_hash`.
3. `test_check_staleness_stale_after_shard_edit` — build, then edit one shard file's content
   (append a real, valid new entry) in the scratch ledger dir, then check staleness; assert
   `status == "STALE"` and `db_hash != live_hash`.
4. `test_check_staleness_reuses_load_shards_not_reimplemented` — a real-content assertion, not
   an implementation-detail test: verify staleness-check's own live hash matches exactly what a
   fresh `build()` into a second scratch DB would produce for the same ledger dir — proves the
   check can't silently drift from what a real build actually hashes.
5. `test_check_staleness_cli_exit_code` — `0` for FRESH, `1` for STALE and for NOT_BUILT
   (subprocess or direct `main()` call with patched `sys.argv`, matching this test file's own
   existing CLI-invocation test style if one exists — check first, don't invent a new pattern).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms the hash mechanism is separable from a full rebuild | Done |
| A `make` target exists to build/rebuild parity-index/parity.db | Implement (Makefile) |
| Staleness check reports FRESH/STALE/NOT_BUILT correctly for all 3 real cases | Tests 1-3 |
| Scoped pytest passes | Tests 1-5 |
