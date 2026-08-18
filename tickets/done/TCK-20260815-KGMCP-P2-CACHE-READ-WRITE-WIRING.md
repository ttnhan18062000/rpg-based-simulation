---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING
phase: done
date: 2026-08-15
tags: [ai, mcp, security]
---

# TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING

## Title
Wire cache lookup, evidence-fingerprint validation, and cache write into the real Phase 1 gateway

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` builds the schema; `TCK-20260815-KGMCP-P2-
REDACTION-WRITE-PATH` builds the redaction/write-path functions. This ticket wires both into the
real, already-shipped Phase 1 gateway's actual request handling: on `knowledge_context`, check the
cache first (validating direct evidence fingerprints per §12.2, falling back to provider generation
only when finer-grained evidence isn't available per §12.1's fallback rule), serve a real hit when
valid, and write a real, redacted, policy-compliant result on a miss.

## Scope
- Implement cache-lookup identity per `evidence_cache_identity_contract.md` §1 (normalized_intent,
  resolved_entity_ids, filters, budget_class, routing_policy_version, repo_branch_scope) as the real
  key computed from a real `knowledge_context` request.
- Implement evidence-validity checking per §2/§3's non-collapse rule: lookup identity and
  evidence-validity identity are checked as genuinely separate steps, never collapsed into one.
- Implement §12.2's lazy, read-time evidence-fingerprint revalidation: re-check direct evidence
  fingerprints before serving a hit, falling back to `PROVIDER_GENERATION`-level validation only
  when the provider capability contract lacks reliable finer-grained evidence (per
  `evidence_cache_identity_contract.md` §4's already-frozen fallback rule).
- Implement §12.3's branch/working-tree awareness: cache scope includes repository identity,
  branch/detached-HEAD marker, HEAD commit (recorded for provenance, not itself a cache-miss
  trigger), and a fingerprint of relevant uncommitted changes — computed only for the overlap
  between changed paths and cached evidence paths, never a full working-tree hash per request.
- On a genuine cache miss, call the real providers (exactly as Phase 1's `knowledge_context` already
  does), assemble the packet as Phase 1 already does, then write the result through the redaction
  write-path (dependency ticket) before returning it.
- On a genuine cache hit, return the cached, already-redacted result without a provider round-trip
  — this is the behavior `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` will measure.
- Update `knowledge_status`'s response to include real cache-domain fields Phase 1 explicitly
  omitted (cache entry counts, hit/miss rates, staleness counts) — now genuinely populable since a
  real cache exists.

## Out of Scope
- Any change to routing decisions (`tools/knowledge_gateway_router.py` stays untouched) or
  extractive rendering logic in `tools/knowledge_gateway_packet_assembly.py` beyond the minimal
  hook needed to check/write the cache — this ticket adds caching around Phase 1's existing
  pipeline, it does not redesign that pipeline.
- Level 2 (context-packet) or Level 3 (verified knowledge) caching — Phase 3/6.
- Semantic/fuzzy cache-key matching (Phase 5) — this ticket implements exact normalized-query reuse
  only.
- Cache-GC scheduling/automation — the GC defaults are defined by the dependency ticket; actually
  running GC on a schedule (vs. on-demand/manual) is not required here unless Plan finds it trivial
  to include.

## Acceptance Criteria
- [x] An identical repeated `knowledge_context` call (same normalized intent/entity IDs/filters/
      budget class) produces a genuine cache hit on the second call — verified by a real test
      proving the second call never reaches `_run_search()`/`graphify query`.
      (`test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit`)
- [x] A cache hit is rejected and refreshed when its direct evidence fingerprint no longer matches
      real repository state (e.g. a cited document's content hash changed) — real test, not a
      documentation claim. Real live-provider coverage is `PROVIDER_GENERATION`-level only (both
      real providers report `fine_grained_fingerprints: false` today — a genuine, disclosed
      limitation, see investigation.md Risks item 2); the SYMBOL/FILE-kind fingerprint-mismatch
      path is fixture-based and labeled as such.
      (`test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists`,
      `test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture`)
- [x] The `PROVIDER_GENERATION` fallback genuinely triggers only when the provider capability
      contract lacks finer-grained evidence (confirmed against the real
      `provider_capabilities_*.json` files, same providers Phase 1 already validated) — never used
      as the default path when finer-grained evidence IS available.
      (`test_provider_generation_fallback_used_for_both_real_providers_today`,
      `test_finer_fingerprint_preferred_over_provider_generation_when_capability_advertises_it`)
- [x] Branch/working-tree scope is real: a cached result from one branch is not served on an
      unrelated branch when the underlying evidence differs; a new commit alone does not force a
      cache miss when direct evidence is unchanged.
      (`test_cached_result_from_feature_branch_not_served_on_different_branch`,
      `test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged`)
- [x] Cache writes go through `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`'s real functions — no
      raw/unredacted write path exists anywhere in this ticket's code.
      (`test_cache_write_calls_evaluate_write_candidate_before_any_insert`,
      `test_cache_write_reject_verdict_results_in_zero_rows_written`,
      `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module`)
- [x] `knowledge_status`'s cache-domain fields (previously omitted per Phase 1's own honest
      not-yet-available disclosure) are now real and populated from the real cache.
      (`test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes`)

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (parent)
- TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS (dependency)
- TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH (dependency)
- TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE (DONE; the real gateway this ticket adds caching to —
  read, do not modify its routing/assembly logic beyond the minimal cache hook)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; the identity/fallback contracts this ticket
  implements as real logic for the first time)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §12, §12.1, §12.2, §12.3, §20 Phase 2
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §4, §6, §11
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py` (the request-handling hook point)
- `tools/retrieval_cache.py` (the schema/write-path this ticket reads/writes through)

