---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
phase: open
date: 2026-07-28
tags: []
---

# TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Title
Epic: Context-Efficient Agent Retrieval and Observability Initiative

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
Create a single epic-tier tracking ticket for the whole context-efficient agent retrieval and observability initiative. It is scope-only (no implementation), references the full 7-phase 'Sequenced Future Epic' sequence (item 0 Prerequisites plus phases 1-7) from the source doc as its own record, and lists all 6 Open Decisions from the source doc as unresolved items to be settled later.

## Scope
- Create epic-tier ticket tracking the context-efficient agent retrieval and observability initiative per docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- Record the full Sequenced Future Epic list (item 0 Prerequisites + phases 1-7) as this epic's own record, verbatim or by citation
- List all 6 Open Decisions from the source doc verbatim in Assumptions/Open Questions as unresolved
- Follow TCK-20260721-PROVIDER-AGNOSTIC-EPIC precedent for epic-tier scope-only wording

## Out of Scope
- No direct implementation of any phase (0-7)
- Does not authorize a new mandatory workflow gate
- Does not authorize a production monitoring-writer change
- Does not authorize a new external retrieval service
- Does not authorize adopting Qdrant/Postgres-pgvector/Neo4j/hosted RAG before measured need
- No child ticket creation performed inside this ticket itself

## Acceptance Criteria
- [ ] Epic's Scope section contains only tracking/sequencing wording, no implementation claimed
- [ ] Epic references source doc's full Sequenced Future Epic list (item 0 Prerequisites + phases 1-7) verbatim or by citation
- [ ] Assumptions/Open Questions section lists all 6 Open Decisions from source doc verbatim, marked unresolved
- [ ] Out of Scope explicitly excludes: new mandatory workflow gate, production monitoring-writer change, new external retrieval service, Qdrant/Postgres-pgvector/Neo4j/hosted RAG before measured need
- [ ] Ticket body ## Tier field is 'epic'; Related Code Areas is empty/none (scope-only)

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260702-OBSISO-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260729-HYBRID-RETRIEVAL-FUSION
- TCK-20260729-DETERMINISTIC-CODE-INDEX
- TCK-20260729-RETRIEVAL-CACHE-LEVELS
- TCK-20260729-CONTEXT-PACKET-ASSEMBLY
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
- TCK-20260729-RETRIEVAL-RETRO-VIEWS
- TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK
- TCK-20260729-SHADOW-PACKET-CALL-SITE
- TCK-20260729-SHADOW-BASELINE-COMPARISON

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md
- tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md
- tickets/todos/obs-isolation/TCK-20260702-OBSISO-EPIC.md

## Related Stored Artifacts
None.

## Related Code Areas
- none (scope-only epic)

## Assumptions / Open Questions
- Need to confirm the Phase 6 deferred-from-provider-agnostic-epic 'stable monitoring path' precondition is not the same thing as this epic's own item 0 prerequisite — verification tracked via child ticket TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- Maturity banner in source doc marks this PROPOSED FUTURE EPIC — does not yet authorize new mandatory workflow gate/writer change/external retrieval service
- OPEN DECISION 1 — **RESOLVED** (2026-07-29, `TCK-20260728-DEFAULT-PACKET-CRITERIA`): Which
  scenarios and phases justify a default context packet, and what are their initial token budgets?
  Answer: Small bugfix, Ticket implementation, and Architecture-planning justify a default packet
  today (directional Small/Medium/Large tiers, each grounded in real `search_count.per_run` volume
  patterns from `retrieval_baseline_metrics.py` — never a fabricated token count, since
  `context_tokens` remains platform-unavailable per `docs/agent-monitoring/schema.md`). Code review
  and Incident-monitoring investigation are deferred — no existing tool aggregates
  `events.jsonl`'s `phase`+`ts` fields into a per-phase (vs per-run) breakdown, so neither scenario
  can be isolated from run-scoped data without inventing a proxy this tool doesn't produce; this
  gap does not block the other three verdicts and does not resolve Open Decision 5. Full
  per-scenario verdict table and evidence: `docs/ai/default_packet_scenarios_decision.md`.
- OPEN DECISION 2 — **RESOLVED** (2026-07-29, `TCK-20260728-CODE-TEST-INDEX-BOUNDARIES`): Which
  code/test relationships can be built deterministically from existing AST, import, test naming,
  and Graphify data before adding any semantic code model? Answer: exactly Graphify's Part A
  (tree-sitter/AST) relation set — `imports`, `imports_from`, `calls`, `contains`, `defines`,
  `uses`, `uses_static_prop`, `references_constant`, `bound_to`, `listened_by`, `includes`,
  `uses_component`, `binds_method`, `rationale_for` — all `confidence_score = 1.0`. Part B
  (LLM-derived `conceptually_related_to`/`semantically_similar_to`/`shares_data_with`) is excluded
  as non-deterministic. Test-naming linkage remains a deterministic *procedure* only (agent prose
  in `.claude/agents/test-scoper.md`), not checked-in code — flagged as an open gap for any future
  Phase 2+ retrieval ticket. Full evidence and relation-type table:
  `docs/ai/code_test_index_boundaries_decision.md`.
