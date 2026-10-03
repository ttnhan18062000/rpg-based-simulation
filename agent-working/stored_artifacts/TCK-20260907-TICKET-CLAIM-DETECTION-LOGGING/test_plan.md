---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING
artifact_type: test_plan
tags: [ai, agent-monitoring, workflows]
---

# Test Plan — TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING

## Regression Surface

Unit / static-source-string guards (must keep passing unmodified — the new insertion point at
`implement-ticket.js` line 213 is chosen specifically to avoid disturbing these):

- `tests/tools/test_current_run_sidecar_orchestrator.py` — all cases, especially
  `test_sidecar_bash_write_precedes_each_covered_agent_call`,
  `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`,
  `test_scope_phase_has_sidecar_coverage`, `test_scope_resume_branch_also_writes_session_scoped_copy`,
  `test_scope_agent_failed_and_resume_pre_tid_paths_stay_identity_less`.
- `tests/tools/test_post_tool_hook.py` — all cases, especially
  `test_stale_scoped_sidecar_pruned`, `test_fresh_scoped_sidecar_not_pruned`,
  `test_scoped_sidecar_preferred_over_stale_unscoped_sidecar`,
  `test_two_concurrent_sessions_each_attributed_correctly`,
  `test_foreign_scoped_sidecar_not_read_by_different_session` — this ticket's new instrumentation
  must never interfere with the hook's own independent glob/prune/read logic over the same
  `.claude/current_run.*` file family.
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — confirms
  `implement-epic.js`/`create-tickets.js` stay unaffected (this ticket is explicitly scoped to
  `implement-ticket.js` only).
- `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` — the third sidecar consumer;
  must show zero interaction with the new detection code path.

Integration:

- `tests/agent-monitoring/` (or wherever `record_run.py`/`record_events.py`/`writer.py` are
  covered) — confirm the new `write_line()`-based writer for `claim_detections.jsonl` does not
  regress `runs.jsonl`/`events.jsonl`/`tools.jsonl` writers sharing the same `writer.py` module.
- Any existing `docs/agent-monitoring/schema.md`-adjacent doc-consistency test (if one exists;
  check `tests/tools/test_current_run_sidecar_orchestrator.py`'s `test_schema_doc_*` cases as the
  established pattern) — the new schema section must not break any existing schema-doc assertion.

Architecture guard:

- `tools/gate_checks/doc_staleness_check.py`'s coverage (run as part of the pipeline, not a
  standalone pytest target) — confirm the new `docs/agent-monitoring/schema.md` and
  `docs/parity_ledger/infrastructure.yaml` edits are recognized as the required doc updates for the
  `src/`-adjacent `.claude/workflows/implement-ticket.js` and new
  `tools/agent-monitoring/*.py` diff.

## New Tests Required

