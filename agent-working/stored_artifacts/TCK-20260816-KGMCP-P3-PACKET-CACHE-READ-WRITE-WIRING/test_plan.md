---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING
artifact_type: test_plan
tags: [ai, mcp, security]
---

# Test Plan — TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING

## Regression Surface

Existing tests that must keep passing, grouped by domain (all are unit/integration-tier; this
subsystem has no arena-combat surface):

**Unit — `tools/knowledge_gateway_cache.py`** (`tests/tools/test_knowledge_gateway_cache.py`):
- `test_compute_lookup_identity_filters_excludes_budget_tokens_and_changed_paths` — must keep
  passing unmodified; any Level 2 identity extension must be a **new** function, not a change to
  `compute_lookup_identity()`'s existing behavior.
- `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly` — must keep passing;
  the new Level 2 orchestration added to this module must not import
  `tools.knowledge_gateway_router`/`tools.knowledge_gateway_packet_assembly`.
- `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module` — must keep passing for
  Level 1's existing `perform_cache_write()`; the new Level 2 write path needs its own analogous
  guard (see New Tests Required).
- `test_revalidate_context_packet_row_*` (7 tests) and
  `test_level2_repo_branch_scope_matches_current_repo_branch_scope_join_format`,
  `test_working_tree_overlap_forces_revalidation_called_unmodified_against_evidence_dependencies_shape`,
  `test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket` — must keep passing
  unmodified; this ticket calls these functions, never edits them.
- `test_per_key_stampede_guard_prevents_concurrent_duplicate_write`,
  `test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling` — Level 1 write-path gates,
  unmodified.

**Integration — `tools/knowledge_gateway_mcp.py`** (`tests/tools/test_knowledge_gateway_mcp.py`):
- `test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit` — must keep passing; this
  is Level 1's own hit test and must remain true when Level 2 is checked first and misses (e.g. the
  first call writes to both Level 1 and Level 2; without a Level 2 hit path override this test still
  exercises the fallback correctly, but must be re-verified it does not silently become a Level 2 hit
  instead, changing what it demonstrates — see New Tests Required for the Level-2-specific version).
- `test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists`,
  `test_cached_result_from_feature_branch_not_served_on_different_branch`,
  `test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged` — Level 1 revalidation
  behavior, unmodified.
- `test_cache_write_calls_evaluate_write_candidate_before_any_insert`,
  `test_cache_write_reject_verdict_results_in_zero_rows_written` — Level 1 write-path enforcement,
  unmodified.
- `test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes` — Level 1's existing
  `knowledge_status` fields must remain correct and unchanged in shape once Level 2 fields are added
  additively.
- `test_knowledge_status_omits_all_cache_specific_fields_enumerated` — must be re-checked: if this
  test enumerates every currently-known-absent cache field by name, it may need updating (not
  broken) to reflect that Level 2 fields are now genuinely present after a Level 2 write, while
  still asserting `latency_summary_ms`/`provider_fallback_rate`/etc. remain absent.
- `test_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path` — must keep passing; the
  Level 2 hook must be wrapped in the same fail-open try/except discipline as Level 1's hooks.
- `test_knowledge_context_response_schema_accepts_new_budget_marker_field`,
  `test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker` — dedup/budget
  sibling's regression surface, unmodified.
- `test_only_knowledge_context_and_knowledge_status_registered`,
  `test_mcp_json_gains_exactly_one_new_server_entry`, `test_search_mcp_py_provably_untouched` —
  structural guards, unmodified.

**Unit — `tools/retrieval_cache.py`** (`tests/tools/test_retrieval_cache.py`):
- `TestMigrations` class (migration_001/002/003 tests), `test_retrieval_cache_schema_version_is_
  queryable_and_correct_after_migration`, `test_migration_is_idempotent_when_run_twice` — must keep
  passing; any new `migration_004_*` this ticket adds must not alter migration_001/002/003's own
  stamped version literals.
- `TestLevel2Migrations::test_no_actual_read_write_functions_added_for_the_new_level2_table` — **this
  test's own premise changes** with this ticket (it currently asserts no `check_*`/`write_*`
  functions exist for the Level 2 table — that assertion becomes false once this ticket adds them).
  This test must be updated as part of this ticket's own diff, not silently left failing or deleted
  without a replacement guard — see New Tests Required.
