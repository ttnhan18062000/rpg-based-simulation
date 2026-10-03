---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-PHASE-AGENT-CASE-FOLD
phase: done
date: 2026-07-19
tags: []
---

# TCK-20260719-PHASE-AGENT-CASE-FOLD

## Title
Normalize phase/agent vocabulary casing in retro metrics

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Casing variants of phase/agent labels (e.g. Verify/verify/VERIFY, Implement/implement/IMPLEMENT, and 6 more phases) should be folded into one canonical bucket at read time, extending the existing normalization point in generate_retro.py. This closes a data-quality gap where fragmented vocabulary silently undercounts real failure rates when read naively — Review's true failure rate is 18.2%, the highest of any phase, but only visible after merging casing variants. A regression test proves the previously-undercounted rate is now computed correctly from raw fragmented input.

## Scope
- Extend generate_retro.py's compute_retro_metrics() aggregations (agent_status_distribution, spend_proxy_by_phase, spend_proxy_by_agent, gate counters) to normalize phase/agent casing variants
- Use vocabulary.py's canonical WORKFLOW_PHASES/WORKFLOW_AGENTS lists as the sole merge target (no second hardcoded list)
- Add regression test proving Review's real merged failure rate resolves to 18.2% from fragmented fixture input

## Out of Scope
- Modifying validate.py's compute_drift_report or its drift-visibility output — must remain unchanged, decoupled from retro merging; test_drift_report_frequency_table_non_canonical_phase_and_agent must keep passing unmodified
- Creating a second hardcoded phase/agent vocabulary list
- Implementing TCK-20260713-MONITORING-SQLITE-INDEX's derived-index migration (sibling ticket, confirmed not yet implemented; normalization proceeds directly in generate_retro.py instead of waiting)

## Acceptance Criteria
- [ ] All 8 affected phases' casing variants merged in compute_retro_metrics()'s aggregations (agent_status_distribution, spend_proxy_by_phase, spend_proxy_by_agent, gate counters) using vocabulary.py's canonical WORKFLOW_PHASES/WORKFLOW_AGENTS as merge target
- [ ] New regression test in tests/tools/test_generate_retro.py proving Review's real merged failure rate resolves to 18.2% from fragmented fixture input (Review/review/REVIEW mixed)
- [ ] validate.py's compute_drift_report drift-visibility output remains unchanged/unmodified (test_drift_report_frequency_table_non_canonical_phase_and_agent passes unmodified)
- [ ] test_canonical_vocabulary_single_sourced continues to pass (no second hardcoded vocabulary list introduced)

## Related Tickets
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260713-MONITORING-SQLITE-INDEX
- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/vocabulary.py
- tools/agent-monitoring/validate.py
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- Sequencing dependency on TCK-20260713-MONITORING-SQLITE-INDEX is resolved (confirmed status:active/phase:open, not yet implemented) — safe to proceed directly in generate_retro.py rather than wait for the derived-index migration

## Implementation Notes
Added `_canonicalize(value, canonical_set)` (generic casefold-match-or-passthrough) plus two thin
wrappers `_normalize_phase(e)`/`_normalize_agent(e)` to `generate_retro.py`, importing
`WORKFLOW_PHASES`/`WORKFLOW_AGENTS`/`infer_workflow` from `vocabulary.py` (the same shared module
object `record_events.py`/`validate.py` already import — `test_canonical_vocabulary_single_sourced`
confirms no second hardcoded list was introduced). Each normalizer resolves the event's workflow
via `infer_workflow(run_id)` and looks up a case-insensitive match within that workflow's own
canonical set — a value with no match (unrecognized workflow, or a genuinely non-canonical value
like a create-tickets `investigate:C1` prefix-family agent) passes through completely unchanged,
never invented into a fabricated canonical spelling.

Wired into `compute_retro_metrics()`'s three phase/agent-keyed aggregations: `agent_status_distribution`,
`spend_proxy_by_phase`, `spend_proxy_by_agent`. `_TAG_GATE_PHASE`'s existing `security` tag
comparison (`e.get("phase","").casefold() == gate_phase`) was left untouched — it already
casefold-compares both sides, so it was never actually broken by this bug.

