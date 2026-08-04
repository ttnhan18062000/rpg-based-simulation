---
status: active
layer: ai
authority: P2
audience: developer
maturity: proposed-future-epic
date: 2026-07-21
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Idea: Context-Efficient Agent Retrieval and Observability

> **Maturity: PROPOSED FUTURE EPIC.** This is deliberately sequenced after the
> provider-agnostic orchestration discovery and implementation work. It may
> begin with baseline measurement and a read-only retrieval prototype, but does
> not authorize a new mandatory workflow gate, a production monitoring writer
> change, or a new external retrieval service.

## Problem

The repository is already large enough that broad context loading is expensive
and increasingly unreliable. It contains roughly 150k lines of code, a large
test suite, extensive plans and ticket history, generated registries, Graphify
output, and append-only agent-monitoring logs. The current agent working
process frequently asks agents to run semantic search, Graphify, registry and
ticket-history checks before targeted source and test reads. Those controls are
valuable for high-risk work, but applying them broadly can consume more context
than the implementation problem itself.

The objective is **not** simply faster search or fewer retrieval results. It is
to minimize token use while retaining enough current, authoritative evidence to
make correct decisions for a specific task and phase:

> Return the smallest cited context set that is sufficient for the task's risk,
> phase, and affected code paths.

The system must avoid both failure modes:

- **under-context:** missing an active constraint, paired test, contract, or
  prior decision and producing incorrect work;
- **over-context:** injecting old plans, raw logs, duplicate summaries, or
  unrelated graph communities that dilute the useful signal.

## Current Foundation and Gaps

The repository already has a useful local foundation:

| Component | Current role | Gap to address |
|---|---|---|
| `tools/knowledge_search.py` | Local embeddings, SQLite vector index, BM25, incremental document index | Its intended corpus excludes `src/` and `tests/`; it cannot assemble implementation/test context by itself. |
| `tools/search_mcp.py` | Agent-facing `search_docs` and health tools | It returns ranked document chunks, not a bounded, task-aware context packet. |
| `graphify-out/` and `graphify query` | Code/doc relationship discovery and community overview | Valuable for dependency/path questions, but too broad as a default context source. |
| `docs/REGISTRY.yaml` and `tickets/working_log.csv` | Authority and prior-work discovery | They are consulted separately instead of being ranked/filterable packet inputs. |
| `agent-monitoring/*.jsonl` and dashboard | Workflow and tool activity observability | They do not yet record retrieval selection, context budget, cache use, or adequacy. |

The retrieval path also needs measured calibration. Dense and lexical retrieval
must both contribute candidates before ranking; a lexical-only exact match must
not disappear merely because it was absent from an early dense candidate set.
Existing evaluation queries are a starting point, but must be refreshed when
canonical paths change and expanded to cover agent-work questions, not only
simulation documentation.

## Design Principles

1. **Task-specific, not corpus-wide.** Retrieval begins with task intent,
   ticket metadata, workflow phase, risk/tier, and changed paths where known.
2. **Progressive disclosure.** Start with a small packet; retrieve more only
   after an explicit `insufficient`, `stale`, or `conflicting` verdict.
3. **Authority and freshness first.** Active authoritative contracts and the
   current ticket outrank archived plans, generated summaries, and historical
   monitoring data.
4. **Citations over opaque memory.** Every injected item includes source path,
   heading/symbol, content hash, and inclusion reason.
5. **No raw prompt or source-text telemetry.** Monitoring stores identifiers,
   hashes, counts, scores, and reason codes—not full prompts, full retrieved
   content, or unredacted tool payloads.
6. **Provider-neutral semantics.** Claude Code and Codex use the same context
   packet schema and emit the same retrieval events; adapters may differ only
   in invocation mechanics.
7. **Read-only and reversible first.** The first slice is advisory and derived
   from existing sources. It must not become a live workflow dependency until
   evidence supports that change.

## Proposed Architecture

### 1. Context-packet contract

Define a provider-neutral `ContextPacket` as a bounded, versioned set of
references rather than a copy of an agent conversation:

```text
ContextRequest
  task_ref | ticket_id | free-text intent
  provider, agent_role, workflow, phase
  risk_tier, changed_paths, scenario, token_budget

  → classify and retrieve

ContextPacket
  packet_id, corpus_generation, retrieval_version
  budget_requested, budget_returned
  included[]: source_id, kind, path, heading_or_symbol, hash,
              authority, freshness, score, inclusion_reason, excerpt_budget
  excluded_summary[]: source_id/kind/reason/count only
  expansion_policy and escalation conditions
```

