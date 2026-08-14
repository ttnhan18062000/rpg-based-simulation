---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK
artifact_type: test_plan
tags: [testing, observability, agent-monitoring]
---

# Test Plan — TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK

## Regression Surface

Existing tests that must keep passing, unmodified:

**Unit — retrieval-event schema (the artifact under test):**
- `tests/tools/test_retrieval_events.py` — full file, especially
  `TestFieldShapeConstant::test_field_set_contains_exactly_expected_retrieval_fields`,
  `TestFieldShapeConstant::test_field_set_excludes_execution_id_provider_and_required_base_fields`,
  and `TestSchemaExcludesRawTextAndIdentityFields::test_no_execution_id_provider_or_raw_text_field`
  — the new check must not contradict or duplicate these; they stay green and unedited.
- `tests/tools/test_retrieval_event_wrapper_single_source.py` — the wrapper single-source guard;
  unrelated to this ticket's scope but shares a directory, must not regress.

**Unit — Codex-replay-parity package (the style being mirrored):**
- `tests/agent_replay_codex/test_monitoring_provenance.py` — both tests
  (`test_real_monitoring_corpus_has_zero_codex_provider_records`,
  `test_negative_control_raises_on_a_codex_provider_record`) must keep passing unmodified; this
  ticket's new test file is a sibling, not an edit to this one.
- `tests/agent_replay_codex/` — full directory (`test_codex_config_guard.py`,
  `test_consent_gate.py`, `test_containment.py`, `test_containment_real_process.py`,
  `test_divergence_registration.py`, `test_entry_criterion.py`, `test_no_forbidden_calls.py`,
  `test_no_production_hook_invocation.py`, `test_phase_parity.py`, `test_pre_post_snapshot.py`,
  `test_shadow_mode_comparison.py`, `test_wrapper_script.py`) — this ticket must not import or
  exercise consent/invocation/shadow-mode machinery, so these should be entirely unaffected; run
  them to confirm no accidental import-time side effect from the new module.

**Integration — monitoring writer path (upstream of both):**
- `tests/tools/test_record_events.py` — `record_events.validate_record()`/`REQUIRED` set, which
  `retrieval_events.py` depends on and which this ticket must not touch.
- `tests/tools/test_monitoring_writer_single_source.py` — the existing single-writer-path
  architecture guard (`_CALL_SITES` list scoped to `post_tool_hook.py`/`record_run.py`/
  `record_events.py`); this ticket adds no new writer, so this guard's scope must stay unchanged.

## New Tests Required

Per acceptance criteria:

1. **`test_field_set_contains_no_provider_specific_field`**
   - Category: unit / structural
   - Verifies: iterating a reusable check function (e.g.
     `assert_no_provider_specific_fields(fields: frozenset[str], provider_tokens: frozenset[str])`)
     against the real `tools.retrieval_events.RETRIEVAL_EVENT_FIELDS` raises nothing — no field
     name literally equals or is prefixed by a known provider token (`codex`, `claude`, at minimum;
     decide final token list in plan.md per investigation.md's open question).
   - Location: new test module, e.g. `tests/tools/test_retrieval_event_provider_parity.py`
     (co-located with `test_retrieval_events.py`, the module it validates) — final location
     depends on where plan.md places the check function itself (see investigation.md's open
     question on `tools/agent_replay_codex/` vs. beside `tools/retrieval_events.py`).

2. **`test_execution_id_and_provider_absent_from_retrieval_event_fields`**
   - Category: unit / structural
   - Verifies: explicit assertion (via the new check function, not an inline `assert`) that
     `"execution_id"` and `"provider"` are absent from `RETRIEVAL_EVENT_FIELDS`, and that the
     check raises loudly (a named exception, not a silent `False`/`None` return) if either is
     present. Distinct from `test_retrieval_events.py`'s existing inline assertion of the same
     fact — this test exercises the *check function*, proving it is reusable/importable, not just
     that the fact happens to be true today.
   - Location: same new test module as above.

3. **`test_docstring_and_test_names_state_structural_only_not_live_parity`**
   - Category: unit / documentation-as-contract
   - Verifies: the new check module's docstring (read via `inspect.getdoc()` or a direct string
     assertion on `module.__doc__`) contains language explicitly stating this is
     structural/field-shape parity only, not live cross-provider parity (mirrors
     `provenance_check.py`'s own docstring pattern of stating its invariant class up front). Also
     assert the check function's own name and/or docstring do not imply live-execution
     comparison (e.g. must not be named anything like `assert_codex_claude_output_parity`).
   - Location: same new test module.

4. **`test_negative_control_raises_when_provider_specific_field_injected`**
   - Category: unit / negative-control
   - Verifies: build a `tmp_path`-independent, in-memory fixture — a copy of
     `RETRIEVAL_EVENT_FIELDS` with a fabricated, realistic provider-specific field name injected
     (e.g. `"codex_latency_ms"` or `"claude_cache_status"` — not a trivially unrealistic token, per
     investigation.md's Anti-Drift Hazards), call the check function against the fixture, and
     assert it raises the new exception type. Mirrors
     `test_monitoring_provenance.py::test_negative_control_raises_on_a_codex_provider_record`'s
     shape exactly, adapted from a JSONL-record fixture to a field-set fixture (no file I/O needed
     here — the check operates on an in-memory `frozenset`/iterable, unlike
     `assert_no_codex_provider_writes()` which reads files).
   - Location: same new test module.

5. **`test_check_is_read_only_and_never_touches_real_monitoring_files`**
   - Category: unit / architecture guard
   - Verifies: the new check function's signature/body takes no file-path argument pointing at
     `agent-monitoring/*.jsonl` and performs no file I/O (e.g. assert via `inspect.getsource()`
     that no `open(`, `Path(`, or `agent-monitoring` string literal appears in the check function's
     source — the artifact under test is an in-memory constant, not a corpus on disk, unlike
     `assert_no_codex_provider_writes()`). Prevents future scope creep toward re-reading
     `events.jsonl` for this specific check (that concern already belongs to
     `provenance_check.py`).
   - Location: same new test module.

## Scoped Pytest Commands

```
pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_wrapper_single_source.py -v
pytest tests/agent_replay_codex/ -v
pytest tests/tools/test_record_events.py tests/tools/test_monitoring_writer_single_source.py -v
pytest tests/tools/test_retrieval_event_provider_parity.py -v   # new module, exact path TBD per plan.md's placement decision
```

Never `pytest tests/` — scope stays within `tests/tools/` (retrieval-event schema + this new
check) and `tests/agent_replay_codex/` (the style precedent), consistent with this ticket's
Related Code Areas.

## Anti-Drift Test Guards

- **Guard against reusing/mutating `ContainmentViolationError`:** a test asserting the new check
  raises a distinct, newly-defined exception type (not `ContainmentViolationError`) would catch an
  implementation that lazily reused the Codex package's exception for an unrelated invariant class
  — include this as an explicit `isinstance`/type-identity assertion in test 4 above, not just
  `pytest.raises(Exception)`.
- **Guard against silently editing `RETRIEVAL_EVENT_FIELDS` to "fix" a false positive:** since
  `tools/retrieval_events.py` is explicitly Out of Scope for edits, a CI-visible regression here
  would be the new check module's own test suite failing after a `RETRIEVAL_EVENT_FIELDS` change —
  no additional guard needed beyond running `tests/tools/test_retrieval_events.py` in the same
  scoped command as the new tests, so any accidental co-edit is caught in the same run.
- **Guard against the check accidentally requiring live Codex/consent state:** a test (or a
  `pytest.ini`/marker-free assertion) confirming the new test module's collection and execution
  never reference `CODEX_REPLAY_PARITY_LIVE_CONSENT`, `codex` subprocess invocation, or any symbol
  from `tools/agent_replay_codex/consent_gate.py`/`invoker.py`/`shadow_mode.py` — e.g. a static
  grep-based test (mirrors the sibling ticket's AC5-style "structural grep-based test proving zero
  references") scanning the new module's source for those forbidden imports.
- **Guard against duplicating `TestSchemaExcludesRawTextAndIdentityFields`:** run
  `tests/tools/test_retrieval_events.py` and the new module in the same scoped pytest invocation
  and confirm no test name collision/duplicate assertion — if the new module ends up re-asserting
  exactly what that existing class already covers with no added value (no reusable function, no
  negative control), that is a signal the new module failed to add anything beyond what already
  exists and should be reconsidered before merge.
- **Guard against scope creep into live wrapper instrumentation:** none of the new tests should
  import or call `wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`/`wrap_context_packet_assembly`
  — this ticket checks the field-shape constant only, not the wrapper functions that emit real
  events using it (those are already covered by the sibling ticket's own test classes).
