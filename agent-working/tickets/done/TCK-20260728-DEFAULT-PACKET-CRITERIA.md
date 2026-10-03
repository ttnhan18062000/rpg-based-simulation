---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-DEFAULT-PACKET-CRITERIA
phase: done
date: 2026-07-28
tags: [ai, agent-monitoring]
---

# TCK-20260728-DEFAULT-PACKET-CRITERIA

## Title
Define Default-Packet Scenario Criteria and Initial Token Budgets

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The author wants a decision document resolving Open Decision 1: which scenarios and phases justify a default context packet, and what their initial token budgets should be — grounded in the actual baseline measurements produced by TCK-20260728-RETRIEVAL-BASELINE-METRICS rather than a fresh guess. This matters because context_tokens is platform-blocked/unavailable, so the doc must ground any budget guidance in proxy signals from real corpus data instead of inventing a measured number.

## Scope
- Author a decision document addressing each of the 5 named scenarios (Small bugfix, Ticket implementation, Code review, Architecture-planning, Incident-monitoring investigation) with a yes/no/deferred verdict on "justifies a default context packet," each citing a specific field from tools/agent-monitoring/retrieval_baseline_metrics.py's real output (search_count.per_run, gate_outcome.status_breakdown, duration.rows[].flag).
- Resolve Open Decision 1, updating its status in the idea doc (or a linked decision-doc file) from open to resolved with rationale traceable to TCK-20260728-RETRIEVAL-BASELINE-METRICS's real corpus numbers.
- State initial budgets as directional/relative sizing (small/medium/large tiers) with a named proxy basis, since context_tokens is unavailable.
- Explicitly note as a scoped limitation that no existing tool aggregates agent-monitoring/events.jsonl's phase+ts fields into per-phase (vs per-run) breakdowns, and state whether that gap blocks any part of the decision or is deferred.

## Out of Scope
- Asserting any measured numeric token-budget figure — context_tokens is platform-unavailable per docs/agent-monitoring/schema.md and the baseline tool's own output; the doc must not invent one.
- Using duration.rows[].flag=='pause-contaminated' data as a clean per-scenario cost signal without stating that caveat.
- Silently resolving Open Decision 5 (promotion sample-size/thresholds) — a related but distinct question.
- Any src/ or tools/ implementation.
- Phase 3 retrieval/cache implementation.
- Phase 4 observability events/dashboard work.
- Phase 5-6 shadow packets or workflow adoption.
- Force-resolving any Open Decision other than Decision 1.