The packet is a retrieval artifact, not a new source of truth. Consumers must
re-read the cited source before making a high-impact change and reject packets
whose source hashes no longer match.

### 2. Retrieval layers

Use a query router to select the smallest relevant combination of sources:

| Need | First retrieval source | Optional expansion |
|---|---|---|
| Policy, active decision, prior ticket | Docs/registry/ticket hybrid retrieval | Related Material and working-log links |
| Implementation | Changed-path/symbol index and direct source reads | Graphify call/import neighbors |
| Test selection | Symbol-to-test and changed-path ownership index | Failure-message/exact-term search |
| Architecture/dependency question | Targeted Graphify traversal | Bounded community summary |
| Monitoring/retro question | Derived monitoring read index | Raw JSONL only for a cited anomaly |

The ranker should retrieve a bounded candidate set independently from dense and
lexical channels, union the sets, then apply a stable fusion method such as
reciprocal-rank fusion. It should apply metadata filters before context
assembly: source kind, component, status, authority, provider, lifecycle, and
freshness. A lightweight re-ranker is a later option only if evaluation proves
that fusion and metadata are insufficient.

For code and tests, index symbols and relationships—not entire files as large
embedding chunks. Useful fields include module, symbol, docstring/summary,
imports/calls, owned component, associated tests, and changed-path proximity.
Graphify remains the relationship layer; it should not inject an entire
community unless the task asks for architectural traversal.

### 3. Cache design

Cache retrieval work at three independently invalidatable levels:

| Cache | Key | Value | Invalidation |
|---|---|---|---|
| Embedding/index | content hash + embedding/chunking version | vectors/index rows | Source, model, or chunking change |
| Query result | normalized query + filters + corpus generation + retrieval version | ranked source IDs and scores | Any indexed-source or ranking change |
| Context packet | task/ticket intent + phase + changed paths + scenario + policy version | cited bounded packet | Any cited source hash, corpus generation, policy, or budget change |

SQLite is sufficient for the first implementation: local, inspectable,
zero-operations, and consistent with the current knowledge index. Caches store
references and compact excerpts, never full conversations. Cache events must
also include stale-cache rejection and miss reasons so performance improvements
cannot hide correctness regressions.

Do not introduce Qdrant, Postgres/pgvector, Neo4j, or a hosted RAG service in
this epic. Reconsider a shared retrieval service only if evidence shows a
multi-repository/multi-user workload, continuously updated shared index, or
local SQLite capacity/latency limit that cannot be solved by bounded indexing.

## Working-Process Change

After the initial advisory proof is approved, add one provider-neutral phase to
the applicable workflows:

```text
Classify task and risk
  → request bounded context packet
  → record selection and budget (metadata only)
  → perform phase work using cited sources
  → record adequacy verdict
  → retrieve an expansion only when verdict requires it
```

This phase must be **scenario-aware**, not a universal expensive preamble.

| Scenario | Default packet contents | Expansion rule |
|---|---|---|
| Small bugfix | Ticket/issue, affected symbols, nearest tests, active local contract | Only on ambiguity, failing test, or cross-component call |
| Ticket implementation | Ticket ACs, scoped design/ADR, affected symbols/tests, relevant prior ticket | Architecture traversal only if dependency boundary is crossed |
| Code review | Diff/changed paths, relevant contract, paired tests, risk checklist | Prior history only for a concrete regression question |
| Architecture/planning | Active plans/ADRs, registry entries, Graphify path/community evidence | Larger budget allowed, but still cited and deduplicated |
| Incident/monitoring investigation | Incident/ticket, derived monitoring query results, relevant writer/reader code | Raw logs only to verify a specific cited record |

Each provider adapter must pass an execution identity, provider, role, and
phase to the shared retrieval boundary. It must not require identical provider
tool names or hook mechanics. The provider-agnostic orchestration work is a
prerequisite because it establishes the execution identity and portable
monitoring writer this feature needs.

## Retrieval Observability and Dashboard

Add a versioned, provider-neutral retrieval event family to the shared
monitoring schema only after the monitoring writer/identity decisions are
implemented. Suggested event fields:

