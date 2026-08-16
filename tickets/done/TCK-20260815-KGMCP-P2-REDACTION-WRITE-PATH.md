---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH
phase: done
date: 2026-08-15
tags: [ai, mcp, security]
---

# TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH

## Title
Implement the ratified redaction/retention policy as real, enforced write-path code

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (ratified 2026-08-15)
defines the allowlist, redaction rules, secret-scan baseline, size cap, never-cache enumeration,
`redaction_policy_version`, SQLite operational limits, and cache-GC defaults — all currently
documentation only, explicitly disclaimed as "no callable ships as part of this ticket" at the time
it was written. This ticket is where those rules become real, enforced code, operating against the
schema `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` builds.

## Scope
- Implement the §2 allowlist check: only Context Search and Graphify results, scoped as §2
  describes, may ever reach a cache write attempt.
- Implement the §3 redaction rules (local usernames, machine-specific absolute paths) as real
  regex/replacement logic, applied before hashing, exactly as §3 specifies (redacted-content hash
  only, never the unredacted hash).
- Implement the §4 baseline secret-scan ruleset (the 4 documented patterns: AWS-style key ID,
  generic API-key assignment, PEM private-key header, Bearer token) as real, tested matching logic
  — any match must reject the write outright (never store-redacted), per §4's explicit rule.
  Preserve the doc's own disclosure that this is a non-production-complete starting baseline
  needing a future dedicated security pass — do not present this ticket's implementation as more
  complete than the ratified policy itself claims.
- Implement the §5 payload size cap (8 KB / 8192 bytes on the redacted, UTF-8-encoded payload) —
  a write exceeding this must be rejected outright, never silently truncated.
- Implement `redaction_policy_version` (§6) as a real, stamped column value on every write.
- Implement the §7 never-cache enumeration as a real, enforced check (secrets, tokens, raw env
  values, unredacted sensitive tool output, arbitrary config-file contents, unrestricted raw
  prompts) — each item independently enforceable, not a single catch-all.
- Implement the §9 SQLite operational limits and §10 cache-GC defaults as real, tested logic.

## Out of Scope
- Wiring this write-path logic into the real gateway's request handling — that's
  `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s job. This ticket builds pure, directly-testable
  functions; the next ticket calls them from the real code path.
- Expanding or hardening the §4 secret-scan baseline beyond what's already ratified — the ratified
  policy itself defers that to "a security-focused pass before Phase 2 payload caching goes live";
  if this ticket's own Investigate phase determines that pass must happen as part of shipping this
  ticket, flag it explicitly for Plan to decide, don't silently expand scope or silently ship
  without it.
- Any change to `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  or `tools/knowledge_gateway_mcp.py`.

## Acceptance Criteria
- [x] The allowlist, redaction, secret-scan, size-cap, and never-cache checks are all real,
      independently testable functions — not documentation, not a single monolithic check.
- [x] Each of the 4 secret-scan patterns has a real, passing test proving detection AND a real test
      proving the write is rejected outright (not redacted-and-stored) on a match.
      A real test proves the redacted-content hash differs from the unredacted-content hash for the
      same input, and that only the redacted hash is ever what a write function would persist.
- [x] The 8 KB size cap rejects (not truncates) an oversized payload — real test.
- [x] `redaction_policy_version` is a real, stamped value distinct from the other 3 version axes.
- [x] This ticket's own investigation honestly re-confirms (or updates) whether the security-pass
      precondition for the secret-scan baseline blocks this ticket's own shipping, per the ratified
      policy's own disclosed limitation — not silently assumed resolved.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (parent)
- TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS (dependency; supplies the schema this write-path
  writes into)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (DONE, ratified; the policy this ticket implements
  as real code for the first time)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- New: a redaction/write-path module under `tools/` (path decided by this ticket's own Plan phase)
- `tools/retrieval_cache.py` (the schema this ticket's write-path writes into, built by the
  dependency ticket)

## Assumptions / Open Questions
- Whether the §4 secret-scan baseline's own disclosed "needs a dedicated security pass before
  Phase 2 payload caching goes live" precondition means this ticket cannot ship without that pass
  happening first, or whether it means the baseline (as-is, disclosed as non-production-complete)
  is an acceptable Phase 2 starting point with the security pass tracked as a separate, later
  ticket — Investigate must determine this, citing the ratified policy's own exact wording, before
  Plan decides.

## Implementation Notes
Implemented exactly per the approved `staging_artifacts/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/plan.md`,
Steps 1-10, in one new module `tools/knowledge_gateway_redaction.py`:

- **§2 Allowlist** — `check_allowlist()` against `ALLOWED_SOURCE_TYPES` (`context_search`,
  `graphify`).
- **§3 Redaction + hashing** — `redact_content()` (home-path/username placeholder substitution
  via `_HOME_PATH_PATTERN`, then a generic absolute-path pass `_ABS_PATH_PATTERN` that either
  rewrites to a repo-relative path or falls back to `LOCAL_PATH_PLACEHOLDER`), and a local
  `_hash_text()` (SHA-256, duplicated one-liner, never imports `retrieval_cache.py`'s private
  `_hash_text`).
- **§4 Secret-scan baseline** — `scan_for_secrets()` with the 4 documented patterns verbatim
  (AWS key ID, generic API-key assignment, PEM private-key header, Bearer token); any match is a
  hard reject, never redact-and-store.
- **§5 Size cap** — `check_size_cap()`, 8192-byte ceiling on the UTF-8-encoded *redacted* payload;
  reject only, no truncation path exists anywhere in the module.
- **§7 Never-cache enumeration** — `check_never_cache_categories()` returns a `frozenset` of
  violated categories (6 independently-testable categories; 2 of 6 —
  `secrets_or_credentials`/`tokens` — deliberately reuse `scan_for_secrets()` per plan.md DD6, the
  other 4 have independent detection logic).
- **§6 stamping + orchestrator** — `WriteDecision` (frozen dataclass) and
  `evaluate_write_candidate()`, the fixed-order pipeline (allowlist -> redact -> secret-scan ->
  size-cap -> never-cache -> stamp+hash -> ALLOW) tying Steps 2-6 together. Module-level
  `redaction_policy_version = 1` is stamped on every decision, ALLOW and REJECT alike, and stays
  in-memory-only on `WriteDecision` per plan.md DD2 — no column/migration added to
  `tools/retrieval_cache.py`.
- **§9 SQLite operational limits** — `open_connection_with_limits(db_path: Path)` (WAL mode,
  `busy_timeout=5000`, `chmod 0600` only on first creation) and
  `check_db_size_within_limit(db_path: Path)`, both with `db_path` as a required parameter, no
  default, never importing/aliasing `tools.retrieval_cache.CACHE_DB_PATH` (per DD9). Also
  `execute_bounded_transaction()` (generic, no literal SQL of its own) and an in-process
  `acquire_write_guard()`/`release_write_guard()` stampede guard keyed by cache key (per DD8).
- **§10 GC-eligibility** — `CacheRowSnapshot` (Plan-invented synthetic test shape, per DD7, not a
  claim about `LEVEL1_CACHE_COLUMNS`), 6 independent `gc_eligible_*` predicates, and
  `gc_eligibility_never_flags_protected_evidence()` enforcing the SYMBOL/FILE
  never-flag-on-bare-PROVIDER_GENERATION-bump rule from `evidence_cache_identity_contract.md` §4.
  None of these call `DELETE` or `tools/retrieval_cache.py::prune()` — verified by a static
  AST-based guard test.
- **Whole-module architecture guards** — AST-based test confirms the module never imports
  `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, or
  `tools/knowledge_gateway_mcp.py`; a substring test confirms no literal
  `INSERT INTO retrieval_provider_result_cache_rows` / `UPDATE retrieval_provider_result_cache_rows`
  exists anywhere in the module. Confirmed via `git diff --stat` that all 3 live-gateway files are
  byte-unchanged after implementation.

One documented deviation from plan.md's illustrative Step 3 regex (trailing-path-preservation
detail only, not a behavior/AC change) — see the "Deviations" section appended to
`staging_artifacts/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/plan.md`.

`redaction_policy_version` stays in-memory-only on `WriteDecision` per plan.md DD2 — independently
re-confirmed by Architecture-Verify. No `tools/retrieval_cache.py` edits were made in this ticket
at all.

**Architecture-Verify regression found and fixed:** Document-Update's §9 tense-correction rewrote
the sentence `"not implemented in \`tools/retrieval_cache.py\` by this ticket"` into
`"... by \`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY\`"`, breaking the pre-existing
`test_sqlite_operational_limits_are_documented`'s literal substring assertion (1 failed, 150 passed
on Architecture-Verify's independent re-run, not the 151/0 originally reported). Fixed by rewording
the doc's clause to `"not implemented in \`tools/retrieval_cache.py\` by this document's own
architectural boundary"` — genuinely accurate (retrieval_cache.py is not and will not become the
home for these limits, confirmed by DD9) and restores the exact substring the test checks, rather
than editing the test to accept the broken wording. Re-ran the full scoped command after the fix:
151 passed, 0 failed, confirmed clean.

**Security-Review fix (non-blocking finding, fixed anyway):** Security-Review APPROVED but flagged
that `evaluate_write_candidate()`'s secret-scan step ran `scan_for_secrets(redacted)` (post-redaction
text) rather than `scan_for_secrets(raw_content)` — a redaction placeholder can swallow an adjacent
secret with no separator (e.g. `/home/alice/AKIA...` -> `<local-user>AKIA...`), which could produce
a false negative at that specific check, even though `check_never_cache_categories()` independently
re-scans `raw_content` and still catches it today (so no live ALLOW-on-secret path existed). Fixed
by scanning `raw_content` instead, with an inline comment explaining why, since this keeps the
guarantee independent of the redundant second check rather than relying on it. Re-ran
`tests/tools/test_knowledge_gateway_redaction.py` (49/49) and the full 9-file scoped suite
(240/240) after the change — both clean.

