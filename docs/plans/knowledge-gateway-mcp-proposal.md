---
status: active
layer: ai
authority: P1
audience: agent
tags: [mcp]
---

# Proposal: Local Knowledge Gateway MCP

**Status:** Proposed  
**Scope:** Agent infrastructure; investigation and architecture proposal only  
**Repository:** `rpg-based-simulation`  
**Date:** 2026-08-11

### Proposal Maturity

This document is a direction-setting architecture proposal. Approval authorizes Phase 0 contract,
policy, and measurement work only. It does not yet authorize production gateway wiring or cached
payload retention. Phases 1 and later require Phase 0's versioned contracts, security ruling, and
measured acceptance thresholds to be approved first.

**Status as of 2026-08-16:** Phases 0-5 all have real, implemented, tested, and measured child
tickets landed (see §20 for the full per-phase ledger and §21 for Phase 3's pilot acceptance
measurement, including its post-fix re-measurement). None of this implementation work self-declares
production-capable status — every phase's own text explicitly defers that determination to a
separate, later human-reviewer call, and that remains true here. The real, measured evidence
gathered so far is mixed-to-negative on this proposal's own core latency/token hypothesis (see §25's
"Status update" for the honest summary) — this status line exists so a reader does not mistake
"Phases 0-5 built" for "Phases 0-5 justified the investment." See
`docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md` for a full, consolidated audit of
what was built, what was honestly measured, and what remains open.

### Architectural Invariants

- The gateway is an optimization and coordination layer, never a source of project truth.
- The local database is disposable and rebuildable.
- A cached result is reusable only while its direct evidence and validated scope remain valid.
- Cache lookup identity and evidence-validity identity are separate contracts.
- Agents should pay token cost proportional to the novelty of the question, not repository size.
- The gateway is an ambient, phase-agnostic repository utility. Agents may use it whenever project
  knowledge helps, but no workflow phase is required to call it.
- Agents should use the cheapest reliable information source. A direct `rg` lookup or Graphify
  query remains preferable when it answers the question safely with less work.

## 1. Executive Summary

This proposal recommends building a small, read-first **Knowledge Gateway MCP** over the repository's existing context providers, with a new local SQLite cache that stores reusable, evidence-backed results.

The repository already has strong retrieval components:

- Context Search over documentation, tickets, investigations, and working history
- Graphify for source symbols and code relationships
- Parity Ledger for implementation and verification status
- registries and architecture tests for authority and invariants
- experimental context-packet, retrieval-cache, and retrieval-observability components

What the repository does not yet have is a single agent-facing interface that:

1. chooses the appropriate provider or provider combination,
2. returns a bounded and deduplicated context packet,
3. stores the actual reusable result locally,
4. verifies that cached evidence is still current,
5. handles branch and uncommitted-working-tree differences,
6. and exposes provenance, conflicts, and cache state consistently.

The proposed gateway should not replace Context Search, Graphify, Parity Ledger, source code, tests, tickets, or registries. Those systems retain authority. The gateway is an optimization and coordination layer that can always be deleted and rebuilt.

The initial MCP surface should remain deliberately small:

- `knowledge_context` — answer or assemble task-oriented context under a token budget
- `knowledge_status` — report provider and cache health

Existing provider-specific tools should remain available for direct inspection, debugging, and fallback.

The largest expected benefit is not merely avoiding repeated tool execution. It is avoiding repeated delivery of overlapping, verbose provider results to agents. Meaningful token savings come from cached, bounded, deduplicated packets; a cache that merely returns the same large excerpts would improve latency but would not materially reduce prompt tokens.

## 2. Project Context and Current Use Cases

This repository is a large RPG simulation codebase with extensive domain logic, architectural invariants, agent workflows, tickets, generated indexes, and historical documentation. AI agents routinely need to answer questions such as:

- What is `AuthoritativeState`, and who may mutate it?
- Which files and tests are related to a symbol or subsystem?
- Is a requirement fully implemented and verified?
- Why was a subsystem removed or replaced?
- Which architectural rules constrain a proposed change?
- What previous tickets or investigations cover this problem?
- What is different between a tick, generation, workflow phase, and simulation episode?
- Which work is blocked on a human decision?

The repository currently mandates a Context Search and Graphify scan before broad investigation in
its existing agent guidance. The gateway may simplify that behavior, but this proposal does not add
a new mandatory gateway call. Agents still have to:

- choose tools manually,
- reconcile overlapping results,
- decide which source is authoritative,
- repeat similar searches across tickets and sessions,
- spend tokens reading the same excerpts repeatedly,
- and independently determine whether prior findings are still fresh.

The Knowledge Gateway is intended for local AI-agent use in this repository. It is not designed as a remote service, a general-purpose organizational knowledge base, or a runtime simulation subsystem.

### 2.1 Ambient Utility Positioning

The gateway is a general repository utility in the same conceptual category as `rg`, git history,
Graphify, and Context Search. It is available during investigation, implementation, debugging,
documentation work, review, refactoring, ad-hoc exploration, and non-ticket sessions.

Ticket ID, workflow name, phase, changed paths, agent role, and run ID are optional ranking hints.
Their absence must never prevent a query or reduce the response to an error. Workflow integrations
may recommend or opportunistically call the gateway, but the gateway is not itself a workflow
phase, gate, Definition-of-Done item, or mandatory ticket step.

The tool should reduce the cost of curiosity, not increase the ceremony of investigation. Agents
remain free to bypass it when a cheaper reliable source is obvious:

- use `rg` for a simple exact text check,
- use Graphify directly for a focused code-reference or dependency question,
- use Context Search directly for a focused document lookup,
- and use the gateway when routing, cross-provider reconciliation, bounded context, or safe reuse
  would provide material value.

This positioning is a prospective policy change from the repository's current blanket Context
Search-plus-Graphify pre-scan rule. Phase 0 must propose the exact agent-guidance amendment and have
it reviewed through the repository's normal instruction-generation process. Until that amendment
is approved and generated, current repository instructions remain in force; merely implementing
the MCP does not silently override them.

## 3. Current State

### 3.1 Context Search MCP

`tools/search_mcp.py` currently exposes:

- `search_docs`
- `search_health`

It queries `knowledge-index/knowledge.db` using hybrid dense and BM25 retrieval. The index currently contains documentation, completed tickets, investigations, and working-log material. It returns paths, headings, relevance scores, and short excerpts.

This is the best current provider for:

- terminology and concepts,
- architecture documentation,
- historical reasoning,
- tickets and investigation artifacts,
- and discovery of likely source documents.

It is a retrieval index, not an authoritative source and not a durable cache of synthesized answers.

### 3.2 Graphify

Graphify provides symbol, dependency, reference, and path-oriented code navigation. Deterministic AST-derived relationships are particularly valuable for questions such as:

- Where is this symbol defined?
- Who calls or references it?
- What depends on this module?
- Which tests are connected to the affected source?

Graphify should remain the source/code-relationship provider. The Knowledge Gateway must not rebuild its graph.

Graphify output can also contain inferred relationships. The gateway must preserve relation provenance and confidence rather than treating all graph edges as equally authoritative.

### 3.3 Parity Ledger

`docs/parity_ledger/*.yaml` and the derived `parity-index/parity.db` specialize in questions about whether requirements and behaviors are implemented, tested, missing, divergent, unsupported, or legacy-verified.

The Parity Ledger remains authoritative for implementation-completeness questions. The gateway may cache and explain its results but must never replace or independently override ledger status.

### 3.4 Registries, Tests, Tickets, and Source

Other authoritative or high-value providers include:

- `docs/REGISTRY.yaml` for document authority and lifecycle metadata
- source code and deterministic code indexes for current implementation facts
- architecture tests for enforced invariants
- tickets for decisions, work status, and historical reasoning
- `tickets/working_log.csv` for completed-work history
- agent-orchestration contracts and generated agent instructions for workflow policy

These should be queried through adapters where useful, not copied into a competing truth store.

### 3.5 Existing Context-Packet Work

The context-efficient retrieval epic produced useful foundations:

- a provider-neutral `ContextPacket` shape,
- hybrid retrieval fusion,
- candidate metadata adapters,
- authority and freshness vocabulary,
- conflict annotations for selected active documents,
- retrieval telemetry,
- a fail-open shadow workflow hook,
- and a three-table SQLite retrieval-cache prototype.

This work should be reused, but its present capabilities must be described precisely:

- `ContextPacket` currently contains source-selection metadata and hashes, not answer text or reusable knowledge claims.
- `assemble_context_packet()` shapes candidates supplied by a caller; it does not perform routing, retrieval, cache lookup, or token-aware candidate selection.
- `retrieval_cache.db` stores cache keys, hashes, status, scores, and timing metadata. It does not store query-result payloads or complete packet payloads, so a cache hit cannot currently return reusable context.
- the live shadow hook uses an empty candidate set and remains advisory.

The existing work is therefore a strong substrate, not a completed Knowledge Gateway.

### 3.6 Existing Simulation Knowledge Workflow

`UpdateSimulationKnowledgeWorkflow` is a separate, domain-specific mechanism that writes approved simulation insights, known issues, rules, and decisions under `data/lab_knowledge`. It includes explicit approval, evidence fields, duplicate-ID checks, audit events, and a revert workflow.

This mechanism should be treated as a specialized provider or future integration point. It must not be silently merged with the agent context cache because:

- it may contain unique approved domain knowledge,
- it has different ownership and write semantics,
- it is not merely a disposable retrieval cache,
- and it requires separate review of committed-versus-local storage policy.

## 4. Problem Statement

The current tooling solves discovery but not coordinated reuse.

An agent asking one architectural question may call Context Search, Graphify, inspect the Parity Ledger, open multiple files, and manually reconcile the results. A later agent often repeats most of that work because no shared local layer stores the bounded result and its evidence dependencies.

The missing capability is:

> A local, evidence-aware query gateway that routes questions across existing providers and reuses prior results only while their cited evidence remains valid.

Without this layer:

- repeated questions incur repeated retrieval latency,
- provider selection remains agent-specific,
- overlapping excerpts increase prompt size,
- prior conclusions are difficult to reuse safely,
- conflicts are inconsistently surfaced,
- and stale results are either trusted too long or discarded too broadly.

## 5. Goals

The Knowledge Gateway should:

1. Give agents one natural-language entry point for repository knowledge.
2. Route deterministically where intent and entity metadata permit.
3. Combine Context Search, Graphify, and Parity results when necessary.
4. Return useful context within a caller-provided token budget.
5. Cache actual normalized results and assembled packets, not only cache metadata.
6. Preserve evidence and provider provenance for every returned statement.
7. Reject or refresh cached results when relevant evidence changes.
8. Account for repository, branch, HEAD, and working-tree state.
9. Represent unresolved conflicts without fabricating consensus.
10. Fail open to direct provider use when the gateway or cache is unavailable.
11. Measure whether it reduces latency, provider calls, and delivered tokens.

