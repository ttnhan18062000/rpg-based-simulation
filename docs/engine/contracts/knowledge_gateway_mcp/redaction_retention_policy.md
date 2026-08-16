---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, schema, mcp]
---

# Knowledge Gateway MCP — Redaction and Retention Policy

Source ticket: `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`. This is a Phase 0 policy/contract
document. No `src/` or `tools/` code implementing cache payload writes, secret scanning, SQLite
operational limits, or garbage collection exists yet, and none is added by this ticket. It is
placed under `docs/engine/contracts/knowledge_gateway_mcp/` alongside the sibling wire-contract and
identity-contract documents produced by `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` and
`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`.

## 1. Purpose

This document extends, and does not supersede,
`docs/observability/retrieval_retention_redaction_policy.md`. That document's own Decision A
explicitly frames its category taxonomy as meant to be extended by a later ticket — this is that
later ticket, scoped specifically to the Knowledge Gateway MCP's future cached *payload* rows
(answer/context content), which did not exist as a concept when that prior policy was written.
Where the two documents overlap (the MAY/PROHIBITED field vocabulary, the events-vs-caches
retention split), this document defers to and does not restate that prior policy as authoritative;
where this document adds new rules specific to payload caching (§17/§19/§24 item 1 of
`docs/plans/knowledge-gateway-mcp-proposal.md`), those rules are new and are recorded here.

## 2. Eligible Source Types / Allowlist

Only source types/paths explicitly allowlisted below may ever reach a cache write, once payload
caching is implemented. This is the same MAY-list discipline `MAY_LIST_COLUMNS`
(`tools/retrieval_cache.py:70-89`) already enforces in code today for marker-only rows: hashes,
IDs, counts, reason codes, scores, latency, version numbers, cache status, `created_at`. No
payload/text/content column exists in that allowlist today — this section governs what happens
when a future ticket adds one.

Eligible source types, at Phase 2/3, are limited to:

- Context Search provider results (`tools/search_mcp.py`), scoped to documentation, tickets,
  investigations, and working-history material already indexed in `knowledge-index/knowledge.db`.
- Graphify provider results, scoped to source-symbol and dependency-relationship data already
  extracted into the graphify graph.
- Content derived exclusively from the above two providers — never a raw filesystem read outside
  those indexes, never a live shell command's stdout, never an arbitrary tool-call payload.

Any source type not named above is not eligible for a cache write until a future ticket explicitly
adds it to this allowlist.

## 3. Redaction Rules

Before any content-derived value is hashed or stored in a cache row, the following must be stripped
and replaced with a stable placeholder:

