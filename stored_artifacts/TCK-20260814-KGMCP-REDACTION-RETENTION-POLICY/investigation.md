---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY
artifact_type: investigation
tags: [ai, security, process-improvement]
---

# Investigation — TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY

## Current Behavior

### `tools/retrieval_cache.py` — the existing SQLite retrieval cache
- `_get_connection()` (`tools/retrieval_cache.py:96-105`): opens `CACHE_DB_PATH`
  (`knowledge-index/retrieval_cache.db`), creates the parent dir if missing, calls
  `sqlite3.connect(str(CACHE_DB_PATH))`. **No `PRAGMA journal_mode=WAL`, no
  `PRAGMA busy_timeout`, no file-permission restriction (`os.chmod`), and no
  per-key lease/transaction-guard mechanism exist anywhere in this function or module.**
  These are genuinely undefined today, not merely undocumented.
- `_init_schema()` (`tools/retrieval_cache.py:108-152`): three `CREATE TABLE IF NOT EXISTS`
  statements for `retrieval_index_cache_rows`, `retrieval_query_cache_rows`,
  `retrieval_packet_cache_rows` — all marker-only (hashes, IDs, counts, scores, latency,
  version numbers, `cache_status`, `reason_code`, `created_at`). **No payload/content column
  exists in any of the three tables.** No `retrieval_cache_generation`/schema-version metadata
  table exists yet either (that is design-only, per `cache_migration_plan.md` §1 — not
  implemented).
- `MAY_LIST_COLUMNS` (`tools/retrieval_cache.py:70-89`) + `_validate_may_list_kwargs()`
  (`tools/retrieval_cache.py:155-168`): a hard **allowlist** enforcement point. Any
  `write_*_cache()` kwarg not in `MAY_LIST_COLUMNS` raises `ValueError`. This is the repo's
  actual existing redaction precedent for this subsystem — an allowlist that structurally
  excludes payload/prompt/chunk text, not a pattern-based secret scanner. Verified by
  `tests/tools/test_retrieval_cache.py::TestMayListEnforcement` (`:161-209`), including
  `test_no_stored_row_contains_raw_prompt_or_chunk_text` and
  `test_write_path_rejects_a_prohibited_field_if_offered`.
- `prune(older_than_days, table)` (`tools/retrieval_cache.py:406-428`): the only existing
  eviction mechanism — operator-invoked only, deletes rows by `created_at` age, never called
  from any `check_*_cache`/`write_*_cache` function (asserted by
  `TestPrune::test_prune_is_not_invoked_by_any_check_or_write_function`). No TTL/max-size
  enforcement, no automatic GC, no distinction yet between "safe to evict" and "still valid
  evidence" categories beyond what `prune()`'s blunt age cutoff provides.
- No `migrate`/`rebuild` CLI subcommand exists (`_COMMAND_DISPATCH`,
  `tools/retrieval_cache.py:515-521` has only `stats`/`check-index`/`check-query`/
  `check-packet`/`prune`).

### `tools/retrieval_events.py` — NOT a redaction module
Despite the ticket's framing as "the existing redaction precedent," this module does no
redaction of its own. It is a monitoring/telemetry event emitter: `RETRIEVAL_EVENT_FIELDS`
(`tools/retrieval_events.py:52-73`) is a closed field allowlist for `agent-monitoring/events.jsonl`
rows (hashes, counts, reason codes, scores, latency — same MAY-list vocabulary as
`retrieval_cache.py`, per `docs/observability/retrieval_retention_redaction_policy.md`), and
`emit_retrieval_event()` (`:91-143`) rejects any field outside that set. It never scans content
for secrets and contains no redaction logic of its own; it inherits the same allowlist-only
discipline `retrieval_cache.py` uses.

### No reusable secret-detection tool exists anywhere in this repo
Grepped `tools/` and `src/` for `secret[_-]?scan`, `credential.*detect`, and any
pattern-matching module: zero hits. The only files matching `redact` are:
- `tools/retrieval_cache.py` (docstring cross-reference, not an implementation)
- `tools/agent_codex_posttool_adapter/redaction.py` — a **different, unrelated subsystem**:
  `summarize_tool_input()`/`derive_status()` (`tools/agent_codex_posttool_adapter/redaction.py:12-31`)
  truncate/summarize tool-call inputs (e.g. first 80 chars of a Bash command, a file path) for
  `agent-monitoring/tools.jsonl` records. This does **not** pattern-match or strip secret values
  — it truncates length and picks which field to keep. Conflating this with a secret scanner
  would misrepresent what it does.