## Assumptions / Open Questions
- Whether the cache-lookup hook belongs inside `tools/knowledge_gateway_mcp.py`'s
  `_run_knowledge_context()` directly, or as a new thin wrapper layer between it and the router/
  packet-assembler — Investigate should decide based on the real, already-landed Phase 1 code
  structure, minimizing invasiveness to Phase 1's frozen logic.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING/plan.md`'s
13 steps, with Architecture Review's 4 explicit rulings (DD3/DD4/DD5/DD10) applied as instructed:

- **DD3 (confirmed, option b):** `migration_003_add_redaction_policy_version_column` added to
  `tools/retrieval_cache.py`, guarded by an explicit `PRAGMA table_info` idempotency check.
  `LEVEL1_CACHE_COLUMNS` grew to 22 entries. `migration_002` is never referenced by name anywhere
  (only by ordinal position, per the schema-migrations ticket's own reservation).
- **DD4 (accepted as-is):** the new Level 1 write functions open `CACHE_DB_PATH` via
  `knowledge_gateway_redaction.open_connection_with_limits()`, going WAL file-wide for the real
  cache DB. `test_wal_mode_effect_on_real_cache_db_path_is_a_documented_deliberate_choice` added
  per the plan's own instruction. No guard/rollback added beyond that test.
- **DD10:** `check_provider_result_cache()` does a PK `SELECT` by `(query_hash, repo_branch_scope)`
  then compares `normalized_intent`/`filters`/`budget_class`/`routing_policy_version` in Python;
  any mismatch is `MISS` (`reason_code="identity_mismatch_on_shared_key"`), never served as a hit.
  `routing_policy_version` type handling: stored as `TEXT` via `str(int)` on write, compared via
  `str(routing_policy_version)` on read — a dedicated test
  (`test_check_provider_result_cache_routing_policy_version_type_coercion_is_consistent`) proves a
  real int/int-as-string round-trip matches and a genuine value mismatch still correctly misses.
- **DD5:** no code or comment anywhere in this ticket's diff claims the security-pass precondition
  is "satisfied" — Security-Review's own verdict is left entirely open, per plan.md's own framing.

Two things surfaced during Implement that the plan's own pseudocode didn't fully resolve —
both recorded in detail as a new "Deviations" section at the bottom of `plan.md` (12 items total,
covering import style, two small helper-signature completions, `perform_cache_write()`'s
`packet`→`response` signature swap per the plan's own Anti-Drift instruction, two new supporting
helpers the plan referenced but never defined, the `cache_key_version` constant choice, the real
`knowledge_status` rate formula, and 4 narrow, justified test corrections). The two most
architecturally significant ones:

1. **`perform_cache_write()` now refuses to write a PARTIAL-status response.** Discovered as a real
   regression, not a hypothetical: without this gate, a transient provider failure got cached and
   replayed verbatim on the next identical query, breaking
   `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` (which issues the
   same query twice expecting two independently-computed outcomes). Only `OK`/`CONFLICTED`
   responses are cached; `PARTIAL` never is.
2. **Two pre-existing guard tests were narrowed**, not deleted or weakened wholesale: both
   `test_sqlite_defaults_not_silently_implemented` (docs) and
   `TestSqliteOperationalLimits::test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py`
   (redaction tests) previously banned the literal string `"PRAGMA"` anywhere in
   `tools/retrieval_cache.py`. DD3's own explicit, Architecture Review-confirmed instruction
   ("guarded by an explicit PRAGMA table_info idempotency check") necessarily puts one real
   `PRAGMA table_info(...)` statement into that file. Both guards now ban specifically
   `"PRAGMA journal_mode"`/`"PRAGMA busy_timeout"` (their actual stated purpose — preventing
   `retrieval_cache.py` from re-implementing `open_connection_with_limits()`'s own connection-tuning
   logic) while still fully banning `busy_timeout`/`chmod`/`import os`.

**Post-Security-Review fix (2026-08-16): §4 secret-scan baseline expansion.** Security-Review
BLOCKED this ticket because `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
§4/§11 requires the 4-pattern secret-scan baseline (`tools/knowledge_gateway_redaction.py:121-128`,
`_SECRET_SCAN_PATTERNS`, owned by the already-closed sibling `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`)
to be "reviewed and expanded by a security-focused pass before Phase 2 payload caching goes live" —
and this ticket is that go-live moment (real cache writes are now reachable from a live
`knowledge_context` call for the first time). The reviewer found concrete gaps: no named-service
token formats (GitHub, Slack), no OpenAI/Anthropic API-key formats, no generic `password`/`secret`-
named assignment (the existing pattern is hardcoded to `api[_-]?key`/`apikey` only), no
basic-auth-in-URL pattern. The user explicitly authorized closing this ticket's own blocking gate by
expanding the patterns — described by Security-Review itself as "narrow, not a redesign."

This legitimately edits `tools/knowledge_gateway_redaction.py`, a file owned by the sibling,
already-DONE `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` ticket — justified here because *this*
ticket's own Security-Review gate is what requires the expansion (§4/§11's "before Phase 2 payload
caching goes live" precondition names this ticket by ID), mirroring the precedent already set this
session by `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`, which legitimately edited 2 DONE sibling
files when its own scope required it.

`_SECRET_SCAN_PATTERNS` grew from 4 to 10 entries: the original AWS-access-key/generic-api-key/PEM-
header/Bearer-token 4, plus `github_token` (`gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}`,
covering `ghp_`/`gho_`/`ghs_`/`ghr_`/`github_pat_`), `slack_token` (`xox[baprs]-[A-Za-z0-9\-]+`),
`openai_api_key` (`sk-(?!ant-)[A-Za-z0-9]{20,}` — negative lookahead deliberately excludes the
`sk-ant-` prefix so an Anthropic key is never double-matched or mis-attributed as OpenAI),
`anthropic_api_key` (`sk-ant-[A-Za-z0-9\-_]{20,}`), `generic_password_or_secret_assignment`
(mirrors the existing generic-api-key pattern's shape for `password`/`passwd`/`secret`-named keys),
and `basic_auth_in_url` (`https?://[^\s:/@]+:[^\s:/@]+@`). `check_never_cache_categories()`'s
token-vs-credential classification was extended via a new `_TOKEN_SHAPED_SECRET_PATTERNS` frozenset
(`{"bearer_token", "github_token", "slack_token"}` map to `CATEGORY_TOKENS`; the remaining 7
credential-shaped match names, including the 4 new API-key/password/basic-auth patterns, map to
`CATEGORY_SECRETS_OR_CREDENTIALS`) — a direct, necessary consequence of adding named-service token
patterns, not a new decision axis. The module docstring's disclosure was updated to record the
expansion without claiming production-completeness; the literal phrases
`"not a production-complete secret scanner"` and `"security-focused pass before Phase 2 payload
caching goes live"` were deliberately preserved verbatim so `TestModuleDisclosure` and
`tests/docs/test_redaction_retention_policy_doc.py`'s existing assertions on those exact substrings
continue to pass without modification.

