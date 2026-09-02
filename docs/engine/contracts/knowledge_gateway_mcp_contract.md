---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, schema, mcp]
---

# Knowledge Gateway MCP Contract

This document defines a **contract for a future implementation**. No `src/` or `tools/` code
implementing a `knowledge_context`/`knowledge_status` MCP tool, a provider router, or a gateway
cache exists yet, and none is added by this ticket (`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`). It is
placed under `docs/engine/contracts/` alongside `context_packet_contract.md`, whose role — a
schema contract for a not-yet-built subsystem — this document mirrors for the Knowledge Gateway
MCP proposal (`docs/plans/knowledge-gateway-mcp-proposal.md`, Phase 0, §20). This is Phase 0's
interface-shape half: the MCP wire contract and the provider adapter contract. Evidence identity,
cache-lookup identity, and redaction/retention policy are covered by sibling tickets
(`KGMCP-EVIDENCE-CACHE-IDENTITY`, `KGMCP-REDACTION-RETENTION-POLICY`), not this document.

**Phase 1 update (2026-08-15, `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`):** the "no code exists yet"
framing above describes this document's own Phase 0 ticket and is now historical, not current — a
real `knowledge_context`/`knowledge_status` MCP server (`tools/knowledge_gateway_mcp.py`) and
router (`tools/knowledge_gateway_router.py`) now exist and were built and validated against this
contract's frozen schemas without any schema change. No gateway cache exists yet (Phase 2), so the
cache-related portions of this framing remain accurate today.

---

## 1. Provider adapter invocation contract

Per `docs/plans/knowledge-gateway-mcp-proposal.md` §7.1: "All adapters must support timeout,
cancellation where the underlying interface permits it, version reporting, and deterministic
fixture tests."

The table below checks the two existing candidate adapters against each of the four requirements.
Every cell is grounded in direct observation of the real, currently-installed code/binary — not in
the proposal's own aspirational language for what a finished adapter should do.

| Requirement | Context Search (`tools/search_mcp.py`) | Graphify (CLI-shelled, `graphify` binary) |
|---|---|---|
| Timeout | Not supported today — no wrapping timeout anywhere in `_run_search()`'s call path in `tools/search_mcp.py` or `tools/hybrid_retrieval.py`. | Not supported today — `graphify -h`'s `query` subcommand accepts only `--dfs`, `--context`, `--budget`, `--graph`. No `--timeout` flag exists on `query` or any other subcommand (confirmed by reading the full `graphify -h` output). |
| Cancellation | Not supported — no cancellation hook anywhere in the call path. | Not supported — no `cancel`/`kill` subcommand or signal-based cancellation is documented anywhere in `graphify -h`'s output. |
| Version reporting | Not supported at the adapter level — `_run_health()` returns `index_version`, derived from the SQLite index file's mtime (`os.path.getmtime`), not a code/adapter version. | Supported at the CLI level — `graphify --version` prints `graphify 0.8.39` (stdout, exit 0). No *adapter* exists yet to version separately from the CLI tool it shells out to. |
| Deterministic fixture tests | Established pattern exists: `tests/tools/test_search_mcp.py` (15 tests) exercises `_run_search`/`_run_health`/error-dict shapes. | No adapter fixture tests exist yet — no adapter code exists to test. This ticket's own `tests/tools/test_knowledge_gateway_contract_schemas.py` fixture-tests the CLI's raw observable behavior (`graph.json`'s structure, `graphify -h`'s documented flags) as the nearest honest equivalent. |

Neither adapter satisfies timeout or cancellation today. This is recorded honestly rather than
defaulted to `true` by echoing §7.1's aspirational requirement — see §3 below.

---

## 2. `ProviderCapabilities` descriptor semantics

Per `docs/plans/knowledge-gateway-mcp-proposal.md` §8.1, every adapter (Context Search, Graphify
now; Parity Ledger later, per Phase 4) must expose a `ProviderCapabilities` descriptor —
structurally defined in
`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` — with the
following twelve fields: `provider_id`, `adapter_version`, `stable_entity_ids`,
`evidence_granularities[]`, `fine_grained_fingerprints`, `incremental_refresh`,
`deterministic_relationships`, `historical_queries`, `negative_knowledge_support`, `cancellation`,
`timeout`, `branch_awareness`, and the optional `generation_fingerprint`.