## 6. Non-Goals

The initial implementation should not:

- replace Context Search, Graphify, Parity Ledger, tickets, tests, or registries,
- create a remote or cloud knowledge service,
- require an external vector or graph database,
- become mandatory for repository correctness,
- cache secrets, tokens, credentials, or raw environment data,
- automatically promote AI conclusions into canonical project truth,
- provide unrestricted agent writes to durable knowledge,
- solve every semantic-equivalence problem in the first release,
- or introduce a large MCP surface with many overlapping tools.

## 7. Architectural Decision

### 7.1 Chosen Approach

Build a **modular gateway backed by provider adapters and a local SQLite cache**.

```text
Agent
  |
  v
Knowledge Gateway MCP
  |-- Query classifier and entity resolver
  |-- Cache coordinator
  |-- Provider router
  |-- Result normalizer and conflict detector
  `-- Token-budgeted packet assembler
        |
        |-- Context Search adapter
        |-- Graphify adapter
        |-- Parity Ledger adapter
        |-- Registry/ticket/source adapters
        `-- Future specialized providers

Local SQLite cache
  |-- provider results
  |-- assembled packets
  |-- evidence dependencies
  |-- provider generations
  `-- health and usage metrics
```

This is a facade and coordination layer, not a new search engine.

The MCP server should be a thin transport over a provider-neutral Python gateway library. The
initial adapters should use local deterministic interfaces rather than one MCP server recursively
calling another:

- Context Search adapter: call the existing Python hybrid-retrieval/search interface in-process.
- Graphify adapter: invoke a bounded local Graphify query adapter with timeout, structured output,
  and explicit stale/unavailable results.
- Parity adapter, when Phase 4 begins: call the existing parity-index Python/query interface.

Exact callable boundaries and structured Graphify output are Phase 0 contract deliverables. All
adapters must support timeout, cancellation where the underlying interface permits it, version
reporting, and deterministic fixture tests.

### 7.2 Alternatives Considered

| Option | Benefits | Costs and risks | Decision |
|---|---|---|---|
| Keep tools separate | No new code or abstraction | Repeated routing, repeated searches, inconsistent synthesis, no reusable packet cache | Reject as the long-term state |
| Add caching independently to every provider | Simple local changes | Duplicated cache policy, inconsistent freshness and observability, no cross-provider packet reuse | Reject |
| Build a new autonomous RAG/knowledge platform | Broad theoretical capability | Duplicates existing indexes, high operational and hallucination risk, difficult authority model | Reject |
| Thin MCP gateway plus shared local cache | Reuses current tools, one contract, incremental delivery, safe fallback | Requires careful invalidation and normalization | Choose |

### 7.3 Trade-offs Accepted

- The gateway introduces another abstraction and must be kept thinner than its providers.
- Initial semantic reuse will be conservative; some differently worded questions will still miss the cache.
- Fine-grained invalidation requires dependency metadata and more writes than a single global generation key.
- Results may take slightly longer on a cold miss because more than one provider can be consulted.
- Direct provider tools remain necessary for debugging and advanced queries.

## 8. Query Routing

Routing should use cheap deterministic signals before optional AI classification.

| Intent or query shape | Primary provider | Optional supporting providers |
|---|---|---|
| Definition, terminology, architecture explanation | Context Search | Registry, Graphify |
| Symbol definition, callers, references, dependency path | Graphify | Context Search |
| Requirement completeness or verification status | Parity Ledger | Source/tests, Context Search |
| Ticket contents or historical rationale | Context Search/ticket index | Working log, Registry |
| Tests affected by a code change | Graphify/code-test index | Architecture-test mapping |
| Current ticket/work status | Ticket index | Working log |
| Broad task context | Multiple providers | All relevant adapters |

Routing rules should recognize stable identifiers before classifying free text:

- ticket IDs,
- parity IDs,
- source paths,
- symbol names,
- registered document paths,
- and known subsystem IDs.

When the intent is ambiguous, the gateway may query a small provider set in parallel and merge the results. It should report which providers were used.

### 8.1 Provider Capability Contract

Every adapter must publish a versioned capability descriptor. The router and cache validator must
use declared capabilities rather than assume that all providers offer identical identity,
freshness, history, or execution guarantees.

```text
ProviderCapabilities
  provider_id
  adapter_version
  stable_entity_ids: NONE | PARTIAL | FULL
  evidence_granularities[]
  fine_grained_fingerprints: boolean
  incremental_refresh: boolean
  deterministic_relationships: NONE | PARTIAL | FULL
  historical_queries: boolean
  negative_knowledge_support: NONE | SCOPED | COMPLETE
  cancellation: boolean
  timeout: boolean
  branch_awareness: NONE | CALLER_SCOPED | PROVIDER_NATIVE
  generation_fingerprint: optional
```

Examples of routing consequences:

- A provider without fine-grained fingerprints cannot support a fine-grained cache hit by itself;
  its generation fingerprint becomes the fallback validity boundary.
- Inferred Graphify relationships cannot satisfy a deterministic-only request.
- A provider with no negative-knowledge support cannot establish absence from an empty result.
- A provider without branch awareness must receive branch/working-tree scoping from the gateway.
- A provider without cancellation must still be protected by the adapter's process-level timeout.

Phase 0 must populate and test this descriptor for Context Search and Graphify. Parity Ledger gains
one before its Phase 4 adapter is enabled.

## 9. MCP Tool Surface

### 9.1 `knowledge_context`

Purpose: answer a repository question or assemble task-oriented context under a budget.

Conceptual input:

```json
{
  "query": "change Redis stream retry semantics",
  "mode": "task_context",
  "budget_tokens": 1800,
  "changed_paths": ["src/observability/streams.py"],
  "include_history": false,
  "evidence_detail": "summary"
}
```

`query` is required. Other fields are optional hints. `mode` expresses the caller's desired output
shape (`answer` or `task_context`); internal normalized intent and provider routing are never
caller-supplied requirements.

Caller options express information needs, not routing internals. The public contract may accept a
budget, optional changed paths, desired evidence detail, and history relevance. It must not expose
provider weights, cache-level selection, semantic thresholds, provider forcing, or ranking-policy
switches. Ticket/workflow/run metadata, if later accepted, remains optional advisory context.

Conceptual response:

```json
{
  "mode": "task_context",
  "status": "OK",
  "freshness": "FRESH",
  "verification": "SUPPORTED",
  "cache": "HIT",
  "answer": "...",
  "statements": [
    {
      "statement_id": "statement-1",
      "text": "Observability must remain fail-open.",
      "classification": "FACT",
      "verification": "VERIFIED",
      "evidence_ids": ["evidence-1"]
    }
  ],
  "context": [
    {
      "kind": "invariant",
      "summary": "Observability must remain fail-open.",
      "source_id": "...",
      "path": "docs/...",
      "evidence_hash": "...",
      "authority": "P0"
    }
  ],
  "evidence": [
    {
      "evidence_id": "evidence-1",
      "source_id": "...",
      "path": "docs/...",
      "evidence_hash": "..."
    }
  ],
  "conflicts": [],
  "provenance_providers": ["context_search", "graphify"],
  "providers_consulted_this_call": [],
  "budget_requested": 1800,
  "budget_returned": 920,
  "cache_key_version": 1
}
```

`provenance_providers` always identifies the providers supporting the response. On a cold miss,
`providers_consulted_this_call` lists the providers queried. On a cache hit, the latter may be empty
while the former and the per-item evidence remain populated.

Top-level `status` describes request disposition (`OK`, `PARTIAL`, `CONFLICTED`, `UNVERIFIED`, or
`ERROR`). It is separate from `freshness`, evidence authority, and each statement's
`FACT`/`INFERENCE`/`DECISION` classification; these dimensions must not be collapsed into a single
confidence label.

`verification` describes the support level of the returned result (`VERIFIED`, `SUPPORTED`,
`INFERRED`, or `UNVERIFIED`). Every sentence in `answer` must be a rendering of one or more entries
in `statements`; each statement must point to evidence IDs. An answer with an unsupported sentence
is invalid and must not be cached.

`mode` is `answer` or `task_context`. In `answer` mode, the gateway returns the shortest supported
answer plus evidence. In `task_context` mode, it prioritizes actionable constraints, files, tests,
and history. The first release uses deterministic routing and extractive/template-based assembly;
model-generated synthesis and model-based intent classification are deferred until separately
approved. An unclassified request uses a bounded multi-provider fallback rather than an LLM.

### 9.2 `knowledge_status`

Purpose: expose operational health without returning cached content.

It should report:

- gateway and schema version,
- provider availability and generation,
- cache entry counts by result kind and freshness,
- fresh, stale, conflicted, and failed-validation counts,
- cache hit/miss/stale-rejection rates,
- lookup, evidence-validation, provider-fallback, packet-assembly, and end-to-end latency summaries,
- provider fallback rates,
- recent invalidation reasons,
- branch and working-tree scope,
- and whether the cache can be safely rebuilt.

It should not expose provider weights, semantic thresholds, internal cache-level controls, or
provider-selection switches. Detailed diagnostics belong in local logs or an operator CLI, not the
ordinary agent-facing MCP response.

### 9.3 Deferred Tools

Do not initially expose `knowledge_learn`, `knowledge_promote`, `knowledge_verify`, or arbitrary invalidation tools to agents. Add a separate evidence or dossier tool only if real usage shows that `knowledge_context` cannot remain coherent without it.

## 10. Cache Design

### 10.1 Storage

Evolve the existing gitignored retrieval-cache database:

```text
knowledge-index/retrieval_cache.db
```

Add versioned payload and dependency tables through migrations. Preserve the current marker-only
tables during migration until their callers and tests have moved. Do not create a second gateway
database unless Phase 0 demonstrates an incompatible lifecycle or locking requirement.

SQLite fits the repository because it provides:

- one-file local persistence,
- transactions,
- indexed lookup,
- JSON payload support,
- relationship joins,
- schema versioning,
- simple backup/deletion,
- and no external service dependency.

The database must be disposable. Unique project truth must remain in committed authoritative sources or an explicitly governed durable subsystem.

### 10.2 Cache Levels

#### Level 0: Provider/index metadata

Tracks provider generations and source fingerprints. Existing index manifests and Graphify metadata should be reused rather than duplicated.

#### Level 1: Provider-result cache

Stores normalized, bounded provider results, including the content required to return the result. A row should contain:

- keyed query hash, deterministic intent, resolved provider-native entity IDs, and filters,
- provider name and adapter version,
- result payload,
- source IDs and paths,
- evidence hashes,
- provider generation,
- repository/branch scope,
- timestamps and hit counters.

This differs materially from the existing `retrieval_query_cache_rows`, which stores only a key and metrics.

#### Level 2: Assembled context-packet cache

Stores the final bounded packet returned to an agent:

- answer or task summary,
- deduplicated context items,
- conflicts,
- complete evidence dependencies,
- routing plan,
- token budget and returned estimate,
- policy and schema versions,
- and scope/freshness metadata.

#### Level 3: Verified reusable knowledge

Deferred until Levels 1 and 2 demonstrate value and correctness. This level may later store canonicalized claims, aliases, explanations, and normalized Q&A. It requires stronger promotion and conflict rules than an ephemeral result cache.

### 10.3 Conceptual Cached Packet Schema

```text
CachedPacket
  packet_id
  normalized_intent
  query_key_hash
  entity_ids[]
  answer
  statements[]
  context_items[]
  evidence[]
  conflicts[]
  evidence_dependencies[]
  provenance_providers[]
  providers_consulted_this_call[]
  repository_id
  branch
  head_commit
  working_tree_fingerprint
  provider_generations{}
  policy_version
  schema_version
  budget_requested
  budget_returned
  status
  freshness
  verification
  lifecycle
  created_at
  last_validated_at
  hit_count
