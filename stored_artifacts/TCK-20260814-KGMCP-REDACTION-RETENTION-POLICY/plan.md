---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY
artifact_type: plan
tags: [ai, security, process-improvement]
---

# Implementation Plan — TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY

## Summary

This is a Phase-0 policy/documentation ticket: no code path in `tools/retrieval_cache.py` is
implemented or modified. The plan produces one new contract document,
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`, built section-by-section
across six ordered steps (each step appends one self-contained section plus its own test), one new
test module (`tests/docs/test_redaction_retention_policy_doc.py`) that asserts doc-structure
completeness rather than runtime behavior, one new test class in the existing
`tests/tools/test_retrieval_cache.py` that exercises real (already-existing)
`CREATE TABLE IF NOT EXISTS` rebuild behavior against today's marker-only schema, and light
cross-reference edits to two already-existing docs (`docs/plans/knowledge-gateway-mcp-proposal.md`
§20 checklist, `docs/observability/retrieval_retention_redaction_policy.md`). Two design decisions
that investigation flagged as open (secret-detection ruleset, token-counting method) are resolved
here as Plan-level calls — documented under Design Decisions — because neither is the §24 item 1
reviewer-ratification question, which is explicitly deferred, not decided, by this plan (Step 6,
AC7).

## Design Decisions

### Decision 1 — Secret-detection: baseline regex ruleset, explicitly labeled non-production-complete

Investigation confirmed (repo-wide grep for `secret[_-]?scan`, `credential.*detect`, and any
pattern-matching module) that no secret-detection/credential-scanning module exists anywhere in
this repo. `tools/agent_codex_posttool_adapter/redaction.py` is a length-truncation/field-selection
tool for `agent-monitoring/tools.jsonl` records (`summarize_tool_input()`/`derive_status()`,
`tools/agent_codex_posttool_adapter/redaction.py:12-31`) — it does not pattern-match or strip secret
values, and citing it as "existing secret-detection rules" would misrepresent it.

**Resolution: define a new, explicitly-labeled-as-baseline regex ruleset as part of this ticket's
own policy artifact** (Step 1), rather than (a) fabricating false completeness by claiming reuse of
something that doesn't exist, or (b) leaving §17 step 4 wholly undefined. This is a Phase 0 policy
document, not a security-tooling ticket — a production-grade scanner is out of scope to build here —
but §17 step 4 requires the *scan* step to exist as a defined pipeline stage before payload caching
begins, so the ruleset must be named, not hand-waved.

The baseline ruleset covers four common credential shapes, chosen because each is a well-known,
low-false-positive-risk regex pattern (no new dependency required):
- AWS-style access key IDs (`AKIA[0-9A-Z]{16}` shape).
- Generic API-key-looking assignments (`(api[_-]?key|apikey)\s*[:=]\s*['"][A-Za-z0-9_\-]{16,}['"]`
  shape).
- PEM private-key headers (`-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----`).
- Bearer tokens (`Bearer\s+[A-Za-z0-9\-_.]{20,}`).

The policy doc must state, verbatim in intent: *this baseline ruleset is a documented starting
point, not a production-complete secret scanner; it must be reviewed and expanded by a
security-focused pass before Phase 2 payload caching goes live.* This satisfies AC1/AC2's
"explicitly enumerate" requirement honestly — the ruleset is disclosed as NEW and incomplete, not
silently assumed to already exist and be sufficient.

### Decision 2 — Token-counting: dependency-free character-based heuristic