Hook placement in `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` matches DD1's
Implement-time correction (stated in plan.md itself): the cache-check runs immediately after
`routing_decision = _kgr.route(query)` succeeds (not before), since `compute_lookup_identity()`
structurally requires `routing_decision.matched_identifier`. Both hooks are wrapped in broad
`try/except Exception` for fail-open semantics — verified directly against
`tests/tools/test_knowledge_gateway_failure_semantics.py`'s full 13-test matrix (all pass unmodified
except gaining the new cache-DB isolation fixture) plus a new dedicated
`test_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path` test.

`tools/knowledge_gateway_router.py` and `tools/knowledge_gateway_packet_assembly.py` are confirmed
byte-unchanged (`git diff --quiet HEAD -- tools/knowledge_gateway_router.py
tools/knowledge_gateway_packet_assembly.py` exits 0).

## Test Summary

All three of test_plan.md's Scoped Pytest Commands run green, plus the new module's own file:

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_retrieval_cache.py tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_evidence_cache_identity_contract.py -q
  → 142 passed

.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_failure_semantics.py tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_knowledge_gateway_cache.py -q
  → 139 passed (was 137; +2 — see gap fix below)
```

Combined total: **281 passed** (was 279).

`tests/tools/test_knowledge_gateway_mcp.py::test_knowledge_status_omits_all_cache_specific_fields_enumerated`
is the one deliberate, plan-anticipated (DD13) correction — narrowed, not deleted; its remaining
guarantee (`latency_summary_ms`/`provider_fallback_rate`/`recent_invalidation_reasons`/
`cache_rebuildable` stay omitted) is unweakened and still asserted.

New tests added: 6 in `tests/tools/test_retrieval_cache.py` (`TestProviderResultCache`,
`TestMigration003`, `TestProviderResultCacheStats` classes, 16 test methods total), 20 in
`tests/tools/test_knowledge_gateway_cache.py` (18 original + 2 added post-Implement, see gap fix
below), and 9 in `tests/tools/test_knowledge_gateway_mcp.py` (AC1/AC2/AC4/AC5/AC6 integration tests
plus a fail-open test) — covering every AC's real, executable behavior, not documentation claims.

**Gap fix (post-Implement, per Architecture-Verify):** plan.md's own Step 8 Verify list named
`test_per_key_stampede_guard_prevents_concurrent_duplicate_write` and
`test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling` as required integration-level
coverage against `perform_cache_write()` itself. Neither existed as such at the point Implement's
Test Summary was first written: the stampede-guard test existed only as a bare-primitive unit test
of `acquire_write_guard`/`release_write_guard` in `tests/tools/test_knowledge_gateway_redaction.py`,
and the size-cap-gate branch (`tools/knowledge_gateway_cache.py:289-290`) had no test anywhere. Both
gates fail open, so this was a silent test-coverage gap, not a functional break — but a real one on
a security-tagged ticket. Both tests were added to `tests/tools/test_knowledge_gateway_cache.py`,
calling the real `perform_cache_write()` orchestrator (concurrency via two real threads sharing one
cache key for the stampede test; `rk.check_db_size_within_limit` mocked at the real call boundary,
not the DB actually grown to 256 MB, for the size-cap test). Full detail and rationale recorded in
`staging_artifacts/TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING/plan.md`'s Deviations item 13.

Full domain sweep (`pytest tests/tools/ -k "knowledge_gateway or retrieval_cache or evidence_cache"`)
also green (255 passed, was 253). No `knowledge-index/retrieval_cache.db` artifact left behind
(cleaned up; `git status` confirms nothing tracked under `knowledge-index/`).

**Post-Security-Review fix (2026-08-16): §4 secret-scan pattern expansion re-run.** Both of
test_plan.md's Scoped Pytest Commands re-run after expanding `_SECRET_SCAN_PATTERNS` from 4 to 10
patterns in `tools/knowledge_gateway_redaction.py`, plus the redaction test file specifically:

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_retrieval_cache.py tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_evidence_cache_identity_contract.py -q
  → 158 passed (was 142, +16)

.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_failure_semantics.py tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_knowledge_gateway_cache.py -q
  → 139 passed (unchanged — none of these files touch tools/knowledge_gateway_redaction.py directly;
    tests/docs/test_redaction_retention_policy_doc.py's 6 tests re-verified green against the
    updated §4 table/disclosure text)

.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_redaction.py -q
  → 65 passed (was 51, +14)
```

