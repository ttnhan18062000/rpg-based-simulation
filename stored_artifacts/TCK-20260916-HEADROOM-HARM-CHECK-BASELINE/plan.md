# Plan — TCK-20260916-HEADROOM-HARM-CHECK-BASELINE

1. Pick and justify a pre-trial window (see investigation.md) — `2026-09-16` through report time.
2. Check `session_id` population directly against the real corpus before relying on it in the
   design.
3. Extend `tools/agent-monitoring/retrieval_baseline_metrics.py` with
   `build_harm_check_baseline_section(runs, events, tools, window_start_ts)`, reusing
   `_resolve_status`/`_is_gate_fail` rather than reimplementing status logic, computing:
   DONE-rate, per-event failed/blocked rate, `reason_code` frequency, `tool_call_count` per phase
   (excluding `None` rather than treating it as 0), `session_id` population rate, the window's own
   population counts, and the ticket's own required statistical-limit disclosure string.
4. Wire a new, additive, opt-in `--harm-check-window-start` CLI flag rather than merging into
   `build_baseline_report()`'s own pinned dict (see investigation.md for why).
5. Deliberately exclude any Agent-tool-call duration metric, carrying the fork-relay finding
   forward in the new function's own docstring.
6. Run against the real corpus, record the exact numbers and the exact reproducing command in the
   ticket (never transcribed by hand from a different run).
7. Write tests: window filtering, rate computation, `None`-vs-zero handling for
   `tool_call_count`, the hand-orchestration caveat (both present and absent), an empty-window
   case, both CLI report shapes, and a zero-mutation check.
8. Run the full `tests/tools/` suite to confirm the existing pinned report and its tests are
   unaffected.
9. Close via the standard hand-orchestrated path: `stored_artifacts/`,
   `record_hand_orchestrated_closure.py`, `docs/REGISTRY.yaml` regeneration.
