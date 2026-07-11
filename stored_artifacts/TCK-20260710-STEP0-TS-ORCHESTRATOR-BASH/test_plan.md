---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH
artifact_type: test_plan
tags: [agent-monitoring, workflows, data-quality]
---

# Test Plan — TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH

## Regression Surface

No JS test runner exists for `.claude/workflows/*.js` in this repo (confirmed by both this
investigation and the sibling C1 investigation) — regression coverage is entirely Python
static-text-parsing tests plus one documented live run. Baseline (run before any changes, all pass):

**Unit — `tests/tools/`**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — 9 tests, all currently passing. **One of
  them, `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`, is expected to be intentionally
  rewritten by this ticket's implementation** (see New Tests Required — it is not a "must stay
  green untouched" regression item, it is a "must be deliberately updated" item). The other 8 in this
  file must remain passing unmodified: `test_no_step_0b_agent_prompt_sidecar_text_remains`,
  `test_sidecar_bash_write_precedes_each_covered_agent_call`,
  `test_finalize_call_site_still_registers_sidecar`,
  `test_writeMonitoring_call_has_no_preceding_sidecar_write`,
  `test_scope_phase_call_site_has_no_preceding_sidecar_write`,
  `test_tid_and_seq_passed_as_argv_not_json_embedded`,
  `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`,
  `test_schema_doc_no_longer_describes_agent_self_report_mechanism`,
  `test_writeMonitoring_step5_sidecar_clear_still_present`,
  `test_record_events_required_fields_unchanged`, `test_all_nine_two_line_site_labels_present`.
  (Full list is 11 test functions across the earlier count of "9 tests" — see Scoped Pytest Commands
  for the exact collected count to compare against.)
- `tests/tools/test_record_events.py` — `REQUIRED`/`validate_record` behavior for `ts` as a
  non-nullable field. Must keep passing unmodified — this ticket changes *where* `ts` comes from, never
  `record_events.py`'s write-time contract (explicitly Out of Scope on the ticket).
- `tests/tools/test_record_run.py` — `record_run.py`'s `start_ts`/`end_ts`/`duration_s` handling.
  Unaffected (this ticket touches `events.jsonl`'s per-event `ts`, not `runs.jsonl`'s `start_ts`/
  `end_ts`, though `TICKET_SCHEMA`'s `ts` value is also what seeds `startTs` → `runs.jsonl`'s
  `start_ts` in implement-ticket.js — the *value* must still land correctly after the capture
  mechanism changes, even though this test file's own assertions don't change).
- `tests/tools/test_generate_retro.py` — confirmed (investigation.md) that `generate_retro.py` never
  reads `events.jsonl`'s `ts` field for any computation; must keep passing unmodified.
- `tests/tools/test_validate_agent_monitoring.py` — `validate.py`'s cross-file checks. Unaffected;
  must keep passing unmodified.
- `tests/tools/test_tag_skill_mapping_check.py` — reference pattern for raw-source-text parsing of
  `.claude/workflows/*.js`, including `create-tickets.js`. Must keep passing unmodified — this ticket
  must not touch the tag→skill mapping tables these tests assert on.

No integration or arena-combat tests apply — this is `layer: ai` orchestration tooling with zero
overlap with `src/` simulation code (confirmed: Mechanics/Engine Constraints section is empty, Parity
Ledger Overlap is empty).

## New Tests Required

