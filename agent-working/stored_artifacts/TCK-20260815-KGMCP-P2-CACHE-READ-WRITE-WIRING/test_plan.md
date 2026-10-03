---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING

## Regression Surface

**Unit (schema/cache-layer):**
- `tests/tools/test_retrieval_cache.py` (all 9 existing classes: `TestIndexCache`, `TestQueryCache`,
  `TestPacketCache`, `TestMayListEnforcement`, `TestStaticGuards`, `TestPrune`, `TestMigrations`,
  `TestRetrievalVersionAndManifest`, `TestCrashRecovery`) — must keep passing unmodified; this
  ticket adds new functions/classes to this file, never edits an existing test.
- `tests/tools/test_knowledge_gateway_redaction.py` (all classes) — must keep passing unmodified;
  this ticket is the first real *caller* of `evaluate_write_candidate()`/`open_connection_with_limits()`/
  `acquire_write_guard()` etc., but must not edit their definitions or existing tests.
- `tests/tools/test_evidence_cache_identity_contract.py` (all 12 tests) — structural/fixture-based
  contract tests; must keep passing unmodified since this ticket does not edit any contract doc's
  substance (only annotates §20 Done markers, which these tests do not assert against).
- `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
  — scoped only to `tools/retrieval_cache.py`'s source text; must keep passing (this ticket must not
  add `PRAGMA`/`busy_timeout`/`chmod`/`import os` directly into `tools/retrieval_cache.py` — those
  stay confined to `tools/knowledge_gateway_redaction.py`, called from wherever this ticket's new
  code lives).

**Integration (live gateway):**
- `tests/tools/test_knowledge_gateway_mcp.py` — all 10 existing tests, **except**
  `test_knowledge_status_omits_all_cache_specific_fields_enumerated`, which this ticket must
  deliberately update (see New Tests Required and Anti-Drift Test Guards) — not silently broken, not
  left failing, not weakened beyond the specific fields this ticket's own scope newly populates.
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (all tests, esp.
  `test_module_does_not_modify_or_import_retrieval_cache`, `test_module_does_not_edit_knowledge_gateway_router`)
  — must keep passing unmodified; this ticket must not create any import relationship between
  `knowledge_gateway_packet_assembly.py` and the cache layer.
- `tests/tools/test_knowledge_gateway_router.py` (all 31 tests) — must keep passing unmodified;
  `tools/knowledge_gateway_router.py` stays untouched (Out of Scope).
- `tests/tools/test_knowledge_gateway_failure_semantics.py` (all 13 tests) — fail-open behavior must
  survive cache wiring: a cache lookup/write failure (e.g. cache DB unreadable) must never prevent a
  direct provider call from succeeding, mirroring this file's existing "gateway down, providers still
  independently callable" guarantee one level up (cache down, gateway still functions via
  cold-provider path).
- `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`
  — must keep passing; the current 4-path banned tuple (`search_mcp.py`, `hybrid_retrieval.py`,
  `context_packet_assembler.py`, `retrieval_events.py`) does not include any file this ticket touches.
- `tests/tools/test_knowledge_gateway_contract_schemas.py` (all tests) — must keep passing; this
  ticket adds no new schema file and edits no existing one (both response schemas already carry the
  fields this ticket populates — see investigation.md).

**Arena-combat:** not applicable — this subsystem has no combat/simulation surface.

## New Tests Required

Per each Acceptance Criteria bullet:

1. **AC1 — genuine cache hit on identical repeated call, second call never reaches
   `_run_search()`/`graphify query`.**
   - Test name: `test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit`
   - Category: integration
   - Verifies: two back-to-back `_mod._run_knowledge_context(query, ...)` calls with identical
     args; spy (via `monkeypatch`, mirroring the existing `test_wrapper_functions_genuinely_not_applicable_zero_invoked`/
     test 9/10 monkeypatch style already used in this file) on `pa_search_mod._run_search` and
     `pa_router_mod.match_symbol_name`; assert both spies are called on the first invocation and
     **zero** times on the second; assert the second response's `cache` field equals `"HIT"`.
   - Location: `tests/tools/test_knowledge_gateway_mcp.py` (new test, cache-DB-isolated).

2. **AC2 — cache hit rejected/refreshed when direct evidence fingerprint no longer matches real
   repository state.**
   - Test name (PROVIDER_GENERATION-level, real/exercisable):
     `test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists`
   - Category: integration
   - Verifies: warm the cache via a real call, then mutate `manifest.json`'s `built_at` (mirroring
     `_corpus_generation()`'s existing precedent), then repeat the same query; assert the second call
     is a genuine miss (falls through to `_run_search()`/`match_symbol_name` again) and the cached row
     is refreshed, not silently served stale.
   - Location: `tests/tools/test_knowledge_gateway_mcp.py`.
   - Test name (SYMBOL/FILE-level, fixture-based — per investigation.md Risks item 2, real live
     providers cannot supply this today): `test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture`
   - Category: unit (fixture-based, mirroring `test_evidence_cache_identity_contract.py`'s own
     pattern)
   - Verifies: a directly-constructed `retrieval_provider_result_cache_rows` row with
     `evidence_fingerprints` set to a `SYMBOL`-kind fingerprint; the evidence-validity revalidation
     function is called with a *different* current fingerprint for the same symbol and an
     *unchanged* `provider_generation`; assert the row is rejected as stale on fingerprint mismatch
     alone (never on generation alone) — and the mirror case,
     `test_symbol_backed_cache_row_survives_unrelated_generation_bump_fixture`, asserting the same row
     with an *unchanged* fingerprint survives a `provider_generation` bump (direct AC3/§4 test).
   - Location: new cache-layer test module (wherever Plan places the cache-check module's own test
     file — e.g. `tests/tools/test_knowledge_gateway_cache.py`).
   - Both tests' docstrings must state plainly that the SYMBOL/FILE path is fixture-based because no
     real live provider capability descriptor advertises `fine_grained_fingerprints: true` today —
     mirroring `knowledge_gateway_packet_assembly.py`'s own "Honesty notes" disclosure precedent, not
     silently presented as an end-to-end real-provider test.

3. **AC3 — `PROVIDER_GENERATION` fallback triggers only when finer-grained evidence is unavailable,
   confirmed against the real `provider_capabilities_*.json` files.**
   - Test name: `test_provider_generation_fallback_used_for_both_real_providers_today`
   - Category: unit
   - Verifies: loads the real `provider_capabilities_context_search.json` and
     `provider_capabilities_graphify.json`, asserts both currently report
     `fine_grained_fingerprints == false`, and asserts the cache-check module's own fallback-selection
     function returns `PROVIDER_GENERATION` as the validation basis for both — an honest,
     currently-vacuously-true-but-real assertion (see investigation.md Risks item 2), not a
     hand-wave.
   - Test name: `test_finer_fingerprint_preferred_over_provider_generation_when_capability_advertises_it`
   - Category: unit (fixture-based — monkeypatches/temp-copies a capability descriptor with
     `fine_grained_fingerprints: true`, mirroring `test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support`'s
     existing precedent in `test_knowledge_gateway_packet_assembly.py`)
   - Verifies: with a capability descriptor claiming finer-grained support, the fallback-selection
     function chooses the finer fingerprint, never `PROVIDER_GENERATION`, confirming the "never the
     default path when finer evidence IS available" half of AC3 that cannot be exercised against
     today's two real descriptors alone.
   - Location: new cache-layer test module.

4. **AC4 — branch/working-tree scope is real.**
   - Test name: `test_cached_result_from_feature_branch_not_served_on_different_branch`
   - Category: integration
   - Verifies: write a cache row under `repo_branch_scope` for branch A (via direct row construction
     or a monkeypatched `_git_branch_scope()`), then call the cache-check function with branch B for
     an otherwise-identical lookup identity; assert a miss, never a hit — the hard-partition rule,
     checked *before* any fingerprint comparison.
   - Test name: `test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged`
   - Category: integration
   - Verifies: warm the cache, simulate a new commit (different `HEAD`, same branch, same evidence
     fingerprints/content), repeat the same query; assert a genuine hit — `HEAD` is provenance-only,
     never itself a miss trigger.
   - Test name: `test_working_tree_fingerprint_uses_changed_paths_intersection_not_full_tree_hash`
   - Category: unit
   - Verifies: a cached row's evidence paths and a `changed_paths` request field that does **not**
     intersect them leaves the row presumed compatible (no full-tree hash computed — assert via a
     spy/counter that no full-repository hashing routine is invoked); a `changed_paths` set that
     **does** intersect forces revalidation of exactly the affected row, not unrelated rows.
   - Location: `tests/tools/test_knowledge_gateway_mcp.py` (branch tests, real `_git_branch_scope()`
     is already exercised by existing `knowledge_status` tests) and the new cache-layer test module
     (working-tree-intersection unit test).

5. **AC5 — cache writes go through the redaction write-path; no raw/unredacted write path exists.**
   - Test name: `test_cache_write_calls_evaluate_write_candidate_before_any_insert`
   - Category: integration
   - Verifies: spy on `knowledge_gateway_redaction.evaluate_write_candidate`; a real cache-miss call
     that reaches the write path calls it exactly once before any `INSERT`; a `REJECT` verdict
     results in **zero** rows written.
   - Test name: `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module`
   - Category: architecture guard (AST/substring-based, mirroring
     `tests/tools/test_knowledge_gateway_redaction.py`'s own
     `test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py`-style guard)
   - Verifies: every `INSERT INTO retrieval_provider_result_cache_rows` literal in the new
     read/write functions is reachable only downstream of a call to `evaluate_write_candidate()` —
     static check, not just a runtime spy (defense against a future refactor silently adding a
     second write path).
   - Location: new cache-layer test module plus `tests/tools/test_knowledge_gateway_mcp.py` for the
     integration half.

6. **AC6 — `knowledge_status`'s cache-domain fields are real and populated.**
   - Test name: `test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes`
   - Category: integration
   - Verifies: perform a real cache hit and a real cache miss+write, then call
     `_mod._run_knowledge_status()`; assert `cache_entry_counts`, `cache_hit_rate`, `cache_miss_rate`,
     `cache_stale_rejection_rate` are present with real, non-fabricated values consistent with the
     just-performed operations; assert `latency_summary_ms` and `provider_fallback_rate` remain
     **absent** (this ticket's scope does not add latency instrumentation — see investigation.md).
   - Location: `tests/tools/test_knowledge_gateway_mcp.py` (replaces/narrows the now-stale
     `test_knowledge_status_omits_all_cache_specific_fields_enumerated` — see Anti-Drift Test Guards
     below for how the old test's remaining valid guarantee must be preserved, not deleted wholesale).

**Migration-invocation tests (supports AC1/AC5, not a separate AC):**
- `test_check_provider_result_cache_creates_table_on_first_real_use` (unit,
  `tests/tools/test_retrieval_cache.py`, new test in a new `TestProviderResultCache` class) —
  calling the new `check_provider_result_cache()` against a fresh, unmigrated DB does not raise and
  the table exists afterward (idempotent `migration_001_add_level1_tables` call at the function's own
  top).
- `test_migration_001_still_never_called_from_the_original_six_check_or_write_functions` (regression
  re-run of the existing guard, confirming this ticket's addition of new check/write functions did
  not require touching the original 6 — the existing test already covers this by construction, but
  Verify must re-run it explicitly as part of this ticket's own pass, not merely trust it silently).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_retrieval_cache.py tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_evidence_cache_identity_contract.py -v
```

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_failure_semantics.py tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/docs/test_redaction_retention_policy_doc.py -v
```

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_cache.py -v   # new cache-layer module's own test file, once Plan confirms its exact name
```

