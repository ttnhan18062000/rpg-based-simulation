---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-CONTRACT-SCHEMAS
artifact_type: investigation
tags: [ai, schema, mcp]
---

# Investigation — TCK-20260814-KGMCP-CONTRACT-SCHEMAS

## Current Behavior

**`tools/search_mcp.py`** (the existing Context Search adapter this ticket must write a
capability descriptor for):
- Exposes two MCP tools via `FastMCP` stdio transport: `search_docs` (`tools/search_mcp.py:224-244`)
  and `search_health` (`:246-253`).
- `_run_search()` (`:82-144`) has **no explicit timeout, no cancellation hook, and no version
  field in its return shape**. It lazy-loads a `SentenceTransformer` model and BM25 index on first
  call (`_ensure_loaded()`, `:64-77`), returning `{"error": "index not found", "action": "..."}` on
  missing index and `{"error": f"embed failed: {exc}"}` on embedding failure — both untyped ad hoc
  error dicts, not a structured error contract.
- `_run_health()` (`:147-165`) returns `{status, index_version, chunks, model}` — `index_version`
  is derived from the SQLite file's mtime, not a semantic adapter version.
- Result rows carry `doc_id, title, heading, source_path, section, score, semantic_score,
  keyword_score, excerpt` (`:129-141`) — no `authority`/`freshness`/`kind` fields at the MCP-tool
  boundary (those exist one layer down, in `HybridResult`, but `_run_search()` does not surface
  them into the returned dict today).
- **Conclusion for the capability descriptor**: today's adapter has `cancellation: false`,
  `timeout: false` (no wrapping timeout anywhere in `search_mcp.py` or its caller path), and no
  `adapter_version` field to report — populating `ProviderCapabilities.timeout`/`cancellation` as
  `true` would misrepresent current behavior.

**`tools/hybrid_retrieval.py`** (underlying retrieval `search_mcp.py` calls):
- `hybrid_fuse_and_filter()` (`:224-331`) is the core entry point: bounded dense (ANN) +
  lexical (BM25) candidate retrieval, RRF fusion (`reciprocal_rank_fusion()`, `:59-77`,
  `DEFAULT_RRF_K = 60`), and a pre-fusion authority/freshness filter (`filter_candidates()`,
  `:127-156`) resolved against `docs/REGISTRY.yaml` via `resolve_metadata()` (`:104-120`).
- `HybridResult` (`:163-182`) is an explicitly frozen, load-bearing dataclass shape — its docstring
  states `TCK-20260729-CONTEXT-PACKET-ASSEMBLY has a hard, load-bearing dependency on this field
  set`. It already carries `authority`/`freshness`/`kind` (registry-backed, `UNRATED` sentinel
  otherwise per `resolve_metadata()`) — this is the closest existing analog to this ticket's
  `verification`/`evidence` concepts, but it is a retrieval-fusion result, not a knowledge-gateway
  statement; the two vocabularies must not be silently equated.
- No timeout, cancellation, or generation-fingerprint concept exists in this module either.
  `resolve_metadata()`'s `UNRATED` sentinel (asserted distinct from `AUTHORITY_VALUES`/
  `STATUS_VALUES` at `:41-45`) is a real precedent for "no registry-backed signal" — directly
  relevant to how the frozen `ProviderCapabilities`/evidence contract should represent "provider
  cannot supply this."

**Graphify query adapter — does not exist as a Python-callable interface.** Confirmed by direct
check: `graphify` resolves to a standalone CLI binary (`/home/u24desktop/.local/bin/graphify`);
`python3 -c "import graphify"` raises `ModuleNotFoundError: No module named 'graphify'`. `tools/`
contains no Graphify wrapper module — the only Graphify-adjacent file is
`tools/graphify_to_html.py`, which converts an existing `graphify-out/graph.json` to HTML and is
not a query interface. There is no in-process "bounded local Graphify query adapter with timeout,
structured output, and explicit stale/unavailable results" anywhere in this repo today. The
proposal's own §7.1 already anticipates this: "Exact callable boundaries and structured Graphify
output are Phase 0 contract deliverables" — i.e., this ticket is expected to *define* the adapter
boundary on paper, not find a pre-existing one. See Risks below — this materially affects how
honestly the Graphify `ProviderCapabilities` descriptor can be populated.

**`docs/parity_ledger/schema.json`** (cited versioned-schema precedent):
- Draft-07 (`"$schema": "http://json-schema.org/draft-07/schema#"`), a single self-contained file
  (`type: array` of `items`), `required: [id, text, status, priority]`, enum-typed `status`/
  `priority`, and three `allOf` conditional rules (verified/divergent → `v2_evidence`+`test_path`
  required; divergent → `divergence_note` required; `P0` → `test_path` required).
