---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-GAP
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260915-SIDECAR-ATTRIBUTION-GAP

## Disposition: accept with a documented, ratcheted floor (AC #2)

A structural fix is out of this ticket's reasonable scope on either candidate mechanism:
guaranteeing 100% `writeSidecar()` compliance across every hand-orchestrating session on this
machine is a process-discipline problem, not a code fix this ticket can land; and confirming/fixing
a subagent-vs-orchestrator session-id mismatch (if that's part of the cause) would mean redesigning
how `.claude/current_run.<session_id>` identity is threaded through `Agent()` dispatch across three
separate workflow scripts — a cross-cutting architecture change, not a targeted repair. Per
`SEQUENCE.md`'s own explicit allowance, "accept and document" is the disposition here, backed by
the classification evidence in investigation.md rather than asserted by default.

## `tools/agent-monitoring/generate_retro.py` — coverage disclosure (AC #3)

`compute_retro_metrics()` already computes `scored_events` (events with `cost_proxy_score`) before
building `spend_proxy_by_phase`/`by_agent` — add a `spend_proxy_coverage` key to the returned dict:
`{"events_scored": len(scored_events), "events_total": len(events), "coverage_pct": round(100 *
len(scored_events) / len(events), 1) if events else None}`. Render it as a one-line note directly
above both Spend Proxy tables in `generate()`, e.g. "_Computed over 30.5% of this window's events
(579 of 1,897 scored) — see TCK-20260915-SIDECAR-ATTRIBUTION-GAP for why the rest lack a
`cost_proxy_score`._" This directly satisfies AC #3's literal wording.

## Ratchet check

New `tools/gate_checks/sidecar_attribution_coverage_check.py`: computes the tool-row attribution
rate (`1 - unattributed/total`) over the real corpus and PASSes if it is at or above a measured
floor, FAILs if it drops further. **This ratchets upward (a floor), the mirror image of every
other check in this batch** (which ratchet a ceiling on a defect count) — ceiling-style ratchets
don't fit a coverage-percentage metric, so the floor/PASS-above direction is the correct shape
here, disclosed explicitly since it's the first of this shape in the batch. Baseline: measured
14-day attribution rate, **75.3%** (100% - 24.7%) — re-derive at implementation time. A FAIL means
attribution coverage got WORSE, which is the direction actually worth catching (a new code path
that fails to call `writeSidecar()`, or a broader-than-expected subagent gap).

## Tests

- `tests/tools/test_generate_retro.py`: extend with a test proving `spend_proxy_coverage` is
  computed and rendered when `events` is non-empty, and gracefully omitted (not a `ZeroDivisionError`)
  when `events` is empty.
- `tests/tools/test_sidecar_attribution_coverage_check.py` (new): floor-check pass/fail, the
  floor-may-only-increase-or-stay pin (mirrored from the ceiling-may-only-decrease convention),
  real-corpus check, Makefile wiring.

## No fix to `post_tool_hook.py`/`.claude/current_run` itself in this ticket

Per the accept-with-floor disposition above — the mechanism investigation.md found (mixed-session
hand-orchestration compliance gaps, possibly compounded by a subagent session-id mismatch) needs
either a much larger architecture change or ongoing process discipline, neither of which this
ticket implements. The subagent-session-id hypothesis is recorded as an open question for
`TCK-20260915-MONITORING-ANOMALY-VALIDATOR` or a dedicated follow-up, not silently dropped.