```

Raw user prompts and normalized free text are not persisted in the initial release. Store a keyed
query hash plus extracted safe entities, deterministic intent, and filters. The proposal recommends
permitting bounded answer/context payloads only from allowlisted repository source types after
redaction and secret scanning. Phase 0 must ratify this extension to the existing retrieval policy
before Phase 2 may begin.

## 11. Cache Identity and Equivalent Questions

### 11.1 Architectural Rule: Lookup Identity Is Not Validity Identity

These identities answer different questions and must never be represented by one overloaded key:

- **Cache lookup identity:** Which previously cached result might satisfy this request?
- **Evidence-validity identity:** Is that candidate result still safe to return now?

Lookup selects a candidate packet. It does not prove freshness. Every candidate hit must pass the
separate validity check before its payload is returned.

```text
lookup identity
  normalized intent
  + resolved provider-native entity IDs
  + safe filters
  + budget class
  + routing/policy version
  + repository/branch compatibility scope

validity identity
  direct evidence identities and fingerprints
  + validated search scopes for negative claims
  + adapter versions
  + relevant working-tree overlap
  + provider generation only where finer evidence is unavailable
```

A new question wording may resolve to an existing lookup identity, while a changed cited symbol
causes validity rejection. Conversely, an unrelated provider generation or repository change should
not force a miss when all direct evidence fingerprints remain valid and the provider contract says
that granularity is reliable.

### 11.2 Lookup Identity and Equivalent Questions

The first implementation should use deterministic identity wherever possible:

- `symbol:<qualified-name>`
- `ticket:<ticket-id>`
- `parity:<entry-id>`
- `doc:<registry-id>`
- `subsystem:<registered-name>`

Cache identity should combine:

```text
normalized intent
+ resolved entity IDs
+ filters
+ budget class
+ routing-policy version
+ repository/branch compatibility scope
```

Early phases use provider-native IDs (`doc_id`, qualified symbol, ticket ID, parity ID). Canonical
cross-provider entity IDs and alias consolidation remain Phase 5 work.

Raw-string hashing alone is insufficient because equivalent questions can have different wording. Embedding similarity alone is also insufficient because two superficially similar questions can require different authority or freshness rules.

Initial equivalence should therefore be conservative:

1. normalize whitespace and casing,
2. extract stable identifiers and known aliases,
3. classify intent,
4. reuse only when intent and resolved entities agree,
5. use semantic similarity later as a candidate generator, followed by deterministic compatibility checks.

## 12. Freshness and Invalidation

Freshness and verification should be separate dimensions:

- A result may be previously verified but now require revalidation because evidence changed.
- A fresh retrieval result may still be unverified or conflicted.

Recommended freshness states:

- `FRESH`
- `NEEDS_REVALIDATION`
- `STALE`
- `UNKNOWN`

Conflict is a request/result disposition, and verification is a separate support dimension; neither
is a freshness state. Lifecycle (`ACTIVE`, `HISTORICAL`, `DEPRECATED`) is also separate and is
populated only where the authoritative provider defines it.

### 12.1 Evidence Dependency Granularity

Phase 0 must define a closed, versioned set of evidence identity kinds. Each provider advertises the
finest identity and fingerprint it can produce reliably for each result.

| Evidence kind | Stable identity example | Preferred fingerprint |
|---|---|---|
| `DOCUMENT` | registry ID or repository-relative path | complete document content hash |
| `DOCUMENT_SECTION` | document ID plus stable heading/section ID | normalized section content hash |
| `FILE` | repository-relative path | file content hash |
| `SYMBOL` | provider-qualified symbol ID | deterministic symbol/AST fingerprint |
| `TICKET` | ticket ID | normalized ticket record/content hash |
| `PARITY_ENTRY` | parity entry ID | canonical entry hash plus schema/importer version |
| `REGISTRY_ENTRY` | registry path or stable entry ID | canonical registry-entry hash |
| `PROVIDER_GENERATION` | provider ID plus snapshot ID | provider-declared generation fingerprint |

`PROVIDER_GENERATION` is a fallback safety boundary, not the preferred dependency for every result.
For example, a symbol result should depend on a `SYMBOL` or `FILE` fingerprint when Graphify can
provide one; a document excerpt should depend on `DOCUMENT_SECTION` when the Context Search adapter
can produce a stable section identity. A provider that can only guarantee corpus-level freshness
must declare that limitation, and the gateway must accept the broader invalidation rather than
fabricate precision.

Evidence identities are provider-qualified to prevent accidental collisions. Phase 0 must define
normalization for headings, renamed paths, deleted records, duplicate symbol names, and provider
schema/version changes.

### 12.2 Evidence-Aware Invalidation

Each context item must retain its direct dependencies:

```text
source ID
path or resource identity
content/symbol/record hash
provider generation
relationship type
```

Invalidation should follow those dependencies:

```text
changed document
  -> invalidate cached items citing that document
  -> invalidate packets containing those items
  -> preserve unrelated packets

changed source file or symbol
  -> invalidate Graphify/code-derived items for that evidence
  -> invalidate dependent packets and Q&A
  -> preserve unrelated documentation answers

changed parity entry
  -> invalidate completeness answers for that entry
  -> preserve unrelated code-navigation results
```

`corpus_generation` remains a useful fallback safety signal, but it should not be the only invalidation mechanism because it rejects unrelated results after any corpus-wide rebuild.

Primary validation is lazy and occurs before serving a hit. The gateway rechecks direct evidence
fingerprints at read time, falling back to provider generation only where the provider capability
contract lacks reliable finer-grained evidence. Existing index-refresh and Graphify-update workflows
may additionally mark affected paths stale eagerly, but missed eager events cannot compromise
correctness because read-time validation remains mandatory.

Deletion and rename are represented as a missing old evidence identity plus a new path identity.
Working-tree inspection must include staged, unstaged, untracked, deleted, and renamed paths. The
gateway should snapshot the path set before hashing and retry or reject the hit if the working-tree
state changes during validation.

### 12.3 Branch and Working-Tree Awareness

Cache scope must include:

- repository identity,
- branch name or detached-HEAD marker,
- HEAD commit,
- and a fingerprint of relevant uncommitted changes.

HEAD is recorded for provenance, but a new commit is not automatically a cache miss. Compatibility
is determined by repository identity, branch policy, adapter/policy versions, and unchanged direct
evidence. This preserves reuse across unrelated commits while preventing branch contamination.

The gateway does not need to hash the entire working tree for every request. It can:

1. obtain changed paths,
2. intersect them with cached evidence paths,
3. compute hashes only for overlapping evidence,
4. reject or refresh affected entries.

Feature-branch packets must never silently become valid on the main branch.

## 13. Authority and Provenance

Authority remains provider-specific:

| Knowledge question | Authoritative provider |
|---|---|
| Current runtime/code fact | Source code and deterministic analysis |
| Enforced architectural invariant | Architecture tests plus authoritative docs |
| Requirement implementation status | Parity Ledger |
| Current ticket state | Ticket lifecycle files |
| Historical reasoning | Completed tickets and active/historical docs |
| Document policy | Registry-rated authoritative documentation |
| Derived explanation | Knowledge Gateway, with cited evidence |

The gateway must never collapse provider-specific meanings into one unexplained numeric confidence score.

Every derived statement should distinguish:

- `FACT` — directly supported by authoritative evidence
- `INFERENCE` — synthesized from evidence and explicitly labeled
- `DECISION` — a human-authored policy or choice

In early phases these are ephemeral labels on returned statements; they help agents interpret one
packet but do not create durable claim entities. Phase 6, if justified, separately defines stored
claim/fact/inference/decision records, lifecycle, aliases, and promotion governance.

Human decisions must remain recorded in tickets, docs, registries, or another governed durable system. Caching a decision does not make the cache its source of truth.

### 13.1 Negative Knowledge

Negative claims require both supporting evidence and a validated search scope. An empty provider
result is not evidence of absence.

```text
NegativeClaimSupport
  statement
  subject/entity IDs[]
  validated_scopes[]
  scope_evidence_dependencies[]
  providers_and_adapter_versions[]
  exclusions_or_blind_spots[]
  checked_at
  verification