| Group | Fields |
|---|---|
| Attribution | `execution_id`, `provider`, `agent_role`, `workflow`, `phase`, `ticket_id` |
| Request | `scenario`, `risk_tier`, normalized-query hash, changed-path count, requested budget |
| Retrieval | corpus/graph generation, retrieval version, cache level/status, latency, candidate count, selected count |
| Context | source-kind counts, authority/freshness counts, returned token estimate, exclusion reason counts, cited-source hashes |
| Outcome | adequacy verdict (`sufficient`, `insufficient`, `noisy`, `stale`, `conflicting`), expansion reason/count, final phase status |
| Quality joins | test/gate result, review outcome, rework/reopen signal when deterministically attributable |

The dashboard and periodic retro should make these decision-support views
available:

- Median and percentile context tokens by scenario, phase, role, and provider.
- Cache hit, miss, and stale-rejection rates by cache level.
- Candidate-to-selected and selected-to-cited ratios as noise indicators.
- Follow-up retrieval/expansion rate as an initial-packet adequacy indicator.
- Freshness/authority distribution and most frequently stale or never-used
  sources.
- Test, gate, review, and rework outcomes by context-budget band—interpreted
  cautiously, never as proof of causation from a small sample.
- Before/after baseline comparisons with corpus/retrieval-version labels.

The dashboard must not reward smaller packets by themselves. A context-budget
reduction is successful only when correctness signals hold or improve.

## Evaluation and Decision Follow-Up

### Baseline

Before changing any mandatory workflow, collect a baseline period for the
current process. Record only available, safe metadata; unknown values must be
explicitly marked rather than synthesized. Establish scenario-specific ranges
for context tokens, follow-up search count, phase duration, test/gate outcome,
and review rework.

### Offline retrieval evaluation

Extend `tools/eval/queries.json` (or a successor versioned fixture set) with:

1. documentation and exact-identifier queries;
2. active-policy and superseded/archived-document disambiguation queries;
3. ticket-history and prior-decision queries;
4. symbol-to-test and changed-path queries;
5. provider/workflow/monitoring questions; and
6. known difficult/no-result cases.

For each query, maintain expected authoritative source IDs, allowable
alternatives, source lifecycle assumptions, and a context budget. Measure
recall at the packet boundary, authority/freshness correctness, duplicate rate,
and estimated injected-token cost—not only rank position.

### Shadow evaluation and approval gate

Run the new packet builder in shadow/advisory mode for selected scenarios. It
must not block agent work. Compare its packets and outcomes with the baseline.

Promotion from advisory to default workflow behavior requires a recorded review
showing all of the following for the selected scenarios:

- authoritative-source recall is at least the agreed baseline;
- no material increase in missed contracts, test/gate failures, or review
  rework attributable to missing context;
- a meaningful, pre-declared reduction in median injected context tokens or
  follow-up retrieval burden;
- cache correctness: stale packets are rejected and source-hash checks pass;
- provider parity: comparable request/packet/outcome events are emitted for
  every enabled provider; and
- privacy boundary: monitoring contains no raw prompts, raw retrieved source
  text, or sensitive tool payloads.

The numeric thresholds, sample size, and attribution method are deliberately
open decisions for discovery. They must be selected before shadow evaluation,
not retrofitted after results are known.

## Sequenced Future Epic

This should be implemented as a limited, evidence-led epic after the
provider-agnostic implementation has a stable shared monitoring path:

0. **Prerequisites** — provider-neutral execution identity and monitoring writer
   are implemented; the provider-agnostic adapter has a stable replay/live
   boundary.
1. **Baseline and evaluation fixtures** — audit retrieval behavior, repair stale
   expectations, define scenarios and outcome joins; no workflow change.
2. **Retrieval contract and metadata inventory** — decide context-packet schema,
   authority/freshness rules, code/test index boundaries, retention, and privacy
   controls.
3. **Read-only hybrid retrieval and cache proof** — build local docs/code/test
   retrieval plus cache invalidation tests; no mandatory invocation.
4. **Observability and dashboard proof** — add retrieval events through the
   approved shared writer and dashboard/retro queries; validate provider parity.
5. **Shadow context packets** — advisory packets for selected workflows/phases;
   evaluate against baseline and review evidence.
6. **Selective workflow adoption** — enable the packet phase only for scenarios
   that pass the approval gate; retain direct targeted reads as the safety
   fallback.
7. **Continuous calibration** — periodic effectiveness reviews, fixture updates,
   source-quality remediation, and budget tuning.

## Non-Goals

- Replacing agents' direct source/test reads with opaque RAG answers.
- Persisting or replaying full agent conversations as a retrieval cache.
- Automatically broadening context after a low-confidence answer without an
  explicit escalation reason.
