---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING
phase: done
date: 2026-08-16
tags: [ai, mcp, security]
---

# TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING

## Title
Wire real Level 2 context-packet cache lookup and write into the live `_run_knowledge_context()`,
checked before Level 1

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` builds the Level 2 schema;
`TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT` builds real deduplicated, budget-enforced
packet assembly; `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` builds packet dependency
records and targeted invalidation. This ticket wires all three into the real, already-shipped
`_run_knowledge_context()` call path: on `knowledge_context`, check Level 2 (the assembled-packet
cache) FIRST for an exact packet match, serve a real hit when valid, and only on a genuine Level 2
miss fall back to Level 1 (the already-wired provider-result cache from Phase 2) or, on a further
miss, live providers — mirroring `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s own precedent of
adding a layer around Phase 1's existing pipeline, not redesigning it. This ticket adds a layer, it
does not redesign the existing Level 0/1 pipeline Phase 1/Phase 2 already shipped.

## Scope
- Implement Level 2 lookup identity (packet-level equivalent of §1's normalized_intent/
  resolved_entity_ids/filters/budget_class/routing_policy_version/repo_branch_scope) as the real
  key computed from a real `knowledge_context` request, reusing `compute_lookup_identity()` where
  the identity shape is genuinely the same as Level 1's, extending it only where a packet-level
  identity genuinely differs (e.g. budget_tokens as part of the key, since two requests for the same
  question at different budgets may need different assembled packets).
- On a Level 2 hit (exact packet match, dependency-invalidation-checked per the dependency ticket's
  real logic), return the cached, already-assembled, already-redacted packet payload without
  reassembling from Level 1/live providers.
- On a Level 2 miss, fall through to Level 1's already-wired provider-result cache lookup exactly as
  it already works today (Phase 2's real, unmodified behavior), assemble the packet using the
  dedup/budget-enforcement ticket's real logic, then write the result through the Level 2
  write-path before returning it.
- **Explicit re-verification requirement, not an assumption:** independently verify whether
  Level 1's existing write-path enforcement (`tools/knowledge_gateway_redaction.py`'s
  `evaluate_write_candidate()`, allowlist, secret-scan, `MAX_PAYLOAD_BYTES = 65536` size cap)
  correctly applies to Level 2 packet payloads too, given a packet aggregates content from
  potentially multiple provider results and may be a materially different shape/size than a single
  Level 1 row. Do not assume Level 1's write-path enforcement automatically covers Level 2 — call it
  and prove with a real test that a Level 2 write is genuinely gated through the same (or an
  explicitly justified equivalent) redaction/secret-scan/size-cap machinery, with no bypass path.
- Update `knowledge_status`'s response to include real Level 2 cache-domain fields (Level 2 entry
  counts, Level 2 hit/miss rates, Level 2 vs. Level 1 hit attribution) — distinct from, and
  additive to, Phase 2's already-real Level 1 fields.

## Out of Scope
- Any change to routing decisions (`tools/knowledge_gateway_router.py` stays untouched) beyond the
  minimal hook needed to check/write the Level 2 cache.
- Level 3 (verified reusable knowledge) caching — Phase 6.
- Semantic/fuzzy cache-key matching (Phase 5) — this ticket implements exact normalized-identity
  reuse only, at the packet level.
