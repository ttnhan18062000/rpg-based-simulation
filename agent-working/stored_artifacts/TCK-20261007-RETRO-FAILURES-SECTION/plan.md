---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-RETRO-FAILURES-SECTION
artifact_type: plan
tags: [agent-monitoring, retro]
---

# Plan

## Design
- New `tools/agent-monitoring/retro_failures.py` (stdlib only), `render_section(runs, events, is_failed_run, agent_of) -> str`:
  - **Runs**: from the already deduped latest-per-execution runs passed in, keep `is_failed_run(r)` (generate_retro's `_is_gate_fail`); one line each: `run_id | final_status | workflow | start date`.
  - **Events**: every event with `status` in {failed, blocked}; group by `agent_of(e)` (`_normalize_agent`) then `reason_code or "unspecified"`; each group header has a count; each event is one line `run_id | seq | phase | summary` (summary squeezed to one line, cut at 160 chars).
  - **Recurring tests**: parse node ids `[\w/.-]+\.py::[\w\[\]:.-]+` (and `FAILED <name>` mentions) from failed/blocked event summaries; group by test; list those failing in >= 2 distinct tickets (`ticket_id` or a `TCK-` run_id) with the count and the ticket ids, most frequent first. The heading says the names are parsed from summaries (lossy by construction).
  - No failures at all: `_No non-DONE runs and no failed or blocked events in this period._`
- `generate_retro.py`: `_failures_section(runs, events)` (try/except -> None, like `_gates_section`), a `failures=None` keyword on `generate(...)`, rendered after `## Paths` and before `## Notes`; `main()` passes the period's `runs` and `events` (already scoped for week, `--days` and `--all`).
- Read-only: the module only reads the lists it is given.

## Not in this ticket
Known-failing-test baseline, suppression, a structured per-test field in the event schema, the Gates section.

## Edit overlap with the other two tickets
Touches `generate()` signature and `main()` wiring in generate_retro.py (a few lines). The Notes ticket touches `_write_report_preserving_notes` and the final `print(...)` line in main(). Order: execution-id (validate.py only), failures, notes; no shared lines.

## Question for the planner
Placement: after Paths (right before Notes) as planned, or near the top after "Gate Failure Breakdown", where the reader looks for failures first? Planned: after Paths, to leave the existing section order untouched.