**Routing consequence (§8.1).** A capability descriptor is not decorative metadata — it is the
sole authority the router may consult before treating a provider as able to do something. The
router must never claim a capability the descriptor does not advertise: if `cancellation: false`,
the router must not attempt to cancel a call to that provider; if `timeout: false`, the router must
not assume a bounded-latency guarantee from that provider. The contract-level expression of this
rule is a helper `capability_allows(descriptor: dict, capability_name: str) -> bool`, returning the
boolean value of the named field. `tests/tools/test_knowledge_gateway_contract_schemas.py` defines
this helper inline (test-only, not `tools/` code). A real router now exists —
`tools/knowledge_gateway_router.py::capability_allows()`, built by
`TCK-20260815-KGMCP-P1-QUERY-ROUTER` — and owns the live decision logic; the test-local copy above
was deliberately left in place unmodified as a cross-checked stub rather than retired
(`tests/tools/test_knowledge_gateway_router.py::test_router_never_claims_unadvertised_capability`
asserts the two agree on real fixtures). Both copies assert `capability_allows()` returns `False`
for both populated descriptors' `cancellation` and `timeout` fields, matching §3's grounded values
below.

The two populated instances are:
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json`
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_graphify.json`

---

## 3. Evidence for the populated descriptor values

### Context Search (`provider_capabilities_context_search.json`)

- `adapter_version: null` — `_run_health()` (`tools/search_mcp.py`) returns
  `{status, index_version, chunks, model}`; `index_version` is derived from the SQLite index
  file's mtime, not a code/adapter version. Reporting it as `adapter_version` would misrepresent
  current behavior, so `null` is the honest value — there is no adapter version to report.
- `stable_entity_ids: "PARTIAL"` — result rows carry `doc_id` (`_run_search()`'s result-dict
  construction), but this ticket's investigation did not verify `doc_id` uniqueness/stability
  across index rebuilds, so `"FULL"` would overclaim.
- `evidence_granularities: ["chunk"]` — results are per-chunk (`doc_id` + `section` + `heading`).
- `fine_grained_fingerprints: false` — no per-result hash field exists in the returned dict
  (confirmed fields: `doc_id, title, heading, source_path, section, score, semantic_score,
  keyword_score, excerpt` — no hash).
- `incremental_refresh: false` — `_run_search()`'s own error dict says `"action": "run make
  knowledge-index"` on a missing index, implying a full rebuild path; no incremental mechanism is
  evidenced.
- `deterministic_relationships: "NONE"` — this is a ranked-retrieval provider, not a
  relationship-graph provider.
- `historical_queries: false` — no query-history storage is evidenced anywhere in
  `tools/search_mcp.py`.
- `negative_knowledge_support: "NONE"` — an empty result list carries no evidenced
  verified-absence guarantee.
- `cancellation: false`, `timeout: false` — confirmed, no mechanism anywhere in the call path.
- `branch_awareness: "NONE"` — `_run_search(query, top_k, section, mode)`'s signature has no
  branch/working-tree parameter.
- `generation_fingerprint: true` — `index_version` (mtime-derived) is a real, if coarse,
  whole-index generation signal, consistent with `fine_grained_fingerprints: false`.

### Graphify (`provider_capabilities_graphify.json`)

- `adapter_version: "graphify-cli-0.8.39"` — `graphify --version` prints `graphify 0.8.39`
  (confirmed this session). Named explicitly as `graphify-cli-<version>`, not a bare version
  string, because no adapter exists yet — the version being reported belongs to the wrapped CLI
  tool, not to a code artifact this ticket would otherwise be claiming exists.
- `stable_entity_ids: "PARTIAL"` — `graphify-out/graph.json` node objects carry a deterministic,
  path-derived `id` (e.g. `"agents_skills_api_design_principles_assets_rest_api_template_py_..."`
  for `source_file: ".agents/skills/api-design-principles/assets/rest-api-template.py"`), not a
  random UUID, but cross-rebuild uniqueness across all 31,422 current nodes was not verified in
  this ticket, so `"FULL"` would overclaim.
- `evidence_granularities: ["node", "edge"]` — `graph.json` has top-level `nodes`, `links`, and
  `hyperedges` keys (confirmed by direct read).