Investigation confirmed no tokenizer library (`tiktoken` or otherwise) is a repo dependency
(grepped `requirements*.txt`/`pyproject.toml`: zero hits), and that
`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2 already establishes a
repo-wide precedent of refusing to add a single-purpose dependency for a Phase-0 concern (explicit
refusal to add a migration library). Adding a tokenizer dependency for a policy-only ticket that
does not even ship a live caching path would repeat exactly the pattern that precedent rejects.

**Resolution: define the token-counting method as a deterministic, dependency-free heuristic —
`token_count ≈ ceil(len(text.encode("utf-8")) / 4)`** (the widely-used "~4 bytes per token"
approximation) — documented by name in the policy doc as the
`kgmcp_char_heuristic_v1` method, with a **documented tolerance of ±20%** against any
downstream true count, for validating the Phase 3 pilot's "returned content respects the requested
budget within a documented tolerance" acceptance bar (§21). The policy doc must state this method
produces a plain non-negative integer (matching `budget_tokens`/`budget_requested`/
`budget_returned`'s `"type": "integer"` constraint —
`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json:17-19` and
`knowledge_context_response.schema.json:117-118`, both read and confirmed during Plan), and that it
is *documented only* at Phase 0 — no callable ships in `tools/` as part of this ticket, consistent
with the ticket's Out of Scope excluding cache read/write implementation. The doc must also state
how `budget_class` (a separate tier/bucket field,
`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md:43`, confirmed
during Plan: "The caller's budget tier (token/latency budget bucket), not the raw numeric budget")
is derived from the raw integer count without redefining either schema — e.g. by naming
provisional bucket boundaries (small/medium/large) as illustrative only, not a frozen enum, since no
schema currently defines `budget_class`'s value set.

## Steps

### Step 1 — Create the policy doc: allowlist, redaction rules, secret-scan disclosure, size cap, versioning, never-cache enumeration

**Files:**
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (new)
- `tests/docs/test_redaction_retention_policy_doc.py` (new)

**Change:**
Create the policy doc with YAML frontmatter matching the sibling contract docs' shape (`status:
active`, `layer: ai`, `authority: P1`, `audience: agent` — confirmed against
`docs/observability/retrieval_retention_redaction_policy.md:1-6`'s frontmatter shape, read during
Plan) and these sections, each a distinct heading (not folded into prose):

1. **Purpose** — states this doc extends (not supersedes)
   `docs/observability/retrieval_retention_redaction_policy.md`, consistent with that doc's own
   Decision A framing that its categories are meant to be extended by a later ticket (confirmed by
   reading that doc during Investigation).
2. **Eligible source types / allowlist** — the set of source types/paths permitted to ever reach a
   cache write, expressed as an allowlist (structurally the same MAY-list discipline
   `MAY_LIST_COLUMNS` already enforces in code, `tools/retrieval_cache.py:70-89`, confirmed read
   during Plan — hashes, IDs, counts, reason codes, scores, latency, version numbers, cache status,
   `created_at`; no payload/text/content column exists in that allowlist today).
3. **Redaction rules** — local usernames and machine-specific absolute paths must be
   stripped/replaced with a stable placeholder before any content-derived value is hashed or
   stored, so no cache row can leak a local filesystem layout or OS username.
4. **Secret-scan disclosure** — Decision 1 above, verbatim: the baseline regex ruleset (AWS key
   shape, generic API-key assignment shape, PEM private-key header, bearer token), explicitly
   labeled NEW (not reused) and explicitly labeled as a starting point requiring review/expansion
   before Phase 2 goes live.
5. **Payload size cap** — a concrete numeric byte/character cap per cached payload row (state a
   specific number, e.g. a low-KB ceiling consistent with "bounded/redacted" framing in §24 item 1
   of the proposal) and what happens on exceeding it (reject the write, do not silently truncate).
6. **Redaction-policy version** — a named version field (e.g. `redaction_policy_version: 1`),
   distinct from `retrieval_cache_schema_version` (DDL shape,
   `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md:26-58`, confirmed read
   during Plan), `RETRIEVAL_VERSION` (cache-key logic, `tools/retrieval_cache.py:45`), and
   `retrieval_event_schema_version` (event field shape, `tools/retrieval_events.py:46`) — do not
   reuse or alias any of these three existing scoped names (see Anti-Drift Notes).
7. **Never-cache enumeration** — an explicit, individually-listed (not catch-all-sentence) list:
   secrets/credentials, tokens, raw environment values, unredacted sensitive tool output, arbitrary
   configuration-file contents, unrestricted raw prompts. This is verbatim from the ticket's Scope
   section and must appear as discrete bullet items so the doc-structure test can assert each one
   individually.

Then create `tests/docs/test_redaction_retention_policy_doc.py` with
`test_redaction_retention_policy_doc_exists_and_has_required_sections`: asserts the file exists at
the path above and that each of the seven section headings/each never-cache item is present as
distinct, individually matchable text (not folded into one paragraph). This is a static
doc-structure assertion, mirroring the pattern `test_knowledge_gateway_contract_schemas.py` uses to
assert schema *shape* rather than schema *semantics* (confirmed by reading that test file's
`budget_tokens` assertion at `tests/tools/test_knowledge_gateway_contract_schemas.py:177` during
Plan).

**Do NOT touch:** `tools/retrieval_cache.py`, `tools/retrieval_events.py`,
`docs/observability/retrieval_retention_redaction_policy.md` (cross-referenced only, in Step 6 —
not edited here), any `.schema.json` file under `docs/engine/contracts/knowledge_gateway_mcp/`.

**Verify:** `test_redaction_retention_policy_doc_exists_and_has_required_sections` (AC1, AC2).

### Step 2 — Token-counting method + budget-class tolerance section

**Files:**
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (append section)
- `tests/docs/test_redaction_retention_policy_doc.py` (append test)

**Change:**
Append a **Token-Counting Method** section to the same doc: Decision 2 above, verbatim —
`kgmcp_char_heuristic_v1` (`ceil(len(text.encode("utf-8")) / 4)`), ±20% documented tolerance, the
statement that it produces a plain non-negative integer, and named citation of the exact schema
fields it must stay compatible with: `budget_tokens`
(`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json:17-19`),
`budget_requested`/`budget_returned`
(`knowledge_context_response.schema.json:117-118`) — both confirmed present with
`"type": "integer"` by direct read during Plan — and the `budget_class` tier field
(`evidence_cache_identity_contract.md:43`). State explicitly that no callable ships in `tools/` yet
(Phase 0 documents the method only; a future ticket implements it).

Add `test_token_counting_method_returns_integer_compatible_with_budget_schema` to the same test
file: since no callable exists to test behaviorally (consistent with Phase-0/policy-only scope,
per test_plan.md's own instruction not to fabricate a premature implementation), this test asserts
the doc text names the method (`kgmcp_char_heuristic_v1`) and cites all three exact schema field
names it must stay compatible with — do not assert against a runnable function.

**Do NOT touch:** any `.schema.json` file (budget fields are frozen by the sibling
CONTRACT-SCHEMAS ticket — this step only *cites* them), `evidence_cache_identity_contract.md`
(read-only reference).

**Verify:** `test_token_counting_method_returns_integer_compatible_with_budget_schema` (AC3).

### Step 3 — Freeze SQLite operational limits section

**Files:**
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (append section)
- `tests/docs/test_redaction_retention_policy_doc.py` (append two tests)

**Change:**
Append a **SQLite Operational Limits** section stating concrete values/rules for: maximum database
size (state a specific ceiling, e.g. a bounded MB figure), TTL/usage-based eviction (references
Step 4's GC defaults by name), restrictive file permissions (e.g. `0600`, owner-only), WAL mode
(`PRAGMA journal_mode=WAL`), bounded transactions, busy timeouts (a specific millisecond value,
e.g. `PRAGMA busy_timeout=...`), one-writer-safe migration discipline (references
`cache_migration_plan.md`'s existing additive `CREATE TABLE IF NOT EXISTS` migration design,
confirmed via grep during Plan at `cache_migration_plan.md:26-58` and `:122`), and a per-key
lease/transaction guard against cache stampedes (a named mechanism, e.g. an in-process or
row-level lock keyed by cache key, described as policy not implementation).

**Every other writer to `tools/retrieval_cache.py`'s connection path must be listed and the
interaction stated, because this section documents future behavior of a module this ticket does
not modify:** `_get_connection()` (`tools/retrieval_cache.py:96-105`, confirmed by direct read
during Plan: currently zero `PRAGMA`, zero `busy_timeout`, zero `os.chmod`, zero lease/stampede-guard
code) is called by every `check_*_cache`/`write_*_cache` function and by `prune()`
(`tools/retrieval_cache.py:406-428`) — i.e., today there is exactly one connection-opening code
path, not several competing writers, so there is no existing race/collision to reconcile; this
section documents *new* defaults for that single existing path, to be wired in by a future
(explicitly out-of-scope-here) implementation ticket. State this plainly in the doc text: these
defaults are not yet enforced in `tools/retrieval_cache.py`.

State explicitly (must appear in the doc, verbatim): *these are documented defaults; they are not
implemented in `tools/retrieval_cache.py` by this ticket. Implementation is deferred to a future
ticket.*

Add two tests:
- `test_sqlite_operational_limits_are_documented`: asserts each of the eight named
  values/rules above appears individually in the doc (max size, TTL/usage-based eviction, file
  permissions, WAL mode, bounded transactions, busy timeouts, one-writer-safe migration, stampede
  guard) — not a single prose paragraph referencing proposal §19.
- `test_sqlite_defaults_not_silently_implemented`: an AST or text scan of
  `tools/retrieval_cache.py`'s current source asserting it still contains no `PRAGMA journal_mode`,
  no `busy_timeout`, and no `os.chmod` call in `_get_connection()` — this is the anti-scope-creep
  guard confirming this "documentation ticket" did not silently implement connection-setup changes
  under cover of satisfying AC4. This test must fail loudly if any future step in this plan (or a
  drifting implementer) adds such code to `tools/retrieval_cache.py`.

**Do NOT touch:** `tools/retrieval_cache.py` itself — this step documents defaults only; any code
change to `_get_connection()`/`_init_schema()` is out of scope and is exactly what
`test_sqlite_defaults_not_silently_implemented` exists to prevent.

**Verify:** `test_sqlite_operational_limits_are_documented`,
`test_sqlite_defaults_not_silently_implemented` (AC4).

### Step 4 — Cache-GC defaults and safe-eviction candidates, cross-referenced against the evidence-identity contract

**Files:**
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (append section)
- `tests/docs/test_redaction_retention_policy_doc.py` (append test)

**Change:**
Append a **Cache-GC Defaults** section enumerating safe-eviction candidates verbatim from the
ticket's Scope: expired exact-query results, packets for deleted branches, obsolete
provider-version rows, low-use regenerable packets, stale rows superseded by refreshed rows,
failed/incomplete writes. Each candidate description must be phrased so it cannot be read as
authorizing eviction of a `SYMBOL`- or `FILE`-backed evidence row on a bare `PROVIDER_GENERATION`
bump alone.

**Every other writer/reader of GC-relevant state must be listed:** the only existing eviction
mechanism today is `prune(older_than_days, table)`
(`tools/retrieval_cache.py:406-428`, confirmed by direct read during Plan — operator-invoked only,
never called from any `check_*`/`write_*` function, per `TestPrune::test_prune_is_not_invoked_by_
any_check_or_write_function` in `tests/tools/test_retrieval_cache.py`, confirmed read during Plan).
This section's GC defaults are new *policy* describing future automatic GC behavior; they do not
change `prune()`'s current manual-only status, and the doc must state that plainly. Cross-reference
the sibling `evidence_cache_identity_contract.md` §4's hard rule verbatim (confirmed exact wording
by direct read during Plan, `evidence_cache_identity_contract.md:123-140`): *"a `SYMBOL`- or
`FILE`-backed evidence record ... must never be invalidated by an unrelated corpus-wide
`PROVIDER_GENERATION` bump alone."* State that this GC policy defers to and does not override that
rule.

Add `test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects`: a
lightweight text-based check asserting the doc explicitly cites §4's fallback rule (e.g. asserts the
phrase "PROVIDER_GENERATION" and "SYMBOL" or "FILE" both appear near the GC-defaults section,
alongside an explicit deferral statement) — acceptable given no live GC implementation exists yet to
test behaviorally, matching test_plan.md's specified approach.

**Do NOT touch:** `evidence_cache_identity_contract.md` (read-only reference — do not edit the
sibling ticket's already-closed artifact), `tools/retrieval_cache.py`'s `prune()` function or any
other code in that module.

**Verify:** `test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects`
(AC5).

### Step 5 — Crash-recovery test scoped to today's marker-only schema

**Files:**
- `tests/tools/test_retrieval_cache.py` (append new test class)

**Change:**
Append a new `TestCrashRecovery` class to the existing test file, following the existing
`_isolated_cache_db` fixture pattern (`tests/tools/test_retrieval_cache.py:33-37`, confirmed read
during Plan: monkeypatches `CACHE_DB_PATH`/`_MANIFEST_PATH` to `tmp_path`) and the existing
`_TABLE_NAME_BY_ALIAS.values()` iteration idiom already used by `TestPrune`
(`tests/tools/test_retrieval_cache.py`, confirmed read during Plan in
`test_prune_deletes_rows_older_than_threshold_across_all_three_tables`). Add
`test_deleted_cache_db_rebuilds_clean_marker_only_schema`:
1. Write one row each via `rc.write_index_cache(...)`, `rc.write_query_cache(...)`,
   `rc.write_packet_cache(...)` (same call shapes as `TestPrune`'s existing test, confirmed by
   direct read).
2. Delete the underlying `.db` file directly via `Path.unlink()` (the isolated `tmp_path` path,
   not the real `knowledge-index/retrieval_cache.db`).
3. Call any `check_*_cache` function with no prior manual re-init.
4. Assert no exception is raised.
5. Assert all three tables (`rc._TABLE_NAME_BY_ALIAS.values()`) exist and are empty — proving
   clean recreation via `_init_schema()`'s `CREATE TABLE IF NOT EXISTS`
   (`tools/retrieval_cache.py:108-152`, confirmed read during Plan), not silent corruption or a
   half-written schema.
6. Assert no file outside the isolated `tmp_path` cache DB directory was touched (no write to any
   `docs/`, `tickets/`, or other repo path) — proven by construction, since
   `tools/retrieval_cache.py` has no code path that writes outside `CACHE_DB_PATH` (confirmed by
   reading the full module's write surface during Investigation and Plan).

The test's docstring must state, verbatim: *this test verifies rebuild of the schema that exists
today (three marker-only tables: `retrieval_index_cache_rows`, `retrieval_query_cache_rows`,
`retrieval_packet_cache_rows`). It does not and cannot test payload-row recovery, because no payload
column exists yet (`cache_migration_plan.md` confirms Level 1/2 payload tables are unimplemented
Phase 2/3 work). A future ticket that adds payload tables must extend this test, not treat it as
already covering that case.* This is the explicit scope boundary the investigation required to avoid
over-claiming AC6.

**Do NOT touch:** any existing test in `TestMayListEnforcement` or `TestPrune` — this step only
appends a new class; zero lines in existing test classes change. Do not add any assertion about
payload rows/content (none exist yet — asserting on them would either always fail or silently test
nothing real).

**Verify:** `test_deleted_cache_db_rebuilds_clean_marker_only_schema` (AC6).

### Step 6 — Ratification-pending flag (§24 item 1) and cross-reference updates

**Files:**
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (append final
  section)
- `tests/docs/test_redaction_retention_policy_doc.py` (append test)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edit §20 checklist)
- `docs/observability/retrieval_retention_redaction_policy.md` (edit — add cross-reference only)

**Change:**
Append a **Ratification Status** section to the policy doc, stating explicitly and
unambiguously: *this policy artifact is drafted, not ratified. Phase 2 payload caching may not
begin until a reviewer explicitly ratifies or rejects §24 item 1 of
`docs/plans/knowledge-gateway-mcp-proposal.md` (caching bounded/redacted answer/context payloads
from allowlisted source types at all). This ticket produces the artifact reviewers decide on; it
does not itself decide or imply approval.* This must not be phrased in a way that could be misread
as approval-in-waiting — use direct, unambiguous language, not a passive "pending review" footer
that could be silently dropped in a later edit.

Add `test_policy_doc_explicitly_flags_ratification_pending`: asserts the doc contains an
unambiguous ratification-pending statement (e.g. asserts presence of specific phrases like
"not ratified" / "may not begin until" / "does not itself decide") — guards against future edits
quietly dropping the flag.

Update `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 0 checklist: annotate the two
unmarked bullets — "Ratify the cached-payload redaction and retention policy" and "Define a
reproducible token-counting method, budget tolerance, SQLite operating limits, and cache-GC
defaults" — with a reference to `redaction_retention_policy.md` and status
"drafted / pending ratification" (not "Done" — matches how the two already-closed sibling tickets
annotated their own §20 bullets, confirmed pattern from Investigation).

