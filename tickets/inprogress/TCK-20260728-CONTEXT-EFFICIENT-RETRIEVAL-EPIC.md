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
- TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS
- TCK-20260802-CONTEXT-KIND-PRIORITY
- TCK-20260802-STORED-ARTIFACT-KIND
- TCK-20260802-EXACT-LOOKUP-CONVENTION

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
- OPEN DECISION 5 — **RESOLVED** (2026-07-30, `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS`): What
  sample size and thresholds are sufficient to promote a scenario from advisory to default behavior?
  Answer: applies only to the 3 scenarios Open Decision 1 already justified (Small bugfix, Ticket
  implementation, Architecture-planning). Each of the idea doc's six approval-gate criteria gets an
  explicit bar (e.g. cache correctness and privacy boundary are zero-tolerance invariants; the
  token/burden-reduction criterion uses `search_count.per_run` as a token-unavailable proxy, requiring
  at least 1 whole search fewer at the median). Sample size is a per-scenario shadow-enabled run-count
  floor (56 / 122 / 6 respectively) grounded in the same real `retrieval_baseline_metrics.py` evidence
  Decision 1 used for each scenario, combined with an elapsed-period floor reusing the existing
  agent-monitoring-retro weekly/5-ticket cadence — whichever is reached later. No existing Phase 0-5
  tool computes causal attribution between an outcome and missing/present context; a join-by-`run_id`
  method is proposed (§4) but requires a human-reviewed audit until a structured gate-failure-cause
  field exists, since `reason_code` is null for every `Review`/`Architecture-Verify` event today.
  Authoritative-source recall and provider parity are flagged as **not** fully defensible a priori —
  recall lacks a join from `eval_search.py`'s index-level Recall@5 gate to a real shadow packet's
  cited sources, and provider parity cannot be measured with only one of two known adapters
  (`claude-code`) ever live. Zero real shadow-packet production events exist as of this decision
  (`SHADOW_CONTEXT_PACKET_ENABLED` off by default, confirmed via `TCK-20260729-SHADOW-PACKET-CALL-SITE`/
  `TCK-20260729-SHADOW-BASELINE-COMPARISON`) — thresholds are deliberately chosen in that absence, per
  the idea doc's own instruction that they be selected before evaluation, not retrofitted after. Full
  per-criterion table and evidence: `docs/ai/shadow_promotion_gate_thresholds_decision.md`.
- OPEN DECISION 6 — **RESOLVED** (2026-07-30, `TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION`):
  Should context packets be exposed as an MCP tool, a provider-adapter library, or both after the
  provider-neutral contract is implemented? Answer: both, but not symmetric — a provider-adapter
  library is the default/primary integration (matches
  `docs/architecture/agent_orchestration_contract.md`'s one `Decided` sub-decision, Provider-Adapter
  Boundary, and the one real Phase 5 shadow-packet-call-site precedent), with MCP tool exposure as a
  secondary, optional interface layered over the same library (matching `tools/search_mcp.py`'s
  existing `search_docs`/`search_health` precedent and Codex's confirmed hook-matcher awareness of
  MCP tool names). Explicitly directional, not final: two of the ADR's three relevant sub-decisions
  remain `Proposed-pending-implementation-evidence`, and Codex has zero live runtime presence in this
  repo as of this decision (`tickets/todos/codex-runtime-activation/` not started, no `.codex/`
  directory exists) — provider parity is exactly as unverifiable here as it was for Open Decision 5.
  Full evidence and reasoning: `docs/ai/context_packet_exposure_mechanism_decision.md`.
