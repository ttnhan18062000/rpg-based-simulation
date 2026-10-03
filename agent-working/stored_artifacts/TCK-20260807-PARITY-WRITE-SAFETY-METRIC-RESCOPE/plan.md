---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE
artifact_type: plan
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE

## Code change (`tools/agent-monitoring/generate_retro.py`)

1. Add a new helper `_is_parity_index_build_call(tool_row)` — extracted from
   `_is_unsafe_parity_build_call`'s own precondition (`tool == "Bash"`, `"parity_index.py" in
   summary`, `"build" in summary`), reused as the co-occurrence signal. (Do not just call
   `_is_unsafe_parity_build_call` itself for this — that function's job is "is this ONE call
   unsafe", which additionally requires a missing/real `--db-path`; a co-occurring SAFE
   scratch-path build still establishes real risk-adjacent behavior in that run and should still
   count as the qualifying signal. `_is_parity_index_build_call` is the shared, broader
   "did this run touch parity_index.py's build path at all" precondition both functions need.)
   Refactor `_is_unsafe_parity_build_call` to call the new helper for its own first two checks,
   avoiding duplicated logic.
2. In `compute_tool_safety_metrics`, before computing `parity_yaml_writes`: build
   `run_ids_with_build_calls = {r.get("run_id") for r in tools if _is_parity_index_build_call(r) and r.get("run_id")}`.
   Change `parity_yaml_writes` to `[r for r in tools if _is_parity_ledger_yaml_write(r) and r.get("run_id") in run_ids_with_build_calls]`.
3. Update `compute_tool_safety_metrics`'s docstring: "zero-tolerance count of Edit/Write calls into
   docs/parity_ledger/*.yaml" → "count of Edit/Write calls into docs/parity_ledger/*.yaml made in a
   run that ALSO invokes parity_index.py's build path — a normal parity-ledger edit alone is not
   flagged."
4. Find and update the report-render function's "Parity Ledger Write-Safety" heading/prose (the
   Markdown-render call site for this section) to describe the new, narrower semantics.

## Test changes (`tests/tools/test_generate_retro.py`)

Per test_plan.md: update `test_parity_write_safety_detects_edit_targeting_parity_ledger_yaml` to
add a same-run_id build call; add 3 new tests (lone-edit-no-longer-counts,
different-run-ids-not-flagged, help-call-does-not-count).

## Acceptance-criteria map

| AC | Step |
|---|---|
| investigation.md confirms rescope logic + baseline preservation | Investigate (done) |
| `_is_parity_ledger_yaml_write` rescoped (co-occurring build required) | Code change steps 1-2 |
| report heading/copy updated | Code change step 4 |
| `test_generate_retro.py` parity tests updated to new semantics | Test changes |
| real-corpus re-verification shows no ordinary-edit false positives | Already confirmed in investigation.md; re-run `--all` at Test phase |
| scoped pytest passes | `pytest tests/tools/test_generate_retro.py -q` |
