---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION

## Regression Surface

All must keep passing unmodified in behavior/assertions — this ticket adds a new
`PacketAssembly.evidence_dependencies` field and a new packet-level revalidation function, both
additive; no existing field, function signature, or assertion should need to change.

**Unit — `tools/knowledge_gateway_packet_assembly.py`**
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (all 38 tests) — in particular:
  - Every existing `PacketAssembly` construction/field-access test — must still pass with the new
    `evidence_dependencies` field added as a dataclass field with a real computed value (never a
    required-but-unpopulated field that breaks existing direct-construction test fixtures that don't
    pass it, unless a default is supplied).
  - `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids` and the other
    dedup/budget-marker tests added by the sibling ticket — untouched by this ticket's change, since
    `evidence_dependencies` is derived from `final_evidence` (already fully computed by the time this
    ticket's new aggregation step would run) and does not feed back into dedup or truncation
    ordering.
  - The existing "Out-of-scope architecture guards"
    (`test_module_not_referenced_by_any_claude_workflows_file`,
    `test_module_introduces_zero_mcp_server_code`,
    `test_module_does_not_modify_or_import_retrieval_cache`,
    `test_module_does_not_edit_knowledge_gateway_router`) — must all still pass; this ticket does not
    touch the router, retrieval_cache, or MCP server registration from this module.

**Unit — `tools/knowledge_gateway_cache.py`**
- `tests/tools/test_knowledge_gateway_cache.py` (all 20 tests) — in particular:
  - `test_working_tree_fingerprint_uses_changed_paths_intersection_not_full_tree_hash`,
    `test_is_branch_compatible_hard_partition`,
    `test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture`,
    `test_symbol_backed_cache_row_survives_unrelated_generation_bump_fixture`,
    `test_provider_generation_fallback_used_for_both_real_providers_today` — must all still pass
    unmodified; this ticket calls `working_tree_overlap_forces_revalidation()`/
    `is_branch_compatible()` but does not change either function's own signature or logic.
  - `test_lookup_function_never_returns_a_freshness_or_verification_field` — must still pass; this
    ticket's own new function must independently satisfy the same discipline (see New Tests below),
    not weaken this existing guard's scope.
  - `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly` — **must still pass**;
    this is the single most load-bearing regression check for this ticket specifically, since
    investigation.md's central finding is that this guard is exactly why the new revalidation
    function must be added here without importing `knowledge_gateway_packet_assembly`. A failure here
    would mean the new function was implemented incorrectly (imports `PacketAssembly` where it must
    only consume a plain row dict).
  - `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module` — must still pass; this
    ticket adds no SQL/write logic to this module.

**Schema — `tools/retrieval_cache.py`**
- `tests/tools/test_retrieval_cache.py::TestLevel2Migrations` (13 tests) — must all still pass
  unmodified; this ticket does not touch `migration_002_add_level2_tables()`, `LEVEL2_CACHE_COLUMNS`,
  or the table DDL. In particular
  `test_no_actual_read_write_functions_added_for_the_new_level2_table` (the schema ticket's own
  guard, cited by `docs/guidelines/intentional_divergences.md` §2.44) must keep passing — confirms
  this ticket does not accidentally add a `check_*_cache`/`write_*_cache` pair, which is explicitly
  Out of Scope here.

**Integration — `tools/knowledge_gateway_mcp.py`**
- `tests/tools/test_knowledge_gateway_mcp.py` (all tests) — must remain fully passing; this ticket
  does not touch `_run_knowledge_context()` (explicit Out of Scope), so no response-shape or
  cache-flow assertion here should be affected.

**Adjacent-subsystem guard**
- `tests/tools/test_knowledge_gateway_router.py` — run directly as an edit-detection proxy, per the
  established sibling-ticket convention; must confirm the router stays byte-unchanged.

## New Tests Required

Per acceptance criteria, one entry per required new test:

1. **`test_evidence_dependencies_aggregated_from_packet_evidence_paths`**
   - Category: unit
   - Verifies: `PacketAssembly.evidence_dependencies` (or the new aggregation function, whichever
     Plan names) returns the real, deduplicated, sorted set of `path` values from
     `PacketAssembly.evidence` (`final_evidence`) for a packet assembled from real `context_search`-
     sourced results — i.e. the recorded dependency set genuinely equals the paths the packet's own
     constituent evidence actually depends on, not a superset of every source ever consulted (per the
     ticket's own Scope wording). Constructs a real `RoutingDecision`/monkeypatched provider call
     (mirroring this test file's existing `assemble_packet()` test fixtures) with 2+ `context_search`
     results from different paths and asserts the aggregated set matches exactly.
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

2. **`test_evidence_dependencies_excludes_paths_from_omitted_budget_truncated_statements`**
   - Category: unit — closes the "not merely a superset copy of every source ever consulted" clause
     of AC1
   - Verifies: given a budget small enough that `assemble_within_budget()` drops one or more
     statements, the resulting `evidence_dependencies` set contains only the paths backing the
     statements that actually survived truncation (`final_evidence`), never the paths of dropped
     statements — proving the aggregation runs on `final_evidence`, not the pre-truncation candidate
     set.
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

3. **`test_evidence_dependencies_omits_graphify_symbol_evidence_with_no_path`**
   - Category: unit — honesty/edge-case coverage
   - Verifies: a `graphify`-sourced statement (whose `EvidenceEntry.path` is `None`, per
     `_evidence_id_for_graphify_result()`'s own design) contributes nothing to the path-based
     `evidence_dependencies` set — confirms the aggregation correctly excludes `None` paths rather
     than crashing or inserting a literal `"None"` string, and documents (via the test's own
     docstring) that symbol-kind evidence is not path-tracked by this mechanism, mirroring the same
     limitation Level 1's own `source_paths` computation already has (`working_tree_overlap_json`
     never covers `graphify` results either — not a new gap this ticket introduces).
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

4. **`test_working_tree_overlap_forces_revalidation_called_unmodified_against_evidence_dependencies_shape`**
   - Category: architecture guard / direct-reuse proof — closes Investigate Question 1
   - Verifies: `tools.knowledge_gateway_cache.working_tree_overlap_forces_revalidation()` is called
     with the *exact* JSON string produced by this ticket's new aggregation (i.e.
     `json.dumps(sorted(evidence_dependencies))`), with no intermediate transformation, and produces
     the correct `True`/`False` result for an intersecting/non-intersecting `changed_paths` list —
     proving direct reuse, not a reimplementation, of the Level 1 primitive.
   - Where: `tests/tools/test_knowledge_gateway_cache.py` (new function under test, imported from
     `knowledge_gateway_packet_assembly` only for constructing the fixture packet, never the reverse
     import direction)

5. **`test_revalidate_context_packet_row_rejects_on_changed_paths_intersection`**
   - Category: unit — the real "a changed cited source invalidates the affected packet" AC test
   - Verifies: constructs a Level-2-row-shaped dict (`evidence_dependencies`, `repository_id`,
     `branch`, `provider_generations` — matching `LEVEL2_CACHE_COLUMNS`' real column names) whose
     `evidence_dependencies` includes a path, calls the new packet-level revalidation function with a
     `changed_paths` list containing exactly that path, and asserts the function returns `False`
     (stale/invalidate).
   - Where: `tests/tools/test_knowledge_gateway_cache.py`

6. **`test_revalidate_context_packet_row_survives_unrelated_changed_path`**
   - Category: unit — the real "an unrelated changed source does not invalidate a packet with no
     dependency overlap" AC test
   - Verifies: same row fixture as test 5, but `changed_paths` contains only paths disjoint from
     `evidence_dependencies` — asserts the function returns `True` (still valid).
   - Where: `tests/tools/test_knowledge_gateway_cache.py`

7. **`test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies`**
   - Category: unit — the real "branch identity remains a hard partition at the packet level" AC test
   - Verifies: two row/current-scope pairs with byte-identical `evidence_dependencies` and
     `provider_generations` but different `branch`/`repository_id` values — asserts the function
     (or the branch-compatibility check it calls first) returns `False`/rejects, and that the branch
     check runs *before* any fingerprint/generation comparison is even consulted (per §5 rule 2's
     "before any fingerprint comparison is even consulted" wording) — assert via a call-order
     mechanism (e.g. a spy on the generation-comparison step never being invoked when branch check
     already fails), mirroring `revalidate_cache_row()`'s own existing short-circuit structure.
   - Where: `tests/tools/test_knowledge_gateway_cache.py`

8. **`test_revalidate_context_packet_row_survives_new_commit_alone_unchanged_generations`**
   - Category: unit — the real "a new commit alone, with unchanged evidence fingerprints, does not
     force a packet cache miss" AC test, mirroring §5's Level 1 precedent
     (`test_symbol_backed_cache_row_survives_unrelated_generation_bump_fixture`'s own pattern)
   - Verifies: row fixture with `provider_generations` matching the current real corpus generation
     (via `rc._corpus_generation()`, mirroring Level 1's own test convention) and an empty
     `changed_paths` list — asserts the function returns `True` regardless of any commit-SHA-shaped
     value never being consulted at all (since neither Level 1 nor Level 2's schema stores or checks
     a commit SHA for this decision — only `head_commit` exists as a provenance-only column, never
     read by the revalidation function; assert this by confirming the function's signature/body never
     references `head_commit`).
   - Where: `tests/tools/test_knowledge_gateway_cache.py`

9. **`test_revalidate_context_packet_row_multi_provider_generations_dict_all_checked`**
   - Category: unit — closes Investigate Question 2's own finding (packet-level generation check is
     genuinely dict-shaped, not a single-string reuse)
   - Verifies: a row fixture whose `provider_generations` dict has two entries
     (`{"context_search": "gen-1", "graphify": "gen-1"}`), and a "current" generations dict where only
     one provider's value has changed (`{"context_search": "gen-2", "graphify": "gen-1"}`) — asserts
     the function correctly detects the mismatch (returns `False`) using the dict comparison, proving
     the function is genuinely multi-provider-aware and not hardcoded to read a single string field.
   - Where: `tests/tools/test_knowledge_gateway_cache.py`

10. **`test_revalidate_context_packet_row_never_returns_freshness_or_verification_field`**
    - Category: architecture guard — Non-collapse rule (§3) compliance for this ticket's own new
      function, independent of the schema ticket's own §2.44 divergence (which concerns the schema's
      column co-location, not this ticket's function contract)
    - Verifies: the new revalidation function's return type/shape carries no `freshness`/
      `verification` field — asserted via `inspect.signature()`/return-type check or, if the
      function returns a small dataclass rather than a bare `bool`, a field-name assertion mirroring
      `test_lookup_function_never_returns_a_freshness_or_verification_field`'s own existing pattern.
    - Where: `tests/tools/test_knowledge_gateway_cache.py`

11. **`test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket`**
    - Category: architecture guard (anti-scope-creep) — enforces the schema ticket's own Anti-Drift
      Hazard that this ticket must not add a junction table "to help"
    - Verifies: `tools/retrieval_cache.py` (if touched at all by this ticket, which is expected to be
      untouched per Out of Scope) contains no new `CREATE TABLE` statement beyond
      `migration_002_add_level2_tables()`'s existing single table — a `git diff --stat` /source-text
      check confirming `tools/retrieval_cache.py` is byte-unchanged by this ticket's own diff, since
      this ticket's Out of Scope explicitly excludes all schema/table work.
    - Where: `tests/tools/test_knowledge_gateway_cache.py` or a new dedicated architecture-guard test
      file, Plan to decide exact location.

12. **`test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`** (existing, re-run
    as a direct proof this ticket's own new revalidation function did not violate the guard)
    - Category: architecture guard — regression re-confirmation, not new logic, but explicitly called
      out here since it is the single test whose continued passing most directly proves this ticket's
      central architectural finding was actually implemented correctly, not just documented.
    - Where: `tests/tools/test_knowledge_gateway_cache.py` (already exists — see Regression Surface)

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v
python3 -m pytest tests/tools/test_knowledge_gateway_cache.py -v
python3 -m pytest tests/tools/test_retrieval_cache.py::TestLevel2Migrations -v
python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -q
python3 -m pytest tests/tools/test_knowledge_gateway_router.py -q
```

Never `pytest tests/` — scoped to the Knowledge Gateway MCP subsystem's own 5 direct test files/
classes (the two modules this ticket edits, the Level 2 schema-guard class it must not disturb, and
the two adjacent modules — MCP tool surface and router — that must stay behaviorally/byte
unchanged).

## Anti-Drift Test Guards

- **`test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`** (existing, see New
  Test 12 above) — the single most important anti-drift guard for this ticket: any future change
  that makes the packet-level revalidation function "convenient" by importing `PacketAssembly`
  directly instead of consuming a plain row dict would fail this test, catching exactly the
  architectural mistake this ticket's own investigation identifies as the central design constraint.
- **`test_no_actual_read_write_functions_added_for_the_new_level2_table`** (existing, schema
  ticket's own guard, `tests/tools/test_retrieval_cache.py`) — re-run to confirm this ticket does not
  silently absorb the read/write-wiring ticket's own scope by adding a
  `check_context_packet_cache()`/`write_context_packet_cache()` pair "for convenience."
- **`test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket`** (New Test 11 above) —
  guards against the schema ticket's own explicitly-forbidden junction-table drift.
- **`test_evidence_dependencies_omits_graphify_symbol_evidence_with_no_path`** (New Test 3 above) —
  doubles as an anti-drift guard: a future change that tries to "fix" the symbol-evidence path gap by
  inventing a synthetic path value (rather than correctly leaving it un-path-tracked, consistent with
  Level 1's own identical limitation) would fail this test's exact-set assertion.
- **`test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies`** (New
  Test 7 above) — guards against a future refactor accidentally reordering the branch check after the
  generation/fingerprint comparison, which would silently reintroduce cross-branch reuse risk (§5
  rule 2's explicit "before any fingerprint comparison is even consulted" ordering requirement).
- **Parity-ledger schema validity**: the new `INFRA-348` entry must validate against
  `docs/parity_ledger/schema.json` — run via the repo's existing parity-ledger validation tooling as
  part of the Parity phase, not this ticket's pytest scope; flagged here so Test-phase does not treat
  parity-ledger validity as already covered by the pytest commands above.