- `check_provider_result_cache`/`write_provider_result_cache`/`record_provider_result_cache_hit`/
  `provider_result_cache_stats` tests (Level 1) — unmodified.

**Unit — `tools/knowledge_gateway_redaction.py`** (`tests/tools/test_knowledge_gateway_redaction.py`):
- `evaluate_write_candidate()` test suite (allowlist/redaction/secret-scan/size-cap/never-cache/
  ALLOW-stamping) — unmodified; this ticket calls the function as-is, adds no new source-type
  literal.

**Doc/contract structural guards:**
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — schema-shape assertions; must keep
  passing for the request schema (byte-unchanged) and pass against any additive
  `knowledge_status_response.schema.json` field this ticket adds.
- `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
  — must keep passing; the new Level 2 write path must reuse `rk.open_connection_with_limits()`
  exactly like Level 1's `_get_level1_connection()` does, never hand-roll PRAGMA/chmod.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_cache.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v
.venv/bin/python3 -m pytest tests/tools/test_retrieval_cache.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_redaction.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v
.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v
```

Never `pytest tests/` — scoped to the Knowledge Gateway MCP tool surface and its direct doc-contract
guards only.

## New Tests Required

Mapped to each of the ticket's 8 Acceptance Criteria (AC).

**AC1 — identical repeated call is a genuine Level 2 hit, never reaching packet assembly or Level 1**
- `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit`
  Category: integration. Verifies: two identical `_run_knowledge_context()` calls; the second call's
  `cache` field indicates a Level 2 hit (e.g. `"HIT_L2"` or equivalent — exact literal is a Plan
  decision, the response schema's `cache` field is a deliberately open string per Design Decision D3
  so no schema change is required); spies on both `_kgpa.assemble_packet` (via monkeypatch on the
  loaded packet-assembly module) and `_kgc.perform_cache_lookup` (Level 1) to assert **neither is
  called** on the second request — not merely that live providers are skipped.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.

**AC2 — a Level 2 miss correctly falls through to Level 1's existing, unmodified lookup**
- `test_level2_miss_falls_through_to_unmodified_level1_lookup`
  Category: integration. Verifies: pre-seed a Level 1 row (via a real prior call) but never a Level 2
  row for a second, structurally-identical-but-Level-2-cold request (e.g. via a monkeypatched Level 2
  identity that never matches); spies on `_kgc.perform_cache_lookup` to assert it **is** called and
  returns the Level 1 hit, and that `_kgpa.assemble_packet` is **not** called — proving Level 1's own
  hit behavior is exercised exactly as before this ticket, reached via the new Level 2-miss fallthrough.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.