- **Local usernames** — any OS username or home-directory segment (e.g. `/home/<user>/`,
  `C:\Users\<user>\`) must be replaced with a fixed placeholder token (e.g. `<local-user>`), never
  the real value, so no cache row can leak who ran the agent locally.
- **Machine-specific absolute paths** — any absolute filesystem path that is specific to the local
  machine (not the repository-relative path) must be replaced with a fixed placeholder token (e.g.
  `<local-path>`) or rewritten to the repository-relative path when one exists, so no cache row can
  leak local filesystem layout.

Redaction runs before hashing: a hash computed over unredacted content and a hash computed over
redacted content are different values by design, and only the redacted-content hash may ever be
persisted.

## 4. Secret-Scan Disclosure

No secret-detection or credential-scanning module exists anywhere in this repository today.
`tools/agent_codex_posttool_adapter/redaction.py` is a different, unrelated subsystem — it
truncates/selects fields for `agent-monitoring/tools.jsonl` records (`summarize_tool_input()`/
`derive_status()`, `tools/agent_codex_posttool_adapter/redaction.py:12-31`); it does not
pattern-match or strip secret values, and must not be cited as an existing secret-detection
precedent for this policy.

**This policy defines a new baseline regex ruleset, as part of this ticket's own scope**, originally
covering four common credential shapes, each a well-known, low-false-positive-risk pattern requiring
no new dependency. `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s own Security-Review phase (see
below) expanded this to ten shapes, closing the concrete gaps that phase identified (no named-service
token formats, no generic password/secret-named assignment, no basic-auth-in-URL form):

| Shape | Pattern (illustrative) |
|---|---|
| AWS-style access key ID | `AKIA[0-9A-Z]{16}` |
| Generic API-key-looking assignment | `(api[_-]?key\|apikey)\s*[:=]\s*['"][A-Za-z0-9_\-]{16,}['"]` |
| PEM private-key header | `-----BEGIN (RSA \|EC \|OPENSSH )?PRIVATE KEY-----` |
| Bearer token | `Bearer\s+[A-Za-z0-9\-_.]{20,}` |
| GitHub token (`ghp_`/`gho_`/`ghs_`/`ghr_`/`github_pat_`) | `gh[pousr]_[A-Za-z0-9]{36,}\|github_pat_[A-Za-z0-9_]{20,}` |
| Slack token (`xoxb-`/`xoxa-`/`xoxp-`/`xoxr-`/`xoxs-`) | `xox[baprs]-[A-Za-z0-9\-]+` |
| OpenAI API key | `sk-(?!ant-)[A-Za-z0-9]{20,}` |
| Anthropic API key | `sk-ant-[A-Za-z0-9\-_]{20,}` |
| Generic password/secret-named assignment | `(password\|passwd\|secret)\s*[:=]\s*['"][^'"]{6,}['"]` |
| Basic-auth-in-URL | `https?://[^\s:/@]+:[^\s:/@]+@` |

**This baseline ruleset is a documented starting point, not a production-complete secret scanner.
It is explicitly NEW (not a reuse of any existing repository tooling) and explicitly
non-production-complete.** The original four-pattern set was reviewed and expanded to the ten
patterns above by a security-focused pass, closing the "must be reviewed and expanded ... before
Phase 2 payload caching goes live" precondition below for this policy's go-live moment — expansion
is not the same claim as completeness: ten well-known shapes still do not cover every real-world
credential format, and this baseline remains open to further expansion by a future pass. Any content
matching one of these ten patterns must cause the write to be rejected outright (see §7, Never-Cache
Enumeration), never silently redacted and stored.

**This precondition is now operative, not merely prospective, and has been addressed (not waived).**
`TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` implemented the original ruleset as pure functions with
no live caller. `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` is the ticket that wired real cache
reads and writes into the live `knowledge_context` request path
(`tools/knowledge_gateway_mcp.py::_run_knowledge_context()`), so cache writes governed by this
ruleset are now genuinely reachable from a real, running MCP tool call — the condition this
precondition's own "before Phase 2 payload caching goes live" language names. That ticket's own
Architecture Review ruling (DD5) made no claim that this precondition was satisfied at Implement
time; its own Security-Review phase subsequently found the original four-pattern baseline had
concrete, named gaps and required — as a narrow, bounded fix, not a redesign — the expansion to ten
patterns documented above before that ticket's own blocking gate could close. This document's table
and disclosure above reflect that expanded, current state.

## 5. Payload Size Cap

Each cached payload row is capped at **8 KB** (8192 bytes, measured on the UTF-8-encoded redacted
payload) — consistent with the "bounded/redacted" framing of
`docs/plans/knowledge-gateway-mcp-proposal.md` §24 item 1's proposed policy. A payload exceeding
this cap must cause the write to be **rejected**, not silently truncated: silent truncation would
produce a cache row that looks complete but is missing content, which is a worse failure mode than
a visible cache miss.

## 6. Redaction-Policy Version

This policy introduces its own version field, **`redaction_policy_version`** (e.g.
`redaction_policy_version: 1`), stamped onto any future payload-bearing cache row so a row can be
identified as having been written under a specific version of this policy's rules.

`redaction_policy_version` is a fourth, genuinely distinct "version" concept in this subsystem's
vocabulary, alongside three already-existing/already-scoped names, and must never be aliased to,
merged with, or confused with any of them:

- `retrieval_cache_schema_version` — the DDL/table-shape version constant
  (`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md:26-58`).
- `RETRIEVAL_VERSION` — the cache-key-derivation-logic version constant
  (`tools/retrieval_cache.py:45`).
- `retrieval_event_schema_version` — the event-field-shape version constant
  (`tools/retrieval_events.py:46`).

`redaction_policy_version` versions none of those three axes — it versions only the redaction/
allowlist/secret-scan/size-cap rules defined in §2–§5 of this document. A future implementation
bumps `redaction_policy_version` when, and only when, those rules themselves change.

**No callable shipped as part of this ticket** (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`) —
this section documented the field only. `redaction_policy_version` is now implemented as a real,
stamped value: the module-level constant `redaction_policy_version = 1`
(`tools/knowledge_gateway_redaction.py:47`) and the `WriteDecision.redaction_policy_version` field
(`tools/knowledge_gateway_redaction.py:225`), stamped on every `ALLOW` and `REJECT` decision
returned by `evaluate_write_candidate()`, added by `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`.
Its distinctness from the other 3 version axes named above is verified by a dedicated test in
`tests/tools/test_knowledge_gateway_redaction.py`.

**Persistence resolved by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` (Architecture Review DD3,
option b).** `redaction_policy_version` is now persisted onto an actual
`retrieval_provider_result_cache_rows` column, not stamped in-memory only: a new
`migration_003_add_redaction_policy_version_column(conn)` (`tools/retrieval_cache.py:265-283`) adds
the column via an idempotent `ALTER TABLE ... ADD COLUMN`, guarded by an explicit `PRAGMA
table_info` existence check (SQLite has no `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).
`LEVEL1_CACHE_COLUMNS` grew from 21 to 22 entries as a result. See
`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2 for the migration's
documented shape.

## 7. Never-Cache Enumeration

The following must never be written to any Knowledge Gateway cache row, under any circumstance,
regardless of source type, redaction pass, or size:

- Secrets and credentials.
- Tokens (API tokens, session tokens, auth tokens of any kind).
- Raw environment values (the literal contents of environment variables).
- Unredacted sensitive tool output (any tool-call output that has not passed the redaction rules in
  §3 and the secret-scan check in §4).
- Arbitrary configuration-file contents (a config file's raw text, as opposed to a reference to it
  by hash or path).
- Unrestricted raw prompts (a caller's full, unprocessed prompt text, as opposed to the normalized/
  hashed form `tools/retrieval_cache.py:175-180` already uses for query identity today).

This list is exhaustive of the categories this policy defines as never-cacheable; it is not a
catch-all sentence, and each item above must be treated as independently enforceable.

## 8. Token-Counting Method

The reproducible, dependency-free token-counting method for this subsystem is named
**`kgmcp_char_heuristic_v1`**:

```
token_count ≈ ceil(len(text.encode("utf-8")) / 4)
```

This is the widely-used "~4 bytes per token" approximation. No tokenizer library (`tiktoken` or
otherwise) is a repository dependency today — this method is chosen specifically to avoid adding
one, consistent with the repo-wide precedent already set by
`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2's explicit refusal to add
a migration library for a comparable Phase-0 concern.

`kgmcp_char_heuristic_v1` carries a **documented tolerance of ±20%** against any downstream true
token count. This tolerance is the standard against which a future implementation validates the
Phase 3 pilot's "returned content respects the requested budget within a documented tolerance"
acceptance bar (`docs/plans/knowledge-gateway-mcp-proposal.md` §21).

The method produces a plain non-negative integer, compatible with the already-frozen integer-typed
budget fields it must feed:

- `budget_tokens` — `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json:17-19`
  (`"type": "integer"`).
- `budget_requested` and `budget_returned` —
  `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json:117-118`
  (both `"type": "integer"`).

`budget_class` (the caller's budget tier/bucket,
`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md:43` — "The
caller's budget tier (token/latency budget bucket), not the raw numeric budget") is a separate
field from the raw integer count above. This policy names provisional, illustrative-only bucket
boundaries for deriving `budget_class` from a `kgmcp_char_heuristic_v1` count — small (≤500 tokens),
medium (501–2000 tokens), large (>2000 tokens) — without redefining `budget_class` itself, since no
schema currently freezes its value set as an enum.

**No callable shipped in `tools/` as part of this ticket** (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`)
— this section documented the method only, consistent with that ticket's Out of Scope excluding
cache read/write implementation. `kgmcp_char_heuristic_v1` is now implemented as a real callable at
`tools/knowledge_gateway_packet_assembly.py:81`, added by `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`
as part of its token-budgeted assembly work (§15); see
`test_kgmcp_char_heuristic_v1_matches_frozen_formula`
(`tests/tools/test_knowledge_gateway_packet_assembly.py:111`) for the formula-parity test.

**Ratification (§24 item 4):** approved as drafted by the repository owner on 2026-08-15, recorded
in `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`. `kgmcp_char_heuristic_v1` and its ±20%
tolerance are approved; no changes were made to the method described above as a result of
ratification.

## 9. SQLite Operational Limits

These were **documented defaults, not implemented in `tools/retrieval_cache.py` by this
document's own architectural boundary** — `tools/retrieval_cache.py` is not, and is not intended to
become, the home for these limits. They are now implemented as real, tested logic
in a separate new module, `tools/knowledge_gateway_redaction.py`, added by
`TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`: `open_connection_with_limits(db_path)` applies
`PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` on every connection open and chmods the
file `0600` immediately after creation (never re-chmodding a pre-existing file);
`check_db_size_within_limit(db_path)` enforces the 256 MB ceiling; `execute_bounded_transaction()`
wraps a caller-supplied statement list in a single per-call transaction; and
`acquire_write_guard()` / `release_write_guard()` implement the per-key stampede guard as an
in-process lock keyed by cache key (not multi-process safe — see the functions' own docstrings).
`tools/retrieval_cache.py` itself remains byte-unchanged by this work — `db_path` is a required,
caller-supplied parameter with no default onto `tools.retrieval_cache.CACHE_DB_PATH`, and
`test_sqlite_defaults_not_silently_implemented` (`tests/docs/test_redaction_retention_policy_doc.py`)
continues to pass because it is scoped only to `tools/retrieval_cache.py`'s own source text. Wiring
these functions into `tools/retrieval_cache.py`'s or the live gateway's actual connection-opening
path remains a separate, not-yet-started ticket (`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`).

`tools/retrieval_cache.py`'s `_get_connection()` (`tools/retrieval_cache.py:96-105`) is the single
existing connection-opening code path, called by every `check_*_cache`/`write_*_cache` function and
by `prune()` (`tools/retrieval_cache.py:406-428`). Today it contains zero `PRAGMA` statements, zero
`busy_timeout` configuration, zero file-permission restriction, and zero lease/stampede-guard code —
these are genuinely undefined, not merely undocumented. Because there is exactly one connection path
today, there is no existing race or competing-writer behavior to reconcile; the defaults below
describe new behavior for that single existing path, to be wired in by a future implementation
ticket.

| Limit | Documented default |
|---|---|
| Maximum database size | 256 MB. Exceeding this ceiling blocks further writes until GC (§10) or manual `prune()` frees space. |
| TTL/usage-based eviction | Governed by the Cache-GC Defaults in §10 below, by name. |
| File permissions | `0600` (owner read/write only) on `knowledge-index/retrieval_cache.db`, set immediately after the file is created. |
| WAL mode | `PRAGMA journal_mode=WAL`, enabled on every connection open. |
| Bounded transactions | Every write path wraps its `INSERT`/`UPDATE`/`DELETE` statements in a single transaction per call (matching the existing `execute(...)` + one `commit()` shape already used throughout `tools/retrieval_cache.py`), never an open-ended multi-call transaction. |
| Busy timeouts | `PRAGMA busy_timeout=5000` (5000 ms), set on every connection open. |
| One-writer-safe migration discipline | Migrations follow `cache_migration_plan.md`'s existing additive `CREATE TABLE IF NOT EXISTS` design (`cache_migration_plan.md:26-58`, `:122`) — idempotent, safe to re-run, no `ALTER TABLE` against populated tables. |
| Per-key stampede guard | A named mechanism — a per-cache-key lease/transaction guard (e.g. an `INSERT OR IGNORE` sentinel row or an in-process lock keyed by the write's primary key) that prevents two concurrent writers from recomputing and writing the same cache key simultaneously. Described here as policy, not implementation. |

## 10. Cache-GC Defaults

The only existing eviction mechanism today is `prune(older_than_days, table)`
(`tools/retrieval_cache.py:406-428`) — operator-invoked only, never called from any
`check_*_cache`/`write_*_cache` function
(`TestPrune::test_prune_is_not_invoked_by_any_check_or_write_function`,
`tests/tools/test_retrieval_cache.py`). This section's GC defaults are new *policy* describing
future automatic GC behavior; **they do not change `prune()`'s current manual-only status**, and no
automatic GC is implemented by this ticket.

Safe-eviction candidates, once automatic GC is implemented, are limited to:

- Expired exact-query results (rows whose query/filters/corpus-generation/retrieval-version key is
  no longer reachable by any live query and has aged past its category's placeholder duration per
  `docs/observability/retrieval_retention_redaction_policy.md` Decision C).
- Packets for deleted branches (a context-packet row whose `repo_branch_scope` no longer resolves to
  an existing branch).
- Obsolete provider-version rows (a row keyed to a provider adapter version that has since been
  superseded, where no caller can address the old version anymore).
- Low-use regenerable packets (a packet row with negligible hit count, cheap to recompute on demand).
- Stale rows superseded by a refreshed row sharing the same primary key (the pre-existing
  `INSERT OR REPLACE` pattern already used by `write_index_cache`/`write_query_cache`/
  `write_packet_cache` naturally produces this case).
- Failed/incomplete writes (a row left in a non-terminal `cache_status` by an interrupted write,
  never a row with a completed, valid `cache_status`).

**This GC policy defers to, and never overrides,**
`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §4's hard rule:
*"a `SYMBOL`- or `FILE`-backed evidence record ... must never be invalidated by an unrelated
corpus-wide `PROVIDER_GENERATION` bump alone."* None of the six safe-eviction candidates above
authorizes evicting a `SYMBOL`- or `FILE`-backed evidence row on a bare `PROVIDER_GENERATION` bump —
each candidate is scoped to disposable cache bookkeeping (expired keys, deleted-branch scope,
superseded rows, low-value regenerable packets, incomplete writes), never to the identity contract's
protected evidence categories. Historical project facts remain in authoritative sources (docs,
tickets, source code, parity ledger) regardless of any cache eviction under this section — a cache
row's eviction never deletes or alters the underlying project truth it referenced.

## 11. Ratification Status

**Ratified as drafted.** The repository owner, acting as reviewer, ratified §24 item 1 of
`docs/plans/knowledge-gateway-mcp-proposal.md` (caching bounded/redacted answer/context payloads
from allowlisted source types) on 2026-08-15, recorded in
`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`. No changes were made to §2–§10's rules as a result
of ratification — the allowlist, redaction rules, size cap, secret-scan baseline, never-cache
enumeration, token-counting method, SQLite limits, and cache-GC defaults are approved exactly as
drafted.

Ratification authorizes a future ticket to begin implementing Phase 2 payload caching against this
policy. It does not itself implement anything — no `src/`/`tools/` code changes accompany this
ratification. The secret-scan ruleset in §4 remains explicitly flagged as a non-production-complete
starting baseline; ratifying the policy's overall shape did not itself discharge the "must still be
reviewed and expanded by a dedicated security-focused pass before Phase 2 payload caching goes live"
follow-up requirement. **Phase 2 payload caching went live with
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`; that ticket's own Security-Review phase — not this
ratification — was the vehicle for the required security-focused pass, and performed it: §4's
secret-scan baseline was reviewed and expanded from four to ten patterns as a direct result. See §4
for the expanded pattern set and its own disclosure that expansion is not a claim of completeness —
the baseline remains a documented starting point, open to further expansion, not a
production-complete secret scanner.**

## 12. Cross-References

- `docs/observability/retrieval_retention_redaction_policy.md` — the prior, more general
  retrieval/event redaction and retention policy this document extends (§1).
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §4 — the
  `PROVIDER_GENERATION` fallback rule this document's GC defaults (§10) defer to.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — the migration design this
  document's SQLite limits (§9) and redaction-policy version (§6) stay compatible with.
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` /
  `knowledge_context_response.schema.json` — the frozen `budget_tokens`/`budget_requested`/
  `budget_returned` integer fields this document's token-counting method (§8) must stay compatible
  with.
- `tools/retrieval_cache.py` — the existing module this document's SQLite limits (§9) and GC
  defaults (§10) describe future behavior for; zero edits made to it by this ticket.

No `docs/parity_ledger/` entry accompanies this document — this subsystem is
agent-orchestration/retrieval tooling, the same category the sibling
`evidence_cache_identity_contract.md` §6 and `knowledge_gateway_mcp_contract.md` §5 already classify
as not requiring a parity ledger entry.