- Redesigning or weakening Level 1's existing lookup/write behavior — this ticket adds a Level 2
  check in front of it; Level 1's own already-tested logic (`TCK-20260815-KGMCP-P2-CACHE-READ-
  WRITE-WIRING`) is reused as-is, not modified, except for the minimal call-site change needed to
  fall through from a Level 2 miss.
- Assuming (rather than verifying) that Level 1's write-path enforcement covers Level 2 payloads —
  see the Scope section's explicit re-verification requirement; if verification finds a genuine gap,
  closing that gap is in scope for this ticket (it is the ticket that makes Level 2 writes live), but
  silently assuming coverage without checking is explicitly disallowed.
- Cache-GC scheduling/automation beyond what the dependency-invalidation ticket already defines.

## Acceptance Criteria
- [x] An identical repeated `knowledge_context` call (same normalized intent/entity IDs/filters/
      budget class/budget_tokens) produces a genuine Level 2 cache hit on the second call — verified
      by a real test proving the second call never reaches packet assembly or the Level 1 lookup at
      all (not merely that it skips live providers).
      (`test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit`)
- [x] A Level 2 miss correctly falls through to Level 1's existing, unmodified lookup behavior —
      verified by a real test showing Level 1 is still consulted on a Level 2 miss, exactly as
      before this ticket landed.
      (`test_level2_miss_falls_through_to_unmodified_level1_lookup`)
- [x] A Level 2 hit is rejected and refreshed when the underlying packet's dependency-invalidation
      logic (from the dependency ticket) determines it stale — real test, not a documentation claim.
      (`test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`,
      `test_level2_hit_rejected_on_provider_generation_bump_real_call`)
- [x] Level 2 cache writes are independently verified — not assumed — to go through real redaction/
      secret-scan/size-cap enforcement with no bypass path; if this required extending or adapting
      Level 1's existing `evaluate_write_candidate()` call for packet-shaped payloads, that
      extension itself is tested.
      (`test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert`,
      `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`,
      `test_level2_write_reject_verdict_results_in_zero_rows_written`,
      `test_level2_write_stamps_redaction_policy_version_column`,
      `test_level2_write_respects_max_payload_bytes_size_cap_with_real_measured_packet`)
- [x] Branch/working-tree scope from the dependency ticket is genuinely enforced before a Level 2
      hit is served — real test.
      (`test_level2_cached_result_from_feature_branch_not_served_on_different_branch`)
- [x] `knowledge_status`'s Level 2 cache-domain fields are real and populated from the real Level 2
      cache, distinct from Level 1's existing fields.
      (`test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1`,
      `test_knowledge_status_level2_fields_omitted_when_level2_cache_has_zero_rows`,
      `test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db`)
- [x] `tools/knowledge_gateway_router.py` remains byte-unchanged.
      (`test_knowledge_gateway_router_py_provably_untouched`; independently confirmed via
      `git status`/`git diff HEAD -- tools/knowledge_gateway_router.py` showing no change)
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this
      ticket's own behavior change, per this repo's own governance rule.
      (`INFRA-349`, added via the schema-validating writer in the Parity phase.)

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (parent)
- TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS (dependency)
- TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT (dependency)
- TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION (dependency)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; the real Level 1 wiring this ticket falls
  through to on a Level 2 miss — read, do not modify beyond the minimal call-site hook)
- TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION (DONE; the real `MAX_PAYLOAD_BYTES = 65536`
  value this ticket's write-path re-verification checks against Level 2 payload sizes)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2, §10.3, §12.1-§12.3, §20 Phase 3, §21
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §4, §5, §6, §11 (the
  write-path enforcement this ticket must verify, not assume, applies to Level 2 payloads)
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py` (`_run_knowledge_context()`, `_run_knowledge_status()` — the
  request-handling hook points this ticket extends)