**New combined total: 297 passed (was 281, +16).** The +16 breaks down as 14 new
`TestSecretScan` detection/reject-outright test pairs (one pair per new pattern: `github_token`,
`slack_token`, `openai_api_key`, `anthropic_api_key`, `generic_password_or_secret_assignment`,
`basic_auth_in_url` = 12, plus 2 cross-match tests —
`test_openai_pattern_does_not_mismatch_an_anthropic_key` and
`test_anthropic_pattern_does_not_mismatch_an_openai_key` — confirming the `sk-(?!ant-)` negative
lookahead prevents an Anthropic key from ever being double-matched or mis-attributed as an OpenAI
key) plus 2 new `TestNeverCacheCategories` tests
(`test_never_cache_rejects_named_service_tokens_as_tokens_category`,
`test_never_cache_rejects_named_service_api_keys_as_secrets_or_credentials_category`) verifying the
new patterns' token-vs-credential classification. Full domain sweep
(`pytest tests/tools/ -k "knowledge_gateway or retrieval_cache or evidence_cache"`) re-run: 271
passed (was 255, +16). No pre-existing test was weakened, deleted, or had its assertions loosened —
`TestModuleDisclosure`'s and `tests/docs/test_redaction_retention_policy_doc.py`'s literal-substring
assertions on `"not a production-complete secret scanner"` and `"security-focused pass before Phase
2 payload caching goes live"` pass unmodified because those exact phrases were deliberately
preserved verbatim in the updated docstring/doc text.

