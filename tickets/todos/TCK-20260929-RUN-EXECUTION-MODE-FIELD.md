---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260929-RUN-EXECUTION-MODE-FIELD
phase: open
date: 2026-09-29
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20260929-RUN-EXECUTION-MODE-FIELD

## Title
Record whether a run went through the pipeline or was closed by hand (`execution_mode` on runs.jsonl), and split the retro on it

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
A ticket can be closed two ways. The `implement-ticket` pipeline runs its phases live and records
timing and tool calls as it goes. A hand-orchestrating session does the work directly and then
writes a run record after the fact with `tools/agent-monitoring/record_hand_orchestrated_closure.py`.
That script labels its record `workflow: implement-ticket` by default (line 280), so the retro
counts both as the same thing. `agent-monitoring/retro/RETRO-2026-W40.md` Notes measured that
since ~2026-09-06 about 94% of "implement-ticket" runs are hand closures with zero duration and no
tool attribution. Every pipeline metric in the retro (duration, gate failures by agent, reviewer
coverage) is therefore mostly measuring runs that never went through the pipeline, and the report
doesn't say so.

On 2026-09-29 the user chose option B: keep `workflow` unchanged and add a separate field,
`execution_mode` (`pipeline` | `hand`), so existing readers of `workflow` keep working and the retro
can split the two populations. This is NOT a gate on hand closure and must not discourage it
(agent-tooling checks stay proportionate). It only stops the report from blending two different
things.

## Scope
- **Consumer audit first (acceptance blocker, record the result in Implementation Notes).** List
  every reader of the run `workflow` field and confirm none breaks or changes meaning. Known
  readers, found while drafting (not yet exhaustive):
  - `tools/agent-monitoring/build_index.py` (lines 114, 139, 170)
  - `tools/agent-monitoring/retro_nudge_hook.py:44`
  - `tools/gate_checks/tool_call_count_mismatch_check.py:88`
  - `src/api/agent_ops_dashboard/ingest.py:394`
  - `tools/agent-monitoring/validate.py:123` (`RUN_REQUIRED_FIELDS_FOR_DRIFT`)
  - `vocabulary.infer_workflow(run_id)` (used by `validate.py`/`generate_retro.py`), which infers
    the workflow from the run_id prefix rather than reading the field
- Add optional `execution_mode` to the run record. `record_run.py` must accept it; it is not added
  to `REQUIRED`, because older rows never have it.
- `record_hand_orchestrated_closure.py` writes `execution_mode: "hand"` on every run it records.
- Every pipeline run-writer writes `execution_mode: "pipeline"`: the `writeMonitoring` run-record
  command in `.claude/workflows/implement-ticket.js`, `implement-epic.js`, `create-tickets.js` and
  `simq-audit.js`. That covers both the formal runtime and the hand-translated skill path, since
  both execute the same record_run command text. Update each workflow's `SKILL.md` wherever it
  restates that command.
- `tools/agent-monitoring/generate_retro.py`: the `## Run Summary` section reports pipeline and
  hand runs separately (counts, and avg duration for pipeline only). Rows with no
  `execution_mode` field are shown as their own "unlabelled (pre-field)" group, never silently
  merged into either population.
- Document the field in `docs/agent-monitoring/schema.md` (runs table), including the legacy
  meaning of its absence.
- Tests for each writer and for the retro split.

## Out of Scope
- Changing the `workflow` value of any writer (option A was not chosen).
- Backfilling or rewriting historical rows. This follows the precedent from
  `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP` and
  `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE`: an honestly-labelled
  historical gap beats fabricated retroactive certainty.
- Inferring `hand` for legacy rows from the zero-duration / empty-tool-stats signature. It could be
  shown as a separate, clearly-labelled heuristic note later, but is not built here.
- Any gate, ratchet, or blocking check on hand closures.
- Normalizing the 20 legacy rows that already carry `workflow: "hand-orchestrated"` (W36, two
  spacing variants), except that the retro must not crash on them.
- The dashboard UI. `ingest.py` only needs to keep working; surfacing the field there is follow-up.

## Acceptance Criteria
- [ ] Implementation Notes contain the completed consumer audit of the run `workflow` field. It
  lists each reader and states that it is unaffected, because `workflow` values are unchanged.
- [ ] `record_run.py --data '{..., "execution_mode": "pipeline"}'` writes the field through, and
  a record without it is still accepted (no change to `REQUIRED`).
- [ ] `record_hand_orchestrated_closure.py` run records contain `"execution_mode": "hand"` and still
  contain `"workflow": "implement-ticket"` by default. This is pinned by a test in
  `tests/tools/`.
- [ ] Each of the 4 workflow `.js` files' `record_run.py` command text includes
  `"execution_mode":"pipeline"`, and a text-level test pins it for each file.
- [ ] Given fixture runs with `execution_mode` pipeline, hand, and absent, the generated
  `## Run Summary` shows three separate groups with correct counts. Pipeline avg duration excludes
  hand and unlabelled runs.
- [ ] `generate_retro.py` over the real corpus (including the W36 `workflow: "hand-orchestrated"`
  rows) runs without error, and its output is deterministic across two runs.
- [ ] `docs/agent-monitoring/schema.md` documents `execution_mode` (values, optional, what absence
  means). `make knowledge-index-update` has been run.
- [ ] Existing agent-monitoring tests pass (`pytest tests/tools -k "monitoring or retro or record"`
  plus the dashboard ingest tests under `tests/`).

## Related Tickets
- TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP
- TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP
- TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE
- TCK-20260915-DUPLICATE-RUN-RECORDS

## Related Docs
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- docs/guides/agent_monitoring.md
- agent-monitoring/retro/RETRO-2026-W40.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/build_index.py
- tools/agent-monitoring/retro_nudge_hook.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/vocabulary.py
- tools/gate_checks/tool_call_count_mismatch_check.py
- src/api/agent_ops_dashboard/ingest.py
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- .claude/workflows/simq-audit.js

## Assumptions / Open Questions
- The field name `execution_mode` and the values `pipeline` / `hand` are a recommendation. Any
  pair works as long as it is documented once in schema.md.
- `simq-audit.js` is assumed to write a run record like the others. If it doesn't, drop it from the
  writer list and note why.
- The retro's other per-agent sections (gate failures by agent, reviewer coverage) may also want the
  split. This ticket only requires the Run Summary. Extend it if the change is small; otherwise
  note it as follow-up.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