- `fine_grained_fingerprints: false` — only one whole-graph `built_at_commit` field
  (`"29d78798a1a66296231cede82bcf20de55b93cd8"`, confirmed) exists; no per-node/per-edge hash was
  found on the sampled node or link objects.
- `incremental_refresh: false` — `graphify update <path>` exists (`graphify -h`), but re-extracts
  and can overwrite `graph.json`; no evidence of a narrower, verified incremental path was
  gathered, so the conservative default applies.
- `deterministic_relationships: "PARTIAL"` — `graph.json`'s `links`/`hyperedges` carry a
  `confidence` field whose value set is confirmed (by direct read of the live `graph.json`) to be
  `{"EXTRACTED", "INFERRED"}` — both deterministic-extraction and inferred (non-deterministic)
  relationship kinds coexist in the same graph, so `"FULL"` would overclaim and `"NONE"` would
  underclaim.
- `historical_queries: false` — `save-result` (`graphify -h`) writes Q&A memory for the graph's
  own feedback loop, not a queryable history of past calls; the two are not the same thing.
- `negative_knowledge_support: "NONE"` — not evidenced.
- `cancellation: false`, `timeout: false` — confirmed: no `--timeout` flag exists on `query` or any
  other subcommand in `graphify -h`'s full output, and no cancel/kill mechanism is documented.
- `branch_awareness: "NONE"` — `graph.json` is built from whatever was checked out at
  `built_at_commit`; no branch-scoping flag exists on `query`.
- `generation_fingerprint: true` — `built_at_commit` is a real, confirmed field.

### Parity Ledger (`provider_capabilities_parity_ledger.json`)

**Phase 4 update (2026-08-16, `TCK-20260816-KGMCP-P4-PARITY-ADAPTER`):** this subsection fulfills
§2's own forward reference above ("Parity Ledger gains one before its Phase 4 adapter is enabled").
Unlike Graphify's descriptor (§4 below), this one describes a real, tested, **in-process** adapter
(`tools/knowledge_gateway_router.py::_run_parity_provider()`), not a CLI shell-out — it is
genuinely, end-to-end wired: `tools/knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()`
dispatches to it for any query routed to the `requirement_completeness_verification` shape (a
`parity_id`-matched identifier, or the free-text `Q3_requirement_completeness` shape), and
`render_candidates()` renders its results into real response statements/context/evidence entries.

- `adapter_version: null` — no adapter code exists to version yet; `tools/parity_index.py` exposes
  `SCHEMA_VERSION`/`IMPORTER_VERSION` module constants, but these describe the *index build format*,
  not the caller/adapter code — the same reasoning already applied to Context Search's
  `index_version` above. `null` is the honest value.