Update `docs/observability/retrieval_retention_redaction_policy.md`: add one cross-reference
sentence noting it is extended (not superseded) by
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`, consistent with that
doc's own Decision A framing (confirmed by direct read during Investigation) that its categories
are meant to be extended by a later ticket. Do not alter that doc's existing MAY/PROHIBITED list,
Decision B, or Decision C content — add only the cross-reference.

**Do NOT touch:** any other section of `docs/plans/knowledge-gateway-mcp-proposal.md` besides the
two named §20 bullets; any other section of
`docs/observability/retrieval_retention_redaction_policy.md` besides the added cross-reference
sentence; do not mark either §20 bullet "Done" — ratification itself remains an open reviewer
decision per this ticket's own Out of Scope.

**Verify:** `test_policy_doc_explicitly_flags_ratification_pending` (AC7).

## Scope Guards

- Do not implement or edit `tools/retrieval_cache.py` — no `PRAGMA`, `os.chmod`, lease/stampede-guard
  code, or GC/eviction logic may be added to that module by this ticket. Enforced mechanically by
  `test_sqlite_defaults_not_silently_implemented` (Step 3).
- Do not implement or edit `tools/retrieval_events.py`.
- Do not create or edit any `.schema.json` file under
  `docs/engine/contracts/knowledge_gateway_mcp/` — those are frozen by the already-closed sibling
  `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`. This ticket only cites exact field names/line numbers from
  them.
- Do not edit `evidence_cache_identity_contract.md` or `cache_migration_plan.md` — both are
  already-closed sibling artifacts; cross-reference and cite them, do not modify them.
- Do not touch `src/observability/reporting/retention.py`, `src/core/retention.py`, or any
  `tools/agent-monitoring/*.py` writer — out of scope per the prior sibling ticket and unchanged by
  this one.
- Do not invent a new bare `schema_version` name anywhere in the new doc — use
  `redaction_policy_version` for this ticket's own version field, and never alias it to or confuse
  it with `retrieval_cache_schema_version`, `RETRIEVAL_VERSION`, or `retrieval_event_schema_version`.
- Do not self-ratify §24 item 1 (Step 6) — the doc must read as pending reviewer decision, never as
  approved.
- Do not add any assertion or claim (in the doc or the crash-recovery test) about payload-row
  recovery — no payload column exists in the schema today.
- Do not add a `docs/parity_ledger/` entry for this ticket — consistent with both already-closed
  sibling tickets' explicit statement that this subsystem classifies as not requiring one
  (confirmed in Investigation).
- Do not add a new dependency (tokenizer library, secret-scanning package) to
  `requirements*.txt`/`pyproject.toml` — Decision 1 and Decision 2 are both dependency-free by
  design.

## Dependency Map

- Step 1 must land first — it creates `redaction_retention_policy.md` and
  `tests/docs/test_redaction_retention_policy_doc.py`, which Steps 2, 3, 4, and 6 append to.
- Steps 2, 3, 4 are content-independent of each other (each appends a distinct section/test) but
  must follow Step 1 for the file to exist. They may be implemented in any order relative to each
  other.
- Step 5 is fully independent — it touches only `tests/tools/test_retrieval_cache.py` and exercises
  existing `tools/retrieval_cache.py` behavior. It has no file dependency on Steps 1-4, 6, though
  doing it last keeps the plan's step order matching the ticket's Scope-section ordering.
- Step 6 should land last: it references Step 4's GC section (by name, for the ratification
  statement's Phase 2 framing) and is the natural place to finalize the two cross-reference doc
  edits once the policy doc's content (Steps 1-4) is complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — written policy doc covering allowlist, redaction rules, secret-scan reuse, size cap, versioning | Step 1 | `test_redaction_retention_policy_doc_exists_and_has_required_sections` |
| AC2 — explicit never-cache enumeration, no ambiguity | Step 1 | `test_redaction_retention_policy_doc_exists_and_has_required_sections` |
| AC3 — reproducible token-counting method + budget-class tolerance, referenced by name from CONTRACT-SCHEMAS budget fields | Step 2 | `test_token_counting_method_returns_integer_compatible_with_budget_schema` |
| AC4 — SQLite operational limits documented and testable | Step 3 | `test_sqlite_operational_limits_are_documented`, `test_sqlite_defaults_not_silently_implemented` |
| AC5 — cache-GC defaults distinguishing disposable rows from durable project truth | Step 4 | `test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects` |
| AC6 — crash-recovery test, currently-empty-schema database deleted/rebuilt, no loss of authoritative project truth | Step 5 | `test_deleted_cache_db_rebuilds_clean_marker_only_schema` |
| AC7 — policy artifact explicitly flagged as requiring reviewer ratification, no self-ratification | Step 6 | `test_policy_doc_explicitly_flags_ratification_pending` |

## Anti-Drift Notes

- `tools/agent_codex_posttool_adapter/redaction.py` is not a secret scanner — do not cite it as
  "existing secret-detection rules" anywhere in the new doc (Step 1's secret-scan disclosure must
  name the baseline ruleset as NEW).
- The doc must state plainly, in Step 3's SQLite section, that the documented WAL/busy-timeout/
  permissions/stampede-guard defaults are **not yet enforced** in `tools/retrieval_cache.py` —
  AC4's "documented and testable" must not be read or written as "already enforced."
- The crash-recovery test (Step 5) must not assert anything about payload rows/content — a future
  maintainer adding such an assertion without first shipping the Level 1/2 payload schema would
  produce a test that always fails or silently tests nothing real. The docstring note specified in
  Step 5 is the enforcement mechanism for this boundary.
- `redaction_policy_version` (this ticket's new version field) is a fourth, genuinely distinct
  "version" concept alongside `retrieval_cache_schema_version` (DDL shape),
  `RETRIEVAL_VERSION` (cache-key logic, `tools/retrieval_cache.py:45`), and
  `retrieval_event_schema_version` (event field shape, `tools/retrieval_events.py:46`). Do not
  merge, alias, or rename any of these into a shared bare `schema_version`.
- §24 item 1 (ratify/reject payload caching at all) is not decided by this ticket. Step 6's doc
  language must read as pending, not approved, at all times — including in any future edit to that
  section.
- The GC-defaults section (Step 4) must defer to, not override, `evidence_cache_identity_contract.md`
  §4's hard rule about `SYMBOL`/`FILE`-backed evidence records never being invalidated by a bare
  `PROVIDER_GENERATION` bump alone.
- `tests/docs/` already exists with an `__init__.py` and existing doc-structure test files
  (`test_contributor_guardrails.py`, `test_design_patterns_currency.py`, `test_doc_integrity.py`,
  confirmed via directory listing during Plan) — no pytest discovery/config risk exists for the new
  `test_redaction_retention_policy_doc.py` file; this resolves the uncertainty test_plan.md flagged
  about `testpaths` configuration.

## Deviations

- **Step 4 test wording**: the plan describes asserting a phrase resembling
  `prune()'s current manual-only status`. The implemented doc prose reads "they do not change
  `prune()`'s current manual-only status" (backtick-quoted function name, apostrophe-s). To avoid a
  test assertion that is brittle to exact backtick/apostrophe placement in prose, the implemented
  test in `tests/docs/test_redaction_retention_policy_doc.py::
  test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects` asserts the
  substring `"current manual-only status"` (without the leading `prune()'s`/backtick portion),
  which still uniquely and unambiguously matches only this sentence in the document. No change to
  the plan's required doc content or AC5 coverage — this is a test-assertion robustness deviation
  only, not a content deviation.
- No other deviations. All 6 steps, all file targets, and all Scope Guards were followed exactly as
  written.