## Test Summary
New test file `tests/tools/test_knowledge_gateway_redaction.py` — 49 tests, all passing, covering
every function/dataclass listed above (allowlist x3, redaction+hashing x5, secret-scan x10,
size-cap x4, never-cache x7, redaction_policy_version x2, §9 SQLite-limits x7, §10 GC-eligibility
x8, whole-module architecture guards x2, module-docstring-disclosure x1 — counts independently
re-verified by class during Parity, correcting an initial "secret-scan x9" arithmetic slip).

Scoped regression run (per test_plan.md's first Scoped Pytest Command):
```
pytest tests/tools/test_retrieval_cache.py tests/docs/test_redaction_retention_policy_doc.py \
  tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_retrieval_events.py \
  tests/tools/test_knowledge_gateway_redaction.py -v
```
Result: **151 passed**, 0 failed.

Scope-guard run (per test_plan.md's second Scoped Pytest Command, confirming zero drift into the
3 live-gateway files):
```
pytest tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_knowledge_gateway_mcp.py \
  tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_packet_assembly.py -v
```
Result: **89 passed**, 0 failed (5 pre-existing, unrelated `jsonschema.RefResolver` deprecation
warnings).

`git diff --stat -- tools/knowledge_gateway_router.py tools/knowledge_gateway_packet_assembly.py tools/knowledge_gateway_mcp.py`
confirmed empty (byte-unchanged). `tools/retrieval_cache.py` was not opened for editing by this
ticket at all (its working-tree diff present in this repo predates this ticket's session, from
the already-closed sibling `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS`).

## Files Changed
- `tools/knowledge_gateway_redaction.py` (new)
- `tests/tools/test_knowledge_gateway_redaction.py` (new)
- `staging_artifacts/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/plan.md` (Deviations section
  appended)
- `tickets/inprogress/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH.md` (this file — Implementation
  Notes / Test Summary / Files Changed / Status)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (Document-Update: §20 Phase 2 "Store actual
  bounded normalized results" bullet annotated **Done**, citing the new module's functions and
  test count)
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (Document-Update: §6
  and §9 tense-corrected from future/deferred to past-tense, citing the new module's real callables,
  mirroring §8's precedent; §4's non-production-complete secret-scan disclosure left untouched)
- `docs/parity_ledger/infrastructure.yaml` (Parity: new entry `INFRA-342`, status `verified`,
  priority `P1`, proof_type `regression`, citing `tools/knowledge_gateway_redaction.py`'s real
  function/line locations and `tests/tools/test_knowledge_gateway_redaction.py`'s 49 passing tests;
  citations corrected again post-Security-Review to reflect the +6-line shift from the
  raw_content-scan fix, see below)
- `tools/knowledge_gateway_redaction.py` (Security-Review: `evaluate_write_candidate()`'s
  secret-scan step changed from `scan_for_secrets(redacted)` to `scan_for_secrets(raw_content)`,
  with an explanatory inline comment — see Implementation Notes)

## Completion Summary
Document-Update has run: `docs/plans/knowledge-gateway-mcp-proposal.md` and
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` were both updated (see
Files Changed above) to reflect that this ticket's redaction/allowlist/secret-scan/size-cap/
SQLite-limits/GC-eligibility functions are now real, tested code in
`tools/knowledge_gateway_redaction.py`. Parity has run: `docs/parity_ledger/infrastructure.yaml`
gained entry `INFRA-342` via the schema-validating writer (`tools/parity_ledger_writer.py::write_entry()`),
with `support_boundary` explicitly stating the zero-wiring/zero-cache-write/in-memory-only-version-stamp
boundaries and the Sec.4 secret-scan baseline's unchanged non-production-complete status. The
sibling ticket's `INFRA-341` entry was independently re-verified against the current
`tools/retrieval_cache.py` and needs no correction — this ticket confirmed that file byte-unchanged
by its own diff (its pre-existing working-tree diff predates this session, from the already-closed
`TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS`). `tools/parity_index.py build` was re-run
separately after the write to keep the derived index fresh. Security-Review has since run
(APPROVED, non-blocking finding fixed anyway — see Implementation Notes), and `INFRA-342`'s
`v2_evidence` line citations were corrected in place for the resulting +6-line shift; `tools/parity_index.py
build` was re-run again after that correction. Verify (`done-checker`) independently re-ran the
full 9-file scoped suite (240 passed, 0 failed), byte-confirmed every `INFRA-342` line citation
against the live file, confirmed the 3 Phase 1 gateway files remain byte-unchanged, confirmed
`tools/retrieval_cache.py` was never touched by this ticket, confirmed the `security` tag genuinely
triggered a completed (not skipped) Security-Review event, and confirmed all 13 DoD conditions
PASS — verdict READY_TO_CLOSE. This ticket is now finalized and moved to `tickets/done/`.