- `stable_entity_ids: "FULL"` — parity entry-ids are human-authored YAML fields
  (`docs/parity_ledger/schema.json` id pattern `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`, extended from the
  single-segment-only `^[A-Z]+-[0-9]{3}$` by `TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT`
  to admit established multi-segment shard ids like `WORLD-DEMO-001`), never build-derived;
  cross-shard uniqueness is enforced at build time by `DuplicateEntryIdError`
  (`tools/parity_index.py:235`, inside `_populate_entries()`). A removed id is tombstoned, never
  reused (`evidence_identity_kinds.schema.json`'s `PARITY_ENTRY.normalization_rules.delete`). This
  is a directly-verified guarantee, unlike Context Search's `doc_id`/Graphify's node `id`, both
  marked `PARTIAL` above because cross-rebuild stability was not verified for either — Parity's is.
- `evidence_granularities: ["entry"]` — `entry()` (`tools/parity_index.py:550-596`) returns one
  whole ledger entry per call; no sub-entry granularity exists.
- `fine_grained_fingerprints: true` — `entry()`'s returned record includes `canonical_fragment_hash`,
  a real per-entry sha256 of the entry's own serialized YAML content, computed at
  `tools/parity_index.py:238-240` and stored per `_EXPECTED_COLUMNS["entries"]`
  (`tools/parity_index.py:113-117`) — the exact field `evidence_identity_kinds.schema.json`'s
  `PARITY_ENTRY.preferred_fingerprint` already names. Unlike Context Search (`false`, no per-result
  hash field exists), Parity genuinely has one.
- `incremental_refresh: false` — `build()` (`tools/parity_index.py:530-547`) always does a full
  `_atomic_replace_db()` rebuild of the whole index file; no single-entry incremental update path
  exists anywhere in the module.
- `deterministic_relationships: "PARTIAL"` — `entry()`'s `code_refs`/`test_refs`/`constraint_refs`/
  `ticket_refs` come from `_populate_ref_tables()` (`tools/parity_index.py:271-310`), which inserts
  both `relation="declared"` refs (the structured `test_path` field, L288-289, explicitly authored)
  and `relation=None` refs (regex-scraped out of free-text `v2_evidence`/`legacy_evidence`/`text`
  fields, L296-310, deterministic match but never validated against the actual file or curated by a
  human) — a coexisting validated/unvalidated split, the same reasoning Graphify's own `PARTIAL`
  (`EXTRACTED`/`INFERRED` split) applies above. `FULL` would overclaim the unvalidated half; `NONE`
  would underclaim the declared half.
- `historical_queries: false` — no query-history storage exists anywhere in `tools/parity_index.py`.
- `negative_knowledge_support: "SCOPED"` — **earned, not assumed**: `_run_parity_provider()` calls
  `check_staleness()` (`tools/parity_index.py:406-447`) whenever `entry()` returns `found: False`,
  attaching the real freshness signal (`source_manifest_hash`/`live_hash` recomputed against the
  live `docs/parity_ledger/*.yaml` shards) to its return value under a `staleness` key. Per
  `tmp/mcp-followup-instruction.md` §5's stricter definition ("evidence + validated search scope,"
  not just an absent lookup), a bare `entry()` call alone would only justify `NONE` — the checked
  scope is what earns `SCOPED` here. **Disclosed limitation (not silently dropped):** this makes the
  *adapter's* `SCOPED` claim honest, but it does not yet flip any real `_run_knowledge_context()`
  response's `verification` field end-to-end — `assemble_packet()`'s own zero-statements
  negative-claim auto-trigger (`tools/knowledge_gateway_packet_assembly.py`, the `if not statements:`
  block) never threads a real `validated_scopes` value through to `build_negative_claim_support()`
  regardless of which provider's descriptor declares `SCOPED`. Threading `validated_scopes` into
  that single auto-trigger call site is a distinct, separately-scoped follow-up, deliberately
  deferred by this ticket's plan.md (see its Anti-Drift Notes and Summary).
- `cancellation: false`, `timeout: false` — `entry()`'s call path (`_connect_readonly()` → a
  synchronous `sqlite3` query, `tools/parity_index.py:94-99, 550-556`) has no cancellation hook and
  no timeout parameter anywhere.
- `branch_awareness: "NONE"` — `entry(entry_id, db_path=None)`'s signature has no branch/
  working-tree parameter; the index reflects whatever `docs/parity_ledger/*.yaml` shards existed at
  the last `build()` call, not the current branch.
- `generation_fingerprint: true` — `check_staleness()`'s `source_manifest_hash`/`live_hash`
  (`tools/parity_index.py:402, 424`) is a real, content-derived, whole-shard-set fingerprint,
  directly analogous to Graphify's `built_at_commit` above.