- OPEN DECISION 7 — **RESOLVED** (2026-08-02/03, `TCK-20260802-CONTEXT-KIND-PRIORITY`): Open
  Decision 3 fixed how a single `included[]` entry's `authority`/`freshness` are populated per
  `kind`, but never how competing candidates of *different* `kind`s are ranked or chosen between
  under a bounded `token_budget`. What cross-kind candidate-selection/ranking policy applies?
  Answer: three technical constraints are resolved definitively — `unrated` must not default to
  worst (§3's existing fabricated-default prohibition is newly binding cross-kind), `score` is not
  a cross-kind-comparable signal today (`code_symbol`/`parity_ledger_entry` candidates hardcode
  `score = 0.0` while `HybridResult`-derived candidates carry a real RRF float), and
  `_resolve_subject_conflicts()` cannot structurally fire cross-kind (its `_CONFLICT_ELIGIBLE_
  FRESHNESS` gate mathematically excludes every `unrated`/parity-status freshness value before
  comparison begins). The residual ordering question — where `unrated` sits relative to `P1`/`P2`,
  and whether a `P0` `parity_ledger_entry` gets a hard inclusion floor — is explicitly **not**
  resolved here: it is a genuine value judgment with zero existing repo precedent for an
  inclusion-floor/budget-trimming mechanism, and is deferred pending explicit human sign-off rather
  than settled by self-chosen ordering. Full resolution and code citations:
  `docs/engine/contracts/context_packet_contract.md` §5.
- OPEN DECISION 8 — **RESOLVED** (2026-08-02/03, `TCK-20260802-STORED-ARTIFACT-KIND`): should
  `stored_artifacts/{ticket_id}/*.md` become its own registry-indexed `kind` (its rationale/decision
  content is currently invisible to retrieval except via the parent ticket's `artifact_files` path
  list), and should `staging_artifacts/`'s current total exclusion from `generate_registry.py` be
  recorded as an explicit permanent decision rather than an implicit gap? Answer: resolved as a
  documentation-only change. Yes — `stored_artifacts/*.md` (the canonical
  `investigation.md`/`plan.md`/`test_plan.md` triplet) warrants a new `stored_artifact`
  registry-indexed kind, classified under Open Decision 3's Branch 1 (REGISTRY-backed direct
  mapping), since its frontmatter carries the same `status`/`authority` enums REGISTRY.yaml's own
  `doc`/`ticket` entries use and the only reason it isn't already indexed is `collect_docs()`'s
  `docs/`-only walk, a directory-scope gap rather than a schema mismatch. `staging_artifacts/`'s
  exclusion is confirmed intentional permanent design, not an accidental gap. Corpus heterogeneity
  (412 `index.md` files, legacy non-`TCK-*` directories, dozens of non-canonical filenames) is
  flagged as a scope boundary for a future scanner-building ticket, not resolved here. Full
  resolution and code citations: `docs/engine/contracts/context_packet_contract.md` §6.
- OPEN DECISION 9 — **RESOLVED** (2026-08-02/03, `TCK-20260802-EXACT-LOOKUP-CONVENTION`): should
  the exact-structural-lookup query pattern `tools/parity_index.py`'s `entry()`/`impact()`/
  `health()` establishes (deterministic, gate-safe, distinct from the fuzzy RRF-fused `search`
  path) be documented as a general project convention for future `kind`s needing gate-safe
  lookups, rather than staying parity-specific? Answer: **no**, for now. With n=1 (no second
  `kind` has ever needed a gate-safe exact lookup), rule-of-three reasoning applies — applicability
  criteria written today from a single instance would either overfit to `parity_index.py`'s
  specific implementation choices or be abstracted so far it becomes unfalsifiable. The Gate A GO
  verdict's recall numbers (66.7% vs. 4.8%) are evidence of parity-domain retrieval quality, not
  of pattern generalizability to a different `kind` — those are two different claims, and this
  resolution does not conflate them. The pattern's generalizable properties (read-only access,
  exact equality matching, deterministic sort, explicit typed no-match response, zero mutation
  surface) are recorded as a citable, non-mandatory reference, not a mandatory convention, with an
  explicit reopening condition: revisit once a second real `kind` genuinely needs a gate-safe
  exact lookup. Full resolution and code citations:
  `docs/engine/contracts/context_packet_contract.md` §7.

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

**2026-07-29 — Phase 5 batch complete.** Both child tickets
(`TCK-20260729-SHADOW-PACKET-CALL-SITE`, `TCK-20260729-SHADOW-BASELINE-COMPARISON`) are
`DONE` — an opt-in, fail-open shadow context-packet call site wired into
`implement-ticket.js`'s Investigate phase (gated behind `SHADOW_CONTEXT_PACKET_ENABLED`,
off by default, using a monotonic-negative `seq` counter provably disjoint from real
per-phase event seqs — the first `.claude/workflows/*.js`-touching ticket in this whole
epic), and a shadow-vs-baseline retrieval comparison report section added to
`generate_retro.py`, partitioning real (`TCK-...`) vs. synthetic (`RETRIEVAL-EVENT-...`)
run_id provenance and reusing `compute_retrieval_metrics()` per cohort. Both plans
required one architecture-review revision cycle each (a seq-collision bug and a missing
None-guard, respectively) before approval. Parity ledger entries INFRA-296/297/299/300
added or corrected.

