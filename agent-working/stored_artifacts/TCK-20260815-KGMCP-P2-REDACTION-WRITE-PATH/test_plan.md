---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH
artifact_type: test_plan
tags: [ai, mcp, security]
---

# Test Plan — TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH

## Regression Surface

Existing tests that must keep passing, unmodified in behavior (this ticket adds a new module and,
at most, new test files — it should not need to edit any of these):

**Unit — `tools/retrieval_cache.py` and doc-structure guards**
- `tests/tools/test_retrieval_cache.py` (all classes, including the just-added `TestMigrations` and
  the new `TestCrashRecovery` sibling method) — this ticket must not alter `LEVEL1_CACHE_COLUMNS`,
  `migration_001_add_level1_tables()`, or any of the 3 legacy marker-only tables without an explicit,
  separately-justified reason (see Anti-Drift Hazards in investigation.md re: the
  `redaction_policy_version` column gap).
- `tests/docs/test_redaction_retention_policy_doc.py` — all 6 tests, especially
  `test_sqlite_defaults_not_silently_implemented` (must keep passing precisely because this ticket's
  §9 work must land in the *new* module, never in `tools/retrieval_cache.py`) and
  `test_redaction_retention_policy_doc_exists_and_has_required_sections` (must keep passing
  unmodified unless this ticket's own Document-Update phase deliberately edits §6/§9's tense — in
  which case this test's literal-phrase assertions may need a corresponding, deliberate update
  mirroring `test_token_counting_method_returns_integer_compatible_with_budget_schema`'s own
  precedent for a tense-correction; not to be done silently).
- `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`
  — the 4-path banned tuple (`search_mcp.py`, `hybrid_retrieval.py`, `context_packet_assembler.py`,
  `retrieval_events.py`) must remain unedited by this ticket; a new module path is not in this tuple
  and needs no change here.
- `tests/tools/test_retrieval_events.py::TestFieldShapeConstant` — the version-constant-distinctness
  test pattern this ticket's own `redaction_policy_version` distinctness test should mirror; must
  keep passing unmodified (`retrieval_event_schema_version` is untouched by this ticket).
- `tests/agent_codex_posttool_adapter/test_redaction.py` — unrelated subsystem (per the policy doc's
  own §4 disclaimer); must remain unaffected — a regression here would indicate an accidental import
  or name collision between the new redaction module and this pre-existing, differently-scoped one.

**Integration**
- `tests/tools/test_knowledge_gateway_contract_schemas.py`,
  `tests/tools/test_knowledge_gateway_mcp.py`,
  `tests/tools/test_knowledge_gateway_router.py`,
  `tests/tools/test_knowledge_gateway_packet_assembly.py` — none of these should observe any change,
  since this ticket touches none of the 3 live-gateway files; run as a scope-guard, not because logic
  they cover changed.

## New Tests Required

Per acceptance criteria — new tests live in a new test file mirroring the new module's name (e.g.
`tests/tools/test_<new_module_name>.py`, Plan's naming decision; suggested
`tests/tools/test_knowledge_gateway_redaction.py` if the module is
`tools/knowledge_gateway_redaction.py`, following the `knowledge_gateway_*` naming precedent already
used by the 3 live-gateway files).

**§2 Allowlist**
- `test_allowlist_accepts_context_search_source_type` — unit — verifies a Context Search-tagged
  candidate passes the allowlist check.
- `test_allowlist_accepts_graphify_source_type` — unit — verifies a Graphify-tagged candidate passes.
- `test_allowlist_rejects_unlisted_source_type` — unit — verifies any source type not named in §2
  (e.g. a raw filesystem read, a live shell stdout, an arbitrary tool-call payload) is rejected
  outright by the allowlist check, independent of redaction/secret-scan/size outcomes.
- Located in the new module's test file.

**§3 Redaction Rules**
- `test_redaction_replaces_local_username_in_home_path` — unit — input containing `/home/<user>/...`
  or `C:\Users\<user>\...` produces output with the fixed placeholder token, never the real username.
