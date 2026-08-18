---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY
artifact_type: test_plan
tags: [ai, security, process-improvement]
---

# Test Plan — TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY

## Regression Surface

This ticket is Phase 0 policy/documentation-only (no edits to `tools/retrieval_cache.py` or
`tools/retrieval_events.py`, per its own Out of Scope). The regression surface is therefore
"prove the existing subsystems this ticket documents are unmodified and unbroken," not new
production code.

**Unit / module-level**
- `tests/tools/test_retrieval_cache.py` — all classes, especially
  `TestMayListEnforcement` (`:161-209`, the existing allowlist-redaction guard this ticket's
  policy documents) and `TestPrune` (`:251-299`, the existing eviction backstop this ticket's
  GC-defaults policy documents). Must stay green untouched — this ticket adds no code to this
  module.
- `tests/tools/test_retrieval_events.py` — the event-emission allowlist
  (`RETRIEVAL_EVENT_FIELDS`) this ticket's policy references as the events-side counterpart to
  the cache-side MAY-list.

**Integration**
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — the frozen `budget_tokens`/
  `budget_requested`/`budget_returned` field-shape assertions (`:177` and neighboring lines) this
  ticket's token-counting method must remain compatible with. Must stay green; this ticket does
  not edit any `.schema.json` file.
- `tests/tools/test_evidence_cache_identity_contract.py` — asserts the provider-generation
  fallback rule this ticket's GC-eligibility rules must not violate (no GC rule may describe
  evicting a `SYMBOL`/`FILE`-backed row on a bare corpus-generation bump alone).

**Arena-combat**: not applicable — this subsystem has no combat/simulation surface
(confirmed: no `docs/mechanics/`/`docs/engine/` chapter governs it, per Investigation).

## New Tests Required

Per Acceptance Criteria (`tickets/inprogress/TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY.md`):

1. **AC1/AC2 — policy document existence and completeness (allowlist, redaction rules,
   secret-scan disclosure, size cap, versioning, never-cache list)**
   - Test name: `test_redaction_retention_policy_doc_exists_and_has_required_sections`
   - Category: unit (static doc-structure assertion, not a semantic-content check)
   - Verifies: `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
     exists and contains named sections/headings for each of: eligible-source-types allowlist,
     redaction rules, secret-scan status (existing-vs-newly-defined disclosure), payload size
     cap, redaction-policy version, and the explicit PROHIBITED/never-cache enumeration from
     §17 (secrets/credentials, tokens, raw environment values, unredacted sensitive tool output,
     arbitrary configuration-file contents, unrestricted raw prompts) — each item individually
     present, not folded into a vague catch-all sentence.
   - Location: `tests/docs/test_redaction_retention_policy_doc.py` (new file; mirrors the
     doc-structure-assertion pattern used for other Phase-0 contract docs, e.g. how
     `test_knowledge_gateway_contract_schemas.py` asserts schema file shape rather than schema
     semantics).

2. **AC3 — token-counting method compatibility with frozen budget fields**
   - Test name: `test_token_counting_method_returns_integer_compatible_with_budget_schema`
   - Category: unit
   - Verifies: whatever token-counting function/method this ticket's policy specifies (even if
     only documented, not yet implemented in `tools/`) produces a plain non-negative integer, and
     that the documented method's output type matches `budget_tokens`/`budget_requested`/
     `budget_returned`'s `"type": "integer"` schema constraint
     (`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json:17-19`,
     `knowledge_context_response.schema.json:117-118`). If the policy only documents the method
     without shipping a callable (consistent with Phase-0/policy-only scope), this test instead
     asserts the doc explicitly names the method and cites the exact schema fields it must stay
     compatible with — do not fabricate a premature implementation to make this test "richer"
     than the ticket's actual scope.
   - Location: `tests/docs/test_redaction_retention_policy_doc.py` (same file as test 1, or a
     sibling test module if the assertions grow large enough to warrant a split).

3. **AC4 — SQLite operational limits documented and testable**
   - Test name: `test_sqlite_operational_limits_are_documented`
   - Category: unit
   - Verifies: the policy doc states concrete values/rules for max database size,
     TTL/usage-based eviction, restrictive file permissions, WAL mode, bounded transactions,
     busy timeouts, one-writer-safe migration discipline, and the per-key lease/stampede guard —
     each named explicitly, not merely referenced by pointing back at proposal §19's prose.
   - Location: `tests/docs/test_redaction_retention_policy_doc.py`.
   - Companion architecture guard: `test_sqlite_defaults_not_silently_implemented` — asserts
     `git diff`-equivalent (or an AST/text scan of `tools/retrieval_cache.py`) shows no
     `PRAGMA journal_mode`, no `busy_timeout`, and no `os.chmod` call was added to
     `_get_connection()` by this ticket — enforces the Out-of-Scope boundary that this ticket
     documents defaults without implementing them (prevents silent scope creep into Phase 1/2
     implementation work under cover of a "test").

4. **AC5 — cache-GC defaults distinguish disposable rows from durable project truth**
   - Test name: `test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects`
   - Category: unit / cross-document consistency check
   - Verifies: none of the policy doc's enumerated "safe eviction candidates" (expired
     exact-query results, packets for deleted branches, obsolete provider-version rows, low-use
     regenerable packets, stale rows superseded by refreshed rows, failed/incomplete writes)
     is phrased in a way that would authorize evicting a `SYMBOL`/`FILE`-backed row on a bare
     `PROVIDER_GENERATION` bump alone — cross-checked against
     `evidence_cache_identity_contract.md` §4's hard rule. A lightweight text-based check (e.g.
     asserting the doc explicitly cites and defers to §4's fallback rule) is acceptable given no
     live GC implementation exists yet to test behaviorally.
   - Location: `tests/docs/test_redaction_retention_policy_doc.py`.

5. **AC6 — crash-recovery test demonstrating the currently-empty-schema database can be
   deleted and rebuilt with no loss of authoritative project truth**
   - Test name: `test_deleted_cache_db_rebuilds_clean_marker_only_schema`
   - Category: integration (exercises real `tools/retrieval_cache.py` code, isolated to a
     `tmp_path`, following the existing `_isolated_cache_db` fixture pattern at
     `tests/tools/test_retrieval_cache.py:33-37`)
   - Verifies: (a) write rows to all three existing tables via `write_index_cache`/
     `write_query_cache`/`write_packet_cache`; (b) delete the underlying `.db` file directly
     (`Path.unlink()`); (c) call any `check_*_cache` function again with no prior re-init; (d)
     assert no exception is raised, all three tables exist and are empty (proving clean
     recreation via `_init_schema()`'s `CREATE TABLE IF NOT EXISTS`, not silent corruption); (e)
     assert no file outside the isolated `tmp_path` cache DB was touched (no write to any
     `docs/`, `tickets/`, or other authoritative-source path) — this is the "no loss of
     authoritative project truth" half of AC6, proven by construction since this module never
     touches those paths (confirmed in Investigation).
   - Scope note (must be stated in the test's docstring, per Investigation's Risk): this test
     verifies rebuild of the schema that exists **today** (three marker-only tables). It does
     not and cannot test payload-row recovery, because no payload column exists yet
     (`cache_migration_plan.md` confirms Level 1/2 tables are unimplemented Phase 2/3 work). A
     future ticket that adds payload tables must extend this test, not treat it as already
     covering that case.
   - Location: `tests/tools/test_retrieval_cache.py` (new test class, e.g.
     `TestCrashRecovery`, appended to the existing file — this is the one new test in this
     ticket that touches real `tools/` code rather than only the new doc, since AC6 explicitly
     requires demonstrating real rebuild behavior, not just documenting it).

6. **AC7 — policy artifact explicitly flagged as requiring reviewer ratification**
   - Test name: `test_policy_doc_explicitly_flags_ratification_pending`
   - Category: unit
   - Verifies: the policy doc contains an explicit, unambiguous statement that Phase 2 payload
     caching may not begin until a reviewer ratifies §24 item 1, and that this ticket does not
     itself claim ratification. Guards against the doc's tone silently drifting into "caching is
     approved" language during future edits.
   - Location: `tests/docs/test_redaction_retention_policy_doc.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_retrieval_cache.py tests/tools/test_retrieval_events.py -v