Never `pytest tests/` — both commands above are scoped to the Knowledge Gateway MCP domain
(`tools/knowledge_gateway_*.py`, `tools/retrieval_cache.py`, `tools/knowledge_gateway_redaction.py`,
and their direct doc-contract tests) plus the packet-assembly/router/failure-semantics/measurement-
baseline files this ticket's changes are most likely to have side effects on.

## Anti-Drift Test Guards

- **`test_module_does_not_modify_or_import_retrieval_cache` and
  `test_module_does_not_edit_knowledge_gateway_router`** (`tests/tools/test_knowledge_gateway_packet_assembly.py`)
  — must keep passing unmodified; the single strongest guard against this ticket accidentally routing
  the cache hook through the assembler instead of the two designated hook points in
  `_run_knowledge_context()`.
- **`test_search_mcp_py_provably_untouched`** (`tests/tools/test_knowledge_gateway_mcp.py`) — must
  keep passing; guards `tools/knowledge_gateway_router.py`/`tools/knowledge_gateway_packet_assembly.py`/
  `tools/search_mcp.py`/`tools/retrieval_events.py` against any accidental edit while wiring the
  cache.
- **`TestMigrations::test_migration_001_function_is_never_called_from_any_check_or_write_function`**
  (`tests/tools/test_retrieval_cache.py`) — must keep passing exactly as-is (iterates only the
  original 6 functions); this ticket's new functions calling `migration_001_add_level1_tables()` at
  their own top must not be added to that test's iteration set, and a new, separate assertion (see
  New Tests Required) should confirm the new functions *do* call it, so the two guarantees stay
  distinguishable rather than silently merged.
