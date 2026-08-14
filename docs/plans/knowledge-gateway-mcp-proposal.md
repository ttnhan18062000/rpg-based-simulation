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
  evidence, conflicts, and status/freshness/verification enums.
- Define provider adapter invocation, timeout, version, and fixture contracts.
- Define and test provider capability descriptors for Context Search and Graphify.
- Define evidence identity kinds, provider-qualified normalization, and the finest supported
  dependency granularity per provider.
- Freeze separate cache-lookup and evidence-validity identity contracts.
- Record current latency, tool-call counts, repeated-demand signals, and returned-token estimates
  for representative queries.
- Define separate measurement for lookup, evidence validation, provider fallback, packet assembly,
  and end-to-end latency.
- Predeclare measurable promotion thresholds from that baseline.
- Define repository, branch, and working-tree cache identity.
- Ratify the cached-payload redaction and retention policy.
- Define migrations that evolve the existing `retrieval_cache.db` rather than creating a parallel
  store.
- Define a reproducible token-counting method, budget tolerance, SQLite operating limits, and
  cache-GC defaults.
- Draft the generated-agent-instruction change replacing the blanket pre-scan mandate with the
  cheapest-reliable-source and ambient-utility rule; do not activate it before review.

### Phase 1: Read-Only Gateway

- Implement deterministic routing over Context Search and Graphify.
- Expose `knowledge_context` and `knowledge_status`.
- Register the gateway as an ambient general repository utility, with no ticket or workflow
  metadata required.
- Return uncached normalized results with provenance.
- Use deterministic classification and extractive/template packet assembly only.
- Preserve direct provider tools and fail-open behavior.

### Phase 2: Real Provider-Result Cache

- Add SQLite schema and migrations.
- Store actual bounded normalized results.
- Validate direct evidence fingerprints before hits, falling back to provider generation only when
  the provider capability contract lacks reliable finer-grained evidence.
- Add exact normalized-query reuse.

### Phase 3: Context-Packet Cache and Token Budgets

- Assemble deduplicated multi-provider packets.
- Store and return actual packet payloads.
- Enforce caller budgets using measured output size.
- Add packet dependency records and targeted invalidation.

Completion of Phase 3 is the first production-capable pilot boundary. Its provider set is Context
Search plus Graphify; Parity Ledger is not required until Phase 4. Production-capable here means an
opt-in advisory tool with approved payload policy and acceptance tests, not mandatory workflow use.

### Phase 4: Parity and Workflow Integration

- Add Parity Ledger routing.
- Add changed-path-aware task context.
- Evaluate optional workflow recommendations or opportunistic calls without creating a mandatory
  phase, gate, or ticket step.
- Compare gateway packets against existing direct-tool behavior.

### Phase 5: Entity-Aware Reuse

- Add canonical entity IDs and aliases.
- Reuse results across compatible phrasings.
- Add conservative semantic candidate matching with deterministic validation.

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

1. Ratify or reject the proposal's recommendation to cache bounded, redacted answer/context
   payloads from allowlisted source types.
2. Select the canonical repository and branch identity format.
3. Select the Graphify relation types eligible for deterministic answers.
4. Approve the packet token-counting method, budget classes, and tolerance produced in Phase 0.
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
