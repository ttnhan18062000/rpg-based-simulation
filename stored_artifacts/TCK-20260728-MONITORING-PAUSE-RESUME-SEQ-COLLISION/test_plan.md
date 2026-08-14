---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
artifact_type: test_plan
tags: [agent-monitoring, data-quality, root-cause, bug]
---

# Test Plan — TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION

## Regression Surface

All of these are static/pure-function suites (no live workflow execution — this repo has no JS test
runner for `.claude/workflows/*.js`; these tests parse the file's raw source text and/or exercise
Python functions directly). Must stay green after the fix:

**Unit / static-source-parsing (`.claude/workflows/implement-ticket.js` coverage):**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — the full 27-test suite. Specifically at risk:
  - `test_scope_phase_has_sidecar_coverage` — currently asserts the literal
    `"open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1, 'phase': 'Scope', 'agent': 'ticket-scoper'}))"`
    string is present verbatim. **This assertion will break** once the hardcoded `'seq': 1` becomes a
    computed offset expression — this test must be updated in the same change, not left failing.
  - `test_sidecar_bash_write_precedes_each_covered_agent_call` — regex-counts exactly 10
    `writeSidecar(events.length + 1, '<phase>', '<agent>')` call sites. If the fix changes this
    expression shape (e.g. to `events.length + 1 + seqOffset`), this regex must be updated to match,
    and the count of 10 must still hold (no call site added/removed).
  - `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` — asserts `writeSidecar`'s
    argv-quoting convention. If `writeSidecar`'s signature grows a new parameter, the existing four
    argv assertions must still pass unchanged.
  - `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` — asserts
    `writeSidecar` is defined exactly once, in a specific position. Must still hold if `writeSidecar`
    is modified in place (not redefined).
  - `test_record_events_required_fields_unchanged` — guards `record_events.py`'s `REQUIRED` set.
    Must stay untouched (confirms the fix did not drift into Candidate 2's schema-widening approach).
  - All other tests in this file (Finalize sidecar coverage, writeMonitoring Step-0 ordering, schema
    doc assertions, the 9-site label sanity check) are unrelated to this ticket's change and must
    pass unmodified — regression proof that the fix is additive, not a rewrite.
- `tests/tools/test_validate_agent_monitoring.py` — the full suite, especially
  `test_tool_count_drift_report_*` (4 tests: no-mismatch, undercounted, overcounted, null-field-skip,
  interactive-row-immunity). These must still pass against `compute_tool_count_drift_report`
  unmodified in its existing behavior — the new resume-collision check (below) is additive, not a
  replacement.
- `tests/tools/test_record_events.py` — `record_events.py`'s `REQUIRED`/`compute_tool_stats()`
  behavior must be unaffected (this ticket's fix lives upstream, in how `seq` values are *produced*,
  not in how `events.jsonl` records are validated/written).
- `tests/tools/test_record_run.py` — unaffected surface, included as a cheap regression guard since
  it shares `agent-monitoring/` infrastructure.

**Integration:**
- None of this repo's test suites execute `.claude/workflows/implement-ticket.js` live (no JS runner) —
  there is no integration test category for this file beyond the static-source-parsing tests above.
  A "reproduction" per the ticket's AC #2 is necessarily a **new static/fixture-based test** that
  constructs a fixture `events.jsonl` shaped like a pre-pause session and asserts the computed
  `seqOffset`/next-`seq` value continues past it — see New Tests Required below.

**Arena-combat:** N/A — no combat/simulation surface touched by this ticket.

## New Tests Required

Per Acceptance Criteria:

1. **AC: "Root cause mechanism confirmed and documented precisely"** — satisfied by
   `investigation.md`, not a test. No new test required for this AC directly, but the *documentation*
   of the mechanism should be cross-checked against test #2 below (the test proves the documented
   mechanism was real and is now closed).

