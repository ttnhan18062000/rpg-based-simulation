---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-HARM-CHECK-BASELINE
phase: done
date: 2026-09-16
tags: [agent-monitoring, benchmarking, process-improvement]
---

# TCK-20260916-HEADROOM-HARM-CHECK-BASELINE

## Title
Capture the pre-trial agent-monitoring baseline **before** Headroom is enabled — a baseline measured
afterwards is worthless, and no existing one can be reused

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Second child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`. Depends on nothing except being
done *before* the trial starts.

The epic must detect whether compression degrades agent behaviour. That requires a comparison point
captured while compression is off. No earlier baseline can be reused: the corpus moved substantially
during 2026-09-15/16 (six tickets closed in PR #211 alone, plus gate removals that changed which
checks run at all), so any pre-existing figure describes a different system.

**What this baseline is not.** It is not a cost or token baseline. `docs/agent-monitoring/schema.md`
is explicit that token counts are not recorded and there is "no workaround within the current
platform," and `cost_proxy_score` is computed from tool-call *shape*, not tokens — so it would stay
flat regardless of how much Headroom saves. Treating it as a savings metric would measure the wrong
thing entirely. Savings are measured separately, from Headroom's own ledger.

## Scope
- Record, over a defined pre-trial window, the scale-invariant *rates* that the harm check will
  later compare against:
  - `final_status` DONE-rate; per-event `failed` / `blocked` rate
  - `reason_code` frequency distribution
  - `tool_call_count` per phase — the over-compression detector: if compression drops something the
    agent needed, it calls `headroom_retrieve` to recover it, inflating tool calls per phase
- Record the window's own boundaries (dates, run count, event count) so the comparison window can be
  matched rather than eyeballed.
- Prefer extending `tools/agent-monitoring/retrieval_baseline_metrics.py` — it already has a real
  CLI (`argparse`, `main()`, `__main__`) and section builders for duration, gate outcome, and review
  rework — over writing a new one-off script.

## Out of Scope
- Enabling Headroom, or any compression. This ticket runs against the current, uncompressed system.
- Building a token baseline. Platform-blocked; see Request Summary.
- Changing what monitoring records. This is a **read-time-only** derivation, following the precedent
  of `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT`, which computes a derived split without ever mutating
  `runs.jsonl`/`events.jsonl`.
- Any new gate, ratchet, or blocking check over these numbers. They are a comparison point, not a
  threshold — and per the standing principle that agent-working checks stay proportionate, a
  blocking gate here would be actively wrong.

## Acceptance Criteria
- [x] A baseline record exists with each rate above, plus the window boundaries and population
      counts that produced it. See Completion Summary for the real numbers.
- [x] Every figure is reproducible by re-running a recorded command — not transcribed by hand.
      `python3 tools/agent-monitoring/retrieval_baseline_metrics.py --harm-check-window-start
      2026-09-16` (recorded exactly, in Test Summary).
- [x] The baseline explicitly states its own statistical limit: at roughly 16–70 runs/week this is a
      coarse tripwire, able to catch "noticeably worse" but not a subtle few-percent regression.
      `statistical_limit` field in the report, verbatim.
- [x] No new blocking check, gate, or ratchet is introduced. Confirmed: the new
      `--harm-check-window-start` flag is opt-in, additive, and produces a plain JSON report to
      stdout — nothing calls it automatically, nothing fails a build on its values.
- [x] Nothing under `agent-monitoring/data/` is mutated.
      `test_cli_does_not_mutate_agent_monitoring` (git-porcelain before/after, matching the
      module's own existing zero-diff test's pattern).

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` (done) — the read-time-only derived-metric precedent
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — why no token baseline is possible

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Measurement section
- `docs/agent-monitoring/schema.md` — "What is not recorded"

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-HEADROOM-HARM-CHECK-BASELINE/investigation.md`
- `stored_artifacts/TCK-20260916-HEADROOM-HARM-CHECK-BASELINE/plan.md`
- `stored_artifacts/TCK-20260916-HEADROOM-HARM-CHECK-BASELINE/test_plan.md`

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (`build_baseline_report`,
  `build_gate_outcome_section`, `build_review_rework_section`)
- `tools/agent-monitoring/generate_retro.py`
- `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`

## Assumptions / Open Questions
- ~~The pre-trial window length is the implementer's call~~ — **resolved: `2026-09-16` through
  report-generation time**. Chosen because the ticket's own Request Summary already establishes
  that the corpus "moved substantially during 2026-09-15/16" — anything before that describes a
  different system, so the window starts at the stabilization point, not earlier. This yields 42
  runs / 252 events / 4956 tools rows, comfortably inside the ticket's own stated 16–70 runs/week
  expectation for a several-day window.
- ~~`tools.jsonl` carries `session_id`... Verify that it is populated consistently enough to
  rely on~~ — **resolved: yes, reliable**. `session_id_population_rate` is checked directly
  against the real corpus (`233,161/233,163` = effectively 100% across the *entire* corpus's
  history, and `1.0` within the chosen pre-trial window specifically) — the harm check's future
  ability to isolate trial-session rows by `session_id` is not a leap of faith.

## Implementation Notes
Use the Python interpreter that matches CI (3.13) when running anything that must agree with CI
behaviour; this repo has two environments and using the wrong one has produced false "matches CI"
evidence before. Used `.venv313` throughout.

Extended `tools/agent-monitoring/retrieval_baseline_metrics.py` per the ticket's own stated
preference, rather than writing a new one-off script — reused `_resolve_status`, `_is_gate_fail`,
and the existing `load_all_sources()`/CLI scaffolding. **Did not add the new section to
`build_baseline_report()`'s own dict** — that report's exact key set is pinned by a different,
already-closed ticket's own test
(`test_baseline_report_cli_runs_against_real_corpus_and_prints_json`), and mixing an unrelated
ticket's fields into it would risk exactly the kind of drift that pin exists to catch (the same
trap discovered and avoided while building `TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-
WHOLE-FILE-READS`'s own baseline script). Instead added a new, additive, opt-in CLI flag
(`--harm-check-window-start`) that prints a **separate** report only when explicitly requested —
confirmed the flag-less default output is byte-for-byte the same shape the existing pinned test
expects (`test_cli_without_flag_still_produces_the_original_pinned_report_shape`).

**Deliberately excludes any Agent-tool-call duration metric.** Per the epic's own carried-forward
finding (`TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE`): an `Agent` row's own
`duration_ms` times only the async-launch confirmation (~2s), never the dispatched work itself —
a confirmed finding, not a hypothesis. This baseline's own metrics (DONE-rate, per-event failed/
blocked rate, reason_code frequency, tool_call_count per phase) never touch `duration_ms` for
this reason; a future extension that adds one must carry this caveat forward explicitly, stated
directly in the new function's own docstring so it isn't rediscovered the hard way.

**A real, load-bearing finding surfaced while computing this, not assumed away**:
`tool_call_count_per_phase` reads flat zero for every phase in the chosen window. This is not
because no tool calls happened — it's because this window's real activity is dominated by
hand-orchestrated ticket closures (`record_hand_orchestrated_closure.py`), which never had a live
per-phase sidecar tracking tool calls as they occurred (the same structural gap
`TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` already names). The
over-compression detector this field is meant to serve will read as flat zero for a
hand-orchestrated trial too, for the identical reason — recorded as an explicit
`tool_call_count_hand_orchestration_caveat` field in the report itself (not silently `null`), so
whoever reads a future comparison against this baseline sees the caveat inline rather than having
to rediscover it.

**Captured explicitly before any real trial activity**: the smoke test already run under
`TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL` compressed only synthetic payloads via
explicit MCP tool calls — it changed no session's own behavior and is not part of the window this
baseline measures. Stated directly in the report's own `trial_not_yet_started_note` field so a
reader doesn't have to wonder or cross-reference another ticket to confirm it.

## Test Summary
- `pytest tests/tools/test_headroom_harm_check_baseline.py -v`: 11 passed (new file) — window
  filtering, DONE-rate/event-rate computation, reason_code frequency, tool_call_count-per-phase
  None-vs-zero handling, the hand-orchestration caveat (both present and absent cases),
  session_id population rate, an empty-window no-crash case, the two distinct CLI report shapes
  (with and without the new flag), and a zero-mutation check.
- `pytest tests/tools/test_retrieval_baseline_metrics.py -v`: 20 passed — confirms the existing,
  already-pinned report shape and its own tests are completely unaffected by this addition.
- `pytest tests/tools/ -m "not slow and not extra_slow" -q`: 2767 passed, 0 failed.
- Real command run against the actual corpus, recorded verbatim:
  `python3 tools/agent-monitoring/retrieval_baseline_metrics.py --harm-check-window-start
  2026-09-16` → `done_rate: 1.0`, `per_event_failed_rate: 0.0`, `per_event_blocked_rate: 0.0`,
  `reason_code_frequency: {}`, `session_id_population_rate: 1.0`,
  `population: {run_count: 42, event_count: 252, tools_count: 4956}`,
  `tool_call_count_per_phase`: all 6 phases present with `mean: 0.0` (the hand-orchestration
  caveat correctly fired).

## Files Changed
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — added
  `build_harm_check_baseline_section()` and the `--harm-check-window-start` CLI flag; the
  existing `build_baseline_report()`/default CLI behavior is untouched.
- `tests/tools/test_headroom_harm_check_baseline.py` (new)
- `tickets/todos/` → `tickets/done/TCK-20260916-HEADROOM-HARM-CHECK-BASELINE.md`
- `stored_artifacts/TCK-20260916-HEADROOM-HARM-CHECK-BASELINE/` (new)

## Completion Summary
Captured the pre-trial baseline the epic's own harm check will later compare against, extending
the existing baseline tool rather than writing a new script, and without touching the exact
report shape a different, already-closed ticket's own test pins. Window: `2026-09-16` (the
corpus's own stated stabilization point) through report-generation time — 42 runs, 252 events,
4956 tools rows. Real numbers: `done_rate=1.0`, `per_event_failed_rate=0.0`,
`per_event_blocked_rate=0.0`, empty `reason_code_frequency`, `session_id_population_rate=1.0`
(the isolation question this ticket flagged is answered: yes, reliable). The one genuinely
load-bearing finding — `tool_call_count_per_phase` reads flat zero because this window's real
activity is dominated by hand-orchestrated closures with no live per-phase sidecar, not because
nothing happened — is recorded as an explicit field in the report itself, not glossed over, since
it will affect how any future comparison against this baseline should be read. Carried the
fork-relay finding forward as a documented exclusion (no Agent-duration metric here) rather than
silently reproducing the mistake that finding was meant to prevent, and stated explicitly that
the prior smoke test's synthetic-payload MCP calls are not part of this window's measured
activity.