## Files Changed

- `tools/knowledge_gateway_cache.py` (new) — the orchestration module (Steps 1, 5, 6, 7, 8).
- `tools/retrieval_cache.py` — Steps 2, 3, 4, 10: `ProviderResultCacheLookup`,
  `check_provider_result_cache`, `_get_level1_connection`, `write_provider_result_cache`,
  `record_provider_result_cache_hit`, `migration_003_add_redaction_policy_version_column`,
  `provider_result_cache_stats`; `LEVEL1_CACHE_COLUMNS` gained a 22nd entry; new top-of-file
  `sys.path` bootstrap + `from tools import knowledge_gateway_redaction as _kgr_redaction` import.
- `tools/knowledge_gateway_mcp.py` — Step 9/10: `_load_cache_module()`, the two cache-check/
  cache-write hook call-outs in `_run_knowledge_context()`, `_run_knowledge_status()`'s real
  cache-domain field population, updated docstrings.
- `tests/tools/test_retrieval_cache.py` — new `TestProviderResultCache`/`TestMigration003`/
  `TestProviderResultCacheStats` classes; one existing test
  (`test_new_table_column_set_matches_proposal_section_10_2_row_shape`) updated to also apply
  `migration_003` (mechanical DD3 consequence); `import dataclasses` added.
- `tests/tools/test_knowledge_gateway_cache.py` (new) — unit/fixture tests + architecture guards;
  gained 2 more tests post-Implement (`test_per_key_stampede_guard_prevents_concurrent_duplicate_write`,
  `test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling`) closing a real Step 8
  Verify-list gap flagged by Architecture-Verify — see plan.md Deviations item 13.
- `tests/tools/test_knowledge_gateway_mcp.py` — new `_isolated_cache_db` autouse fixture (DD14);
  `test_knowledge_status_omits_all_cache_specific_fields_enumerated` narrowed (DD13); 9 new
  AC1/AC2/AC4/AC5/AC6/fail-open integration tests.
