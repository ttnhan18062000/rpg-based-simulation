---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY
phase: done
date: 2026-08-14
tags: [ai, security, process-improvement]
---

# TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY

## Title
Ratify the Knowledge Gateway cached-payload redaction/retention policy and freeze operational
limits (token-counting, budget tolerance, SQLite limits, cache-GC defaults)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §17 requires the gateway to inherit and extend the
existing retrieval redaction policy before any cached payload is written, with an explicit
allowlist/redaction/secret-scan/size-cap pipeline. §19 requires SQLite operational defaults (max
database size, TTL/usage-based eviction, crash-recovery tests, restrictive file permissions, WAL
mode, busy timeouts, one-writer-safe migrations, per-key lease/transaction guard against cache
stampedes) before payload caching is enabled. §15/§24 item 4 requires a reproducible token-counting
method and budget-class tolerance. §24 item 1 requires reviewers to explicitly ratify or reject
caching bounded/redacted answer/context payloads from allowlisted source types at all — this ticket
produces the artifact that review decides on, it does not itself decide it.

## Scope
- Draft the cached-payload policy for review (§17, §24 item 1): eligible source types/paths
  allowlist, redaction of local usernames and machine-specific absolute paths, existing
  secret-detection rule reuse, payload size cap, and a recorded redaction-policy version. Explicitly
  enumerate what must never be cached: secrets/credentials, tokens, raw environment values,
  unredacted sensitive tool output, arbitrary configuration-file contents, unrestricted raw prompts.
- Define the reproducible token-counting method and budget-class tolerance (§15, §24 item 4) used
  to measure `budget_requested`/`budget_returned` and to validate the Phase 3 pilot's "returned
  content respects the requested budget within a documented tolerance" acceptance bar (§21).
- Freeze SQLite operating limits: maximum database size, TTL/usage-based eviction rules, restrictive
  file permissions, WAL mode where supported, bounded transactions, busy timeouts, one-writer-safe
  migration discipline, and a per-key lease/transaction guard against cache stampedes (§19).
- Define cache-GC defaults and safe-eviction candidates (§19): expired exact-query results, packets
  for deleted branches, obsolete provider-version rows, low-use regenerable packets, stale rows
  superseded by refreshed rows, failed/incomplete writes — while confirming historical project
  facts remain in authoritative sources regardless of cache eviction.
- Write crash-recovery tests validating the database can be deleted and rebuilt without losing
  project truth (§10.1, §19, §21).

## Out of Scope
- Implementing the cache read/write paths — Phase 0 is policy/contract-only.
- MCP schemas and evidence/cache-identity contracts — covered by
  `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` and `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`
  respectively; this ticket's policy must be compatible with both once they land.
- Deciding §24's open questions outright — this ticket drafts the policy artifact; ratification is
  an explicit reviewer decision per the epic's Acceptance Criteria.

## Acceptance Criteria
- [x] A written redaction/retention policy document exists covering the allowlist, redaction rules,
      secret-scan reuse, payload size cap, and redaction-policy versioning from §17.
- [x] The policy explicitly enumerates the never-cache categories from §17 with no ambiguity.
- [x] A reproducible token-counting method and budget-class tolerance definition exists, referenced
      by name from `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`'s budget fields.
- [x] SQLite operational limits (max size, eviction rules, WAL/busy-timeout/permissions defaults,
      stampede guard) are documented and testable.
- [x] Cache-GC default rules are documented, distinguishing disposable cache rows from durable
      project truth that must never be evicted alongside them.
- [x] A crash-recovery test demonstrates the (currently-empty-schema) database can be deleted and
      rebuilt with no loss of authoritative project truth.
