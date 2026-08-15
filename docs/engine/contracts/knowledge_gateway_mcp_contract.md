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
sole authority a future router may consult before treating a provider as able to do something. The
router must never claim a capability the descriptor does not advertise: if `cancellation: false`,
the router must not attempt to cancel a call to that provider; if `timeout: false`, the router must
not assume a bounded-latency guarantee from that provider. The contract-level expression of this
rule is a helper `capability_allows(descriptor: dict, capability_name: str) -> bool`, returning the
boolean value of the named field. `tests/tools/test_knowledge_gateway_contract_schemas.py` defines
this helper inline (test-only, not `tools/` code — no router exists yet to own it) and asserts it
returns `False` for both populated descriptors' `cancellation` and `timeout` fields, matching §3's
grounded values below.

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
  `provider_capabilities_graphify.json` — the two populated descriptor instances (§3 above).
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
