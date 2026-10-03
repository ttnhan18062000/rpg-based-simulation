---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT

> **Architecture-Review-mandated additions (this revision).** Tests 11 and 12 below are new in
> this revision, added per Architecture Review's `NEEDS_CHANGES` ruling on plan.md (see plan.md's
> own top-of-file note) — not implementer-discovered gaps. Test 11 proves the new Step 4 fail-loud
> cardinality assertion actually raises on desync (Finding 1). Test 12 proves `render_candidates()`
> and `_dedup_key()`'s fallback both delegate to the one shared `_content_hash()` helper rather than
> each inlining its own copy of the formula (Finding 2). Total new-test count is 13, up from 11.

## Regression Surface

All must keep passing unmodified in behavior/assertions (only new tests are added; no existing
assertion should need to change if Gap 1's hash-based dedup key and Gap 3's new marker field are
implemented additively, per investigation.md's compatibility analysis):

**Unit — `tools/knowledge_gateway_packet_assembly.py`**
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (all 24 tests) — in particular:
  - `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids` — must still
    pass under a hash-based dedup key (shared text -> same hash -> same collapse).
  - `test_deduplication_occurs_before_truncation_not_after` — must still pass; dedup-before-
    truncation ordering is untouched by both Gap 1 and Gap 2 changes.
  - `test_conflict_only_surfaces_real_supersession_metadata` /
    `test_conflicts_never_populated_from_bare_topical_similarity` — must still pass; these exercise
    `build_conflicts()` directly and are not expected to change.
  - `test_budget_returned_never_exceeds_budget_requested`,
    `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`,
    `test_priority_order_invariants_before_facts_before_tests_before_history`,
    `test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content`,
    `test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output` — must
    still pass; `assemble_within_budget()`'s own truncation mechanics are not being rewritten, only
    consumed by new marker-computation logic in `assemble_packet()`.
  - `test_evidence_id_uses_closed_evidence_identity_kind_form`,
    `test_evidence_id_disambiguates_duplicate_anchor_within_same_document`,
    `test_evidence_id_for_ticket_source_path_uses_ticket_kind`,
    `test_evidence_id_for_non_doc_non_ticket_path_uses_file_kind` — evidence_id derivation itself is
    untouched (only the dedup *key* changes, not `_evidence_id_for_*()`).
  - The three "Out-of-scope architecture guards" (`test_module_not_referenced_by_any_claude_
    workflows_file`, `test_module_introduces_zero_mcp_server_code`,
    `test_module_does_not_modify_or_import_retrieval_cache`,
    `test_module_does_not_edit_knowledge_gateway_router`) — must all still pass; this ticket does
    not touch the router, retrieval_cache, or MCP server registration.

**Unit/Integration — `tools/knowledge_gateway_mcp.py`**
- `tests/tools/test_knowledge_gateway_mcp.py` (all tests) — response-schema validation, budget
  pass-through, cache-hit-skips-assemble_packet() behavior must all remain intact. Any new response
  field must not cause an existing fixture's schema validation to fail (additive field, response
  schema's top-level `additionalProperties` is open per investigation.md).

**Adjacent-subsystem guard (per Anti-Drift Hazard — routing must stay byte-unchanged)**
- `tests/tools/test_knowledge_gateway_router.py` — run directly (this ticket's own regression proof,
  mirroring the existing `test_module_does_not_edit_knowledge_gateway_router`'s own convention of
  using the router's full test suite as an edit-detection proxy).

## New Tests Required

Per acceptance criteria, one entry per required new test:

1. **`test_dedup_identity_uses_content_hash_not_casefold_normalization`**
   - Category: unit
   - Verifies: two statements whose rendered text differs only by case/whitespace (e.g.
     `"Damage Equals ATK Minus DEF."` vs `"damage equals atk minus def."`) are **not** collapsed by
     `deduplicate_statements()` once the dedup key is content-hash-based (this directly proves Gap 1
     landed — a regression to the old casefold key would make this test fail by over-merging).
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

2. **`test_dedup_collapses_only_on_exact_content_hash_match_across_providers`**
   - Category: unit (extends the existing cross-provider dedup test with a hash-identity assertion,
     not a replacement)
   - Verifies: two providers returning byte-identical evidence text collapse to one statement with
     merged `evidence_ids` (already covered structurally by the existing
     `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids` — this new
     test additionally asserts the dedup key equals a real `hashlib.sha256(...)` computation of the
     statement text, proving the mechanism is hash-based, not incidentally-matching casefold logic).
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

3. **`test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text`**
   - Category: unit — the highest-value new test in this ticket (closes Gap 2)
   - Verifies: two `context_search` results carrying identical `excerpt` text but flagged as
     mutually conflicting via `superseded_by`/`incompatible_with` (the same real signal keys
     `_structural_supersession_signal()` already checks) produce **two distinct** `Statement`s in the
     final packet (not one merged statement), **and** `packet.conflicts` is non-empty for that
     subject, **and** `packet.status == "CONFLICTED"`. This is the real regression-prone edge case
     identified in investigation.md Gap 2 — a naive text/hash-only dedup key would incorrectly merge
     this pair.
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

4. **`test_conflicting_claims_with_different_text_still_never_merge_and_pass_through_dedup`**
   - Category: unit (companion to #3 — the "normal" conflict case, ordinary different-text claims,
     asserting the pre-existing behavior is not accidentally broken by the new conflict-awareness
     guard added to close Gap 2)
   - Verifies: `test_conflict_only_surfaces_real_supersession_metadata`'s existing scenario (old/new,
     different excerpt text) still produces 2 statements (not accidentally over-merged or
     under-merged by the new guard logic).
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

5. **`test_budget_truncation_produces_visible_marker_when_content_is_dropped`**
   - Category: unit — closes AC2/AC3
   - Verifies: given >=2 real statements after dedup and a `budget_requested` sized to admit only
     one of them, the resulting `PacketAssembly` (and the response dict built by
     `_run_knowledge_context()`) carries a `True`/nonzero visible marker (exact field name per
     Plan's decision, e.g. `budget_truncated: True`, `omitted_items_count: 1`) — asserted via a real
     field read, not by inference from `budget_returned < budget_requested` alone (per AC2/AC3's own
     "verified by a real test using actual measurement, not an estimate" / "never silent... verified
     by a real test").
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

6. **`test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`**
   - Category: unit — the "never silent" negative case (a caller must be able to positively confirm
     *nothing* was dropped, not just infer it from an absent field)
   - Verifies: given a `budget_requested` large enough to admit every deduped statement, the marker
     field is present and explicitly `False`/`0` (not omitted from the packet/response dict), per
     investigation.md's Risk 5 note about `_omit_none()` never being allowed to strip this field.
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

7. **`test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too`**
   - Category: unit — edge case coverage for the existing §16 budget-assembly-failure path
     (`budget_assembly_failed`, `statements` non-empty but `included_statements` empty)
   - Verifies: the marker/count correctly reflects "all N deduped statements were omitted" in this
     pre-existing total-failure branch, not just the ordinary partial-truncation branch.
   - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

8. **`test_knowledge_context_response_schema_accepts_new_budget_marker_field`**
   - Category: integration (schema contract)
   - Verifies: a real `_run_knowledge_context()` call whose packet was budget-truncated produces a
     response dict that validates against the live
     `knowledge_context_response.schema.json` (post-doc-update) via the existing
     `jsonschema.Draft7Validator`-based `_validate_response()` helper already used in
     `tests/tools/test_knowledge_gateway_mcp.py`.
   - Where: `tests/tools/test_knowledge_gateway_mcp.py`

9. **`test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker`**
   - Category: integration
   - Verifies: the marker field set inside `PacketAssembly` by `assemble_packet()` survives the
     field-by-field response-dict construction in `_run_knowledge_context()` (lines 241-251) and is
     not accidentally dropped/renamed on the way out — closes the gap between "unit-level packet
     assembly is correct" and "the real MCP tool response is correct," mirroring this test file's
     own existing pattern of validating both layers separately.
   - Where: `tests/tools/test_knowledge_gateway_mcp.py`

10. **`test_dedup_key_is_stricter_than_semantic_similarity_no_fuzzy_merge`**
    - Category: architecture guard (anti-scope-creep)
    - Verifies: two statements with similar-but-not-identical text (e.g. differing by one word,
      "Damage equals ATK minus DEF." vs "Damage equals ATK minus DEF plus bonus.") are **not**
      merged — guards against a future accidental fuzzy/semantic-similarity dedup implementation
      creeping into Phase 3 scope (explicitly reserved for Phase 5 per this ticket's own Out of
      Scope).
    - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

11. **`test_conflict_index_pairs_correspondence_invariant_raises_on_desync`** (Architecture-Review
    Finding 1 — new this revision)
    - Category: architecture guard / fail-loud invariant
    - Verifies: the plan's Step 4 runtime assertion in `assemble_packet()` (checking
      `len(statements) == len(context_search results) + (1 if graphify else 0)`) actually fires.
      Deliberately breaks the `statements[i]` <-> raw-provider-result-index correspondence via a
      targeted monkeypatch (e.g. monkeypatching `render_candidates()` to return one extra
      `Statement` not backed by any corresponding provider result, so the cardinality check fails),
      then asserts a real `AssertionError` (or whichever exception type the implementer's exact
      assertion raises) is raised by `assemble_packet()` — proving the desync fails loudly, not
      silently. Must NOT assert on dedup behavior being merely "wrong" in this scenario — the point
      is that the pipeline refuses to proceed past a broken precondition at all.
    - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

12. **`test_evidence_hash_and_dedup_key_share_single_content_hash_helper`** (Architecture-Review
    Finding 2 — new this revision)
    - Category: architecture guard (single-source-of-truth)
    - Verifies: `render_candidates()`'s `evidence_hash` computation and `_dedup_key()`'s hash
      fallback both delegate to the one shared `_content_hash()` helper, rather than each inlining
      its own copy of `hashlib.sha256(...).hexdigest()`. Recommended mechanism: monkeypatch
      `_content_hash` (or the module's reference to it) to a distinguishable stub return value and
      assert that both (a) a `ContextEntry`/`EvidenceEntry`/`Statement.evidence_hash` produced by a
      real `render_candidates()` call and (b) `_dedup_key()`'s fallback output for a directly
      constructed `Statement` with `evidence_hash=None`, reflect the stubbed value — proving both
      code paths call through the same function object rather than each having independently
      inlined the formula.
    - Where: `tests/tools/test_knowledge_gateway_packet_assembly.py`

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v
python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v
python3 -m pytest tests/tools/test_knowledge_gateway_router.py -q
python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -q
```

Never `pytest tests/` — scoped to the Knowledge Gateway MCP tool subsystem (`tools/knowledge_
gateway_*.py` and its 3 direct test files) plus the doc-consistency guard test that already asserts
`tools/retrieval_cache.py` contains no undeclared SQLite defaults (unaffected by this ticket, run
only as a cheap confirm-untouched signal since this ticket must not touch that module at all).

## Anti-Drift Test Guards

- **`test_no_semantic_or_embedding_dependency_introduced`** (new, architecture guard): parse
  `tools/knowledge_gateway_packet_assembly.py`'s imports (mirroring the existing
  `test_statement_classification_is_ephemeral_not_persisted`'s AST-walk pattern already in the test
  file) and assert no new embedding/similarity/tokenizer library import (`sentence_transformers`,
  `sklearn`, `tiktoken`, `difflib.SequenceMatcher` used for merge decisions, etc.) was added —
  catches silent Phase-5-scope creep into this Phase-3 ticket.
- **`test_kgmcp_char_heuristic_v1_still_matches_frozen_formula`** (existing,
  `test_kgmcp_char_heuristic_v1_matches_frozen_formula` — re-run, not new): must keep passing
  unmodified; the ticket's own Scope explicitly forbids reimplementing the token-counting formula.
- **`test_module_does_not_edit_knowledge_gateway_router`** (existing): must keep passing unmodified
  — direct proof `tools/knowledge_gateway_router.py` stays byte-unchanged, per this ticket's own
  Acceptance Criterion.
- **`test_module_does_not_modify_or_import_retrieval_cache`** (existing): must keep passing
  unmodified — direct proof this ticket does not reach into Level 1/Level 2 cache code, consistent
  with investigation.md's confirmed finding that no cache interaction exists for this ticket's scope.
- **Conflict-non-merge test (#3 above) doubles as an anti-drift guard in its own right**: any future
  change that makes dedup "smarter" by comparing raw provider-result metadata loosely (rather than
  the specific, narrow conflict-signal check) would need to keep this test passing, which bounds how
  aggressive any future dedup enhancement can be without also updating conflict-awareness logic in
  lockstep.
- **`test_conflict_index_pairs_correspondence_invariant_raises_on_desync`** (#11 above,
  Architecture-Review Finding 1): guards against the specific silent-desync failure mode AC4 exists
  to prevent — a future edit to `render_candidates()`'s or `_conflict_signal_index_pairs()`'s
  iteration order that breaks their index correspondence must fail this test loudly (via the raised
  assertion no longer firing as expected, or firing where it previously didn't), not slip through as
  a silently-wrong dedup result.
- **`test_evidence_hash_and_dedup_key_share_single_content_hash_helper`** (#12 above,
  Architecture-Review Finding 2): guards against a future edit to either `render_candidates()`'s
  hash computation or `_dedup_key()`'s fallback reintroducing a second, independently-inlined copy
  of the hash formula instead of updating the shared `_content_hash()` helper both must keep calling.
- **Parity-ledger schema validity**: the new `INFRA-347` entry must validate against
  `docs/parity_ledger/schema.json` — run the repo's existing parity-ledger validation tooling (e.g.
  `tools/parity_index.py` import path, per `PARITY_ENTRY` kind's own `preferred_fingerprint`
  citation in investigation.md) as part of the Parity phase, not this ticket's pytest scope, but
  flagged here so Test-phase does not treat parity-ledger validity as already covered by the pytest
  commands above.
