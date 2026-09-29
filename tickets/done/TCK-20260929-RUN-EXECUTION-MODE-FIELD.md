---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260929-RUN-EXECUTION-MODE-FIELD
phase: done
date: 2026-09-29
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20260929-RUN-EXECUTION-MODE-FIELD

## Title
Record whether a run went through the pipeline or was closed by hand (`execution_mode` on runs.jsonl), and split the retro on it

## Status
DONE

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
- [x] Implementation Notes contain the completed consumer audit of the run `workflow` field. It
  lists each reader and states that it is unaffected, because `workflow` values are unchanged.
- [x] `record_run.py --data '{..., "execution_mode": "pipeline"}'` writes the field through, and
  a record without it is still accepted (no change to `REQUIRED`).
- [x] `record_hand_orchestrated_closure.py` run records contain `"execution_mode": "hand"` and still
  contain `"workflow": "implement-ticket"` by default. This is pinned by a test in
  `tests/tools/`.
- [x] Each of the 4 workflow `.js` files' `record_run.py` command text includes
  `"execution_mode":"pipeline"`, and a text-level test pins it for each file.
- [x] Given fixture runs with `execution_mode` pipeline, hand, and absent, the generated
  `## Run Summary` shows three separate groups with correct counts. Pipeline avg duration excludes
  hand and unlabelled runs.
- [x] `generate_retro.py` over the real corpus (including the W36 `workflow: "hand-orchestrated"`
  rows) runs without error, and its output is deterministic across two runs.
- [x] `docs/agent-monitoring/schema.md` documents `execution_mode` (values, optional, what absence
  means). `make knowledge-index-update` has been run.
- [x] Existing agent-monitoring tests pass (`pytest tests/tools -k "monitoring or retro or record"`
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

### Consumer audit of the run `workflow` field (acceptance blocker — completed)
All 6 known readers confirmed unaffected. `workflow` values are unchanged by this ticket (option
A — changing `workflow` — was not chosen); `execution_mode` is a brand-new, separate, optional
key, and none of these readers reject or choke on an unrecognized extra key in the record dict:
- `tools/agent-monitoring/build_index.py` (`_ingest_runs`/`_ingest_events`): reads `record.get("workflow")`
  only for its own `workflow` SQLite column; also stores the *entire* record as `raw_json` via
  `json.dumps(record, sort_keys=True)`, so `execution_mode` flows through there transparently
  without any code change. Confirmed no schema/column addition needed for this ticket's scope.
- `tools/agent-monitoring/retro_nudge_hook.py:44` (`_count_done_since`): filters on
  `workflow != "implement-ticket"`. Unaffected — that comparison's both sides are untouched.
- `tools/gate_checks/tool_call_count_mismatch_check.py:88`: builds a `run_id -> workflow` lookup
  dict via `.get("workflow")`. Unaffected — pure passthrough read.
- `src/api/agent_ops_dashboard/ingest.py:394` (`_build_run_summary`): sets
  `RunSummary.workflow = record.get("workflow") or ""`. Unaffected; confirmed via the full
  `tests/tools/test_agent_ops_dashboard_ingest.py` suite (49 passed, no changes needed) — matches
  this ticket's Out of Scope ("The dashboard UI... only needs to keep working").
- `tools/agent-monitoring/validate.py:123` (`RUN_REQUIRED_FIELDS_FOR_DRIFT = ("workflow", "tier",
  "final_status")`): a fixed 3-tuple of null-check fields; `execution_mode` is not in it and this
  ticket does not add it (optional field, drift-checking it is out of scope). Unaffected.
- `vocabulary.infer_workflow(run_id)`: infers workflow from the `run_id` string prefix alone —
  never reads the `workflow` or `execution_mode` fields at all. Structurally unaffected.

Bonus check beyond the ticket's known-readers list: `record_run.py`'s own `validate_record()` has
no `additionalProperties`-style restriction — `REQUIRED` is a membership check, not an exhaustive
schema — so passing an unrecognized extra key was already accepted before this ticket, confirmed
by `test_record_without_execution_mode_still_accepted`/`test_execution_mode_pipeline_passes_through_unchanged`.

### What changed
- `record_hand_orchestrated_closure.py::build_records`: added `"execution_mode": "hand"` to the
  run record dict (unconditional — every run this wrapper produces is by definition a hand
  closure). `workflow` continues to default to `"implement-ticket"` at the CLI layer, unchanged.
- 8 `record_run.py --data '{...}'` call sites across the 4 workflow `.js` files (2 in
  `implement-ticket.js`, 4 in `implement-epic.js` — including the 3 early-exit paths
  INVALID_ARGS/EPIC_CREATED/NOTHING_TO_DO, which are still real pipeline executions, not hand
  closures — 1 each in `create-tickets.js`/`simq-audit.js`) now include
  `"execution_mode":"pipeline"`. No `SKILL.md` restates the literal command text (confirmed via
  grep — each `SKILL.md` only says "use `record_run.py`", pointing back at the `.js` file's own
  code, never duplicating the JSON payload), so none needed updating.
- `generate_retro.py::compute_retro_metrics`: new `execution_mode_runs`/`execution_mode_summary`
  split (pipeline / hand / unlabelled), added to `run_summary["execution_mode"]`.
  `generate()`'s `## Run Summary` section renders a new "**By execution mode**" sub-table with
  per-group count/DONE/avg-duration — each group's avg duration is computed only from that
  group's own `duration_s` values, so it structurally cannot be diluted by the other groups
  (satisfies "Pipeline avg duration excludes hand and unlabelled runs" by construction, not a
  special-cased filter).
- `docs/agent-monitoring/schema.md`: new `execution_mode` row in the runs-table Fields section.
- A pre-existing frozen-output regression-lock test
  (`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` /
  `test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture`, both sharing one
  `_FIXED_CORPUS_EXPECTED_REPORT` constant) needed its pinned string literal updated to include
  the new table — expected and correct, since this ticket genuinely changes `generate()`'s
  output; not a defect being routed around.

## Test Summary
- `tests/tools/test_record_hand_orchestrated_closure.py`: new
  `test_build_records_sets_execution_mode_hand_and_keeps_workflow_default`.
- `tests/tools/test_record_run.py`: new `test_execution_mode_pipeline_passes_through_unchanged`,
  `test_record_without_execution_mode_still_accepted`.
- `tests/tools/test_run_execution_mode_field_wiring.py` (new file): parametrized text-level pin
  over all 4 workflow `.js` files' `record_run.py` call sites (8 total call sites, not just one
  per file) plus a negative check that no `.js` file ever writes `execution_mode: "hand"`.