- `test_redaction_replaces_machine_specific_absolute_path` — unit — a local absolute path not
  resolvable to a repo-relative path is replaced with the placeholder; a local absolute path that
  *is* under the repo root is rewritten to its repo-relative form (per §3's "or rewritten to the
  repository-relative path when one exists").
- `test_redacted_hash_differs_from_unredacted_hash_for_same_input` — unit — **AC-mandated**: hash
  the same raw content before and after redaction; assert the two hashes differ.
- `test_only_redacted_hash_is_ever_returned_for_persistence` — unit — the write-path decision
  function's return value must expose only the redacted-content hash field, never an unredacted
  hash field, for content that required redaction.
- `test_redaction_runs_before_hashing_order_is_enforced` — unit — construct input where redaction
  changes content (so pre/post hashes provably differ) and assert the function's hashing step
  observably operates on already-redacted text, not raw text (e.g. by asserting the returned hash
  matches `hash(redact(x))` and not `hash(x)`).

**§4 Secret-Scan Baseline (4 patterns × detection + rejection, per AC)**
- `test_secret_scan_detects_aws_style_access_key_id` — unit — `AKIA` + 16 alnum chars matches.
- `test_secret_scan_rejects_write_on_aws_key_match` — unit — a payload containing the above must
  cause the write-decision function to return REJECT, never a redacted-and-stored verdict.
- `test_secret_scan_detects_generic_api_key_assignment` — unit — `api_key = "..."` /
  `apikey: '...'` (>=16 chars) shapes match.
- `test_secret_scan_rejects_write_on_api_key_match` — unit — REJECT, not redact-and-store.
- `test_secret_scan_detects_pem_private_key_header` — unit — `-----BEGIN RSA PRIVATE KEY-----` (and
  the `EC `/`OPENSSH ` variants, and the bare form) matches.
- `test_secret_scan_rejects_write_on_pem_header_match` — unit — REJECT.
- `test_secret_scan_detects_bearer_token` — unit — `Bearer <20+ char token>` matches.
- `test_secret_scan_rejects_write_on_bearer_token_match` — unit — REJECT.
- `test_secret_scan_clean_content_is_not_rejected` — unit — a negative-control payload with none of
  the 4 shapes passes the secret-scan step (guards against overly-broad regex false positives that
  would silently block all legitimate content).
- `test_secret_scan_match_short_circuits_before_size_cap_or_redaction_store` — unit — a
  secret-scan-matching payload is rejected even if it would otherwise pass allowlist/size-cap,
  confirming §4's "never silently redacted and stored" rule is not bypassable by ordering.

**§5 Payload Size Cap**
- `test_payload_under_cap_is_accepted` — unit — a redacted UTF-8 payload just under 8192 bytes
  passes the size check.
- `test_payload_exactly_at_cap_is_accepted` — unit — boundary case, exactly 8192 bytes.
- `test_payload_over_cap_is_rejected_not_truncated` — unit — **AC-mandated**: a payload of 8193+
  bytes causes REJECT; assert the function does not return any truncated variant of the payload
  (i.e. no partial-content success path exists).
- `test_size_cap_measured_on_redacted_not_raw_payload` — unit — construct a raw payload that exceeds
  8192 bytes only before redaction (e.g. many long local-path occurrences that shrink to short
  placeholders after redaction) and confirm the cap is evaluated against the *redacted* byte length,
  per §5's explicit "measured on the UTF-8-encoded redacted payload" wording.

**§6 `redaction_policy_version`**
- `test_redaction_policy_version_is_stamped_on_every_write_decision` — unit — every returned
  decision object (ALLOW and REJECT alike, if REJECT still carries policy metadata) carries
  `redaction_policy_version` with the current value.
- `test_redaction_policy_version_distinct_from_retrieval_version` — unit — mirrors
  `tests/tools/test_retrieval_events.py::TestFieldShapeConstant::test_schema_version_constant_distinct_from_cache_key_version_constant`
  — assert `redaction_policy_version != tools.retrieval_cache.RETRIEVAL_VERSION`-shape identity (by
  value or by name-absence-from-sibling-module's `dir()`), and likewise distinct from
  `retrieval_cache_schema_version` and `retrieval_event_schema_version`. AST- or `dir()`-based,
  following the existing precedent's static-check style.

**§7 Never-Cache Enumeration (each of the 6 categories independently testable, per ticket's explicit "not a single catch-all" requirement)**
- `test_never_cache_rejects_secrets_or_credentials` — unit.
- `test_never_cache_rejects_tokens` — unit (distinct from the §4 Bearer-token regex test — this
  proves the categorical enumeration rule is enforced even for a token shape not matched by any of
  the 4 §4 regexes, if the module implements this as a genuinely separate check; if the
  implementation folds token-rejection entirely into §4's secret-scan, this test should assert that
  explicitly and document the fold as a real design decision, not silently skip the category).
- `test_never_cache_rejects_raw_environment_values` — unit — a payload containing an env-var-shaped
  raw value is rejected.
- `test_never_cache_rejects_unredacted_sensitive_tool_output` — unit — content that has not passed
  the §3 redaction step and §4 secret-scan step is rejected, not silently allowed through.
- `test_never_cache_rejects_arbitrary_config_file_contents` — unit — raw config-file text (as
  opposed to a hash/path reference to it) is rejected.
- `test_never_cache_rejects_unrestricted_raw_prompts` — unit — full unprocessed prompt text (as
  opposed to the normalized/hashed query form) is rejected.
- `test_never_cache_categories_are_independently_enforced` — architecture guard — construct 6 inputs,
  each violating exactly one category and satisfying every other rule; assert each is individually
  rejected by its own dedicated check, not merely coincidentally caught by an unrelated rule (proves
  "independently enforceable," not a monolithic catch-all, per the ticket's AC1 wording).

**§9 SQLite Operational Limits**
- `test_wal_mode_pragma_applied_on_connection_open` — unit — the new module's connection-opening
  helper sets `PRAGMA journal_mode=WAL`; assert via `PRAGMA journal_mode` query on the resulting
  connection.
- `test_busy_timeout_pragma_set_to_5000ms` — unit — assert via `PRAGMA busy_timeout` query.
- `test_file_permissions_set_to_0600_after_creation` — unit — create a fresh DB file via the new
  module's helper and assert `oct(path.stat().st_mode)[-3:] == "600"`.
- `test_max_db_size_check_flags_oversized_database` — unit — simulate/mock a DB file at or above 256
  MB and assert the size-ceiling check reports blocked; a DB under the ceiling reports not blocked.
- `test_write_path_wraps_statements_in_single_bounded_transaction` — unit — a multi-statement write
  helper commits exactly once per call (mirrors the `execute(...)+one commit()` shape already used
  throughout `tools/retrieval_cache.py`), never leaves an open transaction across calls.
- `test_per_key_stampede_guard_prevents_concurrent_duplicate_write` — unit/integration — two
  simulated concurrent write attempts for the same cache key; assert only one proceeds to a
  successful outcome and the second observes the guard (exact mechanism — sentinel row or
  in-process lock — is Plan's implementation choice; test asserts the observable guarantee, not the
  mechanism).
- `test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py` — **architecture guard,
  regression-proof for the existing gate** — reads `tools/retrieval_cache.py`'s source directly (same
  technique as `test_sqlite_defaults_not_silently_implemented`) and asserts none of the new §9
  functions/PRAGMA text leaked into that file; this is a belt-and-suspenders duplicate of the
  existing doc-test's guarantee, scoped from this ticket's own test suite so a regression is caught
  even if someone runs only this ticket's new file.

**§10 Cache-GC Defaults (eligibility check only — `prune()` stays manual-only, no auto-GC wiring)**
- `test_gc_eligibility_flags_expired_exact_query_result` — unit.
- `test_gc_eligibility_flags_packet_for_deleted_branch` — unit.
- `test_gc_eligibility_flags_obsolete_provider_version_row` — unit.
- `test_gc_eligibility_flags_low_use_regenerable_packet` — unit.
- `test_gc_eligibility_flags_stale_row_superseded_by_refresh` — unit.
- `test_gc_eligibility_flags_failed_incomplete_write` — unit — only a non-terminal `cache_status`,
  never a completed valid one.
- `test_gc_eligibility_never_flags_symbol_or_file_backed_evidence_on_bare_generation_bump` —
  architecture guard — **directly enforces the §10 deference rule to
  `evidence_cache_identity_contract.md` §4**: construct a row with `SYMBOL`/`FILE`-kind evidence and
  only a `PROVIDER_GENERATION` bump as the "change," assert the GC-eligibility function does NOT
  flag it for eviction.
- `test_prune_remains_the_only_eviction_call_site` — architecture guard — mirrors
  `TestPrune::test_prune_is_not_invoked_by_any_check_or_write_function` in
  `tests/tools/test_retrieval_cache.py`; asserts this ticket's new GC-eligibility function is a pure
  predicate/reporter, never itself calling `DELETE`/`prune()`, keeping automatic-GC wiring genuinely
  out of scope.

**Baseline security-pass disclosure (documentation honesty guard)**
- `test_module_docstring_preserves_non_production_complete_disclosure` — unit — reads the new
  module's own docstring/comment near the secret-scan function and asserts it states the baseline is
  a starting point pending a dedicated security-focused pass (mirrors this ticket's own Anti-Drift
  Hazard: do not present the baseline as more complete than the ratified doc claims).

## Scoped Pytest Commands

```
pytest tests/tools/test_retrieval_cache.py tests/docs/test_redaction_retention_policy_doc.py \
  tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_retrieval_events.py \
  tests/tools/test_<new_module_name>.py -v
```

Plus, as a scope guard confirming zero drift into the live gateway files:

```
pytest tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_knowledge_gateway_mcp.py \
  tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_packet_assembly.py -v
```

Never `pytest tests/` (unscoped), per CLAUDE.md's testing rule.

## Anti-Drift Test Guards

- **`test_sqlite_defaults_not_silently_implemented` (existing, `tests/docs/test_redaction_retention_policy_doc.py`)**
  must be re-run and pass unmodified after this ticket's §9 work lands — the single strongest guard
  against the §9-logic-landing-in-the-wrong-file mistake this investigation specifically flagged.
- **`test_no_live_gateway_code_or_search_mcp_edits_introduced` (existing,
  `tests/tools/test_kgmcp_measurement_baseline.py`)** must be re-run and pass unmodified — catches
  any accidental edit to `search_mcp.py`/`hybrid_retrieval.py`/`context_packet_assembler.py`/
  `retrieval_events.py`.
- **`test_never_cache_categories_are_independently_enforced`** (new, above) is itself an anti-drift
  guard against collapsing the 6 never-cache categories into one catch-all check, which the ticket's
  own AC explicitly forbids.
- **`test_prune_remains_the_only_eviction_call_site`** (new, above) guards against silently wiring
  automatic GC into a hot path, which would violate §10's explicit "does not change `prune()`'s
  current manual-only status" framing and the Durable State Rule's authoritative-application-path
  discipline.
- **A new static/AST test asserting the new module never imports from
  `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, or
  `tools/knowledge_gateway_mcp.py`** — mirrors the existing
  `tests/tools/test_context_packet_assembler.py::TestWorkflowIsolationGuards::test_assembler_does_not_import_contextpacket_from_retrieval_cache`
  pattern; guards against accidental live-gateway coupling given this ticket explicitly builds
  functions the *next* ticket wires in, not this one.
- **A test asserting the new write-decision function never calls `sqlite3.Connection.execute` with
  an `INSERT`/`UPDATE` statement against `retrieval_provider_result_cache_rows`** — AST-based scan
  of the new module's source for `INSERT INTO retrieval_provider_result_cache_rows` /
  `UPDATE retrieval_provider_result_cache_rows` literal text, asserting absence — guards against this
  ticket silently absorbing child 3's (`CACHE-READ-WRITE-WIRING`'s) job.
