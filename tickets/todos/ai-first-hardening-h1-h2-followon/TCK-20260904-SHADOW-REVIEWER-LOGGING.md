---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-SHADOW-REVIEWER-LOGGING
phase: open
date: 2026-09-04
tags: [ai, agent-monitoring, security]
---

# TCK-20260904-SHADOW-REVIEWER-LOGGING

## Title
Shadow-mode logging for candidate reviewer model

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
architecture-reviewer and security-reviewer both run on the same model family as implementer — the correlated-failure risk independent review exists to prevent (confirmed: 0/16 agent files declare model: frontmatter). The plan is to wire a candidate model to run alongside the current reviewer on every diff for both, logging both verdicts without blocking the workflow, with two extra requirements: attributable per-reviewer cost/timing figures, and a bounded (not indefinite) sample window. Investigation found a directly reusable precedent — TCK-20260729-SHADOW-PACKET-CALL-SITE already implements this exact advisory, env-var-gated, fail-open, negative-seq shadow-event pattern — and also found a hard test constraint (a hard-coded 11-call sidecar-adjacency test) that a naive dual-call implementation will break unless updated in this same ticket, plus a genuinely unresolved implementation fork (whether the harness supports a per-call model override) that must not be guessed.

## Scope
- Wire a candidate model to run alongside the current architecture-reviewer call (implement-ticket.js line 992, Architecture-Verify, runs on all tiers except hotfix) and the current security-reviewer call (line 1364, Security-Review, tag-gated trigger)
- Log both verdicts as distinct joinable records for the same (run_id, phase, diff), reusing TCK-20260729-SHADOW-PACKET-CALL-SITE's existing mechanism (negative monotonic seq counter, events.jsonl write, env-var gate, fail-open)
- Record and label candidate call count, review-phase wall time, workflow wall time, and cost_proxy_score by which reviewer produced them
- Implement a bounded sample/window condition a run can check to skip the candidate call once the window is closed
- Update tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call's hard-coded 11-call count/adjacency assertions to reflect the new dual-call sites, in this same ticket

## Out of Scope
- Cutting over the production gate outcome to the candidate model — a candidate-only failure must never trigger pushEvent('failed') or an early return
- Extending shadow evaluation to any reviewer other than architecture-reviewer and security-reviewer
- The pre-Implement Review phase's separate architecture-reviewer call against a prose plan (implement-ticket.js line 703) — different call site, out of this M1 scope
- Building the separate comparison-decision milestone that determines when the shadow window has "enough evidence" to promote — that is a distinct, not-yet-ticketed Bucket-B item

## Acceptance Criteria
- [ ] For every review-eligible run within the shadow window, both models' verdicts are recorded as distinct joinable records for the same (run_id, phase, diff) for both reviewers
- [ ] The workflow's actual gate outcome is driven exclusively by the current/production model's verdict — a candidate-only failure never triggers pushEvent('failed') or an early return, verified by a test stubbing a candidate-only-failing scenario
- [ ] Candidate call count, review-phase wall time, workflow wall time, and cost_proxy_score are recorded and labeled by which reviewer produced them
- [ ] Shadow evaluation is gated by an explicit bounded window/sample condition a run can check to skip the candidate call once closed, verified by a test, and test_sidecar_bash_write_precedes_each_covered_agent_call (or its updated equivalent) still passes

## Related Tickets
- TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
- TCK-20260705-WORKFLOW-SECURITY-GATE
- TCK-20260729-SHADOW-PACKET-CALL-SITE
- TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS
- TCK-20260710-SECURITY-REVIEWER-AGENT-DOC

## Related Docs
- docs/agent-monitoring/schema.md
- docs/ai/shadow_promotion_gate_thresholds_decision.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/architecture-reviewer.md
- .claude/agents/security-reviewer.md
- .claude/workflows/implement-ticket.js
- docs/agent-monitoring/schema.md
- docs/ai/shadow_promotion_gate_thresholds_decision.md
- tests/tools/test_current_run_sidecar_orchestrator.py
- tests/tools/test_architecture_reviewer_static.py
- tests/tools/test_step0_ts_orchestrator.py
- tools/agent-monitoring/cost_proxy.py

## Assumptions / Open Questions
- Whether the agent()/Agent tool harness actually supports a per-call model: override parameter, versus only a per-agent-file model: frontmatter, is genuinely unresolved and must be settled explicitly during Plan/Implementation rather than guessed — this is the single biggest implementation-choice fork and the epic itself defers it to implementation time
- security-reviewer's shadow sample accumulates far more slowly than architecture-reviewer's due to its asymmetric (tag-gated) trigger condition — the bounded-window design must account for this rather than using one uniform sample count
- Shadow mode roughly doubles model calls for 2 phases, and token/cost data doesn't otherwise reach agent-monitoring today — the Attributable requirement is the only safeguard against this becoming an invisible workflow slowdown

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