```

For “Kafka is not currently used by runtime code,” a defensible scope may include:

- runtime source imports and symbol references,
- runtime initialization and adapter registration,
- dependency manifests and lock files,
- active runtime configuration,
- and authoritative current architecture documentation.

The claim is valid only for the recorded scope. A change to any file, symbol, manifest, registry,
configuration family, or provider generation that defines that scope invalidates the claim. If the
gateway cannot establish that the scope is complete enough for the requested wording, it returns
`UNVERIFIED` and states the unchecked scopes.

Providers declare negative-knowledge support through their capability contract. The gateway may
compose a scoped negative claim from several providers, but it must never upgrade `NONE` or partial
coverage into complete absence. General durable negative claims remain part of the later reusable
knowledge phase, not the early packet cache.

## 14. Conflict Handling

A conflict is not simply two retrieved documents on the same subject. It is two credible claims that cannot both describe the same scope and time as true.

The gateway response should represent:

```json
{
  "status": "CONFLICTED",
  "subject": "...",
  "claims": [
    {
      "value": "...",
      "source_id": "...",
      "authority": "...",
      "valid_from": "...",
      "valid_to": null
    }
  ],
  "automatic_resolution": null,
  "recommended_action": "human review"
}
```

Automatic resolution is safe only where repository policy provides an explicit precedence rule, such as:

- current source over stale descriptive documentation for current implementation facts,
- Parity Ledger over derived explanation for completeness status,
- a superseding ticket decision over an explicitly superseded older decision.

The gateway should not automatically resolve:

- two current human policy decisions,
- code and an authoritative requirement that disagree,
- branch-specific facts without a requested branch scope,
- or two sources whose authority relationship is undefined.

Before Phase 6, conflict detection is intentionally limited to contradictions already represented
structurally by providers, explicit supersession metadata, and incompatible current document
records. The gateway may return multiple sources without claiming they conflict when semantic
comparison would require model judgment. General claim-level semantic conflict detection belongs
with Phase 6's knowledge model.

Human resolution occurs in the authoritative provider, not by editing the cache. The reviewer
records the decision in the appropriate ticket, document, parity entry, test, or source change;
the provider is refreshed; and the gateway rejects or rebuilds packets citing the old evidence.
This prevents a conflict from being “resolved” only inside disposable local state.

## 15. Token-Budgeted Assembly

The gateway should optimize packet content in this order:

1. Hard invariants and current human decisions
2. Directly relevant facts, symbols, and parity status
3. Required tests and immediate dependencies
4. Relevant history and prior investigations
5. Optional background

Budgeting must measure the content actually returned, not estimate cost as a constant multiplied by the number of candidates.

Deduplication should occur before truncation. When multiple providers support the same fact, the packet should normally include one concise statement with multiple evidence references rather than repeat similar excerpts.

**Accounting scope (updated by `TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`):**
"the content actually returned" is measured per statement — each included statement's own text
plus its own matched `context[]`/`evidence[]` entries are costed together as one atomic unit
(`assemble_within_budget()`'s widened per-statement cost), since a statement and its supporting
context/evidence are architecturally inseparable in the current assembly pipeline (one is never
shipped without the other). `conflicts[]` is measured and truncated separately, against whatever
budget remains after statements/context/evidence, since it is not owned by any single statement.
This closes the previously-disclosed gap where `context[]`/`evidence[]`/`conflicts[]` were
structurally unbudgeted — but the accounting still does not include JSON structural overhead or
untouched response fields (`statement_id`, `classification`, `kind`, `EvidenceEntry.source_id`,
etc.), so it remains a real, honestly-disclosed underestimate of the true serialized response
size; see `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`'s
"Post-fix re-measurement" section for the real measured gap.

## 16. Failure and Fallback Semantics

The Knowledge Gateway is never a correctness dependency.

| Failure | Required behavior |
|---|---|
| Gateway process unavailable | Agent calls provider tools directly |
| Cache missing or corrupt | Recreate schema and perform cold provider query |
| One provider unavailable | Return partial result with explicit provider failure |
| Graphify stale | Use Context Search/Parity where applicable; flag code-graph result unavailable |
| Context Search stale | Use direct docs/tickets/source where appropriate |
| Cached evidence mismatch | Reject the cache hit and refresh |
| Token-budget assembly failure | Return a smaller evidence list or provider references, never fabricated content |

Failures should be observable but fail-open for agent work.

**Phase 1 test coverage (as of `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`):** the "Gateway process
unavailable," "One provider unavailable," and "Token-budget assembly failure" rows are each proven
by a dedicated, deterministic test against the real gateway in
`tests/tools/test_knowledge_gateway_failure_semantics.py` (13 tests total). The remaining 4 rows are
explicitly deferred, not silently untested — recorded in that same file's module docstring, each
with a one-line reason and file:line citation: "Graphify stale" and "Context Search stale" have no
Phase 1 implementation to test (`freshness` is a hardcoded `"UNKNOWN"` literal in
`tools/knowledge_gateway_packet_assembly.py`, never computed or compared against a baseline); "Cache
missing or corrupt" and "Cached evidence mismatch" remain Phase-2-only, since no cache exists yet.

## 17. Security and Privacy

The gateway should inherit the existing retrieval redaction policy and extend it for cached payloads.

Never cache:

- secrets or credentials,
- tokens,
- raw environment values,
- unredacted tool output containing sensitive values,
- arbitrary configuration-file contents,
- or unrestricted raw prompts.

Before writing a cached payload:

1. allowlist fields,
2. restrict eligible source paths and source types,
3. redact local usernames and machine-specific absolute paths where unnecessary,
4. scan content using existing secret-detection rules,
5. cap payload size,
6. and record the redaction-policy version.

Cache inspection and status tools must not expose cached sensitive content by default.

## 18. Observability and Cache Economics

The gateway is justified only if it measurably improves agent work.

Measure:

- exact and entity-aware cache hit rates,
- stale-hit rejection rate,
- cache lookup latency,
- evidence-validation latency,
- provider fallback latency,
- packet assembly latency,
- end-to-end warm-hit latency,
- provider calls avoided,
- cold versus warm latency,
- tokens returned to the agent,
- estimated raw provider tokens avoided,
- packet deduplication ratio,
- provider fallback and failure rates,
- conflict rate,
- invalidations by provider and reason,
- frequently queried entities,
- repeated misses,
- and cache size/GC activity.

Token savings should be measured as:

```text
tokens in raw provider results that would have been returned
- tokens in the final gateway packet
```

Cache hits alone must not be presented as token savings.

A reported hit must include lookup and validation cost separately. A hit that avoids provider work
but spends comparable time revalidating broad evidence may still improve consistency, yet it should
not be counted as a latency success. Evaluation must compare end-to-end warm-hit cost with the
equivalent cold provider path.

### 18.1 Repeated Knowledge Demand

Before Phase 6 receives substantial investment, telemetry must estimate how often agents ask
semantically repeated project questions. Because raw prompts are not retained, demand grouping
should use safe deterministic intent, provider-native entity IDs, normalized filters, and the keyed
query hash. Phase 5 may add privacy-reviewed semantic clustering as a candidate signal; it must not
store raw prompt text merely to improve this metric.

Report at least:

- exact repeated lookup identities,
- entity-and-intent-equivalent requests with different query hashes,
- repeated misses by entity and intent,
- queries that repeatedly require the same evidence set,
- and the share of demand served by Levels 1–2 without a durable claim/Q&A layer.

Repeated misses are also documentation and terminology telemetry. A frequently requested entity
that produces weak, conflicting, or expensive results should be surfaced as a documentation or
project-lexicon opportunity rather than automatically promoted into cached canonical knowledge.

Phase 6 should proceed only if this demand evidence shows meaningful residual repetition beyond
what provider-result and packet caching already serve.

Phase 0 must create a fixed representative-query corpus and record the direct-tool baseline for
each query: provider outputs, authoritative sources recalled, wall time, tool calls, and serialized
tokens. It must then set minimum latency, token-reduction, and no-regression recall thresholds
before gateway evaluation begins. This proposal deliberately does not invent numeric thresholds
before that baseline exists.

## 19. Garbage Collection and Schema Evolution

Knowledge retention and cache eviction are different concerns.

Safe cache-GC candidates include:

- expired exact-query results,
- packets for deleted branches,
- obsolete provider-version rows,
- low-use packets that can be regenerated,
- stale rows superseded by refreshed rows,
- and failed or incomplete writes.

Historical project facts must remain in authoritative sources even when their cache entries are evicted.

The SQLite store should include:

- `schema_version`,
- ordered migrations,
- provider adapter versions,
- routing-policy version,
- redaction-policy version,
- transaction-safe upgrades,
- a rebuild command,
- and a health check that detects unsupported or corrupt schemas.

Operational defaults should use restrictive file permissions, WAL mode where supported, bounded
transactions, busy timeouts, and one-writer-safe migrations. Packet construction should use a
per-key lease or equivalent transaction guard to prevent cache stampedes. Phase 0 must set maximum
database size, TTL/usage-based eviction rules, and crash-recovery tests before payload caching is
enabled.

If migration is unsafe, deleting and rebuilding the cache must remain a valid recovery path.

## 20. Incremental Delivery Plan

### Phase 0: Contract and Measurement Baseline

- Freeze versioned JSON Schemas for MCP requests, success/partial/error responses, statements,
  evidence, conflicts, and status/freshness/verification enums. **Done** (`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`) —
  frozen `schema_version: 1` JSON Schema files under `docs/engine/contracts/knowledge_gateway_mcp/`
  (`shared_enums.schema.json`, `knowledge_context_request.schema.json`,
  `knowledge_context_response.schema.json`, `knowledge_status_response.schema.json`); prose contract
  at `docs/engine/contracts/knowledge_gateway_mcp_contract.md`.
- Define provider adapter invocation, timeout, version, and fixture contracts. **Done**
  (`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`) — see
  `docs/engine/contracts/knowledge_gateway_mcp_contract.md` §1 (adapter invocation contract table,
  grounded in direct observation of `tools/search_mcp.py` and the installed `graphify` CLI binary).
- Define and test provider capability descriptors for Context Search and Graphify. **Done**
  (`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`) — `docs/engine/contracts/knowledge_gateway_mcp/
  provider_capabilities.schema.json` (shape) plus the two populated instances,
  `provider_capabilities_context_search.json` and `provider_capabilities_graphify.json`; tested by
  `tests/tools/test_knowledge_gateway_contract_schemas.py` (19 tests). See
  `knowledge_gateway_mcp_contract.md` §2–§4 for descriptor semantics and the Graphify
  CLI-vs-in-process-adapter design decision (D1).
- Define evidence identity kinds, provider-qualified normalization, and the finest supported
  dependency granularity per provider. **Done** (`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) —
  the closed 8-kind taxonomy, stable-identity forms, preferred fingerprints, and
  rename/delete/duplicate-name/schema-version-change normalization rules at
  `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`; per-provider
  finest-granularity advertisement via `provider_capabilities.schema.json`'s
  `evidence_granularities[]` field (frozen by the sibling `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`).