pytest tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_evidence_cache_identity_contract.py -v
pytest tests/docs/test_redaction_retention_policy_doc.py -v
```

Never `pytest tests/`. If `tests/docs/` does not yet exist as a directory with an `__init__.py`
or discoverable conftest, confirm pytest's rootdir config picks it up the same way other
`tests/docs/*` (if any) or `tests/tools/*` doc-shape tests are already discovered before adding
the new file — check `pytest.ini`/`pyproject.toml`'s `testpaths` first.

## Anti-Drift Test Guards

- `test_sqlite_defaults_not_silently_implemented` (above, AC4) — the primary anti-scope-creep
  guard: fails if this "documentation ticket" accidentally starts implementing
  `tools/retrieval_cache.py` connection-setup changes under cover of satisfying AC4.
- `TestMayListEnforcement`/`TestPrune` (existing, `tests/tools/test_retrieval_cache.py`) staying
  green with zero diff to `tools/retrieval_cache.py` is itself an anti-drift guard: any local
  change to those tests' pass/fail status would indicate this ticket silently touched cache
  code it isn't scoped to touch.
- `test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects` (AC5) —
  guards against the GC policy silently drifting into authorizing eviction of evidence the
  sibling identity contract still protects, which would be a cross-ticket contract violation
  invisible to a reviewer reading only this ticket's diff.
- `test_policy_doc_explicitly_flags_ratification_pending` (AC7) — guards against future edits
  quietly dropping the ratification-pending flag, which would functionally self-ratify §24 item
  1 without the explicit reviewer decision this ticket's own Out of Scope reserves.
- Any test asserting the crash-recovery behavior (AC6) must not assert anything about payload
  rows/content — a future maintainer adding such an assertion without first shipping the Level
  1/2 payload schema would produce a test that always fails or, worse, silently tests nothing
  real. This boundary should be enforced by the docstring note specified in test 5 above.