Per AC #1 (every `date -u` Step 0 site replaced, wired into `pushEvent`/`start_ts`), AC #2
(`record_events.py`'s `ts` REQUIRED check still passes), AC #3 (monotonic `ts` in a live run), AC #4
(`schema.md` updated for doc/code parity):

1. **`test_step_0_ts_capture_lines_gone_from_all_covered_sites`** (rewrite of / replacement for
   `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`)
   Category: unit / architecture guard (static text parsing)
   Verifies: the literal `` Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` `` prompt text is **absent**
   from all 11 genuine implement-ticket.js sites (9 two-line sites + both Scope branches), all 3
   implement-epic.js Discover sites, and the 1 create-tickets.js Comprehend site — not merely "count
   unchanged," the opposite assertion. Must explicitly NOT assert anything about the `PHASE_TS:`
   free-text convention (covered by test 3 below) or about `writeMonitoring`'s/batch-monitoring-write's
   END_TS captures (must remain present — those are explicitly out of scope, see test 6).
   Location: `tests/tools/test_current_run_sidecar_orchestrator.py` (same file — this ticket's fix is
   directly adjacent to C1's; reuse the fixture/import setup already there) or a new
   `tests/tools/test_step0_ts_orchestrator.py` if the existing file's docstring/scope framing (entirely
   about the sidecar, not ts) makes co-locating confusing — planner's call, document the choice.

2. **`test_ts_capture_bash_precedes_each_covered_agent_call`**
   Category: unit / architecture guard
   Verifies: an orchestrator-side ts-capture (`bash('date -u +%Y-%m-%dT%H:%M:%SZ')` or equivalent
   helper call) immediately precedes each of the 11 implement-ticket.js sites, 3 implement-epic.js
   sites, and 1 create-tickets.js site, with the captured value visibly wired into the corresponding
   `pushEvent(...)` call's `ts` argument (implement-ticket.js) or schema-bypass assignment
   (`batchStartTs`/`startTs` in implement-epic.js/create-tickets.js). Mirrors
   `test_sidecar_bash_write_precedes_each_covered_agent_call`'s adjacency-string-matching approach.
   Location: same file as test 1.

3. **`test_phase_ts_prefix_convention_removed_from_investigate_and_plan`**
   Category: unit / architecture guard
   Verifies: the `PHASE_TS: <result>` free-text response-prefix instruction is gone from both the
   Investigate and Plan prompt strings, AND the orchestrator's regex-parse/strip logic
   (`investigation.toString().match(/^PHASE_TS: (\S+)/m)`, `.replace(/^PHASE_TS: \S+\n?/, '')` and
   the Plan-phase equivalents) is gone from the surrounding JS — not just the prompt text. Guards
   against leaving dead parsing code that silently no-ops once the prefix is never produced again.
   Location: `tests/tools/test_current_run_sidecar_orchestrator.py` or new file (same choice as test 1).

4. **`test_ts_schema_required_field_dropped_at_scope_and_discover`**
   Category: unit / architecture guard
   Verifies: `TICKET_SCHEMA`'s `required` array (implement-ticket.js) and `DISCOVER_SCHEMA`'s
   `required` array (implement-epic.js) no longer list `'ts'` — the companion schema edit flagged in
   investigation.md Risk #4. Parses the `required: [...]` literal text for each schema object.
   Location: same file as test 1/2/3.

5. **`test_record_events_ts_still_required`** (extend, don't duplicate, if
   `test_record_events_required_fields_unchanged` from C1 already covers this)
   Category: unit
   Verifies: `record_events.py`'s `REQUIRED` set is unchanged and still includes `"ts"` — this ticket
   changes where the value comes from, never `record_events.py`'s write-time contract (AC #2). Check
   `tests/tools/test_current_run_sidecar_orchestrator.py::test_record_events_required_fields_unchanged`
   first; if it already asserts the full set including `"ts"`, do not add a duplicate assertion — just
   confirm it still passes unmodified.

6. **`test_end_ts_and_batch_end_ts_captures_untouched`**
   Category: unit / architecture guard (anti-drift)
   Verifies: `writeMonitoring`'s Step 1 END_TS capture (implement-ticket.js line ~217,
   `` Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ `` inside the `monitoring-write` agent prompt) and
   implement-epic.js's batch-monitoring-write Step 1 END_TS capture (line ~235) are both still present,
   byte-identical, unmoved — these are explicitly out of scope (investigation.md Anti-Drift Hazards)
   and must not be accidentally swept up by a careless global find-and-replace across "Step 0"/"date
   -u" occurrences.
   Location: same file as test 1.

7. **Live end-to-end verification (AC #3 — no pytest equivalent possible)**
   Category: manual / operational, not pytest
   Verifies: after implementation, running `/implement-ticket` (this ticket's own close-out run
   satisfies this) produces `agent-monitoring/events.jsonl` entries for this `run_id` whose `ts` values
   are monotonically non-decreasing in `seq` order, with the Step 0 `date -u` prompt text structurally
   absent from every prompt actually dispatched. Record the observed `run_id` and outcome in the
   ticket's Test Summary before Finalize — same resolution pattern C1 used for its own AC #2 (Step 9 of
   its plan.md).

## Scoped Pytest Commands

```
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_generate_retro.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_tag_skill_mapping_check.py -v
```

If a new file (`tests/tools/test_step0_ts_orchestrator.py`) is created instead of extending
`test_current_run_sidecar_orchestrator.py`, add it explicitly to the command above — never rely on a
bare `pytest tests/` collection.

Never: `pytest tests/` (repo-wide) — this ticket's change surface is entirely `.claude/workflows/*.js`
+ `docs/agent-monitoring/schema.md`, zero `src/` files; a repo-wide run would waste time on thousands
of unrelated simulation tests.

## Anti-Drift Test Guards

- **`test_writeMonitoring_call_has_no_preceding_sidecar_write` and
  `test_scope_phase_call_site_has_no_preceding_sidecar_write`** (existing, C1's) must keep passing
  unmodified — proves this ticket's ts-capture helper insertion doesn't accidentally also insert a
  `writeSidecar(` call at either of the two permanently-sidecar-free sites.
- **`test_sidecar_bash_write_precedes_each_covered_agent_call`** (existing, C1's) must keep passing
  unmodified — proves this ticket's new ts-capture `bash()` call, inserted alongside `writeSidecar`,
  does not disturb the exact adjacency string C1's test matches (i.e., ts-capture should be added
  without breaking the `writeSidecar(...)\n<call> = await agent(` adjacency; order between the two
  calls should be decided once and asserted, not left ambiguous).
- **`test_all_nine_two_line_site_labels_present`** (existing, C1's) must keep passing unmodified —
  confirms no `label: '...'` site is accidentally dropped while editing the same 9 blocks this ticket
  also touches.
- **New test 6 (`test_end_ts_and_batch_end_ts_captures_untouched`)** exists specifically to catch a
  global "replace every `date -u` occurrence" mistake that would also destroy the intentionally-excluded
  `writeMonitoring`/batch-monitoring-write END_TS captures.
- **New test 4 (schema `required` check)** exists specifically to catch the silent-breakage mode where
  the Step 0 prompt text is removed but the schema still demands `ts`, which would make Scope/Discover
  agent calls newly fail validation the next time either is run against a strict-schema harness — a
  regression that a purely text-presence test (test 1) would not catch on its own.
