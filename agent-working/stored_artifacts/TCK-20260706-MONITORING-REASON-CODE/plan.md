---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260706-MONITORING-REASON-CODE
artifact_type: plan
tags: [agent-monitoring, tagging, reporting]
---

# Plan — TCK-20260706-MONITORING-REASON-CODE

## Steps

1. **`tools/gate_checks/done_checker_static.py`**: add
   `classify_checklist_failure(checklist: list[dict]) -> str | None` near `run_static_precheck`.
   Iterates `checklist` in order, returns on the first `status == "FAIL"` entry:
   `"tag_registry_rejection"` if `"is not in the tag registry" in evidence`, else
   `"dod_condition_failed"`. Returns `None` if no `FAIL` entries exist (all `PASS`/`NA`).

2. **`.claude/workflows/implement-ticket.js`**:
   - `pushEvent` signature: `(phaseLabel, agentName, status, summary, ts, toolCallCount,
     reasonCode)` — `reasonCode` defaults to `null`, included in the pushed object as
     `reason_code: reasonCode || null`.
   - Immediately before the existing `if (doneCheck.verdict !== 'READY_TO_CLOSE')` block's
     `pushEvent` call, add a `bash()` call classifying `doneCheck.checklist`:
     ```js
     const checklistJson = JSON.stringify(doneCheck.checklist).replace(/'/g, "'\\''")
     const reasonCodeOutput = await bash(
       `python3 -c "
     import sys, json
     sys.path.insert(0, 'tools')
     from gate_checks.done_checker_static import classify_checklist_failure
     checklist = json.loads(sys.argv[1])
     print('REASON_CODE_JSON:' + json.dumps(classify_checklist_failure(checklist)))
     " '${checklistJson}'`
     )
     ```
     Parse via `indexOf('REASON_CODE_JSON:')`, matching the Architecture-Verify precedent exactly.
     Pass the parsed value as the 7th arg to the `Verify`/`failed` `pushEvent` call only.
   - No other `pushEvent` call site touched (11 other call sites keep their current 5-6 args;
     `reasonCode` positional arg is simply omitted → defaults to `null`, per JS default-parameter
     semantics — no need to touch them at all).

3. **`docs/agent-monitoring/schema.md`**: add `reason_code` to the `events.jsonl` field table —
   type string, nullable, "populated only for `Verify`/`failed` events today; `null` for every
   other phase/status and for all pre-existing records (same growth pattern as `tool_call_count`)."
   List the 2 known values with one-line meanings. Explicit note: not a closed enum — a future
   phase found to have its own catch-all-status problem could add its own value later, but none is
   added speculatively here.

4. **`tools/agent-monitoring/generate_retro.py`**: in the per-agent aggregation section, add a
   small block — for `done-checker` events specifically with a non-null `reason_code`, tally counts
   and add a line to the report (e.g. `Verify block reasons: tag_registry_rejection=2,
   dod_condition_failed=1`). Only render this line when at least one `reason_code` is present in
   the input window (don't print an empty/zero-value section for weeks with no DOD_BLOCKED runs).

5. **Tests**: `tests/tools/test_done_checker_static.py` — add a small test class for
   `classify_checklist_failure`: all-pass → `None`; single FAIL with tag-registry substring in
   evidence → `"tag_registry_rejection"`; single FAIL with unrelated evidence →
   `"dod_condition_failed"`; FAIL not in the first position (confirms it scans, not just checks
   index 0); NA-only entries mixed with one FAIL (confirms NA doesn't trigger a false positive).

## Verification

- `pytest tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py -v`
- Full `tests/tools/` regression to confirm no unrelated breakage.
- Manual JS review: read the edited `implement-ticket.js` section end-to-end to confirm the
  `bash()` call, marker-parsing, and `pushEvent` call are syntactically and logically consistent
  with the Architecture-Verify precedent — no automated JS test harness exists in this repo for
  workflow scripts, so this is a read-through, not a run (disclosed, not hidden).
- `python3 tools/agent-monitoring/generate_retro.py --all` (or whatever the existing invocation is)
  against the live `agent-monitoring/*.jsonl` to confirm it still runs without error with the new
  aggregation code present (even though no live event currently carries a `reason_code`, since no
  ticket has gone through the new code path yet — the report should simply omit the new section).

## Out of scope reaffirmed

No retrofitting other phases, no `create-tickets.js` changes, no skill-suggestion-follow-through
tracking, no `validate.py` changes (confirmed unnecessary — it doesn't enforce a closed field set).