**Scope decision made during implementation, not left implicit**: the ticket's own AC
("proving Review's real merged failure rate resolves to 18.2%") is not computable from anything
`compute_retro_metrics()` returned *before* this ticket — `agent_status_distribution` is keyed by
agent, not phase, and no phase-keyed ok/failed breakdown existed anywhere in the function's output.
Added a new `phase_status_distribution` key (identical shape to `agent_status_distribution`,
normalized the same way) as the minimum necessary addition to make the AC's own claim testable and
to actually close the "silently undercounts real failure rates" gap the ticket describes — a
casing fix alone, with no phase-level view to read it from, would not have made Review's true rate
visible to anyone. Rendered as a new "## Phase Status Distribution" Markdown section (same table
shape as Agent Status Distribution), and added to `test_compute_retro_metrics_returns_all_documented_keys`'s
expected key set. Verified this doesn't affect the Agent Ops Dashboard's typed API boundary
(`AgentMonitoringStats`/`get_agent_monitoring_stats()` map specific known keys explicitly, never
`**metrics` passthrough — confirmed by re-running `test_agent_ops_dashboard_stats.py`, 8/8 still
passing) — the new key is simply not yet consumed there, not a breaking change.

**Deliberately NOT touched**: `gate_counter` (the `Counter(_resolve_status(r) for r in gate_fails)`
at the top of `compute_retro_metrics()`) counts `final_status` values (`DOD_BLOCKED`,
`NEEDS_CHANGES`, legacy strings like `success`/`complete`/`done`), a completely different
vocabulary from phase/agent labels. `_resolve_status`'s own docstring explicitly states it does
**not** normalize legacy status-string spellings by design — that is a separate, already-decided
architectural boundary this ticket does not reopen. The Scope's mention of "gate counters" is
interpreted as referring to the phase-keyed ok/failed counts that determine a phase's gate-failure
rate (i.e. the new `phase_status_distribution`), not `gate_counter`'s `final_status` values.

**Real-data scope note**: the ticket's Request Summary cites "8 more phases"; direct measurement
against live `agent-monitoring/events.jsonl` found **9** implement-ticket phases with genuine
casing fragmentation (Finalize, Implement, Investigate, Parity, Plan, Review, Scope, Test, Verify —
`Architecture-Verify`/`Security-Review` show no drift). The fix normalizes against the full
`WORKFLOW_PHASES["implement-ticket"]` canonical set unconditionally, not a hardcoded list of
exactly 8, so this discrepancy has zero effect on correctness — noted for accuracy, not because it
required a different implementation.

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: implemented directly in the same pass as investigation, with staging
artifacts (`investigation.md`/`plan.md`/`test_plan.md`) written retroactively after implementation
and full test verification — same pattern as `TCK-20260719-COST-PROXY-WRITE-PATH` immediately
before this ticket in the same batch.

## Test Summary
- `python3 -m pytest tests/tools/test_generate_retro.py -q` — 26/26 passing (6 new: Review's 18.2%
  merged-failure-rate proof with a naive-vs-merged comparison, Markdown rendering of the new
  section, agent-casing-merge mechanism proof, spend-proxy-by-phase merge proof, unknown-workflow
  passthrough safety, create-tickets prefix-family non-collision).
- `python3 -m pytest tests/tools/test_validate_agent_monitoring.py -q` — 13/13 passing, **zero diff
  to `validate.py`** (confirmed via `git diff --stat`) — drift-visibility output genuinely
  unmodified, not just coincidentally still passing.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py -q` — 8/8 passing (confirms the
  new `phase_status_distribution` key doesn't break the dashboard's typed API boundary).
- `python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard or generate_retro or validate_agent"` — 162/162 passing.

## Files Changed
- tools/agent-monitoring/generate_retro.py (`_canonicalize`/`_normalize_phase`/`_normalize_agent`
  helpers, wired into 3 existing aggregations, new `phase_status_distribution` key + rendering)
- tests/tools/test_generate_retro.py (1 test updated for the new key, 6 new tests)
- docs/parity_ledger/infrastructure.yaml (new entry INFRA-283)

## Completion Summary
Phase/agent casing variants (`Verify`/`verify`/`VERIFY` and 8 more phases, confirmed via direct
measurement against live `agent-monitoring/events.jsonl`) now merge into their canonical spelling
at read time in `generate_retro.py::compute_retro_metrics()`, sourced from `vocabulary.py`'s
existing `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` — no second hardcoded vocabulary list. A new
`phase_status_distribution` output (and matching "## Phase Status Distribution" report section)
was added since no phase-keyed ok/failed breakdown existed anywhere before, making the ticket's own
"Review's real failure rate" claim genuinely unverifiable without it — proven correct by a
regression test showing raw fragmented input (41 failed/184 ok split across 3 casing variants)
correctly merges to the real 18.2% rate, versus a naive single-casing-variant read that would show
16.7%. `validate.py`'s drift-visibility output is confirmed genuinely untouched (zero diff), and
`implement-epic`'s not-yet-implemented `TCK-20260713-MONITORING-SQLITE-INDEX` sequencing dependency
was re-confirmed still unimplemented, so proceeding directly in `generate_retro.py` was correct.
