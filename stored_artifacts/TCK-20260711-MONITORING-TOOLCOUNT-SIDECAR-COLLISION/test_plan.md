---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
artifact_type: test_plan
tags: [agent-monitoring, data-quality, root-cause]
---

# Test Plan — TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

Not yet executed — implementation is deferred. This records what a future implementation session must cover.

## Regression test: reproduce the collision deterministically

Before any fix lands, add a test that reproduces Finding 3's mechanism directly (not just asserts the fix's happy path) — write two sidecar updates in sequence with overlapping "tool call" events in between, and assert that under the *current* (pre-fix) code, attribution is wrong; this is the test that should flip from failing to passing once the fix lands, proving the fix addresses the actual traced mechanism rather than a different, easier-looking problem.

```python
def test_interleaved_sidecar_writes_do_not_cross_attribute(tmp_path, monkeypatch):
    # Simulate: run A's writeSidecar(seq=5) is written, some tool calls happen,
    # then run B's writeSidecar(seq=1) overwrites the same shared file mid-flight
    # of run A's still-in-progress phase, then more tool calls happen that
    # actually belong to run A but read run B's sidecar value.
    ...
    # Assertion depends on chosen fix (Option A/B/C from plan.md); at minimum,
    # assert no tool call ends up attributed to a run_id it didn't belong to.
```

## Drift-detection tool tests

For the new `validate.py` check (workstream 2 in plan.md):
- Unit test with synthetic `events.jsonl`/`tools.jsonl` fixtures covering: exact match (no drift reported), over-count, under-count, zero-actual-with-nonzero-recorded (this ticket's traced case shape).
- Integration-style test against a small real slice of current `agent-monitoring/` data, asserting the tool reports a drift count `>= 0` without crashing (guards against the tool itself breaking on legacy-shape records, same defensive pattern `validate.py`'s existing incomplete-run check already uses for `LEGACY_COMPLETION_FIELDS`).

## Prevention-mechanism tests (depends on chosen option from plan.md)

- **If Option A (per-run sidecar filename):** test that two run-scoped sidecar files can coexist without the discovery step picking the wrong one; test the discovery step's own tie-breaking logic under a simulated near-simultaneous write.
- **If Option B (nonce/timestamp):** test that a stale nonce is correctly rejected by the hook, and that the orchestrator's read-after-write check correctly detects and retries a lost write.
- **If Option C (session/timestamp reconstruction):** test the join logic directly against a synthetic `runs.jsonl`/`events.jsonl`/raw-tool-log fixture with two overlapping runs, asserting correct reconstruction.

## Full existing suite

Run the full `tools/agent-monitoring/` test suite (`pytest tests/tools/ -k agent_monitoring` or equivalent scoped path — confirm exact path at implementation time) to confirm no regression in the existing incomplete-run/legacy-shape handling that `TCK-20260705-MONITORING-RUNID-JOIN` already established as correct.

## Acceptance gate

Before closing the eventual implementation ticket: re-run this investigation's own cross-check script (see `investigation.md`'s Method section) against a batch of new post-fix runs and confirm the mismatch rate is at or near 0% for anything produced after the fix lands (historical data remains uncorrected, per the explicit non-goal).

---

## Addendum — what was actually executed

The mechanism turned out deterministic (see `investigation.md`/`plan.md` addenda), so the collision-simulation tests originally sketched above (interleaved sidecar writes, session/timestamp reconstruction) were unnecessary — the actual fix is two static, always-true code changes, verified the same way the rest of `.claude/workflows/implement-ticket.js` already is: raw-source-text-parsing tests (no JS runtime exists for this file in this repo).

- `tests/tools/test_current_run_sidecar_orchestrator.py`: `test_scope_phase_call_site_has_no_preceding_sidecar_write` replaced with `test_scope_phase_has_sidecar_coverage` (asserts both branches — real sidecar write when resuming, clear-to-`{}` when creating new); `test_writeMonitoring_step5_sidecar_clear_still_present` replaced with `test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4` (asserts Step 0 precedes Steps 1-4, and that the old trailing "Step 5" label is fully gone, not duplicated). All 11 tests in this file pass.
- `tests/tools/test_validate_agent_monitoring.py`: 6 new tests for `compute_tool_count_drift_report` (agreement case, undercounted-mismatch case reproducing the real `recorded=0/actual=34` shape, overcounted-mismatch case reproducing the real `recorded=2/actual=0` shape, null-field skip, cross-run-pollution-immunity for interactive `run_id: null` tool rows, read-only guarantee).
- Full regression suite run before closing: `tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_cost_proxy.py` — 66/66 pass.
- Live verification: `compute_tool_count_drift_report` invoked directly against the real `agent-monitoring/events.jsonl`/`tools.jsonl` reproduces the exact 433/1247 mismatch count from the manual audit, confirming correctness. `validate.py`'s `main()` itself currently exits before reaching this report due to 6 pre-existing, unrelated `errors` (orphaned `FOLDER-*`/legacy runs with zero events) — out of scope for this ticket to fix; the new report's wiring is otherwise correct and will print for any future clean run.