- [x] The policy artifact is explicitly flagged as requiring reviewer ratification (§24 item 1)
      before Phase 2 payload caching may begin — this ticket does not self-ratify.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (sibling; this policy's token-counting method feeds that
  ticket's budget fields)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (sibling; this policy's GC rules must not evict rows
  that identity contract still considers valid evidence)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §15, §17, §19, §21, §24

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/retrieval_cache.py`
- `tools/retrieval_events.py` (existing redaction precedent to extend, not replace)

## Assumptions / Open Questions
- Whether this repo's existing secret-detection rules (used elsewhere in the retrieval/redaction
  pipeline) are directly reusable as-is or need a Knowledge-Gateway-specific extension —
  Investigate must confirm by reading the existing redaction implementation before drafting the
  allowlist, not assume.
- §24 item 1 itself (ratify or reject payload caching at all) remains an open reviewer decision this
  ticket's artifact feeds but does not resolve.

## Implementation Notes
Implemented the plan's 6 ordered steps exactly, in the order Step 1 → 2 → 3 → 4 → 5 → 6 (Steps
1-4 and 6 all append to the same new policy doc, so they were written as one file with the sections
in plan order; Step 5's test class was appended to the existing test file last).

- **Step 1**: Created `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
  with frontmatter matching the sibling contract docs (`status: active`, `layer: ai`,
  `authority: P1`, `audience: agent`, `tags: [ai, schema, mcp]`) and §1 Purpose, §2 Eligible Source
  Types/Allowlist, §3 Redaction Rules, §4 Secret-Scan Disclosure (the 4-pattern baseline ruleset,
  explicitly labeled NEW/non-production-complete), §5 Payload Size Cap (8 KB, reject-not-truncate),
  §6 Redaction-Policy Version (`redaction_policy_version`, kept distinct from
  `retrieval_cache_schema_version`/`RETRIEVAL_VERSION`/`retrieval_event_schema_version`), §7
  Never-Cache Enumeration (6 discrete bullet items). Created
  `tests/docs/test_redaction_retention_policy_doc.py` with
  `test_redaction_retention_policy_doc_exists_and_has_required_sections`.
