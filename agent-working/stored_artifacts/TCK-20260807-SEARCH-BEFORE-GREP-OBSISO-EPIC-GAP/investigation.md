---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP
artifact_type: investigation
tags: [agent-monitoring, process-improvement]
---

# Investigation — TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP

## Docs Requiring Update

None. This ticket updates `.claude/agents/investigator.md`, which is outside `docs/` (agent
definition files are not part of the docs/ doc-staleness contract).

## Real tool-call sequence for both flagged pairs (`agent-monitoring/tools.jsonl`)

Cross-checked `tools.jsonl`'s own `phase` field per row against `events.jsonl`'s phase-per-seq —
**fully self-consistent, no seq/phase attribution bug** (confirmed by direct comparison against
`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT` as a control: both runs show tools.jsonl's own `phase` field
matching events.jsonl exactly at every seq). The one surface anomaly noticed (an `Agent` tool row
with `input_summary` reading "Plan TCK-20260702-OBSISO-TRACE-ASYNC" while correctly tagged
`phase: Investigate`) is a cosmetic `description`-text mismatch on that one Agent dispatch, not a
seq-misattribution — `_is_search_or_graphify_call`/`_is_grep_call` only inspect `tool`/
`input_summary` for Read/Write/Edit/Bash/mcp rows, never `Agent` rows, so it has zero effect on the
compliance computation. Investigated and ruled out as a false lead.

`TCK-20260702-OBSISO-TRACE-ASYNC`'s real Investigate-phase (seq 2) tool list: reads the ticket,
reads 2 staging artifacts, then 2 `grep`/`ls | grep` calls, ~7 source-file reads, 4 `sed` calls,
writes `investigation.md`. **Zero `search_docs`/`graphify` calls anywhere in this window.**

`TCK-20260702-OBSISO-BROKER-CONFIG`'s real Investigate-phase (seq 2): reads the ticket + 2 staging
artifacts, then a `grep` on `docs/parity_ledger/infrastructure.yaml`, ~7 source-file reads, writes
`investigation.md`/`test_plan.md`. **Zero `search_docs`/`graphify` calls anywhere in this window.**

`TCK-20260702-OBSISO-ISOLATION-PROOF` (the sibling epic child that did NOT get flagged): its own
Investigate-phase window (seq 1 — this run's Scope resume-branch used seq 1, one lower than the
other two, an unrelated numbering-offset artifact of when it was created) opens with 2
`search_docs` calls and 1 `graphify query` call **before** any grep, then ~35 source reads/greps
against a genuinely different subsystem (perf/benchmark: hardware-class bands,
`perf_baseline_policy.md`, `bench_harness.py`) — correctly compliant.

## Shared cause: confirmed, real, and specific to the 2 flagged tickets

Both `TRACE-ASYNC` and `BROKER-CONFIG`'s own `search_docs`/`graphify` calls DID happen — but during
**Scope** (seq 1), not Investigate (seq 2): `TRACE-ASYNC` seq 1 shows 2 `search_docs` calls
("DecisionTraceWriter write_trace hot path file IO", "observability hot path safety contract
BoundedObservabilityQueue QueueDrainWorker") plus 2 `graphify query` calls, all preceding its own
first grep. `BROKER-CONFIG` seq 1 shows the same pattern (1 `search_docs`, 1 `graphify query`,
before its own first grep). Both are genuinely topic-relevant to their respective tickets, not
generic epic-level boilerplate — meaning whoever scoped these 2 child tickets already did the real
research up front, during Scope, then Investigate's own agent proceeded straight to source-level
grep/read without repeating a fresh `search_docs`/`graphify` call scoped to its own phase window.

Both share the same parent epic (`tickets/done/obs-isolation/TCK-20260702-OBSISO-EPIC.md`,
confirmed via its own `## Related Tickets`) and the same tightly-coupled observability subsystem
(`DecisionTraceWriter`, `BoundedObservabilityQueue`, `QueueDrainWorker`, broker/stream wiring) —
`ISOLATION-PROOF`, by contrast, targets a genuinely distinct concern (performance/benchmark
methodology for the same subsystem) that Scope's own research didn't already cover, so its
Investigate phase needed and made a fresh search call.

**Root cause is not a broken shared prompt/template** — `.claude/agents/investigator.md` was read
in full and contains **zero mention of `search_docs`, `graphify`, or CLAUDE.md's search-before-grep
hard rule anywhere in its own persistent definition** (confirmed via direct grep: no matches).
Investigator currently relies entirely on CLAUDE.md's global context being followed implicitly —
which this exact evidence shows is not reliable, matching this session's own earlier, unrelated
finding for the sidecar-write gap (`TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`): an
instruction that lives only in global project context, with no explicit callout in the
specific agent's own definition, gets skipped under real task pressure — here, specifically when
Scope-phase research already substantially covered the topic, making a fresh Investigate-phase
call feel redundant to the agent even though it's still required by the hard rule.
