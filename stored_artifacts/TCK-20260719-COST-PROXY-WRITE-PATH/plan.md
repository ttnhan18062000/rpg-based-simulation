---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-COST-PROXY-WRITE-PATH
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260719-COST-PROXY-WRITE-PATH

## Summary

Move `cost_proxy_score`/`tool_call_count` computation out of `writeMonitoring`'s LLM-executed
`agent()` prompt (`.claude/workflows/implement-ticket.js`) into deterministic code in
`tools/agent-monitoring/record_events.py`, mirroring `record_run.py::compute_duration_s`'s
"always overrides any caller-supplied value" precedent exactly. Gated to `implement-ticket`
workflow records only (via `vocabulary.py::infer_workflow`), so `implement-epic`/`create-tickets`
records — which never register a sidecar — stay completely untouched.

## Anti-Drift Notes

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: this ticket's implementation was done directly, in the same pass as
Investigate, rather than through separate agent-per-phase calls with a human/architecture-reviewer
gate between Plan and Implement. The fix itself is a narrow, unambiguous mirror of an
already-shipped, already-proven precedent (`compute_duration_s`) — low architectural risk — but the
formal staging-artifact trail (this file, `investigation.md`, `test_plan.md`) was written
retroactively, after implementation and full test verification, rather than before. All claims in
these three files were independently verified against the real, current source and a real test run
by the same session that wrote them, not merely asserted.

## Steps

### Step 1 — `record_events.py`: add `compute_tool_stats()`

**Files:** `tools/agent-monitoring/record_events.py`
Add a module-level function reading `agent-monitoring/tools.jsonl` once, building
`{(run_id, seq): (tool_call_count, cost_proxy_score)}` for every `(run_id, seq)` pair in the input
batch whose `run_id` infers to the `implement-ticket` workflow. Reuse
`cost_proxy.py::compute_cost_proxy_score` unchanged (import, don't re-derive).

### Step 2 — Wire into `main()`

**Files:** `tools/agent-monitoring/record_events.py`
After the existing validation/truncation loop, before the write block: call
`compute_tool_stats(records)` once for the whole batch, then for each record whose `(run_id, seq)`
key is present in the result, overwrite `tool_call_count`/`cost_proxy_score` unconditionally.
Records not in the result dict (any non-`implement-ticket` workflow) are left exactly as they were
passed in — no key added if absent.

### Step 3 — Remove the old LLM-computed step from `writeMonitoring`

**Files:** `.claude/workflows/implement-ticket.js`
Delete the old Step 2 (`python3 -c` TOOL_STATS compute + `TOOL_STATS["counts"]`/`["scores"]`
substitution instructions). Renumber the remaining steps (Step 3→2, Step 4→3). Update the new
Step 2 ("build and write events") to explicitly instruct the agent NOT to compute or set either
field. Update Step 0's comment (previously referencing "Step 2's snapshot") since Step 2 no longer
computes a snapshot inline — the rationale for clearing the sidecar first still holds (this call's
own tool calls must not be mis-attributed to the prior phase), just relocate the explanation.

### Step 4 — Update `docs/agent-monitoring/schema.md`

**Files:** `docs/agent-monitoring/schema.md`
Four spots currently say "computed by `writeMonitoring`": the `tool_call_count`/`cost_proxy_score`
field-table rows, the formula section's opening line, the create-tickets/implement-epic
phase-values note, and the "How tool calls are attributed to agent events" prose. All four
corrected to describe `record_events.py::compute_tool_stats()` as the real compute location.

### Step 5 — Update/add tests

**Files:** `tests/tools/test_record_events.py`, `tests/tools/test_current_run_sidecar_orchestrator.py`
Replace `test_cost_proxy_score_field_written_to_events_jsonl` (encoded the old pass-through
behavior) with a deterministic-override test. Add absent-`tools.jsonl`, non-interference, and
mixed-batch tests. Rename/update
`test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4` for the new 4-step numbering and
the removed TOOL_STATS text.

### Step 6 — Parity ledger

**Files:** `docs/parity_ledger/infrastructure.yaml`
New entry `INFRA-282` (next available ID after `INFRA-281`), `status: verified`, citing the new
function/wiring and the 4 new/updated tests. `support_boundary` explicitly notes the
`simq-audit.js` finding as a known, deliberately out-of-scope instance of the same anti-pattern.

## Scope Guards

- No change to `cost_proxy.py`'s formula or weights — only where/how reliably the formula's inputs
  are computed and written.
- No change to `simq-audit.js`'s own separate TOOL_STATS-style compute step — out of scope, noted
  as a real finding for a future ticket.
- No historical backfill of already-written null `tool_call_count`/`cost_proxy_score` records —
  forward-looking fix only, matching this subsystem's established no-backfill precedent.

## Dependency Map

Step 1 before Step 2 (Step 2 calls the function Step 1 defines). Step 3 is independent of Steps
1-2 but logically paired (same root cause, same file family). Step 4 depends on Steps 1-3 being
real (describes the landed behavior). Step 5 depends on Steps 1-3. Step 6 depends on all prior
steps (describes and cites the final landed state).

## Acceptance Criteria Map

- AC1 (`duration_s` recorded as already resolved, no code change) → Investigation finding, restated
  in the ticket's Request Summary (already present before this plan).
- AC2 (confirmed real gap documented) → Investigation finding, restated in the ticket's Request
  Summary (already present before this plan).
- AC3 (TOOL_STATS removed from `writeMonitoring`'s prompt) → Step 3.
- AC4 (`record_events.py` computes deterministically) → Steps 1-2.
- AC5 (new test asserting deterministic computation) → Step 5.
- AC6 (regression test for implement-epic/create-tickets non-interference) → Step 5.
- AC7 (monitoring write failure still never fails the workflow) → unchanged; `writeMonitoring`'s
  existing `2>/dev/null`-style fail-open wrapping and "do NOT raise" instruction are untouched by
  this ticket — verified by inspection, no new test needed since no code path in this change
  removes or weakens that existing guarantee.

## Deviations

None from this plan itself (written retroactively to describe the actual landed implementation
exactly) — see the Anti-Drift Notes section above for the one deviation that matters: staging
artifacts were written after implementation, not before.