**AC3 — a Level 2 hit is rejected/refreshed when dependency-invalidation logic determines it stale**
- `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`
  Category: integration. Verifies: write a Level 2 row via a real call, then issue a second identical
  call with `changed_paths` intersecting the row's real `evidence_dependencies`; asserts the second
  call is a genuine miss (falls through to Level 1/live assembly, not served from the stale Level 2
  row) — end-to-end exercise of `revalidate_context_packet_row()`'s `working_tree_overlap_forces_
  revalidation()` branch via the real lookup orchestrator, not the already-existing unit-level fixture
  tests in `test_knowledge_gateway_cache.py` (which test the pure function directly, never through a
  live lookup path).
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.
- `test_level2_hit_rejected_on_provider_generation_bump_real_call`
  Category: integration. Verifies: mirrors
  `test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists`'s existing
  Level 1 pattern (manifest `built_at` bump between two calls), but asserts the *Level 2* row is
  rejected and a genuine refresh occurs.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.

**AC4 — Level 2 cache writes independently verified to go through redaction/secret-scan/size-cap
enforcement, no bypass path**
- `test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert`
  (ticket-named; confirmed accurate — mirrors the existing
  `test_cache_write_calls_evaluate_write_candidate_before_any_insert` exactly, adapted for Level 2:
  spy on `kgc_mod.rk.evaluate_write_candidate`, assert it is called with the real assembled-packet
  payload before any row exists in `retrieval_context_packet_cache_rows`, and that the row count is 0
  before and 1 after.
  Category: integration. Location: `tests/tools/test_knowledge_gateway_mcp.py`.
- `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`
  (ticket-named; confirmed accurate — mirrors the existing
  `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module` exactly, adapted for the
  new Level 2 orchestrator function(s) in `tools/knowledge_gateway_cache.py`: asserts no `.execute(`/
  `sqlite3` literal in the module, that `write_context_packet_cache()` is called from exactly one
  place across `tools/*.py` (the new Level 2 write orchestrator), and that
  `evaluate_write_candidate()` precedes `write_context_packet_cache()` in source order with an
  intervening `decision.verdict`-gated early return.
  Category: architecture guard (AST-based, mirrors the Level 1 precedent's own technique).
  Location: `tests/tools/test_knowledge_gateway_cache.py`.
- `test_level2_write_reject_verdict_results_in_zero_rows_written`
  Category: integration. Verifies: force a `REJECT` verdict (monkeypatched
  `evaluate_write_candidate`), assert zero rows written to `retrieval_context_packet_cache_rows` and
  the live response is still returned to the caller (fail-open on write, not fail-closed on read).
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.
- `test_level2_write_stamps_redaction_policy_version_column`
  Category: unit/integration. Verifies: the genuine gap flagged in investigation.md (no
  `redaction_policy_version` column existed on the Level 2 table before this ticket) is closed — a
  real write persists a non-null `redaction_policy_version` value on the row, retrievable via a
  direct `SELECT`.
  Location: `tests/tools/test_retrieval_cache.py`.
- `test_level2_write_respects_max_payload_bytes_size_cap_with_real_measured_packet`
  Category: integration. Verifies: a real (not fixture-mocked) assembled packet is measured against
  `MAX_PAYLOAD_BYTES = 65536`; either confirms real packets stay under the cap (asserting size with a
  real number, not an assumption) or, if a real oversized case can be constructed, confirms the write
  is rejected via `check_size_cap`/`oversized_payload`, never silently truncated. Directly discharges
  the ticket's own Scope "explicit re-verification requirement."
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.

**AC5 — branch/working-tree scope from the dependency ticket is genuinely enforced before a Level 2
hit is served**
- `test_level2_cached_result_from_feature_branch_not_served_on_different_branch`
  Category: integration. Mirrors
  `test_cached_result_from_feature_branch_not_served_on_different_branch`'s existing Level 1 pattern,
  adapted to assert the Level 2 row (not Level 1) is branch-scoped and rejected across branches via a
  real call through `_run_knowledge_context()`, exercising `is_branch_compatible()`/
  `_level2_repo_branch_scope()` through the new live orchestrator, not just the existing unit-level
  fixture test.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.

**AC6 — `knowledge_status`'s Level 2 cache-domain fields are real and populated, distinct from Level
1's**
- `test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1`
  Category: integration. Verifies: after one Level 2 write + one Level 2 hit + one Level 1-only
  scenario, `knowledge_status()`'s new Level 2 fields (entry counts, hit/miss rate, hit-attribution)
  report values that are numerically distinct from and additive to the existing Level 1 fields — not
  aliases or the same computed numbers reused under a new key name.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.
- `test_knowledge_status_level2_fields_omitted_when_level2_cache_has_zero_rows`
  Category: unit/integration. Mirrors the existing zero-row-omission discipline
  `_run_knowledge_status()` already applies to Level 1 fields — Level 2 fields must be genuinely
  omitted (never a fabricated `0`) on a fresh DB, consistent with the module's own established
  "never a fabricated placeholder" rule.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.
- `test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db`
  Category: unit. Mirrors `provider_result_cache_stats()`'s own "never raises on a fresh/
  never-migrated DB" contract for the new Level 2 equivalent stats function.
  Location: `tests/tools/test_retrieval_cache.py`.

**AC7 — `tools/knowledge_gateway_router.py` remains byte-unchanged**
- `test_knowledge_gateway_router_py_provably_untouched`
  Category: architecture guard. Verifies: a real content-hash (or `git diff`-based) comparison of
  `tools/knowledge_gateway_router.py` against its pre-ticket state — mirrors the existing
  `test_search_mcp_py_provably_untouched` technique exactly.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.

**AC8 — a real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added**
- Verified by the repo's existing parity-ledger schema validation tooling (`docs/parity_ledger/
  schema.json`-based check), not a new pytest test — this is a Finalize-phase / done-checker
  concern, not a code-behavior test. Note in Anti-Drift Test Guards below for completeness.

**Cross-cutting (not tied to a single AC, but required by the ticket's own Non-collapse-rule
inheritance):**
- `test_level2_lookup_function_never_returns_a_freshness_or_verification_field`
  Category: unit. Mirrors the existing
  `test_lookup_function_never_returns_a_freshness_or_verification_field` (Level 1) exactly, applied
  to the new Level 2 lookup function. **Directly discharges the named obligation inherited from
  `docs/guidelines/intentional_divergences.md` §2.44's own "Verification" clause** — this is not
  optional coverage, it is a pre-committed requirement from a prior ticket's divergence entry.
  Location: `tests/tools/test_knowledge_gateway_cache.py`.
- `test_level2_lookup_disambiguates_multiple_rows_sharing_the_same_query_key_hash`
  Category: unit/integration. Directly targets Risk 3 from investigation.md (`query_key_hash` is
  unindexed/non-unique, `packet_id` is the real PK): seeds two Level 2 rows with the same
  `query_key_hash` but different `repository_id`/`branch` (or budget, per Central Question 3's
  resolution), and asserts the lookup function returns the correct row for the current scope, never
  the first row returned by an unordered `fetchone()`.
  Location: `tests/tools/test_retrieval_cache.py`.
- `test_level2_double_write_on_full_miss_writes_both_level1_and_level2_rows`
  Category: integration. Directly targets Risk 6 (double-write question): one full-miss call writes
  exactly one Level 1 row and one Level 2 row; both are independently confirmed via
  `rc.provider_result_cache_stats()` and the new Level 2 stats function.
  Location: `tests/tools/test_knowledge_gateway_mcp.py`.
- `TestLevel2Migrations::test_check_and_write_functions_now_exist_for_the_new_level2_table` (or
  equivalent rename/replacement of the now-inverted
  `test_no_actual_read_write_functions_added_for_the_new_level2_table`)
  Category: unit — regression-surface update, not new coverage, but required because this ticket
  makes the old assertion's premise false. Must not be silently deleted without a replacement
  asserting the new functions' real presence and shape.
  Location: `tests/tools/test_retrieval_cache.py`.

## Anti-Drift Test Guards

- `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly` (existing, unmodified) —
  catches any accidental import of the packet-assembly module into
  `tools/knowledge_gateway_cache.py` while building the Level 2 orchestrator.
- `test_knowledge_gateway_router_py_provably_untouched` (new, AC7) — catches any accidental edit to
  the router, even a whitespace-only one.
- `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module` (new, AC4) —
  catches any future refactor that adds a second, unredacted write path to
  `retrieval_context_packet_cache_rows`.
- `test_level2_lookup_function_never_returns_a_freshness_or_verification_field` (new,
  cross-cutting) — catches a Non-collapse-rule violation being silently introduced by the new lookup
  function.
- `test_migration_001_still_never_called_from_the_original_six_check_or_write_functions` (existing,
  unmodified) — re-run to confirm the new `migration_004_*` (if added) does not get wired into the
  wrong hot-path functions.
- `test_search_mcp_py_provably_untouched`, `test_only_knowledge_context_and_knowledge_status_
  registered`, `test_mcp_json_gains_exactly_one_new_server_entry` (existing, unmodified) — catch any
  scope creep into the MCP server's registered-tool surface or `search_mcp.py`.
- Parity ledger schema validation (existing tooling, not a new pytest test) — catches a
  schema-invalid or missing `INFRA-349` entry at Finalize/done-checker time (AC8).
- `test_level2_double_write_on_full_miss_writes_both_level1_and_level2_rows` (new, cross-cutting) —
  catches an accidental regression where wiring in the Level 2 write path silently breaks or
  duplicates the existing, unmodified Level 1 write path.