**2026-07-30 — Phase 6 prep: Open Decision 5 resolved.** `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS`
is `DONE` — `docs/ai/shadow_promotion_gate_thresholds_decision.md` attaches a falsifiable
threshold or qualitative bar to each of the six approval-gate criteria, grounds a sample
size in real per-scenario run counts from `retrieval_baseline_metrics.py`, and proposes a
`run_id`-join attribution method (explicitly flagged as unimplemented by any existing
Phase 0-5 tool). Two criteria — authoritative-source recall and provider parity — are
honestly flagged as not fully defensible a priori given zero real shadow-packet
production events exist as of this decision, rather than forced into invented numbers.
This ticket was decision-document-only, per its own scope guard: no code changed, no
promotion occurred, `SHADOW_CONTEXT_PACKET_ENABLED` was not enabled anywhere.

**2026-07-30 — First real shadow-packet data collected.** `SHADOW_CONTEXT_PACKET_ENABLED`
was enabled permanently in this development machine's shell environment (user decision,
outside any ticket's scope) and the placement-legality mini-epic
(`TCK-20260716-PLACELEGAL-HARDLAW`, `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`, both `DONE`) was
run as a real vehicle to exercise it. Result: 2 real shadow-packet events now exist in
`agent-monitoring/events.jsonl` (`agent: context-packet-wrapper`, real `TCK-...` `run_id`s),
up from the 0 recorded at the time `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` set the
sample-size floors. This is a genuine first data point, not a threshold crossing — the
per-scenario floors resolved for Open Decision 5 (56 / 122 / 6 shadow-enabled runs, or one
full agent-monitoring-retro cadence cycle, whichever is later) remain far off. Phase 6
implementation (selective workflow adoption using those thresholds) still cannot be
responsibly scoped from 2 samples; this note exists so a future ticketing pass can see real
progress has begun, not to imply the gate can be evaluated yet.

**2026-07-30 — Second data-collection vehicle: progress-timeline batch (4 tickets).**
`TCK-20260720-BULK-RUN-TIMELINE`, `TCK-20260720-ECHARTS-PHASE-PALETTE`,
`TCK-20260720-PROGRESS-TIMELINE-VIEW`, `TCK-20260720-TIMELINE-RANGE-CONTROL` — all `DONE`.
Run as a second real vehicle (user-chosen, after the placement-legality batch) purely for
its side effect of exercising `SHADOW_CONTEXT_PACKET_ENABLED=1` during each ticket's
Investigate phase. Result: 4 additional real shadow-packet events, bringing the running
total to **6** (`agent-monitoring/events.jsonl`, `agent: context-packet-wrapper`, all real
`TCK-...` `run_id`s). Still far short of the 56/122/6 per-scenario floors from Open
Decision 5 — 6 samples is meaningful *progress*, not close to sufficiency for any
promotion-gate evaluation. No change to this epic's own scope or the Phase 6 blocker below.

**2026-07-30 — Open Decision 6 resolved.** `TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION` is
`DONE` — `docs/ai/context_packet_exposure_mechanism_decision.md` recommends a provider-adapter
library as the default/primary integration path with MCP tool exposure as a secondary optional
interface over the same library, explicitly flagged as directional (not final) pending two
still-`Proposed-pending-implementation-evidence` ADR sub-decisions and zero live Codex runtime
presence in this repo. All 6 Open Decisions this epic tracks are now resolved. This does not
authorize any Phase 6 wiring — the 56/122/6 sample-size floors from Open Decision 5 remain the
gate for that, and remain far from met (6 real shadow-packet events as of this writing).

This epic remains **open**, not closed — per its own Scope and `SEQUENCE.md`, it
deliberately covers only Phase 0-5 plus this Phase 6 prep decision so far; actual Phase 6
implementation (selective workflow adoption — enabling the shadow-packet phase only for
scenarios that pass the approval gate using the thresholds resolved above) still cannot be
scoped: it requires real, non-fixture shadow-packet evidence that does not yet exist
(`SHADOW_CONTEXT_PACKET_ENABLED` remains off by default in production), and Open Decision 6
in Assumptions/Open Questions remains unresolved. Do not mark this ticket DONE or move it
to `tickets/done/` until a future ticketing pass scopes and closes the remaining phases
(or a deliberate decision is made to stop pursuing them, in which case this ticket should
instead move to `tickets/backlogs/` per `docs/ai/ticket-lifecycle.md`'s backlog convention
— not silently closed as done).

## Test Summary

## Files Changed

## Completion Summary