- `tests/tools/test_knowledge_gateway_failure_semantics.py` — new `_isolated_cache_db` autouse
  fixture (necessary extension of DD14, see Deviations item 8 in plan.md).
- `tests/docs/test_redaction_retention_policy_doc.py` — `test_sqlite_defaults_not_silently_implemented`
  narrowed to ban only connection-tuning PRAGMA forms (Deviations item 9).
- `tests/tools/test_knowledge_gateway_redaction.py` —
  `TestSqliteOperationalLimits::test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py`
  narrowed identically (Deviations item 9). (Note: this file and `tools/knowledge_gateway_redaction.py`
  itself were newly added by the prior, already-closed `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`
  ticket, not created by this ticket — this ticket only edited the one test above within that file.)
- `staging_artifacts/TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING/plan.md` — new Deviations
  section appended (13 items — the 13th added post-Implement, closing the Step 8 Verify-list gap
  Architecture-Verify found).
- `docs/plans/knowledge-gateway-mcp-proposal.md` — §20 Phase 2's "Validate direct evidence
  fingerprints before hits..." and "Add exact normalized-query reuse." bullets annotated **Done**,
  mirroring the 2 prior sibling-ticket bullets' convention.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — §4 and §11 updated to
  record that the security-pass precondition is now operative (write-path reachable from a live
  `knowledge_context` call), without claiming it is satisfied — that verdict is left to this ticket's
  own not-yet-run Security-Review phase; §6 updated in past tense to record that
  `redaction_policy_version` persistence (Risks item 1) resolved to Architecture Review DD3 option b
  (a new `migration_003` column), superseding the prior "unresolved" language.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — §2 gained a new ordered
  entry for `migration_003_add_redaction_policy_version_column`, in the same format as the existing
  migration_001/migration_002 entries; no other part of this frozen design doc was touched.
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-343` (status=verified, priority=P1,
  proof_type=regression) added via `tools/parity_ledger_writer.py::write_entry()`, citing real
  function names/line numbers in `tools/knowledge_gateway_cache.py`,
  `tools/retrieval_cache.py`, and `tools/knowledge_gateway_mcp.py`, plus
  `tests/tools/test_knowledge_gateway_cache.py` (20 tests) and the other affected pre-existing test
  files. Existing entry `INFRA-341` (schema-migrations ticket) had its `v2_evidence` line-number
  citations into `tools/retrieval_cache.py` corrected in place (same entry, same claims — only the
  line numbers, which had shifted from this ticket's own additions to that file); `INFRA-342`
  (redaction-write-path ticket, cites `tools/knowledge_gateway_redaction.py`) needed no correction
  since this ticket did not edit that file. `python3 tools/parity_index.py build` re-run after each
  write.

**Post-Security-Review fix (2026-08-16) — additional files:**

- `tools/knowledge_gateway_redaction.py` — **owned by the already-DONE sibling
  `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`; edited here because this ticket's own
  Security-Review gate required it** (§4/§11's "before Phase 2 payload caching goes live"
  precondition names this ticket by ID as the go-live moment). `_SECRET_SCAN_PATTERNS` expanded
  from 4 to 10 entries (added `github_token`, `slack_token`, `openai_api_key`,
  `anthropic_api_key`, `generic_password_or_secret_assignment`, `basic_auth_in_url`); new
  `_TOKEN_SHAPED_SECRET_PATTERNS` frozenset added and wired into `check_never_cache_categories()`'s
  token-vs-credential classification; module docstring and `scan_for_secrets()` docstring updated
  to disclose the expansion without claiming production-completeness (the two literal phrases the
  existing test suite asserts on verbatim were preserved unchanged).
- `tests/tools/test_knowledge_gateway_redaction.py` — 14 new tests in `TestSecretScan` (6
  detect/reject-outright pairs + 2 OpenAI/Anthropic cross-match tests) and 2 new tests in
  `TestNeverCacheCategories` for the new patterns' token-vs-credential classification.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — §4's illustrative
  pattern table expanded from 4 to 10 rows; §4 and §11 text updated to record that the
  security-focused pass has now been performed (patterns reviewed and expanded), while explicitly
  preserving the "documented starting point, not a production-complete secret scanner" disclosure
  — expansion is not claimed as completeness.
- `staging_artifacts/TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING/plan.md` — new addendum entry
  appended documenting this post-Security-Review fix cycle.

**Post-Security-Review fix — Parity correction pass (2026-08-16):** the first Parity pass (above)
correctly noted `INFRA-342` needed no correction, but that was true only as of that snapshot,
before the post-Security-Review fix edited `tools/knowledge_gateway_redaction.py`. Re-verified via
`tools/parity_ledger_writer.py::write_entry()`:

- `docs/parity_ledger/infrastructure.yaml` `INFRA-342` — every `v2_evidence` line-number citation
  into `tools/knowledge_gateway_redaction.py` had shifted (the new module-docstring "Update"
  paragraph plus the 6 new `_SECRET_SCAN_PATTERNS` dict entries pushed every downstream symbol
  down); all citations corrected against the current file. The `"_SECRET_SCAN_PATTERNS` 4-pattern
  dict"` phrase was corrected to note the dict now has 10 entries (expanded by this ticket's own
  post-Security-Review fix, cross-referenced to `INFRA-343`) while leaving `INFRA-342`'s underlying
  claims about what `REDACTION-WRITE-PATH` itself built unchanged. `test_path` test-class counts
  corrected (`TestSecretScan` 10→24, `TestNeverCacheCategories` 7→9, total 49→65), with a note that
  the +16 came from this ticket's fix, not from `REDACTION-WRITE-PATH`. `support_boundary` gained a
  trailing sentence noting the "4 patterns only" baseline was later expanded by this ticket.