- Freeze separate cache-lookup and evidence-validity identity contracts. **Done**
  (`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) — see
  `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §1 (lookup
  identity), §2 (evidence-validity identity), §3 (non-collapse rule), §4 (`PROVIDER_GENERATION`
  fallback rule).
- Record current latency, tool-call counts, repeated-demand signals, and returned-token estimates
  for representative queries. **Done** (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`) — a fixed,
  versioned 7-entry representative-query corpus at
  `tools/agent-monitoring/kgmcp_baseline_corpus.py`, with a real recorded direct-tool baseline
  (latency, tool-call counts, sources recalled, serialized-token estimate) at
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, produced by
  `tools/agent-monitoring/kgmcp_baseline_runner.py`; see
  `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §1.
- Define separate measurement for lookup, evidence validation, provider fallback, packet assembly,
  and end-to-end latency. **Done** (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`) — see
  `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §2 (the 5
  measurement-point definitions, each citing `tools/retrieval_events.py`'s Wrapper functions where
  a live precedent exists) and §2.6 (the fixture-baseline-vs-future-gateway-latency
  non-conflation rule).
- Predeclare measurable promotion thresholds from that baseline. **Done**
  (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`) — see
  `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4 (minimum
  latency, minimum token-reduction, and no-regression-recall thresholds, each a formula over the
  recorded-baseline fixture's fields) and §5 (the §18.1 repeated-demand estimation design).
- Define repository, branch, and working-tree cache identity. **Done**
  (`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) — see
  `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5.
- Ratify the cached-payload redaction and retention policy. **Done (ratified 2026-08-15)**
  (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`, ratified by
  `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`) — see
  `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §11 (Ratification
  Status): §24 item 1 approved as drafted; no changes to the policy's rules. Phase 2 payload-caching
  implementation is still a separate, un-started future ticket.
- Define migrations that evolve the existing `retrieval_cache.db` rather than creating a parallel
  store. **Done** (`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) — design-only migration plan at
  `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (scoped
  `retrieval_cache_schema_version` constant, ordered `migration_00N_*` function list, same-file
  in-place evolution; zero edits to `tools/retrieval_cache.py`).
- Define a reproducible token-counting method, budget tolerance, SQLite operating limits, and
  cache-GC defaults. **Done (ratified 2026-08-15)**
  (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`, ratified by
  `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`) — see
  `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8 (token-counting
  method, `kgmcp_char_heuristic_v1`, §24 item 4 approved as drafted), §9 (SQLite operational
  limits), §10 (cache-GC defaults) — §9/§10 were documented defaults not gated on a formal §24 item,
  ratified alongside §8 for consistency. None of these defaults are implemented in
  `tools/retrieval_cache.py` yet — that remains a separate, un-started future ticket.
- Draft the generated-agent-instruction change replacing the blanket pre-scan mandate with the
  cheapest-reliable-source and ambient-utility rule; do not activate it before review.
  **Done (drafted; not activated)** (`TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`) — see
  `docs/ai/claude_md_prescan_mandate_relaxation_draft.md`: drafted replacement instruction text
  covering §2.1's ambient-utility/cheapest-reliable-source substance, cross-referencing all 3 live
  instruction surfaces (`CLAUDE.md`'s Context Scan section, `CLAUDE.md`'s Proactive Tool Use table,
  and `.claude/skills/implement-ticket/SKILL.md`'s Step 2 callout) without editing any of them.
  Activation is explicitly gated on `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s compliance
  fix being retro-confirmed by `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation
  section — pending as of this ticket; this ticket does not itself activate or unblock activation.

### Phase 1: Read-Only Gateway

- Implement deterministic routing over Context Search and Graphify. **Done**
  (`TCK-20260815-KGMCP-P1-QUERY-ROUTER`) — standalone `tools/knowledge_gateway_router.py`: six
  stable-identifier matchers, the §8 7-row intent/provider routing table, capability-aware routing
  constraints consulting the frozen `provider_capabilities_*.json` descriptors, and a
  sequential-bounded `{context_search, graphify}` ambiguous-intent fallback; tested by
  `tests/tools/test_knowledge_gateway_router.py` (31 tests). No MCP tool surface, packet assembly,
  or caching — those remain separate Phase 1 bullets/tickets below.
- Expose `knowledge_context` and `knowledge_status`. **Done**
  (`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`) — `tools/knowledge_gateway_mcp.py`: a real FastMCP
  server (`FastMCP("knowledge-gateway")`) registering exactly these two tools over
  `knowledge_gateway_router.py::route()` and `knowledge_gateway_packet_assembly.py`, request/
  response validated against the frozen §9.1/§9.2 JSON Schemas with a real
  `jsonschema.Draft7Validator`; tested by `tests/tools/test_knowledge_gateway_mcp.py` (12 tests).
- Register the gateway as an ambient general repository utility, with no ticket or workflow
  metadata required. **Done** (`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`) — one new
  `knowledge-gateway` entry added to `.mcp.json` under `mcpServers`, mirroring the existing
  `knowledge-search` entry's shape exactly; the pre-existing `knowledge-search` and `github`
  entries, and `tools/search_mcp.py` itself, are provably untouched (zero diff).
- Return uncached normalized results with provenance. **Done**
  (`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`) — `knowledge_context` is the first live call site that
  actually returns `PacketAssembly` output to a caller: `provenance_providers[]`, per-item
  `context[].path`/`context[].authority`, and `evidence[].path` are all populated from real
  provider content, and no caching exists in this response path (Phase 2 not yet built).
- Use deterministic classification and extractive/template packet assembly only. **Done**
  (`TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`) — `tools/knowledge_gateway_packet_assembly.py`:
  extractive statement/context/evidence construction rendering real provider content only (§9.1),
  the `FACT`/`INFERENCE`/`DECISION` per-statement classification (§13), `NegativeClaimSupport`
  handling that never treats an empty result alone as evidence of absence (§13.1), structural
  conflict representation (§14), and token-budgeted assembly with priority tiers and truncation
  (§15) using the first real `kgmcp_char_heuristic_v1` callable
  (`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8); tested by
  `tests/tools/test_knowledge_gateway_packet_assembly.py` (27 tests).
- Preserve direct provider tools and fail-open behavior. **Done**
  (`TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`) — `tests/tools/test_knowledge_gateway_failure_semantics.py`
  (13 tests) proves this against the real gateway rather than trusting the MCP-tool-surface ticket's
  own happy-path tests: subprocess-level smoke tests confirm `tools/search_mcp.py` and the `graphify`
  CLI remain independently callable, unmodified, when the gateway process is down; a static guard
  confirms `tools/search_mcp.py`'s own source never imports any `knowledge_gateway_*` module. The
  "one provider unavailable" §16 row also got a real code fix here, not just a test — a
  `provider_failures` list was already computed internally in `tools/knowledge_gateway_packet_assembly.py`
  and silently discarded before reaching the response; it is now carried onto `PacketAssembly` and
  always emitted (even as `[]`) in `knowledge_context`'s response (`tools/knowledge_gateway_mcp.py`),
  documented additively in
  `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`. A second,
  previously-uncaught `FileNotFoundError`/`TimeoutExpired` propagation path internal to
  `knowledge_gateway_router.py::route()` is now also caught at the `knowledge_gateway_mcp.py` call
  site, without editing the frozen router itself. See §16 below for per-row Phase 1 test-coverage
  status.

Phase 1 acceptance check against the Phase 0 measurement baseline (`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`,
the epic's own closing acceptance ticket): the real gateway was run against all 7 of Phase 0's
frozen corpus entries and measured against §4's three predeclared promotion thresholds. The
honest result is a full miss — §4.1 (latency), §4.2 (token reduction), and §4.3 (no-regression
recall) each FAIL in aggregate and for every one of the 7 entries, including an expected FAIL on
`Q2_symbol_lookup`/`Q5_test_impact` recall (routing-design behavior from the real
single-primary-provider `ROUTING_TABLE`, not a defect) and, for the other 5 entries, an
additional structural cause discovered during measurement (Phase 0's `doc_id` and Phase 1's
`source_path`-derived evidence identity diverge for documents nested more than one directory
level under `docs/`). Full per-threshold numbers, root-cause analysis, and the committed
comparison fixture are at
`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` and
`tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`. This is not characterized as
Phase 1 "succeeding" against its own predeclared bar — it did not — and no threshold was
redefined or narrowed to obscure the miss. Whether and how to proceed toward Phase 2 in light of
this result is a separate, later human-reviewer decision, out of this ticket's own scope.

### Phase 2: Real Provider-Result Cache

- Add SQLite schema and migrations. **Done**
  (`TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS`) — `tools/retrieval_cache.py`: added the
  `retrieval_cache_schema_version` constant, the `LEVEL1_CACHE_COLUMNS` allowlist, and a standalone
  `migration_001_add_level1_tables(conn)` function that creates the new
  `retrieval_provider_result_cache_rows` (§10.2's Level 1: Provider-result cache row shape) and
  `retrieval_cache_generation` metadata tables — additive-only, `CREATE TABLE IF NOT EXISTS` against
  the same `knowledge-index/retrieval_cache.db` file, never called from `_get_connection()`,
  `_init_schema()`, or any existing `check_*_cache()`/`write_*_cache()`/`prune()` hot path, and the 3
  existing marker-only tables left byte-unchanged; tested by 11 new tests in
  `tests/tools/test_retrieval_cache.py` (new `TestMigrations` class plus one `TestCrashRecovery`
  sibling test). Read/write wiring against the new table and the Level 2 migration remain separate,
  not-yet-started Phase 2 tickets.
- Store actual bounded normalized results. **Done**
  (`TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`) — new module `tools/knowledge_gateway_redaction.py`:
  `check_allowlist()` (§2 Context Search/Graphify-only allowlist), `redact_content()` plus a local
  `_hash_text()` (§3 home-path/absolute-path redaction before hashing, redacted-hash-only), the
  4-pattern `scan_for_secrets()` (§4 baseline, reject-outright on match, never redact-and-store),
  `check_size_cap()` (§5 8192-byte cap on the redacted payload, reject not truncate),
  `check_never_cache_categories()` (§7's 6 independent categories), the `WriteDecision` dataclass
  and `evaluate_write_candidate()` orchestrator stamping `redaction_policy_version` (§6, a 4th
  distinct version axis) on every ALLOW/REJECT decision, and the §9 SQLite operational-limits
  helpers `open_connection_with_limits()` / `check_db_size_within_limit()` /
  `execute_bounded_transaction()` / `acquire_write_guard()` / `release_write_guard()`, plus §10 GC-
  eligibility predicates (`gc_eligible_*`, `gc_eligibility_never_flags_protected_evidence()`) against
  a synthetic `CacheRowSnapshot`; tested by 49 new tests in
  `tests/tools/test_knowledge_gateway_redaction.py`. Pure, directly-testable functions only — no
  `INSERT`/`UPDATE` against `retrieval_provider_result_cache_rows`, and `tools/retrieval_cache.py`
  was not edited. Wiring these functions into the live gateway request path remains a separate,
  not-yet-started ticket (`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`).
- Validate direct evidence fingerprints before hits, falling back to provider generation only when
  the provider capability contract lacks reliable finer-grained evidence. **Done**
  (`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`) — new module `tools/knowledge_gateway_cache.py`
  implements lookup-identity computation (§1) and evidence-validity revalidation (§2/§3/§4) as
  genuinely separate, non-collapsed steps. §12.2's lazy, read-time fingerprint revalidation runs
  before serving a hit, falling back to `PROVIDER_GENERATION`-level validation only when the provider
  capability contract lacks finer-grained evidence (confirmed against both real
  `provider_capabilities_*.json` files, which today both declare `fine_grained_fingerprints: false` —
  a genuine, disclosed limitation, not a defect this ticket introduces). §12.3's branch/working-tree
  scope is enforced as a hard partition checked before any fingerprint comparison: a new commit alone
  never forces a cache miss when direct evidence is unchanged, and a cached result from one branch is
  never served on an unrelated branch. Wired into
  `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` via two new hook call-outs
  (cache-check immediately after routing, cache-write before response-schema validation); every cache
  write routes exclusively through `knowledge_gateway_redaction.evaluate_write_candidate()`, no
  bypass path anywhere. The SYMBOL/FILE-kind fingerprint-mismatch path is fixture-based (mirroring
  Phase 0's own precedent), not exercisable against real live provider output today, since both real
  providers currently only supply `PROVIDER_GENERATION`-level evidence — labeled honestly, not
  presented as tested end-to-end against real data. Tested by 18 new tests in
  `tests/tools/test_knowledge_gateway_cache.py` plus 9 new integration tests in
  `tests/tools/test_knowledge_gateway_mcp.py`.
- Add exact normalized-query reuse. **Done** (`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`) — an
  identical repeated `knowledge_context` call (same normalized intent/resolved entity IDs/filters/
  budget class) now produces a genuine cache hit on the second call, served without a provider
  round-trip, verified by a real test proving the second call never reaches
  `_run_search()`/`graphify query`
  (`test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit`). Cache writes on a genuine
  miss go through `tools/retrieval_cache.py`'s new `check_provider_result_cache()`/
  `write_provider_result_cache()` pair; a `PARTIAL`-status response is deliberately never cached
  (discovered as a real regression during Implement — see the ticket's own Implementation Notes).
  `knowledge_status` now also reports real cache entry counts and hit/miss/stale-rejection rates via
  the new `provider_result_cache_stats()`, previously omitted per Phase 1's own honest
  not-yet-available disclosure; `latency_summary_ms`/`provider_fallback_rate` remain honestly omitted
  since this ticket adds no latency instrumentation.

Phase 2 acceptance recomparison against Phase 0's promotion thresholds and Phase 1's own recorded
cold-path result (`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`, the "other half" of Phase 2's own
bargain): the real, now-cache-wired gateway was run twice per entry (cold, then warm) against the
same 7-entry frozen corpus, under the exact same request shape Phase 1 used (no `budget_tokens`
override — an explicit Architecture Review ruling, not a default). The honest result is 0/7
genuine cache hits: every one of the 7 entries' real, default-budget response payload (10.6–30.5 KB)
exceeds the deployed cache's `MAX_PAYLOAD_BYTES = 8192` write size cap, so every cache write was
rejected (`cache_write_rejection_reason: "oversized_payload"` on all 7 entries, independently
confirmed by both a provider-round-trip spy and a direct cache-table `hit_count` delta check — never
inferred from the response body alone). §4.1 (warm-path latency), §4.2 (token reduction, cold and
warm computed separately), and §4.3 (no-regression recall, recomputed with the now-fixed evidence-ID
normalization) each FAIL in aggregate and for every entry; the Q2/Q5 recall miss persists for the
same documented single-primary-provider routing reason, and the non-Q2/Q5 recall counts are
identical to Phase 1's own recorded counts (the doc_id fix was already fully reflected by Phase 1's
own measurement, so no further change was expected or found). Full per-threshold numbers and the
committed recomparison fixture are at
`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` and
`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`. This is not characterized as
Phase 2 "succeeding" against its own predeclared bar — the real cache, as deployed, cannot
demonstrate a genuine warm-hit path against this gateway's real, default-shaped response sizes.
Whether to widen the size cap, change the default response shape, or otherwise revisit the cache's
design is a separate, later human-reviewer decision, out of this ticket's own scope.

### Phase 3: Context-Packet Cache and Token Budgets

- Assemble deduplicated multi-provider packets.
- Store and return actual packet payloads. **Done** (`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`) —
  a real Level 2 (assembled-packet) cache lookup and write path is now genuinely wired into the live
  `_run_knowledge_context()` call path, checked before Level 1: an identical repeated
  `knowledge_context` call (same normalized intent/resolved entity IDs/`repository_id`/branch/
  `budget_tokens`) now returns the cached, already-assembled, already-redacted packet payload without
  ever reaching `assemble_packet()` or Level 1's own lookup
  (`test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit`). A Level 2 miss
  falls through unmodified to Level 1's existing lookup, then to live providers
  (`test_level2_miss_falls_through_to_unmodified_level1_lookup`). A Level 2 hit is rejected and
  refreshed when dependency-invalidation logic determines staleness
  (`test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`,
  `test_level2_hit_rejected_on_provider_generation_bump_real_call`), and branch/working-tree scope is
  enforced before a hit is served (`test_level2_cached_result_from_feature_branch_not_served_on_different_branch`).
  Level 2 writes are independently verified — not assumed — to route through the same
  `evaluate_write_candidate()` redaction/secret-scan/size-cap enforcement Level 1 already uses, with
  no bypass path (`test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert`,
  `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`). `knowledge_status`
  now reports real Level 2 cache-domain fields distinct from Level 1's. This closes the one gap this
  bullet's own core capability required — a live store-and-return path — that did not exist anywhere
  before this ticket, unlike the sibling bullets above/below, which this ticket's own predecessor
  tickets hardened rather than originated.
- Enforce caller budgets using measured output size.
- Add packet dependency records and targeted invalidation. **Done**
  (`TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION`, wired live by
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`, independently re-verified at real-corpus/
  live scale by `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`) — the dependency-invalidation
  ticket built the real mechanism (`PacketAssembly.evidence_dependencies` aggregated from
  `final_context`, plus `revalidate_context_packet_row()`/`_level2_repo_branch_scope()` in
  `tools/knowledge_gateway_cache.py`, reusing §5's `is_branch_compatible()`/
  `working_tree_overlap_forces_revalidation()` primitives unmodified) as additive, pure, tested
  logic with no live call path yet. The read-write-wiring ticket made it genuinely reachable: Level
  2 lookups in `_run_knowledge_context()` now call `perform_context_packet_cache_lookup()`, which
  revalidates against this dependency/branch logic before ever serving a hit. The pilot-acceptance
  ticket then independently re-verified the wired mechanism against real, live gateway calls (not
  synthetic row dicts) for `Q1_authoritative_state`: stale rejection on a real changed cited path
  (`cache_status: "MISS"`, `genuinely_refreshed: true`), unrelated-change non-invalidation on a
  follow-up real call (`cache_status: "HIT_L2"`, `genuine_hit_preserved: true`), and
  uncommitted-change invalidation (sharing the stale-rejection evidence, since `changed_paths` is
  the gateway's only representation of uncommitted changes) all **PASS** —
  `test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip` and
  `test_uncommitted_change_invalidation_shares_stale_rejection_evidence_not_double_counted` in
  `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`. Branch partition also **PASS**,
  via a disclosed, targeted technique (`test_branch_partition_live_direct_call_against_a_real_current_row`):
  a direct call to the real `revalidate_context_packet_row()` against a real, just-written row with
  a synthetic incompatible branch argument — not a full round trip through an actual second git
  branch, since the frozen 7-entry corpus cannot organically produce one; disclosed as such in both
  the committed fixture's `technique_disclosure` field and
  `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`'s AC6
  section. See §21 below for the two Phase 3 pilot acceptance criteria (budget tolerance, conflict
  visibility) this same measurement ticket found did NOT pass or could not be exercised — targeted
  invalidation's own criteria are the ones that did.

Completion of Phase 3 is the first production-capable pilot boundary. Its provider set is Context
Search plus Graphify; Parity Ledger is not required until Phase 4. Production-capable here means an
opt-in advisory tool with approved payload policy and acceptance tests, not mandatory workflow use.

`TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` performed the first real measurement of this
boundary's §21 Pilot Acceptance Criteria against the live Level 2 cache path — a real, mixed
result (5/8 newly-measurable criteria PASS, 1 FAIL, 1 disclosed coverage limitation, 1 PARTIAL on
the closing criterion; see §21 and
`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` for full
detail). This measurement does not itself declare Phase 3 production-capable or close this pilot
boundary — that determination is a separate, later human-reviewer call based on these real numbers.

### Phase 4: Parity and Workflow Integration

- Add Parity Ledger routing. **Done** (`TCK-20260816-KGMCP-P4-PARITY-ADAPTER`) — a real, versioned
  `ProviderCapabilities` descriptor
  (`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_parity_ledger.json`) and a
  real, in-process adapter (`tools/knowledge_gateway_router.py::_run_parity_provider()`) now exist,
  calling `tools/parity_index.py::entry()` only — never `impact()`/`health()`, never a subprocess or
  recursive MCP call, per §7.1's own design decision. `ROUTING_TABLE["requirement_completeness_verification"]`
  no longer carries the Phase 1 `not_yet_routed="parity_ledger"` placeholder; it now routes to
  `primary_providers=("context_search", "parity_ledger")`. This is genuinely, end-to-end wired, not
  just a router-level unit test in isolation: the real per-call dispatch layer,
  `tools/knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()`, gained a
  `parity_ledger` branch, so a live `_run_knowledge_context()` call for a parity-ID-shaped query (or
  the free-text `Q3_requirement_completeness` shape) reaches `entry()` and returns real ledger data
  in the response's `statements`/`context`/`evidence` — confirmed by
  `test_parity_id_query_reaches_real_entry_lookup_end_to_end` and
  `test_gateway_call_never_crashes_when_parity_index_absent` (both real calls, no
  `tools.parity_index` internals mocked). `negative_knowledge_support` is declared `SCOPED`, earned
  by the adapter calling `check_staleness()` whenever `entry()` returns `found: False`. A
  missing/stale `parity-index/parity.db` fails open via a named `IndexNotBuiltError` catch at the
  dispatch layer, never crashing the gateway call
  (`test_missing_parity_index_fails_open_not_crash`,
  `test_stale_parity_index_is_disclosed_not_silently_trusted`). `context_search` stays a co-primary
  provider on the same row (a deliberate choice, not a stopgap — the free-text case still needs it).
  Two limitations are disclosed, not silently left implicit: (1) `assemble_packet()`'s own
  zero-statements negative-claim auto-trigger never threads `validated_scopes` through, so the
  `SCOPED` declaration does not yet flip any real response's `verification` field end-to-end — a
  distinct, separately-scoped threading change, deferred to a follow-up ticket; (2) the cached-payload
  redaction eligible-source allowlist (`tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES`)
  and the Level 1/Level 2 cache-write `source_type` derivation in `tools/knowledge_gateway_cache.py`
  were not updated to recognize `parity_ledger` as a distinct source type, so a cached packet
  containing real parity-sourced content is currently mislabeled as Context-Search-sourced rather
  than explicitly allowlisted — see
  `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §2 for the full
  disclosure. See
  `docs/engine/contracts/knowledge_gateway_mcp_contract.md` §3's new "Parity Ledger" subsection for
  the full per-field capability evidence.
- Add changed-path-aware task context. **Done** (`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`) —
  `changed_paths` is a real, optional `knowledge_context` field
  (`tools/knowledge_gateway_mcp.py:153`), already wired into cache-validity revalidation
  (integration point (a), built incidentally by the Phase 2/3 cache-wiring tickets) via
  `working_tree_overlap_forces_revalidation()` (`tools/knowledge_gateway_cache.py:206-211`) at both
  Level 1 and Level 2, proven end-to-end by
  `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`. Routing-integration
  (point (b), preferring the Parity adapter's `impact(changed_path=...)` over `entry()`) was
  evaluated and explicitly declined — one-line reason: it would be a change to the adapter's own
  routing decision (out of this ticket's scope) with a real singular/plural shape mismatch
  (`impact(changed_path=...)` vs. the gateway's plural `changed_paths`) and no demonstrated need,
  and a sibling-committed guard test
  (`test_changed_path_impact_call_is_not_wired_by_this_ticket`) already locks the non-wiring in
  place. See `INFRA-352` for the full reasoning.
- Evaluate optional workflow recommendations or opportunistic calls without creating a mandatory
  phase, gate, or ticket step. **Done** (`TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`) —
  real, evidence-based evaluation performed across every candidate integration point in
  `.claude/workflows/*.js` and `.claude/agents/*.md`. Result: recommend against integration at 3 of
  4 candidate points (Scope/Investigate `search_docs`+`graphify` sequence; Architecture Review's
  `docs/REGISTRY.yaml` filter), measured universally 1.05x-3.0x heavier in tokens and slower in
  latency for 4 of 7 corpus entries (1.35x-2.85x; the other 3 entries measured faster on latency
  alone) than the existing baseline; insufficient evidence at 1 (Document-Update/doc-updater — capability mismatch,
  not a measured regression); the dormant `SHADOW_CONTEXT_PACKET_ENABLED` hook flagged as a future-
  only candidate conditioned on Phase 3's own disclosed budget-enforcement and token-count gaps
  closing first. No code, workflow, or skill file changed by this ticket. See
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md` for the full
  breakdown.
- Compare gateway packets against existing direct-tool behavior. **Done**
  (`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`) — a real, paired, fresh (no Phase 1-3 fixture
  reuse) run of all 7 frozen corpus entries against both the real gateway call and the real
  equivalent direct-tool call(s) (Context Search, Graphify, and — newly callable for
  `Q3_requirement_completeness` since `INFRA-351` landed — the Parity Ledger `entry()` adapter
  directly). Real, honest, negative result on cost: **the gateway was slower (1.31x-3.76x) and
  heavier in tokens (1.04x-2.93x) than direct tool use for all 7 of 7 entries** in this fresh,
  cold-cache run — no entry excluded, no threshold redefined to flip an unfavorable result. On
  objective quality (source-completeness), the Graphify half matched exactly (0 missing, 0 extra)
  on all 4 Graphify-routed entries; the Context-Search half showed real, narrow drops on 3 of 7
  entries after hand-inspection ruled out 2 recorded misses as normalization-shape false positives,
  not real content loss. Hand-written reviewer judgments (disclosed, non-computed, each citing a
  real recorded source_id/path per entry): 6 of 7 entries (`Q1`, `Q2`, `Q4`, `Q5`, `Q6`, `Q7`)
  judged `direct_equal_or_better`; 1 of 7 (`Q3_requirement_completeness`, the newly-live Parity
  Ledger route) judged `mixed`; 0 of 7 judged `gateway_equal_or_better`. This does not characterize
  the gateway as broadly superior or inferior to direct tool use, nor does it declare Phase 4
  complete — per this ticket's own Out of Scope, that determination is a separate, later,
  human-reviewer call. See
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` for full per-entry
  detail.

### Phase 5: Entity-Aware Reuse

- Add canonical entity IDs and aliases.
- Reuse results across compatible phrasings.
- Add conservative semantic candidate matching with deterministic validation.

`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` performed the first real measurement of
repeated/semantically-equivalent question demand for this phase, against this repository's own
real historical usage (not the frozen 7-entry corpus, which is deliberately built unique-per-entry
and cannot demonstrate repeated demand by design). Primary source
(`agent-monitoring/events.jsonl` Investigate-phase summaries, 521 distinct tickets): 17
conservative repeated-demand pairs. Secondary/corroborating source (`tickets/working_log.csv`,
1,411 tickets): 372 conservative repeated-demand pairs. See
`docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` for full
per-source detail, method, and figures. The finding is a small, real, but mostly-non-literal
signal — most matched pairs are natural incremental/sequential investigation of an evolving
codebase, not the same question asked twice with different wording. Cross-referenced against
Phase 3's own real budget-tolerance FAIL and genuine-cache-hit token-count regression, and Phase
4's own real 7/7 negative gateway-vs-direct-tool comparison, the honest recommendation is: proceed
with Phase 5's remaining two bullets (canonical entity IDs/aliases; conservative semantic
candidate matching) only after Phase 3's own disclosed gaps close — not now, not never. This
paragraph does not itself declare any Phase 5 bullet built, and does not authorize or block a
future child ticket; that determination is a separate, later human-reviewer call based on these
real numbers.

### Phase 6: Verified Knowledge, Only If Justified

- Require repeated-demand evidence showing meaningful residual value beyond Levels 1–2.
- Define claim, fact, inference, decision, and evidence records.
- Add session/candidate/verified lifecycle rules.
- Integrate specialized approved knowledge such as lab knowledge without changing its authority.
- Add human-gated promotion for durable reusable claims.

## 21. Phase 3 Pilot Acceptance Criteria

The first production-capable gateway should satisfy all of the following:

- Context Search and Graphify remain independently callable.
- A gateway failure never blocks repository investigation.
- `knowledge_context` reports every provider supporting the response, every provider queried during
  the current call, and every evidence source returned.
- A warm hit returns a stored result payload without rerunning the provider.
- A cache lookup match never bypasses the separate evidence-validity check.
- Context Search and Graphify publish tested capability descriptors, and routing does not claim a
  capability they do not advertise.
- A changed cited source causes a stale rejection.
- An unrelated changed source does not invalidate the cached packet.
- Direct evidence identities are used at the finest granularity each provider reliably supports;
  provider generation is the fallback rather than the default dependency.
- Branch-local results are not reused across incompatible branches.
- Relevant uncommitted changes invalidate affected cached evidence.
- Returned content respects the requested budget within a documented tolerance.
- Conflicts are visible and never silently merged.
- Negative claims are returned as verified only when their validated search scopes and scope
  dependencies are recorded; an empty result alone remains `UNVERIFIED`.
- Pre-Phase-6 conflict reporting stays within the explicitly structured conflict boundary defined
  in §14.
- No prohibited sensitive content is written to the cache.
- The database can be deleted and rebuilt without losing project truth.
- Evaluation reports lookup, validation, fallback, assembly, and end-to-end latency separately and
  demonstrates lower median end-to-end latency and fewer delivered tokens for repeated
  representative queries without reducing authoritative-source recall.

**Phase 3 Pilot Acceptance measurement (first real pass against the live Level 2 cache):**
`TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` ran the frozen 7-entry corpus against the
real, live Level 2 packet-cache path for the first time and honestly measured the 8 criteria above
that depend on Level 2 behavior (warm hit/no re-run, stale rejection, unrelated-change
non-invalidation, branch partition, uncommitted-change invalidation, budget tolerance, conflict
visibility, and the closing latency/token/recall criterion). Real, mixed result: 5/8 PASS (warm hit
no-rerun, stale rejection, unrelated-change non-invalidation, branch partition, uncommitted-change
invalidation); 1 FAIL (budget tolerance — only 2/7 corpus entries stayed within the documented
±20% tolerance, since `context[]`/`evidence[]`/`conflicts[]` are structurally unbudgeted by
`assemble_within_budget()`); 1 disclosed coverage limitation, not a pass/fail (conflict visibility
— 0/7 real cross-provider conflicts observed across the corpus, a genuine gap in this corpus's own
design, not evidence the mechanism itself is broken); 1 PARTIAL on the closing criterion (median
end-to-end latency genuinely improved against both the Phase 1 cold baseline and a
freshly-measured Level 1 warm baseline, but delivered-token count did not improve against either
baseline, so `pass: false` is reported honestly; recall stayed regression-free at 0/7). Full
per-criterion detail, real numbers, and disclosed limitations are in
`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`. No criterion
above is marked satisfied by this note — the real, mixed result stands as measured.

**Update (`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`):** the budget-tolerance
FAIL was addressed by widening `assemble_within_budget()`'s per-statement cost to include each
statement's own matched `context[]`/`evidence[]` content, plus a new, separate
`truncate_conflicts_within_budget()` pass for `conflicts[]`. The real, honest re-measured pass rate
is still **2/7**, unchanged — every previously-failing entry's real payload genuinely shrank
(11%-22%), but not enough to cross the ±20% tolerance threshold, because the widened accounting
still does not count JSON structural overhead or untouched response fields (`statement_id`,
`classification`, `kind`, `EvidenceEntry.source_id`, etc.) that the real `json.dumps(response)`
measurement counts. See `phase3_pilot_acceptance_measurement.md`'s own "Post-fix re-measurement"
section for full per-entry numbers. The multi-provider dedup real-corpus-proof gap (§21's own
conflict-visibility-adjacent coverage question) was independently re-confirmed still open — 0/7
real cross-provider content duplicates in the live corpus — locked in by a regression test rather
than closed via a fabricated corpus extension.

**Further update (`TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING`):** closed the accounting
gap the prior update disclosed. `statement_response_fragment()`/`context_response_fragment()`/
`evidence_response_fragment()`/`conflict_response_fragment()` (new,
`tools/knowledge_gateway_packet_assembly.py`) are now the single source of truth for what each
item serializes to, called by both the real cost functions and `tools/knowledge_gateway_mcp.py`'s
actual response builder (refactored from inlining the same dict shape a second time) — cost is now
`kgmcp_char_heuristic_v1(json.dumps(fragment, sort_keys=True))` per item, capturing every
serialized field (`statement_id`, `classification`, `verification`, `ContextEntry.kind`/
`source_id`/`path`/`evidence_hash`/`authority`, `EvidenceEntry.source_id`) plus that item's own
real JSON structural overhead, not a hand-picked subset. Verified via 49+92 passing tests,
including a new test proving the response and the budget accounting can no longer silently drift
apart (both now read from the same functions) and a new test proving a previously-invisible field
(`Statement.verification`) now correctly affects cost and inclusion.

**Real re-measurement: PASS, 7/7** (up from 2/7) — cache tables cleared, corpus re-run twice at
`budget_tokens=1000`, confirmed `cache: MISS` (genuine cold compute) both times with identical
results. Every previously-failing `context_search`-routed entry dropped from the post-INFRA-356
range of 2200-2450 tokens to 1038-1171, comfortably under the 1200 threshold. Full per-entry table
in `phase3_pilot_acceptance_measurement.md`'s own "Further accounting closure" section. (An earlier
draft of this update wrongly reported this as blocked by a missing knowledge-search stack — that
check used the wrong Python interpreter; corrected here.)

## 22. Representative Use Cases

### “What is `AuthoritativeState`, and who may mutate it?”

Route to Context Search for the architectural explanation and Graphify/source analysis for current definitions and mutation paths. Cache a concise explanation linked to document and symbol hashes. Invalidate it when relevant state/pipeline files or cited architecture documents change.

### “Is feature X fully implemented?”

Route first to the Parity Ledger. Use Context Search only to explain related tickets or requirements. The packet must preserve Parity Ledger status as authoritative.

### “Why was `WorldTemplateExpander` removed?”

Route to ticket and historical-document search. Historical results may remain valid even though the symbol is absent, provided their scope is clearly historical.

### “What tests must run if `pipeline.py` changes?”

Use Graphify/code-test relationships plus architecture-test mappings. Cache by path and symbol identity. Invalidate when the file, related graph generation, or test-mapping policy changes.

### “Is Kafka currently used?”

This is a negative-knowledge query. A missing search result is not sufficient evidence. The gateway must either perform a defined absence check over dependency manifests, source imports, runtime configuration, and active docs, or return `UNVERIFIED`. Any cached negative fact must record the searched scopes and invalidate when those scopes change.

## 23. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Stale cache misleads agents | Evidence hashes, provider generations, branch/working-tree scope, stale rejection |
| Gateway becomes a new source of truth | Provider-specific authority, mandatory provenance, disposable database |
| Cache saves time but not tokens | Deduplicated bounded packets and explicit token measurements |
| Semantic reuse returns a related but wrong answer | Deterministic entity/intent compatibility checks before reuse |
| Provider conflicts are hidden | Structured `CONFLICTED` responses containing all credible claims |
| Cache invalidation becomes repository-wide | Direct dependency records with generation keys only as fallback |
| Sensitive source content is persisted | Content allowlist, secret scan, redaction version, restricted paths |
| MCP surface becomes confusing | Begin with two read tools; add tools only from demonstrated use cases |
| Existing retrieval epic is duplicated | Reuse its fusion, contracts, telemetry, and tests; replace only marker-only cache limitations |
| Durable lab knowledge is accidentally treated as disposable | Keep separate ownership and write policy; integrate through a read adapter only |

## 24. Open Decisions Requiring Explicit Review

Before implementation, reviewers should decide:

1. **Ratified 2026-08-15** (`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`) — approved as drafted:
   cache bounded, redacted answer/context payloads from allowlisted source types, per
   `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`.
2. Select the canonical repository and branch identity format.
3. Select the Graphify relation types eligible for deterministic answers.
4. **Ratified 2026-08-15** (`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`) — approved as drafted:
   the `kgmcp_char_heuristic_v1` packet token-counting method (±20% tolerance), per
   `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8.
5. Classify the specialized `data/lab_knowledge` store and decide whether it is eligible for a
   future read adapter.
6. Select the authoritative committed location for any future human-approved reusable knowledge.

## 25. Recommendation

Proceed with a focused Knowledge Gateway MCP initiative, but do not frame it as replacing or merely renaming the existing context-efficient retrieval epic.

The existing epic should supply reusable building blocks:

- hybrid retrieval,
- source metadata normalization,
- packet identity concepts,
- cache correctness tests,
- retrieval event schemas,
- and fail-open workflow integration patterns.

The new work should specifically deliver what is still missing:

- provider routing,
- actual cached result and packet payloads,
- evidence-aware fine-grained invalidation,
- branch and working-tree safety,
- bounded multi-provider synthesis,
- and a coherent MCP response contract.

This approach can be implemented incrementally and preserves existing authority boundaries. It has
the potential to reduce latency and delivered tokens, but the size of that benefit remains a Phase
0 measurement question. Promotion beyond an advisory read-only gateway should depend on measured
results, not on cache-hit counts alone.

**Status update (2026-08-16, real measured results from Phases 3-5):** the "size of that benefit"
question this recommendation deferred to measurement has now been measured, and the honest answer
is mixed-to-negative, not the hoped-for clean win:

- Phase 3's own pilot acceptance measurement found budget-tolerance FAILing (2/7 corpus entries
  within tolerance) even after a real, dedicated fix widened the cost-accounting formula
  (`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`) — payloads shrank 11%-22% per
  entry but the pass rate stayed 2/7, because the fix's own approved design still doesn't count
  JSON structural overhead. Genuine-cache-hit token count also did not improve against either
  baseline in the original pilot measurement.
- Phase 4's direct-tool comparison (`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`) found the
  gateway **slower (1.31x-3.76x) and heavier in tokens (1.04x-2.93x) than direct tool use for all 7
  of 7 corpus entries** in a fresh, cold-cache, paired run — no entry excluded, no threshold
  redefined. Reviewer judgment: 6/7 direct-tool-equal-or-better, 1/7 mixed, 0/7 gateway-better.
- Phase 4's workflow-integration evaluation recommended against integration at 3 of 4 candidate
  points, measured 1.05x-3.0x heavier in tokens universally.
- Phase 5's repeated-demand measurement found a small, real, but mostly-non-literal repeated-question
  signal against this repository's own real historical usage, and recommended proceeding with
  entity-aware reuse "only after Phase 3's own disclosed gaps close — not now, not never." Those
  gaps are now closed in the sense of being re-measured and honestly re-confirmed (see above), not
  in the sense of the underlying numbers having improved.

None of this means the gateway is a failed idea — the architecture (versioned provider contracts,
evidence-aware invalidation, branch/working-tree safety, typed truncation visibility) is real,
tested, and independently verified sound at every phase by Architecture Review. What it means is
that this proposal's original latency/token hypothesis is not yet empirically supported by the
gateway's cold/warm-cache-mixed real-world corpus performance, and Phase 6 (or any further
production-promotion decision) should be weighed against these real numbers, not against the
optimistic framing in this section's original text above. See
`docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md` for the full consolidated audit.

## 26. Repository Evidence Map

The proposal's current-state claims should be revalidated when Phase 0 starts. The inspected
evidence for this 2026-08-11 snapshot is:

| Claim | Repository evidence |
|---|---|
| Mandatory Context Search and Graphify context scan | `CLAUDE.md` §Context Scan and investigation routing table |
| Context Search MCP tools and response fields | `tools/search_mcp.py`, `.mcp.json` |
| Hybrid dense/BM25 retrieval and source kinds | `tools/hybrid_retrieval.py`, `tools/knowledge_search.py` |
| Context-packet fields and current metadata-only assembly | `docs/engine/contracts/context_packet_contract.md`, `tools/context_packet_assembler.py` |
| Marker-only retrieval cache schema and manual pruning | `tools/retrieval_cache.py`, `tests/tools/test_retrieval_cache.py` |
| Empty-candidate, opt-in shadow hook | `.claude/workflows/implement-ticket.js`, `.agents/skills/implement-ticket/SKILL.md` |
| Retrieval observability | `tools/retrieval_events.py`, `docs/agent-monitoring/schema.md` |
| Parity authority and derived index | `docs/parity_ledger/schema.json`, `tools/parity_index.py` |
| Document authority/lifecycle vocabulary | `docs/REGISTRY.yaml`, `tools/generate_registry.py`, `tools/validate_frontmatter.py` |
| Graphify current graph and extraction mix | `graphify-out/GRAPH_REPORT.md`, `graphify-out/manifest.json` |
| Existing context-efficient retrieval initiative | `tickets/backlogs/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` and its linked decision docs |
| Approved simulation knowledge writes and revert | `src/lab/workflows.py`, `docs/ai/workflows.md` §`update-knowledge-store` |

## 27. Follow-Up Clarification Map

This revision preserves the proposal's architecture and changes only the areas materially affected
by `tmp/mcp-followup-instruction.md`.

| Follow-up concern | Prior proposal state | Revision |
|---|---|---|
| Ambient, phase-agnostic positioning | Gateway was read-first and fail-open, but workflow language overemphasized Investigate | Consolidated as an invariant; added §2.1; removed phase-specific pilot requirement |
| Cheapest reliable source | Direct tools remained available, but bypass guidance was implicit | Added explicit `rg`/Graphify/Context Search bypass guidance in §2.1 |
| Cache identity vs validity identity | Both concepts existed but were interleaved | Added the explicit two-contract rule and examples in §11.1 |
| Evidence granularity | Direct hashes and provider generation were described generically | Added closed evidence kinds and provider-qualified granularity rules in §12.1 |
| Provider capability differences | Adapter versions/timeouts existed, but capability-based routing was absent | Added the versioned capability contract in §8.1 |
| Negative knowledge | Kafka example correctly rejected empty-result reasoning | Formalized scope-backed negative claims in §13.1 |
| Cache validation cost | Cold/warm latency and stale rejection were already measured | Split lookup, validation, fallback, assembly, and end-to-end latency in §18 |
| Repeated knowledge demand | Exact/entity-aware hits and repeated misses were metrics | Added explicit demand evaluation and Phase 6 gate in §18.1 |
| Early retrieval vs later knowledge | Already separated through cache Levels 1–2 and deferred Level 3/Phase 6 | Preserved; Phase 6 now additionally requires demonstrated residual demand |
| Small MCP surface | Already limited to `knowledge_context` and `knowledge_status` | Preserved; clarified need-oriented caller options and hidden routing internals in §9 |
| Authority, disposability, evidence validity | Already present across goals, storage, provenance, and acceptance criteria | Consolidated into the top-level architectural invariants without changing ownership |