**A second disclosed gap, found during this same doc-update pass, outside this ticket's own
Related Code Areas:** now that `parity_ledger` is a genuinely live third provider (able to appear in
a real response's `providers_consulted_this_call`), `tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES`
(only `SOURCE_TYPE_CONTEXT_SEARCH`/`SOURCE_TYPE_GRAPHIFY`) and the Level 1/Level 2 cache-write
`source_type` derivation in `tools/knowledge_gateway_cache.py` (`"context_search" in
providers_consulted else SOURCE_TYPE_GRAPHIFY` — a binary check with no `parity_ledger` branch) do
not account for it. Because `parity_ledger` is only ever selected alongside `context_search` on the
`requirement_completeness_verification` row (never alone), this binary check always resolves such a
payload's `source_type` to `SOURCE_TYPE_CONTEXT_SEARCH` — the write is allowed, but the resulting
cache row is mislabeled rather than being explicitly allowlisted (or rejected) as parity-sourced.
See `redaction_retention_policy.md` §2 for the full disclosure; not fixed here, as it is a
code change to files outside this ticket's own Scope/Related Code Areas, not a documentation gap.

---

## 4. Design Decision D1 — the Graphify descriptor documents the real CLI binary, not a future in-process adapter

The Knowledge Gateway proposal's own architectural preference (§7.1) is for "local deterministic
interfaces rather than one MCP server recursively calling another" — i.e. a bounded, in-process
Graphify query adapter. That preference describes a **Phase 1 implementation target**, not a
Phase 0 contract-freeze requirement; §7.1 itself says "Exact callable boundaries and structured
Graphify output are Phase 0 contract deliverables," meaning Phase 0's job is to *write down* the
target boundary, not claim it already exists.

No Python-callable Graphify interface exists anywhere in this repo today — `graphify` resolves to
a standalone CLI binary, `python3 -c "import graphify"` raises `ModuleNotFoundError`, and
`tools/graphify_to_html.py` (the only Graphify-adjacent file under `tools/`) converts an existing
`graph.json` to HTML, not a query interface. Populating a *tested*, *honest* descriptor (a hard
acceptance criterion) therefore means describing the CLI's real, observable behavior — a
descriptor that instead described a hypothetical in-process adapter would describe code that does
not exist and so could not be tested against anything but itself. §3 above cites the exact
`graphify -h` flag, `graph.json` key, or command output backing every field value. This does not
implement the target in-process adapter or any gateway/routing code — that remains explicitly out
of this ticket's scope, and Phase 1 must build the interface §7.1 anticipates before this
descriptor's values (particularly `timeout`/`cancellation`) can honestly change to `true`.

---

## 5. Cross-references

- `docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json` — `status`, `freshness`,
  `verification`, `statement_classification` enum definitions.
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` — the
  `ProviderCapabilities` descriptor shape.
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json`,
  `provider_capabilities_graphify.json`, `provider_capabilities_parity_ledger.json` — the three
  populated descriptor instances (§3 above; the Parity descriptor added by
  `TCK-20260816-KGMCP-P4-PARITY-ADAPTER`).
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` — the
  `knowledge_context` request contract.
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` — the
  `knowledge_context` response contract (success/partial/error, three-dimension status, `conflicts[]`).
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json` — the
  `knowledge_status` response contract.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — the
  lookup-identity vs. evidence-validity-identity split (§11.1/§11.2) and repository/branch/
  working-tree cache scope (§12.3), owned by the sibling `KGMCP-EVIDENCE-CACHE-IDENTITY` ticket.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` — the 8 closed
  evidence identity kinds (§12.1), owned by the same sibling ticket.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — the migration design for
  evolving `knowledge-index/retrieval_cache.db` in place (§10.1/§19), owned by the same sibling
  ticket.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — the cached-payload
  eligible-source allowlist, redaction rules, secret-scan disclosure, payload size cap,
  `redaction_policy_version`, never-cache enumeration, `kgmcp_char_heuristic_v1` token-counting
  method, SQLite operational limits (§9), and cache-GC defaults (§10), owned by the sibling
  `KGMCP-REDACTION-RETENTION-POLICY` ticket. Drafted, not ratified — see that document's §11
  (Ratification Status).
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` — the fixed,
  versioned representative-query corpus and its real recorded direct-tool baseline, the 5-point
  latency measurement/instrumentation contract (lookup, evidence-validation, provider-fallback,
  packet-assembly, end-to-end), baseline-derived promotion thresholds, and the §18.1 repeated-demand
  estimation design, owned by the sibling `KGMCP-MEASUREMENT-BASELINE` ticket.

`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 0's three relevant checklist bullets
("Freeze versioned JSON Schemas...", "Define provider adapter invocation, timeout, version, and
fixture contracts", "Define and test provider capability descriptors for Context Search and
Graphify") are satisfied by this ticket's schema files, this document, and
`tests/tools/test_knowledge_gateway_contract_schemas.py`. §20 itself is not edited by this ticket —
that cross-reference update, if desired, is a separate, optional follow-up.

No `docs/parity_ledger/` entry accompanies this document — this subsystem is
agent-orchestration/retrieval tooling, the same category `context_packet_contract.md` §4 already
classifies as not requiring a parity ledger entry.