- Making Graphify, semantic search, cache availability, or dashboard health a
  hard gate for all tasks.
- Replacing the existing provider-agnostic discovery epic, monitoring schema
  work, or replay proof.
- Introducing a new external vector/graph database before measured need.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Token reduction hides missing critical context | Require authority-recall and task-quality measures alongside token metrics. |
| Cache returns stale guidance | Content hashes, corpus generations, source revalidation, and stale-rejection events. |
| Retrieval telemetry leaks sensitive content | Store hashes, IDs, counts, and reason codes only; never raw prompts or chunks. |
| Another mandatory process layer increases ceremony | Begin advisory-only; enable only scenario/phase combinations with evidence of net benefit. |
| Graph expansion becomes broad context dumping | Enforce traversal and token budgets; record expansion reason and selected edges. |
| Claude and Codex optimize differently | Shared packet/event contracts and provider-separated dashboard comparisons. |
| Evaluation fixtures become stale | Version fixtures, test canonical paths/status, and include stale-path regression cases. |

## Open Decisions

1. Which scenarios and phases justify a default context packet, and what are
   their initial token budgets?
2. Which code/test relationships can be built deterministically from existing
   AST, import, test naming, and Graphify data before adding any semantic code
   model?
3. Which authority/freshness metadata should be mandatory for a packet source,
   and how should conflicting active documents be represented?
4. What retention and redaction policy applies to retrieval events and cache
   entries?
5. What sample size and thresholds are sufficient to promote a scenario from
   advisory to default behavior?
6. Should context packets be exposed as an MCP tool, a provider-adapter library,
   or both after the provider-neutral contract is implemented?
7. Open Decision 3 fixed how a single `included[]` entry's `authority`/`freshness` are
   populated per `kind`, but never how competing candidates of *different* `kind`s
   (e.g. a `doc` and a `parity_ledger_entry`) are ranked or chosen between when a bounded
   `token_budget` cannot fit both. What cross-kind candidate-selection/ranking policy
   applies once more than one live `kind` exists? (Raised 2026-08-02, surfaced by
   `tools/parity_index.py`'s new `parity_ledger_entry` read path landing alongside the
   existing `doc`/`ticket`/`code_symbol`/etc. kinds with no decided precedence between
   them — `tools/context_packet_assembler.py::assemble_context_packet()` takes an
   already-decided `included_candidates` list and never re-sorts/weights by `kind`.)
8. Should `stored_artifacts/{ticket_id}/*.md` (`investigation.md`/`plan.md`/`test_plan.md`,
   each carrying real frontmatter — `artifact_type`, `status`, `authority`) become its own
   registry-indexed `kind` (e.g. `stored_artifact`), so the rationale/decision content
   inside a closed ticket's artifacts is retrievable on its own terms rather than only
   visible via the parent ticket's `artifact_files` path list (`tools/generate_registry.py`
   ::`join_artifact_files()`)? Relatedly: confirm whether `staging_artifacts/`'s current
   total exclusion from `generate_registry.py`'s scan (correct today, since it holds
   in-progress/scratch content for open tickets) should be recorded as an explicit,
   permanent design decision rather than an implicit gap, once/if Decision 8 gives
   `stored_artifacts/` its own retrieval treatment. (Raised 2026-08-02.)
9. `tools/parity_index.py`'s `entry()`/`impact()`/`health()` functions establish a
   deterministic, exact-structural-lookup query pattern (never similarity-ranked, always
   gate-safe, explicitly distinct from the fuzzy RRF-fused `search`/`tools/hybrid_retrieval.py`
   path) for the `parity_ledger_entry` kind specifically. Should this exact-vs-fuzzy
   retrieval-type split be documented as a general project convention that any future
   `kind` needing gate-safe lookups should follow, rather than remaining an
   implicit, parity-specific pattern? (Raised 2026-08-02.)

## Related Material

- `docs/plans/archive/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` (archived — shipped)
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` (archived — shipped)
- `tools/knowledge_search.py`
- `tools/search_mcp.py`
- `tools/eval/queries.json`
- `docs/ai/workflows.md`
- `docs/guidelines/agent_working_environment.md`
- `docs/agent-monitoring/schema.md`

---

*Raised: 2026-07-21. This future epic captures the need to control context
growth in the project agent system while preserving quality and making the
result measurable. It is intentionally separate from the current
provider-agnostic migration: that work establishes the shared identities,
contracts, and monitoring path this proposal will reuse.*