- **Important finding: this file itself has no `schema_version` field.** Grepping the file and the
  whole repo for `schema_version` turns up no such field inside `schema.json` or anywhere in
  `docs/parity_ledger/`. The ticket's Scope/Related Docs describe `docs/parity_ledger/schema.json`
  as "this repo's existing versioned-schema precedent," but the *structural* precedent (draft-07,
  self-contained, `allOf` conditionals, enum arrays) and the *explicit versioned-field* precedent
  are two different things, and only the former is actually present in this file. The real
  concrete precedent for an explicit versioned integer field in this repo is
  `tools/retrieval_events.py:46`: `retrieval_event_schema_version: int = 1` — "Version of this
  additive field family itself... starting at 1" (`docs/agent-monitoring/schema.md:276`), explicitly
  distinguished from an unrelated `retrieval_version` field on the same line's neighbor. This
  ticket's `schema_version` fields should follow that integer-starting-at-1, additive-versioning
  convention rather than inventing a new format.
- Runtime enforcement is **hand-rolled Python, not a `jsonschema` library validator**:
  `tools/parity_ledger_writer.py::validate_entry()` (`:64-85`) mirrors each `schema.json` rule in
  plain `if`/`raise` code and explicitly never loads the JSON file at runtime (per its own
  docstring). `tests/tools/test_parity_ledger_schema.py` is the test precedent: it does not use a
  schema-validation library either — it `json.loads()`s the raw file and asserts specific structural
  facts (`"if" not in items`, `len(items["allOf"]) == 3`). Confirmed repo-wide: no `jsonschema`
  package appears in `pyproject.toml`'s `[project.optional-dependencies]` or anywhere else grepped.
  **This is the pattern to mirror**: write the frozen `.schema.json` files as documentation-grade,
  hand-parsed-and-asserted-against JSON, not wired through a schema-validation library dependency
  this repo does not currently have.

**`docs/engine/contracts/context_packet_contract.md`** (packet-shape precedent):
- Pure prose contract — plain Markdown bullet lists describing `ContextRequest`/`ContextPacket`
  fields, no embedded JSON Schema file, no `.json` sibling. Explicitly states "No `src/` or
  `tools/` code implementing `ContextRequest`/`ContextPacket` construction... exists yet" — it is a
  contract for a *future* implementation, same posture this ticket's contract should take for
  Phase 1+.
- Confirmed via directory listing: **no `docs/engine/contracts/*.md` file today embeds or
  references an actual sibling `.json` schema file.** `docs/engine/` itself has two `.json` files
  (`manifest.json`, `_category_.json`) but neither is a JSON Schema — `manifest.json` is a
  certification-target manifest, `_category_.json` is a Docusaurus sidebar config. So there is no
  existing precedent, inside `docs/engine/contracts/`, of a prose contract `.md` file sitting next
  to real frozen `.schema.json` files. `docs/parity_ledger/` is the only place in the repo that
  actually pairs a machine-parseable schema file with governed data (the `*.yaml` ledger shards).

## Mechanics / Engine Constraints