## Acceptance Criteria
- [x] Decision doc addresses each of the 5 named scenarios with a yes/no/deferred verdict on "justifies a default context packet," each citing a specific field from retrieval_baseline_metrics.py's real output (search_count.per_run, gate_outcome.status_breakdown, duration.rows[].flag).
- [x] Doc explicitly states context_tokens is "unavailable" (citing schema.md and the baseline tool's own output) and does not assert any measured numeric token-budget figure; states initial budgets as directional/relative sizing (small/medium/large tiers) with proxy basis named.
- [x] Doc updates Open Decision 1's status (in the idea doc or a linked decision-doc file) from open to resolved, with rationale traceable to RETRIEVAL-BASELINE-METRICS's real corpus numbers.
- [x] Doc explicitly notes as a scoped limitation that no existing tool aggregates events.jsonl's phase+ts fields into per-phase breakdowns, and states whether that gap blocks any part of the decision or is deferred.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-EVAL-FIXTURE-REPAIR

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/investigation.md
- stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/plan.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- tools/agent-monitoring/retrieval_baseline_metrics.py
- tools/agent-monitoring/vocabulary.py
- .claude/workflows/implement-ticket.js
- stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/investigation.md
- stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/plan.md
- tickets/done/TCK-20260728-RETRIEVAL-BASELINE-METRICS.md
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/done/TCK-20260728-PHASE0-PREREQ-CONFIRMATION.md
- agent-monitoring/events.jsonl
- expected: docs/ai/default_packet_scenarios_decision.md

## Assumptions / Open Questions
- context_tokens is confirmed platform-blocked/unavailable in 3 independent places (docs/agent-monitoring/schema.md, cost_proxy.py docstring, retrieval_baseline_metrics.py output) — the doc must ground "token budgets" in proxy signals, never a fabricated measured number.
- retrieval_baseline_metrics.py aggregates search_count/duration per whole run_id only, with no per-phase breakdown, despite events.jsonl carrying phase+ts fields — phase-level budget precision is unavailable today and must be stated as a scoped limitation, not silently absorbed.
- duration.rows[].flag is "pause-contaminated" in all current data — this caveat must be carried wherever duration is cited as a cost signal.
- Tier is hotfix per explicit investigation recommendation: this ticket mirrors TCK-20260728-PHASE0-PREREQ-CONFIRMATION's precedent (single decision-doc deliverable citing already-produced evidence, no new code/tests, self-evident intent, no architecture change).

## Implementation Notes
Authored `docs/ai/default_packet_scenarios_decision.md`, resolving Open Decision 1 from the epic's
idea doc. Ran `python3 tools/agent-monitoring/retrieval_baseline_metrics.py` (stdout only, no
`--output` used, nothing to clean up) against the live corpus (2026-07-29): 721 `runs.jsonl`
records, `gate_outcome.status_breakdown` shows `DONE: 622` dominant, `NEEDS_CHANGES: 4`,
`BLOCKED: 1`; `search_count.total = 1694` across 118 ticket-scoped `run_id`s (median per_run = 3,
excluding the `unattributed` interactive bucket of 852); highest-volume tickets were
`TCK-20260614-WORLDMOD-PARAMS: 143`, `TCK-20260623-FIX-WORLDASSEMBLY: 69`,
`TCK-20260630-SIMQ-WIRE-KERNEL: 38`; lowest were hotfix-shaped tickets at 1-2 (53 of 118 runs ≤2);
`duration.rows[].flag` is `"pause-contaminated"` on all 167 rows with no exception.

Verdicts: Small bugfix (Yes, Small tier) and Ticket implementation (Yes, Medium tier) and
Architecture-planning (Yes, Large tier) are grounded in `search_count.per_run` volume clusters.
Code review and Incident-monitoring investigation are Deferred — confirmed via direct inspection
of `retrieval_baseline_metrics.py` that `build_search_count_section()` and
`build_duration_section()` both aggregate at `run_id` granularity only; no function reads
`events.jsonl`'s `phase`/`ts` fields at all in this tool. Confirmed `events.jsonl` genuinely
carries both fields via a live tail of the file. Confirmed `context_tokens` unavailability by
reading `docs/agent-monitoring/schema.md`'s "What is not recorded" section verbatim and comparing
it to the baseline tool's own `build_context_tokens_section()` output — both cite the same fact
independently.

No deviation from the ticket's plan/scope. No code, no `src/`/`tools/` changes. Updated the epic
ticket's Open Questions section to mark Open Decision 1 RESOLVED, in the same style as the existing
Open Decision 2/3 entries (read both as formatting templates before editing).

## Test Summary
Documentation-only ticket — no code changed, no tests run or added. Verification consisted of
running the read-only baseline tool and cross-checking its live JSON output and
`agent-monitoring/events.jsonl`'s raw content directly, both cited above.

## Files Changed
- docs/ai/default_packet_scenarios_decision.md (new)
- tickets/inprogress/TCK-20260728-DEFAULT-PACKET-CRITERIA.md (this ticket)
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md (Open Decision 1 marked RESOLVED)

## Completion Summary
Open Decision 1 is resolved: 3 of 5 named scenarios (Small bugfix, Ticket implementation,
Architecture-planning) justify a default context packet at directional Small/Medium/Large tiers
grounded in real `search_count.per_run` proxy data; Code review and Incident-monitoring
investigation are deferred pending per-phase event aggregation tooling that does not exist today.
No numeric token-budget figure was asserted anywhere, since `context_tokens` is confirmed
platform-unavailable in 3 independent places. The scoped per-phase aggregation gap is stated
explicitly and does not silently resolve Open Decision 5.
