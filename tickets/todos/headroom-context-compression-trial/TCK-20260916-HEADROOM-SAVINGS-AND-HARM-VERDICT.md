---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT
phase: open
date: 2026-09-16
tags: [agent-monitoring, benchmarking, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT

## Title
Record a promote-or-abandon verdict with evidence — savings from Headroom's own ledger, harm from
agent-monitoring rates against the pre-trial baseline

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Fourth child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`. Requires the trial
(`TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`) and the baseline
(`TCK-20260916-HEADROOM-HARM-CHECK-BASELINE`) to be closed.

This ticket exists so the trial produces a **decision**, not an impression. The user's requirement
was explicit: *"we need to observe the result after applying this."* A trial that ends without a
recorded verdict, with the tooling quietly left in place, is the failure mode to avoid.

## Scope
- **Savings**: read Headroom's savings ledger / `headroom_stats` for the trial's paired
  measurements. This is the only real token source available — our own schema states token counts
  are not recorded and there is "no workaround within the current platform."
- **Harm**: re-run the baseline's rate computations over a matched post-trial window and compare
  against `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE`:
  - `final_status` DONE-rate; `failed` / `blocked` rate
  - `reason_code` mix
  - `tool_call_count` per phase — the over-compression detector
- Record a **promote** or **abandon** verdict against the plan's decision criteria, with the
  evidence inline.
- On abandon: execute the revert runbook and confirm state is gone.

## Out of Scope
- Extending the trial to change the result. If the numbers are inconclusive, "inconclusive" is the
  verdict — re-running until a favourable figure appears is exactly the anti-pattern this repo has
  been removing all week.
- Promotion itself. Phase 2 is `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT`, which stays
  BLOCKED on this verdict **and** the user's explicit approval.
- Using `cost_proxy_score` as a savings metric. It is computed from tool-call shape, not tokens, and
  would stay flat regardless of savings.
- Comparing cost between tickets. Invalid — scale varies by orders of magnitude.

## Acceptance Criteria
- [ ] A savings figure is recorded, sourced from paired same-payload measurements, with the source
      named.
- [ ] Harm comparison is recorded against the pre-trial baseline, using matched window boundaries
      and population counts — not eyeballed windows.
- [ ] The verdict is stated explicitly as promote / abandon / inconclusive, with reasoning.
- [ ] The verdict states its own confidence limit honestly: at roughly 16–70 runs/week this is a
      coarse tripwire and cannot resolve a subtle few-percent regression.
- [ ] If the verdict is abandon or inconclusive, the revert runbook is executed and the result
      recorded.
- [ ] No gate, ratchet, or blocking check is introduced over any of these numbers.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE` — the comparison point
- `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL` — the trial being judged
- `TCK-20260916-HEADROOM-PROXY-SESSION-CLASS-ROLLOUT` — unblocked only by a "promote" verdict plus
  the user's approval

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Decision criteria
- `docs/agent-monitoring/schema.md` — "What is not recorded"

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`

## Assumptions / Open Questions
- A confounder to state rather than hide: the trial window will contain unrelated work whose mix of
  tiers and workloads differs from the baseline window. Rate-based metrics reduce but do not
  eliminate this. Note it in the verdict rather than implying a controlled experiment.
- If `session_id` attribution proves unreliable, the harm check cannot cleanly isolate the trial —
  report that as a limitation of the verdict rather than proceeding as though it were clean.

## Implementation Notes
A negative or inconclusive verdict is a completely acceptable outcome and should be recorded as
plainly as a positive one. The trial was designed to be cheap to abandon.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
