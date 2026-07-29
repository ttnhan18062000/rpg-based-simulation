---
status: active
layer: ai
authority: P2
audience: developer
date: 2026-07-29
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval, Phase 5

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md`'s Phase 5 only.

This supersedes `ticket_plan_structure_phase4.md` for this batch — Phase 4 is now
`DONE` (`TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`, `TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK`,
`TCK-20260729-RETRIEVAL-RETRO-VIEWS`), giving this phase a real, tested retrieval-event schema
and dashboard views to build advisory packets on top of.

## Scope this batch to Phase 5 of the source doc's "Sequenced Future Epic" only

Phase 5 is **"Shadow context packets — advisory packets for selected workflows/phases; evaluate
against baseline and review evidence."** This is the FIRST phase in the sequence that touches
real `.claude/workflows/*.js` files — every prior phase (3, 4) was explicitly forbidden from any
workflow-file wiring; that constraint lifts here, but only in one narrow, load-bearing way:
**advisory/shadow mode only, never blocking, never a gate.** The Maturity banner still applies in
full: this batch does **not** authorize promoting shadow packets to default/mandatory workflow
behavior — that promotion is an explicit future decision gated on the source doc's own "Shadow
evaluation and approval gate" criteria (six conditions, quoted below), none of which can be
evaluated yet since this phase is what generates the evidence those criteria are checked against.

**Ground every ticket in this batch in the following confirmed facts — do not re-derive or
silently contradict them:**

- `tools/context_packet_assembler.py` (Phase 3, `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) already
  assembles a real `ContextPacket` from fused/cached retrieval results — this phase's shadow
  packets should call that assembler, not reimplement packet construction.
- `tools/retrieval_events.py` (Phase 4, `TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`) already
  defines the versioned, `run_id`-scoped retrieval-event schema and `emit_retrieval_event()` —
  shadow-packet requests/outcomes should emit through this existing schema/writer path, extended
  additively if new fields are genuinely needed (never a new writer mechanism, per Phase 4's own
  precedent), not a new event family built from scratch.
- **CONFIRMED GAP, still current:** `runs.jsonl`/`events.jsonl` do **not** carry `execution_id` or
  `provider` fields (re-verified: neither string appears in `record_run.py` or `record_events.py`
  as of this phase's scoping). The idea doc's own Phase 5 text says "Each provider adapter must
  pass an execution identity, provider, role, and phase to the shared retrieval boundary" — this
  assumes infrastructure Phase 4 explicitly deferred as a "Phase 4b follow-on." **Do NOT silently
  add `execution_id`/`provider` fields to `runs.jsonl`/`events.jsonl` to satisfy this** — that is
  still a `runs.jsonl`/`events.jsonl` schema-extension decision no phase so far has made. If a
  ticket's investigation finds the shadow-packet request genuinely cannot proceed without it
  (e.g. multi-provider comparison is a hard Phase 5 requirement), flag this plainly as a
  cross-phase blocker/risk in the ticket rather than inventing the field — this may mean Phase 5
  itself needs its own "Phase 4b" prerequisite ticket, which is a legitimate investigation finding,
  not a failure to scope.
- `docs/parity_ledger/infrastructure.yaml` `INFRA-293` through `INFRA-298` are the 6 real, working
  modules this phase builds on top of — reference, don't rebuild.

**RESOLVED (do not re-litigate in this batch): "advisory" and "shadow" are structural
requirements, not vague framing.** A shadow-packet call site must:
1. Never block, delay past a fail-open timeout, or change any gate's PASS/FAIL/BLOCKED outcome —
   if the packet builder errors or is slow, the wrapped workflow phase must proceed exactly as it
   would have with no packet requested at all.
2. Never be read, consumed, or acted on by the agent performing the wrapped phase's real work —
   the packet is recorded for later evaluation only, not injected into any agent prompt in this
   phase. (Injecting it into a real agent's context, even non-blockingly, would already be
   "adoption," which is explicitly Phase 6, not Phase 5.)
3. Be trivially and safely disable-able (a single flag, env var, or config toggle) without
   requiring a code revert, so any unexpected cost/behavior can be turned off immediately.

**This batch should produce standard-tier ticket(s) whose deliverable is: (a) a `ContextRequest`
→ shadow-packet-build call site inserted into 1-2 SPECIFIC, NAMED phases of
`implement-ticket.js` (the ticket's own investigation must pick which phase(s) — e.g. Scope or
Investigate are natural candidates per the idea doc's own scenario table — and justify the
choice against real evidence, not guess), wired so it only ever records the packet request/outcome
via the Phase 4 event schema and NEVER surfaces the packet to the agent performing that phase's
work, (b) recording of the adequacy-verdict-adjacent outcome fields already defined in
`RETRIEVAL_EVENT_FIELDS` (reuse, do not invent a second `adequacy_verdict`-shaped field), and
(c) a baseline-comparison query/report extending `generate_retro.py` (Phase 4's own precedent)
showing shadow-packet outcomes alongside the existing baseline metrics — not yet a promotion
recommendation, just the comparison data the future approval-gate decision will need.**

**Cover these source-doc items, each traceable to a concrete deliverable:**

1. **Shadow packet call site, advisory-only** — one or two specific `implement-ticket.js` phase
   insertion points (chosen by investigation, justified against the idea doc's scenario table),
   wrapped so a build failure/timeout never changes wrapped-phase behavior, and the packet is
   never read by the agent doing that phase's work.
2. **Request/outcome recording through the existing event schema** — extend
   `tools/retrieval_events.py`'s field set additively if a genuinely new field is needed (e.g. a
   `shadow_mode: true` marker distinguishing these from Phase 4's own test/manual-invocation
   events), reusing `emit_retrieval_event()`'s existing writer path, never a new mechanism.
3. **Baseline-comparison reporting** — extend `generate_retro.py` (mirroring Phase 4's own
   `compute_retrieval_metrics()` precedent) with a query comparing shadow-packet-covered phases
   against the existing baseline metrics from `TCK-20260728-RETRIEVAL-BASELINE-METRICS`, fixture-
   tested, not validated only against live data (near-zero real volume is expected and acceptable,
   same as every prior phase).

**Do NOT ticket in this batch** (still gated behind this phase's own evidence, per the doc's
Sequenced Future Epic and its explicit "Shadow evaluation and approval gate" section):
- Any change to a gate's PASS/FAIL/BLOCKED outcome, or any packet content surfaced to an agent's
  actual prompt/context — that is Phase 6 (Selective workflow adoption), not this phase.
- A formal promotion-readiness recommendation or scorecard against the six approval-gate criteria
  quoted below — this phase only generates the comparison data; judging it against the criteria is
  future work once real evidence volume exists.
- Any `execution_id`/`provider` field addition to `runs.jsonl`/`events.jsonl`, unless a ticket's
  own investigation concludes this phase is hard-blocked without it — in which case ticket that
  blocker explicitly rather than silently adding the fields.
- Resolving Open Decision 5 (sample size/thresholds for promotion) or Open Decision 6 (MCP tool vs
  provider-adapter-library exposure) — both remain explicitly deferred.
- Any external vector/graph database, hosted RAG, or non-SQLite/non-JSONL storage.
- Wiring into `implement-epic.js` or `create-tickets.js` — scope this batch to `implement-ticket.js`
  only; those two workflows' phase structures are materially different and out of scope here.
- A live Codex pilot execution or any change enabling `CODEX_REPLAY_PARITY_LIVE_CONSENT`.

**Approval-gate criteria (quoted verbatim from the idea doc, for context only — NOT this phase's
job to satisfy or score against):**
> - authoritative-source recall is at least the agreed baseline;
> - no material increase in missed contracts, test/gate failures, or review rework attributable to
>   missing context;
> - a meaningful, pre-declared reduction in median injected context tokens or follow-up retrieval
>   burden;
> - cache correctness: stale packets are rejected and source-hash checks pass;
> - provider parity: comparable request/packet/outcome events are emitted for every enabled
>   provider; and
> - privacy boundary: monitoring contains no raw prompts, raw retrieved source text, or sensitive
>   tool payloads.

If investigation reveals Phase 5 cannot be meaningfully scoped without first resolving the
`execution_id`/`provider` gap, or without a real Codex pilot to evaluate "provider parity"
criterion above, say so plainly as a risk/open-question in the ticket — do not silently guess an
answer or quietly narrow "advisory shadow packet" into something that secretly influences a gate.
