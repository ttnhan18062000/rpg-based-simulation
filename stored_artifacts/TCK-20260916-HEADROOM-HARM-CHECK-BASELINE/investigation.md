# Investigation — TCK-20260916-HEADROOM-HARM-CHECK-BASELINE

## Window choice

The ticket's own Request Summary already established the corpus "moved substantially during
2026-09-15/16" — six tickets closed in PR #211 alone, plus gate removals that changed which
checks run at all. Any window including data from before that point would describe a different
system. Chose `2026-09-16` (UTC, ISO date) as the window start, ending at report-generation time
(a live snapshot, not a fixed historical range, since "now" is the moment right before any real
trial activity begins). Checked the actual population this window contains before committing to
it: 42 runs, 252 events, 4956 tools rows — inside the ticket's own stated 16–70 runs/week
expectation.

## `session_id` reliability, checked directly rather than assumed

```
tools rows with session_id present: 233161 / 233163 = 100.0%
```
across the entire corpus's history (not just the chosen window). Within the window itself, the
rate is `1.0`. This directly answers the ticket's own flagged open question: yes, `session_id` is
reliable enough for a later harm check to isolate a trial session's own rows from concurrent
sessions.

## The `tool_call_count` finding

Initial computation showed every phase in the window reading `mean: 0.0` for `tool_call_count`.
Rather than reporting this as "no tool activity happened" (false) or silently omitting the field
(misleading), traced the cause: `infer_workflow(run_id)` classifies all 42 runs in the window as
`implement-ticket` by run_id *shape* alone — it cannot distinguish a hand-orchestrated closure
(`record_hand_orchestrated_closure.py`, which writes events with `tool_call_count` left at
whatever it was passed, typically 0/unset since no live per-phase sidecar tracked calls as they
happened) from a real formal-pipeline run (where `record_events.py::compute_tool_stats()` derives
a real per-phase count from `tools.jsonl` at write time). Direct check: `events with
tool_call_count > 0: 0 / 37` in the window's own real events. This is the same structural gap
`TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` already names, now confirmed
to affect this exact baseline window. Recorded as an explicit report field
(`tool_call_count_hand_orchestration_caveat`) rather than a silent `null`.

## Where the new function lives, and where it deliberately doesn't

`build_baseline_report()`'s own dict has a fixed key set pinned by
`test_baseline_report_cli_runs_against_real_corpus_and_prints_json`, a test belonging to a
different, already-closed ticket (`TCK-20260728-RETRIEVAL-BASELINE-METRICS`). Adding a new key to
that dict would risk exactly the drift that pin exists to catch — the same trap already found and
avoided once this session while building `TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-
WHOLE-FILE-READS`'s own `read_ranged_baseline.py` (there, resolved by writing a fully separate
script; here, since this ticket explicitly prefers extending the existing file, resolved instead
by adding a new function *and* a new, additive, opt-in CLI flag that produces a distinct report
only when explicitly requested, leaving the flag-less default path — and its pinned test — byte-
for-byte unaffected). Confirmed directly rather than assumed:
`test_cli_without_flag_still_produces_the_original_pinned_report_shape`.