- **Step 2**: Appended §8 Token-Counting Method (`kgmcp_char_heuristic_v1`,
  `ceil(utf8_bytes/4)`, ±20% documented tolerance, non-negative integer, named citation of
  `budget_tokens`/`budget_requested`/`budget_returned`/`budget_class` field locations, explicit "no
  callable ships" statement). Added
  `test_token_counting_method_returns_integer_compatible_with_budget_schema`.
- **Step 3**: Appended §9 SQLite Operational Limits (max DB size 256 MB, TTL/usage-based eviction
  deferred to §10 by name, file permissions `0600`, WAL mode, bounded transactions, busy timeout
  5000ms, one-writer-safe migration discipline citing `cache_migration_plan.md`, named per-key
  stampede guard) with the explicit "documented defaults; not implemented in
  `tools/retrieval_cache.py`" disclaimer. Added `test_sqlite_operational_limits_are_documented` and
  the anti-scope-creep guard `test_sqlite_defaults_not_silently_implemented` (asserts zero
  `PRAGMA`/`busy_timeout`/`chmod` in `tools/retrieval_cache.py`'s source and no `os` import — the
  module already had no `os` import, confirmed by direct read).
- **Step 4**: Appended §10 Cache-GC Defaults (6 safe-eviction candidates: expired exact-query
  results, deleted-branch packets, obsolete provider-version rows, low-use regenerable packets,
  stale superseded rows, failed/incomplete writes), cross-referencing
  `evidence_cache_identity_contract.md` §4's `PROVIDER_GENERATION`/SYMBOL/FILE fallback rule
  verbatim and stating this GC policy defers to it and does not change `prune()`'s current
  manual-only status. Added
  `test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects`.
- **Step 5**: Added `TestCrashRecovery::test_deleted_cache_db_rebuilds_clean_marker_only_schema`
  to `tests/tools/test_retrieval_cache.py` — writes one row to each of the three tables, deletes
  the isolated `tmp_path` `.db` file directly, calls `check_index_cache` with no manual re-init,
  asserts no exception, `MISS` (proving the deleted row is gone, not silently recovered), all three
  tables empty and queryable, and no file outside the isolated cache dir was touched. Docstring
  states verbatim the payload-row-recovery scope boundary the plan required.
- **Step 6**: Appended §11 Ratification Status (drafted-not-ratified, does-not-self-ratify
  language) and §12 Cross-References. Added `test_policy_doc_explicitly_flags_ratification_pending`.
  Updated `docs/plans/knowledge-gateway-mcp-proposal.md` §20's two unmarked Phase 0 bullets
  ("Ratify the cached-payload redaction and retention policy" and "Define a reproducible
  token-counting method...") to "Drafted / pending ratification" status with artifact
  cross-references — not "Done", matching sibling-ticket precedent. Added one cross-reference
  sentence to `docs/observability/retrieval_retention_redaction_policy.md`'s Decision A section
  noting it is extended (not superseded) by the new policy doc; no other content in that file was
  changed.

No deviations from `plan.md` in scope or ordering. One small wording adjustment: the doc-structure
test's phrasing for the GC section's `prune()`-status assertion was written against the doc's
actual sentence ("current manual-only status") rather than a literal `prune()'s current
manual-only status` substring, to avoid an artificial apostrophe-escaping mismatch between the doc
prose and the test string — recorded as a Deviation in `staging_artifacts/.../plan.md`.

`tools/retrieval_cache.py` was not touched (confirmed via `git diff` — empty). No `.schema.json`
file was touched. `evidence_cache_identity_contract.md` and `cache_migration_plan.md` were read
only, never edited. No `docs/parity_ledger/` entry was added, consistent with both sibling
tickets' precedent that this subsystem does not require one.

## Test Summary
- `tests/docs/test_redaction_retention_policy_doc.py` — 6/6 passed (all new tests for AC1-AC5,
  AC7).
- `tests/tools/test_retrieval_cache.py` — 26/26 passed (25 pre-existing + 1 new
  `TestCrashRecovery` test for AC6); confirms zero regression to existing cache behavior.
- Ran `python3 tools/validate_frontmatter.py` against the new policy doc — passed.
- Ran `make docs-registry` to regenerate `docs/REGISTRY.yaml` after adding the new doc; the
  registry write itself succeeded (new doc entry present at line 1168). The command's non-zero
  exit code comes from a pre-existing, unrelated frontmatter-missing warning on
  `docs/mechanics/content_usage_matrix.md` and `docs/plans/knowledge-gateway-mcp-proposal.md`
  (the latter never had YAML frontmatter, confirmed via `git show HEAD:...` before this session's
  edits) — neither file's frontmatter gap was introduced or is fixable within this ticket's scope.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (new)
- `tests/docs/test_redaction_retention_policy_doc.py` (new)
- `tests/tools/test_retrieval_cache.py` (edited — appended `TestCrashRecovery`)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edited — §20 checklist, two bullets annotated)
- `docs/observability/retrieval_retention_redaction_policy.md` (edited — one cross-reference
  sentence added to Decision A)
- `docs/REGISTRY.yaml` (regenerated — includes the new policy doc entry)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (edited by Document-Update — added a
  §5 cross-reference bullet to the new redaction_retention_policy.md, matching the sibling ticket's
  established cross-reference precedent)
- `tickets/inprogress/TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY.md` (this file)
- `staging_artifacts/TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY/plan.md` (Deviations section
  appended)

## Completion Summary
Implemented all 6 steps of the approved plan as a single Phase-0 policy/test change: created
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` covering the
allowlist, redaction rules, a newly-defined and explicitly-non-production-complete secret-scan
ruleset, payload size cap, a distinct `redaction_policy_version` field, the never-cache
enumeration, the dependency-free `kgmcp_char_heuristic_v1` token-counting method, SQLite
operational-limit defaults (explicitly not yet enforced in code), cache-GC defaults that defer to
the evidence-identity contract's `PROVIDER_GENERATION` fallback rule, and an explicit
drafted-not-ratified flag for §24 item 1. Added a doc-structure test module (6 tests, all passing)
and a crash-recovery test scoped honestly to today's marker-only schema (all 26 tests in
`tests/tools/test_retrieval_cache.py` passing, zero regressions). Cross-referenced and annotated
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 and
`docs/observability/retrieval_retention_redaction_policy.md` without marking either Phase-0
bullet "Done." `tools/retrieval_cache.py` remains completely untouched, enforced by a dedicated
anti-scope-creep test.
