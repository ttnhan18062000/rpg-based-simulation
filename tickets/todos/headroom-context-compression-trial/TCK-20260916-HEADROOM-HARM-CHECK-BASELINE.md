---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-HARM-CHECK-BASELINE
phase: open
date: 2026-09-16
tags: [agent-monitoring, benchmarking, process-improvement]
---

# TCK-20260916-HEADROOM-HARM-CHECK-BASELINE

## Title
Capture the pre-trial agent-monitoring baseline **before** Headroom is enabled — a baseline measured
afterwards is worthless, and no existing one can be reused

## Status
OPEN

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
- [ ] A baseline record exists with each rate above, plus the window boundaries and population
      counts that produced it.
- [ ] Every figure is reproducible by re-running a recorded command — not transcribed by hand.
- [ ] The baseline explicitly states its own statistical limit: at roughly 16–70 runs/week this is a
      coarse tripwire, able to catch "noticeably worse" but not a subtle few-percent regression.
- [ ] No new blocking check, gate, or ratchet is introduced.
- [ ] Nothing under `agent-monitoring/data/` is mutated.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` (done) — the read-time-only derived-metric precedent
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — why no token baseline is possible

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Measurement section
- `docs/agent-monitoring/schema.md` — "What is not recorded"

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (`build_baseline_report`,
  `build_gate_outcome_section`, `build_review_rework_section`)
- `tools/agent-monitoring/generate_retro.py`
- `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`

## Assumptions / Open Questions
- The pre-trial window length is the implementer's call, but it must be long enough to contain
  enough runs to be meaningful and recorded explicitly. State the chosen window and why.
- `tools.jsonl` carries `session_id`, which should allow trial-session rows to be separated from
  concurrent sessions later. Verify that it is populated consistently enough to rely on — if it is
  not, say so, because the harm check's ability to isolate the trial depends on it.

## Implementation Notes
Use the Python interpreter that matches CI (3.13) when running anything that must agree with CI
behaviour; this repo has two environments and using the wrong one has produced false "matches CI"
evidence before.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