This ticket is agent-orchestration/retrieval tooling, not simulation logic — no `docs/mechanics/`
chapter or `docs/engine/` runtime contract (kernel, pipeline, combat, economy) constrains it. The
only "engine constraint" in the CLAUDE.md sense that applies is the Authoritative Mechanics Rule's
parity-ledger clause, addressed under Parity Ledger Overlap below (none required, by the same
`support_boundary` posture context_packet_contract.md §4 already established for this doc family).

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp_contract.md`: new prose contract doc (mirrors
  `context_packet_contract.md`'s role/location) documenting the provider adapter invocation
  contract (timeout, cancellation-where-supported, version reporting, fixture-test requirement),
  the `ProviderCapabilities` descriptor semantics, and cross-referencing the new frozen
  `.schema.json` files this ticket adds — no such document exists yet and the ticket's scope
  requires this contract to be "written down."
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 0 checklist items ("Freeze versioned
  JSON Schemas for MCP requests...", "Define provider adapter invocation, timeout, version, and
  fixture contracts", "Define and test provider capability descriptors for Context Search and
  Graphify") should get a cross-reference to the new frozen contract doc/schema files once this
  ticket lands, so the proposal's own delivery-plan section reflects that these specific bullets
  are now satisfied rather than still-open.

If no `docs/parity_ledger/` entry is added (see Parity Ledger Overlap — none is warranted), this is
the complete "Docs Requiring Update" list. No `docs/mechanics/` chapter changes.

## Parity Ledger Overlap

None. This ticket governs agent-orchestration/retrieval tooling (MCP wire contracts, provider
adapter shape), the same category `docs/engine/contracts/context_packet_contract.md` §4 already
classifies as not requiring a `docs/parity_ledger/` entry — it cites the existing posture recorded
for agent-monitoring tooling under `docs/parity_ledger/infrastructure.yaml`'s INFRA-281 through
INFRA-292 entries (`support_boundary` field, confirmed present and used, currently `null`, on
every entry inspected in that file). No entry ID in any `docs/parity_ledger/*.yaml` shard
currently references `knowledge_context`, `knowledge_status`, `search_mcp`, or `hybrid_retrieval`
by text search. A future reader should not read this absence as a gap — it follows the same
documented precedent context_packet_contract.md already established for this doc family, not a new
judgment call invented here.

## Prior Work

- `TCK-20260728-CONTEXT-PACKET-SCHEMA` / `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` — produced
  `docs/engine/contracts/context_packet_contract.md` and `tools/context_packet_assembler.py`. This
  is the closest prior-art precedent for "freeze a field-shape contract before implementation
  exists," including its own explicit non-registry-backed-source (`unrated` sentinel) and
  cross-kind-ranking open-decision handling (§5–§9 of that doc) — several of the same
  authority/freshness/verification-shaped problems this ticket's `status`/`freshness`/
  `verification` three-dimension requirement will need to stay consistent with, so the frozen
  enums in this ticket should not silently duplicate or contradict `unrated`/`P0-P2`/
  `authoritative`-`archive` vocabulary already governed there.
- `TCK-20260612-LOCAL-CTX-MCP` (DONE) — built `tools/search_mcp.py` itself. Its Implementation
  Notes record two directly reusable facts: (1) `.mcp.json`, not `.claude/settings.json`, is the
  correct project-scoped MCP registration file (Claude Code's schema rejects `mcpServers` under
  `settings.json`); (2) the `mcp` Python package is an optional dependency
  (`pyproject.toml[search-mcp]`) and is not installed in this dev environment — `search_mcp.py`
  handles `ImportError` gracefully. Its test file, `tests/tools/test_search_mcp.py` (15 tests), is
  the established pattern for testing an MCP tool's shape/command/args/error-dict behavior without
  a live MCP client, and is the closest direct precedent (alongside
  `tests/tools/test_parity_ledger_schema.py`) for this ticket's own `tests/tools/` additions.
- `TCK-20260624-FIX-TOOLS-SERVER` — prior graceful-degradation fix for MCP/knowledge-search tooling
  server tests; relevant if this ticket's fixture tests need to assert adapter behavior when a
  provider is unavailable (§16 Failure and Fallback Semantics of the proposal).
- `tools/retrieval_events.py:46` — `retrieval_event_schema_version: int = 1`, the concrete
  in-repo precedent for how an additive schema-version field should be shaped (see Current
  Behavior above); `docs/agent-monitoring/schema.md:276-277` documents the convention in prose.

## Risks and Open Questions

1. **Frozen-schema physical location is not fully settled by precedent and needs a decision, not
   an assumption.** `docs/parity_ledger/schema.json`'s structural conventions (draft-07,
   self-contained, `allOf`, hand-rolled Python enforcement, JSON-parsing test) are a solid pattern
   to mirror, but its *directory* is scoped to the parity subsystem specifically (sibling to the
   `*.yaml` shards it governs) — there is no existing `docs/engine/contracts/*.json` precedent to
   directly copy for a *different* subsystem's schema files. Recommendation for the implementer:
   place the new `.schema.json` files under a new `docs/engine/contracts/knowledge_gateway_mcp/`
   subdirectory, with a sibling prose `knowledge_gateway_mcp_contract.md` in
   `docs/engine/contracts/` (parallel to `context_packet_contract.md`, which this ticket's own
   Related Docs already names as the packet-shape precedent) narrating the provider-adapter
   invocation contract and cross-referencing the schema files. This keeps `docs/parity_ledger/`
   scoped to the parity subsystem only, avoids inventing a brand-new `tools/mcp_gateway/schemas/`
   location with no doc-authority story, and is a real judgment call flagged here for confirmation
   rather than presented as an established precedent — no committed decision doc settles this
   today.
2. **Graphify has no Python-callable query interface today** — only a CLI binary. Populating a
   *tested*, *honest* `ProviderCapabilities` descriptor for Graphify (a hard acceptance criterion)
   forces a choice: (a) describe Graphify's *actual current* capabilities as a CLI-shelled
   provider (weaker cancellation/timeout guarantees, subprocess-based invocation, no in-process
   version reporting beyond whatever `graphify --version`-equivalent exists, if any — unverified
   here), which is honest but conflicts with the proposal's stated architectural preference for
   "local deterministic interfaces rather than one MCP server recursively calling another"; or (b)
   define the *target* in-process callable boundary as a documented interface this ticket
   specifies but does not implement (Phase 0 is contract-only — implementing it is explicitly Out
   of Scope). This ticket's Out of Scope line ("Implementing the gateway, routing, or any live MCP
   tool — Phase 0 is contract-only") supports reading (b): the adapter invocation contract and
   capability descriptor should describe the target interface Phase 1 must build, with the
   descriptor's fields set to reflect what a correctly-built in-process adapter would honestly
   support — but this is an interpretation, not a directly stated instruction, and should be
   confirmed rather than assumed if the distinction materially changes any specific
   `ProviderCapabilities` field value (e.g. `cancellation`, `timeout`) the acceptance criteria will
   check.
3. **`docs/plans/knowledge-gateway-mcp-proposal.md`'s "existing versioned-schema precedent" claim
   about `docs/parity_ledger/schema.json` is only partially accurate** (see Current Behavior) —
   that file has no `schema_version` field of its own. This does not block the ticket (the
   structural JSON-Schema conventions are still a valid pattern to mirror), but the frozen schemas'
   `schema_version` field should be modeled on `tools/retrieval_events.py`'s
   `retrieval_event_schema_version: int = 1` convention instead, not on anything literally present
   in `schema.json`.
4. **No sibling ticket (`KGMCP-EVIDENCE-CACHE-IDENTITY`, `KGMCP-REDACTION-RETENTION-POLICY`) has
   started yet** — both are still in `tickets/todos/knowledge-gateway-mcp/`, not
   `tickets/inprogress/`. Per the epic's own `SEQUENCE.md`, this ticket is intentionally
   foundational and first; no coordination gap exists today, but the frozen `status`/`freshness`/
   `verification`/`FACT`/`INFERENCE`/`DECISION` enums and evidence-kind vocabulary this ticket
   defines will be cited by `KGMCP-EVIDENCE-CACHE-IDENTITY`'s own evidence-dependency contract —
   any later rename of these enum values would ripple into that ticket.

## Anti-Drift Hazards

- **Do not implement any live routing, caching, or MCP tool code.** The ticket's Out of Scope line
  is explicit and the epic's `SEQUENCE.md` reiterates "Phase 0 ... work only." A schema/contract
  freeze must not grow into a `knowledge_context`/`knowledge_status` tool implementation, even a
  stub one, and must not touch `.mcp.json`.
- **Do not collapse `status`/`freshness`/`verification` into one field or score.** This is an
  explicit acceptance criterion and an explicit proposal invariant (§12, §13) — a schema or test
  that merges them (e.g. a single `confidence` enum) is a scope violation, not a simplification.
- **Do not silently redefine `authority`/`freshness` vocabulary already governed by
  `tools/validate_frontmatter.py` (`AUTHORITY_VALUES`, `STATUS_VALUES`) or
  `docs/parity_ledger/schema.json` (`status`, `priority`).** The new gateway-specific enums
  (`FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN` freshness; `VERIFIED`/`SUPPORTED`/`INFERRED`/
  `UNVERIFIED` verification; `FACT`/`INFERENCE`/`DECISION` classification) are a genuinely new,
  separate vocabulary per the proposal — they must not be aliased onto or confused with the
  existing `P0`-`P2`/`authoritative`-`archive` doc-frontmatter enums, nor with parity's own
  five-value `status` enum. `context_packet_contract.md` §3's "second, differently-shaped
  vocabulary" warning about `parity_ledger_entry` is the direct precedent for why this distinction
  matters.
- **Do not expose forbidden request fields.** The public `knowledge_context` request schema must
  not include provider weights, cache-level selection, semantic thresholds, provider forcing, or
  ranking-policy switches — this is both an explicit acceptance criterion and an explicit proposal
  invariant (§9.1). A schema author reusing internal routing-config shapes as a shortcut is the
  most likely way this gets violated.
- **Do not invent a `ProviderCapabilities` field value for Graphify that the current CLI-only
  interface cannot honestly support** (see Risk 2) — e.g. do not mark `cancellation: true` or
  `timeout: true` for Graphify unless the contract text is explicit that this describes the target
  in-process interface Phase 1 must build, not today's CLI reality.
- **Do not add a `jsonschema` pip dependency** to validate these files at runtime — the established
  repo pattern (`docs/parity_ledger/schema.json` + `tools/parity_ledger_writer.py::validate_entry`)
  is hand-rolled Python validation plus a test that parses the raw JSON structurally. Introducing a
  new validation-library dependency for this ticket alone would be inconsistent with that
  precedent and is not required by any acceptance criterion.