- `docs/parity_ledger/infrastructure.yaml` `INFRA-343` — `support_boundary`'s closing sentence
  (previously: security-pass precondition "operative... but explicitly NOT claimed satisfied here...
  belongs to this ticket's own not-yet-run Security-Review phase") was stale now that
  Security-Review has run (BLOCKED once, then re-ran to APPROVED after the pattern expansion) —
  replaced with a sentence recording the BLOCKED→fix→APPROVED sequence and the 4→10 pattern
  expansion as a real, substantive addition this ticket ultimately shipped. `test_path` gained a
  new citation into `tests/tools/test_knowledge_gateway_redaction.py::TestSecretScan`/
  `TestNeverCacheCategories` for the 16 new tests proving that expansion.
- `python3 tools/parity_index.py build` re-run after each write.

## Completion Summary

Implemented the full read/write cache wiring into the real, live Knowledge Gateway MCP gateway:
lookup identity (§1) and evidence-validity identity (§2/§3/§4) computed as genuinely separate steps
(Non-collapse rule), branch/working-tree scope (§5/§12.3) enforced as a hard partition checked
before any fingerprint comparison, and every real cache write routed exclusively through
`knowledge_gateway_redaction.evaluate_write_candidate()` with no bypass path anywhere (statically
guarded). `knowledge_context` now genuinely skips the provider round-trip on a revalidated hit and
writes a real, redacted row on a miss (except a PARTIAL/degraded result, deliberately never
cached); `knowledge_status` now reports real cache entry counts and hit/miss/stale-rejection rates.
All 4 of Architecture Review's explicit rulings (DD3/DD4/DD5/DD10) were implemented exactly as
instructed, with DD5's security-pass precondition left fully open for the Security-Review phase to
adjudicate — this ticket makes no claim of its own sufficiency. `tools/knowledge_gateway_router.py`
and `tools/knowledge_gateway_packet_assembly.py` are confirmed byte-unchanged.

**Post-Implement gap fix (Architecture-Verify):** plan.md Step 8's Verify list named two integration
tests against `perform_cache_write()` itself — the per-key stampede guard and the size-cap gate —
that did not exist at real-orchestrator granularity when Implement's Test Summary was first
written. Both were added to `tests/tools/test_knowledge_gateway_cache.py`, calling the real
`perform_cache_write()` function (not the bare guard primitives, not a reimplementation of the size
check). No production logic changed; full detail in plan.md Deviations item 13.

**Parity phase:** `docs/parity_ledger/infrastructure.yaml` gained `INFRA-343` (verified/P1/
regression), the first parity ledger entry to certify this ticket's real cache read/write wiring
into the live gateway. `INFRA-341`'s `v2_evidence` line-number citations into
`tools/retrieval_cache.py` were corrected in place (drifted from this ticket's own additions to
that file — new top-of-file import bootstrap, `migration_003`, and the Level 1 read/write
functions all shifted line numbers below them); its underlying claims were otherwise unaffected.
`INFRA-342` needed no correction as of that Parity-phase snapshot (this ticket had not yet edited
`tools/knowledge_gateway_redaction.py` at that point).

**Parity correction pass, post-Security-Review fix:** once the Security-Review fix cycle edited
`tools/knowledge_gateway_redaction.py` (4→10 secret-scan patterns), `INFRA-342`'s line-number
citations into that file and its test-class counts had drifted and were corrected in place
(claims about what `REDACTION-WRITE-PATH` itself built left unchanged); `INFRA-343` gained a new
`support_boundary` sentence recording that this ticket's own Security-Review BLOCKED once on the
4-pattern baseline and re-ran to APPROVED after the fix, plus a `test_path` citation into the 16
new `tests/tools/test_knowledge_gateway_redaction.py` tests proving it. Both writes went through
`tools/parity_ledger_writer.py::write_entry()`, followed by `python3 tools/parity_index.py build`.

**Post-Security-Review fix (2026-08-16):** Security-Review ran and BLOCKED this ticket on DD5's
security-pass precondition, finding the 4-pattern §4 secret-scan baseline
(`tools/knowledge_gateway_redaction.py`, owned by the already-DONE sibling
`TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`) had concrete gaps: no named-service token formats
(GitHub, Slack), no OpenAI/Anthropic API-key formats, no generic `password`/`secret`-named
assignment, no basic-auth-in-URL pattern. Per explicit user authorization, this ticket's own
blocking gate was closed by expanding `_SECRET_SCAN_PATTERNS` from 4 to 10 entries — a narrow,
bounded fix to the sibling's file, legitimate here because this ticket's own Security-Review gate
(not the sibling's, which is already closed) required it. 16 new tests added (14 in
`TestSecretScan`, 2 in `TestNeverCacheCategories`); no existing test weakened. Combined scoped-test
total: 297 passed (was 281). `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
§4/§11 updated to record the expansion while explicitly preserving the "documented starting point,
not a production-complete secret scanner" disclosure — this is an expansion, not a claim of
completeness. (`INFRA-342`'s citations were, in fact, later corrected — see the "Parity correction
pass, post-Security-Review fix" paragraph above; this paragraph's earlier claim that no correction
was needed was superseded by that pass and is left here only for chronological accuracy of what was
known at this point in the ticket's history.) Security-Review re-ran and returned APPROVED after
independently verifying all 6 new patterns (no ReDoS/anchoring defects, correct OpenAI/Anthropic
disambiguation) and the 16 new tests.

**Verify fix (post-Verify):** `done-checker`'s first Verify pass found `INFRA-343`'s `v2_evidence`
cited the wrong lines for the no-bypass claim — `:296-298` pointed at the `source_type`/`raw_payload`
construction, not the real `evaluate_write_candidate()` call (actually at `tools/knowledge_gateway_cache.py:306`,
verdict-gated at `:307`); the PARTIAL-refusal citation was off by one line (`:283-284` vs. the real
`:282-283`). Both corrected in place via a direct edit (not `write_entry()`, since only the citation
substring changed, no schema fields) followed by `python3 tools/parity_index.py build`. The
underlying code (the actual `evaluate_write_candidate()` gate and PARTIAL check) was never in
question — only the parity ledger's pointer to it was wrong. Verify (`done-checker`) re-ran,
confirmed the correction byte-accurate, re-confirmed all 297/297 tests and the full monitoring
trail (both Architecture-Verify passes, both Security-Review passes, 3 Parity passes), and
confirmed all 13 DoD conditions PASS — verdict READY_TO_CLOSE. This ticket is now finalized and
moved to `tickets/done/`.