- OPEN DECISION 3 — **RESOLVED** (2026-07-29, `TCK-20260728-CONTEXT-PACKET-SCHEMA`): Which
  authority/freshness metadata should be mandatory for a packet source, and how should conflicting
  active documents be represented? Answer: packet `authority`/`freshness` map directly onto
  `docs/REGISTRY.yaml`'s existing `authority` (`P0`/`P1`/`P2`) and `status`
  (`authoritative`/`active`/`historical`/`archive`) enums for REGISTRY-backed sources (docs
  outside `_SKIP_DOC_SUBDIRS`, `tickets/done/` entries) — no new independent vocabulary. Two
  extensions cover what the idea doc's field list didn't specify: non-registry-backed `kind`
  values (`code_symbol`, `test`, `graphify_node`, `tickets/inprogress/` bodies) get
  `authority`/`freshness: unrated`, a doc-only sentinel distinct from REGISTRY's enums;
  `parity_ledger_entry` sources use the parity ledger's own differently-shaped `priority`/`status`
  proxy instead. Conflicting active documents are resolved by an advisory, doc-only tie-break:
  include both, rank by `authority` then `last_verified` recency, and flag the lower-ranked
  entry's `inclusion_reason` as superseded — never silently dropped. No `docs/REGISTRY.yaml`
  schema/enum change accompanies this. Full field shapes and evidence:
  `docs/engine/contracts/context_packet_contract.md`.
- OPEN DECISION 4 — **RESOLVED** (2026-07-29, `TCK-20260728-RETRIEVAL-RETENTION-REDACTION`): What
  retention and redaction policy applies to retrieval events and cache entries? Answer: retrieval
  events (landing in `agent-monitoring/*.jsonl`) inherit that system's existing retain-forever/
  append-only convention — "retention" for events means redaction-only (hashes/IDs/counts/reason
  codes/scores; never raw prompt or retrieved-content text), not a deletion duration. Caches
  (embedding/index, query-result, context-packet) are ephemeral/rebuildable and DO get
  duration-based expiry, each assigned its own placeholder category extending `RetentionPolicy`'s
  7d/30d/permanent naming pattern in prose only (no code change to `retention.py`). Full
  MAY/PROHIBITED field list, per-cache-level category table, and rationale:
  `docs/observability/retrieval_retention_redaction_policy.md`.
- OPEN DECISION 5: What sample size and thresholds are sufficient to promote a scenario from advisory to default behavior?
- OPEN DECISION 6: Should context packets be exposed as an MCP tool, a provider-adapter library, or both after the provider-neutral contract is implemented?

## Implementation Notes

**2026-07-28 — Phase 0-1 batch complete.** All 3 child tickets from this batch
(`TCK-20260728-PHASE0-PREREQ-CONFIRMATION`, `TCK-20260728-RETRIEVAL-BASELINE-METRICS`,
`TCK-20260728-EVAL-FIXTURE-REPAIR`) are `DONE` — see `tickets/done/` and
`tickets/working_log.csv`. Phase 0's own prerequisite (provider-neutral execution
identity, shared monitoring writer, stable replay/live boundary) was directly
confirmed satisfied by `TCK-20260728-PHASE0-PREREQ-CONFIRMATION`.

**2026-07-29 — Phase 2 batch complete.** All 4 decision-doc child tickets
(`TCK-20260728-CONTEXT-PACKET-SCHEMA`, `TCK-20260728-CODE-TEST-INDEX-BOUNDARIES`,
`TCK-20260728-DEFAULT-PACKET-CRITERIA`, `TCK-20260728-RETRIEVAL-RETENTION-REDACTION`)
are `DONE`, resolving Open Decisions 1-4 (see Assumptions/Open Questions above).

**2026-07-29 — Phase 3 batch complete.** All 4 code-producing child tickets
(`TCK-20260729-DETERMINISTIC-CODE-INDEX`, `TCK-20260729-HYBRID-RETRIEVAL-FUSION`,
`TCK-20260729-RETRIEVAL-CACHE-LEVELS`, `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) are
`DONE` — standalone, read-only hybrid retrieval, code/test index, 3-level SQLite
cache, and ContextPacket assembler, none wired into any `.claude/workflows/*.js`
file per this phase's "no mandatory invocation" constraint.

**2026-07-29 — Phase 4 batch complete.** All 3 child tickets
(`TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`, `TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK`,
`TCK-20260729-RETRIEVAL-RETRO-VIEWS`) are `DONE` — a new versioned, `run_id`-scoped
retrieval-event field family wired through the existing monitoring writer
(`tools/retrieval_events.py`), a structural (not live) provider-parity check for that
field shape, and real dashboard/retro views (cache rates, noise ratios, freshness/
authority distribution, expansion rate) rendered into `generate_retro.py`'s report
output for the first time. Standalone-invocation provenance uses a new
`RETRIEVAL-EVENT-<slug>` `run_id` prefix deliberately unrecognized by
`vocabulary.py::infer_workflow()`, so these events never interleave into any real
ticket's event stream and are visible only under `--all` (never `--days`/`--week`).
Nothing in this phase was wired into any `.claude/workflows/*.js` file or made to
fire automatically during real agent workflow runs, per this phase's own scope
constraint.

This epic remains **open**, not closed — per its own Scope and `SEQUENCE.md`, it
deliberately covers only Phase 0-4 of the source doc's full 7-phase Sequenced Future
Epic so far; Phase 5 onward (shadow context packets, selective workflow adoption,
continuous calibration) is intentionally not yet ticketed, and Open Decisions 5-6 in
Assumptions/Open Questions remain unresolved. Do not mark this ticket DONE or move it
to `tickets/done/` until a future ticketing pass scopes and closes the remaining
phases (or a deliberate decision is made to stop pursuing them, in which case this
ticket should instead move to `tickets/backlogs/` per `docs/ai/ticket-lifecycle.md`'s
backlog convention — not silently closed as done).

## Test Summary

## Files Changed

## Completion Summary