- **`test_sqlite_defaults_not_silently_implemented`** (`tests/docs/test_redaction_retention_policy_doc.py`)
  — must keep passing; confirms this ticket did not "helpfully" inline `PRAGMA`/`busy_timeout`/
  `chmod`/`import os` directly into `tools/retrieval_cache.py` instead of calling
  `knowledge_gateway_redaction`'s existing helpers.
- **`test_knowledge_status_omits_all_cache_specific_fields_enumerated` must be updated, not deleted
  or weakened wholesale.** The new version must still assert `latency_summary_ms` and
  `provider_fallback_rate` are absent (the two fields this ticket's own scope does not populate) —
  only the assertion that `cache_entry_counts`/`cache_hit_rate`/`cache_miss_rate`/
  `cache_stale_rejection_rate` are absent should be removed/inverted. A test that simply deletes this
  guard entirely would silently permit a future regression (e.g. `latency_summary_ms` accidentally
  fabricated) to pass unnoticed.
- **A new architecture guard: cache-check and cache-write are genuinely separate steps (non-collapse
  rule, contract §3).** `test_lookup_function_never_returns_a_freshness_or_verification_field` —
  mirrors `test_evidence_cache_identity_contract.py`'s own Test 2 pattern
  (`test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof`), but against this
  ticket's *real* new lookup function this time (Phase 0's version was necessarily a structural
  check against docs only, since no live function existed) — AST-inspects the new lookup-check
  function's return type/dataclass fields and asserts no `freshness`/`verification` field is present;
  a separate, distinct function call is required to obtain a validity verdict.
- **A new guard against WAL-mode surprise (investigation.md Risks item 3):**
  `test_wal_mode_effect_on_real_cache_db_path_is_a_documented_deliberate_choice` — this test's exact
  shape depends on Plan's resolution of Risks item 3; at minimum, if `open_connection_with_limits()`
  is called against the real `CACHE_DB_PATH`, a test must assert the resulting file's journal mode
  and cite the deliberate-choice documentation (comment/doc) explaining why, so a future contributor
  cannot silently revert or silently extend this effect without noticing.
- **A guard against premature schema drift (investigation.md Risks item 1):**
  `test_level1_cache_columns_unchanged_unless_migration_003_explicitly_added` — if Plan resolves
  Risks item 1 as option (a) (in-memory-only, no persistence), this test asserts
  `LEVEL1_CACHE_COLUMNS` still has exactly its current 21 columns (regression guard against a future
  accidental silent column addition); if Plan resolves it as option (b), this test is replaced by the
  `migration_003_add_redaction_policy_version_column`-specific tests analogous to
  `TestMigrations`'s existing `migration_001` test set (fresh-DB apply, idempotency, zero data loss to
  the 20 pre-existing Level 1 columns and rows).