- `tests/tools/test_generate_retro.py`: 6 new tests — 3-group split, pipeline-avg-excludes-others,
  legacy `workflow: "hand-orchestrated"` lands in `unlabelled` not `hand`, Markdown rendering
  (including a zero-count group's `0%` doesn't crash `fmt_pct`), and a real-corpus
  no-crash-plus-determinism test (confirmed against the real corpus including the 20 W36
  `workflow: "hand-orchestrated"` rows).
- Full run: `pytest tests/tools -k "monitoring or retro or record"` → 573 passed, 4 skipped.
  `tests/tools/test_agent_ops_dashboard_ingest.py` → 49 passed (unaffected, confirms the
  consumer audit's dashboard finding). `node --check` on all 4 edited `.js` files: no syntax
  errors. `tools/gate_checks/workflow_vocabulary_check.py`: all PASS (unaffected — no new
  agent/phase literal introduced, only a JSON payload key).

## Files Changed
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/agent-monitoring/generate_retro.py`
- `.claude/workflows/implement-ticket.js`, `implement-epic.js`, `create-tickets.js`, `simq-audit.js`
- `docs/agent-monitoring/schema.md`
- `tests/tools/test_record_hand_orchestrated_closure.py`
- `tests/tools/test_record_run.py`
- `tests/tools/test_generate_retro.py`
- `tests/tools/test_run_execution_mode_field_wiring.py` (new)

## Completion Summary
Added `execution_mode` (`pipeline`/`hand`, optional, additive) to the run record schema exactly
per the user's option-B decision — `workflow` values are completely unchanged, confirmed by a
full consumer audit of all 6 known readers plus a bonus schema-permissiveness check. Every real
pipeline call site (8 across the 4 workflow `.js` files, including early-exit paths) and the
hand-closure wrapper are labelled; `generate_retro.py`'s Run Summary now splits pipeline / hand /
unlabelled instead of blending them, addressing the exact problem `RETRO-2026-W40`'s Notes
measured. No backfill, no gate, no inference — all explicitly out of scope and respected. All
stated acceptance criteria verified via tests, direct invocation, and a real-corpus run.
