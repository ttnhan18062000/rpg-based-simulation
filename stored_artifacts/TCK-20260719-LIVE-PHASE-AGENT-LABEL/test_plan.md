---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-LIVE-PHASE-AGENT-LABEL
artifact_type: test_plan
tags: [agent-monitoring, observability, workflows]
---

# Test Plan — TCK-20260719-LIVE-PHASE-AGENT-LABEL

## Regression Surface

Existing tests that must keep passing (or be updated in-place where the signature change requires
it — see New Tests Required for exactly which assertions need edits):

**unit — `tests/tools/test_current_run_sidecar_orchestrator.py`** (static source-text parsing
against `.claude/workflows/implement-ticket.js` and `docs/agent-monitoring/schema.md`; no JS
runtime, so this is the only regression coverage for the orchestration file):
- `test_no_step_0b_agent_prompt_sidecar_text_remains` — unaffected, no signature dependency.
- `test_sidecar_bash_write_precedes_each_covered_agent_call` — **will break**, must be updated (see
  New Tests Required; not one of the 3 the ticket names, but confirmed broken by the signature
  change — investigation.md Risk #2).
- `test_finalize_call_site_still_registers_sidecar` — **will break**, must be updated (same reason,
  also not named in the ticket).
- `test_writeMonitoring_call_has_no_preceding_sidecar_write` — unaffected; asserts `writeSidecar(`
  literal substring absence in `writeMonitoring`'s body, independent of arg count.
- `test_scope_phase_has_sidecar_coverage` — unaffected **only if** the Scope-decision (AC #6) comes
  out "no, don't add phase/agent to the Scope inline write." If "yes," this test's hardcoded JSON
  string assertion at line 161 breaks too and must be updated (investigation.md Risk #3).
- `test_tid_and_seq_passed_as_argv_not_json_embedded` — **will break**, must be updated (named in
  ticket Scope bullet 3).
- `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` — **will break**,
  must be updated (named in ticket Scope bullet 3).
- `test_schema_doc_no_longer_describes_agent_self_report_mechanism` — unaffected; checks doc prose
  markers unrelated to the field additions, but re-run to confirm the schema.md edit didn't
  accidentally remove/duplicate the required markers (`"writeSidecar(seq)"`,
  `"implement-ticket.js"`, `"create-tickets"`, `"implement-epic"`, `"neither ever has"`).
- `test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4` — unaffected, no signature
  dependency.
- `test_record_events_required_fields_unchanged` — unaffected; asserts `record_events.py`'s
  `REQUIRED` set for **events.jsonl**, a different file/module than this ticket touches. Run as a
  sanity guard that this ticket's change didn't accidentally touch `record_events.py`.
- `test_all_nine_two_line_site_labels_present` — unaffected; checks `label: '...'` option strings
  in `agent()` calls, untouched by the `writeSidecar` arg-count change.

**unit — `tests/tools/test_post_tool_hook.py`** (subprocess-driven hook tests; this file exists —
the ticket's claim that it doesn't is incorrect, see investigation.md Risk #1):
- `test_single_writer_produces_one_well_formed_line` — **will break** (exact `set(record.keys()) ==
  _RECORD_FIELDS` equality at line 62 against the closed set at lines 23-26). Must update
  `_RECORD_FIELDS` to include `phase`, `agent`.
- `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` — **will break**, same
  `_RECORD_FIELDS` equality check at line 93. Same fix.
- `test_locking_failure_does_not_propagate` — unaffected; doesn't inspect record contents, only
  process exit code/stderr.

**unit — `tests/tools/test_validate_agent_monitoring.py`** — unaffected (no hardcoded `tools.jsonl`
field-set assertions found; only row-count-mismatch string assertions independent of extra keys).
Run as a regression guard, not because a change is expected.

**integration — `tests/tools/test_agent_ops_dashboard_ingest.py`,
`tests/tools/test_agent_ops_dashboard_concurrency.py`** — unaffected (synthetic `tools.jsonl`
fixtures with their own small field subset; dashboard's `phase`/`agent` derivation reads
`events.jsonl`, not `tools.jsonl` rows — confirmed in investigation.md Risk #4). Run as a
non-regression guard.

**No arena-combat / simulation tests apply** — this ticket touches no `src/` file.

## New Tests Required

Per Acceptance Criteria:

- **AC #1** (`writeSidecar(seq, phase, agent)` writes all 4 keys; a `tools.jsonl` row during that
  phase carries matching non-null `phase`/`agent`) —
  - Test name: `test_phase_and_agent_included_when_sidecar_present`
  - Category: unit
  - Verifies: given a `.claude/current_run` sidecar file (in `tmp_path`, matching the existing
    fixture style) containing `{"run_id": "TCK-X", "seq": 3, "phase": "Implement", "agent":
    "implementer"}`, running `post_tool_hook.py` via subprocess produces a `tools.jsonl` record
    with `"phase": "Implement"` and `"agent": "implementer"` (not null, not dropped).
  - Location: `tests/tools/test_post_tool_hook.py` (extend existing file — it already has the
    right subprocess-driven fixture pattern; do not create a second test file for the same module).

- **AC #1 (helper shape)** — `writeSidecar`'s new 3-arg signature writes the correct dict to
  `.claude/current_run`:
  - Test name: `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` (replaces/
    renames the existing `test_tid_and_seq_passed_as_argv_not_json_embedded`)
  - Category: unit (static source-text)
  - Verifies: the `writeSidecar` helper body passes `tid`/`seq`/`phase`/`agent` as individually
    quoted argv elements (`"${tid}" "${seq}" "${phase}" "${agent}"`), reads them via
    `sys.argv[1]`..`sys.argv[4]`, contains no inline JSON literal embedding any of the 4 values
    directly in the `-c` string, and preserves the `2>/dev/null || true` fail-open suffix.
  - Location: `tests/tools/test_current_run_sidecar_orchestrator.py`

- **AC #2** (a `tools.jsonl` row for a tool call outside any active run has `phase: null, agent:
  null`) —
  - Test name: `test_phase_and_agent_null_when_no_active_run` (or extend
    `test_single_writer_produces_one_well_formed_line`'s existing no-sidecar-file default case if
    one already covers "no sidecar present" — confirm during implementation; add a dedicated test
    if the existing default-case coverage doesn't already assert `run_id`/`seq` are `None` with no
    sidecar file present, since AC #2 is specifically about `phase`/`agent` alongside that existing
    `run_id: None`/`seq: None` behavior)
  - Category: unit
  - Verifies: hook invocation with no `.claude/current_run` file present (or a sidecar missing
    `phase`/`agent` keys, e.g. `{"run_id": null, "seq": null}`) produces a record with
    `"phase": null, "agent": null` — no `KeyError`, no crash, fail-open exactly like the existing
    `run_id`/`seq` read.
  - Location: `tests/tools/test_post_tool_hook.py`

- **AC #3** (historical rows without `phase`/`agent` keys remain readable as None/absent) — this is
  a consumer-side guarantee, not a producer-side behavior to unit-test directly against
  `post_tool_hook.py` (which only ever writes forward). Verify by:
  - Test name: `test_load_jsonl_tolerates_missing_phase_agent_keys` — only add if no existing test
    already covers `validate.py`'s `load_jsonl`/downstream readers handling a dict without
    `phase`/`agent` keys via `.get()` rather than `[...]` indexing. Check
    `tools/agent-monitoring/validate.py` and `src/api/agent_ops_dashboard/ingest.py`'s tools.jsonl
    read paths for `.get("phase")`/`["phase"]` usage during implementation — if all reads already
    use `.get(...)`, this is provably safe by inspection and an explicit new test is optional (do
    not force one for coverage-theater's sake per CLAUDE.md's "test meaningful behavior, not
    superficial coverage" rule); if any bare `record["phase"]` indexing is found, a test IS required
    and this becomes non-optional.
  - Category: unit
  - Location: `tests/tools/test_validate_agent_monitoring.py` (if needed).

- **AC #4** (the 3 named `test_current_run_sidecar_orchestrator.py` tests pass against the new
  signature) —
  - Update `_COVERED_SITE_ADJACENCY` (lines 49-60): all 10 strings gain the new trailing args, e.g.
    `"  await writeSidecar(events.length + 1, 'Investigate', 'investigator')\n  investigation =
    await agent("` (repeat per site using the phase/agent literal table in investigation.md's
    Current Behavior section).
  - Update `test_sidecar_bash_write_precedes_each_covered_agent_call`'s counting regex (line 99)
    from `r"await writeSidecar\(events\.length \+ 1\)"` to one that matches the new 3-arg call
    shape (e.g. `r"await writeSidecar\(events\.length \+ 1, '[^']+', '[^']+'\)"`), keeping the
    `== 10` count assertion.
  - Update `test_finalize_call_site_still_registers_sidecar`'s regex (lines 119-121) similarly for
    the Finalize site's specific phase/agent literals (`'Finalize'`, `'finalizer'`).
  - Update `test_tid_and_seq_passed_as_argv_not_json_embedded` → rename/extend per the AC #1 entry
    above; update the helper-match regex (line 180) from `r"const writeSidecar = async \(seq\) =>
    \{.*?\n\}\n"` to match `\(seq, phase, agent\)`.
  - Update `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` (line
    198): change the literal string `"const writeSidecar = async (seq)"` to `"const writeSidecar =
    async (seq, phase, agent)"` at both the `source.index(...)` call and the `source.count(...)`
    assertion.
  - Category: unit (static source-text), all in `tests/tools/test_current_run_sidecar_orchestrator.py`.

- **AC #5** (schema.md documents the two new fields) —
  - Test name: `test_schema_doc_documents_tools_jsonl_phase_agent_fields`
  - Category: unit (static doc-text)
  - Verifies: `docs/agent-monitoring/schema.md`'s `tools.jsonl` Fields table (around lines 219-228)
    contains a `phase` row and an `agent` row, each with `Nullable: Yes` and a note referencing
    "null for records predating [this ticket ID]" — following the same convention already used for
    `events.jsonl`'s `tool_call_count`/`reason_code`/`cost_proxy_score` rows (schema.md:109-111).
  - Location: `tests/tools/test_current_run_sidecar_orchestrator.py` (this file already owns
    schema.md static-text assertions via `_read_schema_doc()`/`test_schema_doc_no_longer_
    describes_agent_self_report_mechanism` — extend it rather than creating a new doc-test file).

- **AC #6** (Scope-phase decision is implemented, not left open) —
  - If the decision is "yes, add the literals": update
    `test_scope_phase_has_sidecar_coverage`'s hardcoded JSON-dict string assertion (line 161) to
    include `'phase': 'Scope', 'agent': 'ticket-scoper'`, and add a new test verifying a Scope-phase
    tool call (during ticket resume) produces a `tools.jsonl` row with non-null `phase`/`agent`.
  - If the decision is "no": no test changes needed beyond documenting the rationale in the
    ticket's Implementation Notes; add a comment near the Scope inline-write block (matching this
    file's existing dense-comment convention) stating the decision and why, so a future reader
    doesn't mistake the omission for an oversight.
  - Category: unit (static source-text) or none, contingent on the decision.
  - Location: `tests/tools/test_current_run_sidecar_orchestrator.py`.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_post_tool_hook.py -v
```

Broader regression sweep (agent-monitoring tooling domain, catches any unexpected cross-file
coupling in `validate.py`/dashboard ingest without running the whole suite):

```
python3 -m pytest tests/tools/ -k "monitoring or sidecar or post_tool_hook or agent_ops_dashboard or validate_agent" -v
```

Never `pytest tests/` — scope is `tests/tools/` only; no `src/` file is touched by this ticket so
no `tests/unit/`, `tests/integration/`, or arena-combat suites are in scope.

## Anti-Drift Test Guards

- **`test_record_events_required_fields_unchanged`** (existing, `events.jsonl`'s `REQUIRED` set) —
  re-run unmodified as a guard that this ticket's edits stay confined to `tools.jsonl`/
  `post_tool_hook.py`/`writeSidecar` and never touch `record_events.py`'s field contract.
- **`test_writeMonitoring_call_has_no_preceding_sidecar_write`** (existing) — re-run unmodified as a
  guard against accidentally adding `writeSidecar` tracking to `writeMonitoring`'s own agent call,
  which would silently reintroduce the exact misattribution bug
  TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION fixed.
- **`test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4`** (existing) — re-run
  unmodified as a guard that the Step-0-clear-first ordering isn't disturbed while editing adjacent
  `writeSidecar`-related code.
- **New: `test_locking_failure_does_not_propagate`-adjacent guard for the new fields** — confirm (by
  re-running the existing test, no new test needed) that `phase`/`agent` being added to the record
  dict doesn't change the fail-silent contract under a forced `fcntl.flock` failure — the new keys
  are computed before the `open()+flock()+write()` block, so a locking failure still can't leave a
  partially-written record; this existing test already proves the whole hook exits 0/stderr-empty
  regardless of dict contents.
- **New: exact-superset guard for `_RECORD_FIELDS`.** After updating `_RECORD_FIELDS` to add
  `phase`/`agent`, keep the equality check (`set(record.keys()) == _RECORD_FIELDS`) rather than
  loosening it to a subset/superset check — an exact-set assertion is what caught this ticket's own
  scope gap during investigation (a stale test file the ticket didn't know existed) and is the
  correct anti-drift property going forward: any *future* accidental field addition/removal to the
  `tools.jsonl` record dict should also be forced to touch this test explicitly, not silently pass.
- **New: Scope-decision consistency guard.** Whichever way AC #6 is decided, add or confirm a test
  that fails if a *future* change makes the Scope inline-write and the `writeSidecar` helper
  silently diverge in whether they populate `phase`/`agent` (e.g. someone adds it to one path but
  not the other without updating the corresponding test) — the existing
  `test_scope_phase_has_sidecar_coverage` test already isolates the Scope region text from the
  `writeSidecar`-helper region text (`pre_scope_region` vs. the rest of the file), so extending its
  existing assertions (rather than writing an entirely new cross-cutting test) is sufficient and
  keeps the two code paths' regression coverage co-located with their existing tests.
