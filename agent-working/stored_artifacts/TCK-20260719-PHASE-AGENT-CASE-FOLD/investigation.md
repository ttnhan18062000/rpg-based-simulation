---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-PHASE-AGENT-CASE-FOLD
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260719-PHASE-AGENT-CASE-FOLD

## Current Behavior

`tools/agent-monitoring/generate_retro.py::compute_retro_metrics()` aggregates `phase`/`agent`
directly off raw event field values with no casefold, in three places (before this ticket):
`agent_status_distribution` (`agent_stats[e.get("agent", "?")][e.get("status", "?")] += 1`),
`spend_proxy_by_phase`/`spend_proxy_by_agent` (`phase_scores[e.get("phase", "?")]`/
`agent_scores[e.get("agent", "?")]`). `validate.py::compute_drift_report()` separately, correctly,
counts casing variants as distinct drift entries (by design, per its own test
`test_drift_report_frequency_table_non_canonical_phase_and_agent`) — the two modules serve
different purposes (drift *visibility* vs. accurate *aggregation*) and must stay decoupled.

Confirmed by direct measurement against live `agent-monitoring/events.jsonl` (not assumed): 9
implement-ticket phases show genuine casing fragmentation — `Finalize`/`finalize`/`FINALIZE`,
`Implement`/`implement`/`IMPLEMENT`, `Investigate`/`investigate`/`INVESTIGATE`,
`Parity`/`parity`/`PARITY`, `Plan`/`plan`/`PLAN`, `Review`/`review`, `Scope`/`scope`,
`Test`/`test`/`TEST`, `Verify`/`verify`. `Architecture-Verify`/`Security-Review` show zero drift.
Agent-name casing was also checked: **zero drift found** for any implement-ticket agent literal —
all already lowercase-consistent in real data. The fix is written generically for both fields
regardless (per the ticket's stated Scope), but only phase-side fragmentation exists today.

`compute_retro_metrics()`'s return dict, before this ticket, had **no phase-keyed ok/failed/
blocked/skipped breakdown at all** — only `agent_status_distribution` (agent-keyed). This means the
ticket's own claim ("Review's true failure rate is 18.2%... only visible after merging casing
variants") was not actually computable from this function's output at all, casing aside — a real
gap beyond pure normalization.

## Mechanics/Engine Constraints

None — agent-monitoring is orchestration/observability tooling, not simulation gameplay.

## Parity Ledger Overlap

No `src/` file touched and no on-disk schema change (`events.jsonl`/`runs.jsonl` unmodified) — but
this IS a real, observable behavior change (the retro report's rendered output changes: a new
"## Phase Status Distribution" section, and previously-fragmented percentages now merge correctly)
per `implement-ticket.js`'s Parity-skip condition (`parityNoSrcChange && !behavior_changed` —
`behavior_changed=true` here means the full parity path runs regardless of the `src/`-touch check).
`INFRA-281`/`INFRA-282` (the two immediately-preceding tickets in this same batch) are the direct
precedent: pure orchestration/tooling behavior changes, no Mechanics Bible chapter, still get a
`docs/parity_ledger/infrastructure.yaml` entry.

## Prior Work

`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` built `vocabulary.py`'s canonical
`WORKFLOW_PHASES`/`WORKFLOW_AGENTS` and `validate.py`'s drift-visibility report — this ticket
extends the read-time consumer side, reusing that same canonical source, never duplicating it.
`TCK-20260713-MONITORING-SQLITE-INDEX` (sibling ticket, `tickets/todos/agent-monitoring-derived-index/`)
is confirmed still `status: active`/`phase: open`, not implemented — the proposal's own carried-
forward sequencing note says normalization should extend `generate_retro.py` directly now, and
defer to the derived index only once it lands. Re-confirmed true at investigation time.

## Risks and Open Questions

None outstanding. The one real design decision (adding `phase_status_distribution` since nothing
phase-keyed existed to prove the AC against) is made and documented in `plan.md`/the ticket's own
Implementation Notes, not left open.

## Anti-Drift Hazards

- Normalization must be workflow-aware (via `infer_workflow(run_id)`), not a single global
  casefold-to-nearest-match — different workflows have disjoint phase vocabularies (e.g.
  `create-tickets`' `Comprehend` vs. `implement-ticket`'s phases), and a global match risks
  cross-workflow collisions.
- Must never mutate `validate.py`'s drift-report output or its test
  (`test_drift_report_frequency_table_non_canonical_phase_and_agent`) — the two are deliberately
  decoupled: `validate.py` should keep showing casing variants as distinct (drift visibility),
  `generate_retro.py` should merge them (accurate aggregation).
- Must reuse `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`/`infer_workflow` directly (same
  imported module object) — never redefine or copy the canonical sets a second time
  (`test_canonical_vocabulary_single_sourced` guards this).