- **`test_two_concurrent_session_sidecars_for_same_ticket_produce_one_detection`**
  Category: unit.
  Verifies: two `.claude/current_run.<session>` files, both with `run_id` == the same ticket ID and
  both within the recommended short window (mtimes set via `os.utime`), produce exactly one
  detection record when the new detection function/module runs from a third (or either) session's
  perspective — not zero, not more than one per invocation.
  Location: `tests/tools/test_ticket_claim_detection.py` (new file, mirroring
  `test_post_tool_hook.py`'s tmp-`cwd`-based subprocess-or-direct-import test style).

- **`test_single_session_sidecar_produces_zero_detections`**
  Category: unit.
  Verifies: exactly one `.claude/current_run.<session>` file exists for a given ticket ID (no other
  session's scoped file references the same `run_id`) — the detection call produces zero records.
  Location: `tests/tools/test_ticket_claim_detection.py`.

- **`test_instrumentation_never_raises_on_malformed_sidecar`**
  Category: unit / failure mode.
  Verifies: a `.claude/current_run.<other-session>` file containing invalid JSON, or valid JSON
  missing the `run_id` key entirely, does not raise — the detection call completes normally with no
  exception propagated, matching every other sidecar-reading call site's `try/except
  Exception: pass` convention in this codebase.
  Location: `tests/tools/test_ticket_claim_detection.py`.

- **`test_instrumentation_never_blocks_or_raises_regardless_of_detection_outcome`**
  Category: unit / architecture guard.
  Verifies: whether zero, one, or multiple other sessions are detected, the function/module's
  return value (or the wrapping `bash()` call's exit code, if driven through
  `implement-ticket.js`) never signals failure/refusal — asserts no `ClaimRefusedError`-shaped
  exception type exists anywhere in the new module (grep-based architecture guard, mirroring how
  this repo checks for absence of a pattern elsewhere), and that the new `bash(...)` call site in
  `implement-ticket.js` keeps the `2>/dev/null || true` fail-open suffix.
  Location: `tests/tools/test_ticket_claim_detection.py` (function-level) and
  `tests/tools/test_current_run_sidecar_orchestrator.py` (new case, for the JS call-site
  fail-open suffix — static source check, same style as its existing adjacency tests).

- **`test_stale_sidecar_outside_short_window_does_not_false_positive`**
  Category: unit / regression-prone edge case.
  Verifies: a `.claude/current_run.<other-session>` file with the same `run_id` but an `mtime`
  older than the recommended short-window threshold (e.g. set via `os.utime` to 30+ minutes in the
  past, well past the 15-minute recommendation and well short of the unrelated 24-hour prune
  threshold, so this test is unambiguous about which mechanism it exercises) produces zero
  detections — proving crashed/abandoned sessions' leftover sidecars don't false-positive.
  Location: `tests/tools/test_ticket_claim_detection.py`.

- **`test_own_session_sidecar_excluded_from_detection`**
  Category: unit.
  Verifies: the detecting session's own `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` file (which
  legitimately carries the same `run_id`/`tid` it is checking against) is excluded from the
  enumeration — a lone session must never detect itself as a second claimant.
  Location: `tests/tools/test_ticket_claim_detection.py`.

- **`test_ad_hoc_null_sentinel_sidecar_never_counted_as_a_claim`**
  Category: unit / regression-prone edge case.
  Verifies: a scoped sidecar written as the `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`
  null-valued sentinel (`{"run_id": null, ...}`) is never counted as a detected concurrent session,
  regardless of its mtime.
  Location: `tests/tools/test_ticket_claim_detection.py`.

- **`test_detection_record_written_to_dedicated_jsonl_not_runs_or_events`**
  Category: unit / architecture guard.
  Verifies: a real two-sidecar detection writes to the new `agent-monitoring/data/<iso-week>/
  claim_detections.jsonl` path (write-time `%G-W%V` bucketing, matching the existing
  `runs`/`events`/`tools` convention) and does **not** append to `runs.jsonl` or `events.jsonl` —
  guards against accidentally coupling the experimental signal to the schema-validated shards.
  Location: `tests/tools/test_ticket_claim_detection.py`.

- **`test_scope_phase_wires_detection_call_at_tid_confirmation_point`**
  Category: unit / static source guard.
  Verifies (source-string check, same style as `test_current_run_sidecar_orchestrator.py`'s
  existing adjacency tests): `implement-ticket.js` contains a call into the new detection module
  positioned after `const tid = ticketInfo.ticket_id` and before `writeSidecar`'s own definition —
  i.e. the recommended insertion point was actually used, not silently relocated during
  implementation without updating this artifact.
  Location: `tests/tools/test_current_run_sidecar_orchestrator.py` (new case, alongside its
  existing `test_scope_phase_has_sidecar_coverage`).

## Scoped Pytest Commands

```
pytest tests/tools/test_ticket_claim_detection.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_post_tool_hook.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v
```

If a broader agent-monitoring writer-path suite exists (confirm exact path during Test phase —
likely under `tests/agent-monitoring/` or `tests/tools/`), add it scoped, e.g.:

```
pytest tests/tools/ -k "sidecar or claim_detection or writer" -v
```

Never `pytest tests/` — scope stays within `tests/tools/` (the sidecar/hook/orchestrator domain)
plus wherever the new `tests/tools/test_ticket_claim_detection.py` lands.

## Anti-Drift Test Guards

- Re-running `tests/tools/test_current_run_sidecar_orchestrator.py` in full after the change is
  itself an anti-drift guard: any accidental relocation of the new detection call to sit between an
  existing `writeSidecar(...)` and its paired `agent(...)` call would fail
  `test_sidecar_bash_write_precedes_each_covered_agent_call` immediately.
- `test_stale_sidecar_outside_short_window_does_not_false_positive` (above) doubles as a guard
  against silently reusing `post_tool_hook.py`'s unrelated 24-hour prune threshold as the detection
  window — if a future edit collapses the two constants into one shared value, this test's
  30-minute fixture (chosen to sit strictly between the two real thresholds) will start failing
  once the shared value crosses 30 minutes, surfacing the conflation immediately.
- `test_detection_record_written_to_dedicated_jsonl_not_runs_or_events` guards against scope creep
  where a future edit starts appending detection records into `events.jsonl` as a new field family
  (the retrieval-event/shadow-reviewer-event pattern) instead of the dedicated file this plan
  recommends — a silent schema-coupling change that would need its own `record_events.py`
  `validate_record()` review this ticket never asked for.
- `test_epic_create_tickets_sidecar_orchestrator.py` and
  `test_settings_json_edit_write_hook_sidecar_scope.py` passing unmodified is itself the guard
  against silent scope-widening into `implement-epic.js`/`create-tickets.js`/the settings hook,
  which this ticket's Out of Scope explicitly forbids.
- `test_instrumentation_never_blocks_or_raises_regardless_of_detection_outcome`'s grep-based check
  for absence of any `ClaimRefusedError`-shaped raise is the direct guard against this ticket
  silently growing into the "build a lock" behavior the epic's kill-criteria gate defers.