- `tools/agent_codex_pilot_executor/simulation.py` (one comment mentioning "redacted-differently"
  as a hypothetical, not an implementation)

**Conclusion: §17 step 4 ("scan content using existing secret-detection rules") has no existing
rule set to reuse.** This must be resolved as an open design decision (define a new lightweight
ruleset as part of this ticket's own policy artifact, or explicitly flag the gap as blocking
Phase 2 payload caching until a scanner exists) — not silently assumed away. See Risks below.

### `docs/observability/retrieval_retention_redaction_policy.md` — the real prior policy doc
This is the actual redaction/retention policy this ticket must extend (§Decision A explicitly
frames its own categories as extensible in a future ticket). Key content:
- **MAY-Contain vs PROHIBITED field list** (lines 31-49): hashes, IDs, counts, reason codes,
  scores, latency, generation/version numbers, cache status are MAY; raw prompt text, raw
  retrieved chunk/source text, full unredacted tool payloads, and any field reproducing source
  content are PROHIBITED. This is the vocabulary `MAY_LIST_COLUMNS` implements in code.
- **Decision B**: retrieval *events* (`agent-monitoring/*.jsonl`) are retain-forever/redaction-only
  (no deletion, ever — matches the files' documented append-only-forever convention). Retrieval
  *caches* (SQLite) are duration-based and evictable.
- **Decision C**: per-cache-level placeholder retention durations —
  `retrieval_index_cache` ~30d, `retrieval_query_cache` ~7d, `retrieval_packet_cache` ~14d or
  ticket-lifetime — explicitly uncalibrated placeholders "by analogy," not measured values, and
  explicitly *not yet* implemented as real eviction logic (`prune()` is a manual backstop, not a
  scheduled job).
- This doc's own **Out of Scope** excludes any Phase 3+ cache implementation or GC-number
  freezing — i.e., it deliberately left today's ticket's exact job (freezing real SQLite
  operational numbers and GC defaults) for later.

### Frozen budget fields this ticket's token-counting method must be compatible with
- Request: `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json`
  — `budget_tokens: { "type": "integer" }` (line 17-19), `additionalProperties: false`.
- Response: `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json:117-118`
  — `budget_requested: { "type": "integer" }`, `budget_returned: { "type": "integer" }`.
- `evidence_cache_identity_contract.md:43` separately defines `budget_class` (a caller
  budget *tier*, not the raw numeric budget) as a lookup-identity field — distinct from the
  three integer fields above; this ticket's token-counting method must produce both the raw
  integer count (for `budget_requested`/`budget_returned`) and support a tier/bucket derivation
  for `budget_class` without redefining either schema.
- **No tokenizer library is a repo dependency.** Grepped `requirements*.txt`/`pyproject.toml`
  for `tiktoken`/`token`: zero hits. The token-counting method this ticket defines must either
  propose a new lightweight dependency (against the repo's demonstrated single-purpose-dependency
  aversion — see `cache_migration_plan.md` §2's explicit refusal to add a migration library) or
  define a deterministic, dependency-free approximation (e.g. word/char-count-based heuristic)
  native to this repo. This is an open design decision, not something already answered elsewhere.

### Crash-recovery precedent (`tests/tools/test_retrieval_cache.py`, `tests/tools/test_parity_index.py`)
`test_retrieval_cache.py` has no existing crash-recovery/rebuild test today — its
`_isolated_cache_db` fixture (`:33-37`) monkeypatches `CACHE_DB_PATH`/`_MANIFEST_PATH` to a
`tmp_path`, but no test deletes the `.db` file mid-suite and asserts recreation. The nearest
precedent is implicit: because `_get_connection()` unconditionally calls `_init_schema()`
(`:96-105`) with `CREATE TABLE IF NOT EXISTS` on every connect, deleting the file and calling
any `check_*`/`write_*` function already re-creates an empty, valid schema — this is existing,
untested-but-present behavior, not something to build new.
`tools/parity_index.py`'s `build()`/`_atomic_replace_db()` (cited in `cache_migration_plan.md`
§3) is a *different* pattern — full rebuild from an external shard source-of-truth
(`docs/parity_ledger/*.yaml`) — not applicable here, since `retrieval_cache.db` has no such
external shard source (per `cache_migration_plan.md` §3's own explicit statement).

**What AC6's crash-recovery test can honestly verify today**: delete
`knowledge-index/retrieval_cache.db` (or an isolated `tmp_path` equivalent), call any
`check_*_cache`/`write_*_cache` function, and assert (a) no exception, (b) all three
marker-only tables exist and are queryable, (c) the deleted rows are gone (proving nothing
silently persisted outside the file), (d) no `src/` state or authoritative doc was touched by
the deletion. It **cannot** honestly test payload-row recovery, because no payload column
exists in the schema yet (`cache_migration_plan.md` confirms Level 1/2 payload tables are
still Phase 2/3, unimplemented). The AC6 test must be scoped to the schema that exists today,
not a hypothetical future one — see Risks.

## Mechanics / Engine Constraints

This is agent-orchestration/retrieval tooling, not simulation behavior. No `docs/mechanics/`
chapter or `docs/engine/` contract governs its semantics — the same classification the sibling
INFRA-295/INFRA-297 parity ledger entries and the sibling `evidence_cache_identity_contract.md`/
`knowledge_gateway_mcp_contract.md` documents already record for this subsystem. The
`CLAUDE.md` "Durable State Rule" still applies conceptually (cache rows must never become an
undocumented durable-meaning store), and this ticket's own policy artifact is the mechanism
that keeps that rule honored for the Knowledge Gateway's future cache rows.

## Docs Requiring Update

- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 0 checklist has two unmarked
  bullets this ticket's artifact resolves — "Ratify the cached-payload redaction and retention
  policy" and "Define a reproducible token-counting method, budget tolerance, SQLite operating
  limits, and cache-GC defaults." Both must be annotated with the artifact reference and status
  (drafted/pending-ratification, not "Done" — ratification itself stays an open reviewer
  decision per this ticket's own Out of Scope), mirroring how the two already-closed sibling
  tickets annotated their own §20 bullets.
- `docs/observability/retrieval_retention_redaction_policy.md`: this is the doc §17 instructs
  the gateway to "inherit... and extend." Add a cross-reference noting it is extended (not
  superseded) by the new Knowledge-Gateway-specific cached-payload policy artifact this ticket
  produces, consistent with Decision A's own framing that its categories are meant to be
  extended by a later ticket.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (new file, path
  chosen to match the sibling contract documents' naming/location convention in the same
  directory): the actual policy artifact this ticket's Scope and every Acceptance Criterion
  requires — allowlist/redaction rules, explicit never-cache enumeration, the secret-detection
  gap disclosure and its resolution, payload size cap, redaction-policy version, the
  token-counting method and budget-class tolerance, SQLite operational limits (max DB size,
  TTL/usage-based eviction, WAL/busy-timeout/permissions defaults, stampede guard), cache-GC
  default rules distinguishing disposable rows from durable project truth, and the explicit
  reviewer-ratification flag required by AC7.

## Parity Ledger Overlap

- `INFRA-295` (`docs/parity_ledger/infrastructure.yaml`): the 3-level `retrieval_cache.py`
  entry. Status `verified`, priority `P2`, `test_path: tests/tools/test_retrieval_cache.py`.
  Its `support_boundary` explicitly states "no simulation behavior, Mechanics Bible chapter, or
  engine contract governs this module's semantics." This ticket does not modify
  `retrieval_cache.py` (Phase 0 policy-only, per its own Out of Scope), so INFRA-295 needs no
  status change — flagged here only because this ticket's GC/eviction rules describe future
  behavior of the module INFRA-295 already covers.
- `INFRA-297` (`docs/parity_ledger/infrastructure.yaml`): the `retrieval_events.py` entry.
  Status `verified`, priority `P2`. Same non-modification relationship as INFRA-295.
- No `P0` entries are touched.
- Following the explicit precedent set by both already-closed sibling tickets'
  `evidence_cache_identity_contract.md` (§6, final paragraph) and `knowledge_gateway_mcp_contract.md`
  (§5, final paragraph) — each states "No `docs/parity_ledger/` entry accompanies this document...
  agent-orchestration/retrieval tooling... classifies as not requiring a parity ledger entry" —
  this ticket's policy artifact is the same kind of Phase-0 design document and, by the same
  reasoning, does not require a new parity ledger entry of its own. This is a judgment call
  consistent with existing sibling precedent, not an assumption made in isolation.

## Prior Work

- `TCK-20260728-RETRIEVAL-RETENTION-REDACTION` (done; `stored_artifacts/TCK-20260728-RETRIEVAL-RETENTION-REDACTION/`):
  produced `docs/observability/retrieval_retention_redaction_policy.md` itself. Decision-only,
  explicitly out-of-scope for any code change. This is the direct ancestor this ticket extends.
- `TCK-20260729-RETRIEVAL-CACHE-LEVELS` (done): implemented `tools/retrieval_cache.py`'s
  three marker-only tables and the MAY-list enforcement, per the policy doc above.
- `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` (done): produced
  `evidence_cache_identity_contract.md` and `cache_migration_plan.md`. The migration plan's §6
  explicitly defers all redaction/retention/GC numbers to this ticket and confirms no conflict
  exists between its additive `CREATE TABLE IF NOT EXISTS` migration design and whatever GC
  policy this ticket defines.
- `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` (done): froze the `budget_tokens`/`budget_requested`/
  `budget_returned` integer fields this ticket's token-counting method must stay compatible
  with, and the `knowledge_status_response.schema.json`'s `cache_rebuildable: boolean` field
  (line 63) — relevant to AC6's crash-recovery framing (`knowledge_status` is meant to report
  exactly the "can this be safely rebuilt" fact this ticket's test proves).

## Risks and Open Questions

- **Blocking-ish open question**: there is no existing secret-detection ruleset in this repo.
  §17 step 4 assumes one exists to reuse. This ticket's own Assumptions section already flagged
  this as something Investigate must confirm rather than assume — confirmed: it does not exist.
  The policy artifact must make an explicit choice (define a new minimal rule set as part of
  this ticket's scope vs. flag Phase 2 as blocked pending a scanner) rather than silently
  asserting reuse of something that isn't there. This should go to Plan/reviewer, not be
  resolved unilaterally by Investigate.
- **Token-counting method has no existing library to build on.** Any method chosen (character
  heuristic, word-count heuristic, or a new dependency) is a real design decision with repo-wide
  consequences (every future `budget_requested`/`budget_returned` value depends on it). Flag for
  Plan rather than assume a specific implementation.
- **AC6 crash-recovery test scope**: must be written against today's marker-only schema, not a
  hypothetical future payload schema. If a future ticket adds Level 1/2 payload tables, this
  test's assertions will need extending — this is expected and should be noted in the test file
  itself so it isn't mistaken for already covering payload recovery.
- **SQLite operational defaults are pure policy, not implementation, in this ticket.** Because
  Implementing the cache read/write paths is explicitly Out of Scope, the WAL/busy-timeout/
  permissions/stampede-guard defaults this ticket documents will not actually be enforced in
  `tools/retrieval_cache.py` until a later ticket wires them in. The policy doc must say this
  plainly so AC4's "documented and testable" isn't read as "already enforced."
- §24 item 1 (ratify/reject payload caching at all) remains open — the policy artifact must be
  written so it is useful regardless of which way that reviewer decision goes, and must not
  imply caching is already approved.

## Anti-Drift Hazards

- Do not conflate `tools/agent_codex_posttool_adapter/redaction.py` (tool-input truncation for
  an unrelated Codex-adapter monitoring pipeline) with a secret scanner for this ticket's
  purposes — it is not one, and citing it as "existing secret-detection rules" would be
  inaccurate.
- Do not silently ratify §24 item 1 by writing the policy doc in a tone that assumes payload
  caching is already approved — AC7 requires the artifact to explicitly flag itself as pending
  reviewer ratification.
- Do not implement or edit `tools/retrieval_cache.py` in this ticket — Out of Scope explicitly
  excludes cache read/write path implementation; this is a documentation/policy ticket only.
- Do not touch `src/observability/reporting/retention.py`, `src/core/retention.py`, or any
  `tools/agent-monitoring/*.py` writer — the prior sibling ticket's Out of Scope excluded these
  and nothing in this ticket's scope reopens that boundary.
- Do not write GC rules that could evict rows the evidence-cache-identity contract still
  considers valid evidence — cross-check any "safe eviction candidate" language against
  `evidence_cache_identity_contract.md` §4's provider-generation-fallback rule before finalizing.
- Do not invent a new bare `schema_version` name for any SQLite metadata this ticket discusses —
  `cache_migration_plan.md` §1 already reserves `retrieval_cache_schema_version` as the DDL-shape
  version, distinct from `RETRIEVAL_VERSION` (cache-key logic) and `retrieval_event_schema_version`
  (event field shape). Reusing the bare name would recreate the exact ambiguity that document
  exists to prevent.
