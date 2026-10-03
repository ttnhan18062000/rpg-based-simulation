---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260730-CLAUDE-EXECUTION-IDENTITY
artifact_type: test_plan
tags: [ai, workflows, agent-monitoring, observability, testing]
---

# Test Plan — TCK-20260730-CLAUDE-EXECUTION-IDENTITY

## Regression Surface

All of these are pre-existing and currently green; none should need behavior changes to keep
passing, only tolerate the new fields being populated where they previously weren't.

**Unit / static-source (`.claude/workflows/implement-ticket.js` text-parsing):**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — full file, in particular:
  - `test_no_step_0b_agent_prompt_sidecar_text_remains`
  - `test_sidecar_bash_write_precedes_each_covered_agent_call` (10-site adjacency + exact regex
    count)
  - `test_finalize_call_site_still_registers_sidecar`
  - `test_writeMonitoring_call_has_no_preceding_sidecar_write`
  - `test_scope_phase_has_sidecar_coverage`
  - `test_new_ticket_branch_seq_offset_is_zero_not_null`
  - `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` (argv-ordering guard
    — see Anti-Drift Test Guards)
  - `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` (signature
    literal-match guard)
  - `test_schema_doc_no_longer_describes_agent_self_report_mechanism`,
    `test_schema_doc_documents_tools_jsonl_phase_agent_fields`,
    `test_schema_doc_documents_pause_resume_seq_collision_fix`
  - `test_writeMonitoring_step0_sidecar_clear_precedes_other_steps` (Step 0-1-2-3 ordering guard)
  - `test_record_events_required_fields_unchanged` (imports `REQUIRED` from the real
    `record_events.py` — proves this ticket doesn't touch it)
  - `test_all_nine_two_line_site_labels_present`

**Unit (monitoring writer tools):**
- `tests/tools/test_post_tool_hook.py` — full file, in particular
  `test_execution_identity_fields_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`,
  `test_single_writer_produces_one_well_formed_line` (all already assert the exact 12-field
  `_RECORD_FIELDS` set including `execution_id`/`provider`/`ticket_id` — must keep passing
  unmodified since `post_tool_hook.py` itself is not touched by this ticket).
- `tests/tools/test_record_events.py` — full file, in particular
  `test_execution_identity_fields_pass_through_unchanged`,
  `test_record_events_required_fields_unchanged`-equivalent assertions.
- `tests/tools/test_record_run.py` — full file, in particular
  `test_execution_identity_fields_pass_through_unchanged`.

**Integration (dashboard ingest / reader-side legacy normalization):**
- `tests/tools/test_agent_ops_dashboard_ingest.py` — full file, in particular
  `test_run_summary_carries_provider_execution_id_ticket_id_when_present`,
  `test_run_summary_labels_legacy_record_as_legacy_not_none_silently`,
  `test_get_runs_filters_by_provider_and_execution_id`,
  `test_load_jsonl_handles_all_legacy_shapes_plus_new_execution_identity_format`.

**Architecture guard:**
- `tests/architecture/test_api_read_model_guard.py` (cited by `INFRA-275`'s own evidence trail —
  re-run as a regression guard since the dashboard API surface is adjacent, even though this
  ticket touches no `src/api/` file).

## New Tests Required

Per this ticket's ACs:

1. **`test_execution_id_generated_once_and_reused_across_events`** (AC1, AC2) — Category: unit
   (static-source). Assert `.claude/workflows/implement-ticket.js` computes `executionId` (or
   equivalent const name) exactly once, at a point after `const tid = ticketInfo.ticket_id` and
   before `writeSidecar`/`writeMonitoring` are defined (index-ordering assertion, mirroring
   `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`'s pattern).
   Where: `tests/tools/test_current_run_sidecar_orchestrator.py` (extend) or a new
   `tests/tools/test_execution_identity_orchestrator.py`.

2. **`test_writeSidecar_body_includes_execution_id_and_provider_via_closure_not_param`** (AC1,
   AC3) — Category: unit (static-source). Assert the `writeSidecar` function body contains
   `'execution_id': sys.argv[5]` (or the chosen argv index) and `'provider': sys.argv[6]`
   (or equivalent), that the function's declared parameter list is still exactly `(seq, phase,
   agent)` (no widening), and that the bash template literal's argv-quoting substring
   `'"${tid}" "${seq}" "${phase}" "${agent}"'` remains present unbroken (guards against inserting
   new args in the middle — see existing
   `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`, extend or add
   alongside it). Where: `tests/tools/test_current_run_sidecar_orchestrator.py`.

3. **`test_writeMonitoring_prompt_embeds_execution_id_provider_ticket_id_in_events_and_run_record`**
   (AC1, AC2, AC3) — Category: unit (static-source). Assert the `writeMonitoring` function body's
   prompt text includes `"execution_id"`, `"provider"`, `"ticket_id"` in both the per-event JSON
   construction instructions (Step 2 region) and the `record_run.py --data` JSON literal (Step 3
   region), and that the literal value used for provider is exactly `"claude"` — never
   `"claude-code"` anywhere in new code (a plain substring-absence assertion:
   `"claude-code" not in writemonitoring_region`, distinguishing new code from the untouched
   `docs/ai/monitoring_writer_decision.md` quoted-verbatim text this ticket does not edit). Where:
   `tests/tools/test_current_run_sidecar_orchestrator.py`.

4. **`test_scope_agent_failed_and_resume_pre_tid_paths_stay_identity_less`** (AC4) — Category:
   unit (static-source). Assert neither the Scope-agent-failed fallback block (`:189-194` region)
   nor the Scope-phase resume-branch's pre-`tid` inline sidecar write (`:62-67` region) contains
   `execution_id`/`provider` in their respective `bash()`/python payloads — i.e. these two blocks'
   source text must not gain the new field names. Where:
   `tests/tools/test_current_run_sidecar_orchestrator.py`.

5. **`test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources`** (AC1,
   AC2) — Category: integration. A live (or tightly simulated) `implement-ticket.js`-equivalent
   run — since this repo has no JS test runner for `.claude/workflows/*.js` (per this test file's
   own module docstring precedent), this must be expressed as a Python-level integration test
   that drives `record_events.py`/`record_run.py`/`post_tool_hook.py` with a shared, realistically
   shaped `execution_id`/`provider="claude"`/`ticket_id` across a simulated multi-phase run
   (2+ events + 1 run record + 1+ tools.jsonl row via sidecar), then asserts every written line
   for that run shares one `execution_id` and `provider="claude"`, and that a second simulated
   run produces a **different** `execution_id`. This is the closest reproducible proxy for the
   ticket's own "one controlled Claude implement-ticket execution" AC, given the JS orchestrator
   itself isn't unit-testable. Where: new
   `tests/tools/test_execution_identity_end_to_end.py`, or extend
   `tests/tools/test_agent_ops_dashboard_ingest.py` if reusing its `_init_repo_skeleton` fixture
   is simpler.

6. **`test_baseline_prefix_unchanged_after_new_identity_writes`** (AC6 — "all pre-existing
   monitoring JSONL lines/bytes remain unchanged") — Category: integration. Snapshot
   `agent-monitoring/{runs,events,tools}.jsonl` (line count + content) before appending new
   identity-bearing records, append, then assert the original N lines are byte-identical and only
   new lines were appended (never a rewrite of existing lines). This directly operationalizes the
   "pre/post monitoring prefix or manifest comparison" AC — no existing test does a byte-level
   prefix comparison for this specific purpose. Where: same new/extended file as test 5, or
   `tests/tools/test_agent_monitoring_manifest.py` if a suitable fixture pattern already exists
   there (check before creating a new mechanism — this file was flagged in
   `TCK-20260721-MONITORING-WRITER-UNIFICATION`'s own Completion Summary as the home of a related
   "these files must never be touched" guard that was narrowed to `validate.py`; confirm this new
   test's scope doesn't collide with that narrowing).

7. **`test_provider_claude_code_legacy_value_tolerated_not_normalized_as_new_write`** (AC3) —
   Category: unit. Two assertions in one test: (a) a synthetic legacy-shaped row with
   `"provider": "claude-code"` fed through the dashboard's `ingest.py`/`load_jsonl` path parses
   without error/crash (tolerant pass-through, same `{**record}`-style genericity already proven
   for other fields) — this defines the "reader-compatible" half; (b) a static-source assertion
   that no *new* code this ticket adds anywhere in `implement-ticket.js` constructs the literal
   string `"claude-code"` as a value (only `"claude"`) — this defines the "never an alternative
   newly emitted token" half. Where: split across
   `tests/tools/test_agent_ops_dashboard_ingest.py` (part a) and
   `tests/tools/test_current_run_sidecar_orchestrator.py` (part b, can merge into test 3 above).

## Scoped Pytest Commands

```bash
# Static-source orchestrator guards + monitoring writer unit tests (primary regression surface)
.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_post_tool_hook.py tests/tools/test_record_events.py tests/tools/test_record_run.py -v

# Dashboard ingest / reader-side identity + legacy normalization
.venv/bin/python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -v

# New integration test(s) once added
.venv/bin/python3 -m pytest tests/tools/test_execution_identity_end_to_end.py -v

# Adjacent architecture guard (dashboard API boundary, cited by INFRA-275's evidence trail)
.venv/bin/python3 -m pytest tests/architecture/test_api_read_model_guard.py -v

# Provider-agnostic contract conformance (Claude adapter) — sanity check that no phase/status
# vocabulary drifted as a side effect of this change
.venv/bin/python3 -m pytest tests/agent_orchestration_claude_adapter/ -v
```

Never `pytest tests/` — scoped to `tests/tools/` (monitoring writer + dashboard ingest),
`tests/architecture/` (API boundary guard), and `tests/agent_orchestration_claude_adapter/`
(contract conformance) only.

## Anti-Drift Test Guards

- **Argv-ordering guard** (extends existing
  `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`): the literal substring
  `'"${tid}" "${seq}" "${phase}" "${agent}"'` must remain present unbroken in `writeSidecar`'s
  body — proves new argv elements were appended, not interleaved.
- **Signature-stability guard**: `const writeSidecar = async (seq, phase, agent)` must remain a
  literal substring match — proves identity fields are threaded via closure, not by widening the
  function's parameter list (which would require touching all 10 call sites and risks call-site
  drift).
- **`REQUIRED`-set immutability guard** (existing
  `test_record_events_required_fields_unchanged`, extend with an equivalent for `record_run.py`
  if one doesn't already exist): proves this ticket never makes `provider`/`execution_id`/
  `ticket_id` mandatory, which would break every other workflow (`implement-epic`,
  `create-tickets`) that doesn't populate them.
- **Identity-less-path guard** (new test 4 above): proves the Scope-agent-failed and pre-`tid`
  Scope paths never gain a synthesized identity — directly enforces AC bullet 4.
- **No-`claude-code`-emission guard** (part of new test 3/7): proves no new code path constructs
  the legacy token as a value, only as historical/documentation text that this ticket does not
  edit.
- **Post-`writeMonitoring('DONE')` non-flush guard**: assert
  `check_tag_drift`'s and `check_monitoring_write_recorded`'s `pushEvent` calls remain textually
  after the `writeMonitoring('DONE')` call site and that no second `writeMonitoring`/direct
  `record_run.py`/`record_events.py` call is introduced after them — protects against
  accidentally double-writing a run record while "fixing" TCK-20260731's flagged region.
- **Doc-staleness gate guard**: a test (or manual Verify-phase check) confirming
  `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`
  is among `files_changed` when `implement-ticket.js` changes with `behavior_changed=true` —
  protects against `DOC_STALENESS_BLOCKED` at Implement (see investigation.md Anti-Drift
  Hazards: `agent-orchestration/intentional-divergences.md` alone does not satisfy this gate).
