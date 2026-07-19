---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-COST-PROXY-WRITE-PATH
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260719-COST-PROXY-WRITE-PATH

## Regression Surface

- `tests/tools/test_record_events.py` — all pre-existing tests (except the one that directly
  encoded the anti-pattern this ticket fixes, see below) must keep passing unmodified.
- `tests/tools/test_current_run_sidecar_orchestrator.py` — all 12 tests must pass; one requires
  updating for the removed TOOL_STATS step's renumbering effect on `writeMonitoring`'s prompt.
- `tests/tools/test_record_run.py`, `tests/tools/test_cost_proxy.py`,
  `tests/tools/test_validate_agent_monitoring.py`, `tests/tools/test_generate_retro.py`,
  `tests/tools/test_step0_ts_orchestrator.py` — unaffected by this ticket's changes, must stay
  green as a regression guard.

## New Tests Required

- Deterministic-compute-overrides-caller-value: a record with a deliberately wrong
  `cost_proxy_score`/`tool_call_count` plus a real `tools.jsonl` fixture must be written with the
  hand-computed real value, not the caller's.
- Absent-`tools.jsonl` graceful degradation: no crash, both fields default to `0`/`0.0`.
- `implement-epic`/`create-tickets` non-interference: `compute_tool_stats()` called directly with
  `EPIC-`/`FOLDER-`/`CREATE-TICKETS-` prefixed run_ids must return an empty stats dict.
- Mixed-batch targeting: a batch containing both an `implement-ticket` and a non-`implement-ticket`
  record must compute stats only for the former.

## Test to Retire (encodes the anti-pattern being fixed)

`test_cost_proxy_score_field_written_to_events_jsonl` asserted a caller-supplied
`cost_proxy_score=42.5` is written through unchanged — this is exactly the "trust the LLM-computed
value" behavior this ticket removes. Replace with the deterministic-override test above rather than
keep both (keeping the old assertion would encode the bug as an intentional contract).

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_record_events.py -q
python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py -q
python3 -m pytest tests/tools/test_record_run.py tests/tools/test_cost_proxy.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py tests/tools/test_step0_ts_orchestrator.py -q
python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard"
```

## Anti-Drift Test Guards

- The deterministic-compute test must supply a fixture value clearly distinguishable from any
  plausible real computation (999999) so a silent pass-through regression (the exact bug) would be
  immediately, unambiguously caught rather than accidentally matching by coincidence.
- The mixed-batch test proves the `infer_workflow` gate is applied per-record within one batch, not
  just when the whole batch happens to be one workflow — guards against a future refactor that
  computes stats for the batch's first record's workflow and wrongly applies it to all.