2. **AC: "Resumed sessions can no longer write tool-call attribution into a `(run_id, seq)` bucket a
   prior session already populated — verified against a reproduction of the
   `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`-shaped scenario"**
   - Test name: `test_resume_seq_lookup_continues_past_prior_session_max_seq`
   - Category: unit (pure-function test against whatever new function computes the resume-aware
     offset — e.g. mirroring `test_validate_agent_monitoring.py`'s no-file-I/O fixture-construction
     style: build a fake `events.jsonl`-shaped list of dicts with `run_id="TCK-FAKE"` and `seq` values
     1-6 [mirroring the ticket's own table], call the new lookup function, assert it returns 7 (not 1)
     as the next seq for a resumed session on that same `run_id`).
   - What it verifies: given a `run_id` with existing `events.jsonl` records up to `seq=N`, the
     resume-aware computation returns `N+1` as the starting point for a new session, not `1`.
   - Where it should live: co-located with wherever the lookup function itself lives (likely
     `tools/agent-monitoring/validate.py` or a new small module under `tools/agent-monitoring/`,
     decided at Plan) — a new test file or an addition to `tests/tools/test_validate_agent_monitoring.py`
     if the function lands in `validate.py`, following that file's existing no-file-I/O fixture
     pattern (`_BASE_RUN`-style fixtures, not real files on disk).
   - A second variant: `test_resume_seq_lookup_returns_1_for_run_id_with_no_prior_history` — a
     brand-new `run_id`/first-ever run has no prior `events.jsonl` rows, so the lookup must return 1
     (not error, not `None`) — proves the fix doesn't change behavior for the overwhelmingly common
     non-resume case.

3. **AC: "`compute_tool_count_drift_report()` (or a new sibling function) can detect this specific
   mechanism (multi-invocation seq collision) and distinguish it from the two mechanisms the sibling
   ticket's version already covers"**
   - Test name: `test_multi_invocation_collision_report_detects_duplicate_scope_seq1`
   - Category: unit — pure function, same style as `test_tool_count_drift_report_*` in
     `test_validate_agent_monitoring.py` (construct `events` list as plain dicts, no file I/O).
   - What it verifies: given `events.jsonl`-shaped fixture data containing **more than one**
     `phase="Scope", seq=1` entry for the same `run_id` (the exact signature the ticket's own "Blast
     radius" section used to find the 8 affected `run_id`s empirically), the new report function
     flags that `run_id` as a multi-invocation-collision candidate. A second case with only one
     `Scope`/`seq=1` entry per `run_id` must NOT be flagged (no false positive on ordinary single-session
     runs).
   - Where it should live: `tests/tools/test_validate_agent_monitoring.py`, alongside the existing
     `compute_tool_count_drift_report` tests — same module, same fixture style, natural sibling.
   - Also add: `test_multi_invocation_collision_report_is_read_only` (mirrors
     `test_tool_count_drift_report_is_read_only`'s existing pattern) — the new check must not mutate
     its input lists, consistent with every other function in `validate.py`.

4. **AC: "`docs/agent-monitoring/schema.md` updated with the third mechanism and its fix"** — doc
   change, not directly a test target, but covered indirectly by:
   - Test name: `test_schema_doc_documents_pause_resume_seq_collision_fix`
   - Category: architecture guard (static source-text-parsing, same style as the existing
     `test_schema_doc_no_longer_describes_agent_self_report_mechanism` /
     `test_schema_doc_documents_tools_jsonl_phase_agent_fields` in
     `test_current_run_sidecar_orchestrator.py`).
   - What it verifies: `docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent
     events" section contains a marker string identifying this ticket
     (`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) and describes the resume-aware seq
     continuation, alongside the two mechanisms `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`
     already documented there.
   - Where it should live: `tests/tools/test_current_run_sidecar_orchestrator.py` (same module already
     owns the schema-doc assertions for this section) or a new dedicated test — Plan should decide
     based on whether it extends that file's existing scope or warrants its own module given this is
     now a third mechanism layered onto the same doc section.

5. **AC (implicit, from the "Anti-Drift Hazards" / "Prior Work" findings in investigation.md):
   `test_scope_phase_has_sidecar_coverage` must be updated, not left broken** — this is not a new
   test but a required **modification** to an existing one:
   - Update `test_scope_phase_has_sidecar_coverage` (`tests/tools/test_current_run_sidecar_orchestrator.py:147-169`)
     to assert whatever the new resume-aware seq expression actually is (e.g. containing
     `seqOffset` or equivalent) instead of the literal `'seq': 1,` substring — following this file's
     own established convention of updating (not deleting) assertions when a mechanism changes shape
     (see that file's own precedent: `test_scope_phase_call_site_has_no_preceding_sidecar_write`
     → `test_scope_phase_has_sidecar_coverage` in the sibling ticket).
   - Update `test_sidecar_bash_write_precedes_each_covered_agent_call`'s regex if the
     `events.length + 1` expression shape changes at any of the 10 `writeSidecar` call sites.

6. **New test guarding non-regression for the non-resume path**:
   - Test name: `test_new_ticket_branch_seq_offset_is_zero_not_null`
   - Category: unit / architecture guard
   - What it verifies: the brand-new-ticket branch (no `ticketId`) still produces `seqOffset = 0`
     (or equivalent), never `null`/`undefined`/`NaN`, so ordinary (non-resumed) runs are provably
     unaffected — the single highest-value regression guard for this ticket, since the vast majority
     of runs are not resumes.
   - Where it should live: alongside test #2 above, same file.

## Scoped Pytest Commands

```
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_record_run.py -v
```

Never `pytest tests/` — scoped strictly to `tests/tools/` (agent-monitoring infrastructure), the only
domain this ticket touches. No `src/` or simulation test directories are in scope.

If the resume-aware lookup lands in a new dedicated module (per the open question in
investigation.md), add that module's own new test file explicitly to the command above once its path
is known at Plan/Implement time.

## Anti-Drift Test Guards

- **`test_record_events_required_fields_unchanged`** (already exists, `tests/tools/test_current_run_sidecar_orchestrator.py:295-296`)
  — must still assert `REQUIRED == {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}`
  unchanged. Directly catches an accidental drift toward Candidate 2 (unique-token attribution key)
  instead of the intended minimal Candidate 1 (max-seq continuation) fix.
- **`test_writeMonitoring_step0_sidecar_clear_precedes_other_steps`** (already exists) — must still
  pass unmodified. Guards against this ticket's fix accidentally touching `writeMonitoring`'s
  Step-0-first sidecar-clear ordering, which belongs to the sibling ticket's already-closed fix, not
  this one.
- **`test_finalize_call_site_still_registers_sidecar`** (already exists) — must still pass unmodified;
  proves the Finalize phase's own `writeSidecar` call site is untouched by this ticket's change.
- **New: `test_new_ticket_branch_seq_offset_is_zero_not_null`** (New Tests Required #6 above) — the
  single most important anti-drift guard for this ticket specifically, since a bug in the offset
  computation could silently corrupt `seq` for *every* run (not just resumed ones) if the offset
  leaks a non-zero or non-numeric value into the non-resume branch.
- **New: `test_multi_invocation_collision_report_detects_duplicate_scope_seq1`'s negative case**
  (single `Scope`/`seq=1` per `run_id` must not be flagged) — guards against the new detection check
  becoming a false-positive generator on ordinary single-session runs, which would erode trust in
  `validate.py`'s output the same way the original 433/1247 false-mismatch noise did before the
  sibling ticket's fix.
- **Existing `compute_tool_count_drift_report` tests in `test_validate_agent_monitoring.py`** — must
  all still pass with the new resume-collision function added as a sibling, not a modification to the
  existing function's signature or return shape (its `str` return-value contract, used by
  `validate.py::main()`'s `print()` call, must remain undisturbed).
