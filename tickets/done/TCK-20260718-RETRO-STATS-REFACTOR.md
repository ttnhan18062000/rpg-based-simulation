---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-RETRO-STATS-REFACTOR
phase: done
date: 2026-07-18
tags: [agent-monitoring, reporting, data-quality]
---

# TCK-20260718-RETRO-STATS-REFACTOR

## Title
Refactor generate_retro.py's metric computation into a reusable, typed function

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
`tools/agent-monitoring/generate_retro.py::generate()` (lines 168-434) already computes a rich set of agent-monitoring aggregate metrics — run summary (total/DONE/gate-failure counts), gate failure breakdown, reason-code breakdown, tag breakdown (subsystem-topic and process-skill-signal), tier distribution (count/scoped/DONE/rate), agent status distribution, spend-proxy (cost_proxy_score by phase/agent), summary-quality diagnostics, and slow-run detection (>30min) — but computes and renders all of it inline as `lines.append(...)` Markdown strings in one ~270-line function. Nothing outside this script can consume the computed numbers as data. This ticket extracts the computation into a separate, typed/structured-returning function that the existing Markdown renderer calls, so a future consumer (the sibling ticket TCK-20260718-AGENTOPS-STATS-API) can call the same computation and get JSON instead of Markdown — without duplicating the metric logic a second time.

## Scope
- Extract `generate()`'s computation (everything before the `lines = []` / `lines.append(...)` block starts, plus the per-section value calculations currently interleaved with `lines.append` calls) into a new function returning a structured result (a dataclass or TypedDict — pick whichever fits this module's existing style better, document the choice) containing every metric currently rendered: run_summary (total, done_count, gate_fail_count, avg_duration_s, avg_agents, total_agent_calls), gate_failure_breakdown, reason_code_breakdown, tag_breakdown_subsystem, tag_breakdown_skill, tier_distribution, agent_status_distribution, spend_proxy_by_phase, spend_proxy_by_agent, summary_quality, slow_runs.
- `generate()` itself becomes a thin function: call the new computation function, then render its result to the exact same Markdown structure/text as today.
- `tools/tag_report.py`'s `build_json_report()`/`print_report()` split (same computation, two output shapes) is the direct precedent for this refactor's shape — follow it.
- Existing callers of `generate()` (the CLI in this file's `main()`, and the `agent-monitoring-retro` skill) must continue working with zero behavior change.

## Out of Scope
- Any change to the actual Markdown text/structure `generate()` produces — this is a pure internal refactor, not a redesign of the retro report.
- Building the new JSON/API-facing consumer itself — that is TCK-20260718-AGENTOPS-STATS-API's scope, which depends on this ticket.
- Any change to `tools/agent-monitoring/validate.py`'s legacy-schema tolerance or the retro report's period-selection logic (`--days`/`--all`/`--week`) — reuse as-is.

## Acceptance Criteria
- [x] A new function exists returning all metrics `generate()` currently computes, as structured data (not strings).
- [x] `generate()` is refactored to call the new function and render its result — no metric computation logic remains duplicated between the two.
- [x] Proof that CLI output is unchanged: `git stash` the refactor, run `python3 tools/agent-monitoring/generate_retro.py --all` and save the output, `git stash pop`, run the same command again, diff the two outputs — byte-identical (or the diff is explained and justified, not silently accepted).
- [x] Existing tests for `generate_retro.py` (if any exist — check `tests/tools/`) still pass; new tests cover the extracted computation function directly.
- [x] The `agent-monitoring-retro` skill still produces the same report shape when invoked (skill just invokes the unchanged CLI; validated by the byte-identical proof above).

## Related Tickets
- TCK-20260718-AGENTOPS-STATS-API (depends on this ticket)
- TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (parent epic)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_stats_board.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/tag_report.py (precedent for the computation/rendering split)

## Assumptions / Open Questions
- Whether to use a `dataclass` or `TypedDict` for the structured result is an implementation decision — check whether `generate_retro.py` or its sibling `tools/agent-monitoring/*.py` modules already lean one way.

## Implementation Notes
Extracted `generate_retro.py::generate()`'s ~270-line inline computation into a new
`compute_retro_metrics(runs, events, tickets_root=None)` function returning a plain `dict`
(mirroring `tag_report.py::build_json_report()`'s precedent — no dataclass/TypedDict introduced).
`generate()` keeps its exact original signature and is now a thin renderer: call
`compute_retro_metrics()`, then build the same Markdown `lines` structure as before, reading from
the returned dict instead of local variables.

Proved zero behavior change via `git stash`: ran `python3 tools/agent-monitoring/generate_retro.py
--all` against the real repo data before the refactor (stashed) and after (popped) — both stdout
and the written `agent-monitoring/retro/RETRO-ALL.md` file are byte-identical (`diff` clean both
times).

Deviation (self-flagged, per this session's established precedent): this fork has no Agent-tool
subagent access, so Scope/Investigate/Plan/Review/Implement/Architecture-Verify/Test/Parity/Verify
were all performed directly (Read/Edit/Bash/Write) rather than via the specialized agent roles
`implement-ticket.js` normally spawns. Architecture-Verify used the real
`tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` script directly
(zero findings on the two changed files) rather than an independent architecture-reviewer agent's
judgment call on top of it.

## Test Summary
`python3 -m pytest tests/tools/test_generate_retro.py -q` — 20/20 passing (15 pre-existing,
unmodified, + 5 new tests covering `compute_retro_metrics()` directly: documented-keys shape,
run_summary correctness against a fixture, pure-function/no-side-effects proof, tag-breakdown
cross-check against `generate()`'s rendered output, skill-tag `gate_hits=None` when no gate
exists). `tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` — zero
findings. `tools/parity_ledger_scan.py::find_p0_intersection()` — no P0 intersection, confirming
Parity is genuinely skip-eligible (no `src/` file touched, behavior_changed=false, proven above).

## Files Changed
- tools/agent-monitoring/generate_retro.py (extracted `compute_retro_metrics()`; `generate()`
  rewritten as a thin renderer over it — signature/behavior unchanged, proven byte-identical)
- tests/tools/test_generate_retro.py (5 new tests for `compute_retro_metrics()`; import line
  updated to also import the new function)

## Completion Summary
`generate_retro.py`'s metric computation is now available as a reusable, pure function
(`compute_retro_metrics()`) returning structured data, decoupled from the Markdown-rendering
concern that previously made it Markdown-only. The existing CLI/`agent-monitoring-retro` skill
behavior is provably unchanged (byte-identical stash-comparison proof). This unblocks the sibling
ticket `TCK-20260718-AGENTOPS-STATS-API`, which will import and call this function to expose the
same metrics as a typed JSON API endpoint, without duplicating any computation logic.