- `tools/knowledge_gateway_cache.py` (Level 1's real orchestration module — the direct structural
  precedent for this ticket's Level 2 orchestration; may be extended in place or given a Level 2
  sibling module, per this ticket's own Investigate-phase decision)
- `tools/retrieval_cache.py` (Level 2 schema/read/write functions this ticket calls)
- `tools/knowledge_gateway_redaction.py` (the write-path enforcement this ticket's own scope
  requires independently re-verifying against Level 2 payload shapes)

## Assumptions / Open Questions
- Whether the Level 2 orchestration lives inside `tools/knowledge_gateway_cache.py` (extended in
  place) or a new sibling module (e.g. `tools/knowledge_gateway_packet_cache.py`) is not decided
  here — Investigate should decide based on the real, already-landed Level 1 module structure,
  minimizing invasiveness, consistent with how the Level 1 wiring ticket itself made this same
  choice for its own module.
- Whether Level 1's `evaluate_write_candidate()` needs a genuine code change to correctly handle
  packet-shaped payloads (multi-source aggregated content) versus working unmodified because its
  redaction/scan logic already operates on raw text regardless of source shape, is the central open
  question this ticket's own Investigate phase must resolve — not assumed either way here.
- Whether budget_tokens should be part of the Level 2 lookup-identity key (two different budgets for
  the same question producing two different cached packets) or handled by re-deriving a smaller
  packet from one canonical cached packet is left open — Investigate/Plan should decide with
  reference to the dedup/budget-enforcement ticket's own chosen tolerance mechanism.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING/plan.md`'s
10 ordered steps (Steps 1-6 and Step 10 — code + tests; Steps 7-9, the `intentional_divergences.md`
§2.45 entry, the `docs/parity_ledger/infrastructure.yaml` entry, and the proposal §20 annotation,
are explicitly deferred to the Document-Update/Parity phases per this Implement run's own scope).

- **Step 1** (`tools/retrieval_cache.py`): added `redaction_policy_version`, `budget_truncated`,
  `omitted_statement_count`, `provider_failures` to `LEVEL2_CACHE_COLUMNS`; added
  `migration_004_add_level2_write_path_columns(conn)`, mirroring `migration_003`'s idempotent
  `PRAGMA table_info`/`ALTER TABLE` pattern per column.
- **Step 2** (`tools/retrieval_cache.py`): added `ContextPacketCacheLookup` dataclass,
  `_ensure_level2_schema_for_read()`, `_get_level2_connection()`, `check_context_packet_cache()`
  (queries by non-unique `query_key_hash` via `.fetchall()`, disambiguates in Python against
  `normalized_intent`/`entity_ids`/`repository_id`/`branch`/`budget_requested` — never
  `.fetchone()`), `write_context_packet_cache()`, `record_context_packet_cache_hit()`,
  `context_packet_cache_stats()`.
- **Step 3** (`tools/knowledge_gateway_cache.py`): added `CONTEXT_PACKET_RESPONSE_SCHEMA_VERSION`
  constant, `_current_branch()`, `compute_context_packet_lookup_identity()` (includes the literal
  `budget_tokens` integer per PD2 — the intentional divergence itself is implemented in code here;
  its `intentional_divergences.md` §2.45 documentation entry is deferred, see above),
  `_current_provider_generations_for()`, `_context_packet_row_to_response()` (never sets `mode`,
  per PD5), `perform_context_packet_cache_lookup()`, `perform_context_packet_cache_write()`. None
  of the existing Level 1 functions (`compute_lookup_identity`, `perform_cache_lookup`,
  `perform_cache_write`, `revalidate_context_packet_row`, `_level2_repo_branch_scope`) were
  modified.
- **Step 4**: added `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`
  and `test_level2_lookup_function_never_returns_a_freshness_or_verification_field` to
  `tests/tools/test_knowledge_gateway_cache.py`.
- **Step 5** (`tools/knowledge_gateway_mcp.py`): inserted a Level 2 check-then-fall-through hook
  immediately before the existing Level 1 cache-check hook in `_run_knowledge_context()` (own
  independent fail-open `try/except`), returning `cache: "HIT_L2"` early before `assemble_packet()`
  on a genuine hit; inserted a Level 2 write hook (own independent fail-open `try/except`,
  separate from Level 1's) immediately before the existing Level 1 write hook on the miss path.
  Neither Level 1 hook's own body was touched, only the surrounding call sequence.
- **Step 6** (`tools/knowledge_gateway_mcp.py` + `knowledge_status_response.schema.json`): added
  Level 2 `cache_entry_counts` (`kind: "context_packet"`), `level2_cache_hit_rate`,
  `level2_cache_miss_rate`, `cache_hit_attribution` fields to `_run_knowledge_status()`, additive
  and omitted entirely when Level 2 has zero rows (never a fabricated placeholder). Schema updated
  additively (no `schema_version` bump), consistent with the sibling ticket's own precedent.
- **Step 10**: added `test_knowledge_gateway_router_py_provably_untouched` to
  `tests/tools/test_knowledge_gateway_mcp.py`; independently confirmed via `git status`/`git diff`
  that `tools/knowledge_gateway_router.py` was never touched.

**Type-coercion check (Architecture Review's flagged non-blocking item):** verified directly —
`budget_requested` is stored as `INTEGER` (per `migration_002`'s `CREATE TABLE`), and
`check_context_packet_cache()` compares the stored value directly against the caller's Python
`int` with no coercion. SQLite's INTEGER affinity returns a native Python `int` on read, so no
type-mismatch false-MISS risk exists here — unlike Level 1's `routing_policy_version`, which is
stored as `TEXT` and requires `str()` coercion. No coercion was added since none is needed; this is
documented in `check_context_packet_cache()`'s own docstring.

**Deviations from the literal plan text (see `plan.md`'s own "Deviations" section for full
detail), discovered via real test execution, not anticipated in advance:**
1. `_get_level2_connection()`/`_ensure_level2_schema_for_read()` must also call
   `migration_001_add_level1_tables(conn)` before `migration_002_add_level2_tables(conn)` —
   `migration_002` itself assumes `retrieval_cache_generation` (created only by `migration_001`)
   already exists, and Level 2's hooks now run before Level 1's on a fresh DB.
2. The pre-existing `test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list`
   was updated to also run `migration_004` before comparing columns, mirroring the exact precedent
   the Level 1 sibling ticket already set for `migration_003`.
3. Five pre-existing Level 1-scoped regression tests in `tests/tools/test_knowledge_gateway_mcp.py`
   were updated (not silently broken) because Level 2 being checked first genuinely changes what
   an unmodified repeat call demonstrates — each either forces Level 2's lookup (and, for the
   `knowledge_status` test, also its write) to a no-op to keep testing Level 1's own unmodified
   mechanics, or (for the `evaluate_write_candidate` call-count test) is updated to assert the
   correct doubled call count that Risk 6's own required double-write behavior produces.

## Test Summary

Ran the full KGMCP test surface named in `test_plan.md`'s Scoped Pytest Commands section:

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_cache.py \
  tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_retrieval_cache.py \
  tests/tools/test_knowledge_gateway_redaction.py \
  tests/tools/test_knowledge_gateway_contract_schemas.py \
  tests/tools/test_knowledge_gateway_packet_assembly.py \
  tests/docs/test_redaction_retention_policy_doc.py -q
```

Result: **284 passed, 0 failed** (11 pre-existing `jsonschema.RefResolver` deprecation warnings,
unrelated to this ticket).

Per-file breakdown of this ticket's own new/modified tests:
- `tests/tools/test_retrieval_cache.py`: 83 passed (new: `TestMigration004` (2), `TestContextPacketCache`
  (12, including `test_level2_lookup_disambiguates_multiple_rows_sharing_the_same_query_key_hash`
  and the budget-tokens disambiguation test), `TestContextPacketCacheStats` (3, including
  `test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db`); updated:
  `test_check_and_write_functions_now_exist_for_the_new_level2_table` (inverted from the old
  no-functions-exist guard), `test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list`).
- `tests/tools/test_knowledge_gateway_cache.py`: 32 passed (new:
  `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`,
  `test_level2_lookup_function_never_returns_a_freshness_or_verification_field`).
- `tests/tools/test_knowledge_gateway_mcp.py`: 35 passed (new: 18 tests covering AC1-AC7 plus the
  fail-open and double-write cross-cutting guards; updated: 5 pre-existing Level 1-scoped
  regression tests, per Deviations above).
- `tests/tools/test_knowledge_gateway_redaction.py`,
  `tests/tools/test_knowledge_gateway_contract_schemas.py`,
  `tests/tools/test_knowledge_gateway_packet_assembly.py`,
  `tests/docs/test_redaction_retention_policy_doc.py`: unmodified by this ticket, all passing
  (regression confirmation only).

**Post-Implement Test-phase gap-check (independent pass, not the Implement run above):** ran the
same scoped command again after mapping the 3 changed `tools/` files to their full relevant test
surface. All 8 ACs' named tests were verified to genuinely exist via `grep -rn "def <name>"`
(no prose-only claims). Three real, previously-untested gaps were found and closed with new tests
(all following this session's own naming/docstring conventions, no existing test modified):
- **Double-write failure independence (Risk 6 / plan.md Step 5(b)):** the existing
  `test_level2_double_write_on_full_miss_writes_both_level1_and_level2_rows` and the two
  `*_fail_open_and_never_blocks_the_provider_path` tests only proved both writes succeed together,
  or that breaking *both* levels at once still degrades gracefully — neither proved the Level
  2/Level 1 write hooks' two separate `try/except` blocks (`tools/knowledge_gateway_mcp.py:353-368`)
  are genuinely independent of each other's failure. Closed with
  `test_level2_write_failure_does_not_prevent_or_corrupt_the_level1_write` and
  `test_level1_write_failure_does_not_prevent_or_corrupt_the_level2_write` in
  `tests/tools/test_knowledge_gateway_mcp.py`.
- **Migration-ordering fix (Deviation 1), explicit assertion:** the deviation (must call
  `migration_001_add_level1_tables()` before `migration_002_add_level2_tables()` in
  `_get_level2_connection()`/`_ensure_level2_schema_for_read()`, since `migration_002` assumes
  `retrieval_cache_generation` already exists) was already incidentally exercised by
  `test_check_context_packet_cache_creates_table_on_first_real_use` (would raise
  `sqlite3.OperationalError` without the fix), but no test explicitly named or asserted the fix's
  actual effect (both migrations' tables/rows present on a genuinely fresh, non-existent DB file
  touched via Level 2 first). Closed with
  `test_fresh_nonexistent_db_gets_migration_001_applied_before_migration_002_on_first_level2_access`
  in `tests/tools/test_retrieval_cache.py`.
- `knowledge_status`'s new Level 2 fields being populated from a real cache (not just schema-shape)
  and the zero-row/unmigrated-DB edge cases were both already genuinely covered (
  `test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1`
  performs real writes/hits and checks real computed rates;
  `test_knowledge_status_level2_fields_omitted_when_level2_cache_has_zero_rows` and
  `test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db` cover the
  zero-row/unmigrated cases) — no gap, no new test needed. True concurrent-access testing was not
  added: no other test in this ticket's surface exercises literal thread-level concurrency against
  SQLite, so adding it here would be inconsistent with the rest of the suite's own scope.

Re-ran the full scoped command after the additions:
```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_cache.py \
  tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_retrieval_cache.py \
  tests/tools/test_knowledge_gateway_redaction.py \
  tests/tools/test_knowledge_gateway_contract_schemas.py \
  tests/tools/test_knowledge_gateway_packet_assembly.py \
  tests/docs/test_redaction_retention_policy_doc.py -q
```
Result: **287 passed, 0 failed** (284 + the 3 new gap-closing tests; same pre-existing
`jsonschema.RefResolver` deprecation warnings, unrelated to this ticket).

## Files Changed

- `tools/retrieval_cache.py` — Steps 1-2 (migration_004, Level 2 read/write/stats functions)
- `tools/knowledge_gateway_cache.py` — Step 3 (Level 2 lookup identity + orchestration)
- `tools/knowledge_gateway_mcp.py` — Steps 5-6 (hook wiring in `_run_knowledge_context()`/
  `_run_knowledge_status()`)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json` — Step 6
  (additive `level2_cache_hit_rate`/`level2_cache_miss_rate`/`cache_hit_attribution` fields)
- `tests/tools/test_retrieval_cache.py` — Step 1/2 tests + AC3/AC4/AC6 tests; Test-phase gap-check
  addition: `test_fresh_nonexistent_db_gets_migration_001_applied_before_migration_002_on_first_level2_access`
- `tests/tools/test_knowledge_gateway_cache.py` — Step 4 tests + Non-collapse-rule test
- `tests/tools/test_knowledge_gateway_mcp.py` — Steps 5/6/10 integration tests (AC1, AC2, AC3,
  AC4, AC5, AC6, AC7, fail-open, double-write) + 5 updated pre-existing regression tests;
  Test-phase gap-check additions:
  `test_level2_write_failure_does_not_prevent_or_corrupt_the_level1_write`,
  `test_level1_write_failure_does_not_prevent_or_corrupt_the_level2_write`
- `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING/plan.md` — Deviations
  section appended

Not touched (verified, per Out of Scope/AC7): `tools/knowledge_gateway_router.py`,
`tools/search_mcp.py`, `tools/retrieval_events.py`,
`tools/knowledge_gateway_packet_assembly.py`.

### Document-Update phase

- `docs/guidelines/intentional_divergences.md` — added `### 2.45 Level 2 Lookup Identity Includes
  Exact budget_tokens, Not budget_class (TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING)`,
  immediately after `### 2.44`, mirroring its exact Old/New/Rationale/Verification/Status shape.
  Rationale class: Bounded. Verification cites
  `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit` and
  `tests/tools/test_retrieval_cache.py::TestContextPacketCache::test_level2_lookup_disambiguates_by_budget_tokens_not_just_budget_class`.
  Entries `2.1`-`2.44` and everything from `## 3.` onward left untouched.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 3 — marked the "Store and return actual
  packet payloads" bullet **Done** (`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`), citing
  the real AC1/AC2/AC3/AC4/AC5 test names, per the doc's own strict binary Done/blank convention —
  confirmed genuinely closable (Level 2 lookup+write is live in the production `_run_knowledge_context()`
  call path, not merely tested-but-unreachable) before marking. The other 3 §20 Phase 3 bullets left
  untouched (owned by sibling tickets, per their own already-closed resolutions).
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2 — found genuinely stale,
  not merely a candidate for a new-migration citation: migration 2's own annotation falsely claimed
  "No read/write logic against this table exists yet" (now false as of this ticket) — corrected in
  place. Added `migration_004_add_level2_write_path_columns` as a new, 4th ordered-migration list
  entry (previously absent from this doc entirely), following the exact idempotent-`ALTER TABLE`
  annotation shape migration 3's own entry already uses. This doc is not, in practice, frozen
  against this class of annotation edit — two prior sibling tickets already edited this same file
  the same way once a migration's body landed for real (see investigation.md's Document-Update
  correction for the full citation trail).
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §6 — appended a short
  paragraph, following the section's own established "resolved/extended by TCK-XXX" narrative
  pattern, documenting that `redaction_policy_version` persistence now also covers the Level 2 table
  (via `migration_004`) and that AC4's independent re-verification (Level 2 writes route through
  `evaluate_write_candidate()` unmodified, no bypass path) is real, tested, and cited by name
  (`test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`,
  `test_level2_write_stamps_redaction_policy_version_column`).
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — genuinely
  investigated, left untouched. §2.44 (the direct precedent for a divergence citing this contract)
  added no cross-reference footnote to this file, so §2.45 follows the same established
  no-footnote precedent rather than inventing a new convention unilaterally. Its own frozen §1/§3/
  §4/§5 rule text is unchanged. See investigation.md's "Docs Considered But Not Required" section
  for the full reasoning.
- `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING/investigation.md` —
  corrected the "Docs Requiring Update" section's own prior "not required" call on
  `cache_migration_plan.md` (found wrong during Document-Update, not merely superseded); added a
  "Docs Considered But Not Required" section resolving `evidence_cache_identity_contract.md`; noted
  the additional, not-originally-flagged `redaction_retention_policy.md` §6 edit.

Not touched by Document-Update: `docs/parity_ledger/infrastructure.yaml` (parity-updater's
exclusive territory, separate Parity phase), any `docs/mechanics/` chapter or core engine contract
(this subsystem is explicitly outside their scope), `docs/audits/` (cite-only, never edited).

## Completion Summary
Wired the Level 2 assembled-packet cache genuinely live into the production `knowledge_context`
call path. `tools/retrieval_cache.py` gained `migration_004_add_level2_write_path_columns()`
(closes the `redaction_policy_version`/`budget_truncated`/`omitted_statement_count`/
`provider_failures` write-fidelity gap this ticket's own plan.md PD4 identified, growing
`LEVEL2_CACHE_COLUMNS` 28->32) plus the real Level 2 read/write surface: `ContextPacketCacheLookup`,
`check_context_packet_cache()` (non-unique `query_key_hash` lookup via `.fetchall()`, Python-side
disambiguation — never `.fetchone()`, PD3), `_get_level2_connection()`, `write_context_packet_cache()`,
`record_context_packet_cache_hit()`, `context_packet_cache_stats()`. `tools/knowledge_gateway_cache.py`
gained `compute_context_packet_lookup_identity()` (includes the literal `budget_tokens` integer, not
`budget_class` — PD2), `perform_context_packet_cache_lookup()`/`perform_context_packet_cache_write()`
orchestrators (reusing `revalidate_context_packet_row()`/`_level2_repo_branch_scope()` from the
dependency-invalidation sibling and `evaluate_write_candidate()` from the Level 1 write path, both
unmodified), `_context_packet_row_to_response()` (never sets `mode`, PD5). `tools/knowledge_gateway_mcp.py`'s
`_run_knowledge_context()` now checks Level 2 first via its own independent fail-open hook — a
genuine hit returns `cache: "HIT_L2"` before `assemble_packet()` and before the Level 1 lookup hook
are ever reached — and writes Level 2 via its own independent fail-open hook before the Level 1
write hook on a genuine miss; `_run_knowledge_status()` gained additive `level2_cache_hit_rate`/
`level2_cache_miss_rate`/`cache_hit_attribution` fields, omitted entirely when Level 2 has zero rows.

Implement phase added 37 new tests (2 in `test_knowledge_gateway_cache.py`, 17 in
`test_retrieval_cache.py`, 18 in `test_knowledge_gateway_mcp.py`) plus updated 5 pre-existing Level
1-scoped regression tests (Deviation 3) and one pre-existing column-set test (Deviation 2); Test
phase's independent gap-check pass closed 3 further real, previously-untested gaps (double-write
failure independence, migration-ordering explicit assertion). Full scoped suite: **287 passed, 0
failed**. Document-Update recorded the intentional divergence (`intentional_divergences.md` §2.45,
Bounded — Level 2's lookup identity keys on exact `budget_tokens`, not `budget_class`, since
`assemble_within_budget()`'s truncation is driven by the literal integer) and corrected
`cache_migration_plan.md` §2's stale "no read/write logic exists yet" annotation.

Parity has now run: `INFRA-349` was added to `docs/parity_ledger/infrastructure.yaml` (verified/P1/
regression) via the schema-validating writer, citing real line numbers for every new symbol listed
above and every test named in the Implement/Test-phase Test Summary sections, with an explicit
`support_boundary` stating this is the ticket that makes Level 2 genuinely reachable from the
production `knowledge_context` call path — discharging INFRA-346's "no read/write function yet" and
INFRA-348's "not yet wired into a live lookup/write path" framing — unlike the 3 prior siblings,
which each built real-but-not-yet-wired pieces. `INFRA-343`, `INFRA-346`, `INFRA-347`, and
`INFRA-348`'s own citations into `tools/knowledge_gateway_cache.py` and/or `tools/retrieval_cache.py`
(plus `INFRA-347`'s one drifted citation into `tools/knowledge_gateway_mcp.py`) were corrected in
place (not duplicated) for line-number drift this ticket's own insertions caused — confirmed against
the real current file state via direct read, not inherited arithmetic. `python3 tools/parity_index.py
build` was run as a separate, visible call afterward. AC8 (the parity ledger entry) is now
satisfied — all eight Acceptance Criteria are complete. The remaining item is that this ticket is
still in `tickets/inprogress/` rather than `tickets/done/`; Verify/Finalize have not yet run in this
pass.
